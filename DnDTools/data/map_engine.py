"""
World Map Engine — tile/pixel-layer data model for the interactive map editor.

Separate from the combat grid terrain (engine/terrain.py). Persists as JSON
files in saves/maps/<map_id>.json. Each WorldMap is self-contained and can:
  * Host an uploaded background image (e.g. an Inkarnate JPG) at any resolution.
  * Carry terrain tile layers painted on top of the background.
  * Hold objects (pins, tokens, treasures, traps, armies) with links to
    Locations, NPCs, sub-maps and encounters.
  * Store user-drawn annotation paths used for distance measurement or route
    illustrations.

See plan.md and design discussion in claude/dnd-gm-assistant-tool-n03eS.
"""
from __future__ import annotations

import json
import os
import time
import uuid
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional


# ----------------------------------------------------------------------
# Brush & object palettes
# ----------------------------------------------------------------------

TERRAIN_BRUSHES: Dict[str, Dict] = {
    # Land
    "grass":        {"color": (86, 140, 60),  "icon": "",   "category": "land"},
    "forest":       {"color": (34, 90, 34),   "icon": "T",  "category": "land"},
    "dense_forest": {"color": (20, 60, 20),   "icon": "TT", "category": "land"},
    "hills":        {"color": (140, 120, 70), "icon": "^",  "category": "land"},
    "mountain":     {"color": (130, 130, 140),"icon": "M",  "category": "land"},
    "snow":         {"color": (220, 225, 235),"icon": "",   "category": "land"},
    "desert":       {"color": (210, 190, 130),"icon": "",   "category": "land"},
    "swamp":        {"color": (70, 90, 50),   "icon": "~",  "category": "land"},
    "tundra":       {"color": (170, 180, 175),"icon": "",   "category": "land"},
    "farmland":     {"color": (160, 170, 60), "icon": "#",  "category": "land"},
    # Water
    "river":         {"color": (50, 110, 190),"icon": "~", "category": "water"},
    "lake":          {"color": (40, 90, 170), "icon": "~", "category": "water"},
    "ocean":         {"color": (25, 60, 130), "icon": "~", "category": "water"},
    "shallow_water": {"color": (70, 140, 210),"icon": "~", "category": "water"},
    "coast":         {"color": (180, 170, 120),"icon": "", "category": "water"},
    # Roads
    "road":   {"color": (150, 130, 95), "icon": "=", "category": "road"},
    "trail":  {"color": (120, 105, 75), "icon": "-", "category": "road"},
    "bridge": {"color": (140, 120, 80), "icon": "=", "category": "road"},
    # Special
    "lava":          {"color": (200, 60, 20),  "icon": "!", "category": "hazard"},
    "ice":           {"color": (180, 210, 240),"icon": "",  "category": "land"},
    "cave_entrance": {"color": (60, 50, 45),   "icon": "O", "category": "special"},
    "ruins":         {"color": (100, 90, 80),  "icon": "R", "category": "special"},
    "portal":        {"color": (160, 80, 200), "icon": "*", "category": "special"},
}


