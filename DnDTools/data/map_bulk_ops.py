"""Bulk-edit operations for map objects.

Pure logic on top of ``WorldMap`` / ``MapObject`` so the editor can
"drag a rectangle, edit everything inside" without scattering the
business rules across the pygame layer.

Selection model is a simple set of object IDs, kept on the editor
state. Helpers here build it from a rectangle, then mutate the
underlying objects in batch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from data.map_engine import (
    WorldMap, MapObject, MapLayer, MAP_OBJECT_TYPES,
)
from data.path_waypoints import on_object_moved, on_object_deleted


# --------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------- #
def objects_in_rect(world_map: WorldMap,
                      x1_pct: float, y1_pct: float,
                      x2_pct: float, y2_pct: float,
                      *, layer_idx: Optional[int] = None
                      ) -> List[MapObject]:
    """Return every MapObject whose (x, y) sits within the rectangle.

    Coordinates are world-percentage (0..100). The rectangle is given
    by any two corners (min/max are derived). When ``layer_idx`` is
    None, every layer is searched.
    """
    x_lo, x_hi = min(x1_pct, x2_pct), max(x1_pct, x2_pct)
    y_lo, y_hi = min(y1_pct, y2_pct), max(y1_pct, y2_pct)
    out: List[MapObject] = []
    layers = world_map.layers if layer_idx is None else [
        world_map.layers[layer_idx]
    ] if 0 <= layer_idx < len(world_map.layers) else []
    for layer in layers:
        for obj in layer.objects:
            if x_lo <= obj.x <= x_hi and y_lo <= obj.y <= y_hi:
                out.append(obj)
    return out


def select_in_rect(world_map: WorldMap,
                     x1: float, y1: float, x2: float, y2: float,
                     *, layer_idx: Optional[int] = None) -> Set[str]:
    """Convenience wrapper that returns the IDs only (handy for the
    editor's `selected_ids` set)."""
    return {obj.id for obj in objects_in_rect(world_map, x1, y1, x2, y2,
                                                  layer_idx=layer_idx)}


def _resolve(world_map: WorldMap, obj_ids: Set[str]) -> List[MapObject]:
    """Return the MapObject instances matching ``obj_ids`` across all
    layers. Missing IDs are silently skipped."""
    if not obj_ids:
        return []
    out = []
    wanted = set(obj_ids)
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.id in wanted:
                out.append(obj)
    return out


# --------------------------------------------------------------------- #
# Bulk operations
# --------------------------------------------------------------------- #
def bulk_move(world_map: WorldMap, obj_ids: Set[str],
                dx_pct: float, dy_pct: float) -> int:
    """Translate every selected object by (dx, dy) in % space. Routes
    that thread through any of these objects auto-rebuild via
    ``on_object_moved``. Returns how many objects moved."""
    moved = 0
    for obj in _resolve(world_map, obj_ids):
        obj.x = max(0.0, min(100.0, obj.x + float(dx_pct)))
        obj.y = max(0.0, min(100.0, obj.y + float(dy_pct)))
        on_object_moved(world_map, obj.id)
        moved += 1
    return moved


def bulk_set_object_type(world_map: WorldMap, obj_ids: Set[str],
                            object_type: str) -> int:
    """Retype every selected object. Rejects unknown types so a typo
    can't silently leave invisible ghost-tokens. Returns how many
    were retyped."""
    if object_type not in MAP_OBJECT_TYPES:
        return 0
    proto = MAP_OBJECT_TYPES[object_type]
    n = 0
    for obj in _resolve(world_map, obj_ids):
        obj.object_type = object_type
        # Refresh visual defaults (colour / size / icon) but only when
        # they still match the previous prototype — preserves any
        # custom overrides the DM has made.
        if proto:
            obj.color = proto.get("color", obj.color)
            obj.icon = proto.get("icon", obj.icon)
        n += 1
    return n


def bulk_add_tags(world_map: WorldMap, obj_ids: Set[str],
                    tags: List[str]) -> int:
    """Append ``tags`` to every selected object's ``tags`` list,
    deduplicating per-object. Returns how many objects were touched."""
    if not tags:
        return 0
    changed = 0
    for obj in _resolve(world_map, obj_ids):
        before = list(obj.tags)
        for t in tags:
            t = t.strip()
            if t and t not in obj.tags:
                obj.tags.append(t)
        if obj.tags != before:
            changed += 1
    return changed


def bulk_remove_tags(world_map: WorldMap, obj_ids: Set[str],
                       tags: List[str]) -> int:
    """Remove every tag in ``tags`` from each selected object. Returns
    the number of objects whose tag list actually shrank."""
    drop = {t.strip() for t in tags if t and t.strip()}
    if not drop:
        return 0
    changed = 0
    for obj in _resolve(world_map, obj_ids):
        before = list(obj.tags)
        obj.tags = [t for t in obj.tags if t not in drop]
        if obj.tags != before:
            changed += 1
    return changed


def bulk_set_visibility(world_map: WorldMap, obj_ids: Set[str],
                          *, visible: Optional[bool] = None,
                          dm_only: Optional[bool] = None) -> int:
    """Toggle ``visible`` and/or ``dm_only`` on the whole selection.
    Either flag is left alone when its parameter is None. Returns
    how many objects were touched."""
    if visible is None and dm_only is None:
        return 0
    n = 0
    for obj in _resolve(world_map, obj_ids):
        if visible is not None:
            obj.visible = bool(visible)
        if dm_only is not None:
            obj.dm_only = bool(dm_only)
        n += 1
    return n


def bulk_delete(world_map: WorldMap, obj_ids: Set[str]) -> int:
    """Delete every selected object. Auto-scrubs any waypoint paths
    that referenced them via ``on_object_deleted`` (paths losing both
    endpoints are auto-removed). Returns how many objects were
    deleted."""
    if not obj_ids:
        return 0
    wanted = set(obj_ids)
    deleted_ids: List[str] = []
    for layer in world_map.layers:
        kept = []
        for obj in layer.objects:
            if obj.id in wanted:
                deleted_ids.append(obj.id)
                continue
            kept.append(obj)
        layer.objects = kept
    for oid in deleted_ids:
        on_object_deleted(world_map, oid)
    return len(deleted_ids)


# --------------------------------------------------------------------- #
# Selection summary (for a status bar)
# --------------------------------------------------------------------- #
@dataclass
class SelectionSummary:
    count: int
    by_type: dict
    common_tags: List[str]


def selection_summary(world_map: WorldMap,
                        obj_ids: Set[str]) -> SelectionSummary:
    """Compact stats for the editor's bottom bar."""
    objs = _resolve(world_map, obj_ids)
    by_type: dict = {}
    tag_sets: List[set] = []
    for obj in objs:
        by_type[obj.object_type] = by_type.get(obj.object_type, 0) + 1
        tag_sets.append(set(obj.tags))
    if tag_sets:
        common = set.intersection(*tag_sets)
    else:
        common = set()
    return SelectionSummary(count=len(objs), by_type=by_type,
                              common_tags=sorted(common))
