"""Ready-made battle scenarios — categorized, with terrain layouts and
monster placements. A DM can pick one from a list and jump straight into
combat; the PCs are placed in the scenario's designated party spawn cells
during the usual deployment phase.

Scenarios cover seven categories:
  * bandit_lair — outdoor ambushes and hideouts
  * dungeon    — humanoid-held corridors and rooms
  * cave       — natural caverns, low light
  * underwater — swamp / shallow / deep water
  * outdoor    — wilderness, forests, plains
  * urban      — city, temple, rooftop
  * planar     — infernal / elemental / abyssal sites

Each scenario is pure data, so adding/editing is trivial. The loader
``build_battle_from_scenario`` wires a ``BattleSystem`` with terrain,
monsters (drawn from ``data.library``), ceiling, weather, and optional
JPG background. Party members are not spawned here — the existing
deployment phase places them on the scenario's ``party_spawns`` cells.
"""
import json
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Callable, Dict, Optional


CATEGORIES = (
    "bandit_lair",
    "dungeon",
    "cave",
    "underwater",
    "outdoor",
    "urban",
    "planar",
)


@dataclass
class ScenarioTile:
    terrain_type: str
    x: int
    y: int
    w: int = 1
    h: int = 1
    elevation: int = -1   # -1 = use type default


@dataclass
class ScenarioMonster:
    name: str             # must match library.get_monster()
    x: int
    y: int
    team: str = "Red"     # for multi-team combat


@dataclass
class Scenario:
    id: str
    name: str
    category: str
    description: str
    recommended_party_size: int = 4
    recommended_level_min: int = 1
    recommended_level_max: int = 5
    weather: str = "Clear"
    ceiling_ft: int = 0
    background_image_path: str = ""
    tags: Tuple[str, ...] = ()
    tiles: List[ScenarioTile] = field(default_factory=list)
    monsters: List[ScenarioMonster] = field(default_factory=list)
    party_spawns: List[Tuple[int, int]] = field(default_factory=list)
    lair_enabled: bool = False


# --------------------------------------------------------------------- #
# Tile helpers (to keep the big SCENARIOS list readable)
# --------------------------------------------------------------------- #
def _walls_rect(x: int, y: int, w: int, h: int) -> List[ScenarioTile]:
    """Hollow rectangle of walls (outline only)."""
    tiles: List[ScenarioTile] = []
    for gx in range(x, x + w):
        tiles.append(ScenarioTile("wall", gx, y))
        tiles.append(ScenarioTile("wall", gx, y + h - 1))
    for gy in range(y + 1, y + h - 1):
        tiles.append(ScenarioTile("wall", x, gy))
        tiles.append(ScenarioTile("wall", x + w - 1, gy))
    return tiles


def _line(terrain: str, x1: int, y1: int, x2: int, y2: int) -> List[ScenarioTile]:
    tiles: List[ScenarioTile] = []
    if x1 == x2:
        for gy in range(min(y1, y2), max(y1, y2) + 1):
            tiles.append(ScenarioTile(terrain, x1, gy))
    elif y1 == y2:
        for gx in range(min(x1, x2), max(x1, x2) + 1):
            tiles.append(ScenarioTile(terrain, gx, y1))
    return tiles


def _scatter(terrain: str, positions: List[Tuple[int, int]]) -> List[ScenarioTile]:
    return [ScenarioTile(terrain, x, y) for x, y in positions]


# --------------------------------------------------------------------- #
# SCENARIO CATALOG
# --------------------------------------------------------------------- #
_PARTY_WEST = [(2, 5), (2, 7), (2, 9), (2, 11)]

