"""Terrain objects for the D&D battle grid.

Supports: walls/rocks (impassable), difficult terrain (half move cost),
hazards (fire/acid - damage on entry/start of turn), cover, chasms, bridges,
elevation (height in feet), doors (open/close toggle), climbable surfaces,
and line-of-sight blocking.
"""
from dataclasses import dataclass, field


# elevation_ft: default ground elevation for this type (in feet)
# climbable: can creatures climb onto this (uses half speed)
# blocks_los: blocks line of sight for ranged attacks
# door: is a door (can be opened/closed)
# cover_bonus: AC bonus (2 = half, 5 = three-quarters)
TERRAIN_TYPES = {
    # --- Impassable obstacles ---
    "wall":      {"color": (80, 65, 45),   "passable": False, "label": "Wall",
                  "icon": "▩", "blocks_los": True, "elevation_ft": 10, "cover_bonus": 5},
    "rock":      {"color": (110, 100, 90),  "passable": False, "label": "Rock",
                  "icon": "⬡", "blocks_los": True, "elevation_ft": 5, "climbable": True, "cover_bonus": 5},
    "tree":      {"color": (30, 95, 40),   "passable": False, "label": "Tree",
                  "icon": "♣", "blocks_los": True, "elevation_ft": 20, "climbable": True, "cover_bonus": 5},
    "house":     {"color": (110, 80, 65),  "passable": False, "label": "House",
                  "icon": "⌂", "blocks_los": True, "elevation_ft": 15, "cover_bonus": 5},
    "chasm":     {"color": (15, 15, 28),   "passable": False, "label": "Chasm",
                  "icon": "▼", "elevation_ft": -30},
    # --- Doors ---
    "door":      {"color": (140, 100, 50), "passable": False, "label": "Door",
                  "icon": "D", "blocks_los": True, "door": True, "elevation_ft": 0},
    "door_locked":{"color": (140, 60, 30), "passable": False, "label": "Locked Door",
                  "icon": "D!", "blocks_los": True, "door": True, "locked": True, "elevation_ft": 0},
    # --- Elevation / platforms ---
    "platform_5": {"color": (95, 85, 70),  "passable": True, "label": "Platform 5ft",
                   "icon": "^1", "elevation_ft": 5, "climbable": True},
    "platform_10":{"color": (85, 75, 60),  "passable": True, "label": "Platform 10ft",
                   "icon": "^2", "elevation_ft": 10, "climbable": True},
    "platform_15":{"color": (75, 65, 55),  "passable": True, "label": "Platform 15ft",
                   "icon": "^3", "elevation_ft": 15, "climbable": True},
    "platform_20":{"color": (65, 55, 50),  "passable": True, "label": "Platform 20ft",
                   "icon": "^4", "elevation_ft": 20, "climbable": True},
    "stairs_up":  {"color": (100, 90, 75), "passable": True, "label": "Stairs Up",
                   "icon": "/^", "elevation_ft": 5},
    "stairs_down":{"color": (70, 60, 50),  "passable": True, "label": "Stairs Down",
                   "icon": "\\/", "elevation_ft": -5},
    "ladder":     {"color": (130, 100, 60),"passable": True, "label": "Ladder",
                   "icon": "H", "elevation_ft": 10, "climbable": True},
    "roof":       {"color": (120, 85, 60), "passable": True, "label": "Roof",
                   "icon": "^^", "elevation_ft": 15, "climbable": True},
    # --- Difficult terrain ---
    "table":     {"color": (130, 90, 50),  "passable": True,  "difficult": True,
                  "label": "Table", "icon": "=", "cover_bonus": 2},
    "difficult": {"color": (65, 55, 35),   "passable": True,  "difficult": True,
                  "label": "Difficult", "icon": "~"},
    "water":     {"color": (30, 80, 160),  "passable": True,  "difficult": True,
                  "label": "Water", "icon": "~"},
    "deep_water":{"color": (15, 50, 130),  "passable": True,  "difficult": True,
                  "label": "Deep Water", "icon": "~~", "elevation_ft": -10},
    "ice":       {"color": (180, 210, 230),"passable": True,  "difficult": True,
                  "label": "Ice", "icon": "*"},
    "mud":       {"color": (90, 70, 40),   "passable": True,  "difficult": True,
                  "label": "Mud", "icon": "%%"},
    "rubble":    {"color": (100, 90, 80),  "passable": True,  "difficult": True,
                  "label": "Rubble", "icon": ".."},
    # --- Cover ---
    "cover":     {"color": (80, 80, 105),  "passable": True,  "cover_bonus": 2,
                  "label": "Half Cover", "icon": "|"},
    "cover_3q":  {"color": (70, 70, 100),  "passable": True,  "cover_bonus": 5,
                  "label": "3/4 Cover", "icon": "||", "blocks_los": False},
    "pillar":    {"color": (130, 130, 145),"passable": False, "label": "Pillar",
                  "icon": "O", "blocks_los": True, "cover_bonus": 5},
    "barrel":    {"color": (120, 85, 40),  "passable": True,  "cover_bonus": 2,
                  "label": "Barrel", "icon": "()"},
    "crate":     {"color": (140, 110, 60), "passable": True,  "cover_bonus": 2,
                  "label": "Crate", "icon": "[]", "climbable": True, "elevation_ft": 5},
    # --- Bridge ---
    "bridge":    {"color": (145, 105, 60), "passable": True, "label": "Bridge",
                  "icon": "=", "elevation_ft": 0},
    # --- Hazards ---
    "fire":      {"color": (220, 80, 20),  "passable": True,
                  "hazard_damage": "1d6", "damage_type": "fire", "label": "Fire", "icon": "f",
                  "ongoing": True},
    "acid":      {"color": (80, 190, 30),  "passable": True,
                  "hazard_damage": "1d6", "damage_type": "acid", "label": "Acid", "icon": "a"},
    "poison":    {"color": (130, 50, 160), "passable": True,
                  "hazard_damage": "1d4", "damage_type": "poison", "label": "Poison Gas", "icon": "p"},
    "lava":      {"color": (255, 100, 0),  "passable": True,
                  "hazard_damage": "10d10","damage_type": "fire", "label": "Lava", "icon": "!!",
                  "elevation_ft": -5},
    "spikes":    {"color": (100, 100, 110),"passable": True,
                  "hazard_damage": "2d6", "damage_type": "piercing","label": "Spike Pit", "icon": "vv",
                  "elevation_ft": -10},
    "wall_fire": {"color": (255, 60, 0),   "passable": True,
                  "hazard_damage": "5d8", "damage_type": "fire", "label": "Wall of Fire", "icon": "FF",
                  "blocks_los": True},
    "wall_thorns":{"color": (40, 100, 40), "passable": True, "difficult": True,
                  "hazard_damage": "2d4", "damage_type": "piercing","label": "Wall of Thorns", "icon": "TT",
                  "blocks_los": True},
    "spirit_guardians":{"color": (200, 200, 100), "passable": True, "difficult": True,
                  "hazard_damage": "3d8", "damage_type": "radiant", "label": "Spirit Guard.", "icon": "SG"},
    # --- Darkness / Light ---
    "darkness":  {"color": (10, 10, 15),   "passable": True, "label": "Darkness",
                  "icon": "dk", "blocks_los": True},
    "dim_light": {"color": (40, 40, 50),   "passable": True, "label": "Dim Light",
                  "icon": "dl"},
}


