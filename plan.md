# Interactive World Map System - Implementation Plan

## Overview
Transform the current simple node-based world map into a full interactive map editor
with drawing tools, multi-layer support, clickable town views, and D&D 5e info system.

---

## Phase 1: Map Engine Foundation (`data/map_engine.py`)

New data model for tile/pixel-based maps with layers.

### Data Structures
```python
@dataclass
class MapLayer:
    id: str
    name: str              # "Surface", "Underdark", "Feywild", etc.
    layer_type: str        # "surface", "underground", "plane"
    depth: int             # 0=surface, -1=underground, etc.
    visible: bool
    opacity: float         # 0.0-1.0
    tiles: Dict[str, str]  # "x,y" -> terrain_brush_key
    objects: List[MapObject]  # Placed objects (trees, buildings, etc.)
    background_color: tuple

@dataclass
class MapObject:
    id: str
    x: float               # World percentage position
    y: float
    object_type: str        # "tree", "mountain", "lake", "city_token", "marker", "info_pin"
    icon: str               # Display character/emoji
    color: tuple
    size: float             # Scale
    label: str
    linked_location_id: str # Links to Location for city tokens
    linked_info: str        # Rich text info
    tags: List[str]

@dataclass
class WorldMap:
    id: str
    name: str
    map_type: str           # "world", "region", "town", "dungeon"
    parent_map_id: str      # For drill-down (world -> town)
    width: int              # Grid width in tiles
    height: int
    tile_size: int          # Pixels per tile (adjustable)
    layers: List[MapLayer]
    active_layer_idx: int
    background_image: str   # Optional background image path
    grid_visible: bool
    grid_color: tuple
    # Camera state (not saved)
    camera_x: float
    camera_y: float
    zoom: float
```

### Terrain Brushes (painting tools)
```python
TERRAIN_BRUSHES = {
    # Land
    "grass": {"color": (86, 140, 60), "icon": "", "category": "land"},
    "forest": {"color": (34, 90, 34), "icon": "T", "category": "land"},
    "dense_forest": {"color": (20, 60, 20), "icon": "TT", "category": "land"},
    "hills": {"color": (140, 120, 70), "icon": "^", "category": "land"},
    "mountain": {"color": (130, 130, 140), "icon": "M", "category": "land"},
    "snow": {"color": (220, 225, 235), "icon": "", "category": "land"},
    "desert": {"color": (210, 190, 130), "icon": "", "category": "land"},
    "swamp": {"color": (70, 90, 50), "icon": "~", "category": "land"},
    "tundra": {"color": (170, 180, 175), "icon": "", "category": "land"},
    "farmland": {"color": (160, 170, 60), "icon": "#", "category": "land"},
    # Water
    "river": {"color": (50, 110, 190), "icon": "~", "category": "water"},
    "lake": {"color": (40, 90, 170), "icon": "~", "category": "water"},
    "ocean": {"color": (25, 60, 130), "icon": "~", "category": "water"},
    "shallow_water": {"color": (70, 140, 210), "icon": "~", "category": "water"},
    "coast": {"color": (180, 170, 120), "icon": "", "category": "water"},
    # Roads
    "road": {"color": (150, 130, 95), "icon": "=", "category": "road"},
    "trail": {"color": (120, 105, 75), "icon": "-", "category": "road"},
    "bridge": {"color": (140, 120, 80), "icon": "=", "category": "road"},
    # Special
    "lava": {"color": (200, 60, 20), "icon": "!", "category": "hazard"},
    "ice": {"color": (180, 210, 240), "icon": "", "category": "land"},
    "cave_entrance": {"color": (60, 50, 45), "icon": "O", "category": "special"},
    "ruins": {"color": (100, 90, 80), "icon": "R", "category": "special"},
    "portal": {"color": (160, 80, 200), "icon": "*", "category": "special"},
}
```

### Map Objects (stamps/tokens placed on map)
```python
MAP_OBJECT_TYPES = {
    # Settlements
    "capital": {"icon": "★", "size": 2.0, "color": (255, 215, 0)},
    "city": {"icon": "●", "size": 1.5, "color": (200, 200, 220)},
    "town": {"icon": "●", "size": 1.0, "color": (160, 160, 180)},
    "village": {"icon": "•", "size": 0.7, "color": (120, 120, 140)},
    "fort": {"icon": "⬟", "size": 1.2, "color": (180, 140, 100)},
    # Nature
    "single_tree": {"icon": "T", "size": 0.5, "color": (40, 120, 40)},
    "mountain_peak": {"icon": "▲", "size": 1.0, "color": (140, 140, 150)},
    "volcano": {"icon": "▲", "size": 1.2, "color": (200, 60, 30)},
    # Markers
    "info_pin": {"icon": "i", "size": 0.6, "color": (80, 160, 255)},
    "quest_marker": {"icon": "!", "size": 0.8, "color": (255, 200, 40)},
    "danger_marker": {"icon": "☠", "size": 0.8, "color": (200, 40, 40)},
    "treasure": {"icon": "$", "size": 0.6, "color": (255, 215, 0)},
    "camp": {"icon": "△", "size": 0.7, "color": (200, 140, 60)},
    # D&D Specific
    "temple": {"icon": "†", "size": 0.9, "color": (255, 240, 180)},
    "tavern": {"icon": "🍺", "size": 0.7, "color": (200, 160, 80)},
    "shop": {"icon": "♦", "size": 0.6, "color": (200, 180, 40)},
    "guild": {"icon": "⚔", "size": 0.8, "color": (160, 160, 200)},
    "dock": {"icon": "⚓", "size": 0.8, "color": (80, 140, 200)},
}
```

