"""
World & NPC Management System — Data models and persistence.

Hierarchical location system: Country → Region → City → Place (unlimited nesting).
NPC profiles with appearance, backstory, attitude, stat sheet linking, inventory, relationships.
Shop system with price lists, price modification, and negotiation tracking.
"""
import json
import os
import time
import copy
from typing import List, Dict, Optional
from dataclasses import dataclass, field


WORLDS_DIR = os.path.join(os.path.dirname(__file__), "..", "worlds")


def _timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# LOCATION HIERARCHY
# ============================================================================

@dataclass
class Location:
    """A location in the world hierarchy. Can contain child locations and NPCs."""
    id: str = ""                      # Unique ID (auto-generated)
    name: str = "New Location"
    location_type: str = "region"     # country, region, city, district, building, room, wilderness, etc.
    description: str = ""
    notes: str = ""
    parent_id: str = ""               # Parent location ID ("" = top-level)
    children_ids: List[str] = field(default_factory=list)   # Child location IDs
    npc_ids: List[str] = field(default_factory=list)        # NPCs at this location
    tags: List[str] = field(default_factory=list)           # Searchable tags
    # Visual / gameplay
    environment: str = ""             # outdoor, indoor, underground, etc.
    lighting: str = "bright"          # bright, dim, darkness

LOCATION_TYPES = [
    "country", "region", "city", "town", "village",
    "district", "building", "tavern", "shop", "temple",
    "dungeon", "room", "wilderness", "cave", "castle",
    "port", "camp", "ruins", "other",
]


# ============================================================================
# NPC
# ============================================================================

@dataclass
class NPCRelationship:
    """Per-player-character notes about an NPC."""
    hero_name: str = ""               # Which PC this note is about
    attitude: str = "neutral"         # friendly, neutral, unfriendly, hostile
    notes: str = ""                   # Free-text relationship notes


@dataclass
class ShopItem:
    """An item in a shop's price list."""
    item_name: str = ""               # Item name (from items.py or custom)
    base_price_gp: float = 0.0        # Default price in gold pieces
    current_price_gp: float = 0.0     # Current (possibly negotiated) price
    quantity: int = -1                 # -1 = unlimited stock
    notes: str = ""


@dataclass
class NPC:
    """A non-player character with full profile."""
    id: str = ""                      # Unique ID
    name: str = "New NPC"
    # Profile
    race: str = ""
    gender: str = ""
    age: str = ""
    appearance: str = ""              # Physical description
    personality: str = ""
    backstory: str = ""
    occupation: str = ""              # Innkeeper, blacksmith, guard, etc.
    attitude: str = "neutral"         # Overall default attitude
    notes: str = ""                   # DM notes
    tags: List[str] = field(default_factory=list)
    # Location
    location_id: str = ""             # Where this NPC currently is
    # Stat sheet linking
    stat_source: str = ""             # "monster:Bandit", "hero:MyHero", "custom", or ""
    custom_stats: dict = field(default_factory=dict)  # Serialized CreatureStats if custom
    # Relationships (per player character)
    relationships: List[NPCRelationship] = field(default_factory=list)
    # Inventory / Shop
    is_shopkeeper: bool = False
    shop_name: str = ""               # Shop name if shopkeeper
    shop_type: str = ""               # Key from shop_catalog.SHOP_TYPES (e.g. "blacksmith")
    price_modifier: str = "normal"    # Price tier: very_cheap, cheap, normal, expensive, very_expensive, ripoff
    target_party_level: int = 5       # What level party this shop caters to
    shop_items: List[ShopItem] = field(default_factory=list)
    inventory_items: List[str] = field(default_factory=list)  # Non-shop personal items
    gold: float = 0.0
    # Status
    alive: bool = True
    active: bool = True               # False = removed from play but kept in records


# ============================================================================
# WORLD (top-level container)
# ============================================================================

