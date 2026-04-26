"""Bridge between ``Campaign.world.locations`` (the text/relational
campaign model) and ``WorldMap.layers[*].objects`` (the interactive
map tokens).

The DM works in two views — the campaign manager (lists, NPCs, lore)
and the interactive map editor (drag tokens around) — but both need
to talk about the *same* settlement when the campaign mentions
"Arenhold". This module keeps them in sync.

Two-way operations:

  * ``location_to_map_object(location, map_object_type=...)`` builds
    a fresh ``MapObject`` whose ``linked_location_id`` points back at
    the location, with sensible defaults for the type ("city", "town",
    "fort" etc.) inferred from the location's ``location_type``.

  * ``find_map_object_for_location(world_map, location_id)`` returns
    the existing token bound to a location, or None.

  * ``sync_location_to_map(world, world_map, location_id, ...)``
    upserts a token: existing token's position survives if already
    placed; otherwise a new token is appended at a default cell. The
    DM can then drag it where it belongs.

  * ``sync_map_object_to_location(world, world_map, obj_id, ...)``
    creates a campaign Location for an unlinked map token (the user
    drew a new town directly on the map).

  * ``unlink_location(world_map, location_id)`` clears the link on
    all tokens (used when a location is deleted in the campaign
    manager — keeps the token if the user still wants it on the map).

  * ``available_unplaced_locations(world, world_map)`` returns
    Locations from the world that don't yet have a map token —
    perfect for a sidebar palette: "Drag onto map".

Pure logic, no pygame.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from data.world import World, Location, generate_id
from data.map_engine import (
    WorldMap, MapObject, MapLayer, SETTLEMENT_TYPES,
    MAP_OBJECT_TYPES,
)


# location_type → map object_type
_LOC_TYPE_TO_OBJ_TYPE = {
    "country":    "capital",
    "kingdom":    "capital",
    "capital":    "capital",
    "city":       "city",
    "town":       "town",
    "village":    "village",
    "hamlet":     "village",
    "fort":       "fort",
    "stronghold": "fort",
    "outpost":    "village",
    "wilderness": "info_pin",
    "region":     "info_pin",
    "dungeon":    "dungeon",
    "cave":       "cave",
    "temple":     "temple",
    "tavern":     "tavern",
    "shop":       "shop",
}


def map_object_type_for_location(location: Location) -> str:
    """Pick the right MapObject ``object_type`` for a campaign Location."""
    key = (location.location_type or "").lower()
    return _LOC_TYPE_TO_OBJ_TYPE.get(key, "info_pin")


def location_to_map_object(location: Location, *,
                             object_type: str = "",
                             x: float = 50.0, y: float = 50.0) -> MapObject:
    """Build a MapObject for a campaign location. Doesn't insert into
    any WorldMap — caller decides where to place it."""
    obj_type = object_type or map_object_type_for_location(location)
    if obj_type not in MAP_OBJECT_TYPES:
        obj_type = "info_pin"
    return MapObject(
        x=float(x), y=float(y),
        object_type=obj_type,
        label=location.name,
        hover_info=location.description[:120] if location.description else "",
        notes=location.notes or "",
        linked_location_id=location.id,
        tags=list(location.tags) if location.tags else [],
    )


def find_map_object_for_location(world_map: WorldMap,
                                   location_id: str) -> Optional[MapObject]:
    """Return the (first) MapObject bound to ``location_id`` or None."""
    if not location_id:
        return None
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.linked_location_id == location_id:
                return obj
    return None


def sync_location_to_map(world: World, world_map: WorldMap,
                            location_id: str, *,
                            default_layer_idx: int = 0,
                            default_x: float = 50.0,
                            default_y: float = 50.0) -> MapObject:
    """Make sure ``world.locations[location_id]`` has a MapObject on
    ``world_map``. Updates label / hover / notes from the location if
    a token is already present so the views don't drift. Returns the
    token (existing or newly inserted)."""
    if location_id not in world.locations:
        raise KeyError(f"Unknown location id {location_id!r}")
    loc = world.locations[location_id]
    existing = find_map_object_for_location(world_map, location_id)
    if existing is not None:
        # Refresh display fields — but leave the user's chosen
        # position alone.
        existing.label = loc.name
        existing.hover_info = (loc.description[:120]
                                 if loc.description else "")
        existing.notes = loc.notes or ""
        existing.tags = list(loc.tags) if loc.tags else []
        return existing
    # Create new
    obj = location_to_map_object(loc, x=default_x, y=default_y)
    if not world_map.layers:
        world_map.layers = [MapLayer(id="L0", name="Surface")]
    layer_idx = max(0, min(default_layer_idx, len(world_map.layers) - 1))
    world_map.layers[layer_idx].objects.append(obj)
    return obj


def sync_map_object_to_location(world: World, world_map: WorldMap,
                                  obj_id: str) -> Optional[Location]:
    """Create a campaign Location for an unlinked map token. Returns
    the new Location (or the already-linked one when the token already
    has linked_location_id)."""
    obj = None
    for layer in world_map.layers:
        for o in layer.objects:
            if o.id == obj_id:
                obj = o
                break
        if obj:
            break
    if obj is None:
        return None
    if obj.linked_location_id and obj.linked_location_id in world.locations:
        return world.locations[obj.linked_location_id]
    new_id = generate_id(world, prefix="loc")
    loc = Location(
        id=new_id,
        name=obj.label or new_id,
        location_type=_obj_type_to_loc_type(obj.object_type),
        description=obj.hover_info,
        notes=obj.notes,
        tags=list(obj.tags),
    )
    world.locations[new_id] = loc
    obj.linked_location_id = new_id
    return loc


def _obj_type_to_loc_type(obj_type: str) -> str:
    rev = {v: k for k, v in _LOC_TYPE_TO_OBJ_TYPE.items()}
    return rev.get(obj_type, obj_type)


def unlink_location(world_map: WorldMap, location_id: str) -> int:
    """Clear ``linked_location_id`` from every token bound to
    ``location_id``. Use this when the DM deletes a location in the
    campaign manager but wants its map token to remain (e.g. the
    place was destroyed but is still on the map as a ruin).
    Returns how many tokens were unlinked."""
    n = 0
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.linked_location_id == location_id:
                obj.linked_location_id = ""
                n += 1
    return n


def remove_map_objects_for_location(world_map: WorldMap,
                                       location_id: str) -> int:
    """Delete tokens bound to ``location_id``. Use this when the DM
    wants the location and ALL its representations gone. Returns the
    number of tokens removed."""
    n = 0
    for layer in world_map.layers:
        kept = []
        for obj in layer.objects:
            if obj.linked_location_id == location_id:
                n += 1
                continue
            kept.append(obj)
        layer.objects = kept
    return n


def available_unplaced_locations(world: World,
                                    world_map: WorldMap) -> List[Location]:
    """Locations in the world that don't have a map token yet —
    perfect for a "drag-onto-map" palette."""
    placed = set()
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.linked_location_id:
                placed.add(obj.linked_location_id)
    return [loc for lid, loc in world.locations.items()
            if lid not in placed]


def all_settlement_locations(world: World) -> List[Location]:
    """Filter locations down to settlements (city / town / village /
    fort / capital) — the typical 'settlement palette' content."""
    settlement_keys = {"capital", "city", "town", "village", "fort",
                        "hamlet", "stronghold", "kingdom", "country"}
    return [loc for loc in world.locations.values()
            if (loc.location_type or "").lower() in settlement_keys]


def all_settlement_objects(world_map: WorldMap) -> List[MapObject]:
    """Map tokens whose ``object_type`` is a settlement type."""
    out = []
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.object_type in SETTLEMENT_TYPES:
                out.append(obj)
    return out
