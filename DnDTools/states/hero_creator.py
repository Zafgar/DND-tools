"""
Hero Creator State - A comprehensive in-app character builder with a character sheet-like UI.
Allows creating D&D 5e 2014 player characters via point-buy, with full auto-calculations
for HP, AC, spell slots, saving throws, proficiency bonus, and class resources.
"""
import pygame
import json
import os
import copy
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, Panel, fonts, hp_bar, TabBar, Badge, Divider, draw_gradient_rect
from data.models import CreatureStats, AbilityScores, Action, SpellInfo, Feature, RacialTrait
from data.class_features import get_class_features, BARBARIAN_RAGE_COUNT
from data.racial_traits import get_racial_traits, RACE_TRAITS_MAP, get_racial_asi, RACE_ASI
from data.heroes import hero_list
from data.hero_import import export_hero_to_file

try:
    from data.feats import FEATS_LIST
except ImportError:
    FEATS_LIST = []

SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


# ============================================================
# Data Tables
# ============================================================

RACE_LIST = [
    "Human", "Variant Human", "High Elf", "Wood Elf", "Drow",
    "Hill Dwarf", "Mountain Dwarf", "Lightfoot Halfling", "Stout Halfling",
    "Half-Orc", "Half-Elf", "Rock Gnome", "Forest Gnome", "Dragonborn", "Tiefling",
]

CLASS_LIST = [
    "Barbarian", "Fighter", "Paladin", "Rogue", "Ranger",
    "Cleric", "Wizard", "Warlock", "Sorcerer", "Bard", "Druid", "Monk",
]

SUBCLASS_MAP = {
    "Barbarian": ["Totem Warrior", "Berserker"],
    "Fighter": ["Champion", "Battle Master"],
    "Paladin": ["Devotion", "Vengeance"],
    "Rogue": ["Assassin", "Thief"],
    "Ranger": ["Hunter", "Beast Master"],
    "Cleric": ["Life", "War", "Light"],
    "Wizard": ["Evocation", "Abjuration", "Divination"],
    "Warlock": ["Fiend", "Great Old One"],
    "Sorcerer": ["Draconic Bloodline", "Wild Magic"],
    "Bard": ["College of Lore", "College of Valor"],
    "Druid": ["Circle of the Moon", "Circle of the Land"],
    "Monk": ["Way of the Open Hand", "Way of Shadow"],
}

HIT_DICE = {
    "Barbarian": 12, "Fighter": 10, "Paladin": 10, "Ranger": 10,
    "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8, "Warlock": 8,
    "Sorcerer": 6, "Wizard": 6,
}

SAVING_THROW_PROF = {
    "Barbarian": ("strength", "constitution"),
    "Bard": ("dexterity", "charisma"),
    "Cleric": ("wisdom", "charisma"),
    "Druid": ("intelligence", "wisdom"),
    "Fighter": ("strength", "constitution"),
    "Monk": ("strength", "dexterity"),
    "Paladin": ("wisdom", "charisma"),
    "Ranger": ("strength", "dexterity"),
    "Rogue": ("dexterity", "intelligence"),
    "Sorcerer": ("constitution", "charisma"),
    "Warlock": ("wisdom", "charisma"),
    "Wizard": ("intelligence", "wisdom"),
}

SPELLCASTING_ABILITY = {
    "Bard": "Charisma", "Cleric": "Wisdom", "Druid": "Wisdom",
    "Paladin": "Charisma", "Ranger": "Wisdom", "Sorcerer": "Charisma",
    "Warlock": "Charisma", "Wizard": "Intelligence",
}

FULL_CASTERS = {"Wizard", "Cleric", "Druid", "Bard", "Sorcerer"}
HALF_CASTERS = {"Paladin", "Ranger"}
PACT_CASTER = {"Warlock"}

# Full caster spell slot table (index 0 = level 1)
FULL_CASTER_SLOTS = {
    1:  [2],
    2:  [3],
    3:  [4, 2],
    4:  [4, 3],
    5:  [4, 3, 2],
    6:  [4, 3, 3],
    7:  [4, 3, 3, 1],
    8:  [4, 3, 3, 2],
    9:  [4, 3, 3, 3, 1],
    10: [4, 3, 3, 3, 2],
    11: [4, 3, 3, 3, 2, 1],
    12: [4, 3, 3, 3, 2, 1],
    13: [4, 3, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 1, 1, 1],
}

# Warlock pact magic table: (num_slots, slot_level)
WARLOCK_PACT_SLOTS = {
    1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (2, 2),
    5: (2, 3), 6: (2, 3), 7: (2, 4), 8: (2, 4),
    9: (2, 5), 10: (2, 5), 11: (3, 5), 12: (3, 5),
    13: (3, 5), 14: (3, 5), 15: (3, 5), 16: (3, 5),
    17: (4, 5), 18: (4, 5), 19: (4, 5), 20: (4, 5),
}

