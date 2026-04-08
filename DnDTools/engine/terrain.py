"""Terrain objects for the D&D battle grid.

Supports: walls/rocks (impassable), difficult terrain (half move cost),
hazards (fire/acid - damage on entry/start of turn), cover, chasms, bridges,
elevation (height in feet), doors (open/close toggle), climbable surfaces,
and line-of-sight blocking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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
    "chasm":     {"color": (15, 15, 28),   "passable": False, "label": "Chasm (5ft)",
                  "icon": "▼", "elevation_ft": -100, "is_gap": True, "gap_width_ft": 5,
                  "description": "Bottomless chasm. Jump (5ft) or fly to cross. Fall = death."},
    "chasm_10":  {"color": (12, 12, 25),  "passable": False, "label": "Chasm (10ft)",
                  "icon": "▼▼", "elevation_ft": -100, "is_gap": True, "gap_width_ft": 10,
                  "description": "Wide chasm. Long jump (10ft) or fly to cross."},
    "chasm_15":  {"color": (10, 10, 22),  "passable": False, "label": "Chasm (15ft)",
                  "icon": "▼!", "elevation_ft": -100, "is_gap": True, "gap_width_ft": 15,
                  "description": "Very wide chasm. Long jump (15ft STR) or fly to cross."},
    "chasm_20":  {"color": (8, 8, 20),    "passable": False, "label": "Chasm (20ft)",
                  "icon": "▼!!", "elevation_ft": -100, "is_gap": True, "gap_width_ft": 20,
                  "description": "Massive chasm. Only STR 20+ long jump or fly."},
    "lava_chasm":{"color": (180, 40, 10), "passable": False, "label": "Lava Chasm",
                  "icon": "▼~", "elevation_ft": -100, "is_gap": True, "gap_width_ft": 10,
                  "hazard_damage": "10d10", "damage_type": "fire",
                  "description": "Lava-filled chasm. Jump or fly. Falling = 10d10 fire."},
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
    "spike_growth":{"color": (80, 120, 40), "passable": True, "difficult": True,
                  "hazard_damage": "2d4", "damage_type": "piercing", "label": "Spike Growth", "icon": "SG",
                  "description": "2d4 piercing per 5ft moved through. Difficult terrain."},
    "entangle":  {"color": (50, 110, 30),  "passable": True, "difficult": True,
                  "label": "Entangle", "icon": "EN",
                  "description": "Restrained (STR save). Difficult terrain."},
    "sleet_storm":{"color": (180, 200, 220), "passable": True, "difficult": True,
                  "label": "Sleet Storm", "icon": "SS", "blocks_los": True,
                  "description": "Heavily obscured. Difficult terrain. DEX save or prone."},
    "stinking_cloud":{"color": (140, 160, 50), "passable": True,
                  "label": "Stinking Cloud", "icon": "SC", "blocks_los": True,
                  "description": "Heavily obscured. CON save or Poisoned."},
    "cloudkill": {"color": (80, 140, 30),  "passable": True,
                  "hazard_damage": "5d8", "damage_type": "poison", "label": "Cloudkill", "icon": "CK",
                  "blocks_los": True,
                  "description": "Heavily obscured. 5d8 poison (CON save half)."},
    "moonbeam":  {"color": (200, 220, 255), "passable": True,
                  "hazard_damage": "2d10", "damage_type": "radiant", "label": "Moonbeam", "icon": "MB",
                  "description": "2d10 radiant (CON save half). Shapechanger disadv."},
    "silence":   {"color": (60, 60, 80),   "passable": True, "label": "Silence", "icon": "SI",
                  "description": "No sound. Prevents verbal (V) component spells."},
    # --- Darkness / Light ---
    "darkness":  {"color": (10, 10, 15),   "passable": True, "label": "Darkness",
                  "icon": "dk", "blocks_los": True},
    "fog_cloud": {"color": (190, 190, 200), "passable": True, "label": "Fog Cloud",
                  "icon": "FC", "blocks_los": True,
                  "description": "Heavily obscured area."},
    "dim_light": {"color": (40, 40, 50),   "passable": True, "label": "Dim Light",
                  "icon": "dl", "lightly_obscured": True},
    # --- Magical terrain ---
    "antimagic":  {"color": (60, 60, 80),  "passable": True, "label": "Antimagic Zone",
                  "icon": "AM", "description": "No magic works here."},
    "magic_circle":{"color": (80, 50, 140), "passable": True, "label": "Magic Circle",
                  "icon": "MC", "cover_bonus": 2,
                  "description": "Provides half cover and resistance to magic."},
    "teleport_pad":{"color": (120, 60, 200),"passable": True, "label": "Teleport Pad",
                  "icon": "TP", "description": "Teleports to linked pad."},
    "leyline":    {"color": (100, 60, 180), "passable": True, "label": "Ley Line",
                  "icon": "LL", "description": "+1d4 to spell damage."},
    # --- Structural ---
    "portcullis":  {"color": (120, 120, 130),"passable": False, "label": "Portcullis",
                  "icon": "PC", "blocks_los": False, "cover_bonus": 2, "door": True,
                  "description": "Iron gate. Blocks movement but allows LOS."},
    "altar":      {"color": (150, 130, 100),"passable": False, "label": "Altar",
                  "icon": "AL", "blocks_los": False, "cover_bonus": 2, "elevation_ft": 3,
                  "description": "Stone altar. Provides half cover."},
    "statue":     {"color": (140, 140, 150),"passable": False, "label": "Statue",
                  "icon": "ST", "blocks_los": True, "cover_bonus": 5, "elevation_ft": 10,
                  "description": "Large stone statue."},
    "bookshelf":  {"color": (100, 70, 40),  "passable": False, "label": "Bookshelf",
                  "icon": "BS", "blocks_los": True, "elevation_ft": 8, "climbable": True,
                  "description": "Tall bookshelf. Blocks LOS, climbable."},
    "throne":     {"color": (160, 130, 60), "passable": False, "label": "Throne",
                  "icon": "TH", "blocks_los": False, "cover_bonus": 2, "elevation_ft": 3,
                  "description": "Ornate throne."},
    # --- Natural / cave ---
    "stalactite":  {"color": (90, 85, 80),  "passable": False, "label": "Stalactite Column",
                  "icon": "SC", "blocks_los": True, "cover_bonus": 5, "elevation_ft": 15,
                  "description": "Column from ceiling. Full cover."},
    "mushroom_giant":{"color": (140, 80, 160),"passable": False, "label": "Giant Mushroom",
                  "icon": "GM", "blocks_los": True, "cover_bonus": 5, "elevation_ft": 15,
                  "climbable": True, "description": "Underdark giant mushroom."},
    "mushroom_patch":{"color": (120, 70, 140),"passable": True, "difficult": True,
                  "label": "Mushroom Patch", "icon": "mp",
                  "description": "Bioluminescent mushrooms. Difficult terrain."},
    "web":         {"color": (200, 200, 200),"passable": True, "difficult": True,
                  "label": "Web", "icon": "WB",
                  "description": "Sticky webs. DEX save DC 12 or Restrained. Flammable."},
    "moss":        {"color": (50, 90, 40),  "passable": True, "difficult": True,
                  "label": "Slippery Moss", "icon": "ms",
                  "description": "Slippery moss. Difficult terrain."},
    "crystal":     {"color": (150, 200, 220),"passable": False, "label": "Crystal Formation",
                  "icon": "CR", "blocks_los": False, "cover_bonus": 2, "elevation_ft": 5,
                  "description": "Glowing crystals. Half cover, transparent."},
    # --- Water/ocean ---
    "shipwreck":   {"color": (90, 60, 35),  "passable": True, "difficult": True,
                  "label": "Shipwreck Debris", "icon": "SW", "cover_bonus": 2,
                  "elevation_ft": 3, "climbable": True,
                  "description": "Broken hull. Difficult terrain, half cover."},
    "mast":        {"color": (100, 70, 30), "passable": False, "label": "Ship Mast",
                  "icon": "MA", "blocks_los": True, "cover_bonus": 5, "elevation_ft": 20,
                  "climbable": True, "description": "Tall mast. Climbable to crow's nest."},
    "sand":        {"color": (210, 190, 140),"passable": True, "difficult": True,
                  "label": "Sand", "icon": "sn",
                  "description": "Loose sand. Difficult terrain."},
    "coral":       {"color": (180, 100, 120),"passable": True, "label": "Coral",
                  "icon": "co", "cover_bonus": 2,
                  "hazard_damage": "1d4", "damage_type": "slashing",
                  "description": "Sharp coral. Half cover + 1d4 slashing."},
    # --- Graveyard ---
    "tombstone":   {"color": (120, 120, 130),"passable": False, "label": "Tombstone",
                  "icon": "TS", "blocks_los": False, "cover_bonus": 2, "elevation_ft": 3,
                  "description": "Stone tombstone. Half cover."},
    "sarcophagus": {"color": (100, 95, 90), "passable": False, "label": "Sarcophagus",
                  "icon": "SP", "blocks_los": False, "cover_bonus": 5, "elevation_ft": 4,
                  "description": "Stone coffin. 3/4 cover."},
    "grave_open":  {"color": (40, 30, 25),  "passable": True, "label": "Open Grave",
                  "icon": "OG", "elevation_ft": -5, "difficult": True,
                  "description": "Open grave. Difficult terrain, -5ft elevation."},
    # --- Fog / environmental ---
    "fog":         {"color": (180, 180, 190),"passable": True, "label": "Fog",
                  "icon": "fg", "blocks_los": True,
                  "description": "Heavy fog. Blocks LOS but passable."},
    "fog_light":   {"color": (200, 200, 210),"passable": True, "label": "Light Fog",
                  "icon": "lf",
                  "description": "Thin fog. Ranged attacks have disadvantage."},
    # --- Arena ---
    "pit":         {"color": (25, 20, 15),  "passable": True, "label": "Pit",
                  "icon": "PT", "elevation_ft": -15, "difficult": True,
                  "description": "15ft deep pit. Climb DC 15."},
    "cage":        {"color": (130, 130, 140),"passable": False, "label": "Cage",
                  "icon": "CG", "blocks_los": False,
                  "description": "Iron cage. Blocks movement, allows LOS."},
    "brazier":     {"color": (200, 120, 30),"passable": False, "label": "Brazier",
                  "icon": "BZ", "blocks_los": False, "elevation_ft": 4,
                  "description": "Burning brazier. Dim light 20ft."},
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
    # Spell terrain ownership (for auto-removal on concentration drop)
    spell_owner: str = ""    # caster entity name
    spell_name: str = ""     # spell that created this terrain
    is_spell_terrain: bool = False  # True if created by a spell

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
    def is_gap(self) -> bool:
        """Is this a gap/chasm that can be jumped over or flown across?"""
        return self.props.get("is_gap", False)

    @property
    def gap_width_ft(self) -> int:
        """Width of gap in feet (for jump DC)."""
        return self.props.get("gap_width_ft", 5)

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
        if self.is_spell_terrain:
            d["spell_owner"] = self.spell_owner
            d["spell_name"] = self.spell_name
            d["is_spell_terrain"] = True
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
            spell_owner=d.get("spell_owner", ""),
            spell_name=d.get("spell_name", ""),
            is_spell_terrain=d.get("is_spell_terrain", False),
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