@dataclass
class TerrainObject:
    terrain_type: str      # key from TERRAIN_TYPES
    grid_x: int
    grid_y: int
    width: int = 1         # grid squares wide  (x-axis)
    height: int = 1        # grid squares tall  (y-axis)
    name: str = ""
    elevation: int = -1    # elevation in feet (-1 = use type default)
    door_open: bool = False  # for door types: current open/closed state

    def __post_init__(self):
        if not self.name:
            self.name = TERRAIN_TYPES.get(self.terrain_type, {}).get("label", self.terrain_type)
        if self.elevation == -1:
            self.elevation = self.props.get("elevation_ft", 0)

    @property
    def props(self) -> dict:
        return TERRAIN_TYPES.get(self.terrain_type, {})

    @property
    def passable(self) -> bool:
        # Doors are passable when open
        if self.is_door:
            return self.door_open
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
        return self.cover_bonus > 0

    @property
    def cover_bonus(self) -> int:
        """0 = no cover, 2 = half (+2 AC), 5 = three-quarters (+5 AC)."""
        return self.props.get("cover_bonus", 0)

    @property
    def blocks_los(self) -> bool:
        """Does this terrain block line of sight?"""
        if self.is_door and self.door_open:
            return False
        return self.props.get("blocks_los", False)

    @property
    def is_door(self) -> bool:
        return self.props.get("door", False)

    @property
    def is_locked(self) -> bool:
        return self.props.get("locked", False) and not self.door_open

    @property
    def is_climbable(self) -> bool:
        return self.props.get("climbable", False)

    @property
    def color(self) -> tuple:
        if self.is_door and self.door_open:
            return (100, 140, 80)  # greenish when open
        return self.props.get("color", (80, 80, 80))

    @property
    def icon(self) -> str:
        if self.is_door:
            return "DO" if self.door_open else "DC"
        return self.props.get("icon", "?")

    @property
    def label(self) -> str:
        if self.is_door:
            state = "Open" if self.door_open else ("Locked" if self.is_locked else "Closed")
            return f"Door ({state})"
        base = self.props.get("label", self.terrain_type)
        if self.elevation != 0:
            return f"{base} {self.elevation}ft"
        return base

    def toggle_door(self) -> bool:
        """Toggle door open/closed. Returns False if locked."""
        if not self.is_door:
            return False
        if self.is_locked and not self.door_open:
            return False
        self.door_open = not self.door_open
        return True

    def unlock(self):
        """Unlock a locked door (changes type from door_locked to door)."""
        if self.terrain_type == "door_locked":
            self.terrain_type = "door"

    def occupies(self, gx: int, gy: int) -> bool:
        return (self.grid_x <= gx < self.grid_x + self.width and
                self.grid_y <= gy < self.grid_y + self.height)

    def to_dict(self) -> dict:
        d = {
            "terrain_type": self.terrain_type,
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "width": self.width,
            "height": self.height,
            "name": self.name,
            "elevation": self.elevation,
        }
        if self.is_door:
            d["door_open"] = self.door_open
        return d

    @staticmethod
    def from_dict(d: dict) -> "TerrainObject":
        return TerrainObject(
            terrain_type=d["terrain_type"],
            grid_x=d["grid_x"],
            grid_y=d["grid_y"],
            width=d.get("width", 1),
            height=d.get("height", 1),
            name=d.get("name", ""),
            elevation=d.get("elevation", -1),
            door_open=d.get("door_open", False),
        )


def get_elevation_at(terrain_list: list, gx: int, gy: int) -> int:
    """Get the elevation in feet at a grid position. Returns 0 for empty ground."""
    for t in terrain_list:
        if t.occupies(gx, gy):
            return t.elevation
    return 0


def check_los_blocked(terrain_list: list, x1: int, y1: int, x2: int, y2: int) -> bool:
    """Check if line of sight is blocked between two grid positions.
    Uses Bresenham's line algorithm to trace cells between points.
    Returns True if LOS is blocked."""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    cx, cy = x1, y1

    while True:
        if (cx, cy) != (x1, y1) and (cx, cy) != (x2, y2):
            for t in terrain_list:
                if t.occupies(cx, cy) and t.blocks_los:
                    return True
        if cx == x2 and cy == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
    return False


def calculate_fall_damage(height_ft: int) -> int:
    """Calculate fall damage: 1d6 per 10 feet, max 20d6 (200ft)."""
    import random
    if height_ft <= 0:
        return 0
    dice = min(height_ft // 10, 20)
    if dice <= 0:
        return 0
    return sum(random.randint(1, 6) for _ in range(dice))
