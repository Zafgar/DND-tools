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
# World-engine hook: advance all path-following tokens by N days.
# ----------------------------------------------------------------------

def advance_followers(world_map, days: float) -> int:
    """Move every MapObject on ``world_map`` whose ``follow_path_id``
    resolves to an annotation path forward by ``days`` travel-days.
    Returns the number of tokens advanced."""
    if days <= 0:
        return 0
    base_speed = max(0.0, world_map.travel_speed_miles_per_day or 0.0)
    if base_speed <= 0:
        return 0

    ww = world_map.width * world_map.tile_size
    wh = world_map.height * world_map.tile_size
    scale = max(world_map.scale_miles_per_pct, 0.0)
    paths_by_id = {p.id: p for p in world_map.annotations}

    moved = 0
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
            obj.path_progress_miles = min(total,
                                           obj.path_progress_miles + step)
            x_pct, y_pct = point_at_miles(path.points, ww, wh, scale,
                                           obj.path_progress_miles)
            obj.x = x_pct
            obj.y = y_pct
            moved += 1
    return moved