MAP_OBJECT_TYPES: Dict[str, Dict] = {
    # Settlements — click to open sub-map / NPC panel
    "capital": {"icon": "*",  "size": 2.0, "color": (255, 215, 0)},
    "city":    {"icon": "O",  "size": 1.5, "color": (200, 200, 220)},
    "town":    {"icon": "o",  "size": 1.0, "color": (160, 160, 180)},
    "village": {"icon": ".",  "size": 0.7, "color": (120, 120, 140)},
    "fort":    {"icon": "#",  "size": 1.2, "color": (180, 140, 100)},
    # Nature
    "single_tree":   {"icon": "T", "size": 0.5, "color": (40, 120, 40)},
    "mountain_peak": {"icon": "^", "size": 1.0, "color": (140, 140, 150)},
    "volcano":       {"icon": "^", "size": 1.2, "color": (200, 60, 30)},
    # Markers
    "info_pin":      {"icon": "i", "size": 0.6, "color": (80, 160, 255)},
    "quest_marker":  {"icon": "!", "size": 0.8, "color": (255, 200, 40)},
    "danger_marker": {"icon": "x", "size": 0.8, "color": (200, 40, 40)},
    "treasure":      {"icon": "$", "size": 0.7, "color": (255, 215, 0)},
    "trap":          {"icon": "X", "size": 0.6, "color": (220, 100, 40)},
    "camp":          {"icon": "^", "size": 0.7, "color": (200, 140, 60)},
    # D&D-specific
    "temple":        {"icon": "+", "size": 0.9, "color": (255, 240, 180)},
    "tavern":        {"icon": "B", "size": 0.7, "color": (200, 160, 80)},
    "shop":          {"icon": "$", "size": 0.6, "color": (200, 180, 40)},
    "guild":         {"icon": "G", "size": 0.8, "color": (160, 160, 200)},
    "dock":          {"icon": "&", "size": 0.8, "color": (80, 140, 200)},
    # Drill-down entrances (click to open sub-map)
    "cave":          {"icon": "O", "size": 0.8, "color": (60, 50, 45)},
    "dungeon":       {"icon": "D", "size": 0.9, "color": (90, 40, 40)},
    "portal_down":   {"icon": "v", "size": 0.8, "color": (160, 80, 200)},
    "portal_up":     {"icon": "^", "size": 0.8, "color": (160, 80, 200)},
    # Movable tokens
    "party_token":   {"icon": "P", "size": 1.0, "color": (70, 180, 255)},
    "npc_token":     {"icon": "N", "size": 0.8, "color": (255, 170, 70)},
    "army_token":    {"icon": "A", "size": 1.2, "color": (220, 90, 90)},
    "caravan":       {"icon": "C", "size": 0.9, "color": (220, 180, 80)},
    # Vehicles that can carry passengers (Actor ids stored in
    # passenger_actor_ids). Useful for ships, airships, caravans.
    "ship":          {"icon": "S", "size": 1.3, "color": (120, 180, 220)},
    "airship":       {"icon": "Z", "size": 1.4, "color": (180, 200, 240)},
    "wagon":         {"icon": "W", "size": 0.9, "color": (180, 140, 80)},
}


# Object categories that count as "settlements" — their single-instance nature
# is enforced by the kingdoms navigator so a city only exists in one place.
SETTLEMENT_TYPES = ("capital", "city", "town", "village", "fort")
# Object types that drill down into a sub-map when double-clicked.
DRILLDOWN_TYPES = ("capital", "city", "town", "village", "fort",
                   "cave", "dungeon", "portal_down", "portal_up")
# Object types that represent a movable party/NPC/army token.
TOKEN_TYPES = ("party_token", "npc_token", "army_token", "caravan",
                "ship", "airship", "wagon")
# Subset of tokens that carry passengers (linked via passenger_actor_ids).
VEHICLE_TYPES = ("caravan", "ship", "airship", "wagon")


MAP_TYPES: Tuple[str, ...] = ("world", "region", "town", "dungeon", "plane")
LAYER_TYPES: Tuple[str, ...] = ("surface", "underground", "plane")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------