@dataclass
class World:
    """Top-level world data — all locations and NPCs."""
    name: str = "New World"
    description: str = ""
    created: str = ""
    last_modified: str = ""
    locations: Dict[str, Location] = field(default_factory=dict)  # id -> Location
    npcs: Dict[str, NPC] = field(default_factory=dict)            # id -> NPC
    next_id: int = 1                  # Auto-increment for IDs


def generate_id(world: World, prefix: str = "loc") -> str:
    """Generate a unique ID."""
    uid = f"{prefix}_{world.next_id}"
    world.next_id += 1
    return uid


# ============================================================================
# SERIALIZATION
# ============================================================================

def _serialize_relationship(r: NPCRelationship) -> dict:
    return {"hero_name": r.hero_name, "attitude": r.attitude, "notes": r.notes}

def _deserialize_relationship(d: dict) -> NPCRelationship:
    return NPCRelationship(
        hero_name=d.get("hero_name", ""),
        attitude=d.get("attitude", "neutral"),
        notes=d.get("notes", ""),
    )

def _serialize_shop_item(si: ShopItem) -> dict:
    return {
        "item_name": si.item_name, "base_price_gp": si.base_price_gp,
        "current_price_gp": si.current_price_gp, "quantity": si.quantity,
        "notes": si.notes,
    }

def _deserialize_shop_item(d: dict) -> ShopItem:
    return ShopItem(
        item_name=d.get("item_name", ""), base_price_gp=d.get("base_price_gp", 0),
        current_price_gp=d.get("current_price_gp", 0), quantity=d.get("quantity", -1),
        notes=d.get("notes", ""),
    )

def _serialize_location(loc: Location) -> dict:
    return {
        "id": loc.id, "name": loc.name, "location_type": loc.location_type,
        "description": loc.description, "notes": loc.notes,
        "parent_id": loc.parent_id, "children_ids": loc.children_ids,
        "npc_ids": loc.npc_ids, "tags": loc.tags,
        "environment": loc.environment, "lighting": loc.lighting,
    }

def _deserialize_location(d: dict) -> Location:
    return Location(
        id=d.get("id", ""), name=d.get("name", ""),
        location_type=d.get("location_type", "region"),
        description=d.get("description", ""), notes=d.get("notes", ""),
        parent_id=d.get("parent_id", ""),
        children_ids=d.get("children_ids", []),
        npc_ids=d.get("npc_ids", []),
        tags=d.get("tags", []),
        environment=d.get("environment", ""),
        lighting=d.get("lighting", "bright"),
    )

def _serialize_npc(npc: NPC) -> dict:
    return {
        "id": npc.id, "name": npc.name,
        "race": npc.race, "gender": npc.gender, "age": npc.age,
        "appearance": npc.appearance, "personality": npc.personality,
        "backstory": npc.backstory, "occupation": npc.occupation,
        "attitude": npc.attitude, "notes": npc.notes, "tags": npc.tags,
        "location_id": npc.location_id,
        "stat_source": npc.stat_source,
        "custom_stats": npc.custom_stats,
        "relationships": [_serialize_relationship(r) for r in npc.relationships],
        "is_shopkeeper": npc.is_shopkeeper, "shop_name": npc.shop_name,
        "shop_type": npc.shop_type, "price_modifier": npc.price_modifier,
        "target_party_level": npc.target_party_level,
        "shop_items": [_serialize_shop_item(si) for si in npc.shop_items],
        "inventory_items": npc.inventory_items, "gold": npc.gold,
        "alive": npc.alive, "active": npc.active,
    }

