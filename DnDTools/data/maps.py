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

    # ================================================================
    # NEW TACTICAL MAPS
    # ================================================================

    "underdark_cavern": {
        "name": "Underdark Cavern",
        "description": "A vast Underdark cave with giant mushrooms, crystal formations, "
                       "web-choked passages, and a chasm spanned by a natural stone bridge.",
        "terrain": [
            # Irregular cavern walls
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 0} for x in range(22)],
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 17} for x in range(22)],
            *[{"terrain_type": "rock", "grid_x": 0, "grid_y": y} for y in range(18)],
            *[{"terrain_type": "rock", "grid_x": 21, "grid_y": y} for y in range(18)],
            # Extra wall protrusions for irregular shape
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 20, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 16},
            {"terrain_type": "rock", "grid_x": 20, "grid_y": 16},
            {"terrain_type": "rock", "grid_x": 5, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 16, "grid_y": 1},
            # Giant mushroom forest (upper-left)
            {"terrain_type": "mushroom_giant", "grid_x": 3, "grid_y": 3},
            {"terrain_type": "mushroom_giant", "grid_x": 5, "grid_y": 5},
            {"terrain_type": "mushroom_giant", "grid_x": 2, "grid_y": 6},
            {"terrain_type": "mushroom_patch", "grid_x": 3, "grid_y": 4},
            {"terrain_type": "mushroom_patch", "grid_x": 4, "grid_y": 4},
            {"terrain_type": "mushroom_patch", "grid_x": 4, "grid_y": 5},
            {"terrain_type": "mushroom_patch", "grid_x": 3, "grid_y": 6},
            # Crystal formations (center-right)
            {"terrain_type": "crystal", "grid_x": 15, "grid_y": 7},
            {"terrain_type": "crystal", "grid_x": 16, "grid_y": 6},
            {"terrain_type": "crystal", "grid_x": 16, "grid_y": 8},
            {"terrain_type": "crystal", "grid_x": 17, "grid_y": 7},
            # Web-choked passage (upper-right)
            *[{"terrain_type": "web", "grid_x": x, "grid_y": y}
              for x in range(17, 20) for y in range(2, 5)],
            # Deep chasm running through center
            *[{"terrain_type": "chasm", "grid_x": 10, "grid_y": y} for y in range(2, 16)
              if y not in (8, 9)],
            *[{"terrain_type": "chasm", "grid_x": 11, "grid_y": y} for y in range(2, 16)
              if y not in (8, 9)],
            # Natural stone bridge across chasm
            {"terrain_type": "bridge", "grid_x": 10, "grid_y": 8},
            {"terrain_type": "bridge", "grid_x": 11, "grid_y": 8},
            {"terrain_type": "bridge", "grid_x": 10, "grid_y": 9},
            {"terrain_type": "bridge", "grid_x": 11, "grid_y": 9},
            # Stalactite columns
            {"terrain_type": "stalactite", "grid_x": 7, "grid_y": 4},
            {"terrain_type": "stalactite", "grid_x": 14, "grid_y": 12},
            {"terrain_type": "stalactite", "grid_x": 8, "grid_y": 13},
            # Elevated shelf (left side, above mushroom forest)
            *[{"terrain_type": "platform_10", "grid_x": x, "grid_y": y}
              for x in range(1, 4) for y in range(9, 12)],
            {"terrain_type": "stairs_up", "grid_x": 4, "grid_y": 10},
            # Underground pool
            {"terrain_type": "deep_water", "grid_x": 14, "grid_y": 14},
            {"terrain_type": "deep_water", "grid_x": 15, "grid_y": 14},
            {"terrain_type": "deep_water", "grid_x": 14, "grid_y": 15},
            {"terrain_type": "deep_water", "grid_x": 15, "grid_y": 15},
            {"terrain_type": "water", "grid_x": 13, "grid_y": 14},
            {"terrain_type": "water", "grid_x": 16, "grid_y": 15},
            # Poison gas pocket
            {"terrain_type": "poison", "grid_x": 18, "grid_y": 10},
            {"terrain_type": "poison", "grid_x": 18, "grid_y": 11},
            {"terrain_type": "poison", "grid_x": 19, "grid_y": 10},
            # Darkness zones
            {"terrain_type": "darkness", "grid_x": 7, "grid_y": 14},
            {"terrain_type": "darkness", "grid_x": 7, "grid_y": 15},
            {"terrain_type": "darkness", "grid_x": 8, "grid_y": 14},
            {"terrain_type": "darkness", "grid_x": 8, "grid_y": 15},
            # Moss near water
            {"terrain_type": "moss", "grid_x": 13, "grid_y": 13},
            {"terrain_type": "moss", "grid_x": 16, "grid_y": 14},
        ],
        "spawn_zones": {
            "players": [(2, 4), (3, 5), (4, 3), (5, 4), (2, 5), (3, 3)],
            "enemies": [(15, 3), (16, 3), (18, 3), (19, 5), (17, 5), (15, 5)],
        },
    },

    "sunken_temple": {
        "name": "Sunken Temple",
        "description": "An ancient temple half-submerged in water. Central altar, flooded chambers, "
                       "collapsed pillars, and a raised sanctum with magical wards.",
        "terrain": [
            # Temple outer walls
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(20)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 15} for x in range(20)],
            *[{"terrain_type": "wall", "grid_x": 0, "grid_y": y} for y in range(16)],
            *[{"terrain_type": "wall", "grid_x": 19, "grid_y": y} for y in range(16)],
            # Main entrance (south)
            {"terrain_type": "door", "grid_x": 9, "grid_y": 15},
            {"terrain_type": "door", "grid_x": 10, "grid_y": 15},
            # Inner walls creating rooms
            *[{"terrain_type": "wall", "grid_x": 6, "grid_y": y} for y in range(1, 6)],
            *[{"terrain_type": "wall", "grid_x": 13, "grid_y": y} for y in range(1, 6)],
            *[{"terrain_type": "wall", "grid_x": 6, "grid_y": y} for y in range(10, 15)],
            *[{"terrain_type": "wall", "grid_x": 13, "grid_y": y} for y in range(10, 15)],
            # Doors into side chambers
            {"terrain_type": "door", "grid_x": 6, "grid_y": 3},
            {"terrain_type": "door", "grid_x": 13, "grid_y": 3},
            {"terrain_type": "door", "grid_x": 6, "grid_y": 12},
            {"terrain_type": "door", "grid_x": 13, "grid_y": 12},
            # Central altar (raised sanctum)
            {"terrain_type": "altar", "grid_x": 9, "grid_y": 5},
            {"terrain_type": "altar", "grid_x": 10, "grid_y": 5},
            # Elevated sanctum platform
            *[{"terrain_type": "platform_5", "grid_x": x, "grid_y": y}
              for x in range(8, 12) for y in range(4, 7)],
            {"terrain_type": "stairs_up", "grid_x": 8, "grid_y": 7},
            {"terrain_type": "stairs_up", "grid_x": 11, "grid_y": 7},
            # Pillars lining main hall
            {"terrain_type": "pillar", "grid_x": 8, "grid_y": 9},
            {"terrain_type": "pillar", "grid_x": 11, "grid_y": 9},
            {"terrain_type": "pillar", "grid_x": 8, "grid_y": 12},
            {"terrain_type": "pillar", "grid_x": 11, "grid_y": 12},
            # Flooded chambers (left side)
            *[{"terrain_type": "water", "grid_x": x, "grid_y": y}
              for x in range(1, 6) for y in range(1, 5)],
            {"terrain_type": "deep_water", "grid_x": 2, "grid_y": 2},
            {"terrain_type": "deep_water", "grid_x": 3, "grid_y": 3},
            # Flooded chambers (right side)
            *[{"terrain_type": "water", "grid_x": x, "grid_y": y}
              for x in range(14, 19) for y in range(1, 5)],
            {"terrain_type": "deep_water", "grid_x": 16, "grid_y": 2},
            {"terrain_type": "deep_water", "grid_x": 17, "grid_y": 3},
            # Magical wards
            {"terrain_type": "magic_circle", "grid_x": 9, "grid_y": 4},
            {"terrain_type": "magic_circle", "grid_x": 10, "grid_y": 4},
            {"terrain_type": "leyline", "grid_x": 9, "grid_y": 6},
            {"terrain_type": "leyline", "grid_x": 10, "grid_y": 6},
            # Collapsed section (rubble + difficult)
            {"terrain_type": "rubble", "grid_x": 2, "grid_y": 11},
            {"terrain_type": "rubble", "grid_x": 3, "grid_y": 11},
            {"terrain_type": "rubble", "grid_x": 2, "grid_y": 12},
            {"terrain_type": "rubble", "grid_x": 3, "grid_y": 12},
            # Statues flanking altar
            {"terrain_type": "statue", "grid_x": 7, "grid_y": 5},
            {"terrain_type": "statue", "grid_x": 12, "grid_y": 5},
            # Sarcophagi in side rooms
            {"terrain_type": "sarcophagus", "grid_x": 3, "grid_y": 13},
            {"terrain_type": "sarcophagus", "grid_x": 16, "grid_y": 13},
            # Fog in lower temple
            {"terrain_type": "fog_light", "grid_x": 8, "grid_y": 13},
            {"terrain_type": "fog_light", "grid_x": 9, "grid_y": 14},
            {"terrain_type": "fog_light", "grid_x": 10, "grid_y": 13},
            {"terrain_type": "fog_light", "grid_x": 11, "grid_y": 14},
        ],
        "spawn_zones": {
            "players": [(8, 13), (9, 13), (10, 13), (11, 13), (9, 14), (10, 14)],
            "enemies": [(9, 5), (10, 5), (3, 2), (16, 2), (9, 2), (10, 2)],
        },
    },

    "shipwreck_shore": {
        "name": "Shipwreck Shore",
        "description": "A storm-wrecked ship on a rocky coastline. Half the ship is on sand, "
                       "half in shallow water. Masts, debris, and coral provide cover.",
        "terrain": [
            # Water (upper portion = ocean)
            *[{"terrain_type": "water", "grid_x": x, "grid_y": y}
              for x in range(20) for y in range(0, 4)],
            *[{"terrain_type": "deep_water", "grid_x": x, "grid_y": y}
              for x in range(20) for y in range(0, 2)],
            # Coral reef in shallows
            {"terrain_type": "coral", "grid_x": 3, "grid_y": 3},
            {"terrain_type": "coral", "grid_x": 6, "grid_y": 2},
            {"terrain_type": "coral", "grid_x": 14, "grid_y": 3},
            {"terrain_type": "coral", "grid_x": 17, "grid_y": 2},
            # Beach sand
            *[{"terrain_type": "sand", "grid_x": x, "grid_y": 4} for x in range(20)],
            *[{"terrain_type": "sand", "grid_x": x, "grid_y": 5} for x in range(20)],
            # Ship hull (main body, diagonal across beach)
            # Left hull wall
            *[{"terrain_type": "wall", "grid_x": 4, "grid_y": y} for y in range(5, 14)],
            # Right hull wall
            *[{"terrain_type": "wall", "grid_x": 15, "grid_y": y} for y in range(5, 14)],
            # Bow (in water)
            {"terrain_type": "wall", "grid_x": 5, "grid_y": 4},
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 4},
            {"terrain_type": "wall", "grid_x": 6, "grid_y": 3},
            {"terrain_type": "wall", "grid_x": 13, "grid_y": 3},
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 3} for x in range(7, 13)],
            # Stern (on beach)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 14} for x in range(5, 15)],
            # Ship interior: shipwreck debris
            {"terrain_type": "shipwreck", "grid_x": 6, "grid_y": 6},
            {"terrain_type": "shipwreck", "grid_x": 7, "grid_y": 6},
            {"terrain_type": "shipwreck", "grid_x": 12, "grid_y": 7},
            {"terrain_type": "shipwreck", "grid_x": 13, "grid_y": 7},
            {"terrain_type": "shipwreck", "grid_x": 8, "grid_y": 12},
            {"terrain_type": "shipwreck", "grid_x": 11, "grid_y": 12},
            # Masts (climbable to elevation)
            {"terrain_type": "mast", "grid_x": 9, "grid_y": 6},
            {"terrain_type": "mast", "grid_x": 10, "grid_y": 10},
            # Interior dividers (broken walls)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 9} for x in [5, 6, 13, 14]],
            {"terrain_type": "door", "grid_x": 7, "grid_y": 9},
            {"terrain_type": "door", "grid_x": 12, "grid_y": 9},
            # Cargo (crates and barrels for cover)
            {"terrain_type": "crate", "grid_x": 5, "grid_y": 10},
            {"terrain_type": "crate", "grid_x": 6, "grid_y": 11},
            {"terrain_type": "barrel", "grid_x": 13, "grid_y": 11},
            {"terrain_type": "barrel", "grid_x": 14, "grid_y": 10},
            # Hole in hull (water leaking in)
            {"terrain_type": "water", "grid_x": 5, "grid_y": 7},
            {"terrain_type": "water", "grid_x": 5, "grid_y": 8},
            # Captain's quarters (back room elevated)
            *[{"terrain_type": "platform_5", "grid_x": x, "grid_y": y}
              for x in range(7, 13) for y in range(11, 14)],
            {"terrain_type": "stairs_up", "grid_x": 7, "grid_y": 10},
            {"terrain_type": "table", "grid_x": 9, "grid_y": 12},
            {"terrain_type": "table", "grid_x": 10, "grid_y": 12},
            # Outside ship: rocks on beach
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 8},
            {"terrain_type": "rock", "grid_x": 18, "grid_y": 10},
            {"terrain_type": "rock", "grid_x": 2, "grid_y": 12},
        ],
        "spawn_zones": {
            "players": [(8, 5), (9, 5), (10, 5), (11, 5), (8, 6), (11, 6)],
            "enemies": [(8, 12), (9, 12), (10, 12), (11, 12), (8, 13), (11, 13)],
        },
    },

    "haunted_graveyard": {
        "name": "Haunted Graveyard",
        "description": "A fog-shrouded graveyard with tombstones, open graves, a mausoleum, "
                       "and a ruined chapel. Darkness clings to the crypts.",
        "terrain": [
            # Iron fence border
            *[{"terrain_type": "cage", "grid_x": x, "grid_y": 0} for x in range(18)],
            *[{"terrain_type": "cage", "grid_x": x, "grid_y": 15} for x in range(18)],
            *[{"terrain_type": "cage", "grid_x": 0, "grid_y": y} for y in range(16)],
            *[{"terrain_type": "cage", "grid_x": 17, "grid_y": y} for y in range(16)],
            # Gate entrance
            {"terrain_type": "portcullis", "grid_x": 8, "grid_y": 15},
            {"terrain_type": "portcullis", "grid_x": 9, "grid_y": 15},
            # Tombstone rows (east)
            *[{"terrain_type": "tombstone", "grid_x": 12, "grid_y": y} for y in range(3, 13, 2)],
            *[{"terrain_type": "tombstone", "grid_x": 14, "grid_y": y} for y in range(4, 12, 2)],
            # Tombstone rows (west)
            *[{"terrain_type": "tombstone", "grid_x": 3, "grid_y": y} for y in range(3, 13, 2)],
            *[{"terrain_type": "tombstone", "grid_x": 5, "grid_y": y} for y in range(4, 12, 2)],
            # Open graves
            {"terrain_type": "grave_open", "grid_x": 4, "grid_y": 5},
            {"terrain_type": "grave_open", "grid_x": 13, "grid_y": 7},
            {"terrain_type": "grave_open", "grid_x": 4, "grid_y": 11},
            # Mausoleum (center-north, stone building)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": y}
              for x in range(7, 11) for y in range(1, 4)
              if not (x in (8, 9) and y == 3)],
            {"terrain_type": "door", "grid_x": 8, "grid_y": 3},
            {"terrain_type": "door", "grid_x": 9, "grid_y": 3},
            # Sarcophagi inside mausoleum
            {"terrain_type": "sarcophagus", "grid_x": 8, "grid_y": 2},
            {"terrain_type": "sarcophagus", "grid_x": 9, "grid_y": 2},
            # Ruined chapel (south-east)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 10} for x in range(14, 17)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 14} for x in range(14, 17)],
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 11},
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 12},
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 13},
            {"terrain_type": "wall", "grid_x": 16, "grid_y": 11},
            {"terrain_type": "wall", "grid_x": 16, "grid_y": 13},
            {"terrain_type": "door", "grid_x": 16, "grid_y": 12},
            {"terrain_type": "altar", "grid_x": 15, "grid_y": 11},
            # Fog throughout
            *[{"terrain_type": "fog", "grid_x": x, "grid_y": y}
              for x, y in [(6, 6), (7, 7), (8, 6), (9, 7), (10, 6), (11, 7)]],
            # Light fog (wider area)
            *[{"terrain_type": "fog_light", "grid_x": x, "grid_y": y}
              for x, y in [(6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5),
                           (6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (11, 8)]],
            # Darkness in crypts
            {"terrain_type": "darkness", "grid_x": 8, "grid_y": 1},
            {"terrain_type": "darkness", "grid_x": 9, "grid_y": 1},
            # Large dead tree
            {"terrain_type": "tree", "grid_x": 8, "grid_y": 10},
            {"terrain_type": "tree", "grid_x": 2, "grid_y": 8},
            # Braziers at gate
            {"terrain_type": "brazier", "grid_x": 7, "grid_y": 14},
            {"terrain_type": "brazier", "grid_x": 10, "grid_y": 14},
        ],
        "spawn_zones": {
            "players": [(7, 13), (8, 13), (9, 13), (10, 13), (7, 12), (10, 12)],
            "enemies": [(8, 2), (9, 2), (3, 5), (14, 5), (5, 9), (12, 9)],
        },
    },

    "gladiator_arena": {
        "name": "Gladiator Arena",
        "description": "A grand colosseum arena with a central pit, elevated spectator platforms, "
                       "cage doors releasing monsters, and scattered weapons on racks.",
        "terrain": [
            # Arena walls (roughly oval/octagonal)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(4, 16)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 15} for x in range(4, 16)],
            {"terrain_type": "wall", "grid_x": 3, "grid_y": 1}, {"terrain_type": "wall", "grid_x": 16, "grid_y": 1},
            {"terrain_type": "wall", "grid_x": 2, "grid_y": 2}, {"terrain_type": "wall", "grid_x": 17, "grid_y": 2},
            *[{"terrain_type": "wall", "grid_x": 1, "grid_y": y} for y in range(3, 13)],
            *[{"terrain_type": "wall", "grid_x": 18, "grid_y": y} for y in range(3, 13)],
            {"terrain_type": "wall", "grid_x": 2, "grid_y": 13}, {"terrain_type": "wall", "grid_x": 17, "grid_y": 13},
            {"terrain_type": "wall", "grid_x": 3, "grid_y": 14}, {"terrain_type": "wall", "grid_x": 16, "grid_y": 14},
            # Corner walls
            *[{"terrain_type": "wall", "grid_x": 0, "grid_y": y} for y in range(4, 12)],
            *[{"terrain_type": "wall", "grid_x": 19, "grid_y": y} for y in range(4, 12)],
            # Gate entrances (with portcullises for monster release)
            {"terrain_type": "portcullis", "grid_x": 9, "grid_y": 0},
            {"terrain_type": "portcullis", "grid_x": 10, "grid_y": 0},
            {"terrain_type": "portcullis", "grid_x": 9, "grid_y": 15},
            {"terrain_type": "portcullis", "grid_x": 10, "grid_y": 15},
            # Side gates
            {"terrain_type": "cage", "grid_x": 1, "grid_y": 7},
            {"terrain_type": "cage", "grid_x": 1, "grid_y": 8},
            {"terrain_type": "cage", "grid_x": 18, "grid_y": 7},
            {"terrain_type": "cage", "grid_x": 18, "grid_y": 8},
            # Central pit (sunken area)
            *[{"terrain_type": "pit", "grid_x": x, "grid_y": y}
              for x in range(8, 12) for y in range(6, 10)],
            # Spikes at bottom of pit
            {"terrain_type": "spikes", "grid_x": 9, "grid_y": 7},
            {"terrain_type": "spikes", "grid_x": 10, "grid_y": 8},
            # Elevated VIP platforms (corners)
            *[{"terrain_type": "platform_15", "grid_x": x, "grid_y": y}
              for x in range(2, 5) for y in range(2, 5)],
            {"terrain_type": "stairs_up", "grid_x": 5, "grid_y": 3},
            *[{"terrain_type": "platform_15", "grid_x": x, "grid_y": y}
              for x in range(15, 18) for y in range(2, 5)],
            {"terrain_type": "stairs_up", "grid_x": 14, "grid_y": 3},
            # Pillar obstacles
            {"terrain_type": "pillar", "grid_x": 5, "grid_y": 7},
            {"terrain_type": "pillar", "grid_x": 14, "grid_y": 7},
            {"terrain_type": "pillar", "grid_x": 5, "grid_y": 10},
            {"terrain_type": "pillar", "grid_x": 14, "grid_y": 10},
            {"terrain_type": "pillar", "grid_x": 7, "grid_y": 4},
            {"terrain_type": "pillar", "grid_x": 12, "grid_y": 4},
            {"terrain_type": "pillar", "grid_x": 7, "grid_y": 11},
            {"terrain_type": "pillar", "grid_x": 12, "grid_y": 11},
            # Sand on arena floor
            *[{"terrain_type": "sand", "grid_x": x, "grid_y": y}
              for x, y in [(6, 5), (13, 5), (6, 10), (13, 10)]],
            # Fire hazards (torch pits)
            {"terrain_type": "fire", "grid_x": 4, "grid_y": 7},
            {"terrain_type": "fire", "grid_x": 15, "grid_y": 8},
            # Braziers for atmosphere
            {"terrain_type": "brazier", "grid_x": 3, "grid_y": 1},
            {"terrain_type": "brazier", "grid_x": 16, "grid_y": 1},
            {"terrain_type": "brazier", "grid_x": 3, "grid_y": 14},
            {"terrain_type": "brazier", "grid_x": 16, "grid_y": 14},
            # Weapon racks (as tables/cover)
            {"terrain_type": "table", "grid_x": 6, "grid_y": 2},
            {"terrain_type": "table", "grid_x": 13, "grid_y": 13},
        ],
        "spawn_zones": {
            "players": [(8, 13), (9, 13), (10, 13), (11, 13)],
            "enemies": [(8, 2), (9, 2), (10, 2), (11, 2)],
        },
    },

    "volcanic_forge": {
        "name": "Volcanic Forge",
        "description": "A dwarven forge built into a volcano. Lava rivers, stone bridges, "
                       "anvil platforms, and mechanical elevators. Extreme heat hazards.",
        "terrain": [
            # Cavern walls
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 0} for x in range(22)],
            *[{"terrain_type": "rock", "grid_x": x, "grid_y": 15} for x in range(22)],
            *[{"terrain_type": "rock", "grid_x": 0, "grid_y": y} for y in range(16)],
            *[{"terrain_type": "rock", "grid_x": 21, "grid_y": y} for y in range(16)],
            # Extra wall protrusions
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 20, "grid_y": 1},
            {"terrain_type": "rock", "grid_x": 1, "grid_y": 14},
            {"terrain_type": "rock", "grid_x": 20, "grid_y": 14},
            # Lava rivers (flowing north-south)
            *[{"terrain_type": "lava", "grid_x": 7, "grid_y": y} for y in range(1, 15)
              if y not in (5, 6, 10, 11)],
            *[{"terrain_type": "lava", "grid_x": 14, "grid_y": y} for y in range(1, 15)
              if y not in (4, 5, 9, 10)],
            # Stone bridges over lava
            {"terrain_type": "bridge", "grid_x": 7, "grid_y": 5},
            {"terrain_type": "bridge", "grid_x": 7, "grid_y": 6},
            {"terrain_type": "bridge", "grid_x": 7, "grid_y": 10},
            {"terrain_type": "bridge", "grid_x": 7, "grid_y": 11},
            {"terrain_type": "bridge", "grid_x": 14, "grid_y": 4},
            {"terrain_type": "bridge", "grid_x": 14, "grid_y": 5},
            {"terrain_type": "bridge", "grid_x": 14, "grid_y": 9},
            {"terrain_type": "bridge", "grid_x": 14, "grid_y": 10},
            # Western forge (elevated workspace)
            *[{"terrain_type": "platform_10", "grid_x": x, "grid_y": y}
              for x in range(2, 6) for y in range(4, 8)],
            {"terrain_type": "stairs_up", "grid_x": 6, "grid_y": 5},
            {"terrain_type": "stairs_up", "grid_x": 6, "grid_y": 7},
            # Anvil and forge fire
            {"terrain_type": "altar", "grid_x": 3, "grid_y": 5},  # anvil
            {"terrain_type": "altar", "grid_x": 4, "grid_y": 5},  # anvil
            {"terrain_type": "fire", "grid_x": 3, "grid_y": 6},   # forge fire
            {"terrain_type": "fire", "grid_x": 4, "grid_y": 6},   # forge fire
            # Central island (between lava rivers)
            *[{"terrain_type": "platform_5", "grid_x": x, "grid_y": y}
              for x in range(9, 13) for y in range(6, 10)],
            # Eastern storage
            *[{"terrain_type": "crate", "grid_x": x, "grid_y": y}
              for x, y in [(16, 3), (17, 3), (16, 4), (17, 4)]],
            {"terrain_type": "barrel", "grid_x": 18, "grid_y": 5},
            {"terrain_type": "barrel", "grid_x": 19, "grid_y": 5},
            # Southern workshop
            *[{"terrain_type": "platform_5", "grid_x": x, "grid_y": y}
              for x in range(15, 20) for y in range(11, 14)],
            {"terrain_type": "stairs_up", "grid_x": 15, "grid_y": 10},
            {"terrain_type": "table", "grid_x": 17, "grid_y": 12},
            {"terrain_type": "table", "grid_x": 18, "grid_y": 12},
            # Northern elevated platform (overlooking lava)
            *[{"terrain_type": "platform_15", "grid_x": x, "grid_y": y}
              for x in range(9, 13) for y in range(1, 4)],
            {"terrain_type": "stairs_up", "grid_x": 8, "grid_y": 2},
            {"terrain_type": "stairs_up", "grid_x": 13, "grid_y": 2},
            # Cover: stalactites and pillars
            {"terrain_type": "stalactite", "grid_x": 5, "grid_y": 10},
            {"terrain_type": "stalactite", "grid_x": 16, "grid_y": 8},
            {"terrain_type": "pillar", "grid_x": 9, "grid_y": 5},
            {"terrain_type": "pillar", "grid_x": 12, "grid_y": 10},
            # Fire hazard squares near lava edges
            {"terrain_type": "fire", "grid_x": 6, "grid_y": 3},
            {"terrain_type": "fire", "grid_x": 8, "grid_y": 8},
            {"terrain_type": "fire", "grid_x": 13, "grid_y": 7},
            {"terrain_type": "fire", "grid_x": 15, "grid_y": 12},
        ],
        "spawn_zones": {
            "players": [(2, 5), (3, 5), (4, 5), (5, 5), (2, 6), (5, 6)],
            "enemies": [(16, 3), (17, 3), (18, 6), (19, 7), (16, 12), (17, 12)],
        },
    },

    "wizard_tower": {
        "name": "Wizard's Tower",
        "description": "A multi-level wizard's tower with a grand library, arcane laboratory, "
                       "teleport circles, and a rooftop observatory. Ley lines criss-cross the floors.",
        "terrain": [
            # Tower walls (circular-ish)
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 0} for x in range(2, 14)],
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 17} for x in range(2, 14)],
            *[{"terrain_type": "wall", "grid_x": 1, "grid_y": y} for y in range(1, 17)],
            *[{"terrain_type": "wall", "grid_x": 14, "grid_y": y} for y in range(1, 17)],
            # Rounded corners
            {"terrain_type": "wall", "grid_x": 1, "grid_y": 0},
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 0},
            {"terrain_type": "wall", "grid_x": 1, "grid_y": 17},
            {"terrain_type": "wall", "grid_x": 14, "grid_y": 17},
            # Main entrance
            {"terrain_type": "door", "grid_x": 7, "grid_y": 17},
            {"terrain_type": "door", "grid_x": 8, "grid_y": 17},
            # LEVEL 1 (ground floor) - Entry Hall & Library
            # Bookshelves
            {"terrain_type": "bookshelf", "grid_x": 2, "grid_y": 14},
            {"terrain_type": "bookshelf", "grid_x": 2, "grid_y": 15},
            {"terrain_type": "bookshelf", "grid_x": 13, "grid_y": 14},
            {"terrain_type": "bookshelf", "grid_x": 13, "grid_y": 15},
            {"terrain_type": "bookshelf", "grid_x": 4, "grid_y": 13},
            {"terrain_type": "bookshelf", "grid_x": 11, "grid_y": 13},
            # Reading tables
            {"terrain_type": "table", "grid_x": 6, "grid_y": 14},
            {"terrain_type": "table", "grid_x": 7, "grid_y": 14},
            {"terrain_type": "table", "grid_x": 8, "grid_y": 14},
            {"terrain_type": "table", "grid_x": 9, "grid_y": 14},
            # Floor divider wall with door
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 12}
              for x in range(2, 14) if x not in (7, 8)],
            {"terrain_type": "door", "grid_x": 7, "grid_y": 12},
            {"terrain_type": "door", "grid_x": 8, "grid_y": 12},
            # LEVEL 2 (middle) - Arcane Laboratory
            # Lab floor is elevated
            *[{"terrain_type": "platform_10", "grid_x": x, "grid_y": y}
              for x in range(2, 14) for y in range(6, 12)],
            # Stairs connecting levels
            {"terrain_type": "stairs_up", "grid_x": 3, "grid_y": 12},
            {"terrain_type": "stairs_up", "grid_x": 12, "grid_y": 12},
            # Lab equipment (alchemy tables)
            {"terrain_type": "table", "grid_x": 5, "grid_y": 8},
            {"terrain_type": "table", "grid_x": 6, "grid_y": 8},
            {"terrain_type": "table", "grid_x": 9, "grid_y": 8},
            {"terrain_type": "table", "grid_x": 10, "grid_y": 8},
            # Magical hazards
            {"terrain_type": "acid", "grid_x": 4, "grid_y": 9},
            {"terrain_type": "fire", "grid_x": 11, "grid_y": 9},
            # Crystal formations (magical energy)
            {"terrain_type": "crystal", "grid_x": 3, "grid_y": 7},
            {"terrain_type": "crystal", "grid_x": 12, "grid_y": 7},
            # Ley lines on lab floor
            {"terrain_type": "leyline", "grid_x": 7, "grid_y": 7},
            {"terrain_type": "leyline", "grid_x": 8, "grid_y": 7},
            {"terrain_type": "leyline", "grid_x": 7, "grid_y": 10},
            {"terrain_type": "leyline", "grid_x": 8, "grid_y": 10},
            # Divider wall level 2/3
            *[{"terrain_type": "wall", "grid_x": x, "grid_y": 5}
              for x in range(2, 14) if x not in (7, 8)],
            {"terrain_type": "door_locked", "grid_x": 7, "grid_y": 5},
            {"terrain_type": "door_locked", "grid_x": 8, "grid_y": 5},
            # LEVEL 3 (top) - Sanctum & Observatory
            *[{"terrain_type": "platform_20", "grid_x": x, "grid_y": y}
              for x in range(2, 14) for y in range(1, 5)],
            {"terrain_type": "stairs_up", "grid_x": 3, "grid_y": 5},
            {"terrain_type": "stairs_up", "grid_x": 12, "grid_y": 5},
            # Teleport circles
            {"terrain_type": "teleport_pad", "grid_x": 4, "grid_y": 2},
            {"terrain_type": "teleport_pad", "grid_x": 11, "grid_y": 2},
            # Teleport circle on ground floor too
            {"terrain_type": "teleport_pad", "grid_x": 4, "grid_y": 16},
            {"terrain_type": "teleport_pad", "grid_x": 11, "grid_y": 16},
            # Magic circle (throne room ward)
            {"terrain_type": "magic_circle", "grid_x": 7, "grid_y": 2},
            {"terrain_type": "magic_circle", "grid_x": 8, "grid_y": 2},
            {"terrain_type": "magic_circle", "grid_x": 7, "grid_y": 3},
            {"terrain_type": "magic_circle", "grid_x": 8, "grid_y": 3},
            # Throne
            {"terrain_type": "throne", "grid_x": 7, "grid_y": 1},
            {"terrain_type": "throne", "grid_x": 8, "grid_y": 1},
            # Antimagic field trap
            {"terrain_type": "antimagic", "grid_x": 6, "grid_y": 3},
            {"terrain_type": "antimagic", "grid_x": 9, "grid_y": 3},
            # Statues guarding sanctum
            {"terrain_type": "statue", "grid_x": 5, "grid_y": 1},
            {"terrain_type": "statue", "grid_x": 10, "grid_y": 1},
        ],
        "spawn_zones": {
            "players": [(5, 15), (6, 15), (7, 15), (8, 15), (9, 15), (10, 15)],
            "enemies": [(6, 2), (7, 2), (8, 2), (9, 2), (5, 3), (10, 3)],
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
