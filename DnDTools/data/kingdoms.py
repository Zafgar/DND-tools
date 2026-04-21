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


@dataclass
class KingdomEntry:
    """A top-level political region. Each has its own map and a list of cities."""
    key: str
    name: str
    # Runtime links
    map_id: str = ""                        # kingdom overview map
    capital_key: str = ""
    description: str = ""
    flavour: str = ""
    cities: List[CityEntry] = field(default_factory=list)


# Seed kingdoms — user can extend at runtime via the navigator panel.
# Only the five main kingdoms are required; cities can be added by the user.
SEED_KINGDOMS: List[KingdomEntry] = [
    KingdomEntry(
        key="tarmaas", name="Tarmaas",
        capital_key="frand",
        description="Päävaltakunta — pohjoinen mantere. Kulttuuri keskittyy "
                    "pääkaupunkiin Frandiin.",
        cities=[
            CityEntry(key="frand", name="Frand", is_capital=True,
                      description="Tarmaasin pääkaupunki."),
        ],
    ),
    KingdomEntry(
        key="fundarla", name="Fundarla",
        description="Toinen suurvalta; rinnakkaiselo Tarmaasin kanssa.",
    ),
    KingdomEntry(
        key="smardu", name="Smardu",
        description="Kolmas suurvalta.",
    ),
    KingdomEntry(
        key="aterterra", name="Aterterra",
        description="Neljäs suurvalta.",
    ),
    KingdomEntry(
        key="oblitus", name="Oblitus",
        description="Viides suurvalta.",
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
    )


def _city_to_dict(c: CityEntry) -> Dict:
    return {
        "key": c.key, "name": c.name, "is_capital": c.is_capital,
        "location_id": c.location_id, "map_id": c.map_id,
        "map_x": c.map_x, "map_y": c.map_y, "description": c.description,
    }


def _kingdom_from_dict(d: Dict) -> KingdomEntry:
    return KingdomEntry(
        key=d.get("key", ""), name=d.get("name", ""),
        map_id=d.get("map_id", ""),
        capital_key=d.get("capital_key", ""),
        description=d.get("description", ""),
        flavour=d.get("flavour", ""),
        cities=[_city_from_dict(c) for c in d.get("cities", [])],
    )


def _kingdom_to_dict(k: KingdomEntry) -> Dict:
    return {
        "key": k.key, "name": k.name, "map_id": k.map_id,
        "capital_key": k.capital_key,
        "description": k.description, "flavour": k.flavour,
        "cities": [_city_to_dict(c) for c in k.cities],
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
