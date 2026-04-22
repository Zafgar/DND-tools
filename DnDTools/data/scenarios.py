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
from dataclasses import dataclass, field
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
]


# --------------------------------------------------------------------- #
# Query API
# --------------------------------------------------------------------- #
_BY_ID: Dict[str, Scenario] = {s.id: s for s in SCENARIOS}


def get_scenario(sid: str) -> Scenario:
    if sid not in _BY_ID:
        raise KeyError(f"Scenario '{sid}' not found")
    return _BY_ID[sid]


def list_all() -> List[Scenario]:
    return list(SCENARIOS)


def list_categories() -> Tuple[str, ...]:
    return CATEGORIES


def list_by_category(category: str) -> List[Scenario]:
    return [s for s in SCENARIOS if s.category == category]


def list_by_level(level: int) -> List[Scenario]:
    """Scenarios that accommodate a party of ``level``."""
    return [s for s in SCENARIOS
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
