"""Logic for the "drag campaign locations onto the map" palette.

Pure data — the pygame UI calls these helpers to populate a sidebar
list. Click / drag handling is a thin wrapper in
``states/map_editor*.py``.

Workflow:

  1. Open the map editor with a Campaign whose World has unplaced
     settlements (created in the campaign manager but not yet on the
     interactive WorldMap).
  2. The editor renders ``location_palette_entries(world, world_map)``
     in a sidebar; each entry shows the settlement's name + type +
     description preview.
  3. Click an entry → ``place_location_on_map(...)`` inserts the
     MapObject (using the bridge) at the supplied (x%, y%).
  4. Drag-and-drop variant: caller passes ``defer=True`` to get back
     a "carried" handle they later commit at the drop position.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from data.world import World, Location
from data.map_engine import WorldMap, MapObject
from data.campaign_map_sync import (
    sync_location_to_map, all_settlement_locations,
    available_unplaced_locations,
)


@dataclass
class PaletteEntry:
    """One row in the drag-onto-map sidebar."""
    location_id: str
    name: str
    location_type: str
    description: str = ""
    has_token: bool = False  # True when this loc already has a map token

    @property
    def display(self) -> str:
        kind = self.location_type or "?"
        return f"{self.name}  ·  {kind}"


def location_palette_entries(world: World, world_map: WorldMap,
                                *, settlements_only: bool = True
                                ) -> List[PaletteEntry]:
    """Return the palette rows in alphabetical order. The
    ``has_token`` flag tells the UI to grey out already-placed
    entries (you can still click to focus them on the map)."""
    locs = (all_settlement_locations(world)
            if settlements_only
            else list(world.locations.values()))
    placed_ids = {oid for oid in
                  {obj.linked_location_id
                   for layer in world_map.layers
                   for obj in layer.objects
                   if obj.linked_location_id}}
    out = [
        PaletteEntry(
            location_id=loc.id,
            name=loc.name,
            location_type=loc.location_type,
            description=(loc.description or "")[:80],
            has_token=loc.id in placed_ids,
        )
        for loc in locs
    ]
    out.sort(key=lambda p: p.name.lower())
    return out


def place_location_on_map(world: World, world_map: WorldMap,
                            location_id: str,
                            x_pct: float, y_pct: float) -> Optional[MapObject]:
    """Drop a campaign Location onto the map at (x%, y%). Reuses the
    existing token if there's already one (just moves it to the
    new position). Returns the MapObject or None if location not
    found."""
    if location_id not in world.locations:
        return None
    obj = sync_location_to_map(world, world_map, location_id,
                                  default_x=float(x_pct),
                                  default_y=float(y_pct))
    # If sync returned an existing token at a different spot, snap
    # to the new drop position. (sync preserves position when an
    # existing token is found; the explicit drop overrides that.)
    obj.x = float(x_pct)
    obj.y = float(y_pct)
    return obj


def palette_search(world: World, world_map: WorldMap,
                     query: str = "") -> List[PaletteEntry]:
    """Same as ``location_palette_entries`` but filtered by a loose
    name / type substring match."""
    q = (query or "").strip().lower()
    rows = location_palette_entries(world, world_map)
    if not q:
        return rows
    return [
        r for r in rows
        if q in r.name.lower()
        or q in (r.location_type or "").lower()
        or q in (r.description or "").lower()
    ]


def unplaced_count(world: World, world_map: WorldMap) -> int:
    """How many settlements still lack a map token. Useful for a
    sidebar badge: 'Settlements (3 unplaced)'."""
    return len(available_unplaced_locations(world, world_map))