@dataclass
class MapObject:
    """A pin, token, building marker, treasure cache, trap… anything placed on
    the map.  Position stored as world percentage (0-100) so it stays correct
    regardless of map resolution or zoom."""
    id: str = ""
    x: float = 0.0
    y: float = 0.0
    object_type: str = "info_pin"
    icon: str = ""
    color: Tuple[int, int, int] = (200, 200, 200)
    size: float = 1.0
    label: str = ""
    # Hover tooltip — short, shown while cursor is over the object.
    hover_info: str = ""
    # Long-form DM notes shown in the detail panel.
    notes: str = ""
    # Visibility / DM-only
    visible: bool = True
    dm_only: bool = False
    hidden: bool = False           # Alias used for hidden traps / secret doors
    discovered: bool = True        # When False, player view hides the marker
    # Links
    linked_location_id: str = ""   # World.locations id
    linked_npc_ids: List[str] = field(default_factory=list)
    linked_map_id: str = ""        # Drill-down to another WorldMap
    linked_encounter_id: str = ""  # Quick-start encounter from this token
    linked_info: str = ""          # Free-text extended info (legacy field)
    # Treasure-specific
    treasure_items: List[str] = field(default_factory=list)
    treasure_gold: float = 0.0
    # Trap-specific
    trap_save: str = ""            # "DC 15 DEX"
    trap_damage: str = ""          # "2d10 piercing"
    lockpick_dc: int = 0
    detect_dc: int = 0
    # Token / army-specific
    unit_count: int = 0
    unit_type: str = ""            # "orcs", "knights", etc.
    faction: str = ""              # Army allegiance
    # Movement along an AnnotationPath (party_token / caravan / army_token)
    follow_path_id: str = ""
    path_progress_miles: float = 0.0
    travel_speed_mult: float = 1.0
    # Link to the shared Actor registry so the same token (hero, NPC,
    # vehicle) keeps its identity across world/town/battle views.
    actor_id: str = ""
    # Vehicle manifest: Actor ids of the passengers currently aboard.
    # Only meaningful when object_type is in VEHICLE_TYPES.
    passenger_actor_ids: List[str] = field(default_factory=list)
    # Settlements (and other waypoints) the token has already crossed
    # while travelling along its current path. Keeps `advance_followers`
    # from re-emitting "passed Arenhold" on every subsequent step.
    visited_waypoint_ids: List[str] = field(default_factory=list)
    # Misc
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id("obj")
        proto = MAP_OBJECT_TYPES.get(self.object_type)
        if proto:
            if not self.icon:
                self.icon = proto["icon"]
            if self.color == (200, 200, 200):
                self.color = proto["color"]
            if self.size == 1.0 and proto["size"] != 1.0:
                self.size = proto["size"]

    # Convenience
    @property
    def is_drilldown(self) -> bool:
        return bool(self.linked_map_id) or self.object_type in DRILLDOWN_TYPES

    @property
    def is_token(self) -> bool:
        return self.object_type in TOKEN_TYPES


@dataclass
class AnnotationPath:
    """A user-drawn polyline on the map — typically a road, river or party
    travel trail.  Used for distance measurement (sum of segment lengths in
    map %, times the map scale)."""
    id: str = ""
    name: str = ""
    path_type: str = "route"       # route, road, river, secret, travel,
                                    # sea_route (ship-only), air_route
                                    # (flying-only)
    color: Tuple[int, int, int] = (230, 190, 70)
    thickness: int = 3
    points: List[Tuple[float, float]] = field(default_factory=list)  # world %
    dashed: bool = False
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _new_id("path")

    def length_pct(self) -> float:
        total = 0.0
        for i in range(1, len(self.points)):
            a = self.points[i - 1]
            b = self.points[i]
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        return total


