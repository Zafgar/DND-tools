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
    # Map display
    map_color: str = ""               # Custom hex color for map node (e.g. "#FF8800")
    map_icon: str = ""                # Custom icon text (1-2 chars) for map
    map_note: str = ""                # Hover note shown on map tooltip
    population: int = 0               # Population size (for cities/towns)
    map_size: int = 0                 # Custom node size on map (0 = auto)
    map_image_path: str = ""          # Per-location map background (JPG path)
    # Extended info
    government: str = ""              # Monarchy, council, anarchy, theocracy, etc.
    dominant_races: str = ""          # Comma-separated races (e.g. "Human, Elf, Dwarf")
    languages: str = ""               # Spoken languages
    religion: str = ""                # Dominant faith/temple
    wealth_level: str = ""            # squalid, poor, modest, comfortable, wealthy, aristocratic
    defenses: str = ""                # Walls, guards, traps, etc.
    known_for: str = ""               # What this place is famous for

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
    title: str = ""                   # Noble title, rank, etc. (e.g. "Captain", "Baron")
    faction: str = ""                 # Guild, order, organization (e.g. "Thieves Guild", "City Guard")
    alignment: str = ""               # D&D alignment (e.g. "Lawful Good", "Chaotic Neutral")
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
# QUESTS
# ============================================================================

@dataclass
class QuestObjective:
    """A single objective/milestone within a quest."""
    description: str = ""
    completed: bool = False
    notes: str = ""                   # DM notes for this objective
    target_npc_id: str = ""           # NPC involved (kill, talk to, escort, etc.)
    target_location_id: str = ""      # Location involved (go to, explore, etc.)
    target_item: str = ""             # Item involved (fetch, deliver, etc.)


@dataclass
class Quest:
    """A quest/mission that can be tracked, linked to NPCs and locations."""
    id: str = ""                      # Unique ID
    name: str = "New Quest"
    description: str = ""             # Full quest description
    status: str = "active"            # not_started, active, completed, failed, on_hold
    priority: str = "normal"          # low, normal, high, urgent
    quest_type: str = "main"          # main, side, personal, faction, bounty
    # Links
    giver_npc_id: str = ""            # NPC who gave the quest
    turn_in_npc_id: str = ""          # NPC to turn in to (if different)
    location_ids: List[str] = field(default_factory=list)     # Related locations
    npc_ids: List[str] = field(default_factory=list)          # Related NPCs
    # Objectives
    objectives: List[QuestObjective] = field(default_factory=list)
    # Rewards
    reward_xp: int = 0
    reward_gold: float = 0.0
    reward_items: List[str] = field(default_factory=list)     # Item names
    reward_notes: str = ""            # Custom reward description
    # Meta
    notes: str = ""                   # DM notes
    tags: List[str] = field(default_factory=list)
    created: str = ""
    completed_date: str = ""
    session_given: int = 0            # Session number when quest was given
    level_range: str = ""             # Recommended level range (e.g. "3-5")


QUEST_STATUSES = ["not_started", "active", "completed", "failed", "on_hold"]
QUEST_TYPES = ["main", "side", "personal", "faction", "bounty"]
QUEST_PRIORITIES = ["low", "normal", "high", "urgent"]


# ============================================================================
# WORLD (top-level container)
# ============================================================================

@dataclass
class MapPin:
    """A pin/marker on the world map with notes and optional hyperlinks."""
    id: str = ""
    name: str = "New Pin"
    pin_type: str = "note"            # note, poi, danger, treasure, quest, camp, custom
    description: str = ""             # Short description shown on hover
    notes: str = ""                   # Detailed DM notes
    links: List[str] = field(default_factory=list)  # URLs or file paths
    icon: str = ""                    # 1-2 char icon override (empty = auto from pin_type)
    color: str = ""                   # Custom hex color (empty = auto from pin_type)
    map_x: float = 0.0               # X position on map (percentage 0-100)
    map_y: float = 0.0               # Y position on map (percentage 0-100)
    location_id: str = ""             # Optional link to a Location
    npc_ids: List[str] = field(default_factory=list)  # Optional linked NPCs
    visible: bool = True              # Can be hidden from player view
    overlay: str = "surface"          # Overlay layer this pin belongs to
    # A pin can "open" something when clicked. Supported actions:
    #   "open_submap:<location_id>" - drill into that location's sub-map
    #   "open_location:<location_id>" - switch campaign view to that location
    #   "open_url:<url>" - open an external URL
    #   "" - no default action (falls back to selection)
    open_action: str = ""


