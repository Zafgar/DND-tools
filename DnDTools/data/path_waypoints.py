"""Path-waypoint operations — add / remove / move settlements on an
``AnnotationPath`` and have the polyline rebuild itself.

The intent is the workflow the user described:
  * Click city A, click city C → a path connects A → C.
  * Click city B between them → B becomes a waypoint, polyline now
    threads A → B → C.
  * Drag B to a new spot → the polyline follows B.
  * Delete B → polyline collapses back to A → C.
  * Delete A or C → the path itself loses its endpoint and is
    auto-removed (or shortened).

Everything here works on plain dataclasses; no pygame, no UI state.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from data.map_engine import (
    WorldMap, MapObject, AnnotationPath,
)


def _find_object(world_map: WorldMap, obj_id: str) -> Optional[MapObject]:
    if not obj_id:
        return None
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.id == obj_id:
                return obj
    return None


def rebuild_points_from_waypoints(world_map: WorldMap,
                                     path: AnnotationPath) -> bool:
    """Replace ``path.points`` with the (x%, y%) of every waypoint
    object in order. Drops missing/deleted waypoints from the list.
    Returns True iff the polyline still has 2+ points after rebuild."""
    if not path.waypoint_object_ids:
        return len(path.points) >= 2
    fresh_points: List[Tuple[float, float]] = []
    fresh_ids: List[str] = []
    for wid in path.waypoint_object_ids:
        obj = _find_object(world_map, wid)
        if obj is None:
            continue
        fresh_points.append((float(obj.x), float(obj.y)))
        fresh_ids.append(wid)
    path.points = fresh_points
    path.waypoint_object_ids = fresh_ids
    return len(path.points) >= 2


def add_waypoint(world_map: WorldMap, path: AnnotationPath,
                   obj_id: str, *,
                   position: Optional[int] = None) -> bool:
    """Insert ``obj_id`` into ``path.waypoint_object_ids`` at index
    ``position`` (default: append). Rebuilds the polyline. Returns
    True on success."""
    obj = _find_object(world_map, obj_id)
    if obj is None:
        return False
    if obj_id in path.waypoint_object_ids:
        return False
    if position is None or position < 0 or position > len(path.waypoint_object_ids):
        path.waypoint_object_ids.append(obj_id)
    else:
        path.waypoint_object_ids.insert(position, obj_id)
    rebuild_points_from_waypoints(world_map, path)
    return True


def remove_waypoint(world_map: WorldMap, path: AnnotationPath,
                      obj_id: str) -> bool:
    """Drop ``obj_id`` from the path. Returns True iff it was present."""
    if obj_id not in path.waypoint_object_ids:
        return False
    path.waypoint_object_ids.remove(obj_id)
    rebuild_points_from_waypoints(world_map, path)
    return True


def insert_waypoint_between(world_map: WorldMap, path: AnnotationPath,
                                new_obj_id: str) -> bool:
    """Insert ``new_obj_id`` at the polyline-segment-nearest-it.
    Useful when the DM clicks a settlement to add it to an existing
    A → C path so it becomes A → B → C. Returns True on success."""
    obj = _find_object(world_map, new_obj_id)
    if obj is None or new_obj_id in path.waypoint_object_ids:
        return False
    if len(path.waypoint_object_ids) < 2:
        # Path doesn't have two endpoints yet — append.
        return add_waypoint(world_map, path, new_obj_id)
    # Score every gap between waypoints and pick the smallest detour.
    best_idx = 1
    best_extra = float("inf")
    for i in range(1, len(path.waypoint_object_ids)):
        a = _find_object(world_map, path.waypoint_object_ids[i - 1])
        b = _find_object(world_map, path.waypoint_object_ids[i])
        if a is None or b is None:
            continue
        d_ab = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        d_anew = ((a.x - obj.x) ** 2 + (a.y - obj.y) ** 2) ** 0.5
        d_newb = ((obj.x - b.x) ** 2 + (obj.y - b.y) ** 2) ** 0.5
        extra = (d_anew + d_newb) - d_ab
        if extra < best_extra:
            best_extra = extra
            best_idx = i
    return add_waypoint(world_map, path, new_obj_id, position=best_idx)


# --------------------------------------------------------------------- #
# World-map level reactions to MapObject changes
# --------------------------------------------------------------------- #
def on_object_moved(world_map: WorldMap, obj_id: str) -> int:
    """Call after dragging ``obj_id`` to a new (x, y). Rebuilds every
    path that lists this object as a waypoint. Returns how many paths
    were rebuilt."""
    n = 0
    for path in world_map.annotations:
        if obj_id in path.waypoint_object_ids:
            rebuild_points_from_waypoints(world_map, path)
            n += 1
    return n


def on_object_deleted(world_map: WorldMap, obj_id: str) -> dict:
    """Scrub ``obj_id`` from every path's waypoint list. Paths that
    fall below 2 waypoints get auto-removed from the world map.

    Returns ``{rebuilt: int, removed: int, removed_path_ids: [...]}``.
    """
    rebuilt = 0
    removed_ids: List[str] = []
    surviving = []
    for path in world_map.annotations:
        if obj_id in path.waypoint_object_ids:
            path.waypoint_object_ids.remove(obj_id)
            rebuild_points_from_waypoints(world_map, path)
            if len(path.waypoint_object_ids) < 2:
                # Path lost an endpoint — drop it.
                removed_ids.append(path.id)
                continue
            rebuilt += 1
        surviving.append(path)
    world_map.annotations = surviving
    return {
        "rebuilt": rebuilt,
        "removed": len(removed_ids),
        "removed_path_ids": removed_ids,
    }


def waypoint_objects(world_map: WorldMap,
                       path: AnnotationPath) -> List[MapObject]:
    """Return the actual MapObject instances behind a path's waypoint
    ids — useful for showing a sidebar list when the DM clicks the
    path."""
    out = []
    for wid in path.waypoint_object_ids:
        obj = _find_object(world_map, wid)
        if obj is not None:
            out.append(obj)
    return out


def make_path_between(world_map: WorldMap, *obj_ids: str,
                        path_id: str = "", name: str = "",
                        path_type: str = "route") -> Optional[AnnotationPath]:
    """Create a new AnnotationPath threading the given object ids in
    order. Inserts the path into ``world_map.annotations`` if at
    least 2 valid waypoints exist. Returns the new path (or None)."""
    if len(obj_ids) < 2:
        return None
    p = AnnotationPath(id=path_id, name=name, path_type=path_type)
    for oid in obj_ids:
        add_waypoint(world_map, p, oid)
    if len(p.waypoint_object_ids) < 2:
        return None
    world_map.annotations.append(p)
    return p
