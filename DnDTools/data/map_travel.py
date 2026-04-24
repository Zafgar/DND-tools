"""
map_travel — advance party/caravan/army tokens along annotation paths.

Each MapObject with ``follow_path_id`` set tracks how many miles it has
moved along that path in ``path_progress_miles``.  Given a world-map
scale + polyline geometry, we can:

* Project the progress back into ``(x%, y%)`` coordinates so the token
  snaps to the polyline.
* Advance all followers by a number of travel days — each token moves
  ``world_map.travel_speed_miles_per_day × travel_speed_mult × days``
  miles and we clamp at the total path length.

Pure logic; no pygame imports.  Tests in ``tests/test_map_travel.py``.
"""
from __future__ import annotations

import math
from typing import List, Tuple


# ----------------------------------------------------------------------
# Polyline geometry (aspect-aware miles)
# ----------------------------------------------------------------------

def _segment_lengths_miles(points: List[Tuple[float, float]],
                            world_w_px: int, world_h_px: int,
                            scale_miles_per_pct: float) -> List[float]:
    """Return per-segment lengths in miles using the same aspect-aware
    metric as MapEditorState.distance_miles."""
    if not points or world_w_px <= 0:
        return []
    aspect = world_h_px / world_w_px
    out: List[float] = []
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = (points[i][1] - points[i - 1][1]) * aspect
        d_pct = math.hypot(dx, dy)
        out.append(d_pct * max(scale_miles_per_pct, 0.0))
    return out


def polyline_total_miles(points: List[Tuple[float, float]],
                          world_w_px: int, world_h_px: int,
                          scale_miles_per_pct: float) -> float:
    return sum(_segment_lengths_miles(points, world_w_px, world_h_px,
                                        scale_miles_per_pct))


def point_at_miles(points: List[Tuple[float, float]],
                    world_w_px: int, world_h_px: int,
                    scale_miles_per_pct: float,
                    miles: float) -> Tuple[float, float]:
    """Return the (x%, y%) coordinate at ``miles`` along the polyline.
    Clamps at both ends.  Works in %-space using the same metric as the
    editor's aspect-aware distance."""
    if not points:
        return (0.0, 0.0)
    if len(points) == 1 or miles <= 0:
        return points[0]
    seg_miles = _segment_lengths_miles(points, world_w_px, world_h_px,
                                         scale_miles_per_pct)
    total = sum(seg_miles)
    if miles >= total or total <= 0:
        return points[-1]
    remaining = miles
    for i, sm in enumerate(seg_miles):
        if remaining <= sm or sm <= 0:
            t = (remaining / sm) if sm > 0 else 0.0
            a = points[i]
            b = points[i + 1]
            return (a[0] + (b[0] - a[0]) * t,
                    a[1] + (b[1] - a[1]) * t)
        remaining -= sm
    return points[-1]


# ----------------------------------------------------------------------
# Travel events + world-engine hooks
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Waypoint detection — settlements lying on (or near) a token's route.
# ----------------------------------------------------------------------

DEFAULT_WAYPOINT_TOLERANCE_PCT = 1.5


def nearby_settlements(world_map, x_pct: float, y_pct: float,
                        tolerance_pct: float = DEFAULT_WAYPOINT_TOLERANCE_PCT
                        ) -> list:
    """Return settlements (MapObjects whose ``object_type`` is in
    :data:`data.map_engine.SETTLEMENT_TYPES`) whose position is within
    ``tolerance_pct`` of ``(x_pct, y_pct)`` on the world map. Sorted
    nearest-first."""
    from data.map_engine import SETTLEMENT_TYPES
    out = []
    tol2 = tolerance_pct * tolerance_pct
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.object_type not in SETTLEMENT_TYPES:
                continue
            dx = obj.x - x_pct
            dy = obj.y - y_pct
            d2 = dx * dx + dy * dy
            if d2 <= tol2:
                out.append((d2, obj))
    out.sort(key=lambda t: t[0])
    return [o for _, o in out]


def clear_waypoints(obj) -> None:
    """Forget which settlements the token has crossed — typically called
    when the DM swaps the token onto a new route."""
    obj.visited_waypoint_ids = []


def _detect_passed_waypoints(world_map, obj, path,
                              miles_before: float, miles_after: float,
                              ww: int, wh: int, scale: float,
                              tolerance_pct: float) -> list:
    """Walk the polyline between ``miles_before`` and ``miles_after`` in
    small steps and collect any settlements whose tolerance circle the
    sub-segment touches. New entries are appended to
    ``obj.visited_waypoint_ids``."""
    if miles_after <= miles_before:
        return []
    span = miles_after - miles_before
    # Step at most a quarter of the tolerance per probe so a settlement
    # cannot be skipped over even when the token covers many miles in one
    # advance call. At least one probe per advance.
    step_miles = max(0.1, tolerance_pct * 0.5)
    steps = max(1, int(span / step_miles) + 1)
    fresh: list = []
    seen_this_call: set = set()
    for i in range(1, steps + 1):
        m = miles_before + (span * i / steps)
        x_pct, y_pct = point_at_miles(path.points, ww, wh, scale, m)
        for s in nearby_settlements(world_map, x_pct, y_pct, tolerance_pct):
            if (s.id not in obj.visited_waypoint_ids
                    and s.id not in seen_this_call):
                obj.visited_waypoint_ids.append(s.id)
                seen_this_call.add(s.id)
                fresh.append(s)
    return fresh


