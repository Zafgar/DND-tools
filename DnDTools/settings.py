# --- CONFIGURATION ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60

# --- COLOR PALETTE (Premium Dark Fantasy UI) ---
COLORS = {
    # Backgrounds
    "bg":              (18, 18, 24),
    "bg_dark":         (12, 12, 18),
    "panel":           (28, 30, 38),
    "panel_dark":      (22, 24, 30),
    "panel_light":     (38, 40, 50),
    "panel_header":    (32, 34, 44),

    # Borders & Lines
    "border":          (55, 58, 72),
    "border_light":    (70, 74, 90),
    "border_glow":     (80, 100, 160),
    "separator":       (40, 42, 52),

    # Text
    "text_main":       (225, 225, 230),
    "text_bright":     (255, 255, 255),
    "text_dim":        (140, 142, 155),
    "text_muted":      (90, 92, 105),

    # Primary Accent (Royal Blue)
    "accent":          (88, 130, 230),
    "accent_hover":    (110, 155, 255),
    "accent_dim":      (55, 80, 140),
    "accent_glow":     (88, 130, 230),

    # Danger / Enemy (Crimson)
    "danger":          (210, 50, 60),
    "danger_hover":    (235, 70, 80),
    "danger_dim":      (130, 30, 40),

    # Success / Heal (Emerald)
    "success":         (35, 160, 65),
    "success_hover":   (50, 185, 80),
    "success_dim":     (20, 100, 40),

    # Warning (Amber)
    "warning":         (240, 180, 20),
    "warning_hover":   (255, 200, 40),
    "warning_dim":     (160, 120, 10),

    # Grid
    "grid":            (28, 30, 38),
    "grid_line":       (38, 40, 50),

    # Combat Tokens
    "player":          (50, 180, 240),
    "player_glow":     (30, 140, 220),
    "enemy":           (235, 70, 70),
    "enemy_glow":      (200, 40, 40),
    "neutral":         (180, 180, 80),

    # Magic & Effects
    "spell":           (170, 90, 245),
    "spell_dim":       (110, 55, 165),
    "legendary":       (255, 200, 30),
    "legendary_dim":   (180, 140, 15),
    "reaction":        (255, 140, 30),
    "concentration":   (80, 230, 180),
    "heal":            (80, 255, 140),
    "radiant":         (255, 240, 180),
    "necrotic":        (120, 50, 130),
    "fire":            (255, 100, 30),
    "cold":            (100, 180, 255),
    "lightning":       (255, 255, 100),
    "poison":          (100, 200, 50),

    # Class Colors
    "barbarian":       (200, 60, 40),
    "fighter":         (160, 130, 70),
    "paladin":         (230, 210, 100),
    "rogue":           (80, 80, 80),
    "ranger":          (70, 140, 60),
    "cleric":          (220, 200, 150),
    "wizard":          (90, 90, 200),
    "warlock":         (130, 50, 160),
    "sorcerer":        (200, 60, 60),
    "bard":            (180, 100, 180),
    "druid":           (100, 170, 80),
    "monk":            (100, 180, 200),

    # UI States
    "selected":        (60, 70, 100),
    "hover":           (45, 50, 65),
    "disabled":        (50, 52, 58),
    "input_bg":        (15, 16, 22),
    "input_border":    (55, 58, 72),
    "input_focus":     (88, 130, 230),

    # Scrollbar
    "scrollbar_bg":    (25, 27, 35),
    "scrollbar_thumb": (60, 64, 80),
    "scrollbar_hover": (80, 85, 105),

    # Token HP Colors
    "hp_full":         (40, 200, 80),
    "hp_mid":          (240, 180, 20),
    "hp_low":          (210, 50, 50),
    "hp_bg":           (20, 22, 28),

    # Team Colors (for Combat Roster multi-team system)
    "team_blue":       (50, 140, 240),
    "team_red":        (235, 65, 65),
    "team_green":      (50, 190, 80),
    "team_gold":       (240, 190, 40),
    "team_blue_dim":   (30, 80, 140),
    "team_red_dim":    (140, 35, 35),
    "team_green_dim":  (30, 110, 45),
    "team_gold_dim":   (140, 110, 20),
}

# Team definitions for Combat Roster
TEAM_COLORS = {
    "Blue":  {"color": (50, 140, 240),  "dim": (30, 80, 140),  "glow": (70, 160, 255)},
    "Red":   {"color": (235, 65, 65),   "dim": (140, 35, 35),  "glow": (255, 90, 90)},
    "Green": {"color": (50, 190, 80),   "dim": (30, 110, 45),  "glow": (70, 220, 100)},
    "Gold":  {"color": (240, 190, 40),  "dim": (140, 110, 20), "glow": (255, 210, 60)},
}
TEAM_NAMES = list(TEAM_COLORS.keys())

# Creature type to display icon mapping (2-char symbols for tokens)
CREATURE_ICONS = {
    "Humanoid":      "Hu",
    "Beast":         "Be",
    "Dragon":        "Dr",
    "Undead":        "Un",
    "Fiend":         "Fi",
    "Celestial":     "Ce",
    "Fey":           "Fy",
    "Aberration":    "Ab",
    "Construct":     "Co",
    "Elemental":     "El",
    "Giant":         "Gi",
    "Monstrosity":   "Mo",
    "Ooze":          "Oz",
    "Plant":         "Pl",
    "Swarm":         "Sw",
}

# Creature type to token color tint
CREATURE_TYPE_COLORS = {
    "Humanoid":      (180, 170, 160),
    "Beast":         (140, 180, 100),
    "Dragon":        (200, 60, 60),
    "Undead":        (120, 160, 120),
    "Fiend":         (180, 50, 50),
    "Celestial":     (240, 230, 180),
    "Fey":           (140, 200, 180),
    "Aberration":    (160, 80, 180),
    "Construct":     (160, 160, 180),
    "Elemental":     (100, 160, 220),
    "Giant":         (180, 140, 100),
    "Monstrosity":   (180, 120, 80),
    "Ooze":          (80, 180, 80),
    "Plant":         (80, 160, 60),
    "Swarm":         (160, 140, 100),
}

# Size to token radius multiplier
SIZE_RADIUS = {
    "Tiny":       0.5,
    "Small":      0.8,
    "Medium":     1.0,
    "Large":      1.4,
    "Huge":       2.0,
    "Gargantuan": 2.8,
}