### Serialization
- save_world_map() / load_world_map() → JSON
- Maps stored in `saves/maps/` directory
- Each WorldMap saved as separate file, referenced by ID from World

---

## Phase 2: Map Drawing Tools (`states/map_editor.py`)

New state class: `MapEditorState(GameState)` — full-screen map editor.

### Tool System
```
TOOLS:
├── Paint Brush     - Paint terrain tiles (adjustable size 1-10)
├── Eraser          - Remove terrain tiles
├── Fill Bucket     - Flood fill area with terrain
├── Object Stamp    - Place map objects (cities, trees, markers)
├── Select/Move     - Select & drag objects
├── Info Pin        - Place info markers with rich text
├── Route Draw      - Draw routes between locations
├── Measure         - Measure distance (miles/days)
└── Eyedropper      - Pick terrain from map
```

### UI Layout
```
┌─────────────────────────────────────────────────────────────┐
│ [Toolbar: tools] [Brush Size: 1-10] [Layer: ▼] [Grid ☐]   │
│ [Undo] [Redo] [Save] [Back to Campaign]                    │
├──────────┬──────────────────────────────────────────────────┤
│ Brush    │                                                  │
│ Palette  │              MAP CANVAS                          │
│          │         (pan & zoom with mouse)                   │
│ ──────── │                                                  │
│ Objects  │                                                  │
│ Palette  │                                                  │
│          │                                                  │
│ ──────── │                                                  │
│ Layers   │                                                  │
│ Panel    │                                                  │
│ [+layer] │                                                  │
│ [eye]    │                                                  │
│ [delete] │                                                  │
├──────────┴──────────────────────────────────────────────────┤
│ Status: "Painting grass (3x3)" | Pos: 45, 23 | Zoom: 1.5x  │
└─────────────────────────────────────────────────────────────┘
```

### Drawing Implementation
- Canvas renders active layer tiles as colored rectangles
- Other layers rendered with reduced opacity
- Objects rendered on top of tiles
- Grid overlay toggleable
- Pan: middle-mouse or spacebar+drag
- Zoom: mouse wheel (0.2x - 5.0x)
- Undo/redo stack (last 50 actions)

### Brush System
- Square brush: 1x1 to 10x10 tiles
- Click-drag to paint continuously
- Right-click to erase
- Keyboard shortcuts for brush size ([ and ])

---

## Phase 3: Multi-Layer System

### Plane/Layer Types
```python
LAYER_PRESETS = {
    "surface": {"name": "Surface", "depth": 0, "bg": (40, 60, 30)},
    "underground_1": {"name": "Shallow Caves", "depth": -1, "bg": (35, 30, 28)},
    "underground_2": {"name": "Deep Underdark", "depth": -2, "bg": (20, 18, 22)},
    "underwater": {"name": "Underwater", "depth": -1, "bg": (15, 40, 80)},
    "feywild": {"name": "Feywild", "depth": 0, "bg": (60, 80, 50)},
    "shadowfell": {"name": "Shadowfell", "depth": 0, "bg": (25, 22, 30)},
    "ethereal": {"name": "Ethereal Plane", "depth": 0, "bg": (50, 50, 65)},
    "astral": {"name": "Astral Plane", "depth": 0, "bg": (15, 15, 35)},
    "elemental_fire": {"name": "Plane of Fire", "depth": 0, "bg": (80, 25, 10)},
    "elemental_water": {"name": "Plane of Water", "depth": 0, "bg": (10, 30, 70)},
    "elemental_air": {"name": "Plane of Air", "depth": 0, "bg": (60, 70, 85)},
    "elemental_earth": {"name": "Plane of Earth", "depth": 0, "bg": (50, 40, 30)},
    "abyss": {"name": "The Abyss", "depth": 0, "bg": (30, 10, 10)},
    "nine_hells": {"name": "Nine Hells", "depth": 0, "bg": (60, 15, 10)},
    "custom": {"name": "Custom Layer", "depth": 0, "bg": (30, 30, 35)},
}
```

### Layer Panel Features
- Toggle visibility (eye icon)
- Adjust opacity slider
- Reorder layers (drag up/down)
- Rename layers
- Add/delete layers
- Active layer highlighted
- Portal objects link between layers (click to jump)

---

## Phase 4: Town/City Map View

### Drill-Down System
When clicking a city token on the world map:
1. Check if town has a sub-map (WorldMap with parent_map_id)
2. If yes → open that map in editor
3. If no → offer to create one (with optional background image)
4. "Back to World Map" button to return