# Pin type display defaults
MAP_PIN_TYPES = {
    "note":     {"icon": "N", "color": "#AAAAAA", "label": "Note"},
    "poi":      {"icon": "!", "color": "#FFD700", "label": "Point of Interest"},
    "danger":   {"icon": "X", "color": "#FF4444", "label": "Danger"},
    "treasure": {"icon": "$", "color": "#44FF44", "label": "Treasure"},
    "quest":    {"icon": "?", "color": "#4488FF", "label": "Quest"},
    "camp":     {"icon": "C", "color": "#FF8844", "label": "Camp/Rest"},
    "encounter":{"icon": "E", "color": "#FF2222", "label": "Encounter"},
    "custom":   {"icon": "*", "color": "#CCCCCC", "label": "Custom"},
}


@dataclass
class MapToken:
    """A movable token on the world map (party, NPC caravan, encounter, etc.)."""
    id: str = ""
    name: str = "Token"
    token_type: str = "party"           # party, npc, encounter, caravan, custom
    icon: str = ""                      # 1-2 char icon (empty = auto)
    color: str = ""                     # Custom hex color
    map_x: float = 50.0                # X position (percentage 0-100)
    map_y: float = 50.0                # Y position (percentage 0-100)
    notes: str = ""                     # DM notes
    npc_ids: List[str] = field(default_factory=list)  # Linked NPCs
    encounter_id: str = ""             # Linked encounter (for encounter tokens)
    visible: bool = True


MAP_TOKEN_TYPES = {
    "party":     {"icon": "P", "color": "#44BBFF", "label": "Party"},
    "npc":       {"icon": "N", "color": "#FFAA44", "label": "NPC Group"},
    "encounter": {"icon": "!", "color": "#FF4444", "label": "Encounter"},
    "caravan":   {"icon": "C", "color": "#DDAA44", "label": "Caravan"},
    "custom":    {"icon": "*", "color": "#CCCCCC", "label": "Custom"},
}


@dataclass
class MapRoute:
    """A travel route between two locations on the map."""
    from_id: str = ""
    to_id: str = ""
    route_type: str = "road"          # road, trail, river, sea, air, secret
    label: str = ""                   # Optional label (e.g. "3 days", "King's Road")
    color: str = ""                   # Custom hex color (empty = auto from type)
    distance_miles: float = 0.0       # Distance in miles
    notes: str = ""                   # DM notes about this route
    danger_level: str = "safe"        # safe, low, medium, high, deadly
    terrain_type: str = "road"        # Terrain for travel time calc (road, forest, hills, etc.)
    encounter_ids: List[str] = field(default_factory=list)  # Encounter IDs along this route
    overlay: str = "surface"          # Overlay layer this route belongs to


# ---- Multi-point travel paths (waypoint routes) ----------------------------

@dataclass
class MapPath:
    """A multi-waypoint travel path drawn on the map.

    Unlike MapRoute (two-endpoint, tied to locations), MapPath is a free
    polyline of (map_x%, map_y%) waypoints with per-path terrain and notes.
    Used for winding roads, rivers, or marches of the party across terrain.
    """
    id: str = ""
    name: str = "New Path"
    path_type: str = "road"           # road, trail, river, sea, air, secret, party
    color: str = ""                   # Custom hex color (empty = auto from type)
    points: List[list] = field(default_factory=list)  # [[x%, y%], ...] (pct coords)
    terrain_type: str = "road"        # For travel-time estimation
    label: str = ""                   # Optional static label
    notes: str = ""                   # DM notes
    danger_level: str = "safe"        # safe, low, medium, high, deadly
    distance_miles: float = 0.0       # 0 = auto-estimate from scale
    visible: bool = True
    overlay: str = "surface"          # Overlay layer