@dataclass
class MapLayer:
    id: str = ""
    name: str = "Surface"
    layer_type: str = "surface"
    depth: int = 0
    visible: bool = True
    opacity: float = 1.0
    tiles: Dict[str, str] = field(default_factory=dict)
    objects: List[MapObject] = field(default_factory=list)
    background_color: Tuple[int, int, int] = (30, 40, 55)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id("layer")

    # ---- tile helpers ----
    @staticmethod
    def _key(x: int, y: int) -> str:
        return f"{x},{y}"

    def get_tile(self, x: int, y: int) -> str:
        return self.tiles.get(self._key(x, y), "")

    def set_tile(self, x: int, y: int, brush_key: str) -> None:
        if brush_key:
            self.tiles[self._key(x, y)] = brush_key
        else:
            self.tiles.pop(self._key(x, y), None)

    def erase_tile(self, x: int, y: int) -> None:
        self.tiles.pop(self._key(x, y), None)

    def paint_brush(self, cx: int, cy: int, brush_key: str, radius: int = 0) -> None:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                self.set_tile(cx + dx, cy + dy, brush_key)

    def flood_fill(self, x: int, y: int, brush_key: str,
                   width: int, height: int) -> int:
        if not (0 <= x < width and 0 <= y < height):
            return 0
        target = self.get_tile(x, y)
        if target == brush_key:
            return 0
        changed = 0
        stack = [(x, y)]
        seen = set()
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in seen:
                continue
            seen.add((cx, cy))
            if not (0 <= cx < width and 0 <= cy < height):
                continue
            if self.get_tile(cx, cy) != target:
                continue
            self.set_tile(cx, cy, brush_key)
            changed += 1
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
        return changed


@dataclass
class WorldMap:
    id: str = ""
    name: str = "New Map"
    map_type: str = "world"
    parent_map_id: str = ""        # Drill-up: cave map -> its overworld map
    owner_kingdom: str = ""        # Tarmaas / Fundarla / … for navigation
    width: int = 64
    height: int = 48
    tile_size: int = 24
    layers: List[MapLayer] = field(default_factory=list)
    active_layer_idx: int = 0
    background_image: str = ""     # Relative project path to uploaded JPG/PNG
    bg_opacity: float = 1.0
    grid_visible: bool = True
    grid_color: Tuple[int, int, int] = (60, 60, 80)
    # Scale calibration — lets the editor convert map-% distances to miles.
    scale_miles_per_pct: float = 1.0   # 1% of map width == this many miles
    travel_speed_miles_per_day: float = 24.0   # default overland march
    # User-drawn annotation paths (routes, rivers, travel lines)
    annotations: List[AnnotationPath] = field(default_factory=list)
    # Notes / description
    description: str = ""
    created: str = ""
    last_modified: str = ""
    # Camera (not serialized — transient view state)
    camera_x: float = 0.0
    camera_y: float = 0.0
    zoom: float = 1.0

    _TRANSIENT_FIELDS = ("camera_x", "camera_y", "zoom")

    def __post_init__(self):
        if not self.id:
            self.id = _new_id("map")
        if not self.created:
            self.created = _now_stamp()
        if not self.layers:
            self.layers.append(MapLayer(name="Surface", layer_type="surface", depth=0))
            self.active_layer_idx = 0
        self.active_layer_idx = max(0, min(self.active_layer_idx, len(self.layers) - 1))

    # ---- layer helpers ----
    @property
    def active_layer(self) -> MapLayer:
        return self.layers[self.active_layer_idx]

    def add_layer(self, name: str, layer_type: str = "surface", depth: int = 0) -> MapLayer:
        layer = MapLayer(name=name, layer_type=layer_type, depth=depth)
        self.layers.append(layer)
        self.active_layer_idx = len(self.layers) - 1
        return layer

    def remove_layer(self, idx: int) -> bool:
        if len(self.layers) <= 1 or not (0 <= idx < len(self.layers)):
            return False
        self.layers.pop(idx)
        if self.active_layer_idx >= len(self.layers):
            self.active_layer_idx = len(self.layers) - 1
        return True

    # ---- object helpers ----
    def all_objects(self) -> List[MapObject]:
        out: List[MapObject] = []
        for layer in self.layers:
            out.extend(layer.objects)
        return out

    def find_object(self, obj_id: str) -> Optional[MapObject]:
        for layer in self.layers:
            for obj in layer.objects:
                if obj.id == obj_id:
                    return obj
        return None

    def remove_object(self, obj_id: str) -> bool:
        for layer in self.layers:
            for i, obj in enumerate(layer.objects):
                if obj.id == obj_id:
                    del layer.objects[i]
                    return True
        return False

    # ---- geometry helpers ----
    def pct_to_miles(self, dx_pct: float, dy_pct: float) -> float:
        """Straight-line distance between two %-points converted to miles using
        the map's scale calibration.  Treats the horizontal axis as reference."""
        d = math.hypot(dx_pct, dy_pct)
        return d * max(self.scale_miles_per_pct, 0.0)

    def miles_to_travel_days(self, miles: float) -> float:
        spd = self.travel_speed_miles_per_day or 1.0
        return miles / spd


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------