### Town Map Features
- Larger tile scale (each tile = building/block sized)
- Building placement tools
- Street/road painting
- District zones (market, temple, residential, etc.)
- NPC pins (click to see NPC info)
- Shop pins (click to see shop inventory)
- Quest pins (click to see quest details)
- Background image support (hand-drawn or imported)

### Town-Specific Object Types
```python
TOWN_OBJECTS = {
    "building": {"icon": "■", "color": (140, 120, 100)},
    "market_stall": {"icon": "⬡", "color": (200, 180, 60)},
    "fountain": {"icon": "◉", "color": (80, 140, 220)},
    "statue": {"icon": "♔", "color": (160, 160, 170)},
    "well": {"icon": "○", "color": (100, 130, 180)},
    "gate": {"icon": "⊓", "color": (140, 120, 90)},
    "wall_section": {"icon": "█", "color": (120, 110, 100)},
    "tower": {"icon": "▣", "color": (130, 120, 110)},
    "garden": {"icon": "❋", "color": (60, 140, 50)},
    "graveyard": {"icon": "†", "color": (100, 100, 110)},
    "dock": {"icon": "⊏", "color": (80, 100, 140)},
    "bridge": {"icon": "═", "color": (140, 120, 80)},
    "npc_pin": {"icon": "👤", "color": (80, 160, 255)},  # Links to NPC
    "shop_pin": {"icon": "🛒", "color": (255, 200, 40)},  # Links to shop
    "quest_pin": {"icon": "❗", "color": (255, 100, 40)},   # Links to quest
}
```

---

## Phase 5: Info & Link System

### Info Token System
Each MapObject can have:
- `linked_location_id` → Click opens location detail
- `linked_npc_ids` → Shows NPC list
- `linked_quest_ids` → Shows quest list
- `linked_info` → Rich text popup
- `linked_map_id` → Drill-down to sub-map

### Rich Tooltip/Panel
When hovering/clicking an info token:
```
┌─ Waterdeep ──────────────────┐
│ Type: Metropolis              │
│ Pop: 1,300,000               │
│ Government: Masked Lords     │
│ ──────────────────────────── │
│ NPCs: Durnan, Laeral, Vajra  │
│ Quests: 3 active             │
│ Shops: 5 linked              │
│ ──────────────────────────── │
│ [Open Town Map] [Edit Info]  │
│ [View NPCs] [View Quests]    │
└──────────────────────────────┘
```

### Clipboard/Copy System
- Copy location info as formatted text
- Copy NPC block
- Copy map region (tile selection → paste elsewhere)
- Export map as PNG image (screenshot)

---

## Phase 6: Integration with Campaign Manager

### Navigation Flow
```
Campaign Manager (Tab: World)
├── Locations (tree view)           ← existing
├── All NPCs                       ← existing
├── Shops                          ← existing
├── Map → [Opens MapEditorState]   ← UPGRADED
│   ├── World Map (with layers)
│   │   └── Click city → Town Map
│   │       └── Click building → Location detail / NPC / Shop
│   └── Back to Campaign
├── Quests                         ← just added
├── Templates                      ← existing
├── Services                       ← existing
└── Travel                         ← existing
```

### Save/Load Integration
- WorldMap data saved alongside Campaign
- Quick save: Ctrl+S (auto-saves current map + campaign)
- Maps stored as part of world_data in campaign JSON
- Export individual maps as standalone JSON files

---

## Implementation Order

### Step 1: Data model (`data/map_engine.py`)
- MapLayer, MapObject, WorldMap dataclasses
- Terrain brushes & object type dictionaries
- Serialization/deserialization
- Integration with existing World dataclass

### Step 2: Map editor state (`states/map_editor.py`)
- Basic canvas with pan/zoom
- Tile painting (brush tool)
- Grid rendering
- Toolbar UI
- Save/load

### Step 3: Drawing tools
- Brush size adjustment
- Fill bucket
- Eraser
- Object stamp placement
- Select/move tool
- Undo/redo

### Step 4: Layer system
- Layer panel UI
- Layer switching
- Opacity/visibility toggles
- Plane presets (Underdark, Feywild, etc.)

### Step 5: Object & info system
- City/town tokens with Location links
- Info pins with rich tooltips
- NPC/Quest/Shop pins
- Click-through navigation

### Step 6: Town map drill-down
- Sub-map creation from city tokens
- Town-specific tools and objects
- Navigation between world ↔ town maps
- Background image support

### Step 7: Integration & polish
- Campaign Manager "Map" button → MapEditorState
- Copy/paste/export
- Keyboard shortcuts
- Performance (only render visible tiles)

---

## File Structure (new files)
```
DnDTools/
├── data/
│   └── map_engine.py          # WorldMap, MapLayer, MapObject, brushes, serialization
├── states/
│   └── map_editor.py          # MapEditorState - full map editor
└── (modified files)
    ├── data/world.py          # Add world_maps dict to World
    ├── states/campaign_manager.py  # "Map" button → launch MapEditorState
    └── main.py                # Register MAP_EDITOR state
```
