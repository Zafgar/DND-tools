"""Battle-map prefabs — drop a fully-furnished building / setpiece on
the grid in one click.

Each ``Prefab`` is a list of relative TerrainObject placements
(``offset_x``, ``offset_y``, ``terrain_type``, optional elevation /
size). ``apply_prefab(battle, prefab, anchor_x, anchor_y)`` translates
those into world-positioned ``TerrainObject`` instances and appends
them to ``battle.terrain``.

Pure logic — no pygame. UI integration (drag-and-drop in the terrain
editor) lives in states/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class PrefabTile:
    terrain_type: str
    dx: int = 0          # offset from anchor (x, west→east)
    dy: int = 0          # offset from anchor (y, north→south)
    width: int = 1
    height: int = 1
    elevation: int = -1  # -1 = use type default

    def to_terrain(self, anchor_x: int, anchor_y: int):
        from engine.terrain import TerrainObject
        kwargs = {
            "terrain_type": self.terrain_type,
            "grid_x": int(anchor_x + self.dx),
            "grid_y": int(anchor_y + self.dy),
            "width": int(self.width),
            "height": int(self.height),
        }
        if self.elevation >= 0:
            kwargs["elevation"] = int(self.elevation)
        return TerrainObject(**kwargs)


@dataclass
class Prefab:
    key: str
    name: str
    category: str = "building"   # building, room, decor, encampment, ruin
    description: str = ""
    tiles: List[PrefabTile] = field(default_factory=list)
    footprint: Tuple[int, int] = (0, 0)  # bounding (w, h) of relative tiles

    def __post_init__(self):
        if not self.tiles:
            self.footprint = (0, 0)
            return
        max_x = max(t.dx + t.width for t in self.tiles)
        max_y = max(t.dy + t.height for t in self.tiles)
        self.footprint = (max_x, max_y)


# --------------------------------------------------------------------- #
# Helper builders to keep the catalog readable
# --------------------------------------------------------------------- #
def _wall_rect(w: int, h: int) -> List[PrefabTile]:
    """Hollow rectangle of walls W x H."""
    out = []
    for x in range(w):
        out.append(PrefabTile("wall", x, 0))
        out.append(PrefabTile("wall", x, h - 1))
    for y in range(1, h - 1):
        out.append(PrefabTile("wall", 0, y))
        out.append(PrefabTile("wall", w - 1, y))
    return out


def _scatter(terrain: str, positions: List[Tuple[int, int]]) -> List[PrefabTile]:
    return [PrefabTile(terrain, x, y) for x, y in positions]


# --------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------- #
PREFABS: Dict[str, Prefab] = {
    # ---------- Buildings ----------
    "small_hut": Prefab(
        key="small_hut", name="Small Hut", category="building",
        description="3x3 wattle hut, single door, fireplace inside.",
        tiles=_wall_rect(3, 3)
              + [PrefabTile("door", 1, 0)]            # door on north wall
              + [PrefabTile("fire", 1, 1)],           # central hearth
    ),
    "cottage": Prefab(
        key="cottage", name="Cottage", category="building",
        description="4x4 cottage with door, hearth, table and bed.",
        tiles=_wall_rect(4, 4)
              + [PrefabTile("door", 1, 0)]
              + [PrefabTile("fire", 1, 1)]
              + [PrefabTile("table", 2, 2)]
              + [PrefabTile("crate", 3, 1)],
    ),
    "tavern_common": Prefab(
        key="tavern_common", name="Tavern Common Room",
        category="building",
        description="6x5 tavern, central fireplace, four tables, bar.",
        tiles=_wall_rect(6, 5)
              + [PrefabTile("door", 2, 0), PrefabTile("door", 3, 0)]
              + [PrefabTile("fire", 1, 2)]
              + [PrefabTile("table", 2, 2), PrefabTile("table", 3, 2),
                  PrefabTile("table", 2, 3), PrefabTile("table", 3, 3)]
              + [PrefabTile("table", 4, 1), PrefabTile("table", 4, 2),
                  PrefabTile("table", 4, 3)],
    ),
    "shop": Prefab(
        key="shop", name="Shop", category="building",
        description="4x4 shop with door, counter (table), shelves (crates).",
        tiles=_wall_rect(4, 4)
              + [PrefabTile("door", 1, 0)]
              + [PrefabTile("table", 1, 1), PrefabTile("table", 2, 1)]
              + [PrefabTile("crate", 3, 1), PrefabTile("crate", 3, 2),
                  PrefabTile("crate", 3, 3)],
    ),
    "smithy": Prefab(
        key="smithy", name="Smithy", category="building",
        description="4x4 forge with anvil + hot bed.",
        tiles=_wall_rect(4, 4)
              + [PrefabTile("door", 1, 0)]
              + [PrefabTile("fire", 1, 1), PrefabTile("fire", 2, 1)]  # forge
              + [PrefabTile("crate", 1, 2)]                            # anvil
              + [PrefabTile("table", 2, 2)]                            # bench
              + [PrefabTile("barrel", 3, 1)],                          # quench
    ),
    "watchtower": Prefab(
        key="watchtower", name="Watchtower", category="building",
        description="3x3 stone tower (15 ft platforms inside).",
        tiles=_wall_rect(3, 3)
              + [PrefabTile("door", 1, 0)]
              + [PrefabTile("platform_15", 1, 1)],
    ),
    "stables": Prefab(
        key="stables", name="Stables", category="building",
        description="6x3 horse stalls + central aisle.",
        tiles=_wall_rect(6, 3)
              + [PrefabTile("door", 2, 0)]
              + [PrefabTile("crate", 1, 1), PrefabTile("crate", 2, 1)]
              + [PrefabTile("crate", 3, 1), PrefabTile("crate", 4, 1)],
    ),
    # ---------- Rooms ----------
    "barracks_room": Prefab(
        key="barracks_room", name="Barracks Room", category="room",
        description="5x4 dorm with 4 bunks (crates) and a table.",
        tiles=_wall_rect(5, 4)
              + [PrefabTile("door", 0, 1)]
              + [PrefabTile("crate", 1, 1), PrefabTile("crate", 1, 2),
                  PrefabTile("crate", 3, 1), PrefabTile("crate", 3, 2)]
              + [PrefabTile("table", 2, 2)],
    ),
    "treasure_vault": Prefab(
        key="treasure_vault", name="Treasure Vault", category="room",
        description="4x4 vault, locked door, four chests, two pillars.",
        tiles=_wall_rect(4, 4)
              + [PrefabTile("door_locked", 1, 0)]
              + [PrefabTile("crate", 1, 2), PrefabTile("crate", 2, 2)]
              + [PrefabTile("crate", 1, 1), PrefabTile("crate", 2, 1)]
              + [PrefabTile("pillar", 0, 0), PrefabTile("pillar", 3, 3)],
    ),
    "shrine": Prefab(
        key="shrine", name="Shrine", category="room",
        description="3x3 shrine with altar (table) and braziers.",
        tiles=_wall_rect(3, 3)
              + [PrefabTile("door", 1, 0)]
              + [PrefabTile("table", 1, 1)]                  # altar
              + [PrefabTile("fire", 0, 1), PrefabTile("fire", 2, 1)],
    ),
    # ---------- Decor / setpieces ----------
    "campsite": Prefab(
        key="campsite", name="Campsite", category="encampment",
        description="Open camp: central fire, 4 bedrolls, supply crate.",
        tiles=[PrefabTile("fire", 2, 2)]
              + _scatter("difficult", [(1, 1), (3, 1), (1, 3), (3, 3)])
              + [PrefabTile("crate", 4, 2)],
    ),
    "wagon_circle": Prefab(
        key="wagon_circle", name="Wagon Circle", category="encampment",
        description="Defensive ring of wagons with central fire.",
        tiles=[PrefabTile("crate", 0, 0), PrefabTile("crate", 4, 0),
                PrefabTile("crate", 0, 4), PrefabTile("crate", 4, 4),
                PrefabTile("crate", 2, 0), PrefabTile("crate", 0, 2),
                PrefabTile("crate", 4, 2), PrefabTile("crate", 2, 4)]
              + [PrefabTile("fire", 2, 2)],
    ),
    "well_yard": Prefab(
        key="well_yard", name="Well & Yard", category="decor",
        description="Stone well surrounded by crates and a barrel.",
        tiles=[PrefabTile("rock", 1, 1)]                       # well rim
              + [PrefabTile("crate", 0, 0), PrefabTile("crate", 2, 0),
                  PrefabTile("crate", 0, 2), PrefabTile("crate", 2, 2)]
              + [PrefabTile("barrel", 1, 0)],
    ),
    "ruined_tower": Prefab(
        key="ruined_tower", name="Ruined Tower", category="ruin",
        description="Crumbled tower base with rubble inside.",
        tiles=_wall_rect(3, 3)
              + [PrefabTile("rubble", 1, 1)]
              + [PrefabTile("rubble", 2, 1)]
              # Two collapsed walls (replace with rubble)
              + [PrefabTile("rubble", 0, 2), PrefabTile("rubble", 2, 2)],
    ),
}


def list_prefabs() -> List[Prefab]:
    return list(PREFABS.values())


def list_by_category(category: str) -> List[Prefab]:
    return [p for p in PREFABS.values() if p.category == category]


def get_prefab(key: str) -> Prefab:
    if key not in PREFABS:
        raise KeyError(f"Prefab {key!r} not found. Available: {list(PREFABS)}")
    return PREFABS[key]


def categories() -> List[str]:
    return sorted({p.category for p in PREFABS.values()})


# --------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------- #
def apply_prefab(battle, prefab: Prefab, anchor_x: int, anchor_y: int,
                  *, replace_existing: bool = False) -> int:
    """Drop ``prefab`` onto ``battle.terrain`` so its (0,0) sits at
    (anchor_x, anchor_y).

    Returns the number of tiles placed. If ``replace_existing`` is
    True, any pre-existing terrain tile that occupies the same cell as
    a prefab tile is removed first."""
    placed = 0
    new_tiles = []
    occupied = {(int(anchor_x + t.dx), int(anchor_y + t.dy))
                for t in prefab.tiles}
    if replace_existing:
        battle.terrain[:] = [
            t for t in battle.terrain
            if (int(t.grid_x), int(t.grid_y)) not in occupied
        ]
    for tile in prefab.tiles:
        new_tiles.append(tile.to_terrain(anchor_x, anchor_y))
        placed += 1
    battle.terrain.extend(new_tiles)
    return placed


def prefab_footprint(prefab: Prefab) -> Tuple[int, int]:
    """Bounding (width, height) of the prefab in cells. 0x0 for empty."""
    return prefab.footprint
