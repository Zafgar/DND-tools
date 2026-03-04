"""Premade battle maps for the D&D combat system.

Each map is a dict with:
  name: display name
  description: short description
  terrain: list of terrain dicts (TerrainObject.to_dict() format)
  spawn_zones: dict of team -> list of (x,y) positions
"""

PREMADE_MAPS = {
    "tavern_brawl": {
        "name": "Tavern Brawl",
        "description": "A rowdy tavern interior with tables, a bar, and two exits.",
        "terrain": [
            # Outer walls
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(16)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 11} for x in range(16)],
            *[{"terrain_type": "wall", "grid_x": 0, "grid_y": y} for y in range(12)],
            *[{"terrain_type": "wall", "grid_x": 15, "grid_y": y} for y in range(12)],
            # Front door
            {"terrain_type": "door", "grid_x": 7, "grid_y": 11},
            # Back door
            {"terrain_type": "door", "grid_x": 3, "grid_y": 0},
            # Bar counter (long table)
            *[{"terrain_type": "table", "grid_x": x, "grid_y": 3} for x in range(10, 14)],
            # Tables scattered
            {"terrain_type": "table", "grid_x": 3, "grid_y": 5},
            {"terrain_type": "table", "grid_x": 4, "grid_y": 5},
            {"terrain_type": "table", "grid_x": 3, "grid_y": 8},
            {"terrain_type": "table", "grid_x": 4, "grid_y": 8},
            {"terrain_type": "table", "grid_x": 7, "grid_y": 6},
            {"terrain_type": "table", "grid_x": 8, "grid_y": 6},
            # Barrels for cover
            {"terrain_type": "barrel", "grid_x": 12, "grid_y": 5},
            {"terrain_type": "barrel", "grid_x": 13, "grid_y": 8},
            # Fireplace
            {"terrain_type": "fire", "grid_x": 1, "grid_y": 5},
        ],
        "spawn_zones": {
            "players": [(2, 9), (3, 9), (4, 9), (5, 9)],
            "enemies": [(10, 5), (11, 5), (12, 7), (11, 8)],
        },
    },

    "dungeon_corridor": {
        "name": "Dungeon Corridor",
        "description": "A narrow dungeon passage with doors, a pit trap, and an elevated platform.",
        "terrain": [
            # Corridor walls (long narrow hallway)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(20)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 5} for x in range(20)],
            *[{"terrain_type": "wall", "grid_x": 0, "grid_y": y} for y in range(6)],
            *[{"terrain_type": "wall", "grid_x": 19, "grid_y": y} for y in range(6)],
            # Internal wall with door
            *[{"terrain_type": "wall", "grid_x": 8, "grid_y": y} for y in range(6) if y != 2 and y != 3],
            {"terrain_type": "door", "grid_x": 8, "grid_y": 2},
            {"terrain_type": "door", "grid_x": 8, "grid_y": 3},
            # Second wall with locked door
            *[{"terrain_type": "wall", "grid_x": 14, "grid_y": y} for y in range(6) if y != 3],
            {"terrain_type": "door_locked", "grid_x": 14, "grid_y": 3},
            # Spike pit trap
            {"terrain_type": "spikes", "grid_x": 5, "grid_y": 2},
            {"terrain_type": "spikes", "grid_x": 5, "grid_y": 3},
            # Elevated platform (end room)
            {"terrain_type": "platform_10", "grid_x": 16, "grid_y": 2},
            {"terrain_type": "platform_10", "grid_x": 17, "grid_y": 2},
            {"terrain_type": "stairs_up", "grid_x": 15, "grid_y": 2},
            # Cover in main room
            {"terrain_type": "pillar", "grid_x": 10, "grid_y": 2},
            {"terrain_type": "pillar", "grid_x": 12, "grid_y": 3},
        ],
        "spawn_zones": {
            "players": [(1, 2), (1, 3), (2, 2), (2, 3)],
            "enemies": [(16, 2), (17, 2), (17, 3), (10, 3)],
        },
    },

    "castle_courtyard": {
        "name": "Castle Courtyard",
        "description": "An open courtyard with walls, battlements, a gate, and elevated towers.",
        "terrain": [
            # Outer castle walls
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(18)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 15} for x in range(18)],
            *[{"terrain_type": "wall", "grid_x": 0, "grid_y": y} for y in range(16)],
            *[{"terrain_type": "wall", "grid_x": 17, "grid_y": y} for y in range(16)],
            # Main gate (south)
            {"terrain_type": "door", "grid_x": 8, "grid_y": 15},
            {"terrain_type": "door", "grid_x": 9, "grid_y": 15},
            # Corner towers (elevated platforms)
            {"terrain_type": "platform_20", "grid_x": 1, "grid_y": 1},
            {"terrain_type": "platform_20", "grid_x": 16, "grid_y": 1},
            {"terrain_type": "platform_20", "grid_x": 1, "grid_y": 14},
            {"terrain_type": "platform_20", "grid_x": 16, "grid_y": 14},
            # Ladders to towers
            {"terrain_type": "ladder", "grid_x": 2, "grid_y": 1},
            {"terrain_type": "ladder", "grid_x": 15, "grid_y": 1},
            {"terrain_type": "ladder", "grid_x": 2, "grid_y": 14},
            {"terrain_type": "ladder", "grid_x": 15, "grid_y": 14},
            # Battlements (3/4 cover)
            *[{"terrain_type": "cover_3q", "grid_x": x, "grid_y": 1} for x in range(3, 16)],
            # Central fountain (difficult terrain)
            {"terrain_type": "water", "grid_x": 8, "grid_y": 7},
            {"terrain_type": "water", "grid_x": 9, "grid_y": 7},
            {"terrain_type": "water", "grid_x": 8, "grid_y": 8},
            {"terrain_type": "water", "grid_x": 9, "grid_y": 8},
            # Cover objects
            {"terrain_type": "barrel", "grid_x": 4, "grid_y": 5},
            {"terrain_type": "crate", "grid_x": 13, "grid_y": 5},
            {"terrain_type": "crate", "grid_x": 5, "grid_y": 11},
            {"terrain_type": "barrel", "grid_x": 12, "grid_y": 11},
            # Inside building door
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 3} for x in range(5, 13) if x != 8],
            {"terrain_type": "door", "grid_x": 8, "grid_y": 3},
        ],
        "spawn_zones": {
            "players": [(7, 13), (8, 13), (9, 13), (10, 13)],
            "enemies": [(7, 4), (8, 4), (9, 4), (10, 4), (1, 1), (16, 1)],
        },
    },

    "forest_clearing": {
        "name": "Forest Clearing",
        "description": "A woodland clearing surrounded by trees with rocky outcrops.",
        "terrain": [
            # Dense tree border
            *[{"terrain_type": "tree", "grid_x": x, "grid_y": 0} for x in range(0, 16, 2)],
            *[{"terrain_type": "tree", "grid_x": x, "grid_y": 11} for x in range(0, 16, 2)],
            *[{"terrain_type": "tree", "grid_x": 0, "grid_y": y} for y in range(0, 12, 2)],
            *[{"terrain_type": "tree", "grid_x": 15, "grid_y": y} for y in range(0, 12, 2)],
            # Interior trees
            {"terrain_type": "tree", "grid_x": 4, "grid_y": 3},
            {"terrain_type": "tree", "grid_x": 11, "grid_y": 4},
            {"terrain_type": "tree", "grid_x": 6, "grid_y": 8},
            {"terrain_type": "tree", "grid_x": 13, "grid_y": 7},
            # Rocky outcrops (climbable, elevated)
            {"terrain_type": "rock", "grid_x": 8, "grid_y": 5},
            {"terrain_type": "platform_5", "grid_x": 9, "grid_y": 5},
            # Stream (difficult terrain)
            *[{"terrain_type": "water", "grid_x": 3, "grid_y": y} for y in range(4, 9)],
            # Bridge over stream
            {"terrain_type": "bridge", "grid_x": 3, "grid_y": 6},
            # Difficult underbrush
            {"terrain_type": "difficult", "grid_x": 5, "grid_y": 4},
            {"terrain_type": "difficult", "grid_x": 5, "grid_y": 5},
            {"terrain_type": "difficult", "grid_x": 10, "grid_y": 7},
            {"terrain_type": "difficult", "grid_x": 10, "grid_y": 8},
        ],
        "spawn_zones": {
            "players": [(2, 5), (2, 6), (2, 7), (2, 8)],
            "enemies": [(12, 3), (13, 3), (12, 8), (13, 8)],
        },
    },

    "cliffside_battle": {
        "name": "Cliffside Battle",
        "description": "A multi-level cliff with bridges, chasms, and deadly drops.",
        "terrain": [
            # Ground level (left side)
            # Chasm down the middle
            *[{"terrain_type": "chasm", "grid_x": 7, "grid_y": y} for y in range(12)],
            *[{"terrain_type": "chasm", "grid_x": 8, "grid_y": y} for y in range(12)
              if y != 5 and y != 6],
            # Bridge across chasm
            {"terrain_type": "bridge", "grid_x": 8, "grid_y": 5},
            {"terrain_type": "bridge", "grid_x": 8, "grid_y": 6},
            # Left cliff: elevated platforms
            *[{"terrain_type": "platform_10", "grid_x": x, "grid_y": y}
              for x in range(0, 3) for y in range(0, 4)],
            {"terrain_type": "stairs_down", "grid_x": 3, "grid_y": 2},
            # Right cliff: higher elevation
            *[{"terrain_type": "platform_20", "grid_x": x, "grid_y": y}
              for x in range(12, 15) for y in range(0, 4)],
            {"terrain_type": "stairs_down", "grid_x": 11, "grid_y": 2},
            {"terrain_type": "ladder", "grid_x": 12, "grid_y": 4},
            # Rocks for cover
            {"terrain_type": "rock", "grid_x": 4, "grid_y": 3},
            {"terrain_type": "rock", "grid_x": 5, "grid_y": 7},
            {"terrain_type": "rock", "grid_x": 10, "grid_y": 5},
            {"terrain_type": "rock", "grid_x": 11, "grid_y": 9},
            # Cover at cliff edges
            {"terrain_type": "cover_3q", "grid_x": 6, "grid_y": 4},
            {"terrain_type": "cover_3q", "grid_x": 9, "grid_y": 7},
        ],
        "spawn_zones": {
            "players": [(1, 1), (2, 1), (1, 2), (2, 2)],
            "enemies": [(13, 1), (14, 1), (13, 2), (14, 2)],
        },
    },

    "dragon_lair": {
        "name": "Dragon's Lair",
        "description": "A vast cavern with lava pools, treasure hoard, and elevated perches.",
        "terrain": [
            # Cavern walls (irregular shape)
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 0} for x in range(20)],
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 14} for x in range(20)],
            *[{"terrain_type": "rock", "grid_x": 0, "grid_y": y} for y in range(15)],
            *[{"terrain_type": "rock", "grid_x": 19, "grid_y": y} for y in range(15)],
            # Extra rock formations
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 18, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 13},
            {"terrain_type": "rock", "grid_x": 18, "grid_y": 13},
            # Lava pools
            *[{"terrain_type": "lava", "grid_x": x, "grid_y": y}
              for x in range(6, 9) for y in range(4, 7)],
            *[{"terrain_type": "lava", "grid_x": x, "grid_y": y}
              for x in range(12, 15) for y in range(8, 11)],
            # Elevated dragon perch (back of cave)
            *[{"terrain_type": "platform_15", "grid_x": x, "grid_y": y}
              for x in range(8, 13) for y in range(1, 4)],
            {"terrain_type": "stairs_up", "grid_x": 8, "grid_y": 4},
            {"terrain_type": "stairs_up", "grid_x": 12, "grid_y": 4},
            # Stalactites (pillars providing cover)
            {"terrain_type": "pillar", "grid_x": 4, "grid_y": 6},
            {"terrain_type": "pillar", "grid_x": 15, "grid_y": 5},
            {"terrain_type": "pillar", "grid_x": 5, "grid_y": 10},
            {"terrain_type": "pillar", "grid_x": 16, "grid_y": 10},
            # Treasure hoard (difficult terrain from gold piles)
            *[{"terrain_type": "difficult", "grid_x": x, "grid_y": y}
              for x in range(9, 12) for y in range(2, 4)],
            # Narrow bridge over lava
            {"terrain_type": "bridge", "grid_x": 9, "grid_y": 5},
            {"terrain_type": "bridge", "grid_x": 10, "grid_y": 5},
        ],
        "spawn_zones": {
            "players": [(3, 11), (4, 11), (5, 11), (3, 12)],
            "enemies": [(10, 2)],  # Dragon on perch
        },
    },
}


def get_map_names():
    """Return list of (key, name, description) for all premade maps."""
    return [(k, v["name"], v["description"]) for k, v in PREMADE_MAPS.items()]


def load_map_terrain(map_key: str) -> list:
    """Return list of TerrainObject dicts for a premade map."""
    from engine.terrain import TerrainObject
    map_data = PREMADE_MAPS.get(map_key)
    if not map_data:
        return []
    return [TerrainObject.from_dict(t) for t in map_data["terrain"]]


def get_spawn_zones(map_key: str) -> dict:
    """Get spawn positions for a map."""
    map_data = PREMADE_MAPS.get(map_key)
    if not map_data:
        return {}
    return map_data.get("spawn_zones", {})