SCENARIOS: List[Scenario] = [
    # ============= BANDIT LAIR =============
    Scenario(
        id="bandit_crossroads",
        name="Crossroads Ambush",
        category="bandit_lair",
        description="A small bandit crew waits behind roadside trees and "
                    "rocks at a rural crossroads. Cover on both sides.",
        recommended_level_min=1, recommended_level_max=3,
        tags=("outdoor", "ambush", "cover"),
        tiles=_scatter("tree", [(10, 3), (11, 4), (16, 3), (17, 12),
                                  (18, 11), (10, 13), (11, 12)])
              + _scatter("rock", [(13, 6), (14, 9), (15, 6), (16, 8)])
              + _scatter("difficult", [(13, 8), (14, 7), (15, 8)]),
        monsters=[
            ScenarioMonster("Bandit", 18, 5),
            ScenarioMonster("Bandit", 18, 7),
            ScenarioMonster("Bandit", 19, 9),
            ScenarioMonster("Bandit", 20, 8),
            ScenarioMonster("Thug", 22, 7),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="bandit_hideout_cliffside",
        name="Cliffside Hideout",
        category="bandit_lair",
        description="A bandit camp perched on a low plateau, with a "
                    "20-foot drop-off on the south side.",
        recommended_level_min=2, recommended_level_max=4,
        tags=("outdoor", "elevation", "fall_risk"),
        tiles=[ScenarioTile("platform_20", x, y)
               for x in range(14, 22) for y in range(4, 8)]
              + _scatter("chasm_20", [(14, 9), (15, 9), (16, 9), (17, 9),
                                       (18, 9), (19, 9), (20, 9)])
              + _scatter("barrel", [(16, 5), (20, 6)])
              + _scatter("crate", [(17, 5), (19, 6)]),
        monsters=[
            ScenarioMonster("Bandit", 15, 5),
            ScenarioMonster("Bandit", 16, 6),
            ScenarioMonster("Bandit", 19, 5),
            ScenarioMonster("Thug", 20, 7),
            ScenarioMonster("Scout", 18, 4),
        ],
        party_spawns=[(2, 5), (2, 7), (2, 9), (3, 11)],
    ),

    # ============= DUNGEON =============
    Scenario(
        id="goblin_warrens",
        name="Goblin Warrens",
        category="dungeon",
        description="Narrow tunnels with a 10-foot ceiling; goblins "
                    "swarm from every angle, led by a boss and a worg.",
        recommended_level_min=2, recommended_level_max=4,
        ceiling_ft=10,
        tags=("indoor", "low_ceiling", "swarm"),
        tiles=_walls_rect(0, 2, 28, 13)
              + _scatter("rubble", [(10, 5), (11, 7), (15, 9), (20, 6)])
              + _line("wall", 12, 2, 12, 6)
              + _line("wall", 12, 10, 12, 14)
              + _scatter("door", [(12, 8)]),
        monsters=[
            ScenarioMonster("Goblin", 15, 4),
            ScenarioMonster("Goblin", 15, 10),
            ScenarioMonster("Goblin", 18, 5),
            ScenarioMonster("Goblin", 18, 9),
            ScenarioMonster("Goblin", 21, 6),
            ScenarioMonster("Goblin", 21, 8),
            ScenarioMonster("Goblin Boss", 24, 7),
            ScenarioMonster("Worg", 23, 5),
        ],
        party_spawns=[(2, 5), (2, 7), (3, 9), (3, 11)],
    ),
    Scenario(
        id="kobold_mines",
        name="Kobold Mines",
        category="dungeon",
        description="Crude mining chambers. Kobolds pepper the PCs "
                    "with crossbows while Bugbears guard the shaft.",
        recommended_level_min=3, recommended_level_max=5,
        ceiling_ft=12,
        tags=("indoor", "ranged", "bugbear"),
        tiles=_walls_rect(0, 2, 28, 13)
              + _scatter("pillar", [(8, 5), (8, 11), (16, 5), (16, 11)])
              + _scatter("rubble", [(12, 8), (13, 8), (19, 6), (20, 10)])
              + _scatter("spikes", [(24, 7), (24, 8)]),
        monsters=[
            ScenarioMonster("Kobold", 14, 4),
            ScenarioMonster("Kobold", 14, 10),
            ScenarioMonster("Kobold", 18, 4),
            ScenarioMonster("Kobold", 18, 10),
            ScenarioMonster("Kobold", 22, 4),
            ScenarioMonster("Kobold", 22, 10),
            ScenarioMonster("Kobold", 20, 7),
            ScenarioMonster("Kobold", 21, 7),
            ScenarioMonster("Bugbear", 25, 5),
            ScenarioMonster("Bugbear", 25, 9),
        ],
        party_spawns=[(2, 5), (2, 7), (3, 9), (3, 11)],
    ),

    # ============= CAVE =============
    Scenario(
        id="spider_nest",
        name="Spider Nest",
        category="cave",
        description="A webbed cavern crawling with giant spiders and "
                    "their ettercap masters. 15-foot ceiling.",
        recommended_level_min=3, recommended_level_max=5,
        ceiling_ft=15,
        weather="Fog",
        tags=("cave", "web", "spiders"),
        tiles=_scatter("rock", [(8, 3), (8, 12), (15, 3), (15, 12),
                                  (22, 4), (22, 11)])
              + _scatter("difficult", [(10, 6), (11, 7), (12, 7),
                                         (14, 9), (16, 9), (18, 7), (20, 6)])
              + _scatter("entangle", [(12, 5), (13, 6), (17, 8), (18, 9)]),
        monsters=[
            ScenarioMonster("Giant Spider", 15, 5),
            ScenarioMonster("Giant Spider", 18, 10),
            ScenarioMonster("Giant Spider", 21, 7),
            ScenarioMonster("Ettercap", 23, 5),
            ScenarioMonster("Ettercap", 23, 10),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="troll_den",
        name="Troll's Den",
        category="cave",
        description="A foul cavern reeking of old kills. A hulking troll "
                    "lurks at the back; goblin minions scurry around.",
        recommended_level_min=4, recommended_level_max=6,
        ceiling_ft=18,
        tags=("cave", "regen", "boss"),
        tiles=_scatter("rock", [(7, 4), (7, 11), (14, 3), (14, 12)])
              + _scatter("fire", [(13, 7), (13, 8)])
              + _scatter("rubble", [(10, 5), (11, 10), (16, 6), (19, 9)]),
        monsters=[
            ScenarioMonster("Goblin", 17, 5),
            ScenarioMonster("Goblin", 17, 9),
            ScenarioMonster("Goblin", 20, 6),
            ScenarioMonster("Troll", 23, 7),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= UNDERWATER =============
    Scenario(
        id="lizardfolk_shallows",
        name="Lizardfolk Shallows",
        category="underwater",
        description="Swampy water up to the knee. Lizardfolk burst out "
                    "of the reeds alongside giant frogs.",
        recommended_level_min=2, recommended_level_max=4,
        weather="Rain",
        tags=("water", "swamp", "aquatic"),
        tiles=[ScenarioTile("water", x, y) for x in range(6, 25)
               for y in range(3, 13) if (x + y) % 2 == 0]
              + [ScenarioTile("deep_water", x, y) for x in range(12, 20)
                 for y in range(6, 10)]
              + _scatter("difficult", [(8, 4), (8, 12), (15, 3), (22, 5)]),
        monsters=[
            ScenarioMonster("Lizardfolk", 15, 5),
            ScenarioMonster("Lizardfolk", 15, 9),
            ScenarioMonster("Lizardfolk", 20, 4),
            ScenarioMonster("Lizardfolk", 20, 10),
            ScenarioMonster("Lizardfolk", 23, 7),
            ScenarioMonster("Giant Frog", 18, 7),
            ScenarioMonster("Giant Frog", 17, 8),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="aboleth_grotto",
        name="Aboleth Grotto",
        category="underwater",
        description="A deep, flooded grotto. An aboleth commands its "
                    "enthralled lizardfolk from a pool at the far end.",
        recommended_level_min=8, recommended_level_max=12,
        ceiling_ft=25,
        tags=("water", "boss", "psionic"),
        tiles=[ScenarioTile("deep_water", x, y) for x in range(6, 28)
               for y in range(3, 14)]
              + _scatter("rock", [(10, 4), (11, 12), (22, 4), (23, 12)]),
        monsters=[
            ScenarioMonster("Lizardfolk", 14, 6),
            ScenarioMonster("Lizardfolk", 14, 10),
            ScenarioMonster("Lizardfolk", 20, 5),
            ScenarioMonster("Aboleth", 25, 8),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= OUTDOOR =============
    Scenario(
        id="wolf_pack",
        name="Wolf Pack Hunt",
        category="outdoor",
        description="A pack of timber wolves led by dire wolves closes "
                    "in on the party from the treeline.",
        recommended_level_min=1, recommended_level_max=3,
        tags=("forest", "beast", "pack_tactics"),
        tiles=_scatter("tree", [(8, 3), (9, 12), (14, 3), (14, 12),
                                  (18, 3), (19, 12), (22, 4), (22, 11)])
              + _scatter("difficult", [(12, 7), (13, 7), (17, 8)]),
        monsters=[
            ScenarioMonster("Wolf", 15, 4),
            ScenarioMonster("Wolf", 15, 10),
            ScenarioMonster("Wolf", 18, 5),
            ScenarioMonster("Wolf", 18, 9),
            ScenarioMonster("Wolf", 20, 7),
            ScenarioMonster("Dire Wolf", 22, 6),
            ScenarioMonster("Dire Wolf", 22, 8),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="orc_raid",
        name="Orc Raiding Band",
        category="outdoor",
        description="An orc war-band and their worgs break from the hills.",
        recommended_level_min=3, recommended_level_max=5,
        tags=("open_field", "charge", "worg"),
        tiles=_scatter("rock", [(10, 4), (11, 11), (16, 3), (17, 12)])
              + _scatter("difficult", [(12, 7), (13, 8), (15, 6)]),
        monsters=[
            ScenarioMonster("Orc", 17, 5),
            ScenarioMonster("Orc", 17, 9),
            ScenarioMonster("Orc", 20, 6),
            ScenarioMonster("Orc", 20, 8),
            ScenarioMonster("Worg", 22, 5),
            ScenarioMonster("Worg", 22, 9),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="gnoll_patrol",
        name="Gnoll Patrol",
        category="outdoor",
        description="A hunger-driven gnoll patrol in a dry savannah.",
        recommended_level_min=2, recommended_level_max=4,
        tags=("savannah", "fiend"),
        tiles=_scatter("difficult", [(10, 5), (12, 8), (14, 6), (18, 10),
                                       (19, 4), (22, 7)]),
        monsters=[
            ScenarioMonster("Gnoll", 15, 5),
            ScenarioMonster("Gnoll", 15, 10),
            ScenarioMonster("Gnoll", 18, 6),
            ScenarioMonster("Gnoll", 18, 9),
            ScenarioMonster("Gnoll", 22, 7),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= URBAN =============
    Scenario(
        id="cult_temple",
        name="Cult Temple",
        category="urban",
        description="A dark basement temple, pillars hiding cultists "
                    "and an acolyte ready to buff and heal them.",
        recommended_level_min=2, recommended_level_max=4,
        ceiling_ft=20,
        tags=("indoor", "casters", "pillars"),
        tiles=_walls_rect(3, 2, 23, 13)
              + _scatter("pillar", [(10, 5), (10, 11), (18, 5), (18, 11)])
              + _scatter("table", [(14, 7), (14, 8)])
              + _scatter("fire", [(14, 4), (14, 11)]),
        monsters=[
            ScenarioMonster("Cultist", 15, 5),
            ScenarioMonster("Cultist", 15, 10),
            ScenarioMonster("Cultist", 19, 6),
            ScenarioMonster("Cultist", 19, 9),
            ScenarioMonster("Cultist", 22, 7),
            ScenarioMonster("Acolyte", 23, 7),
        ],
        party_spawns=[(5, 5), (5, 7), (5, 9), (5, 11)],
    ),
    Scenario(
        id="rooftop_heist",
        name="Rooftop Heist",
        category="urban",
        description="Chase across 15-foot city rooftops. Gaps between "
                    "buildings demand jump checks or flight.",
        recommended_level_min=5, recommended_level_max=7,
        tags=("urban", "elevation", "gap"),
        tiles=[ScenarioTile("platform_15", x, y)
               for x in range(5, 12) for y in range(4, 12)]
              + [ScenarioTile("platform_15", x, y)
                 for x in range(15, 22) for y in range(4, 12)]
              + _scatter("chasm", [(12, 4), (12, 5), (12, 6), (12, 7),
                                     (12, 8), (12, 9), (12, 10), (12, 11),
                                     (13, 4), (13, 11), (14, 4), (14, 11)])
              + _scatter("crate", [(16, 5), (19, 9)]),
        monsters=[
            ScenarioMonster("Spy", 17, 5),
            ScenarioMonster("Spy", 17, 10),
            ScenarioMonster("Spy", 20, 7),
            ScenarioMonster("Assassin", 19, 5),
            ScenarioMonster("Assassin", 21, 9),
        ],
        party_spawns=[(6, 5), (6, 7), (6, 9), (6, 11)],
    ),

    # ============= PLANAR =============
    Scenario(
        id="devil_incursion",
        name="Devil Incursion",
        category="planar",
        description="A rift to the Nine Hells opens; devils pour out "
                    "ready to bargain with chains and blades.",
        recommended_level_min=9, recommended_level_max=12,
        weather="Fog",
        tags=("fiends", "infernal", "boss"),
        tiles=_scatter("fire", [(13, 7), (14, 7), (13, 8), (14, 8)])
              + _scatter("rock", [(8, 4), (8, 11), (18, 4), (18, 11)]),
        monsters=[
            ScenarioMonster("Chain Devil", 17, 5),
            ScenarioMonster("Chain Devil", 17, 10),
            ScenarioMonster("Bone Devil", 22, 7),
        ],
        party_spawns=_PARTY_WEST,
    ),
    Scenario(
        id="elemental_rift",
        name="Elemental Rift",
        category="planar",
        description="A crack in the earth spews magma. Salamanders and "
                    "fire snakes attack from the smouldering edges.",
        recommended_level_min=6, recommended_level_max=9,
        weather="Ash",
        tags=("elemental", "fire", "hazard_field"),
        tiles=[ScenarioTile("lava", x, y) for x in range(12, 22)
               for y in range(7, 10)]
              + _scatter("rock", [(10, 5), (10, 11), (23, 5), (23, 11)]),
        monsters=[
            ScenarioMonster("Salamander", 15, 5),
            ScenarioMonster("Salamander", 18, 11),
            ScenarioMonster("Fire Snake", 20, 6),
            ScenarioMonster("Fire Snake", 20, 10),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= URBAN — prefab-driven (Phase 7g) =============
    Scenario(
        id="tavern_brawl",
        name="Tavern Brawl",
        category="urban",
        description="A drunken thug-led brawl in a crowded tavern. "
                    "Tables and a hearth break up the lines of sight.",
        recommended_level_min=1, recommended_level_max=3,
        ceiling_ft=12,
        tags=("indoor", "brawl", "tavern"),
        # Outline of the tavern_common prefab (anchor 8,3)
        tiles=_scatter("wall",
                        [(x, 3) for x in range(8, 14)] +
                        [(x, 7) for x in range(8, 14)] +
                        [(8, 4), (8, 5), (8, 6), (13, 4), (13, 5), (13, 6)])
              + _scatter("door", [(10, 3), (11, 3)])
              + _scatter("fire", [(9, 5)])
              + _scatter("table", [(10, 5), (11, 5), (10, 6), (11, 6),
                                     (12, 4), (12, 5), (12, 6)]),
        monsters=[
            ScenarioMonster("Thug", 11, 6),
            ScenarioMonster("Thug", 12, 6),
            ScenarioMonster("Bandit", 11, 4),
            ScenarioMonster("Bandit", 12, 4),
        ],
        party_spawns=[(2, 5), (2, 6), (3, 5), (3, 6)],
    ),

    # ============= DUNGEON — vault heist =============
    Scenario(
        id="vault_heist",
        name="Vault Heist",
        category="dungeon",
        description="The party reaches the locked vault — but flame "
                    "skeletons have already been animating its guards.",
        recommended_level_min=4, recommended_level_max=6,
        ceiling_ft=15,
        tags=("indoor", "vault", "undead"),
        tiles=_walls_rect(0, 2, 26, 13)
              # Vault chamber against the east wall (4x4)
              + _scatter("wall", [(20, y) for y in range(4, 9)])
              + _scatter("wall", [(x, 9) for x in range(20, 26)])
              + _scatter("wall", [(x, 4) for x in range(20, 26)])
              + _scatter("door_locked", [(20, 6)])
              + _scatter("crate", [(22, 5), (23, 5), (22, 7), (23, 7)])
              + _scatter("pillar", [(20, 4), (24, 8)])
              # Approach corridor decoration
              + _scatter("rubble", [(8, 7), (9, 8), (12, 6)])
              + _scatter("fire", [(11, 5), (11, 11)]),
        monsters=[
            ScenarioMonster("Skeleton", 14, 6),
            ScenarioMonster("Skeleton", 14, 9),
            ScenarioMonster("Flameskull", 17, 7),
            ScenarioMonster("Flameskull", 22, 7),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= OUTDOOR — caravan ambush =============
    Scenario(
        id="caravan_ambush",
        name="Caravan Ambush",
        category="outdoor",
        description="A wagon circle is overrun while travellers "
                    "huddle around the fire. Bandits flank from the trees.",
        recommended_level_min=2, recommended_level_max=4,
        tags=("outdoor", "ambush", "wagon_circle"),
        tiles=_scatter("crate", [(10, 6), (14, 6), (10, 10), (14, 10),
                                   (12, 6), (10, 8), (14, 8), (12, 10)])
              + _scatter("fire", [(12, 8)])
              + _scatter("tree", [(5, 4), (5, 12), (18, 3), (19, 13),
                                    (22, 7), (22, 9)])
              + _scatter("difficult", [(7, 7), (8, 9), (16, 7), (17, 9)]),
        monsters=[
            ScenarioMonster("Bandit", 5, 7),
            ScenarioMonster("Bandit", 5, 9),
            ScenarioMonster("Bandit", 19, 7),
            ScenarioMonster("Bandit", 19, 9),
            ScenarioMonster("Thug", 22, 8),
        ],
        party_spawns=[(11, 7), (11, 9), (13, 7), (13, 9)],
    ),

    # ============= CAVE — ruined watchtower =============
    Scenario(
        id="ruined_watchtower",
        name="Ruined Watchtower",
        category="cave",
        description="A collapsed watchtower haunts the woods. Rubble "
                    "and a 15ft platform inside the broken walls.",
        recommended_level_min=3, recommended_level_max=5,
        ceiling_ft=20,
        tags=("ruin", "tower", "undead"),
        # Ruined tower outline (3x3 at 14,5) + rubble inside
        tiles=_scatter("wall", [(14, 5), (15, 5), (16, 5),
                                  (14, 7), (16, 7)])
              + _scatter("rubble", [(14, 6), (15, 6), (16, 6)])
              + _scatter("platform_15", [(15, 6)])
              + _scatter("rubble", [(8, 5), (9, 9), (11, 11), (18, 11)])
              + _scatter("tree", [(5, 4), (5, 12), (20, 3), (20, 13)]),
        monsters=[
            ScenarioMonster("Skeleton", 15, 4),
            ScenarioMonster("Skeleton", 15, 8),
            ScenarioMonster("Wight", 18, 7),
            ScenarioMonster("Specter", 21, 6),
        ],
        party_spawns=_PARTY_WEST,
    ),

    # ============= URBAN — shrine defense =============
    Scenario(
        id="shrine_defense",
        name="Shrine Defense",
        category="urban",
        description="The party defends a small temple shrine while "
                    "cultists pour through the doors. Two braziers and "
                    "a central altar.",
        recommended_level_min=3, recommended_level_max=5,
        ceiling_ft=20,
        tags=("indoor", "defense", "altar"),
        tiles=_walls_rect(5, 3, 18, 11)
              + _scatter("door", [(5, 7), (5, 9), (22, 7), (22, 9)])
              + _scatter("table", [(13, 8)])               # altar
              + _scatter("fire", [(11, 8), (15, 8)])       # braziers
              + _scatter("pillar", [(9, 5), (9, 11),
                                      (18, 5), (18, 11)]),
        monsters=[
            ScenarioMonster("Cultist", 7, 6),
            ScenarioMonster("Cultist", 7, 10),
            ScenarioMonster("Cultist", 21, 6),
            ScenarioMonster("Cultist", 21, 10),
            ScenarioMonster("Acolyte", 7, 8),
        ],
        party_spawns=[(13, 6), (13, 10), (12, 8), (14, 8)],
    ),
]


# --------------------------------------------------------------------- #
# Query API
# --------------------------------------------------------------------- #
_BY_ID: Dict[str, Scenario] = {s.id: s for s in SCENARIOS}


def get_scenario(sid: str) -> Scenario:
    if sid in _BY_ID:
        return _BY_ID[sid]
    _ensure_user_loaded()
    for s in _USER_SCENARIOS:
        if s.id == sid:
            return s
    raise KeyError(f"Scenario '{sid}' not found")


def list_all() -> List[Scenario]:
    _ensure_user_loaded()
    return list(SCENARIOS) + list(_USER_SCENARIOS)


def list_categories() -> Tuple[str, ...]:
    return CATEGORIES


def list_by_category(category: str) -> List[Scenario]:
    return [s for s in list_all() if s.category == category]


def list_by_level(level: int) -> List[Scenario]:
    """Scenarios that accommodate a party of ``level``."""
    return [s for s in list_all()
            if s.recommended_level_min <= level <= s.recommended_level_max]


def scenario_monsters_as_entities(scenario: Scenario, existing_roster=None):
    """Build a list of Entity instances from the scenario's monster list,
    disambiguating names against any monsters already in ``existing_roster``
    (e.g. ``Wolf`` → ``Wolf 2`` → ``Wolf 3`` when five appear).

    Pure logic — safe to use without pygame.
    """
    import copy as _copy
    from engine.entities import Entity
    from data.library import library

    existing_roster = existing_roster or []
    out = []
    for mon in scenario.monsters:
        try:
            stats = _copy.deepcopy(library.get_monster(mon.name))
        except ValueError:
            continue
        same = sum(
            1 for e in list(existing_roster) + out
            if not e.is_player and e.name.startswith(stats.name)
        )
        if same > 0:
            stats.name = f"{stats.name} {same + 1}"
        ent = Entity(stats, mon.x, mon.y, is_player=False)
        ent.team = mon.team
        out.append(ent)
    return out


# --------------------------------------------------------------------- #
# User-authored scenarios (DM saves their own as reusable prefabs)
# --------------------------------------------------------------------- #
_USER_SCENARIOS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "saves", "user_scenarios",
)
_USER_SCENARIOS: List[Scenario] = []
_USER_LOADED = False


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower()).strip("_")
    return s or f"scenario_{uuid.uuid4().hex[:8]}"


def _scenario_to_dict(s: Scenario) -> dict:
    """Convert a Scenario to a JSON-safe dict."""
    return {
        "id": s.id, "name": s.name, "category": s.category,
        "description": s.description,
        "recommended_party_size": s.recommended_party_size,
        "recommended_level_min": s.recommended_level_min,
        "recommended_level_max": s.recommended_level_max,
        "weather": s.weather,
        "ceiling_ft": s.ceiling_ft,
        "background_image_path": s.background_image_path,
        "tags": list(s.tags),
        "tiles": [asdict(t) for t in s.tiles],
        "monsters": [asdict(m) for m in s.monsters],
        "party_spawns": [list(sp) for sp in s.party_spawns],
        "lair_enabled": s.lair_enabled,
    }


def _scenario_from_dict(d: dict) -> Scenario:
    return Scenario(
        id=d.get("id", ""), name=d.get("name", ""),
        category=d.get("category", "outdoor"),
        description=d.get("description", ""),
        recommended_party_size=int(d.get("recommended_party_size", 4)),
        recommended_level_min=int(d.get("recommended_level_min", 1)),
        recommended_level_max=int(d.get("recommended_level_max", 5)),
        weather=d.get("weather", "Clear"),
        ceiling_ft=int(d.get("ceiling_ft", 0)),
        background_image_path=d.get("background_image_path", ""),
        tags=tuple(d.get("tags", [])),
        tiles=[ScenarioTile(**t) for t in d.get("tiles", [])],
        monsters=[ScenarioMonster(**m) for m in d.get("monsters", [])],
        party_spawns=[tuple(sp) for sp in d.get("party_spawns", [])],
        lair_enabled=bool(d.get("lair_enabled", False)),
    )


def _ensure_user_loaded():
    global _USER_LOADED
    if _USER_LOADED:
        return
    _USER_LOADED = True
    if not os.path.isdir(_USER_SCENARIOS_DIR):
        return
    for fname in sorted(os.listdir(_USER_SCENARIOS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(_USER_SCENARIOS_DIR, fname),
                      encoding="utf-8") as f:
                _USER_SCENARIOS.append(_scenario_from_dict(json.load(f)))
        except (json.JSONDecodeError, OSError, TypeError):
            continue


def save_user_scenario(scenario: Scenario, directory: str = None) -> str:
    """Write ``scenario`` to JSON under ``directory`` (defaults to the
    project-standard saves/user_scenarios/). Assigns an id if missing
    and adds it to the in-memory user catalog. Returns the file path."""
    _ensure_user_loaded()
    directory = directory or _USER_SCENARIOS_DIR
    os.makedirs(directory, exist_ok=True)
    if not scenario.id:
        scenario.id = _slugify(scenario.name) or f"user_{uuid.uuid4().hex[:8]}"
    path = os.path.join(directory, f"{scenario.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_scenario_to_dict(scenario), f, indent=2, ensure_ascii=False)

    # Refresh in-memory catalog: replace if same id, else append
    for i, existing in enumerate(_USER_SCENARIOS):
        if existing.id == scenario.id:
            _USER_SCENARIOS[i] = scenario
            return path
    _USER_SCENARIOS.append(scenario)
    return path


def delete_user_scenario(scenario_id: str,
                          directory: str = None) -> bool:
    _ensure_user_loaded()
    directory = directory or _USER_SCENARIOS_DIR
    path = os.path.join(directory, f"{scenario_id}.json")
    if os.path.isfile(path):
        os.remove(path)
    for i, s in enumerate(_USER_SCENARIOS):
        if s.id == scenario_id:
            del _USER_SCENARIOS[i]
            return True
    return False


def list_user_scenarios() -> List[Scenario]:
    _ensure_user_loaded()
    return list(_USER_SCENARIOS)


def reset_user_cache_for_tests():
    """Drop the in-memory cache so the next call reloads from disk."""
    global _USER_LOADED
    _USER_SCENARIOS.clear()
    _USER_LOADED = False


def scenario_from_battle(battle, name: str, category: str = "outdoor",
                          description: str = "",
                          recommended_level_min: int = 1,
                          recommended_level_max: int = 5,
                          tags: Tuple[str, ...] = ()) -> Scenario:
    """Snapshot the current ``BattleSystem`` as a Scenario.

    * Terrain → ScenarioTile list (preserving elevation overrides)
    * Non-player Entities → ScenarioMonster list (at int-rounded grid
      positions). Entities' stats are referenced by *base name* so
      `library.get_monster()` can resolve them on load.
    * Player Entities' positions become ``party_spawns``.
    * ceiling_ft, weather, lair_enabled, background_image_path are
      copied from the battle.
    """
    tiles: List[ScenarioTile] = []
    for t in battle.terrain:
        tile_elev = t.elevation if t.elevation != t.props.get(
            "elevation_ft", 0) else -1
        tiles.append(ScenarioTile(
            terrain_type=t.terrain_type,
            x=int(t.grid_x), y=int(t.grid_y),
            w=int(t.width), h=int(t.height),
            elevation=int(tile_elev) if tile_elev != -1 else -1,
        ))

    monsters: List[ScenarioMonster] = []
    spawns: List[Tuple[int, int]] = []
    for e in battle.entities:
        if e.is_lair or e.is_summon:
            continue
        x, y = int(round(e.grid_x)), int(round(e.grid_y))
        if e.is_player:
            spawns.append((x, y))
        else:
            monsters.append(ScenarioMonster(
                name=e.stats.name, x=x, y=y,
                team=getattr(e, "team", "") or "Red",
            ))

    return Scenario(
        id=_slugify(name),
        name=name,
        category=category if category in CATEGORIES else "outdoor",
        description=description or f"Captured battle: {name}",
        recommended_level_min=max(1, recommended_level_min),
        recommended_level_max=max(recommended_level_min,
                                    recommended_level_max),
        weather=battle.weather,
        ceiling_ft=int(getattr(battle, "ceiling_ft", 0)),
        background_image_path=getattr(battle, "background_image_path", ""),
        tags=tuple(tags),
        tiles=tiles,
        monsters=monsters,
        party_spawns=spawns or [(2, 5), (2, 7), (3, 9), (3, 11)],
        lair_enabled=bool(getattr(battle, "lair_enabled", False)),
    )


def apply_scenario_to_battle(scenario: Scenario, battle):
    """Apply the scenario's terrain, weather, ceiling, lair, and optional
    background image to an existing ``BattleSystem``. Monsters are NOT
    added — use ``scenario_monsters_as_entities`` for that."""
    from engine.terrain import TerrainObject
    for tile in scenario.tiles:
        kwargs = {"terrain_type": tile.terrain_type,
                  "grid_x": tile.x, "grid_y": tile.y,
                  "width": tile.w, "height": tile.h}
        if tile.elevation >= 0:
            kwargs["elevation"] = tile.elevation
        battle.terrain.append(TerrainObject(**kwargs))
    battle.weather = scenario.weather
    battle.ceiling_ft = scenario.ceiling_ft
    if scenario.lair_enabled:
        battle.lair_enabled = True
    if scenario.background_image_path:
        battle.set_background_image(scenario.background_image_path)


# --------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------- #
def build_battle_from_scenario(scenario: Scenario,
                                log_callback: Optional[Callable[[str], None]] = None):
    """Construct a fresh BattleSystem from a Scenario. PCs must still be
    placed via the deployment phase on scenario.party_spawns cells."""
    from engine.battle import BattleSystem
    from engine.entities import Entity
    from engine.terrain import TerrainObject
    from data.library import library

    if log_callback is None:
        log_callback = lambda msg: None  # noqa: E731

    battle = BattleSystem(log_callback=log_callback, initial_entities=[])
    battle.entities = []   # Drop the demo monsters BattleSystem spawns by default
    battle.terrain = []

    for tile in scenario.tiles:
        tile_kwargs = {"terrain_type": tile.terrain_type,
                       "grid_x": tile.x, "grid_y": tile.y,
                       "width": tile.w, "height": tile.h}
        if tile.elevation >= 0:
            tile_kwargs["elevation"] = tile.elevation
        battle.terrain.append(TerrainObject(**tile_kwargs))

    for mon in scenario.monsters:
        stats = library.get_monster(mon.name)
        ent = Entity(stats, mon.x, mon.y, is_player=False)
        ent.team = mon.team
        battle.entities.append(ent)

    battle.weather = scenario.weather
    battle.ceiling_ft = scenario.ceiling_ft
    battle.lair_enabled = scenario.lair_enabled
    if scenario.background_image_path:
        battle.set_background_image(scenario.background_image_path)

    log_callback(f"[SCENARIO] Loaded: {scenario.name} "
                 f"({scenario.category}, lvls "
                 f"{scenario.recommended_level_min}-"
                 f"{scenario.recommended_level_max})")
    return battle
