"""Terrain objects for the D&D battle grid.

Supports: walls/rocks (impassable), difficult terrain (half move cost),
hazards (fire/acid - damage on entry/start of turn), cover, chasms, bridges.
"""
from dataclasses import dataclass, field


TERRAIN_TYPES = {
    "wall":      {"color": (80, 65, 45),   "passable": False, "label": "Wall",      "icon": "▩"},
    "rock":      {"color": (110, 100, 90),  "passable": False, "label": "Rock",      "icon": "⬡"},
    "tree":      {"color": (30, 95, 40),   "passable": False, "label": "Tree",      "icon": "♣"},
    "house":     {"color": (110, 80, 65),  "passable": False, "label": "House",     "icon": "⌂"},
    "chasm":     {"color": (15, 15, 28),   "passable": False, "label": "Chasm",     "icon": "▼"},
    "table":     {"color": (130, 90, 50),  "passable": True,  "difficult": True,  "label": "Table",     "icon": "═"},
    "difficult": {"color": (65, 55, 35),   "passable": True,  "difficult": True,  "label": "Difficult", "icon": "≈"},
    "water":     {"color": (30, 80, 160),  "passable": True,  "difficult": True,  "label": "Water",     "icon": "~"},
    "bridge":    {"color": (145, 105, 60), "passable": True,  "label": "Bridge",    "icon": "═"},
    "cover":     {"color": (80, 80, 105),  "passable": True,  "cover": True,      "label": "Cover",     "icon": "◘"},
    "fire":      {"color": (220, 80, 20),  "passable": True,
                  "hazard_damage": "1d6",  "damage_type": "fire",  "label": "Fire",   "icon": "♨"},
    "acid":      {"color": (80, 190, 30),  "passable": True,
                  "hazard_damage": "1d6",  "damage_type": "acid",  "label": "Acid",   "icon": "☣"},
    "poison":    {"color": (130, 50, 160), "passable": True,
                  "hazard_damage": "1d4",  "damage_type": "poison","label": "Poison", "icon": "☠"},
}


@dataclass
class TerrainObject:
    terrain_type: str      # key from TERRAIN_TYPES
    grid_x: int
    grid_y: int
    width: int = 1         # grid squares wide
    height: int = 1        # grid squares tall
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = TERRAIN_TYPES.get(self.terrain_type, {}).get("label", self.terrain_type)

    @property
    def props(self) -> dict:
        return TERRAIN_TYPES.get(self.terrain_type, {})

    @property
    def passable(self) -> bool:
        return self.props.get("passable", True)

    @property
    def is_difficult(self) -> bool:
        return self.props.get("difficult", False)

    @property
    def is_hazard(self) -> bool:
        return "hazard_damage" in self.props

    @property
    def hazard_damage(self) -> str:
        return self.props.get("hazard_damage", "")

    @property
    def hazard_damage_type(self) -> str:
        return self.props.get("damage_type", "")

    @property
    def provides_cover(self) -> bool:
        return self.props.get("cover", False)

    @property
    def color(self) -> tuple:
        return self.props.get("color", (80, 80, 80))

    @property
    def icon(self) -> str:
        return self.props.get("icon", "?")

    @property
    def label(self) -> str:
        return self.props.get("label", self.terrain_type)

    def occupies(self, gx: int, gy: int) -> bool:
        return (self.grid_x <= gx < self.grid_x + self.width and
                self.grid_y <= gy < self.grid_y + self.height)

    def to_dict(self) -> dict:
        return {
            "terrain_type": self.terrain_type,
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "width": self.width,
            "height": self.height,
            "name": self.name,
        }

    @staticmethod
    def from_dict(d: dict) -> "TerrainObject":
        return TerrainObject(**d)
