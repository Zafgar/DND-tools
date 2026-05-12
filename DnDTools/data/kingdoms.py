"""
Kingdoms of the campaign world — seed data and navigator helpers.

Organises the campaign's NPCs by kingdom → city → role, providing the data
backbone for the NPC navigator panel in the campaign manager.  Kingdoms here
are the top-level political regions; cities live under them; roles group NPCs
so the DM can jump quickly to "the rulers of Frand" or "every blacksmith in
Tarmaas".

Editable at runtime — users can add kingdoms/cities via the navigator UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ----------------------------------------------------------------------
# NPC role categories — used to group NPCs inside a city view.
# ----------------------------------------------------------------------

NPC_ROLE_CATEGORIES: List[Dict[str, object]] = [
    {"key": "rulers",     "label": "Hallitsijat",          "keywords": [
        "king", "queen", "lord", "lady", "baron", "duke", "count", "emperor",
        "prince", "princess", "chief", "jarl", "mayor", "ruler", "noble",
        "kuningas", "kuningatar", "ruhtinas", "paroni", "jaarli", "pormestari",
    ]},
    {"key": "clergy",     "label": "Uskonnolliset hahmot", "keywords": [
        "priest", "priestess", "cleric", "monk", "paladin", "bishop",
        "pappi", "pappitar", "piispa", "munkki", "temppeli", "druidi",
    ]},
    {"key": "smiths",     "label": "Sepät & Käsityöläiset",   "keywords": [
        "smith", "blacksmith", "armorer", "weaponsmith", "jeweler", "tailor",
        "carpenter", "mason", "alchemist", "enchanter",
        "seppä", "puuseppä", "räätäli", "alkemisti",
    ]},
    {"key": "soldiers",   "label": "Sotilaat & Vartijat",  "keywords": [
        "guard", "soldier", "captain", "knight", "warrior", "sergeant",
        "watchman", "warden", "ranger", "mercenary",
        "vartija", "sotilas", "kapteeni", "ritari",
    ]},
    {"key": "merchants",  "label": "Kauppiaat",            "keywords": [
        "merchant", "shopkeeper", "trader", "innkeeper", "tavernkeeper",
        "shop", "store", "bartender",
        "kauppias", "majatalonpitäjä", "baarimikko",
    ]},
    {"key": "scholars",   "label": "Oppineet & Loitsijat", "keywords": [
        "wizard", "mage", "sorcerer", "warlock", "scholar", "sage", "scribe",
        "librarian", "professor", "archmage", "diviner",
        "velho", "noita", "oppinut", "tutkija",
    ]},
    {"key": "workers",    "label": "Työläiset & Asukkaat", "keywords": [
        "farmer", "miner", "labourer", "laborer", "fisher", "baker",
        "hunter", "herder", "servant", "commoner", "worker", "peasant",
        "maanviljelijä", "kalastaja", "leipuri", "metsästäjä", "palvelija",
    ]},
    {"key": "criminals",  "label": "Rikolliset & Vaaralliset", "keywords": [
        "thief", "bandit", "assassin", "rogue", "pirate", "smuggler",
        "varas", "rosvo", "salamurhaaja", "piraatti",
    ]},
    {"key": "other",      "label": "Muut",                 "keywords": []},
]


def _role_from_npc(npc) -> str:
    """Classify an NPC into one of the role keys above using occupation/title/
    faction/tags. Returns 'other' if nothing matches."""
    haystack = " ".join([
        (npc.occupation or ""), (npc.title or ""),
        (npc.faction or ""), " ".join(npc.tags or []),
    ]).lower()
    if not haystack.strip():
        return "other"
    for cat in NPC_ROLE_CATEGORIES:
        for kw in cat["keywords"]:
            if kw in haystack:
                return cat["key"]  # type: ignore[return-value]
    return "other"


# ----------------------------------------------------------------------
# Kingdom / city data model
# ----------------------------------------------------------------------

@dataclass
class CityEntry:
    """A city or settlement inside a kingdom."""
    key: str                               # stable identifier
    name: str
    is_capital: bool = False
    # Populated at runtime by Campaign data, not persisted here
    location_id: str = ""                  # World.locations id
    map_id: str = ""                       # WorldMap id (town map drill-down)
    map_x: float = -1.0                    # % position on the kingdom map
    map_y: float = -1.0
    description: str = ""
    # Phase 22c: living-world fields
    population: int = 0                    # Total residents
    biome: str = ""                        # Biome tag for demographics
    treasury_gp: float = 0.0               # City treasury in gold pieces
    primary_industry: str = ""             # "trade", "mining", "magic", …
    income_sources: List[str] = field(default_factory=list)
    ruler_npc_id: str = ""                 # NPC who rules the city
    religion: str = ""                     # Dominant church / pantheon
    faction_ids: List[str] = field(default_factory=list)
    demographics: dict = field(default_factory=dict)  # race → pct
    # Phase 22e: per-city relations (city_key → attitude string)
    relations: Dict[str, str] = field(default_factory=dict)


@dataclass
class KingdomEntry:
    """A top-level political region."""
    key: str
    name: str
    # Runtime links
    map_id: str = ""                        # kingdom overview map
    capital_key: str = ""
    description: str = ""
    flavour: str = ""
    cities: List[CityEntry] = field(default_factory=list)
    # Phase 22c: living-world fields
    population: int = 0                    # Estimated total (if 0 — sum cities)
    treasury_gp: float = 0.0               # Crown treasury
    ruler_npc_id: str = ""
    capital_religion: str = ""
    primary_export: str = ""               # "Steel", "Magic", "Grain", …
    biome: str = ""                        # Default biome for new cities
    motto: str = ""
    flag_color: tuple = (180, 180, 180)
    faction_ids: List[str] = field(default_factory=list)
    # Phase 22e: kingdom-to-kingdom relations (key → attitude string)
    relations: Dict[str, str] = field(default_factory=dict)


# Seed kingdoms — user can extend at runtime via the navigator panel.
# Only the five main kingdoms are required; cities can be added by the user.
# Novus Somnium living-world data: each kingdom carries a population
# estimate, crown treasury (gp), ruling biome, primary export, motto and
# starting relations toward the other four.
SEED_KINGDOMS: List[KingdomEntry] = [
    KingdomEntry(
        key="tarmaas", name="Tarmaas",
        capital_key="frand",
        description="Päävaltakunta — pohjoinen mantere. Kulttuuri keskittyy "
                    "pääkaupunkiin Frandiin.",
        flavour="Vanhojen ritarihuoneiden ja kauppakiltojen liitto, jonka "
                "kruunu pitää viiden suurvallan tasapainoa.",
        population=820_000,
        treasury_gp=1_250_000.0,
        capital_religion="Auringonkirkko",
        primary_export="Teräs ja vilja",
        biome="human_heartland",
        motto="Yksi kruunu, monta miekkaa.",
        flag_color=(212, 175, 55),
        relations={
            "fundarla": "ally",
            "smardu": "neutral",
            "aterterra": "trade",
            "oblitus": "hostile",
        },
        cities=[
            CityEntry(
                key="frand", name="Frand", is_capital=True,
                description="Tarmaasin pääkaupunki — suuri muurikaupunki "
                            "Auringonkirkon emäkatedraalin varjossa.",
                population=42_000,
                biome="cosmopolitan",
                treasury_gp=280_000.0,
                primary_industry="hallinto",
                income_sources=["verot", "kauppakillat", "kirkollinen kymmenys"],
                religion="Auringonkirkko",
            ),
        ],
    ),
    KingdomEntry(
        key="fundarla", name="Fundarla",
        description="Toinen suurvalta; rinnakkaiselo Tarmaasin kanssa.",
        flavour="Metsien ja jokien valtakunta, jonka haltia- ja "
                "ihmissuvut hallitsevat yhteisessä neuvostossa.",
        population=540_000,
        treasury_gp=780_000.0,
        capital_religion="Lehtoäidin polku",
        primary_export="Puuvalmisteet ja taikajuomat",
        biome="forest",
        motto="Juuret syvälle, oksat korkealle.",
        flag_color=(60, 130, 80),
        relations={
            "tarmaas": "ally",
            "smardu": "neutral",
            "aterterra": "neutral",
            "oblitus": "hostile",
        },
    ),
    KingdomEntry(
        key="smardu", name="Smardu",
        description="Kolmas suurvalta — louhokset ja vuoristolinnakkeet.",
        flavour="Kääpiöiden ja vuorenkansojen liittokunta, jonka rikkaus "
                "tulee syvistä kaivoksista ja seppämestareista.",
        population=410_000,
        treasury_gp=1_600_000.0,
        capital_religion="Vasaran veljeskunta",
        primary_export="Metallit ja jalokivet",
        biome="mountain",
        motto="Kivessä on totuus.",
        flag_color=(120, 110, 90),
        relations={
            "tarmaas": "neutral",
            "fundarla": "neutral",
            "aterterra": "trade",
            "oblitus": "neutral",
        },
    ),
    KingdomEntry(
        key="aterterra", name="Aterterra",
        description="Neljäs suurvalta — rannikkokauppiaiden tasavalta.",
        flavour="Satamakaupunkien liitto, joka hallitsee meriteitä ja "
                "yhdistää viiden suurvallan kaupan.",
        population=620_000,
        treasury_gp=1_400_000.0,
        capital_religion="Aaltojen kirkko",
        primary_export="Mausteet, silkki ja merikalastus",
        biome="coast",
        motto="Tuuli kuljettaa, kulta jää.",
        flag_color=(70, 130, 180),
        relations={
            "tarmaas": "trade",
            "fundarla": "neutral",
            "smardu": "trade",
            "oblitus": "wary",
        },
    ),
    KingdomEntry(
        key="oblitus", name="Oblitus",
        description="Viides suurvalta — varjojen ja vanhojen velkojen maa.",
        flavour="Mainetonta autiomaata reunustava varjokuningaskunta, "
                "jonka rajoilla Brotherhood of Glorious Sun yhä vaikuttaa.",
        population=300_000,
        treasury_gp=210_000.0,
        capital_religion="Hiljainen vala",
        primary_export="Suola, jäänteet, salaisuudet",
        biome="desert",
        motto="Mitä unohdetaan, ei kuole.",
        flag_color=(120, 70, 90),
        relations={
            "tarmaas": "hostile",
            "fundarla": "hostile",
            "smardu": "neutral",
            "aterterra": "wary",
        },
    ),
]


# ----------------------------------------------------------------------
# Campaign integration helpers
# ----------------------------------------------------------------------

def _city_from_dict(d: Dict) -> CityEntry:
    return CityEntry(
        key=d.get("key", ""), name=d.get("name", ""),
        is_capital=bool(d.get("is_capital", False)),
        location_id=d.get("location_id", ""),
        map_id=d.get("map_id", ""),
        map_x=float(d.get("map_x", -1.0)), map_y=float(d.get("map_y", -1.0)),
        description=d.get("description", ""),
        population=int(d.get("population", 0) or 0),
        biome=d.get("biome", ""),
        treasury_gp=float(d.get("treasury_gp", 0.0) or 0.0),
        primary_industry=d.get("primary_industry", ""),
        income_sources=list(d.get("income_sources", []) or []),
        ruler_npc_id=d.get("ruler_npc_id", ""),
        religion=d.get("religion", ""),
        faction_ids=list(d.get("faction_ids", []) or []),
        demographics=dict(d.get("demographics", {}) or {}),
        relations=dict(d.get("relations", {}) or {}),
    )


def _city_to_dict(c: CityEntry) -> Dict:
    return {
        "key": c.key, "name": c.name, "is_capital": c.is_capital,
        "location_id": c.location_id, "map_id": c.map_id,
        "map_x": c.map_x, "map_y": c.map_y, "description": c.description,
        "population": c.population,
        "biome": c.biome,
        "treasury_gp": c.treasury_gp,
        "primary_industry": c.primary_industry,
        "income_sources": list(c.income_sources),
        "ruler_npc_id": c.ruler_npc_id,
        "religion": c.religion,
        "faction_ids": list(c.faction_ids),
        "demographics": dict(c.demographics),
        "relations": dict(c.relations),
    }


def _kingdom_from_dict(d: Dict) -> KingdomEntry:
    flag = d.get("flag_color", (180, 180, 180))
    if isinstance(flag, list):
        flag = tuple(flag)
    return KingdomEntry(
        key=d.get("key", ""), name=d.get("name", ""),
        map_id=d.get("map_id", ""),
        capital_key=d.get("capital_key", ""),
        description=d.get("description", ""),
        flavour=d.get("flavour", ""),
        cities=[_city_from_dict(c) for c in d.get("cities", [])],
        population=int(d.get("population", 0) or 0),
        treasury_gp=float(d.get("treasury_gp", 0.0) or 0.0),
        ruler_npc_id=d.get("ruler_npc_id", ""),
        capital_religion=d.get("capital_religion", ""),
        primary_export=d.get("primary_export", ""),
        biome=d.get("biome", ""),
        motto=d.get("motto", ""),
        flag_color=flag if isinstance(flag, tuple) else (180, 180, 180),
        faction_ids=list(d.get("faction_ids", []) or []),
        relations=dict(d.get("relations", {}) or {}),
    )


def _kingdom_to_dict(k: KingdomEntry) -> Dict:
    return {
        "key": k.key, "name": k.name, "map_id": k.map_id,
        "capital_key": k.capital_key,
        "description": k.description, "flavour": k.flavour,
        "cities": [_city_to_dict(c) for c in k.cities],
        "population": k.population,
        "treasury_gp": k.treasury_gp,
        "ruler_npc_id": k.ruler_npc_id,
        "capital_religion": k.capital_religion,
        "primary_export": k.primary_export,
        "biome": k.biome,
        "motto": k.motto,
        "flag_color": list(k.flag_color),
        "faction_ids": list(k.faction_ids),
        "relations": dict(k.relations),
    }


def ensure_kingdoms_on_campaign(campaign) -> List[KingdomEntry]:
    """Make sure the given Campaign has a runtime `kingdoms` list on it.
    First call re-hydrates from `campaign.kingdoms_data` (persisted dicts);
    if none present, seeds from SEED_KINGDOMS. Returns the runtime list."""
    import copy
    runtime = getattr(campaign, "kingdoms", None)
    if isinstance(runtime, list) and runtime:
        return runtime

    persisted = getattr(campaign, "kingdoms_data", None) or []
    if persisted:
        runtime = [_kingdom_from_dict(d) for d in persisted]
    else:
        runtime = copy.deepcopy(SEED_KINGDOMS)
    campaign.kingdoms = runtime
    return runtime


def sync_kingdoms_to_campaign(campaign) -> None:
    """Serialize the runtime `kingdoms` list back to `kingdoms_data` so it
    persists with the campaign JSON.  Call before `save_campaign`."""
    runtime = getattr(campaign, "kingdoms", None) or []
    campaign.kingdoms_data = [_kingdom_to_dict(k) for k in runtime]


def find_kingdom(campaign, key: str) -> Optional[KingdomEntry]:
    for k in ensure_kingdoms_on_campaign(campaign):
        if k.key == key:
            return k
    return None


def find_city(campaign, kingdom_key: str, city_key: str) -> Optional[CityEntry]:
    k = find_kingdom(campaign, kingdom_key)
    if not k:
        return None
    for c in k.cities:
        if c.key == city_key:
            return c
    return None


def add_kingdom(campaign, key: str, name: str, **kw) -> KingdomEntry:
    k = KingdomEntry(key=key, name=name, **kw)
    ensure_kingdoms_on_campaign(campaign).append(k)
    return k


def add_city(campaign, kingdom_key: str, city_key: str, name: str,
             is_capital: bool = False, **kw) -> Optional[CityEntry]:
    k = find_kingdom(campaign, kingdom_key)
    if not k:
        return None
    city = CityEntry(key=city_key, name=name, is_capital=is_capital, **kw)
    k.cities.append(city)
    if is_capital and not k.capital_key:
        k.capital_key = city_key
    return city


def group_npcs_by_role(world, location_id: str) -> Dict[str, List]:
    """Return {role_key: [NPC, …]} for all NPCs at a given location.  Every
    category from NPC_ROLE_CATEGORIES is included in the result (possibly
    empty) so UI code can render a stable order."""
    groups: Dict[str, List] = {c["key"]: [] for c in NPC_ROLE_CATEGORIES}
    if not location_id:
        return groups
    for npc in world.npcs.values():
        if not getattr(npc, "active", True):
            continue
        if getattr(npc, "location_id", "") != location_id:
            continue
        groups[_role_from_npc(npc)].append(npc)
    return groups


def search_world_npcs(world, query: str, limit: int = 40) -> List:
    """Thin, case-insensitive name/occupation/faction search for the navigator
    search bar.  Returns NPCs sorted by name."""
    q = (query or "").strip().lower()
    if not q:
        return []
    hits = []
    for npc in world.npcs.values():
        if not getattr(npc, "active", True):
            continue
        hay = f"{npc.name} {npc.occupation} {npc.title} {npc.faction} " \
              f"{npc.race} {' '.join(npc.tags or [])}".lower()
        if q in hay:
            hits.append(npc)
    hits.sort(key=lambda n: n.name.lower())
    return hits[:limit]


# ----------------------------------------------------------------------
# Phase 22e/f — relations + aggregate helpers
# ----------------------------------------------------------------------

# Canonical attitude vocabulary; UI panels render these as coloured chips.
RELATION_LEVELS: List[str] = [
    "ally", "trade", "neutral", "wary", "hostile", "at_war",
]


def _ensure_relation_level(level: str) -> str:
    return level if level in RELATION_LEVELS else "neutral"


def set_kingdom_relation(campaign, key_a: str, key_b: str,
                          level: str) -> None:
    """Symmetrically record the attitude between two kingdoms."""
    if not key_a or not key_b or key_a == key_b:
        return
    level = _ensure_relation_level(level)
    ka = find_kingdom(campaign, key_a)
    kb = find_kingdom(campaign, key_b)
    if ka is not None:
        ka.relations[key_b] = level
    if kb is not None:
        kb.relations[key_a] = level


def get_kingdom_relation(campaign, key_a: str, key_b: str) -> str:
    if key_a == key_b:
        return "self"
    k = find_kingdom(campaign, key_a)
    if k is None:
        return "neutral"
    return k.relations.get(key_b, "neutral")


def set_city_relation(campaign, kingdom_key: str,
                       city_a: str, city_b: str, level: str) -> None:
    """Record an attitude between two cities of the same kingdom."""
    if not city_a or not city_b or city_a == city_b:
        return
    level = _ensure_relation_level(level)
    k = find_kingdom(campaign, kingdom_key)
    if k is None:
        return
    ca = next((c for c in k.cities if c.key == city_a), None)
    cb = next((c for c in k.cities if c.key == city_b), None)
    if ca is not None:
        ca.relations[city_b] = level
    if cb is not None:
        cb.relations[city_a] = level


def get_city_relation(campaign, kingdom_key: str,
                       city_a: str, city_b: str) -> str:
    if city_a == city_b:
        return "self"
    k = find_kingdom(campaign, kingdom_key)
    if k is None:
        return "neutral"
    ca = next((c for c in k.cities if c.key == city_a), None)
    if ca is None:
        return "neutral"
    return ca.relations.get(city_b, "neutral")


def kingdom_relation_matrix(campaign) -> Dict[str, Dict[str, str]]:
    """Build a {key_a: {key_b: attitude}} matrix for the full kingdom list."""
    ks = ensure_kingdoms_on_campaign(campaign)
    matrix: Dict[str, Dict[str, str]] = {}
    for a in ks:
        row: Dict[str, str] = {}
        for b in ks:
            if a.key == b.key:
                row[b.key] = "self"
            else:
                row[b.key] = a.relations.get(b.key, "neutral")
        matrix[a.key] = row
    return matrix


def city_relation_matrix(campaign, kingdom_key: str
                          ) -> Dict[str, Dict[str, str]]:
    k = find_kingdom(campaign, kingdom_key)
    if k is None:
        return {}
    matrix: Dict[str, Dict[str, str]] = {}
    for a in k.cities:
        row: Dict[str, str] = {}
        for b in k.cities:
            if a.key == b.key:
                row[b.key] = "self"
            else:
                row[b.key] = a.relations.get(b.key, "neutral")
        matrix[a.key] = row
    return matrix


def city_population(city: CityEntry) -> int:
    """Effective population: explicit city.population, or the sum of the
    demographics race counts if no explicit total is set."""
    if city.population > 0:
        return city.population
    demo = city.demographics or {}
    # demographics may store either counts or percentages — if values look
    # like percentages (≤1.0 each, or sum ~100), we cannot derive a count.
    total = 0
    for v in demo.values():
        try:
            total += int(v)
        except (TypeError, ValueError):
            continue
    return total


def kingdom_population(kingdom: KingdomEntry) -> int:
    """Effective kingdom population: explicit value, or the sum of city
    populations when none is set."""
    if kingdom.population > 0:
        return kingdom.population
    return sum(city_population(c) for c in kingdom.cities)


def kingdom_treasury_total_gp(kingdom: KingdomEntry,
                                include_cities: bool = True) -> float:
    """Crown treasury + (optionally) all city treasuries, in gold pieces."""
    total = float(kingdom.treasury_gp or 0.0)
    if include_cities:
        total += sum(float(c.treasury_gp or 0.0) for c in kingdom.cities)
    return total


def world_population(campaign) -> int:
    return sum(kingdom_population(k)
                for k in ensure_kingdoms_on_campaign(campaign))


def world_treasury_total_gp(campaign) -> float:
    return sum(kingdom_treasury_total_gp(k)
                for k in ensure_kingdoms_on_campaign(campaign))