def advance_followers_events(world_map, days: float,
                               waypoint_tolerance_pct: float =
                               DEFAULT_WAYPOINT_TOLERANCE_PCT) -> list:
    """Move every MapObject on ``world_map`` whose ``follow_path_id``
    resolves to an annotation path forward by ``days`` travel-days.

    Returns a list of event dicts, one per moved token:
      * ``obj_id``         — MapObject id
      * ``label``          — display label (label or id)
      * ``path_id``        — AnnotationPath id
      * ``path_name``      — path display name (may be empty)
      * ``miles_before``   — progress before this call
      * ``miles_after``    — progress after this call (clamped to total)
      * ``total_miles``    — polyline length
      * ``fraction``       — miles_after / total_miles (0..1)
      * ``arrived``        — True iff the token reached the end *this* call
                              (it was short of the end before, now equals it)
    """
    if days <= 0:
        return []
    base_speed = max(0.0, world_map.travel_speed_miles_per_day or 0.0)
    if base_speed <= 0:
        return []

    ww = world_map.width * world_map.tile_size
    wh = world_map.height * world_map.tile_size
    scale = max(world_map.scale_miles_per_pct, 0.0)
    paths_by_id = {p.id: p for p in world_map.annotations}

    events = []
    for layer in world_map.layers:
        for obj in layer.objects:
            if not obj.follow_path_id:
                continue
            path = paths_by_id.get(obj.follow_path_id)
            if path is None or len(path.points) < 2:
                continue
            total = polyline_total_miles(path.points, ww, wh, scale)
            if total <= 0:
                continue
            mult = obj.travel_speed_mult if obj.travel_speed_mult > 0 else 1.0
            step = base_speed * mult * days
            miles_before = obj.path_progress_miles
            miles_after = min(total, miles_before + step)
            obj.path_progress_miles = miles_after
            x_pct, y_pct = point_at_miles(path.points, ww, wh, scale,
                                           miles_after)
            obj.x = x_pct
            obj.y = y_pct
            arrived = miles_before < total and miles_after >= total - 1e-6
            passed = _detect_passed_waypoints(
                world_map, obj, path, miles_before, miles_after,
                ww, wh, scale, waypoint_tolerance_pct,
            )
            events.append({
                "obj_id": obj.id,
                "label": obj.label or obj.id,
                "path_id": path.id,
                "path_name": getattr(path, "name", "") or path.id,
                "miles_before": miles_before,
                "miles_after": miles_after,
                "total_miles": total,
                "fraction": (miles_after / total) if total > 0 else 0.0,
                "arrived": arrived,
                "waypoints_passed": [
                    {"id": s.id, "label": s.label or s.id,
                     "object_type": s.object_type}
                    for s in passed
                ],
            })
    return events


def advance_followers(world_map, days: float) -> int:
    """Thin wrapper: advance tokens and return how many moved. See
    :func:`advance_followers_events` for per-token event detail
    (needed for arrival notifications)."""
    return len(advance_followers_events(world_map, days))


# ----------------------------------------------------------------------
# Manual progression editing
# ----------------------------------------------------------------------

def set_progress_miles(world_map, obj, miles: float) -> bool:
    """Move ``obj`` to the given miles along its ``follow_path_id``
    polyline, clamping 0..total. Updates ``obj.path_progress_miles``
    and ``obj.x``/``obj.y``. Returns True on success."""
    if not obj.follow_path_id:
        return False
    path = next((p for p in world_map.annotations
                 if p.id == obj.follow_path_id), None)
    if path is None or len(path.points) < 2:
        return False
    ww = world_map.width * world_map.tile_size
    wh = world_map.height * world_map.tile_size
    scale = max(world_map.scale_miles_per_pct, 0.0)
    total = polyline_total_miles(path.points, ww, wh, scale)
    if total <= 0:
        return False
    clamped = max(0.0, min(total, float(miles)))
    obj.path_progress_miles = clamped
    x_pct, y_pct = point_at_miles(path.points, ww, wh, scale, clamped)
    obj.x = x_pct
    obj.y = y_pct
    return True


def set_progress_fraction(world_map, obj, fraction: float) -> bool:
    """Same as :func:`set_progress_miles` but takes a 0..1 fraction."""
    if not obj.follow_path_id:
        return False
    path = next((p for p in world_map.annotations
                 if p.id == obj.follow_path_id), None)
    if path is None or len(path.points) < 2:
        return False
    ww = world_map.width * world_map.tile_size
    wh = world_map.height * world_map.tile_size
    scale = max(world_map.scale_miles_per_pct, 0.0)
    total = polyline_total_miles(path.points, ww, wh, scale)
    if total <= 0:
        return False
    f = max(0.0, min(1.0, float(fraction)))
    return set_progress_miles(world_map, obj, f * total)


def token_progress(world_map, obj) -> dict:
    """Return a progress snapshot for ``obj`` or empty dict if it isn't
    following any path."""
    if not obj.follow_path_id:
        return {}
    path = next((p for p in world_map.annotations
                 if p.id == obj.follow_path_id), None)
    if path is None or len(path.points) < 2:
        return {}
    ww = world_map.width * world_map.tile_size
    wh = world_map.height * world_map.tile_size
    scale = max(world_map.scale_miles_per_pct, 0.0)
    total = polyline_total_miles(path.points, ww, wh, scale)
    if total <= 0:
        return {}
    miles = max(0.0, min(total, obj.path_progress_miles))
    base_speed = max(0.0, world_map.travel_speed_miles_per_day or 0.0)
    mult = obj.travel_speed_mult if obj.travel_speed_mult > 0 else 1.0
    per_day = base_speed * mult
    days_remaining = ((total - miles) / per_day) if per_day > 0 else None
    return {
        "miles_traveled": miles,
        "miles_remaining": max(0.0, total - miles),
        "total_miles": total,
        "fraction": miles / total,
        "arrived": miles >= total - 1e-6,
        "miles_per_day": per_day,
        "days_remaining": days_remaining,
    }