MAPS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves", "maps"
)


def _obj_to_dict(obj: MapObject) -> dict:
    d = asdict(obj)
    d["color"] = list(obj.color)
    return d


def _obj_from_dict(d: dict) -> MapObject:
    return MapObject(
        id=d.get("id", ""),
        x=float(d.get("x", 0.0)),
        y=float(d.get("y", 0.0)),
        object_type=d.get("object_type", "info_pin"),
        icon=d.get("icon", ""),
        color=tuple(d.get("color", (200, 200, 200))),
        size=float(d.get("size", 1.0)),
        label=d.get("label", ""),
        hover_info=d.get("hover_info", ""),
        notes=d.get("notes", ""),
        visible=bool(d.get("visible", True)),
        dm_only=bool(d.get("dm_only", False)),
        hidden=bool(d.get("hidden", False)),
        discovered=bool(d.get("discovered", True)),
        linked_location_id=d.get("linked_location_id", ""),
        linked_npc_ids=list(d.get("linked_npc_ids", [])),
        linked_map_id=d.get("linked_map_id", ""),
        linked_encounter_id=d.get("linked_encounter_id", ""),
        linked_info=d.get("linked_info", ""),
        treasure_items=list(d.get("treasure_items", [])),
        treasure_gold=float(d.get("treasure_gold", 0.0)),
        trap_save=d.get("trap_save", ""),
        trap_damage=d.get("trap_damage", ""),
        lockpick_dc=int(d.get("lockpick_dc", 0)),
        detect_dc=int(d.get("detect_dc", 0)),
        unit_count=int(d.get("unit_count", 0)),
        unit_type=d.get("unit_type", ""),
        faction=d.get("faction", ""),
        follow_path_id=d.get("follow_path_id", ""),
        path_progress_miles=float(d.get("path_progress_miles", 0.0)),
        travel_speed_mult=float(d.get("travel_speed_mult", 1.0)),
        actor_id=d.get("actor_id", ""),
        passenger_actor_ids=list(d.get("passenger_actor_ids", [])),
        visited_waypoint_ids=list(d.get("visited_waypoint_ids", [])),
        tags=list(d.get("tags", [])),
    )


def _path_to_dict(p: AnnotationPath) -> dict:
    return {
        "id": p.id, "name": p.name, "path_type": p.path_type,
        "color": list(p.color), "thickness": p.thickness,
        "points": [list(pt) for pt in p.points],
        "dashed": p.dashed, "notes": p.notes,
    }


def _path_from_dict(d: dict) -> AnnotationPath:
    return AnnotationPath(
        id=d.get("id", ""), name=d.get("name", ""),
        path_type=d.get("path_type", "route"),
        color=tuple(d.get("color", (230, 190, 70))),
        thickness=int(d.get("thickness", 3)),
        points=[tuple(pt) for pt in d.get("points", [])],
        dashed=bool(d.get("dashed", False)),
        notes=d.get("notes", ""),
    )