# ---- Freehand drawings -----------------------------------------------------

@dataclass
class MapDrawing:
    """A freehand annotation stroke drawn on top of the map.

    Stored as a list of (x%, y%) points. The DM can sketch routes,
    circle regions of interest, write highlights, etc. Each stroke keeps
    its own color/width so the DM can build up layered sketches.
    """
    id: str = ""
    points: List[list] = field(default_factory=list)    # [[x%, y%], ...]
    color: str = "#FFDD44"
    width: int = 3                     # Stroke thickness in pixels at 1.0 zoom
    shape: str = "freehand"            # freehand, line, rect, circle
    label: str = ""                    # Optional text label at first point
    notes: str = ""
    visible: bool = True
    overlay: str = "surface"           # Overlay layer


# ---- Overlay layers --------------------------------------------------------
# Overlays are tag filters that hide/show pins, paths, routes, and drawings
# belonging to a specific layer (surface, underdark levels, effects, etc.).
# They do NOT swap background images — use Location.map_image_path for that.

MAP_OVERLAYS = {
    "surface":      {"label": "Surface",       "color": "#8BC34A"},
    "underdark_1":  {"label": "Upperdark",     "color": "#795548"},
    "underdark_2":  {"label": "Middledark",    "color": "#5D4037"},
    "underdark_3":  {"label": "Lowerdark",     "color": "#3E2723"},
    "underwater":   {"label": "Underwater",    "color": "#0288D1"},
    "feywild":      {"label": "Feywild",       "color": "#E91E63"},
    "shadowfell":   {"label": "Shadowfell",    "color": "#424242"},
    "ethereal":     {"label": "Ethereal",      "color": "#9575CD"},
    "astral":       {"label": "Astral",        "color": "#5C6BC0"},
    "effects":      {"label": "Effects/Weather", "color": "#FF9800"},
    "political":    {"label": "Political",     "color": "#F44336"},
    "secret":       {"label": "DM-only",       "color": "#9C27B0"},
}


@dataclass
class World:
    """Top-level world data — all locations and NPCs."""
    name: str = "New World"
    description: str = ""
    created: str = ""
    last_modified: str = ""
    locations: Dict[str, Location] = field(default_factory=dict)  # id -> Location
    npcs: Dict[str, NPC] = field(default_factory=dict)            # id -> NPC
    quests: Dict[str, Quest] = field(default_factory=dict)        # id -> Quest
    next_id: int = 1                  # Auto-increment for IDs
    # Map data
    map_routes: List[MapRoute] = field(default_factory=list)
    map_pins: List[MapPin] = field(default_factory=list)          # Map pin annotations
    map_tokens: List[MapToken] = field(default_factory=list)      # Movable tokens on map
    map_paths: List["MapPath"] = field(default_factory=list)      # Multi-waypoint travel paths
    map_drawings: List["MapDrawing"] = field(default_factory=list)  # Freehand annotations
    map_image_path: str = ""          # Path to custom background image
    map_positions: Dict[str, list] = field(default_factory=dict)  # loc_id -> [x%, y%]
    map_scale_miles: float = 0.0      # Miles per 100% map width (0 = unset)
    map_scale_reference: float = 0.0  # Reference distance in map % for scale calibration
    # Overlay visibility: overlay_key -> bool (True = visible). Missing = visible.
    map_overlay_visible: Dict[str, bool] = field(default_factory=dict)
    map_active_overlay: str = "surface"  # Overlay new annotations attach to


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
    d = {
        "id": loc.id, "name": loc.name, "location_type": loc.location_type,
        "description": loc.description, "notes": loc.notes,
        "parent_id": loc.parent_id, "children_ids": loc.children_ids,
        "npc_ids": loc.npc_ids, "tags": loc.tags,
        "environment": loc.environment, "lighting": loc.lighting,
    }
    # Save map fields only if set (backwards compat)
    if loc.map_color:
        d["map_color"] = loc.map_color
    if loc.map_icon:
        d["map_icon"] = loc.map_icon
    if loc.map_note:
        d["map_note"] = loc.map_note
    if loc.population:
        d["population"] = loc.population
    if loc.map_size:
        d["map_size"] = loc.map_size
    # Extended info (only if set)
    if loc.map_image_path:
        d["map_image_path"] = loc.map_image_path
    for field_name in ("government", "dominant_races", "languages", "religion",
                       "wealth_level", "defenses", "known_for"):
        val = getattr(loc, field_name, "")
        if val:
            d[field_name] = val
    return d

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
        map_color=d.get("map_color", ""),
        map_icon=d.get("map_icon", ""),
        map_note=d.get("map_note", ""),
        population=d.get("population", 0),
        map_size=d.get("map_size", 0),
        map_image_path=d.get("map_image_path", ""),
        government=d.get("government", ""),
        dominant_races=d.get("dominant_races", ""),
        languages=d.get("languages", ""),
        religion=d.get("religion", ""),
        wealth_level=d.get("wealth_level", ""),
        defenses=d.get("defenses", ""),
        known_for=d.get("known_for", ""),
    )

