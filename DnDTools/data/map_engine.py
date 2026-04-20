"""
World Map Engine — Phase 1 foundation for the interactive map editor.

Defines the tile-layer-object data model used by the WorldMap editor. Separate
from the combat grid terrain (engine/terrain.py). Persists as JSON files in
saves/maps/<map_id>.json, referenced by ID from a World or Campaign.

See plan.md "Phase 1: Map Engine Foundation" for the reference spec.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple


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
    # Settlements
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
    "treasure":      {"icon": "$", "size": 0.6, "color": (255, 215, 0)},
    "camp":          {"icon": "^", "size": 0.7, "color": (200, 140, 60)},
    # D&D-specific
    "temple":        {"icon": "+", "size": 0.9, "color": (255, 240, 180)},
    "tavern":        {"icon": "B", "size": 0.7, "color": (200, 160, 80)},
    "shop":          {"icon": "$", "size": 0.6, "color": (200, 180, 40)},
    "guild":         {"icon": "G", "size": 0.8, "color": (160, 160, 200)},
    "dock":          {"icon": "&", "size": 0.8, "color": (80, 140, 200)},
}


MAP_TYPES: Tuple[str, ...] = ("world", "region", "town", "dungeon")
LAYER_TYPES: Tuple[str, ...] = ("surface", "underground", "plane")


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class MapObject:
    id: str = ""
    x: float = 0.0              # world percentage 0-100 (tile-independent)
    y: float = 0.0
    object_type: str = "info_pin"
    icon: str = ""
    color: Tuple[int, int, int] = (200, 200, 200)
    size: float = 1.0
    label: str = ""
    linked_location_id: str = ""
    linked_info: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id("obj")
        # Fill visual defaults from palette if caller didn't.
        proto = MAP_OBJECT_TYPES.get(self.object_type)
        if proto:
            if not self.icon:
                self.icon = proto["icon"]
            if self.color == (200, 200, 200):
                self.color = proto["color"]
            if self.size == 1.0 and proto["size"] != 1.0:
                self.size = proto["size"]


@dataclass
class MapLayer:
    id: str = ""
    name: str = "Surface"
    layer_type: str = "surface"
    depth: int = 0
    visible: bool = True
    opacity: float = 1.0
    tiles: Dict[str, str] = field(default_factory=dict)  # "x,y" -> brush_key
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
        """Paint a square brush of side (2*radius+1) centred on (cx,cy)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                self.set_tile(cx + dx, cy + dy, brush_key)

    def flood_fill(self, x: int, y: int, brush_key: str,
                   width: int, height: int) -> int:
        """4-connected flood fill starting at (x,y). Returns tiles changed.
        Bounded by (width, height) of the map so it cannot run to infinity."""
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
    parent_map_id: str = ""
    width: int = 64
    height: int = 48
    tile_size: int = 24
    layers: List[MapLayer] = field(default_factory=list)
    active_layer_idx: int = 0
    background_image: str = ""
    grid_visible: bool = True
    grid_color: Tuple[int, int, int] = (60, 60, 80)
    created: str = ""
    last_modified: str = ""
    # Camera (not serialized)
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


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------

MAPS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves", "maps"
)


def _now_stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def serialize_world_map(wm: WorldMap) -> dict:
    """Dump a WorldMap to a JSON-ready dict. Skips transient camera state."""
    data = asdict(wm)
    for key in WorldMap._TRANSIENT_FIELDS:
        data.pop(key, None)
    # Tuples become lists through asdict -> ensure consistent shape.
    data["grid_color"] = list(wm.grid_color)
    for i, layer_dict in enumerate(data["layers"]):
        layer_dict["background_color"] = list(wm.layers[i].background_color)
        for j, obj_dict in enumerate(layer_dict["objects"]):
            obj_dict["color"] = list(wm.layers[i].objects[j].color)
    return data


def deserialize_world_map(data: dict) -> WorldMap:
    """Reconstruct a WorldMap from a dict produced by serialize_world_map()."""
    layers = []
    for ldata in data.get("layers", []):
        objects = []
        for odata in ldata.get("objects", []):
            obj = MapObject(
                id=odata.get("id", ""),
                x=float(odata.get("x", 0.0)),
                y=float(odata.get("y", 0.0)),
                object_type=odata.get("object_type", "info_pin"),
                icon=odata.get("icon", ""),
                color=tuple(odata.get("color", (200, 200, 200))),
                size=float(odata.get("size", 1.0)),
                label=odata.get("label", ""),
                linked_location_id=odata.get("linked_location_id", ""),
                linked_info=odata.get("linked_info", ""),
                tags=list(odata.get("tags", [])),
            )
            objects.append(obj)
        layers.append(MapLayer(
            id=ldata.get("id", ""),
            name=ldata.get("name", "Surface"),
            layer_type=ldata.get("layer_type", "surface"),
            depth=int(ldata.get("depth", 0)),
            visible=bool(ldata.get("visible", True)),
            opacity=float(ldata.get("opacity", 1.0)),
            tiles=dict(ldata.get("tiles", {})),
            objects=objects,
            background_color=tuple(ldata.get("background_color", (30, 40, 55))),
        ))

    wm = WorldMap(
        id=data.get("id", ""),
        name=data.get("name", "New Map"),
        map_type=data.get("map_type", "world"),
        parent_map_id=data.get("parent_map_id", ""),
        width=int(data.get("width", 64)),
        height=int(data.get("height", 48)),
        tile_size=int(data.get("tile_size", 24)),
        layers=layers or [MapLayer(name="Surface")],
        active_layer_idx=int(data.get("active_layer_idx", 0)),
        background_image=data.get("background_image", ""),
        grid_visible=bool(data.get("grid_visible", True)),
        grid_color=tuple(data.get("grid_color", (60, 60, 80))),
        created=data.get("created", _now_stamp()),
        last_modified=data.get("last_modified", _now_stamp()),
    )
    return wm


def save_world_map(wm: WorldMap, directory: str = MAPS_DIR) -> str:
    """Persist a WorldMap to <directory>/<id>.json. Returns the file path."""
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
    """Return a sorted list of .json files in the maps directory."""
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory) if f.endswith(".json"))