def serialize_world_map(wm: WorldMap) -> dict:
    """Dump a WorldMap to a JSON-ready dict. Skips transient camera state."""
    return {
        "id": wm.id, "name": wm.name, "map_type": wm.map_type,
        "parent_map_id": wm.parent_map_id,
        "owner_kingdom": wm.owner_kingdom,
        "width": wm.width, "height": wm.height, "tile_size": wm.tile_size,
        "active_layer_idx": wm.active_layer_idx,
        "background_image": wm.background_image,
        "bg_opacity": wm.bg_opacity,
        "grid_visible": wm.grid_visible,
        "grid_color": list(wm.grid_color),
        "scale_miles_per_pct": wm.scale_miles_per_pct,
        "travel_speed_miles_per_day": wm.travel_speed_miles_per_day,
        "description": wm.description,
        "created": wm.created, "last_modified": wm.last_modified,
        "layers": [
            {
                "id": l.id, "name": l.name, "layer_type": l.layer_type,
                "depth": l.depth, "visible": l.visible, "opacity": l.opacity,
                "tiles": dict(l.tiles),
                "background_color": list(l.background_color),
                "objects": [_obj_to_dict(o) for o in l.objects],
            }
            for l in wm.layers
        ],
        "annotations": [_path_to_dict(p) for p in wm.annotations],
    }


def deserialize_world_map(data: dict) -> WorldMap:
    layers = []
    for ldata in data.get("layers", []):
        layers.append(MapLayer(
            id=ldata.get("id", ""),
            name=ldata.get("name", "Surface"),
            layer_type=ldata.get("layer_type", "surface"),
            depth=int(ldata.get("depth", 0)),
            visible=bool(ldata.get("visible", True)),
            opacity=float(ldata.get("opacity", 1.0)),
            tiles=dict(ldata.get("tiles", {})),
            objects=[_obj_from_dict(od) for od in ldata.get("objects", [])],
            background_color=tuple(ldata.get("background_color", (30, 40, 55))),
        ))

    return WorldMap(
        id=data.get("id", ""),
        name=data.get("name", "New Map"),
        map_type=data.get("map_type", "world"),
        parent_map_id=data.get("parent_map_id", ""),
        owner_kingdom=data.get("owner_kingdom", ""),
        width=int(data.get("width", 64)),
        height=int(data.get("height", 48)),
        tile_size=int(data.get("tile_size", 24)),
        layers=layers or [MapLayer(name="Surface")],
        active_layer_idx=int(data.get("active_layer_idx", 0)),
        background_image=data.get("background_image", ""),
        bg_opacity=float(data.get("bg_opacity", 1.0)),
        grid_visible=bool(data.get("grid_visible", True)),
        grid_color=tuple(data.get("grid_color", (60, 60, 80))),
        scale_miles_per_pct=float(data.get("scale_miles_per_pct", 1.0)),
        travel_speed_miles_per_day=float(data.get("travel_speed_miles_per_day", 24.0)),
        description=data.get("description", ""),
        created=data.get("created", _now_stamp()),
        last_modified=data.get("last_modified", _now_stamp()),
        annotations=[_path_from_dict(pd) for pd in data.get("annotations", [])],
    )


def save_world_map(wm: WorldMap, directory: str = MAPS_DIR) -> str:
    os.makedirs(directory, exist_ok=True)
    wm.last_modified = _now_stamp()
    path = os.path.join(directory, f"{wm.id}.json")
    with open(path, "w") as f:
        json.dump(serialize_world_map(wm), f, indent=2)
    return path


def load_world_map(path: str) -> WorldMap:
    with open(path) as f:
        return deserialize_world_map(json.load(f))


def list_world_maps(directory: str = MAPS_DIR) -> List[str]:
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if f.endswith(".json"))


def load_all_world_maps(directory: str = MAPS_DIR) -> Dict[str, WorldMap]:
    """Load every saved map into an {id: WorldMap} dict."""
    out: Dict[str, WorldMap] = {}
    for fname in list_world_maps(directory):
        try:
            wm = load_world_map(os.path.join(directory, fname))
            out[wm.id] = wm
        except Exception:
            continue
    return out


def delete_world_map(map_id: str, directory: str = MAPS_DIR) -> bool:
    path = os.path.join(directory, f"{map_id}.json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False