def _deserialize_npc(d: dict) -> NPC:
    return NPC(
        id=d.get("id", ""), name=d.get("name", ""),
        race=d.get("race", ""), gender=d.get("gender", ""),
        age=d.get("age", ""), appearance=d.get("appearance", ""),
        personality=d.get("personality", ""), backstory=d.get("backstory", ""),
        occupation=d.get("occupation", ""), attitude=d.get("attitude", "neutral"),
        notes=d.get("notes", ""), tags=d.get("tags", []),
        location_id=d.get("location_id", ""),
        stat_source=d.get("stat_source", ""),
        custom_stats=d.get("custom_stats", {}),
        relationships=[_deserialize_relationship(r) for r in d.get("relationships", [])],
        is_shopkeeper=d.get("is_shopkeeper", False),
        shop_name=d.get("shop_name", ""),
        shop_type=d.get("shop_type", ""),
        price_modifier=d.get("price_modifier", "normal"),
        target_party_level=d.get("target_party_level", 5),
        shop_items=[_deserialize_shop_item(si) for si in d.get("shop_items", [])],
        inventory_items=d.get("inventory_items", []),
        gold=d.get("gold", 0),
        alive=d.get("alive", True), active=d.get("active", True),
    )

def save_world(world: World, filepath: str = ""):
    """Save world to JSON file."""
    if not filepath:
        os.makedirs(WORLDS_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in world.name)
        filepath = os.path.join(WORLDS_DIR, f"{safe_name}.json")

    world.last_modified = _timestamp()
    if not world.created:
        world.created = world.last_modified

    data = {
        "name": world.name,
        "description": world.description,
        "created": world.created,
        "last_modified": world.last_modified,
        "locations": {k: _serialize_location(v) for k, v in world.locations.items()},
        "npcs": {k: _serialize_npc(v) for k, v in world.npcs.items()},
        "next_id": world.next_id,
    }

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def load_world(filepath: str) -> World:
    """Load world from JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    return World(
        name=data.get("name", "Unnamed"),
        description=data.get("description", ""),
        created=data.get("created", ""),
        last_modified=data.get("last_modified", ""),
        locations={k: _deserialize_location(v) for k, v in data.get("locations", {}).items()},
        npcs={k: _deserialize_npc(v) for k, v in data.get("npcs", {}).items()},
        next_id=data.get("next_id", 1),
    )


def list_worlds() -> List[str]:
    """List all world files."""
    os.makedirs(WORLDS_DIR, exist_ok=True)
    return sorted([f for f in os.listdir(WORLDS_DIR) if f.endswith(".json")])


def delete_world(filepath: str):
    """Delete a world file."""
    if os.path.exists(filepath):
        os.remove(filepath)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_root_locations(world: World) -> List[Location]:
    """Get all top-level locations (no parent)."""
    return [loc for loc in world.locations.values() if not loc.parent_id]


def get_children(world: World, location_id: str) -> List[Location]:
    """Get child locations of a given location."""
    loc = world.locations.get(location_id)
    if not loc:
        return []
    return [world.locations[cid] for cid in loc.children_ids if cid in world.locations]


def get_location_path(world: World, location_id: str) -> List[Location]:
    """Get breadcrumb path from root to this location."""
    path = []
    current_id = location_id
    visited = set()
    while current_id and current_id not in visited:
        visited.add(current_id)
        loc = world.locations.get(current_id)
        if loc:
            path.insert(0, loc)
            current_id = loc.parent_id
        else:
            break
    return path


def get_npcs_at_location(world: World, location_id: str) -> List[NPC]:
    """Get all NPCs at a specific location."""
    return [npc for npc in world.npcs.values() if npc.location_id == location_id and npc.active]


def search_npcs(world: World, query: str) -> List[NPC]:
    """Search NPCs by name, occupation, race, tags, or notes."""
    q = query.lower()
    results = []
    for npc in world.npcs.values():
        if not npc.active:
            continue
        searchable = f"{npc.name} {npc.race} {npc.occupation} {npc.notes} {npc.backstory} {' '.join(npc.tags)}".lower()
        if q in searchable:
            results.append(npc)
    return results


def search_locations(world: World, query: str) -> List[Location]:
    """Search locations by name, type, description, or tags."""
    q = query.lower()
    results = []
    for loc in world.locations.values():
        searchable = f"{loc.name} {loc.location_type} {loc.description} {' '.join(loc.tags)}".lower()
        if q in searchable:
            results.append(loc)
    return results


def add_location(world: World, name: str, location_type: str = "region",
                 parent_id: str = "", **kwargs) -> Location:
    """Create and add a new location to the world."""
    loc = Location(
        id=generate_id(world, "loc"),
        name=name,
        location_type=location_type,
        parent_id=parent_id,
        **kwargs,
    )
    world.locations[loc.id] = loc
    # Link to parent
    if parent_id and parent_id in world.locations:
        parent = world.locations[parent_id]
        if loc.id not in parent.children_ids:
            parent.children_ids.append(loc.id)
    return loc


def add_npc(world: World, name: str, location_id: str = "", **kwargs) -> NPC:
    """Create and add a new NPC to the world."""
    npc = NPC(
        id=generate_id(world, "npc"),
        name=name,
        location_id=location_id,
        **kwargs,
    )
    world.npcs[npc.id] = npc
    # Link to location
    if location_id and location_id in world.locations:
        loc = world.locations[location_id]
        if npc.id not in loc.npc_ids:
            loc.npc_ids.append(npc.id)
    return npc


def move_npc(world: World, npc_id: str, new_location_id: str):
    """Move an NPC to a new location."""
    npc = world.npcs.get(npc_id)
    if not npc:
        return
    # Remove from old location
    old_loc = world.locations.get(npc.location_id)
    if old_loc and npc_id in old_loc.npc_ids:
        old_loc.npc_ids.remove(npc_id)
    # Add to new location
    npc.location_id = new_location_id
    new_loc = world.locations.get(new_location_id)
    if new_loc and npc_id not in new_loc.npc_ids:
        new_loc.npc_ids.append(npc_id)


def delete_location(world: World, location_id: str, recursive: bool = True):
    """Delete a location. If recursive, also deletes children and unlinks NPCs."""
    loc = world.locations.get(location_id)
    if not loc:
        return
    if recursive:
        for cid in list(loc.children_ids):
            delete_location(world, cid, recursive=True)
    # Unlink NPCs
    for npc_id in loc.npc_ids:
        npc = world.npcs.get(npc_id)
        if npc:
            npc.location_id = ""
    # Remove from parent
    parent = world.locations.get(loc.parent_id)
    if parent and location_id in parent.children_ids:
        parent.children_ids.remove(location_id)
    del world.locations[location_id]


def delete_npc(world: World, npc_id: str):
    """Delete an NPC from the world."""
    npc = world.npcs.get(npc_id)
    if not npc:
        return
    # Remove from location
    loc = world.locations.get(npc.location_id)
    if loc and npc_id in loc.npc_ids:
        loc.npc_ids.remove(npc_id)
    del world.npcs[npc_id]


# ============================================================================
# SHOP HELPERS
# ============================================================================

def populate_shop(npc: NPC, party_level: int = 0):
    """Auto-populate a shopkeeper's inventory from shop_catalog."""
    from data.shop_catalog import generate_shop_inventory, get_item_price, apply_price_modifier
    if not npc.is_shopkeeper or not npc.shop_type:
        return
    level = party_level or npc.target_party_level
    items = generate_shop_inventory(npc.shop_type, level, npc.price_modifier)
    npc.shop_items = []
    for entry in items:
        npc.shop_items.append(ShopItem(
            item_name=entry["name"],
            base_price_gp=entry["base_price"],
            current_price_gp=entry["adjusted_price"],
            quantity=-1,
        ))


def get_shop_suggestions(npc: NPC, count: int = 5) -> list:
    """Get suggested items to add to this shopkeeper's inventory."""
    from data.shop_catalog import suggest_items_for_shop
    if not npc.shop_type:
        return []
    return suggest_items_for_shop(npc.shop_type, npc.target_party_level, count)


def get_shopkeepers(world: World) -> List[NPC]:
    """Get all active shopkeeper NPCs."""
    return [npc for npc in world.npcs.values() if npc.is_shopkeeper and npc.active]


def get_shopkeepers_at_location(world: World, location_id: str) -> List[NPC]:
    """Get shopkeeper NPCs at a specific location."""
    return [npc for npc in world.npcs.values()
            if npc.is_shopkeeper and npc.active and npc.location_id == location_id]