def _serialize_npc(npc: NPC) -> dict:
    return {
        "id": npc.id, "name": npc.name,
        "race": npc.race, "gender": npc.gender, "age": npc.age,
        "appearance": npc.appearance, "personality": npc.personality,
        "backstory": npc.backstory, "occupation": npc.occupation,
        "attitude": npc.attitude, "notes": npc.notes, "tags": npc.tags,
        "title": npc.title, "faction": npc.faction, "alignment": npc.alignment,
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
        occupation=d.get("occupation", ""),
        title=d.get("title", ""), faction=d.get("faction", ""), alignment=d.get("alignment", ""),
        attitude=d.get("attitude", "neutral"),
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

def _serialize_route(r: MapRoute) -> dict:
    return {
        "from_id": r.from_id, "to_id": r.to_id, "route_type": r.route_type,
        "label": r.label, "color": r.color, "distance_miles": r.distance_miles,
        "notes": r.notes, "danger_level": r.danger_level,
        "terrain_type": r.terrain_type, "encounter_ids": r.encounter_ids,
        "overlay": r.overlay,
    }

def _deserialize_route(d: dict) -> MapRoute:
    return MapRoute(
        from_id=d.get("from_id", ""), to_id=d.get("to_id", ""),
        route_type=d.get("route_type", "road"), label=d.get("label", ""),
        color=d.get("color", ""), distance_miles=d.get("distance_miles", 0),
        notes=d.get("notes", ""), danger_level=d.get("danger_level", "safe"),
        terrain_type=d.get("terrain_type", "road"),
        encounter_ids=d.get("encounter_ids", []),
        overlay=d.get("overlay", "surface"),
    )


def _serialize_path(p: MapPath) -> dict:
    return {
        "id": p.id, "name": p.name, "path_type": p.path_type,
        "color": p.color, "points": [[pt[0], pt[1]] for pt in p.points],
        "terrain_type": p.terrain_type, "label": p.label, "notes": p.notes,
        "danger_level": p.danger_level, "distance_miles": p.distance_miles,
        "visible": p.visible, "overlay": p.overlay,
    }

def _deserialize_path(d: dict) -> MapPath:
    pts = d.get("points", []) or []
    # Normalise to list of [x, y]
    norm = []
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            try:
                norm.append([float(p[0]), float(p[1])])
            except (TypeError, ValueError):
                continue
    return MapPath(
        id=d.get("id", ""), name=d.get("name", "Path"),
        path_type=d.get("path_type", "road"),
        color=d.get("color", ""), points=norm,
        terrain_type=d.get("terrain_type", "road"),
        label=d.get("label", ""), notes=d.get("notes", ""),
        danger_level=d.get("danger_level", "safe"),
        distance_miles=d.get("distance_miles", 0.0),
        visible=d.get("visible", True),
        overlay=d.get("overlay", "surface"),
    )


def _serialize_drawing(dw: MapDrawing) -> dict:
    return {
        "id": dw.id, "points": [[pt[0], pt[1]] for pt in dw.points],
        "color": dw.color, "width": dw.width, "shape": dw.shape,
        "label": dw.label, "notes": dw.notes,
        "visible": dw.visible, "overlay": dw.overlay,
    }

def _deserialize_drawing(d: dict) -> MapDrawing:
    pts = d.get("points", []) or []
    norm = []
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            try:
                norm.append([float(p[0]), float(p[1])])
            except (TypeError, ValueError):
                continue
    return MapDrawing(
        id=d.get("id", ""), points=norm,
        color=d.get("color", "#FFDD44"), width=int(d.get("width", 3)),
        shape=d.get("shape", "freehand"),
        label=d.get("label", ""), notes=d.get("notes", ""),
        visible=d.get("visible", True),
        overlay=d.get("overlay", "surface"),
    )

def _serialize_token(t: MapToken) -> dict:
    return {
        "id": t.id, "name": t.name, "token_type": t.token_type,
        "icon": t.icon, "color": t.color, "map_x": t.map_x, "map_y": t.map_y,
        "notes": t.notes, "npc_ids": t.npc_ids,
        "encounter_id": t.encounter_id, "visible": t.visible,
    }

def _deserialize_token(d: dict) -> MapToken:
    return MapToken(
        id=d.get("id", ""), name=d.get("name", "Token"),
        token_type=d.get("token_type", "party"),
        icon=d.get("icon", ""), color=d.get("color", ""),
        map_x=d.get("map_x", 50.0), map_y=d.get("map_y", 50.0),
        notes=d.get("notes", ""), npc_ids=d.get("npc_ids", []),
        encounter_id=d.get("encounter_id", ""), visible=d.get("visible", True),
    )

def _serialize_pin(p: MapPin) -> dict:
    return {
        "id": p.id, "name": p.name, "pin_type": p.pin_type,
        "description": p.description, "notes": p.notes, "links": p.links,
        "icon": p.icon, "color": p.color, "map_x": p.map_x, "map_y": p.map_y,
        "location_id": p.location_id, "npc_ids": p.npc_ids, "visible": p.visible,
        "overlay": p.overlay, "open_action": p.open_action,
    }

def _deserialize_pin(d: dict) -> MapPin:
    return MapPin(
        id=d.get("id", ""), name=d.get("name", "New Pin"),
        pin_type=d.get("pin_type", "note"),
        description=d.get("description", ""), notes=d.get("notes", ""),
        links=d.get("links", []), icon=d.get("icon", ""), color=d.get("color", ""),
        map_x=d.get("map_x", 0.0), map_y=d.get("map_y", 0.0),
        location_id=d.get("location_id", ""), npc_ids=d.get("npc_ids", []),
        visible=d.get("visible", True),
        overlay=d.get("overlay", "surface"),
        open_action=d.get("open_action", ""),
    )


def _serialize_quest_objective(obj: QuestObjective) -> dict:
    return {
        "description": obj.description, "completed": obj.completed,
        "notes": obj.notes, "target_npc_id": obj.target_npc_id,
        "target_location_id": obj.target_location_id, "target_item": obj.target_item,
    }

def _deserialize_quest_objective(d: dict) -> QuestObjective:
    return QuestObjective(
        description=d.get("description", ""), completed=d.get("completed", False),
        notes=d.get("notes", ""), target_npc_id=d.get("target_npc_id", ""),
        target_location_id=d.get("target_location_id", ""),
        target_item=d.get("target_item", ""),
    )

def _serialize_quest(q: Quest) -> dict:
    return {
        "id": q.id, "name": q.name, "description": q.description,
        "status": q.status, "priority": q.priority, "quest_type": q.quest_type,
        "giver_npc_id": q.giver_npc_id, "turn_in_npc_id": q.turn_in_npc_id,
        "location_ids": q.location_ids, "npc_ids": q.npc_ids,
        "objectives": [_serialize_quest_objective(o) for o in q.objectives],
        "reward_xp": q.reward_xp, "reward_gold": q.reward_gold,
        "reward_items": q.reward_items, "reward_notes": q.reward_notes,
        "notes": q.notes, "tags": q.tags,
        "created": q.created, "completed_date": q.completed_date,
        "session_given": q.session_given, "level_range": q.level_range,
    }

def _deserialize_quest(d: dict) -> Quest:
    return Quest(
        id=d.get("id", ""), name=d.get("name", ""),
        description=d.get("description", ""),
        status=d.get("status", "active"), priority=d.get("priority", "normal"),
        quest_type=d.get("quest_type", "main"),
        giver_npc_id=d.get("giver_npc_id", ""),
        turn_in_npc_id=d.get("turn_in_npc_id", ""),
        location_ids=d.get("location_ids", []), npc_ids=d.get("npc_ids", []),
        objectives=[_deserialize_quest_objective(o) for o in d.get("objectives", [])],
        reward_xp=d.get("reward_xp", 0), reward_gold=d.get("reward_gold", 0),
        reward_items=d.get("reward_items", []),
        reward_notes=d.get("reward_notes", ""),
        notes=d.get("notes", ""), tags=d.get("tags", []),
        created=d.get("created", ""), completed_date=d.get("completed_date", ""),
        session_given=d.get("session_given", 0), level_range=d.get("level_range", ""),
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
        "quests": {k: _serialize_quest(v) for k, v in world.quests.items()},
        "next_id": world.next_id,
        "map_routes": [_serialize_route(r) for r in world.map_routes],
        "map_pins": [_serialize_pin(p) for p in world.map_pins],
        "map_tokens": [_serialize_token(t) for t in world.map_tokens],
        "map_paths": [_serialize_path(p) for p in world.map_paths],
        "map_drawings": [_serialize_drawing(d) for d in world.map_drawings],
        "map_image_path": world.map_image_path,
        "map_positions": world.map_positions,
        "map_scale_miles": world.map_scale_miles,
        "map_scale_reference": world.map_scale_reference,
        "map_overlay_visible": dict(world.map_overlay_visible),
        "map_active_overlay": world.map_active_overlay,
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
        quests={k: _deserialize_quest(v) for k, v in data.get("quests", {}).items()},
        next_id=data.get("next_id", 1),
        map_routes=[_deserialize_route(r) for r in data.get("map_routes", [])],
        map_pins=[_deserialize_pin(p) for p in data.get("map_pins", [])],
        map_tokens=[_deserialize_token(t) for t in data.get("map_tokens", [])],
        map_paths=[_deserialize_path(p) for p in data.get("map_paths", [])],
        map_drawings=[_deserialize_drawing(d) for d in data.get("map_drawings", [])],
        map_image_path=data.get("map_image_path", ""),
        map_positions=data.get("map_positions", {}),
        map_scale_miles=data.get("map_scale_miles", 0.0),
        map_scale_reference=data.get("map_scale_reference", 0.0),
        map_overlay_visible=data.get("map_overlay_visible", {}),
        map_active_overlay=data.get("map_active_overlay", "surface"),
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


# ============================================================================
# MAP PIN HELPERS
# ============================================================================

def add_pin(world: World, name: str, pin_type: str = "note",
            map_x: float = 50.0, map_y: float = 50.0, **kwargs) -> MapPin:
    """Create and add a new map pin to the world."""
    pin = MapPin(
        id=generate_id(world, "pin"),
        name=name,
        pin_type=pin_type,
        map_x=map_x,
        map_y=map_y,
        **kwargs,
    )
    world.map_pins.append(pin)
    return pin


def remove_pin(world: World, pin_id: str):
    """Remove a map pin by ID."""
    world.map_pins = [p for p in world.map_pins if p.id != pin_id]


def get_pin_by_id(world: World, pin_id: str) -> Optional[MapPin]:
    """Get a map pin by its ID."""
    for p in world.map_pins:
        if p.id == pin_id:
            return p
    return None


def get_pins_at_location(world: World, location_id: str) -> List[MapPin]:
    """Get all map pins linked to a specific location."""
    return [p for p in world.map_pins if p.location_id == location_id]


def get_pins_by_type(world: World, pin_type: str) -> List[MapPin]:
    """Get all map pins of a specific type."""
    return [p for p in world.map_pins if p.pin_type == pin_type]


def get_visible_pins(world: World) -> List[MapPin]:
    """Get all visible map pins."""
    return [p for p in world.map_pins if p.visible]


def search_pins(world: World, query: str) -> List[MapPin]:
    """Search map pins by name, description, or notes."""
    q = query.lower()
    return [p for p in world.map_pins
            if q in p.name.lower() or q in p.description.lower() or q in p.notes.lower()]


# ============================================================================
# MAP TOKEN HELPERS
# ============================================================================

def add_token(world: World, name: str, token_type: str = "party",
              map_x: float = 50.0, map_y: float = 50.0, **kwargs) -> MapToken:
    """Add a new map token."""
    token = MapToken(
        id=generate_id(world, "tok"),
        name=name, token_type=token_type,
        map_x=map_x, map_y=map_y, **kwargs,
    )
    world.map_tokens.append(token)
    return token

def remove_token(world: World, token_id: str):
    """Remove a map token by ID."""
    world.map_tokens = [t for t in world.map_tokens if t.id != token_id]

def get_token_by_id(world: World, token_id: str) -> Optional[MapToken]:
    """Get token by ID."""
    for t in world.map_tokens:
        if t.id == token_id:
            return t
    return None

# ============================================================================
# MAP PATH HELPERS (multi-waypoint polylines)
# ============================================================================

def add_path(world: World, name: str = "New Path", path_type: str = "road",
             points: Optional[List[list]] = None, overlay: str = "",
             **kwargs) -> MapPath:
    """Add a new multi-waypoint path to the world."""
    path = MapPath(
        id=generate_id(world, "path"),
        name=name, path_type=path_type,
        points=[list(p) for p in (points or [])],
        overlay=overlay or world.map_active_overlay or "surface",
        **kwargs,
    )
    world.map_paths.append(path)
    return path


def remove_path(world: World, path_id: str):
    world.map_paths = [p for p in world.map_paths if p.id != path_id]


def get_path_by_id(world: World, path_id: str) -> Optional[MapPath]:
    for p in world.map_paths:
        if p.id == path_id:
            return p
    return None


def path_length_pct(path: MapPath) -> float:
    """Total polyline length in map-percent units."""
    import math
    if len(path.points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(path.points)):
        x0, y0 = path.points[i - 1][0], path.points[i - 1][1]
        x1, y1 = path.points[i][0], path.points[i][1]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def path_length_miles(world: World, path: MapPath) -> float:
    """Distance in miles. Uses stored override if >0, else map scale."""
    if path.distance_miles > 0:
        return path.distance_miles
    if world.map_scale_miles <= 0:
        return 0.0
    return path_length_pct(path) * world.map_scale_miles / 100.0


# ============================================================================
# MAP DRAWING HELPERS (freehand annotations)
# ============================================================================

def add_drawing(world: World, points: Optional[List[list]] = None,
                color: str = "#FFDD44", width: int = 3,
                shape: str = "freehand", overlay: str = "",
                **kwargs) -> MapDrawing:
    """Add a new freehand drawing stroke."""
    dw = MapDrawing(
        id=generate_id(world, "draw"),
        points=[list(p) for p in (points or [])],
        color=color, width=width, shape=shape,
        overlay=overlay or world.map_active_overlay or "surface",
        **kwargs,
    )
    world.map_drawings.append(dw)
    return dw


def remove_drawing(world: World, drawing_id: str):
    world.map_drawings = [d for d in world.map_drawings if d.id != drawing_id]


def clear_drawings(world: World, overlay: str = ""):
    """Remove all drawings, or only those on a specific overlay."""
    if overlay:
        world.map_drawings = [d for d in world.map_drawings if d.overlay != overlay]
    else:
        world.map_drawings = []


# ============================================================================
# OVERLAY LAYER HELPERS
# ============================================================================

def is_overlay_visible(world: World, overlay: str) -> bool:
    """Whether items on a given overlay should render. Missing = visible."""
    if not overlay:
        overlay = "surface"
    return world.map_overlay_visible.get(overlay, True)


def set_overlay_visible(world: World, overlay: str, visible: bool):
    world.map_overlay_visible[overlay] = visible


def toggle_overlay(world: World, overlay: str):
    world.map_overlay_visible[overlay] = not is_overlay_visible(world, overlay)


def get_route_distance_miles(world: World, from_id: str, to_id: str) -> float:
    """Get the distance in miles between two locations via route. Returns 0 if no route."""
    for route in world.map_routes:
        if (route.from_id == from_id and route.to_id == to_id) or \
           (route.from_id == to_id and route.to_id == from_id):
            return route.distance_miles
    return 0.0

def calculate_map_distance_pct(world: World, from_id: str, to_id: str) -> float:
    """Calculate straight-line distance between two locations in map percentage units."""
    import math
    pos_a = world.map_positions.get(from_id)
    pos_b = world.map_positions.get(to_id)
    if not pos_a or not pos_b:
        return 0.0
    return math.hypot(pos_a[0] - pos_b[0], pos_a[1] - pos_b[1])

def estimate_route_miles_from_scale(world: World, from_id: str, to_id: str) -> float:
    """Estimate miles between two locations using map scale (if set)."""
    if world.map_scale_miles <= 0:
        return 0.0
    dist_pct = calculate_map_distance_pct(world, from_id, to_id)
    return dist_pct * world.map_scale_miles / 100.0


def get_shopkeepers(world: World) -> List[NPC]:
    """Get all active shopkeeper NPCs."""
    return [npc for npc in world.npcs.values() if npc.is_shopkeeper and npc.active]


def get_shopkeepers_at_location(world: World, location_id: str) -> List[NPC]:
    """Get shopkeeper NPCs at a specific location."""
    return [npc for npc in world.npcs.values()
            if npc.is_shopkeeper and npc.active and npc.location_id == location_id]


# ============================================================================
# QUEST MANAGEMENT
# ============================================================================

def add_quest(world: World, name: str, **kwargs) -> Quest:
    """Create and add a new quest to the world."""
    qid = generate_id(world, "quest")
    q = Quest(id=qid, name=name, created=_timestamp(), **kwargs)
    world.quests[qid] = q
    return q

def delete_quest(world: World, quest_id: str):
    """Delete a quest from the world."""
    world.quests.pop(quest_id, None)

def get_quests_by_status(world: World, status: str) -> List[Quest]:
    """Get all quests with a given status."""
    return [q for q in world.quests.values() if q.status == status]

def get_quests_for_npc(world: World, npc_id: str) -> List[Quest]:
    """Get all quests involving a specific NPC (as giver, turn-in, or related)."""
    return [q for q in world.quests.values()
            if q.giver_npc_id == npc_id or q.turn_in_npc_id == npc_id or npc_id in q.npc_ids]

def get_quests_for_location(world: World, location_id: str) -> List[Quest]:
    """Get all quests involving a specific location."""
    return [q for q in world.quests.values() if location_id in q.location_ids]

def search_quests(world: World, query: str) -> List[Quest]:
    """Search quests by name, description, or tags."""
    q = query.lower()
    return [quest for quest in world.quests.values()
            if q in quest.name.lower() or q in quest.description.lower()
            or any(q in t.lower() for t in quest.tags)]

def get_active_quests(world: World) -> List[Quest]:
    """Get all active quests."""
    return [q for q in world.quests.values() if q.status == "active"]

def complete_quest(world: World, quest_id: str):
    """Mark a quest as completed."""
    q = world.quests.get(quest_id)
    if q:
        q.status = "completed"
        q.completed_date = _timestamp()
