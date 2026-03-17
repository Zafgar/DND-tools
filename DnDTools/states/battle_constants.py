"""
Shared constants for battle state modules.
Extracted to avoid circular imports between battle_state, battle_renderer, and battle_events.
"""
from settings import SCREEN_WIDTH

PANEL_W = 520
TOP_BAR_H = 105
GRID_W = SCREEN_WIDTH - PANEL_W

TABS = ["Stats", "Spells", "Log"]

DAMAGE_TYPE_COLORS = {
    "fire": (255, 100, 30), "cold": (100, 180, 255), "lightning": (255, 255, 100),
    "thunder": (160, 140, 255), "acid": (120, 220, 50), "poison": (100, 200, 50),
    "necrotic": (120, 50, 130), "radiant": (255, 240, 180), "psychic": (255, 120, 200),
    "force": (170, 90, 245), "piercing": (180, 180, 180), "slashing": (200, 200, 200),
    "bludgeoning": (160, 160, 160),
}

CONDITION_BADGES = {
    "Poisoned": ("PSN", (100, 200, 50)),
    "Stunned": ("STN", (255, 255, 100)),
    "Blinded": ("BLN", (80, 80, 80)),
    "Deafened": ("DEF", (120, 120, 120)),
    "Frightened": ("FRT", (180, 50, 180)),
    "Paralyzed": ("PAR", (255, 200, 50)),
    "Restrained": ("RST", (180, 120, 60)),
    "Charmed": ("CHM", (255, 120, 200)),
    "Incapacitated": ("INC", (150, 150, 150)),
    "Grappled": ("GRP", (200, 140, 60)),
    "Prone": ("PRN", (140, 100, 60)),
    "Invisible": ("INV", (200, 200, 255)),
    "Petrified": ("PET", (140, 140, 140)),
    "Unconscious": ("UNC", (60, 60, 100)),
    "Exhaustion": ("EXH", (160, 100, 40)),
    "Concentration": ("CON", (80, 230, 180)),
    "Dodge": ("DDG", (100, 200, 255)),
    "Hasted": ("HST", (255, 255, 150)),
    "Slowed": ("SLW", (100, 100, 180)),
    "Hexed": ("HEX", (130, 50, 160)),
    "Blessed": ("BLS", (255, 240, 180)),
    "Silenced": ("SIL", (100, 100, 120)),
}