PROFICIENCY_BY_LEVEL = {
    1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4, 13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

# Default AC by class (simplified: assumes typical starting armor)
DEFAULT_AC_INFO = {
    "Barbarian": ("unarmored_barbarian", 0),   # 10 + DEX + CON
    "Fighter": ("chain_mail", 16),              # Chain mail + shield possibilities
    "Paladin": ("chain_mail_shield", 18),       # Chain mail + shield
    "Rogue": ("leather", 11),                   # Leather + DEX
    "Ranger": ("scale_mail", 14),               # Scale mail + DEX (max 2)
    "Cleric": ("chain_mail_shield", 18),        # Chain mail + shield
    "Wizard": ("none", 10),                     # Robes + DEX (mage armor assumed via spell)
    "Warlock": ("leather", 11),                 # Leather + DEX
    "Sorcerer": ("none", 10),                   # Robes + DEX
    "Bard": ("leather", 11),                    # Leather + DEX
    "Druid": ("leather_shield", 13),            # Leather + shield + DEX
    "Monk": ("unarmored_monk", 0),              # 10 + DEX + WIS
}

RACE_SPEED = {
    "Human": 30, "Variant Human": 30, "High Elf": 30, "Wood Elf": 35, "Drow": 30,
    "Hill Dwarf": 25, "Mountain Dwarf": 25, "Lightfoot Halfling": 25,
    "Stout Halfling": 25, "Half-Orc": 30, "Half-Elf": 30,
    "Rock Gnome": 25, "Forest Gnome": 25, "Dragonborn": 30, "Tiefling": 30,
}

ABILITY_NAMES = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
ABILITY_ABBREVS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

SLOT_LEVEL_NAMES = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"]

# Monk martial arts die progression
MONK_MARTIAL_ARTS = {
    1: "1d4", 2: "1d4", 3: "1d4", 4: "1d4", 5: "1d6", 6: "1d6", 7: "1d6", 8: "1d6",
    9: "1d6", 10: "1d6", 11: "1d8", 12: "1d8", 13: "1d8", 14: "1d8", 15: "1d8",
    16: "1d8", 17: "1d10", 18: "1d10", 19: "1d10", 20: "1d10",
}

# Bard inspiration die progression
BARD_INSPIRATION_DIE = {
    1: "1d6", 2: "1d6", 3: "1d6", 4: "1d6", 5: "1d8", 6: "1d8", 7: "1d8", 8: "1d8",
    9: "1d8", 10: "1d10", 11: "1d10", 12: "1d10", 13: "1d10", 14: "1d10",
    15: "1d12", 16: "1d12", 17: "1d12", 18: "1d12", 19: "1d12", 20: "1d12",
}

# Point buy costs
POINT_BUY_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_TOTAL = 27
POINT_BUY_MIN = 8
POINT_BUY_MAX = 15


# ============================================================
# Dropdown Widget
# ============================================================
class Dropdown:
    """A clickable dropdown that expands to show a scrollable list of options."""

    def __init__(self, x, y, w, h, options, selected=0, label="", on_change=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected = selected
        self.label = label
        self.on_change = on_change
        self.is_open = False
        self.scroll_offset = 0
        self.hover_index = -1
        self.max_visible = 8
        self.item_height = 28
        self._dropdown_rect = None

    @property
    def value(self):
        if 0 <= self.selected < len(self.options):
            return self.options[self.selected]
        return ""

    def set_options(self, options, keep_selection=False):
        old_val = self.value
        self.options = options
        if keep_selection and old_val in options:
            self.selected = options.index(old_val)
        else:
            self.selected = 0
        self.scroll_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.is_open and self._dropdown_rect and self._dropdown_rect.collidepoint(mx, my):
                rel_y = my - self._dropdown_rect.y
                idx = (rel_y // self.item_height) + self.scroll_offset
                if 0 <= idx < len(self.options):
                    self.selected = idx
                    self.is_open = False
                    if self.on_change:
                        self.on_change(self.options[idx])
                return True
            elif self.rect.collidepoint(mx, my):
                self.is_open = not self.is_open
                return True
            else:
                self.is_open = False
                return False

        if event.type == pygame.MOUSEWHEEL and self.is_open:
            mx, my = pygame.mouse.get_pos()
            if self._dropdown_rect and self._dropdown_rect.collidepoint(mx, my):
                self.scroll_offset = max(0, min(
                    len(self.options) - self.max_visible,
                    self.scroll_offset - event.y
                ))
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and self.is_open:
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            elif event.button == 5:
                self.scroll_offset = min(
                    max(0, len(self.options) - self.max_visible),
                    self.scroll_offset + 1
                )
                return True

        return False

    def draw(self, screen, mouse_pos):
        # Label
        if self.label:
            lbl = fonts.small_bold.render(self.label, True, COLORS["text_dim"])
            screen.blit(lbl, (self.rect.x, self.rect.y - 18))

        # Main box
        is_hover = self.rect.collidepoint(mouse_pos)
        border_col = COLORS["input_focus"] if (self.is_open or is_hover) else COLORS["input_border"]
        pygame.draw.rect(screen, COLORS["input_bg"], self.rect, border_radius=5)
        pygame.draw.rect(screen, border_col, self.rect, 1, border_radius=5)

        # Selected text
        txt = self.value if self.value else "-- Select --"
        ts = fonts.body_font.render(txt, True, COLORS["text_main"] if self.value else COLORS["text_muted"])
        clip = self.rect.inflate(-30, 0)
        screen.set_clip(clip)
        screen.blit(ts, (self.rect.x + 8, self.rect.y + (self.rect.height - ts.get_height()) // 2))
        screen.set_clip(None)

        # Arrow
        arrow_x = self.rect.right - 20
        arrow_y = self.rect.centery
        if self.is_open:
            pts = [(arrow_x - 5, arrow_y + 2), (arrow_x + 5, arrow_y + 2), (arrow_x, arrow_y - 4)]
        else:
            pts = [(arrow_x - 5, arrow_y - 2), (arrow_x + 5, arrow_y - 2), (arrow_x, arrow_y + 4)]
        pygame.draw.polygon(screen, COLORS["text_dim"], pts)

    def draw_dropdown_list(self, screen, mouse_pos):
        """Draw the expanded dropdown list. Called after all other UI so it renders on top."""
        if not self.is_open or not self.options:
            return

        visible = min(len(self.options), self.max_visible)
        dh = visible * self.item_height
        dx = self.rect.x
        dy = self.rect.bottom + 2

        # Clamp to screen
        if dy + dh > SCREEN_HEIGHT - 10:
            dy = self.rect.y - dh - 2

        self._dropdown_rect = pygame.Rect(dx, dy, self.rect.width, dh)

        # Shadow
        shadow = pygame.Surface((self.rect.width + 6, dh + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), (0, 0, self.rect.width + 6, dh + 6), border_radius=6)
        screen.blit(shadow, (dx - 3, dy - 3))

        # Background
        pygame.draw.rect(screen, COLORS["panel_dark"], self._dropdown_rect, border_radius=5)
        pygame.draw.rect(screen, COLORS["border_light"], self._dropdown_rect, 1, border_radius=5)

        # Items
        clip_rect = self._dropdown_rect.inflate(-2, -2)
        screen.set_clip(clip_rect)
        for i in range(visible):
            idx = i + self.scroll_offset
            if idx >= len(self.options):
                break
            item_rect = pygame.Rect(dx + 1, dy + i * self.item_height, self.rect.width - 2, self.item_height)
            is_sel = idx == self.selected
            is_hov = item_rect.collidepoint(mouse_pos)

            if is_sel:
                pygame.draw.rect(screen, COLORS["accent_dim"], item_rect)
            elif is_hov:
                pygame.draw.rect(screen, COLORS["hover"], item_rect)

            text_col = COLORS["text_bright"] if is_sel else COLORS["text_main"]
            ts = fonts.body_font.render(self.options[idx], True, text_col)
            screen.blit(ts, (item_rect.x + 8, item_rect.y + (self.item_height - ts.get_height()) // 2))

        screen.set_clip(None)

        # Scrollbar
        if len(self.options) > self.max_visible:
            sb_h = max(15, int(dh * visible / len(self.options)))
            sb_y = dy + int((dh - sb_h) * self.scroll_offset / max(1, len(self.options) - self.max_visible))
            sb_rect = pygame.Rect(dx + self.rect.width - 8, sb_y, 6, sb_h)
            pygame.draw.rect(screen, COLORS["scrollbar_thumb"], sb_rect, border_radius=3)


# ============================================================
# Text Input Widget
# ============================================================
class TextInput:
    """Simple single-line text input field."""

    def __init__(self, x, y, w, h, label="", default="", max_length=30):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = default
        self.max_length = max_length
        self.focused = False
        self.cursor_blink = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return self.focused
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB or event.key == pygame.K_RETURN:
                self.focused = False
            elif event.unicode.isprintable() and len(self.text) < self.max_length:
                self.text += event.unicode
            return True
        return False

    def draw(self, screen, mouse_pos):
        if self.label:
            lbl = fonts.small_bold.render(self.label, True, COLORS["text_dim"])
            screen.blit(lbl, (self.rect.x, self.rect.y - 18))

        is_hover = self.rect.collidepoint(mouse_pos)
        border_col = COLORS["input_focus"] if self.focused else (
            COLORS["border_light"] if is_hover else COLORS["input_border"]
        )
        pygame.draw.rect(screen, COLORS["input_bg"], self.rect, border_radius=5)
        pygame.draw.rect(screen, border_col, self.rect, 1 if not self.focused else 2, border_radius=5)

        ts = fonts.body_font.render(self.text, True, COLORS["text_main"])
        clip = self.rect.inflate(-10, 0)
        screen.set_clip(clip)
        screen.blit(ts, (self.rect.x + 8, self.rect.y + (self.rect.height - ts.get_height()) // 2))
        screen.set_clip(None)

        # Cursor
        if self.focused:
            self.cursor_blink = (self.cursor_blink + 1) % 60
            if self.cursor_blink < 35:
                cx = self.rect.x + 8 + ts.get_width() + 1
                cy = self.rect.y + 5
                pygame.draw.line(screen, COLORS["text_bright"], (cx, cy), (cx, cy + self.rect.height - 10))


# ============================================================
# Calculation helpers
# ============================================================

def calc_modifier(score):
    return (score - 10) // 2


def calc_proficiency(level):
    return PROFICIENCY_BY_LEVEL.get(level, 2)


def calc_hp(char_class, level, con_mod):
    hd = HIT_DICE.get(char_class, 8)
    hp = hd + con_mod  # Level 1: max hit die + CON
    if level > 1:
        avg_roll = hd // 2 + 1  # Average for subsequent levels
        hp += (avg_roll + con_mod) * (level - 1)
    return max(1, hp)


def calc_ac(char_class, abilities, subclass=""):
    armor_type, base_ac = DEFAULT_AC_INFO.get(char_class, ("none", 10))
    dex_mod = calc_modifier(abilities.dexterity)
    con_mod = calc_modifier(abilities.constitution)
    wis_mod = calc_modifier(abilities.wisdom)

    if armor_type == "unarmored_barbarian":
        return 10 + dex_mod + con_mod
    elif armor_type == "unarmored_monk":
        return 10 + dex_mod + wis_mod
    elif armor_type == "none":
        # Draconic Resilience for Draconic Bloodline sorcerer
        if char_class == "Sorcerer" and subclass == "Draconic Bloodline":
            return 13 + dex_mod
        return 10 + dex_mod
    elif armor_type == "leather":
        return 11 + dex_mod
    elif armor_type == "leather_shield":
        return 11 + dex_mod + 2  # leather + shield
    elif armor_type == "scale_mail":
        return 14 + min(dex_mod, 2)
    elif armor_type == "chain_mail":
        return 16
    elif armor_type == "chain_mail_shield":
        return 18
    return base_ac


def calc_spell_slots(char_class, level, subclass=""):
    """Return a dict of spell slot level name -> count."""
    slots = {}
    if char_class in FULL_CASTERS:
        slot_list = FULL_CASTER_SLOTS.get(level, [])
        for i, count in enumerate(slot_list):
            slots[SLOT_LEVEL_NAMES[i]] = count
    elif char_class in HALF_CASTERS:
        # Half casters use full caster table at half level (rounded up), starting at level 2
        if level >= 2:
            effective = max(1, (level + 1) // 2)
            slot_list = FULL_CASTER_SLOTS.get(effective, [])
            for i, count in enumerate(slot_list):
                slots[SLOT_LEVEL_NAMES[i]] = count
    elif char_class in PACT_CASTER:
        num, lvl = WARLOCK_PACT_SLOTS.get(level, (1, 1))
        slot_name = SLOT_LEVEL_NAMES[lvl - 1]
        slots[slot_name] = num
    else:
        # Third casters: Eldritch Knight (Fighter), Arcane Trickster (Rogue)
        if (char_class == "Fighter" and subclass == "Eldritch Knight") or \
           (char_class == "Rogue" and subclass == "Arcane Trickster"):
            if level >= 3:
                effective = max(1, (level + 2) // 3)
                slot_list = FULL_CASTER_SLOTS.get(effective, [])
                for i, count in enumerate(slot_list):
                    slots[SLOT_LEVEL_NAMES[i]] = count
    return slots


def build_default_actions(char_class, abilities, prof_bonus, level):
    """Build default weapon/attack actions for a class."""
    str_mod = calc_modifier(abilities.strength)
    dex_mod = calc_modifier(abilities.dexterity)

    actions = []

    if char_class == "Barbarian":
        atk = str_mod + prof_bonus
        actions.append(Action("Greataxe", "Melee weapon attack", atk, "1d12", str_mod, "slashing", range=5))
    elif char_class == "Fighter":
        atk = str_mod + prof_bonus
        actions.append(Action("Longsword", "Melee weapon attack", atk, "1d8", str_mod, "slashing", range=5))
    elif char_class == "Paladin":
        atk = str_mod + prof_bonus
        actions.append(Action("Longsword", "Melee weapon attack", atk, "1d8", str_mod, "slashing", range=5))
    elif char_class == "Rogue":
        atk = dex_mod + prof_bonus
        actions.append(Action("Shortsword", "Melee finesse weapon", atk, "1d6", dex_mod, "piercing", range=5))
        actions.append(Action("Shortbow", "Ranged weapon attack", atk, "1d6", dex_mod, "piercing", range=80))
    elif char_class == "Ranger":
        atk = dex_mod + prof_bonus
        actions.append(Action("Longbow", "Ranged weapon attack", atk, "1d8", dex_mod, "piercing", range=150))
        actions.append(Action("Shortsword", "Melee finesse weapon", atk, "1d6", dex_mod, "piercing", range=5))
    elif char_class == "Cleric":
        atk = str_mod + prof_bonus
        actions.append(Action("Mace", "Melee weapon attack", atk, "1d6", str_mod, "bludgeoning", range=5))
    elif char_class == "Wizard":
        atk = str_mod + prof_bonus
        actions.append(Action("Quarterstaff", "Melee weapon attack", atk, "1d6", str_mod, "bludgeoning", range=5))
    elif char_class == "Warlock":
        atk = str_mod + prof_bonus
        actions.append(Action("Quarterstaff", "Melee weapon attack", atk, "1d6", str_mod, "bludgeoning", range=5))
    elif char_class == "Sorcerer":
        atk = dex_mod + prof_bonus
        actions.append(Action("Dagger", "Melee/ranged weapon", atk, "1d4", dex_mod, "piercing", range=5))
    elif char_class == "Bard":
        atk = dex_mod + prof_bonus
        actions.append(Action("Rapier", "Melee finesse weapon", atk, "1d8", dex_mod, "piercing", range=5))
    elif char_class == "Druid":
        atk = str_mod + prof_bonus
        actions.append(Action("Quarterstaff", "Melee weapon attack", atk, "1d6", str_mod, "bludgeoning", range=5))
    elif char_class == "Monk":
        atk = dex_mod + prof_bonus
        ma_die = MONK_MARTIAL_ARTS.get(level, "1d4")
        actions.append(Action("Unarmed Strike", "Melee martial arts", atk, ma_die, dex_mod, "bludgeoning", range=5))

    # Add multiattack if Extra Attack is available
    has_extra = False
    attack_count = 1
    if char_class in ("Barbarian", "Fighter", "Paladin", "Ranger", "Monk") and level >= 5:
        has_extra = True
        attack_count = 2
    if char_class == "Fighter" and level >= 11:
        attack_count = 3
    if char_class == "Fighter" and level >= 20:
        attack_count = 4

    if has_extra and actions:
        primary = actions[0].name
        ma_targets = [primary] * attack_count
        multiattack = Action("Multiattack", f"{attack_count} attacks",
                             0, "", 0, "", range=5, is_multiattack=True,
                             multiattack_count=attack_count, multiattack_targets=ma_targets)
        actions.insert(0, multiattack)

    return actions


# ============================================================
# Base GameState
# ============================================================
class GameState:
    def __init__(self, manager):
        self.manager = manager

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass


# ============================================================
# HeroCreatorState
# ============================================================
class HeroCreatorState(GameState):
    """Comprehensive Hero Creator with character sheet-like UI for D&D 5e 2014 characters."""

    def __init__(self, manager):
        super().__init__(manager)
        self.scroll_y = 0

        # Character data defaults
        self._init_character_data()

        # Build UI
        self._init_ui()

        # Track which dropdown is open (to layer draw order)
        self.active_dropdown = None
        self.status_message = ""
        self.status_timer = 0
        self.status_color = COLORS["success"]

        # Feature/trait scroll state for right column
        self.feature_scroll = 0
        self.trait_scroll = 0

    def _init_character_data(self):
        self.ability_scores = {
            "strength": 10, "dexterity": 10, "constitution": 10,
            "intelligence": 10, "wisdom": 10, "charisma": 10,
        }
        self.char_name = ""
        self.char_race = "Human"
        self.char_class = "Fighter"
        self.char_subclass = ""
        self.char_level = 1
        # Variant Human: 2 chosen ASI abilities; Half-Elf: 2 chosen +1 abilities
        self.variant_asi_choices = []  # list of ability names
        self.halfelf_asi_choices = []  # list of ability names (not charisma)

    def _init_ui(self):
        # --- Left Column Widgets (x=30, w=370) ---
        col_left_x = 30
        col_left_w = 370

        self.name_input = TextInput(col_left_x, 100, col_left_w, 36, label="Character Name", default="New Hero")

        self.race_dropdown = Dropdown(
            col_left_x, 178, col_left_w, 34, RACE_LIST,
            selected=0, label="Race",
            on_change=lambda v: self._on_race_change(v)
        )

        self.class_dropdown = Dropdown(
            col_left_x, 256, col_left_w, 34, CLASS_LIST,
            selected=1, label="Class",
            on_change=lambda v: self._on_class_change(v)
        )

        subclass_opts = SUBCLASS_MAP.get(self.char_class, [])
        self.subclass_dropdown = Dropdown(
            col_left_x, 334, col_left_w, 34,
            ["(None)"] + subclass_opts,
            selected=0, label="Subclass",
            on_change=lambda v: self._on_subclass_change(v)
        )

        self.level_buttons = []
        # Level selector
        self.level_down_btn = Button(
            col_left_x, 425, 40, 34, "-",
            lambda: self._change_level(-1),
            color=COLORS["danger"], style="outline", font=fonts.body_bold
        )
        self.level_up_btn = Button(
            col_left_x + col_left_w - 40, 425, 40, 34, "+",
            lambda: self._change_level(1),
            color=COLORS["success"], style="outline", font=fonts.body_bold
        )

        # Dropdowns list for iteration
        self.dropdowns = [self.race_dropdown, self.class_dropdown, self.subclass_dropdown]

        # --- Bottom bar buttons ---
        self.btn_save = Button(
            SCREEN_WIDTH - 330, SCREEN_HEIGHT - 68, 145, 46, "SAVE",
            self._on_save, color=COLORS["success"], font=fonts.header_font
        )
        self.btn_export = Button(
            SCREEN_WIDTH - 170, SCREEN_HEIGHT - 68, 145, 46, "EXPORT JSON",
            self._on_export, color=COLORS["accent"], font=fonts.body_bold
        )
        self.btn_back = Button(
            20, SCREEN_HEIGHT - 68, 180, 46, "BACK TO MENU",
            self._on_back, color=COLORS["danger"], font=fonts.body_bold
        )

        # Apply initial selections
        self.char_race = self.race_dropdown.value
        self.char_class = self.class_dropdown.value
        self._refresh_subclass_options()

    # ---- Event Handlers ----

    def _get_racial_bonuses(self):
        """Get the racial ability score bonuses for the current race, including choices."""
        bonuses = get_racial_asi(self.char_race)
        if self.char_race == "Variant Human":
            for ab in self.variant_asi_choices[:2]:
                bonuses[ab] = bonuses.get(ab, 0) + 1
        elif self.char_race == "Half-Elf":
            for ab in self.halfelf_asi_choices[:2]:
                if ab != "charisma":
                    bonuses[ab] = bonuses.get(ab, 0) + 1
        return bonuses

    def _get_effective_score(self, ability):
        """Get ability score after racial bonuses (base + racial ASI)."""
        base = self.ability_scores[ability]
        bonuses = self._get_racial_bonuses()
        return base + bonuses.get(ability, 0)

    def _on_race_change(self, value):
        self.char_race = value
        self.variant_asi_choices = []
        self.halfelf_asi_choices = []

    def _on_class_change(self, value):
        self.char_class = value
        self._refresh_subclass_options()

    def _on_subclass_change(self, value):
        self.char_subclass = value if value != "(None)" else ""

    def _refresh_subclass_options(self):
        opts = SUBCLASS_MAP.get(self.char_class, [])
        self.subclass_dropdown.set_options(["(None)"] + opts)
        self.char_subclass = ""

    def _change_level(self, delta):
        self.char_level = max(1, min(20, self.char_level + delta))

    def _change_ability(self, ability, delta):
        current = self.ability_scores[ability]
        new_val = current + delta
        if new_val < POINT_BUY_MIN or new_val > POINT_BUY_MAX:
            return
        # Check points remaining
        points_used = self._calc_points_used()
        if delta > 0:
            cost_old = POINT_BUY_COST.get(current, 0)
            cost_new = POINT_BUY_COST.get(new_val, 0)
            if points_used + (cost_new - cost_old) > POINT_BUY_TOTAL:
                return
        self.ability_scores[ability] = new_val

    def _calc_points_used(self):
        total = 0
        for ab in ABILITY_NAMES:
            total += POINT_BUY_COST.get(self.ability_scores[ab], 0)
        return total

    def _on_save(self):
        hero = self._build_creature_stats()
        hero_list.append(hero)
        self.status_message = f"'{hero.name}' added to hero roster!"
        self.status_timer = 180
        self.status_color = COLORS["success"]

    def _on_export(self):
        hero = self._build_creature_stats()
        os.makedirs(SAVES_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in hero.name).strip()
        if not safe_name:
            safe_name = "hero"
        filepath = os.path.join(SAVES_DIR, f"{safe_name}.json")
        try:
            export_hero_to_file(hero, filepath)
            self.status_message = f"Exported to {os.path.basename(filepath)}"
            self.status_timer = 180
            self.status_color = COLORS["accent"]
        except Exception as e:
            self.status_message = f"Export failed: {e}"
            self.status_timer = 240
            self.status_color = COLORS["danger"]

    def _on_back(self):
        if hasattr(self.manager, 'set_state'):
            self.manager.set_state("menu")
        elif hasattr(self.manager, 'change_state'):
            self.manager.change_state("menu")

    # ---- Build the CreatureStats ----

    def _build_creature_stats(self):
        name = self.name_input.text.strip() or "Unnamed Hero"
        race = self.char_race
        char_class = self.char_class
        subclass = self.char_subclass
        level = self.char_level

        # Apply racial ASI to base scores
        abilities = AbilityScores(
            strength=self._get_effective_score("strength"),
            dexterity=self._get_effective_score("dexterity"),
            constitution=self._get_effective_score("constitution"),
            intelligence=self._get_effective_score("intelligence"),
            wisdom=self._get_effective_score("wisdom"),
            charisma=self._get_effective_score("charisma"),
        )

        prof = calc_proficiency(level)
        con_mod = calc_modifier(abilities.constitution)
        hp = calc_hp(char_class, level, con_mod)

        # Hill Dwarf bonus HP
        if race == "Hill Dwarf":
            hp += level

        # Draconic Resilience bonus HP
        if char_class == "Sorcerer" and subclass == "Draconic Bloodline":
            hp += level

        ac = calc_ac(char_class, abilities, subclass)
        speed = RACE_SPEED.get(race, 30)

        # Monk speed bonus
        if char_class == "Monk" and level >= 2:
            bonus_speed = 10 + (5 * ((level - 2) // 4)) if level >= 2 else 0
            # Monk speed: +10 at 2, +15 at 6, +20 at 10, +25 at 14, +30 at 18
            monk_speed_table = {2: 10, 6: 15, 10: 20, 14: 25, 18: 30}
            for threshold in sorted(monk_speed_table.keys(), reverse=True):
                if level >= threshold:
                    speed += monk_speed_table[threshold]
                    break

        # Barbarian fast movement
        if char_class == "Barbarian" and level >= 5:
            speed += 10

        hd_size = HIT_DICE.get(char_class, 8)
        hit_dice_str = f"{level}d{hd_size}+{con_mod * level}"

        # Saving throws (use effective scores with racial ASI applied)
        saving_throws = {}
        prof_saves = SAVING_THROW_PROF.get(char_class, ())
        for ab in ABILITY_NAMES:
            eff_score = self._get_effective_score(ab)
            mod = calc_modifier(eff_score)
            if ab in prof_saves:
                mod += prof
            display_name = ab.capitalize()
            if mod != 0 or ab in prof_saves:
                saving_throws[display_name] = mod

        # Spellcasting
        spell_ability = SPELLCASTING_ABILITY.get(char_class, "")
        spell_save_dc = 0
        spell_atk = 0
        if spell_ability:
            ability_key = spell_ability.lower()
            casting_mod = calc_modifier(self._get_effective_score(ability_key))
            spell_save_dc = 8 + prof + casting_mod
            spell_atk = prof + casting_mod

        spell_slots = calc_spell_slots(char_class, level, subclass)

        # Class features
        features = get_class_features(char_class, level, subclass)

        # Racial traits
        racial_traits = get_racial_traits(race)

        # Actions
        actions = build_default_actions(char_class, abilities, prof, level)

        # Resource pools
        ki_points = level if char_class == "Monk" and level >= 2 else 0
        sorcery_points = level if char_class == "Sorcerer" and level >= 2 else 0
        lay_on_hands_pool = 5 * level if char_class == "Paladin" else 0
        rage_count = BARBARIAN_RAGE_COUNT.get(level, 0) if char_class == "Barbarian" else 0

        bardic_dice = ""
        bardic_count = 0
        if char_class == "Bard":
            bardic_dice = BARD_INSPIRATION_DIE.get(level, "1d6")
            cha_mod = calc_modifier(abilities.charisma)
            bardic_count = max(1, cha_mod)

        # Determine CR approximation from level
        cr = max(0.5, level / 2.0)

        # Build unarmored flag
        is_unarmored = char_class in ("Barbarian", "Monk")

        hero = CreatureStats(
            name=name,
            size="Medium",
            creature_type="Humanoid",
            alignment="Neutral",
            armor_class=ac,
            armor_type="",
            hit_points=hp,
            hit_dice=hit_dice_str,
            speed=speed,
            abilities=abilities,
            saving_throws=saving_throws,
            proficiency_bonus=prof,
            challenge_rating=cr,
            character_class=char_class,
            character_level=level,
            race=race,
            subclass=subclass,
            actions=actions,
            features=features,
            racial_traits=racial_traits,
            spellcasting_ability=spell_ability,
            spell_save_dc=spell_save_dc,
            spell_attack_bonus=spell_atk,
            spell_slots=spell_slots,
            ki_points=ki_points,
            sorcery_points=sorcery_points,
            lay_on_hands_pool=lay_on_hands_pool,
            rage_count=rage_count,
            bardic_inspiration_dice=bardic_dice,
            bardic_inspiration_count=bardic_count,
            base_ac_unarmored=is_unarmored,
        )
        return hero

    # ---- GameState Interface ----

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                return

            # Dropdowns get priority when open - check in reverse order for layering
            dropdown_consumed = False
            for dd in reversed(self.dropdowns):
                if dd.is_open:
                    if dd.handle_event(event):
                        dropdown_consumed = True
                        break

            if not dropdown_consumed:
                for dd in self.dropdowns:
                    if dd.handle_event(event):
                        dropdown_consumed = True
                        break

            if dropdown_consumed:
                continue

            # Text input
            if self.name_input.handle_event(event):
                continue

            # Level buttons
            self.level_down_btn.handle_event(event)
            self.level_up_btn.handle_event(event)

            # Ability score +/- buttons
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_ability_clicks(mouse_pos)

            # Bottom buttons
            self.btn_save.handle_event(event)
            self.btn_export.handle_event(event)
            self.btn_back.handle_event(event)

            # Scroll for features panel
            if event.type == pygame.MOUSEWHEEL:
                # Check if mouse is in right column feature area
                if mouse_pos[0] > 1050 and mouse_pos[1] < 550:
                    self.feature_scroll = max(0, self.feature_scroll - event.y * 20)
                elif mouse_pos[0] > 1050 and mouse_pos[1] >= 550:
                    self.trait_scroll = max(0, self.trait_scroll - event.y * 20)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if mouse_pos[0] > 1050 and mouse_pos[1] < 550:
                        self.feature_scroll = max(0, self.feature_scroll - 20)
                    elif mouse_pos[0] > 1050 and mouse_pos[1] >= 550:
                        self.trait_scroll = max(0, self.trait_scroll - 20)
                elif event.button == 5:
                    if mouse_pos[0] > 1050 and mouse_pos[1] < 550:
                        self.feature_scroll += 20
                    elif mouse_pos[0] > 1050 and mouse_pos[1] >= 550:
                        self.trait_scroll += 20

    def _handle_ability_clicks(self, mouse_pos):
        """Check if an ability +/- button or ASI choice was clicked."""
        center_x = 440
        start_y = 150
        row_h = 62
        for i, ab in enumerate(ABILITY_NAMES):
            y = start_y + i * row_h
            minus_rect = pygame.Rect(center_x + 188, y + 2, 28, 28)
            plus_rect = pygame.Rect(center_x + 245, y + 2, 28, 28)
            if minus_rect.collidepoint(mouse_pos):
                self._change_ability(ab, -1)
            elif plus_rect.collidepoint(mouse_pos):
                self._change_ability(ab, 1)

        # ASI choice clicks for Variant Human / Half-Elf
        if self.char_race in ("Variant Human", "Half-Elf"):
            choice_y = start_y + 6 * row_h + 15
            for i, ab in enumerate(ABILITY_NAMES):
                # Skip charisma for Half-Elf (already gets +2)
                if self.char_race == "Half-Elf" and ab == "charisma":
                    continue
                btn_x = center_x + 15 + (i % 3) * 180
                btn_y = choice_y + 22 + (i // 3) * 30
                btn_rect = pygame.Rect(btn_x, btn_y, 170, 26)
                if btn_rect.collidepoint(mouse_pos):
                    self._toggle_asi_choice(ab)

    def update(self):
        if self.status_timer > 0:
            self.status_timer -= 1

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()

        # Background
        screen.fill(COLORS["bg"])

        # Title bar
        draw_gradient_rect(screen, (0, 0, SCREEN_WIDTH, 60),
                           COLORS["panel_header"], COLORS["panel_dark"])
        title_surf = fonts.title_font.render("HERO CREATOR", True, COLORS["text_bright"])
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 8))

        # Draw columns
        self._draw_left_column(screen, mouse_pos)
        self._draw_center_column(screen, mouse_pos)
        self._draw_right_column(screen, mouse_pos)
        self._draw_bottom_bar(screen, mouse_pos)

        # Draw computed stats summary in the center-bottom area
        self._draw_computed_stats(screen, mouse_pos)

        # Draw dropdown overlays last (so they are on top)
        for dd in self.dropdowns:
            dd.draw_dropdown_list(screen, mouse_pos)

        # Status message
        if self.status_timer > 0:
            alpha = min(255, self.status_timer * 4)
            msg_surf = fonts.header_font.render(self.status_message, True, self.status_color)
            # Background bar
            bar_rect = pygame.Rect(0, SCREEN_HEIGHT // 2 - 25, SCREEN_WIDTH, 50)
            overlay = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
            overlay.fill((*COLORS["panel_dark"], min(220, alpha)))
            screen.blit(overlay, (0, SCREEN_HEIGHT // 2 - 25))
            # Border
            pygame.draw.line(screen, self.status_color,
                             (0, SCREEN_HEIGHT // 2 - 25), (SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 25), 2)
            pygame.draw.line(screen, self.status_color,
                             (0, SCREEN_HEIGHT // 2 + 25), (SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 25), 2)
            screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - msg_surf.get_height() // 2))

    # ---- Drawing Sub-sections ----

    def _draw_left_column(self, screen, mouse_pos):
        """Draw left column: name, race, class, subclass, level."""
        col_x = 20
        col_w = 390
        panel = Panel(col_x, 70, col_w, 410, title="CHARACTER INFO")
        panel.draw(screen)

        # Name input
        self.name_input.draw(screen, mouse_pos)

        # Race dropdown
        self.race_dropdown.draw(screen, mouse_pos)

        # Class dropdown
        self.class_dropdown.draw(screen, mouse_pos)

        # Subclass dropdown
        self.subclass_dropdown.draw(screen, mouse_pos)

        # Level selector
        lbl = fonts.small_bold.render("Level", True, COLORS["text_dim"])
        screen.blit(lbl, (30, 407))

        self.level_down_btn.draw(screen, mouse_pos)
        self.level_up_btn.draw(screen, mouse_pos)

        # Level display
        level_txt = fonts.header_font.render(str(self.char_level), True, COLORS["text_bright"])
        level_cx = 30 + 370 // 2
        screen.blit(level_txt, (level_cx - level_txt.get_width() // 2, 428))

        # Proficiency badge
        prof = calc_proficiency(self.char_level)
        prof_txt = f"Proficiency: +{prof}"
        Badge.draw(screen, 30, 470, prof_txt, COLORS["accent"])

        # --- Summary Stats Panel ---
        summary_panel = Panel(col_x, 500, col_w, 250, title="QUICK STATS")
        summary_panel.draw(screen)

        sy = 535
        effective = {ab: self._get_effective_score(ab) for ab in ABILITY_NAMES}
        con_mod = calc_modifier(effective["constitution"])
        hp = calc_hp(self.char_class, self.char_level, con_mod)
        if self.char_race == "Hill Dwarf":
            hp += self.char_level
        if self.char_class == "Sorcerer" and self.char_subclass == "Draconic Bloodline":
            hp += self.char_level

        ac = calc_ac(self.char_class,
                     AbilityScores(**effective),
                     self.char_subclass)

        speed = RACE_SPEED.get(self.char_race, 30)
        if self.char_class == "Monk" and self.char_level >= 2:
            monk_speed_table = {2: 10, 6: 15, 10: 20, 14: 25, 18: 30}
            for threshold in sorted(monk_speed_table.keys(), reverse=True):
                if self.char_level >= threshold:
                    speed += monk_speed_table[threshold]
                    break
        if self.char_class == "Barbarian" and self.char_level >= 5:
            speed += 10

        hd = HIT_DICE.get(self.char_class, 8)

        stats_data = [
            ("Hit Points", str(hp), COLORS["hp_full"]),
            ("Armor Class", str(ac), COLORS["accent"]),
            ("Speed", f"{speed} ft", COLORS["warning"]),
            ("Hit Dice", f"{self.char_level}d{hd}", COLORS["spell"]),
        ]

        # Class-specific resources
        if self.char_class == "Barbarian":
            rage = BARBARIAN_RAGE_COUNT.get(self.char_level, 0)
            rage_txt = "Unlimited" if rage == -1 else str(rage)
            stats_data.append(("Rages", rage_txt, COLORS["danger"]))
        if self.char_class == "Monk" and self.char_level >= 2:
            stats_data.append(("Ki Points", str(self.char_level), COLORS["monk"]))
        if self.char_class == "Sorcerer" and self.char_level >= 2:
            stats_data.append(("Sorcery Points", str(self.char_level), COLORS["sorcerer"]))
        if self.char_class == "Paladin":
            stats_data.append(("Lay on Hands", str(5 * self.char_level), COLORS["paladin"]))
        if self.char_class == "Bard":
            cha_mod = calc_modifier(self.ability_scores["charisma"])
            die = BARD_INSPIRATION_DIE.get(self.char_level, "1d6")
            stats_data.append(("Bardic Insp.", f"{max(1, cha_mod)}x {die}", COLORS["bard"]))

        for i, (label, val, color) in enumerate(stats_data):
            row_y = sy + i * 28
            if row_y > 730:
                break
            lbl_s = fonts.body_font.render(label, True, COLORS["text_dim"])
            val_s = fonts.body_bold.render(val, True, color)
            screen.blit(lbl_s, (col_x + 15, row_y))
            screen.blit(val_s, (col_x + col_w - 15 - val_s.get_width(), row_y))
            Divider.draw(screen, col_x + 10, row_y + 24, col_w - 20)

    def _draw_center_column(self, screen, mouse_pos):
        """Draw center column: ability scores with point buy + racial ASI."""
        center_x = 440
        center_w = 560

        panel = Panel(center_x, 70, center_w, 480, title="ABILITY SCORES (POINT BUY)")
        panel.draw(screen)

        # Points remaining
        points_used = self._calc_points_used()
        points_left = POINT_BUY_TOTAL - points_used
        points_color = COLORS["success"] if points_left > 0 else (
            COLORS["warning"] if points_left == 0 else COLORS["danger"]
        )
        pts_txt = f"Points Remaining: {points_left} / {POINT_BUY_TOTAL}"
        pts_surf = fonts.body_bold.render(pts_txt, True, points_color)
        screen.blit(pts_surf, (center_x + center_w // 2 - pts_surf.get_width() // 2, 100))

        # Points bar
        bar_x = center_x + 20
        bar_y = 122
        bar_w = center_w - 40
        bar_h = 6
        pct = max(0, min(1, points_left / POINT_BUY_TOTAL))
        pygame.draw.rect(screen, COLORS["hp_bg"], (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if pct > 0:
            pygame.draw.rect(screen, points_color,
                             (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=3)

        # Racial ASI bonuses
        racial_bonuses = self._get_racial_bonuses()

        # Headers
        start_y = 140
        header_y = start_y - 6
        headers = [("Ability", center_x + 20), ("Base", center_x + 218), ("Race", center_x + 270),
                   ("Total", center_x + 325), ("Mod", center_x + 390),
                   ("Save", center_x + 455), ("Cost", center_x + 518)]
        for hdr_text, hdr_x in headers:
            hs = fonts.small_bold.render(hdr_text, True, COLORS["text_muted"])
            screen.blit(hs, (hdr_x, header_y))

        # Saving throw proficiencies for current class
        prof_saves = SAVING_THROW_PROF.get(self.char_class, ())
        prof_bonus = calc_proficiency(self.char_level)

        row_h = 62
        for i, ab in enumerate(ABILITY_NAMES):
            y = start_y + i * row_h + 10
            base_score = self.ability_scores[ab]
            racial_bonus = racial_bonuses.get(ab, 0)
            total_score = base_score + racial_bonus
            mod = calc_modifier(total_score)
            cost = POINT_BUY_COST.get(base_score, 0)

            # Row background (alternating)
            row_rect = pygame.Rect(center_x + 5, y - 4, center_w - 10, row_h - 4)
            if i % 2 == 0:
                pygame.draw.rect(screen, COLORS["panel_light"], row_rect, border_radius=4)

            # Ability name
            ab_label = ABILITY_ABBREVS[i]
            ab_full = ab.capitalize()

            # Class color for the abbreviation
            class_color_key = self.char_class.lower()
            ab_color = COLORS.get(class_color_key, COLORS["accent"])

            ab_abbr_surf = fonts.header_font.render(ab_label, True, ab_color)
            screen.blit(ab_abbr_surf, (center_x + 20, y))
            ab_name_surf = fonts.small_font.render(ab_full, True, COLORS["text_dim"])
            screen.blit(ab_name_surf, (center_x + 65, y + 8))

            # Score with +/- buttons
            minus_rect = pygame.Rect(center_x + 188, y + 2, 28, 28)
            plus_rect = pygame.Rect(center_x + 245, y + 2, 28, 28)

            # Minus button
            minus_hover = minus_rect.collidepoint(mouse_pos)
            minus_col = COLORS["danger_hover"] if minus_hover else COLORS["danger_dim"]
            can_decrease = base_score > POINT_BUY_MIN
            if not can_decrease:
                minus_col = COLORS["disabled"]
            pygame.draw.rect(screen, minus_col, minus_rect, border_radius=4)
            pygame.draw.rect(screen, COLORS["border"], minus_rect, 1, border_radius=4)
            ms = fonts.body_bold.render("-", True,
                                        COLORS["text_bright"] if can_decrease else COLORS["text_muted"])
            screen.blit(ms, (minus_rect.centerx - ms.get_width() // 2,
                             minus_rect.centery - ms.get_height() // 2))

            # Base score value
            score_surf = fonts.body_bold.render(str(base_score), True, COLORS["text_main"])
            score_x = center_x + 224
            screen.blit(score_surf, (score_x - score_surf.get_width() // 2, y + 4))

            # Plus button
            plus_hover = plus_rect.collidepoint(mouse_pos)
            can_increase = base_score < POINT_BUY_MAX and (
                points_used + POINT_BUY_COST.get(base_score + 1, 99) - cost <= POINT_BUY_TOTAL
            )
            plus_col = COLORS["success_hover"] if (plus_hover and can_increase) else (
                COLORS["success_dim"] if can_increase else COLORS["disabled"]
            )
            pygame.draw.rect(screen, plus_col, plus_rect, border_radius=4)
            pygame.draw.rect(screen, COLORS["border"], plus_rect, 1, border_radius=4)
            ps = fonts.body_bold.render("+", True,
                                        COLORS["text_bright"] if can_increase else COLORS["text_muted"])
            screen.blit(ps, (plus_rect.centerx - ps.get_width() // 2,
                             plus_rect.centery - ps.get_height() // 2))

            # Racial bonus
            if racial_bonus > 0:
                rb_surf = fonts.body_bold.render(f"+{racial_bonus}", True, COLORS["success"])
                screen.blit(rb_surf, (center_x + 278, y + 4))
            else:
                rb_surf = fonts.body_font.render("--", True, COLORS["text_muted"])
                screen.blit(rb_surf, (center_x + 278, y + 4))

            # Total score (highlighted)
            total_col = COLORS["text_bright"] if racial_bonus > 0 else COLORS["text_main"]
            total_surf = fonts.header_font.render(str(total_score), True, total_col)
            screen.blit(total_surf, (center_x + 330, y))

            # Modifier (based on total)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            mod_col = COLORS["success"] if mod > 0 else (COLORS["danger"] if mod < 0 else COLORS["text_dim"])
            mod_surf = fonts.body_bold.render(mod_str, True, mod_col)
            screen.blit(mod_surf, (center_x + 398, y + 4))

            # Saving throw (based on total)
            save_mod = mod + (prof_bonus if ab in prof_saves else 0)
            save_str = f"+{save_mod}" if save_mod >= 0 else str(save_mod)
            is_prof = ab in prof_saves
            save_col = COLORS["accent"] if is_prof else COLORS["text_dim"]
            save_surf = fonts.body_bold.render(save_str, True, save_col)
            screen.blit(save_surf, (center_x + 460, y + 4))
            if is_prof:
                pygame.draw.circle(screen, COLORS["accent"],
                                   (center_x + 452, y + 14), 4)

            # Point cost
            cost_surf = fonts.body_font.render(str(cost), True, COLORS["text_muted"])
            screen.blit(cost_surf, (center_x + 525, y + 4))

        # Variant Human / Half-Elf ASI choice buttons
        if self.char_race in ("Variant Human", "Half-Elf"):
            self._draw_asi_choices(screen, mouse_pos, center_x, start_y + 6 * row_h + 15, center_w)

    def _draw_right_column(self, screen, mouse_pos):
        """Draw right column: features and racial traits."""
        right_x = 1030
        right_w = 870

        # --- Class Features Panel ---
        feat_panel_h = 440
        feat_panel = Panel(right_x, 70, right_w, feat_panel_h, title="CLASS FEATURES")
        feat_panel.draw(screen)

        features = get_class_features(self.char_class, self.char_level, self.char_subclass)

        clip_rect = pygame.Rect(right_x + 5, 100, right_w - 10, feat_panel_h - 40)
        screen.set_clip(clip_rect)

        fy = 105 - self.feature_scroll
        for feat in features:
            if fy > 70 + feat_panel_h:
                break
            if fy + 40 >= 100:
                # Feature name
                name_surf = fonts.body_bold.render(feat.name, True, COLORS["text_bright"])
                screen.blit(name_surf, (right_x + 15, fy))

                # Mechanic badge
                if feat.mechanic:
                    badge_x = right_x + 20 + name_surf.get_width() + 5
                    if badge_x + 80 < right_x + right_w:
                        Badge.draw(screen, badge_x, fy + 2, feat.mechanic,
                                   COLORS.get(self.char_class.lower(), COLORS["accent_dim"]),
                                   font=fonts.tiny_font)

                # Description (truncated)
                if feat.description:
                    desc_text = feat.description
                    if len(desc_text) > 100:
                        desc_text = desc_text[:97] + "..."
                    desc_surf = fonts.small_font.render(desc_text, True, COLORS["text_dim"])
                    # Clip the description to not overflow
                    desc_clip = pygame.Rect(right_x + 15, fy + 20, right_w - 30, 16)
                    old_clip = screen.get_clip()
                    screen.set_clip(desc_clip.clip(clip_rect))
                    screen.blit(desc_surf, (right_x + 15, fy + 20))
                    screen.set_clip(clip_rect)

                # Uses indicator
                if feat.uses_per_day > 0:
                    uses_txt = f"{feat.uses_per_day}/day"
                    if feat.short_rest_recharge:
                        uses_txt = f"{feat.uses_per_day}/rest"
                    uses_s = fonts.tiny_font.render(uses_txt, True, COLORS["warning"])
                    screen.blit(uses_s, (right_x + right_w - 70, fy + 3))

            fy += 42

        screen.set_clip(None)

        # Scroll indicator
        if len(features) * 42 > feat_panel_h - 40:
            max_scroll = max(0, len(features) * 42 - feat_panel_h + 40)
            if max_scroll > 0:
                sb_total_h = feat_panel_h - 40
                sb_h = max(20, int(sb_total_h * sb_total_h / (len(features) * 42)))
                sb_y = 100 + int((sb_total_h - sb_h) * min(1, self.feature_scroll / max_scroll))
                sb_rect = pygame.Rect(right_x + right_w - 8, sb_y, 5, sb_h)
                pygame.draw.rect(screen, COLORS["scrollbar_thumb"], sb_rect, border_radius=2)

        # --- Racial Traits Panel ---
        trait_y = 530
        trait_h = SCREEN_HEIGHT - trait_y - 90
        trait_panel = Panel(right_x, trait_y, right_w, trait_h, title=f"RACIAL TRAITS - {self.char_race}")
        trait_panel.draw(screen)

        traits = get_racial_traits(self.char_race)

        clip_rect2 = pygame.Rect(right_x + 5, trait_y + 30, right_w - 10, trait_h - 40)
        screen.set_clip(clip_rect2)

        ty = trait_y + 35 - self.trait_scroll
        for trait in traits:
            if ty > trait_y + trait_h:
                break
            if ty + 30 >= trait_y + 30:
                # Trait name
                tn = fonts.body_bold.render(trait.name, True, COLORS["text_bright"])
                screen.blit(tn, (right_x + 15, ty))

                # Description
                if trait.description:
                    desc = trait.description
                    if len(desc) > 90:
                        desc = desc[:87] + "..."
                    td = fonts.small_font.render(desc, True, COLORS["text_dim"])
                    desc_clip2 = pygame.Rect(right_x + 15, ty + 20, right_w - 30, 16)
                    old_clip2 = screen.get_clip()
                    screen.set_clip(desc_clip2.clip(clip_rect2))
                    screen.blit(td, (right_x + 15, ty + 20))
                    screen.set_clip(clip_rect2)

                # Mechanic badge
                if trait.mechanic:
                    Badge.draw(screen, right_x + 20 + tn.get_width() + 5, ty + 2,
                               trait.mechanic, COLORS["accent_dim"], font=fonts.tiny_font)

            ty += 40

        screen.set_clip(None)

    def _toggle_asi_choice(self, ability):
        """Toggle an ability for Variant Human / Half-Elf free ASI choices."""
        if self.char_race == "Variant Human":
            if ability in self.variant_asi_choices:
                self.variant_asi_choices.remove(ability)
            elif len(self.variant_asi_choices) < 2:
                self.variant_asi_choices.append(ability)
        elif self.char_race == "Half-Elf":
            if ability == "charisma":
                return  # Already gets +2 CHA
            if ability in self.halfelf_asi_choices:
                self.halfelf_asi_choices.remove(ability)
            elif len(self.halfelf_asi_choices) < 2:
                self.halfelf_asi_choices.append(ability)

    def _draw_asi_choices(self, screen, mouse_pos, cx, cy, cw):
        """Draw clickable ASI choice buttons for Variant Human / Half-Elf."""
        if self.char_race == "Variant Human":
            label = f"Choose 2 abilities for +1 ({len(self.variant_asi_choices)}/2):"
            choices = self.variant_asi_choices
        else:  # Half-Elf
            label = f"Choose 2 abilities for +1 ({len(self.halfelf_asi_choices)}/2, not CHA):"
            choices = self.halfelf_asi_choices

        lbl_surf = fonts.small_bold.render(label, True, COLORS["warning"])
        screen.blit(lbl_surf, (cx + 15, cy))

        for i, ab in enumerate(ABILITY_NAMES):
            if self.char_race == "Half-Elf" and ab == "charisma":
                continue
            btn_x = cx + 15 + (i % 3) * 180
            btn_y = cy + 22 + (i // 3) * 30
            btn_rect = pygame.Rect(btn_x, btn_y, 170, 26)

            is_selected = ab in choices
            is_hover = btn_rect.collidepoint(mouse_pos)

            if is_selected:
                pygame.draw.rect(screen, COLORS["success_dim"], btn_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["success"], btn_rect, 2, border_radius=4)
                txt_col = COLORS["text_bright"]
            elif is_hover:
                pygame.draw.rect(screen, COLORS["hover"], btn_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["border_light"], btn_rect, 1, border_radius=4)
                txt_col = COLORS["text_main"]
            else:
                pygame.draw.rect(screen, COLORS["panel_dark"], btn_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["border"], btn_rect, 1, border_radius=4)
                txt_col = COLORS["text_dim"]

            ab_txt = f"{ABILITY_ABBREVS[ABILITY_NAMES.index(ab)]} {ab.capitalize()}"
            if is_selected:
                ab_txt += " +1"
            ts = fonts.small_font.render(ab_txt, True, txt_col)
            screen.blit(ts, (btn_x + 8, btn_y + 5))

    def _draw_computed_stats(self, screen, mouse_pos):
        """Draw spell slots and spellcasting info in the center-bottom area."""
        cx = 440
        cw = 560
        cy = 560
        ch = SCREEN_HEIGHT - cy - 90

        spell_ability = SPELLCASTING_ABILITY.get(self.char_class, "")

        if spell_ability:
            panel = Panel(cx, cy, cw, ch, title="SPELLCASTING")
            panel.draw(screen)

            prof = calc_proficiency(self.char_level)
            ability_key = spell_ability.lower()
            casting_mod = calc_modifier(self._get_effective_score(ability_key))
            save_dc = 8 + prof + casting_mod
            atk_bonus = prof + casting_mod

            # Spellcasting info row
            info_y = cy + 35
            info_items = [
                ("Ability", spell_ability, COLORS["spell"]),
                ("Save DC", str(save_dc), COLORS["warning"]),
                ("Atk Bonus", f"+{atk_bonus}", COLORS["accent"]),
            ]
            ix = cx + 15
            for label, val, color in info_items:
                ls = fonts.small_font.render(label, True, COLORS["text_muted"])
                vs = fonts.body_bold.render(val, True, color)
                screen.blit(ls, (ix, info_y))
                screen.blit(vs, (ix, info_y + 16))
                ix += 150

            # Spell slots
            slots = calc_spell_slots(self.char_class, self.char_level, self.char_subclass)

            if slots:
                slot_y = info_y + 50
                slot_label = fonts.small_bold.render("Spell Slots:", True, COLORS["text_dim"])
                screen.blit(slot_label, (cx + 15, slot_y))
                slot_y += 22

                sx = cx + 15
                for slot_name, count in slots.items():
                    # Draw slot boxes
                    slot_box_w = 55
                    if sx + slot_box_w > cx + cw - 10:
                        sx = cx + 15
                        slot_y += 50

                    # Slot level label
                    sl_surf = fonts.tiny_font.render(slot_name, True, COLORS["text_muted"])
                    screen.blit(sl_surf, (sx + slot_box_w // 2 - sl_surf.get_width() // 2, slot_y))

                    # Slot count
                    count_surf = fonts.header_font.render(str(count), True, COLORS["spell"])
                    screen.blit(count_surf,
                                (sx + slot_box_w // 2 - count_surf.get_width() // 2, slot_y + 14))

                    # Slot dot indicators
                    dot_y = slot_y + 42
                    for d in range(count):
                        dot_x = sx + 5 + d * 12
                        if dot_x < sx + slot_box_w:
                            pygame.draw.circle(screen, COLORS["spell"], (dot_x + 4, dot_y + 4), 4)
                            pygame.draw.circle(screen, COLORS["border"], (dot_x + 4, dot_y + 4), 4, 1)

                    sx += slot_box_w + 5

                # Warlock note
                if self.char_class == "Warlock":
                    note_y = slot_y + 55
                    if note_y < cy + ch - 20:
                        note = fonts.small_font.render(
                            "Pact Magic: All slots at highest level, recharge on short rest",
                            True, COLORS["text_muted"])
                        screen.blit(note, (cx + 15, note_y))

        else:
            # Non-caster: show saving throws summary or additional info
            panel = Panel(cx, cy, cw, ch, title="COMBAT STATS")
            panel.draw(screen)

            info_y = cy + 35
            prof = calc_proficiency(self.char_level)
            prof_saves = SAVING_THROW_PROF.get(self.char_class, ())

            # Saving throws summary
            st_label = fonts.small_bold.render("Saving Throw Proficiencies:", True, COLORS["text_dim"])
            screen.blit(st_label, (cx + 15, info_y))
            info_y += 22

            for ab in ABILITY_NAMES:
                mod = calc_modifier(self._get_effective_score(ab))
                is_prof = ab in prof_saves
                save_val = mod + (prof if is_prof else 0)
                save_str = f"+{save_val}" if save_val >= 0 else str(save_val)
                color = COLORS["accent"] if is_prof else COLORS["text_muted"]

                ab_surf = fonts.body_font.render(f"{ab.capitalize()}: {save_str}", True, color)
                screen.blit(ab_surf, (cx + 15, info_y))

                if is_prof:
                    # Proficiency dot
                    pygame.draw.circle(screen, COLORS["accent"], (cx + 8, info_y + 9), 4)

                info_y += 24

            # Weapon attacks summary
            info_y += 10
            atk_label = fonts.small_bold.render("Default Attacks:", True, COLORS["text_dim"])
            screen.blit(atk_label, (cx + 15, info_y))
            info_y += 22

            eff_scores = {ab: self._get_effective_score(ab) for ab in ABILITY_NAMES}
            abilities_obj = AbilityScores(**eff_scores)
            actions = build_default_actions(self.char_class, abilities_obj, prof, self.char_level)
            for action in actions:
                if action.is_multiattack:
                    continue
                atk_str = f"+{action.attack_bonus}" if action.attack_bonus >= 0 else str(action.attack_bonus)
                dmg_bonus_str = f"+{action.damage_bonus}" if action.damage_bonus > 0 else (
                    str(action.damage_bonus) if action.damage_bonus < 0 else "")
                txt = f"{action.name}: {atk_str} to hit, {action.damage_dice}{dmg_bonus_str} {action.damage_type}"
                as_surf = fonts.small_font.render(txt, True, COLORS["text_main"])
                screen.blit(as_surf, (cx + 25, info_y))
                info_y += 20

    def _draw_bottom_bar(self, screen, mouse_pos):
        """Draw bottom action bar."""
        bar_y = SCREEN_HEIGHT - 80
        pygame.draw.rect(screen, COLORS["panel_dark"], (0, bar_y, SCREEN_WIDTH, 80))
        pygame.draw.line(screen, COLORS["border"], (0, bar_y), (SCREEN_WIDTH, bar_y), 1)

        # Class color indicator
        class_color_key = self.char_class.lower()
        class_color = COLORS.get(class_color_key, COLORS["accent"])
        pygame.draw.rect(screen, class_color, (0, bar_y, 5, 80))

        # Character summary in bottom bar
        name = self.name_input.text.strip() or "Unnamed Hero"
        summary = f"{name}  |  {self.char_race} {self.char_class}"
        if self.char_subclass:
            summary += f" ({self.char_subclass})"
        summary += f"  |  Level {self.char_level}"
        sum_surf = fonts.body_bold.render(summary, True, COLORS["text_main"])
        screen.blit(sum_surf, (220, bar_y + 17))

        # Buttons
        self.btn_back.draw(screen, mouse_pos)
        self.btn_save.draw(screen, mouse_pos)
        self.btn_export.draw(screen, mouse_pos)
