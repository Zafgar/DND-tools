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
from data.models import CreatureStats, AbilityScores, Action, SpellInfo, Feature, RacialTrait, Item
from data.class_features import get_class_features, BARBARIAN_RAGE_COUNT
from data.equipment import (get_item, get_all_weapons, get_all_armor, get_all_shields,
                            get_all_wondrous, get_all_consumables, ALL_ITEMS_DB,
                            WEAPON_DB, ARMOR_DB, SHIELD_DB, WONDROUS_DB, CONSUMABLE_DB)
from data.racial_traits import (get_racial_traits, RACE_TRAITS_MAP, get_racial_asi, RACE_ASI,
                                ALL_RACES, RACE_SPEED as RACIAL_SPEED_TABLE, get_race_size)
from data.heroes import hero_list
from data.hero_import import export_hero_to_file, import_hero_from_file, export_heroes_to_file, import_heroes_from_file

try:
    from data.feats import ALL_FEATS, get_feats_available, FEATS_BY_NAME
except ImportError:
    ALL_FEATS = []
    FEATS_BY_NAME = {}
    def get_feats_available(**kw): return []

from data.spells import _spells as SPELL_DATABASE, get_spell

SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


# ============================================================
# Data Tables
# ============================================================

RACE_LIST = ALL_RACES

CLASS_LIST = [
    "Barbarian", "Fighter", "Paladin", "Rogue", "Ranger",
    "Cleric", "Wizard", "Warlock", "Sorcerer", "Bard", "Druid", "Monk",
]

SUBCLASS_MAP = {
    "Barbarian": ["Totem Warrior", "Berserker", "Ancestral Guardian", "Storm Herald", "Zealot",
                   "Path of the Beast", "Path of Wild Magic"],
    "Fighter": ["Champion", "Battle Master", "Eldritch Knight", "Arcane Archer", "Cavalier", "Samurai",
                "Psi Warrior", "Rune Knight"],
    "Paladin": ["Devotion", "Vengeance", "Ancients", "Conquest", "Redemption", "Crown",
                "Oath of Glory", "Oath of the Watchers"],
    "Rogue": ["Assassin", "Thief", "Arcane Trickster", "Swashbuckler", "Scout", "Inquisitive", "Mastermind",
              "Phantom", "Soulknife"],
    "Ranger": ["Hunter", "Beast Master", "Gloom Stalker", "Horizon Walker", "Monster Slayer",
               "Fey Wanderer", "Swarmkeeper"],
    "Cleric": ["Life", "War", "Light", "Knowledge", "Nature", "Tempest", "Trickery", "Forge", "Grave",
               "Order", "Peace", "Twilight"],
    "Wizard": ["Evocation", "Abjuration", "Divination", "Conjuration", "Enchantment",
               "Illusion", "Necromancy", "Transmutation", "War Magic", "Bladesinging",
               "Order of Scribes"],
    "Warlock": ["Fiend", "Great Old One", "Archfey", "Hexblade", "Celestial",
                "Fathomless", "Genie"],
    "Sorcerer": ["Draconic Bloodline", "Wild Magic", "Divine Soul", "Shadow Magic", "Storm Sorcery",
                 "Aberrant Mind", "Clockwork Soul"],
    "Bard": ["College of Lore", "College of Valor", "College of Swords", "College of Whispers",
             "College of Glamour", "College of Creation", "College of Eloquence"],
    "Druid": ["Circle of the Moon", "Circle of the Land", "Circle of Dreams",
              "Circle of the Shepherd", "Circle of Spores", "Circle of Stars", "Circle of Wildfire"],
    "Monk": ["Way of the Open Hand", "Way of Shadow", "Way of the Four Elements",
             "Way of the Drunken Master", "Way of the Kensei", "Way of the Sun Soul",
             "Way of the Long Death", "Way of the Astral Self", "Way of Mercy"],
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

RACE_SPEED = RACIAL_SPEED_TABLE

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

# ASI / Feat levels per class (all classes get ASI at 4, 8, 12, 16, 19; Fighter/Rogue get extras)
ASI_LEVELS = {
    "Barbarian": [4, 8, 12, 16, 19],
    "Bard": [4, 8, 12, 16, 19],
    "Cleric": [4, 8, 12, 16, 19],
    "Druid": [4, 8, 12, 16, 19],
    "Fighter": [4, 6, 8, 12, 14, 16, 19],
    "Monk": [4, 8, 12, 16, 19],
    "Paladin": [4, 8, 12, 16, 19],
    "Ranger": [4, 8, 12, 16, 19],
    "Rogue": [4, 8, 10, 12, 16, 19],
    "Sorcerer": [4, 8, 12, 16, 19],
    "Warlock": [4, 8, 12, 16, 19],
    "Wizard": [4, 8, 12, 16, 19],
}

# D&D 5e skills with governing ability
ALL_SKILLS = [
    ("Acrobatics", "dexterity"), ("Animal Handling", "wisdom"), ("Arcana", "intelligence"),
    ("Athletics", "strength"), ("Deception", "charisma"), ("History", "intelligence"),
    ("Insight", "wisdom"), ("Intimidation", "charisma"), ("Investigation", "intelligence"),
    ("Medicine", "wisdom"), ("Nature", "intelligence"), ("Perception", "wisdom"),
    ("Performance", "charisma"), ("Persuasion", "charisma"), ("Religion", "intelligence"),
    ("Sleight of Hand", "dexterity"), ("Stealth", "dexterity"), ("Survival", "wisdom"),
]

CLASS_SKILL_CHOICES = {
    "Barbarian": (2, ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]),
    "Bard": (3, [s[0] for s in ALL_SKILLS]),  # Any 3
    "Cleric": (2, ["History", "Insight", "Medicine", "Persuasion", "Religion"]),
    "Druid": (2, ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"]),
    "Fighter": (2, ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"]),
    "Monk": (2, ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"]),
    "Paladin": (2, ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"]),
    "Ranger": (3, ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"]),
    "Rogue": (4, ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"]),
    "Sorcerer": (2, ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"]),
    "Warlock": (2, ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"]),
    "Wizard": (2, ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"]),
}

# Class spell lists (mapping class to list of spell names from SPELL_DATABASE)
CLASS_SPELL_LISTS = {
    "Wizard": {
        "cantrips": ["Acid Splash", "Chill Touch", "Fire Bolt", "Mage Hand", "Poison Spray", "Ray of Frost",
                     "Shocking Grasp", "Toll the Dead", "Sword Burst", "Booming Blade", "Green-Flame Blade",
                     "Lightning Lure", "Mind Sliver"],
        "spells": ["Burning Hands", "Chromatic Orb", "Mage Armor", "Magic Missile", "Shield", "Thunderwave",
                   "Absorb Elements", "Catapult", "Chaos Bolt", "Earth Tremor", "Ice Knife", "Silvery Barbs",
                   "Blindness/Deafness", "Hold Person", "Invisibility", "Misty Step", "Scorching Ray", "Shatter",
                   "Web", "Mirror Image", "Aganazzar's Scorcher", "Dragon's Breath", "Mind Spike", "Shadow Blade",
                   "Tasha's Mind Whip", "Kinetic Jaunt",
                   "Counterspell", "Dispel Magic", "Fear", "Fireball", "Fly", "Haste", "Lightning Bolt",
                   "Erupting Earth", "Thunder Step", "Enemies Abound", "Catnap", "Intellect Fortress", "Spirit Shroud",
                   "Banishment", "Blight", "Dimension Door", "Greater Invisibility", "Ice Storm", "Wall of Fire",
                   "Elemental Bane", "Sickening Radiance", "Vitriolic Sphere", "Storm Sphere",
                   "Summon Aberration", "Summon Construct",
                   "Cloudkill", "Cone of Cold", "Hold Monster", "Synaptic Static", "Steel Wind Strike",
                   "Wall of Light", "Immolation", "Summon Draconic Spirit",
                   "Chain Lightning", "Disintegrate", "Sunbeam",
                   "Finger of Death", "Fire Storm", "Plane Shift",
                   "Dominate Monster", "Power Word Stun", "Sunburst",
                   "Meteor Swarm", "Power Word Kill", "Time Stop"],
    },
    "Sorcerer": {
        "cantrips": ["Acid Splash", "Chill Touch", "Fire Bolt", "Mage Hand", "Poison Spray", "Ray of Frost",
                     "Shocking Grasp", "Booming Blade", "Green-Flame Blade", "Lightning Lure", "Mind Sliver",
                     "Infestation", "Sword Burst"],
        "spells": ["Burning Hands", "Chromatic Orb", "Mage Armor", "Magic Missile", "Shield", "Thunderwave",
                   "Absorb Elements", "Catapult", "Chaos Bolt", "Ice Knife", "Silvery Barbs",
                   "Tasha's Caustic Brew",
                   "Blindness/Deafness", "Hold Person", "Invisibility", "Misty Step", "Scorching Ray", "Shatter", "Web",
                   "Aganazzar's Scorcher", "Dragon's Breath", "Mind Spike", "Tasha's Mind Whip", "Kinetic Jaunt",
                   "Counterspell", "Dispel Magic", "Fear", "Fireball", "Fly", "Haste", "Lightning Bolt",
                   "Erupting Earth", "Thunder Step", "Enemies Abound", "Intellect Fortress",
                   "Banishment", "Blight", "Dimension Door", "Greater Invisibility", "Ice Storm", "Wall of Fire",
                   "Vitriolic Sphere", "Storm Sphere",
                   "Cloudkill", "Cone of Cold", "Hold Monster", "Synaptic Static", "Immolation", "Enervation",
                   "Chain Lightning", "Disintegrate", "Sunbeam",
                   "Finger of Death", "Fire Storm",
                   "Dominate Monster", "Power Word Stun",
                   "Meteor Swarm", "Power Word Kill"],
    },
    "Cleric": {
        "cantrips": ["Guidance", "Resistance", "Sacred Flame", "Toll the Dead", "Word of Radiance"],
        "spells": ["Bless", "Command", "Cure Wounds", "Guiding Bolt", "Healing Word", "Inflict Wounds",
                   "Shield of Faith", "Silvery Barbs",
                   "Blindness/Deafness", "Hold Person", "Lesser Restoration", "Silence", "Spiritual Weapon",
                   "Enhance Ability", "Wither and Bloom",
                   "Animate Dead", "Dispel Magic", "Revivify", "Spirit Guardians", "Life Transference",
                   "Spirit Shroud",
                   "Banishment",
                   "Flame Strike", "Mass Cure Wounds", "Holy Weapon", "Summon Draconic Spirit",
                   "Sunbeam",
                   "Fire Storm",
                   "Sunburst"],
    },
    "Druid": {
        "cantrips": ["Guidance", "Poison Spray", "Resistance", "Primal Savagery", "Infestation"],
        "spells": ["Cure Wounds", "Entangle", "Faerie Fire", "Healing Word", "Thunderwave",
                   "Absorb Elements", "Earth Tremor", "Ice Knife",
                   "Heat Metal", "Hold Person", "Lesser Restoration", "Moonbeam", "Enhance Ability",
                   "Healing Spirit", "Wither and Bloom",
                   "Call Lightning", "Conjure Animals", "Dispel Magic", "Erupting Earth",
                   "Intellect Fortress", "Summon Shadowspawn",
                   "Blight", "Ice Storm", "Wall of Fire", "Elemental Bane", "Summon Construct",
                   "Mass Cure Wounds", "Immolation", "Summon Draconic Spirit",
                   "Sunbeam",
                   "Fire Storm", "Plane Shift",
                   "Sunburst"],
    },
    "Bard": {
        "cantrips": ["Mage Hand", "Vicious Mockery"],
        "spells": ["Cure Wounds", "Dissonant Whispers", "Faerie Fire", "Healing Word", "Heroism",
                   "Tasha's Hideous Laughter", "Silvery Barbs",
                   "Blindness/Deafness", "Hold Person", "Invisibility", "Lesser Restoration", "Silence",
                   "Enhance Ability", "Kinetic Jaunt",
                   "Counterspell", "Dispel Magic", "Fear", "Catnap", "Enemies Abound", "Intellect Fortress",
                   "Dimension Door", "Greater Invisibility",
                   "Hold Monster", "Mass Cure Wounds", "Synaptic Static",
                   "Dominate Monster", "Power Word Stun",
                   "Power Word Kill"],
    },
    "Warlock": {
        "cantrips": ["Chill Touch", "Eldritch Blast", "Mage Hand", "Poison Spray",
                     "Toll the Dead", "Booming Blade", "Green-Flame Blade", "Mind Sliver"],
        "spells": ["Burning Hands", "Hellish Rebuke", "Hex", "Armor of Agathys",
                   "Hold Person", "Invisibility", "Misty Step", "Shatter", "Mirror Image",
                   "Mind Spike", "Shadow Blade",
                   "Counterspell", "Dispel Magic", "Fear", "Fly", "Vampiric Touch",
                   "Enemies Abound", "Thunder Step", "Spirit Shroud", "Summon Shadowspawn",
                   "Banishment", "Blight", "Dimension Door", "Shadow of Moil",
                   "Sickening Radiance", "Elemental Bane", "Summon Aberration",
                   "Cone of Cold", "Hold Monster", "Enervation", "Danse Macabre",
                   "Synaptic Static",
                   "Chain Lightning",
                   "Finger of Death", "Plane Shift",
                   "Dominate Monster", "Power Word Stun",
                   "Power Word Kill"],
    },
    "Paladin": {
        "cantrips": [],
        "spells": ["Bless", "Command", "Cure Wounds", "Divine Favor", "Heroism", "Shield of Faith",
                   "Lesser Restoration", "Magic Weapon",
                   "Dispel Magic", "Revivify", "Spirit Shroud",
                   "Banishment",
                   "Holy Weapon"],
    },
    "Ranger": {
        "cantrips": [],
        "spells": ["Cure Wounds", "Entangle", "Hail of Thorns", "Hunter's Mark",
                   "Absorb Elements", "Zephyr Strike",
                   "Lesser Restoration", "Silence", "Healing Spirit",
                   "Conjure Animals", "Lightning Bolt",
                   "Greater Invisibility",
                   "Steel Wind Strike"],
    },
    "Fighter": {  # Eldritch Knight
        "cantrips": ["Fire Bolt", "Ray of Frost", "Shocking Grasp", "Mage Hand",
                     "Booming Blade", "Green-Flame Blade", "Lightning Lure", "Sword Burst"],
        "spells": ["Burning Hands", "Magic Missile", "Shield", "Thunderwave",
                   "Absorb Elements", "Ice Knife", "Silvery Barbs",
                   "Blindness/Deafness", "Hold Person", "Misty Step", "Scorching Ray", "Shatter",
                   "Web", "Mirror Image", "Shadow Blade", "Tasha's Mind Whip", "Kinetic Jaunt",
                   "Counterspell", "Dispel Magic", "Fireball", "Fly", "Haste", "Lightning Bolt",
                   "Thunder Step", "Intellect Fortress"],
    },
    "Rogue": {  # Arcane Trickster
        "cantrips": ["Fire Bolt", "Mage Hand", "Ray of Frost", "Shocking Grasp",
                     "Booming Blade", "Green-Flame Blade", "Mind Sliver"],
        "spells": ["Burning Hands", "Chromatic Orb", "Mage Armor", "Magic Missile", "Shield", "Thunderwave",
                   "Silvery Barbs", "Tasha's Caustic Brew",
                   "Blindness/Deafness", "Hold Person", "Invisibility", "Misty Step", "Scorching Ray",
                   "Web", "Mirror Image", "Shadow Blade", "Tasha's Mind Whip",
                   "Counterspell", "Dispel Magic", "Fear", "Fireball", "Fly", "Haste"],
    },
}

# Cantrips known by level (full casters)
CANTRIPS_KNOWN = {
    "Wizard":   {1: 3, 4: 4, 10: 5},
    "Sorcerer": {1: 4, 4: 5, 10: 6},
    "Cleric":   {1: 3, 4: 4, 10: 5},
    "Druid":    {1: 2, 4: 3, 10: 4},
    "Bard":     {1: 2, 4: 3, 10: 4},
    "Warlock":  {1: 2, 4: 3, 10: 4},
    "Fighter":  {3: 2, 10: 3},
    "Rogue":    {3: 2, 10: 3},
}

# Spells known by level (for Sorcerer, Bard, Ranger, Warlock, EK, AT)
SPELLS_KNOWN_TABLE = {
    "Sorcerer": {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,13:13,15:14,17:15},
    "Bard":     {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:14,11:15,13:16,15:18,17:19,18:20},
    "Ranger":   {2:2,3:3,5:4,7:5,9:6,11:7,13:8,15:9,17:10,19:11},
    "Warlock":  {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,11:11,13:12,15:13,17:14,19:15},
    "Fighter":  {3:3,4:4,7:5,8:6,10:7,11:8,13:9,14:10,16:11,19:12,20:13},
    "Rogue":    {3:3,4:4,7:5,8:6,10:7,11:8,13:9,14:10,16:11,19:12,20:13},
}

# Equipment choices per class (simplified)
WEAPON_CHOICES = {
    "Barbarian": ["Greataxe", "Greatsword", "Handaxe (x2)", "Maul"],
    "Fighter": ["Longsword + Shield", "Greatsword", "Longbow", "Two Shortswords", "Rapier + Shield"],
    "Paladin": ["Longsword + Shield", "Greatsword", "Warhammer + Shield", "Two Shortswords"],
    "Rogue": ["Rapier", "Shortsword", "Shortbow + Dagger", "Two Daggers"],
    "Ranger": ["Longbow", "Two Shortswords", "Shortsword + Shield"],
    "Cleric": ["Mace + Shield", "Warhammer + Shield", "Light Crossbow"],
    "Wizard": ["Quarterstaff", "Dagger"],
    "Warlock": ["Light Crossbow", "Quarterstaff", "Two Daggers"],
    "Sorcerer": ["Light Crossbow", "Dagger", "Quarterstaff"],
    "Bard": ["Rapier", "Longsword", "Shortbow + Dagger"],
    "Druid": ["Quarterstaff + Shield", "Scimitar + Shield", "Club"],
    "Monk": ["Shortsword", "Quarterstaff", "Handaxe (x2)", "Dart (x10)"],
}

ARMOR_CHOICES = {
    "Barbarian": ["No Armor (Unarmored Defense)", "Shield"],
    "Fighter": ["Chain Mail", "Leather Armor", "Scale Mail", "Chain Mail + Shield"],
    "Paladin": ["Chain Mail + Shield", "Scale Mail + Shield", "Ring Mail + Shield"],
    "Rogue": ["Leather Armor", "Studded Leather"],
    "Ranger": ["Scale Mail", "Leather Armor"],
    "Cleric": ["Chain Mail + Shield", "Scale Mail + Shield", "Leather Armor + Shield"],
    "Wizard": ["No Armor"],
    "Warlock": ["Leather Armor", "Studded Leather"],
    "Sorcerer": ["No Armor"],
    "Bard": ["Leather Armor", "Studded Leather"],
    "Druid": ["Leather Armor + Shield", "Hide Armor + Shield"],
    "Monk": ["No Armor (Unarmored Defense)"],
}


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


def build_default_actions(char_class, abilities, prof_bonus, level, weapon_choice=""):
    """Build default weapon/attack actions for a class."""
    str_mod = calc_modifier(abilities.strength)
    dex_mod = calc_modifier(abilities.dexterity)

    # Weapon database: name -> (die, damage_type, range, ability, is_heavy, is_finesse, is_reach)
    WEAPONS = {
        "Greataxe": ("1d12", "slashing", 5, "str", True, False, False),
        "Greatsword": ("2d6", "slashing", 5, "str", True, False, False),
        "Maul": ("2d6", "bludgeoning", 5, "str", True, False, False),
        "Longsword": ("1d8", "slashing", 5, "str", False, False, False),
        "Warhammer": ("1d8", "bludgeoning", 5, "str", False, False, False),
        "Rapier": ("1d8", "piercing", 5, "dex", False, True, False),
        "Shortsword": ("1d6", "piercing", 5, "dex", False, True, False),
        "Scimitar": ("1d6", "slashing", 5, "dex", False, True, False),
        "Mace": ("1d6", "bludgeoning", 5, "str", False, False, False),
        "Quarterstaff": ("1d6", "bludgeoning", 5, "str", False, False, False),
        "Club": ("1d4", "bludgeoning", 5, "str", False, False, False),
        "Dagger": ("1d4", "piercing", 5, "dex", False, True, False),
        "Handaxe": ("1d6", "slashing", 5, "str", False, False, False),
        "Longbow": ("1d8", "piercing", 150, "dex", True, False, False),
        "Shortbow": ("1d6", "piercing", 80, "dex", False, False, False),
        "Light Crossbow": ("1d8", "piercing", 80, "dex", False, False, False),
        "Hand Crossbow": ("1d6", "piercing", 30, "dex", False, False, False),
        "Halberd": ("1d10", "slashing", 5, "str", True, False, True),
        "Glaive": ("1d10", "slashing", 5, "str", True, False, True),
        "Pike": ("1d10", "piercing", 5, "str", True, False, True),
        "Dart": ("1d4", "piercing", 20, "dex", False, True, False),
    }

    actions = []

    def _add_weapon(name, shield=False):
        """Add a weapon action."""
        w = WEAPONS.get(name)
        if not w:
            return
        die, dtype, rng, ab, heavy, finesse, reach = w
        mod = dex_mod if ab == "dex" else str_mod
        # Finesse: use better of STR/DEX
        if finesse:
            mod = max(str_mod, dex_mod)
        atk = mod + prof_bonus
        r = max(rng, 10 if reach else 5)
        actions.append(Action(name, f"{'Ranged' if rng > 5 else 'Melee'} weapon attack",
                              atk, die, mod, dtype, range=rng, reach=r))

    # Parse weapon choice string
    if weapon_choice:
        wc = weapon_choice
        if "Shield" in wc or "shield" in wc:
            # Extract weapon name before " + Shield" or " + shield"
            parts = wc.replace(" + Shield", "").replace(" + shield", "").replace(" +Shield", "").strip()
            if parts and parts in WEAPONS:
                _add_weapon(parts)
            elif "Two " in wc:
                name = wc.replace("Two ", "").replace("s", "").strip()
                if name in WEAPONS:
                    _add_weapon(name)
            else:
                # Fallback to class default
                weapon_choice = ""
        elif wc.startswith("Two "):
            name = wc[4:].rstrip("s").strip()
            if name in WEAPONS:
                _add_weapon(name)
        elif "(" in wc:
            # "Handaxe (x2)" style
            name = wc.split("(")[0].strip()
            if name in WEAPONS:
                _add_weapon(name)
        elif wc in WEAPONS:
            _add_weapon(wc)
        else:
            weapon_choice = ""  # Invalid, fall through to defaults

    if not weapon_choice:
        # Default weapons by class
        if char_class == "Barbarian":
            _add_weapon("Greataxe")
        elif char_class == "Fighter":
            _add_weapon("Longsword")
        elif char_class == "Paladin":
            _add_weapon("Longsword")
        elif char_class == "Rogue":
            _add_weapon("Shortsword")
            _add_weapon("Shortbow")
        elif char_class == "Ranger":
            _add_weapon("Longbow")
            _add_weapon("Shortsword")
        elif char_class == "Cleric":
            _add_weapon("Mace")
        elif char_class == "Wizard":
            _add_weapon("Quarterstaff")
        elif char_class == "Warlock":
            _add_weapon("Quarterstaff")
        elif char_class == "Sorcerer":
            _add_weapon("Dagger")
        elif char_class == "Bard":
            _add_weapon("Rapier")
        elif char_class == "Druid":
            _add_weapon("Quarterstaff")
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
        # Free edit mode: bypass point buy restrictions
        self.free_edit_mode = False
        # Variant Human: 2 chosen ASI abilities; Half-Elf: 2 chosen +1 abilities
        self.variant_asi_choices = []  # list of ability names
        self.halfelf_asi_choices = []  # list of ability names (not charisma)
        # Feat selection
        self.selected_feats = []  # list of feat name strings
        self.feat_scroll = 0
        # Spell selection
        self.selected_spells = []  # list of spell name strings
        self.selected_cantrips = []  # list of cantrip name strings
        self.spell_scroll = 0
        # Skill proficiency selection
        self.skill_proficiencies = set()  # set of skill name strings
        # Equipment choices
        self.weapon_choice = 0
        self.armor_choice = 0
        # Equipment inventory (Item objects)
        self.inventory: list = []       # List of Item objects
        self.equipment_scroll = 0
        self.equipment_category = "weapons"  # weapons, armor, shields, wondrous, consumables
        self.equipment_shop_open = False  # True when browsing items to add
        self.shop_scroll = 0
        # Multiclass support
        self.multiclass_levels: dict = {}  # {"Wizard": 3} - secondary classes with levels
        self.multiclass_adding = False     # True when choosing a class to add
        # Right panel tab system
        self.right_tab = "features"  # features, feats, spells, skills, equipment, multiclass
        # Edit existing hero
        self.editing_hero_name = None
        self.hero_browser_open = False
        self.hero_browser_scroll = 0
        self.hero_browser_search = ""
        # Persistent hero roster
        self.saved_heroes = []  # List of CreatureStats loaded from disk
        self._load_hero_roster()

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

        # Weapon dropdown
        weapon_opts = WEAPON_CHOICES.get(self.char_class, ["Default"])
        self.weapon_dropdown = Dropdown(
            col_left_x, 334 + 78, col_left_w, 34,
            ["Default"] + weapon_opts,
            selected=0, label="Weapon",
            on_change=lambda v: setattr(self, 'weapon_choice_str', v if v != "Default" else "")
        )
        self.weapon_choice_str = ""

        self.level_buttons = []
        # Level selector
        self.level_down_btn = Button(
            col_left_x, 425 + 78, 40, 34, "-",
            lambda: self._change_level(-1),
            color=COLORS["danger"], style="outline", font=fonts.body_bold
        )
        self.level_up_btn = Button(
            col_left_x + col_left_w - 40, 425 + 78, 40, 34, "+",
            lambda: self._change_level(1),
            color=COLORS["success"], style="outline", font=fonts.body_bold
        )

        # Dropdowns list for iteration
        self.dropdowns = [self.race_dropdown, self.class_dropdown, self.subclass_dropdown, self.weapon_dropdown]

        # --- Free edit toggle ---
        self.btn_free_edit = Button(
            col_left_x, 560, col_left_w, 32, "MODE: POINT BUY",
            self._toggle_free_edit, color=COLORS["panel"], font=fonts.body_bold
        )

        # --- Bottom bar buttons ---
        self.btn_save = Button(
            SCREEN_WIDTH - 510, SCREEN_HEIGHT - 68, 150, 46, "ADD TO ROSTER",
            self._on_save, color=COLORS["success"], font=fonts.body_bold
        )
        self.btn_save_disk = Button(
            SCREEN_WIDTH - 350, SCREEN_HEIGHT - 68, 150, 46, "SAVE TO DISK",
            self._on_save_disk, color=COLORS["accent"], font=fonts.body_bold
        )
        self.btn_export = Button(
            SCREEN_WIDTH - 190, SCREEN_HEIGHT - 68, 150, 46, "EXPORT JSON",
            self._on_export, color=COLORS["spell"], font=fonts.body_bold
        )
        self.btn_back = Button(
            20, SCREEN_HEIGHT - 68, 180, 46, "BACK TO MENU",
            self._on_back, color=COLORS["danger"], font=fonts.body_bold
        )
        self.btn_load = Button(
            220, SCREEN_HEIGHT - 68, 180, 46, "LOAD HEROES",
            self._on_load_roster, color=COLORS["neutral"], font=fonts.body_bold
        )
        self.btn_edit_hero = Button(
            420, SCREEN_HEIGHT - 68, 180, 46, "EDIT HERO",
            self._toggle_hero_browser, color=COLORS["warning"], font=fonts.body_bold
        )

        # Right panel tab buttons
        self.right_tab_buttons = {}
        tab_names = [("features", "Features"), ("feats", "Feats"), ("spells", "Spells"),
                     ("skills", "Skills"), ("equipment", "Equipment"), ("multiclass", "Multiclass")]
        tab_x = 1030
        tab_w = 870 // len(tab_names)
        for i, (key, label) in enumerate(tab_names):
            self.right_tab_buttons[key] = Button(
                tab_x + i * tab_w, 70, tab_w, 30, label,
                lambda k=key: self._set_right_tab(k),
                color=COLORS["accent"] if key == "features" else COLORS["panel"],
                font=fonts.small_bold
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
        # Reset selections that depend on class
        self.selected_feats = [f for f in self.selected_feats if f in FEATS_BY_NAME]
        self.selected_spells = []
        self.selected_cantrips = []
        self.skill_proficiencies = set()
        self.feat_scroll = 0
        self.spell_scroll = 0
        # Update weapon dropdown
        weapon_opts = WEAPON_CHOICES.get(value, ["Default"])
        self.weapon_dropdown.set_options(["Default"] + weapon_opts)
        self.weapon_choice_str = ""

    def _on_subclass_change(self, value):
        self.char_subclass = value if value != "(None)" else ""
        # Reset spells when subclass changes (e.g. Eldritch Knight vs Champion)
        self.selected_spells = []
        self.selected_cantrips = []
        self.spell_scroll = 0

    def _refresh_subclass_options(self):
        opts = SUBCLASS_MAP.get(self.char_class, [])
        self.subclass_dropdown.set_options(["(None)"] + opts)
        self.char_subclass = ""

    def _change_level(self, delta):
        self.char_level = max(1, min(20, self.char_level + delta))

    def _toggle_free_edit(self):
        self.free_edit_mode = not self.free_edit_mode
        if self.free_edit_mode:
            self.btn_free_edit.text = "MODE: FREE EDIT"
            self.btn_free_edit.color = COLORS["warning"]
        else:
            self.btn_free_edit.text = "MODE: POINT BUY"
            self.btn_free_edit.color = COLORS["panel"]

    def _change_ability(self, ability, delta):
        current = self.ability_scores[ability]
        new_val = current + delta

        if self.free_edit_mode:
            # Free edit: allow 1-30
            if new_val < 1 or new_val > 30:
                return
            self.ability_scores[ability] = new_val
            return

        # Point buy mode: standard restrictions
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

    def _load_hero_roster(self):
        """Load saved heroes from disk."""
        roster_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        os.makedirs(roster_dir, exist_ok=True)
        self.saved_heroes = []
        for f in sorted(os.listdir(roster_dir)):
            if f.endswith(".json"):
                try:
                    heroes = import_heroes_from_file(os.path.join(roster_dir, f))
                    self.saved_heroes.extend(heroes)
                except Exception:
                    pass

    def _save_hero_to_disk(self, hero):
        """Save a single hero to the heroes/ directory."""
        roster_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        os.makedirs(roster_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in hero.name).strip()
        if not safe_name:
            safe_name = "hero"
        filepath = os.path.join(roster_dir, f"{safe_name}.json")
        export_heroes_to_file([hero], filepath)

    def _on_save(self):
        hero = self._build_creature_stats()
        hero_list.append(hero)
        self.status_message = f"'{hero.name}' added to hero roster!"
        self.status_timer = 180
        self.status_color = COLORS["success"]

    def _on_save_disk(self):
        hero = self._build_creature_stats()
        try:
            self._save_hero_to_disk(hero)
            hero_list.append(hero)
            self.saved_heroes.append(hero)
            self.status_message = f"'{hero.name}' saved to disk!"
            self.status_timer = 180
            self.status_color = COLORS["success"]
        except Exception as e:
            self.status_message = f"Save failed: {e}"
            self.status_timer = 240
            self.status_color = COLORS["danger"]

    def _on_load_roster(self):
        """Reload heroes from disk into hero_list."""
        self._load_hero_roster()
        count = 0
        for h in self.saved_heroes:
            if not any(existing.name == h.name for existing in hero_list):
                hero_list.append(h)
                count += 1
        self.status_message = f"Loaded {count} heroes from disk"
        self.status_timer = 180
        self.status_color = COLORS["accent"]

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
        if hasattr(self.manager, 'change_state'):
            self.manager.change_state("MENU")

    def _set_right_tab(self, tab):
        self.right_tab = tab
        for key, btn in self.right_tab_buttons.items():
            btn.color = COLORS["accent"] if key == tab else COLORS["panel"]

    # ---- Feat Selection ----

    def _get_max_feats(self):
        """Number of ASI/Feat slots available at current level."""
        levels = ASI_LEVELS.get(self.char_class, [4, 8, 12, 16, 19])
        return sum(1 for lv in levels if lv <= self.char_level)

    def _get_available_feats(self):
        """Get feats available based on character prerequisites."""
        abilities = {ab: self._get_effective_score(ab) for ab in ABILITY_NAMES}
        return get_feats_available(
            character_class=self.char_class,
            race=self.char_race,
            level=self.char_level,
            abilities=abilities,
        )

    def _toggle_feat(self, feat_name):
        """Toggle a feat on/off."""
        if feat_name in self.selected_feats:
            self.selected_feats.remove(feat_name)
        elif len(self.selected_feats) < self._get_max_feats():
            self.selected_feats.append(feat_name)

    # ---- Spell Selection ----

    def _get_class_cantrips(self):
        """Get available cantrips for current class."""
        # Check for third-caster subclasses
        if self.char_class == "Fighter" and self.char_subclass != "Eldritch Knight":
            return []
        if self.char_class == "Rogue" and self.char_subclass != "Arcane Trickster":
            return []
        spell_list = CLASS_SPELL_LISTS.get(self.char_class, {})
        return spell_list.get("cantrips", [])

    def _get_class_spells(self):
        """Get available spells for current class, filtered by max spell level."""
        # Check for third-caster subclasses
        lookup_class = self.char_class
        if self.char_class == "Fighter" and self.char_subclass != "Eldritch Knight":
            return []
        if self.char_class == "Rogue" and self.char_subclass != "Arcane Trickster":
            return []

        spell_list = CLASS_SPELL_LISTS.get(lookup_class, {})
        all_spells = spell_list.get("spells", [])
        # Filter by max castable spell level
        slots = calc_spell_slots(self.char_class, self.char_level, self.char_subclass)
        if not slots:
            return []
        max_level = max(i + 1 for i, name in enumerate(SLOT_LEVEL_NAMES) if name in slots) if slots else 0
        result = []
        for sname in all_spells:
            spell = SPELL_DATABASE.get(sname)
            if spell and spell.level <= max_level:
                result.append(sname)
        return result

    def _get_max_cantrips(self):
        """Max cantrips known for current class/level."""
        table = CANTRIPS_KNOWN.get(self.char_class, {})
        max_known = 0
        for lv, count in table.items():
            if self.char_level >= lv:
                max_known = count
        return max_known

    def _get_max_spells(self):
        """Max spells known for current class/level."""
        # Prepared casters (Cleric, Druid, Paladin) can prepare ability_mod + level spells
        if self.char_class in ("Cleric", "Druid"):
            ability_key = SPELLCASTING_ABILITY.get(self.char_class, "").lower()
            if ability_key:
                mod = calc_modifier(self._get_effective_score(ability_key))
                return max(1, mod + self.char_level)
            return self.char_level
        if self.char_class == "Paladin":
            ability_key = "charisma"
            mod = calc_modifier(self._get_effective_score(ability_key))
            return max(1, mod + self.char_level // 2)
        if self.char_class == "Wizard":
            # Wizard spellbook: 6 + 2 per level above 1
            return 6 + 2 * (self.char_level - 1)
        # Spells known casters
        table = SPELLS_KNOWN_TABLE.get(self.char_class, {})
        known = 0
        for lv, count in table.items():
            if self.char_level >= lv:
                known = count
        return known

    def _toggle_cantrip(self, name):
        if name in self.selected_cantrips:
            self.selected_cantrips.remove(name)
        elif len(self.selected_cantrips) < self._get_max_cantrips():
            self.selected_cantrips.append(name)

    def _toggle_spell(self, name):
        if name in self.selected_spells:
            self.selected_spells.remove(name)
        elif len(self.selected_spells) < self._get_max_spells():
            self.selected_spells.append(name)

    # ---- Skill Selection ----

    def _get_skill_choices(self):
        """Get (count, options) for skill proficiency choices."""
        return CLASS_SKILL_CHOICES.get(self.char_class, (2, [s[0] for s in ALL_SKILLS]))

    def _toggle_skill(self, skill_name):
        max_skills, _ = self._get_skill_choices()
        if skill_name in self.skill_proficiencies:
            self.skill_proficiencies.discard(skill_name)
        elif len(self.skill_proficiencies) < max_skills:
            self.skill_proficiencies.add(skill_name)

    # ---- Edit Existing Hero ----

    def _toggle_hero_browser(self):
        self.hero_browser_open = not self.hero_browser_open
        self.hero_browser_scroll = 0
        self.hero_browser_search = ""

    def _load_hero_into_editor(self, hero):
        """Populate editor fields from an existing hero's CreatureStats."""
        self.editing_hero_name = hero.name
        self.name_input.text = hero.name

        # Set race
        if hero.race in RACE_LIST:
            self.char_race = hero.race
            idx = RACE_LIST.index(hero.race)
            self.race_dropdown.selected = idx

        # Set class
        if hero.character_class in CLASS_LIST:
            self.char_class = hero.character_class
            idx = CLASS_LIST.index(hero.character_class)
            self.class_dropdown.selected = idx
            self._refresh_subclass_options()

        # Set subclass
        if hero.subclass:
            opts = ["(None)"] + SUBCLASS_MAP.get(self.char_class, [])
            if hero.subclass in opts:
                self.char_subclass = hero.subclass
                self.subclass_dropdown.selected = opts.index(hero.subclass)
            else:
                self.char_subclass = hero.subclass

        # Set level
        self.char_level = max(1, min(20, hero.character_level))

        # Set ability scores (subtract racial bonuses to get base scores)
        racial_bonuses = get_racial_asi(hero.race)
        for ab in ABILITY_NAMES:
            total = getattr(hero.abilities, ab, 10)
            bonus = racial_bonuses.get(ab, 0)
            self.ability_scores[ab] = max(1, total - bonus)

        # Enable free edit since loaded heroes may have non-point-buy scores
        self.free_edit_mode = True
        self.btn_free_edit.text = "MODE: FREE EDIT"
        self.btn_free_edit.color = COLORS["warning"]

        # Load feat names from hero features that match known feats
        self.selected_feats = []
        for feat in hero.features:
            if feat.name in FEATS_BY_NAME:
                self.selected_feats.append(feat.name)

        # Load spells
        self.selected_spells = [s.name for s in hero.spells_known]
        self.selected_cantrips = [s.name for s in hero.cantrips]

        # Load skills
        self.skill_proficiencies = set(hero.skills.keys()) if hero.skills else set()

        # Load equipment inventory
        self.inventory = copy.deepcopy(hero.items) if hero.items else []

        # Load multiclass
        self.multiclass_levels = dict(hero.multiclass) if hero.multiclass else {}

        self.hero_browser_open = False
        self.status_message = f"Editing '{hero.name}'"
        self.status_timer = 120
        self.status_color = COLORS["warning"]

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

        # --- Apply selected feats ---
        feat_features = []
        for feat_name in self.selected_feats:
            feat_obj = FEATS_BY_NAME.get(feat_name)
            if not feat_obj:
                continue
            # Apply feat ASI bonuses
            if feat_obj.ability_increase:
                ai = feat_obj.ability_increase
                # Parse "STR+1", "CON+1", "CHA+1", etc. (take first option if "or")
                parts = ai.split(" or ")
                part = parts[0].strip()
                if "+" in part:
                    ab_abbr, val = part.split("+")
                    ab_map = {"STR": "strength", "DEX": "dexterity", "CON": "constitution",
                              "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma"}
                    ab_key = ab_map.get(ab_abbr.strip().upper())
                    if ab_key:
                        try:
                            bonus = int(val)
                            current = getattr(abilities, ab_key)
                            setattr(abilities, ab_key, min(20, current + bonus))
                        except ValueError:
                            pass
            # Convert feat to Feature for combat engine
            feat_feature = Feature(
                name=feat_obj.name,
                description=feat_obj.combat_effect or feat_obj.description[:100],
                feature_type="feat",
                mechanic=feat_obj.mechanic,
                mechanic_value=feat_obj.mechanic_value,
            )
            feat_features.append(feat_feature)
        features = features + feat_features

        # Recalc HP after feat bonuses (Tough feat: +2 HP per level)
        if "Tough" in self.selected_feats:
            hp += 2 * level
        # Recalc con_mod after feats (Durable, etc. may have changed CON)
        con_mod = calc_modifier(abilities.constitution)
        hp = calc_hp(char_class, level, con_mod)
        if race == "Hill Dwarf":
            hp += level
        if char_class == "Sorcerer" and subclass == "Draconic Bloodline":
            hp += level
        if "Tough" in self.selected_feats:
            hp += 2 * level

        # Recalc AC after feat changes
        ac = calc_ac(char_class, abilities, subclass)
        # Dual Wielder feat: +1 AC
        if "Dual Wielder" in self.selected_feats:
            ac += 1

        # Mobile feat: +10 speed
        if "Mobile" in self.selected_feats:
            speed += 10

        # Actions
        actions = build_default_actions(char_class, abilities, prof, level, self.weapon_choice_str)

        # --- Generate feat-based combat actions ---
        str_mod = calc_modifier(abilities.strength)
        dex_mod = calc_modifier(abilities.dexterity)
        if "Great Weapon Master" in self.selected_feats:
            atk = str_mod + prof - 5
            actions.append(Action("GWM Power Attack", "Heavy weapon: -5 attack, +10 damage",
                                  atk, "1d12", str_mod + 10, "slashing", range=5,
                                  action_type="action"))
        if "Sharpshooter" in self.selected_feats:
            atk = dex_mod + prof - 5
            actions.append(Action("Sharpshooter Shot", "Ranged: -5 attack, +10 damage",
                                  atk, "1d8", dex_mod + 10, "piercing", range=150,
                                  action_type="action"))
        if "Polearm Master" in self.selected_feats:
            atk = str_mod + prof
            actions.append(Action("Polearm Butt", "Bonus action butt end strike",
                                  atk, "1d4", str_mod, "bludgeoning", range=5,
                                  action_type="bonus"))
        if "Shield Master" in self.selected_feats:
            actions.append(Action("Shield Bash", "Bonus action shove after Attack",
                                  str_mod + prof, "0", 0, "bludgeoning", range=5,
                                  action_type="bonus"))
        if "Crossbow Expert" in self.selected_feats:
            atk = dex_mod + prof
            actions.append(Action("Hand Crossbow (Bonus)", "Bonus action crossbow attack",
                                  atk, "1d6", dex_mod, "piercing", range=30,
                                  action_type="bonus"))
        if "Martial Adept" in self.selected_feats:
            feat_features_list = [f for f in features if f.name == "Martial Adept"]
            if not feat_features_list:
                features.append(Feature("Superiority Die", "1 superiority die (d6)",
                                        mechanic="superiority_dice", mechanic_value="1d6",
                                        uses_per_day=1, short_rest_recharge=True))
        if "Healer" in self.selected_feats:
            actions.append(Action("Healer's Kit", "Heal 1d6+4+max HD (1/creature/rest)",
                                  0, "1d6", 4, "healing", range=5, action_type="action"))

        # --- Generate racial trait combat actions ---
        for trait in racial_traits:
            if trait.mechanic == "breath_weapon" and trait.damage_dice:
                save_dc_val = 8 + prof + calc_modifier(abilities.constitution)
                actions.append(Action(
                    "Breath Weapon", f"{trait.damage_type} breath ({trait.damage_dice})",
                    0, trait.damage_dice, 0, trait.damage_type or "fire", range=15,
                    aoe_radius=15, aoe_shape="cone",
                    condition_save=trait.save_ability or "Dexterity",
                    condition_dc=save_dc_val
                ))
            elif trait.mechanic == "healing_hands":
                actions.append(Action(
                    "Healing Hands", f"Heal {level} HP (1/long rest)",
                    0, f"{level}", 0, "healing", range=5, action_type="action"
                ))
            elif trait.mechanic == "hellish_rebuke":
                actions.append(Action(
                    "Hellish Rebuke (Racial)", "2d10 fire damage (reaction, 1/day)",
                    0, "2d10", 0, "fire", range=60, action_type="reaction"
                ))
            elif trait.mechanic == "relentless_endurance":
                features.append(Feature("Relentless Endurance", "Drop to 1 HP instead of 0 (1/long rest)",
                                        mechanic="relentless_endurance", uses_per_day=1))

        # --- Assign selected spells and cantrips ---
        spells_known = []
        for sname in self.selected_spells:
            spell = SPELL_DATABASE.get(sname)
            if spell:
                spells_known.append(get_spell(sname,
                    save_dc_fixed=spell_save_dc if not spell.save_dc_fixed else spell.save_dc_fixed,
                    attack_bonus_fixed=spell_atk if not spell.attack_bonus_fixed else spell.attack_bonus_fixed))
        cantrips_list = []
        for sname in self.selected_cantrips:
            spell = SPELL_DATABASE.get(sname)
            if spell:
                cantrips_list.append(get_spell(sname,
                    save_dc_fixed=spell_save_dc if not spell.save_dc_fixed else spell.save_dc_fixed,
                    attack_bonus_fixed=spell_atk if not spell.attack_bonus_fixed else spell.attack_bonus_fixed))

        # --- Apply skill proficiencies ---
        skills = {}
        for skill_name, ability_name in ALL_SKILLS:
            if skill_name in self.skill_proficiencies:
                mod = calc_modifier(self._get_effective_score(ability_name))
                skills[skill_name] = mod + prof

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
        total_level = level + sum(self.multiclass_levels.values())
        cr = max(0.5, total_level / 2.0)

        # Build unarmored flag
        is_unarmored = char_class in ("Barbarian", "Monk")

        size = get_race_size(race)

        # Multiclass: merge features from secondary classes
        mc_features = []
        mc_save_profs = set(SAVING_THROW_PROF.get(char_class, ()))
        for mc_class, mc_level in self.multiclass_levels.items():
            mc_feats = get_class_features(mc_class, mc_level, "")
            mc_features.extend(mc_feats)
            # Multiclass resource pools
            if mc_class == "Monk" and mc_level >= 2:
                ki_points += mc_level
            if mc_class == "Sorcerer" and mc_level >= 2:
                sorcery_points += mc_level
            if mc_class == "Paladin":
                lay_on_hands_pool += 5 * mc_level
            if mc_class == "Barbarian":
                rage_count += BARBARIAN_RAGE_COUNT.get(mc_level, 0)
            if mc_class == "Bard" and not bardic_dice:
                bardic_dice = BARD_INSPIRATION_DIE.get(mc_level, "1d6")
                cha_mod_mc = calc_modifier(abilities.charisma)
                bardic_count = max(1, cha_mod_mc)
        features = features + mc_features

        # Multiclass spell slots (override if multiclassed)
        if self.multiclass_levels:
            mc_slots = self._get_multiclass_spell_slots()
            if mc_slots:
                spell_slots = mc_slots

        # Equipment items (deep copy)
        import copy as _copy
        inventory_items = _copy.deepcopy(self.inventory)

        # Calculate AC from equipment if equipped armor exists
        equipped_armor = None
        equipped_shield = None
        for item in inventory_items:
            if item.equipped and item.item_type == "armor" and item.base_ac > 0:
                equipped_armor = item
            if item.equipped and item.armor_category == "shield":
                equipped_shield = item

        if equipped_armor:
            dex_mod = calc_modifier(abilities.dexterity)
            ac = equipped_armor.base_ac + equipped_armor.ac_bonus
            if equipped_armor.max_dex_bonus == -1:
                ac += dex_mod
            elif equipped_armor.max_dex_bonus > 0:
                ac += min(dex_mod, equipped_armor.max_dex_bonus)
            if equipped_shield:
                ac += equipped_shield.ac_bonus
            # Non-armor AC bonuses (rings, cloaks)
            for item in inventory_items:
                if item.equipped and item.item_type not in ("armor", "shield"):
                    if item.requires_attunement and not item.attuned:
                        continue
                    ac += item.ac_bonus
            is_unarmored = False

        # Build weapon Actions from equipped weapons
        for item in inventory_items:
            if item.equipped and item.item_type == "weapon" and item.weapon_damage_dice:
                # Determine attack stat
                atk_mod = calc_modifier(abilities.strength)
                if "finesse" in item.weapon_properties:
                    dex_mod = calc_modifier(abilities.dexterity)
                    atk_mod = max(atk_mod, dex_mod)
                if "ranged" in item.weapon_category:
                    atk_mod = calc_modifier(abilities.dexterity)
                atk_bonus = atk_mod + prof + item.weapon_bonus
                dmg_bonus = atk_mod + item.weapon_bonus
                rng = item.weapon_range
                reach = item.weapon_range if item.weapon_range <= 10 else 5
                if "reach" in item.weapon_properties:
                    reach = 10
                    rng = 10
                if item.weapon_long_range > 0:
                    rng = item.weapon_range  # Use short range as default

                action = Action(
                    name=item.name,
                    description=item.description or f"{item.weapon_damage_dice}+{dmg_bonus} {item.weapon_damage_type}",
                    attack_bonus=atk_bonus,
                    damage_dice=item.weapon_damage_dice,
                    damage_bonus=dmg_bonus,
                    damage_type=item.weapon_damage_type,
                    range=rng,
                    reach=reach,
                    action_type="action",
                    properties=item.weapon_properties,
                    long_range=item.weapon_long_range,
                )
                actions.append(action)

                # Extra damage from magical weapons (Flame Tongue etc.)
                if item.extra_damage_dice:
                    # The AI handles extra damage through the weapon bonus system
                    # We encode it in the action description for visibility
                    action.description += f" +{item.extra_damage_dice} {item.extra_damage_type}"

        hero = CreatureStats(
            name=name,
            size=size,
            creature_type="Humanoid",
            alignment="Neutral",
            armor_class=ac,
            armor_type="",
            hit_points=hp,
            hit_dice=hit_dice_str,
            speed=speed,
            abilities=abilities,
            saving_throws=saving_throws,
            skills=skills,
            proficiency_bonus=prof,
            challenge_rating=cr,
            character_class=char_class,
            character_level=total_level,
            race=race,
            subclass=subclass,
            actions=actions,
            features=features,
            racial_traits=racial_traits,
            spellcasting_ability=spell_ability,
            spell_save_dc=spell_save_dc,
            spell_attack_bonus=spell_atk,
            spell_slots=spell_slots,
            spells_known=spells_known,
            cantrips=cantrips_list,
            ki_points=ki_points,
            sorcery_points=sorcery_points,
            lay_on_hands_pool=lay_on_hands_pool,
            rage_count=rage_count,
            bardic_inspiration_dice=bardic_dice,
            bardic_inspiration_count=bardic_count,
            base_ac_unarmored=is_unarmored,
            items=inventory_items,
            multiclass=dict(self.multiclass_levels),
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
            self.btn_save_disk.handle_event(event)
            self.btn_export.handle_event(event)
            self.btn_back.handle_event(event)
            self.btn_load.handle_event(event)
            self.btn_free_edit.handle_event(event)
            self.btn_edit_hero.handle_event(event)

            # Right panel tab buttons
            for btn in self.right_tab_buttons.values():
                btn.handle_event(event)

            # Right panel content clicks (feats, spells, skills, equipment, multiclass)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mouse_pos[0] > 1030:
                    if self.right_tab == "feats":
                        self._handle_feat_clicks(mouse_pos)
                    elif self.right_tab == "spells":
                        self._handle_spell_clicks(mouse_pos)
                    elif self.right_tab == "skills":
                        self._handle_skill_clicks(mouse_pos)
                    elif self.right_tab == "equipment":
                        self._handle_equipment_clicks(mouse_pos)
                    elif self.right_tab == "multiclass":
                        self._handle_multiclass_clicks(mouse_pos)

            # Hero browser clicks
            if self.hero_browser_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_hero_browser_click(mouse_pos)

            # Scroll for right panel
            if event.type == pygame.MOUSEWHEEL:
                if mouse_pos[0] > 1030:
                    if self.right_tab == "features":
                        if mouse_pos[1] < 550:
                            self.feature_scroll = max(0, self.feature_scroll - event.y * 20)
                        else:
                            self.trait_scroll = max(0, self.trait_scroll - event.y * 20)
                    elif self.right_tab == "feats":
                        self.feat_scroll = max(0, self.feat_scroll - event.y * 20)
                    elif self.right_tab == "spells":
                        self.spell_scroll = max(0, self.spell_scroll - event.y * 20)
                    elif self.right_tab == "equipment":
                        if self.equipment_shop_open:
                            self.shop_scroll = max(0, self.shop_scroll - event.y * 20)
                        else:
                            self.equipment_scroll = max(0, self.equipment_scroll - event.y * 20)
                # Hero browser scroll
                if self.hero_browser_open and 400 <= mouse_pos[0] <= 1520:
                    self.hero_browser_scroll = max(0, self.hero_browser_scroll - event.y * 25)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if mouse_pos[0] > 1030:
                        if self.right_tab == "features":
                            if mouse_pos[1] < 550:
                                self.feature_scroll = max(0, self.feature_scroll - 20)
                            else:
                                self.trait_scroll = max(0, self.trait_scroll - 20)
                        elif self.right_tab == "feats":
                            self.feat_scroll = max(0, self.feat_scroll - 20)
                        elif self.right_tab == "spells":
                            self.spell_scroll = max(0, self.spell_scroll - 20)
                elif event.button == 5:
                    if mouse_pos[0] > 1030:
                        if self.right_tab == "features":
                            if mouse_pos[1] < 550:
                                self.feature_scroll += 20
                            else:
                                self.trait_scroll += 20
                        elif self.right_tab == "feats":
                            self.feat_scroll += 20
                        elif self.right_tab == "spells":
                            self.spell_scroll += 20
                        elif self.right_tab == "equipment":
                            if self.equipment_shop_open:
                                self.shop_scroll += 20
                            else:
                                self.equipment_scroll += 20

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

    def _handle_feat_clicks(self, mouse_pos):
        """Handle clicks on feat list items."""
        right_x = 1030
        right_w = 870
        content_y = 158  # Matches _draw_feats_tab: info_y(133) + 25
        available = self._get_available_feats()
        row_h = 36
        for i, feat in enumerate(available):
            fy = content_y + i * row_h - self.feat_scroll
            if fy < 133 or fy > SCREEN_HEIGHT - 100:
                continue
            item_rect = pygame.Rect(right_x + 5, fy, right_w - 10, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._toggle_feat(feat.name)
                break

    def _handle_spell_clicks(self, mouse_pos):
        """Handle clicks on spell/cantrip list items."""
        right_x = 1030
        right_w = 870
        row_h = 32
        # Match the draw method coordinates exactly
        cantrips = self._get_class_cantrips()
        cy = 140 - self.spell_scroll  # Matches _draw_spells_tab header start
        cy += 20  # Skip "CANTRIPS" header
        for i, name in enumerate(cantrips):
            fy = cy + i * row_h
            if fy < 133 or fy > SCREEN_HEIGHT - 100:
                continue
            item_rect = pygame.Rect(right_x + 5, fy, right_w - 10, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._toggle_cantrip(name)
                return
        # Spells section
        spells = self._get_class_spells()
        sy = cy + len(cantrips) * row_h + 15 + 20  # +15 gap, +20 header
        for i, name in enumerate(spells):
            fy = sy + i * row_h
            if fy < 133 or fy > SCREEN_HEIGHT - 100:
                continue
            item_rect = pygame.Rect(right_x + 5, fy, right_w - 10, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._toggle_spell(name)
                return

    def _handle_skill_clicks(self, mouse_pos):
        """Handle clicks on skill selection."""
        right_x = 1030
        right_w = 870
        _, available = self._get_skill_choices()
        row_h = 32
        cy = 155  # Matches _draw_skills_tab start
        for i, (skill_name, ability) in enumerate(ALL_SKILLS):
            fy = cy + i * row_h
            if fy < 133 or fy > SCREEN_HEIGHT - 100:
                continue
            item_rect = pygame.Rect(right_x + 5, fy, right_w - 10, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._toggle_skill(skill_name)
                break

    def _handle_hero_browser_click(self, mouse_pos):
        """Handle clicks in the hero browser overlay."""
        bx, by, bw, bh = 400, 80, 1120, SCREEN_HEIGHT - 160
        # Close button area
        close_rect = pygame.Rect(bx + bw - 40, by + 8, 30, 30)
        if close_rect.collidepoint(mouse_pos):
            self.hero_browser_open = False
            return

        # Hero list items
        all_heroes = list(hero_list) + [h for h in self.saved_heroes if not any(e.name == h.name for e in hero_list)]
        if self.hero_browser_search:
            search = self.hero_browser_search.lower()
            all_heroes = [h for h in all_heroes if search in h.name.lower() or
                          search in h.character_class.lower() or search in h.race.lower()]
        row_h = 40
        hdr_y = by + 45
        for i, hero in enumerate(all_heroes):
            fy = hdr_y + 28 + i * row_h - self.hero_browser_scroll
            if fy < hdr_y + 25 or fy > by + bh - 20:
                continue
            # Delete button
            del_rect = pygame.Rect(bx + bw - 100, fy + 4, 60, 28)
            if del_rect.collidepoint(mouse_pos):
                self._delete_hero(hero)
                return
            # Click to edit
            item_rect = pygame.Rect(bx + 10, fy, bw - 120, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._load_hero_into_editor(hero)
                return

    def _delete_hero(self, hero):
        """Delete a hero from roster and disk."""
        # Remove from hero_list
        hero_list[:] = [h for h in hero_list if h.name != hero.name]
        # Remove from saved_heroes
        self.saved_heroes[:] = [h for h in self.saved_heroes if h.name != hero.name]
        # Remove from disk
        roster_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in hero.name).strip()
        filepath = os.path.join(roster_dir, f"{safe_name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        self.status_message = f"Deleted '{hero.name}'"
        self.status_timer = 120
        self.status_color = COLORS["danger"]

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

        # Draw hero browser overlay (on top of everything else)
        if self.hero_browser_open:
            self._draw_hero_browser(screen, mouse_pos)

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
        """Draw left column: name, race, class, subclass, weapon, level."""
        col_x = 20
        col_w = 390
        panel = Panel(col_x, 70, col_w, 490, title="CHARACTER INFO")
        panel.draw(screen)

        # Name input
        self.name_input.draw(screen, mouse_pos)

        # Race dropdown
        self.race_dropdown.draw(screen, mouse_pos)

        # Class dropdown
        self.class_dropdown.draw(screen, mouse_pos)

        # Subclass dropdown
        self.subclass_dropdown.draw(screen, mouse_pos)

        # Weapon dropdown
        self.weapon_dropdown.draw(screen, mouse_pos)

        # Level selector
        lbl = fonts.small_bold.render("Level", True, COLORS["text_dim"])
        screen.blit(lbl, (30, 485))

        self.level_down_btn.draw(screen, mouse_pos)
        self.level_up_btn.draw(screen, mouse_pos)

        # Level display
        level_txt = fonts.header_font.render(str(self.char_level), True, COLORS["text_bright"])
        level_cx = 30 + 370 // 2
        screen.blit(level_txt, (level_cx - level_txt.get_width() // 2, 506))

        # Proficiency badge
        prof = calc_proficiency(self.char_level)
        prof_txt = f"Proficiency: +{prof}"
        Badge.draw(screen, 30, 548, prof_txt, COLORS["accent"])

        # Free edit mode button
        self.btn_free_edit.draw(screen, mouse_pos)

        # --- Summary Stats Panel ---
        summary_panel = Panel(col_x, 600, col_w, 230, title="QUICK STATS")
        summary_panel.draw(screen)

        sy = 633
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
            if row_y > 810:
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

        title_mode = "FREE EDIT" if self.free_edit_mode else "POINT BUY"
        panel = Panel(center_x, 70, center_w, 480, title=f"ABILITY SCORES ({title_mode})")
        panel.draw(screen)

        if self.free_edit_mode:
            # Free edit mode: show warning
            warn_txt = "FREE EDIT: No restrictions (1-30)"
            warn_surf = fonts.body_bold.render(warn_txt, True, COLORS["warning"])
            screen.blit(warn_surf, (center_x + center_w // 2 - warn_surf.get_width() // 2, 100))

            # Orange bar
            bar_x = center_x + 20
            bar_y = 122
            bar_w = center_w - 40
            bar_h = 6
            pygame.draw.rect(screen, COLORS["warning"], (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        else:
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
        points_used = self._calc_points_used() if not self.free_edit_mode else 0

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
            can_decrease = base_score > (1 if self.free_edit_mode else POINT_BUY_MIN)
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
            if self.free_edit_mode:
                can_increase = base_score < 30
            else:
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
        """Draw right column: tabbed panel with features/feats/spells/skills."""
        right_x = 1030
        right_w = 870

        # Draw tab buttons
        for key, btn in self.right_tab_buttons.items():
            btn.draw(screen, mouse_pos)

        # Draw active tab indicator
        tab_keys = ["features", "feats", "spells", "skills", "equipment", "multiclass"]
        active_idx = tab_keys.index(self.right_tab) if self.right_tab in tab_keys else 0
        tab_w = right_w // len(tab_keys)
        indicator_rect = pygame.Rect(right_x + active_idx * tab_w, 100, tab_w, 3)
        pygame.draw.rect(screen, COLORS["accent"], indicator_rect)

        # Draw tab content
        if self.right_tab == "features":
            self._draw_features_tab(screen, mouse_pos)
        elif self.right_tab == "feats":
            self._draw_feats_tab(screen, mouse_pos)
        elif self.right_tab == "spells":
            self._draw_spells_tab(screen, mouse_pos)
        elif self.right_tab == "skills":
            self._draw_skills_tab(screen, mouse_pos)
        elif self.right_tab == "equipment":
            self._draw_equipment_tab(screen, mouse_pos)
        elif self.right_tab == "multiclass":
            self._draw_multiclass_tab(screen, mouse_pos)

    def _draw_features_tab(self, screen, mouse_pos):
        """Draw class features and racial traits."""
        right_x = 1030
        right_w = 870

        # --- Class Features ---
        feat_panel_h = 440
        panel = Panel(right_x, 103, right_w, feat_panel_h, title="CLASS FEATURES")
        panel.draw(screen)

        features = get_class_features(self.char_class, self.char_level, self.char_subclass)

        clip_rect = pygame.Rect(right_x + 5, 133, right_w - 10, feat_panel_h - 40)
        screen.set_clip(clip_rect)

        fy = 138 - self.feature_scroll
        for feat in features:
            if fy > 103 + feat_panel_h:
                break
            if fy + 40 >= 133:
                name_surf = fonts.body_bold.render(feat.name, True, COLORS["text_bright"])
                screen.blit(name_surf, (right_x + 15, fy))
                if feat.mechanic:
                    badge_x = right_x + 20 + name_surf.get_width() + 5
                    if badge_x + 80 < right_x + right_w:
                        Badge.draw(screen, badge_x, fy + 2, feat.mechanic,
                                   COLORS.get(self.char_class.lower(), COLORS["accent_dim"]),
                                   font=fonts.tiny_font)
                if feat.description:
                    desc_text = feat.description[:97] + "..." if len(feat.description) > 100 else feat.description
                    desc_surf = fonts.small_font.render(desc_text, True, COLORS["text_dim"])
                    desc_clip = pygame.Rect(right_x + 15, fy + 20, right_w - 30, 16)
                    screen.set_clip(desc_clip.clip(clip_rect))
                    screen.blit(desc_surf, (right_x + 15, fy + 20))
                    screen.set_clip(clip_rect)
                if feat.uses_per_day > 0:
                    uses_txt = f"{feat.uses_per_day}/rest" if feat.short_rest_recharge else f"{feat.uses_per_day}/day"
                    uses_s = fonts.tiny_font.render(uses_txt, True, COLORS["warning"])
                    screen.blit(uses_s, (right_x + right_w - 70, fy + 3))
            fy += 42
        screen.set_clip(None)

        # Scrollbar
        total_h = len(features) * 42
        if total_h > feat_panel_h - 40:
            max_scroll = max(1, total_h - feat_panel_h + 40)
            sb_total_h = feat_panel_h - 40
            sb_h = max(20, int(sb_total_h * sb_total_h / total_h))
            sb_y = 133 + int((sb_total_h - sb_h) * min(1, self.feature_scroll / max_scroll))
            pygame.draw.rect(screen, COLORS["scrollbar_thumb"],
                             (right_x + right_w - 8, sb_y, 5, sb_h), border_radius=2)

        # --- Racial Traits ---
        trait_y = 560
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
                tn = fonts.body_bold.render(trait.name, True, COLORS["text_bright"])
                screen.blit(tn, (right_x + 15, ty))
                if trait.description:
                    desc = trait.description[:87] + "..." if len(trait.description) > 90 else trait.description
                    td = fonts.small_font.render(desc, True, COLORS["text_dim"])
                    desc_clip2 = pygame.Rect(right_x + 15, ty + 20, right_w - 30, 16)
                    screen.set_clip(desc_clip2.clip(clip_rect2))
                    screen.blit(td, (right_x + 15, ty + 20))
                    screen.set_clip(clip_rect2)
                if trait.mechanic:
                    Badge.draw(screen, right_x + 20 + tn.get_width() + 5, ty + 2,
                               trait.mechanic, COLORS["accent_dim"], font=fonts.tiny_font)
            ty += 40
        screen.set_clip(None)

    def _draw_feats_tab(self, screen, mouse_pos):
        """Draw feat selection tab."""
        right_x = 1030
        right_w = 870

        max_feats = self._get_max_feats()
        selected_count = len(self.selected_feats)
        panel = Panel(right_x, 103, right_w, SCREEN_HEIGHT - 193,
                      title=f"FEAT SELECTION ({selected_count}/{max_feats} slots)")
        panel.draw(screen)

        # Info bar
        info_y = 133
        if max_feats == 0:
            no_feat_txt = "No ASI/Feat slots available at this level (first at level 4)"
            ns = fonts.body_font.render(no_feat_txt, True, COLORS["text_muted"])
            screen.blit(ns, (right_x + 15, info_y + 10))
            return

        slots_txt = f"ASI/Feat slots: {selected_count}/{max_feats}  |  Level required: {ASI_LEVELS.get(self.char_class, [4])[0]}"
        slots_col = COLORS["success"] if selected_count < max_feats else COLORS["warning"]
        ss = fonts.small_bold.render(slots_txt, True, slots_col)
        screen.blit(ss, (right_x + 15, info_y))

        # Available feats list
        available = self._get_available_feats()
        row_h = 36
        content_y = info_y + 25
        clip_rect = pygame.Rect(right_x + 5, content_y, right_w - 10, SCREEN_HEIGHT - content_y - 100)
        screen.set_clip(clip_rect)

        for i, feat in enumerate(available):
            fy = content_y + i * row_h - self.feat_scroll
            if fy > SCREEN_HEIGHT - 100:
                break
            if fy + row_h < content_y:
                continue

            is_selected = feat.name in self.selected_feats
            is_hover = pygame.Rect(right_x + 5, fy, right_w - 10, row_h - 2).collidepoint(mouse_pos)

            # Row background
            if is_selected:
                pygame.draw.rect(screen, COLORS["success_dim"],
                                 (right_x + 5, fy, right_w - 10, row_h - 2), border_radius=4)
                pygame.draw.rect(screen, COLORS["success"],
                                 (right_x + 5, fy, right_w - 10, row_h - 2), 1, border_radius=4)
            elif is_hover:
                pygame.draw.rect(screen, COLORS["hover"],
                                 (right_x + 5, fy, right_w - 10, row_h - 2), border_radius=4)

            # Checkbox
            cb_rect = pygame.Rect(right_x + 12, fy + 8, 18, 18)
            pygame.draw.rect(screen, COLORS["border"], cb_rect, 1, border_radius=3)
            if is_selected:
                pygame.draw.rect(screen, COLORS["success"], cb_rect.inflate(-4, -4), border_radius=2)

            # Feat name
            name_col = COLORS["text_bright"] if is_selected else COLORS["text_main"]
            ns = fonts.body_bold.render(feat.name, True, name_col)
            screen.blit(ns, (right_x + 38, fy + 2))

            # Combat effect (brief)
            if feat.combat_effect:
                effect_text = feat.combat_effect[:80] + "..." if len(feat.combat_effect) > 80 else feat.combat_effect
                es = fonts.tiny_font.render(effect_text, True, COLORS["text_dim"])
                effect_clip = pygame.Rect(right_x + 38, fy + 20, right_w - 60, 14)
                old_clip = screen.get_clip()
                screen.set_clip(effect_clip.clip(clip_rect))
                screen.blit(es, (right_x + 38, fy + 20))
                screen.set_clip(clip_rect)

            # Prerequisite badge
            if feat.prerequisite:
                prereq_x = right_x + right_w - 140
                Badge.draw(screen, prereq_x, fy + 5, feat.prerequisite[:15],
                           COLORS["warning_dim"], font=fonts.tiny_font)

            # ASI badge
            if feat.ability_increase:
                asi_x = right_x + right_w - 60
                Badge.draw(screen, asi_x, fy + 5, feat.ability_increase.split(" or ")[0][:8],
                           COLORS["accent_dim"], font=fonts.tiny_font)

        screen.set_clip(None)

        # Scrollbar
        total_h = len(available) * row_h
        panel_h = SCREEN_HEIGHT - content_y - 100
        if total_h > panel_h:
            max_scroll = max(1, total_h - panel_h)
            sb_h = max(20, int(panel_h * panel_h / total_h))
            sb_y = content_y + int((panel_h - sb_h) * min(1, self.feat_scroll / max_scroll))
            pygame.draw.rect(screen, COLORS["scrollbar_thumb"],
                             (right_x + right_w - 8, sb_y, 5, sb_h), border_radius=2)

    def _draw_spells_tab(self, screen, mouse_pos):
        """Draw spell selection tab."""
        right_x = 1030
        right_w = 870
        spell_ability = SPELLCASTING_ABILITY.get(self.char_class, "")

        if not spell_ability and self.char_subclass not in ("Eldritch Knight", "Arcane Trickster"):
            panel = Panel(right_x, 103, right_w, SCREEN_HEIGHT - 193, title="SPELLS")
            panel.draw(screen)
            txt = f"{self.char_class} is not a spellcasting class"
            if self.char_class == "Fighter":
                txt += " (select Eldritch Knight subclass for spells)"
            elif self.char_class == "Rogue":
                txt += " (select Arcane Trickster subclass for spells)"
            ns = fonts.body_font.render(txt, True, COLORS["text_muted"])
            screen.blit(ns, (right_x + 15, 145))
            return

        max_cantrips = self._get_max_cantrips()
        max_spells = self._get_max_spells()
        panel = Panel(right_x, 103, right_w, SCREEN_HEIGHT - 193,
                      title=f"SPELLS  |  Cantrips: {len(self.selected_cantrips)}/{max_cantrips}  |  Spells: {len(self.selected_spells)}/{max_spells}")
        panel.draw(screen)

        row_h = 32
        clip_rect = pygame.Rect(right_x + 5, 133, right_w - 10, SCREEN_HEIGHT - 233)
        screen.set_clip(clip_rect)

        # Cantrips section
        cantrips = self._get_class_cantrips()
        cy = 140 - self.spell_scroll
        if cantrips:
            hdr = fonts.small_bold.render(f"CANTRIPS ({len(self.selected_cantrips)}/{max_cantrips})", True, COLORS["spell"])
            screen.blit(hdr, (right_x + 15, cy))
            cy += 20
            for name in cantrips:
                if cy > SCREEN_HEIGHT - 100:
                    break
                if cy + row_h >= 133:
                    is_sel = name in self.selected_cantrips
                    is_hov = pygame.Rect(right_x + 5, cy, right_w - 10, row_h - 2).collidepoint(mouse_pos)
                    if is_sel:
                        pygame.draw.rect(screen, COLORS["spell_dim"],
                                         (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)
                    elif is_hov:
                        pygame.draw.rect(screen, COLORS["hover"],
                                         (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)
                    # Checkbox
                    cb = pygame.Rect(right_x + 12, cy + 6, 16, 16)
                    pygame.draw.rect(screen, COLORS["border"], cb, 1, border_radius=2)
                    if is_sel:
                        pygame.draw.rect(screen, COLORS["spell"], cb.inflate(-4, -4), border_radius=1)
                    # Name
                    ns = fonts.body_font.render(name, True, COLORS["text_bright"] if is_sel else COLORS["text_main"])
                    screen.blit(ns, (right_x + 35, cy + 5))
                    # Spell info
                    spell = SPELL_DATABASE.get(name)
                    if spell:
                        info = f"{spell.damage_dice} {spell.damage_type}" if spell.damage_dice else spell.description[:40]
                        info_s = fonts.tiny_font.render(info, True, COLORS["text_dim"])
                        screen.blit(info_s, (right_x + 350, cy + 8))
                cy += row_h

        # Spells section
        spells = self._get_class_spells()
        cy += 15
        if spells or CLASS_SPELL_LISTS.get(self.char_class, {}).get("spells"):
            hdr = fonts.small_bold.render(f"SPELLS ({len(self.selected_spells)}/{max_spells})", True, COLORS["accent"])
            if cy + 20 >= 133:
                screen.blit(hdr, (right_x + 15, cy))
            cy += 20
            for name in spells:
                if cy > SCREEN_HEIGHT - 100:
                    break
                if cy + row_h >= 133:
                    is_sel = name in self.selected_spells
                    is_hov = pygame.Rect(right_x + 5, cy, right_w - 10, row_h - 2).collidepoint(mouse_pos)
                    if is_sel:
                        pygame.draw.rect(screen, COLORS["accent_dim"],
                                         (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)
                    elif is_hov:
                        pygame.draw.rect(screen, COLORS["hover"],
                                         (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)
                    # Checkbox
                    cb = pygame.Rect(right_x + 12, cy + 6, 16, 16)
                    pygame.draw.rect(screen, COLORS["border"], cb, 1, border_radius=2)
                    if is_sel:
                        pygame.draw.rect(screen, COLORS["accent"], cb.inflate(-4, -4), border_radius=1)
                    # Name + level
                    spell = SPELL_DATABASE.get(name)
                    lvl_str = f"[Lv{spell.level}]" if spell else ""
                    ns = fonts.body_font.render(f"{lvl_str} {name}", True,
                                                 COLORS["text_bright"] if is_sel else COLORS["text_main"])
                    screen.blit(ns, (right_x + 35, cy + 5))
                    # Spell info
                    if spell:
                        info_parts = []
                        if spell.damage_dice:
                            info_parts.append(f"{spell.damage_dice} {spell.damage_type}")
                        if spell.heals:
                            info_parts.append(f"Heal {spell.heals}")
                        if spell.applies_condition:
                            info_parts.append(spell.applies_condition)
                        if spell.concentration:
                            info_parts.append("Conc.")
                        info = " | ".join(info_parts) if info_parts else spell.description[:40]
                        info_s = fonts.tiny_font.render(info, True, COLORS["text_dim"])
                        screen.blit(info_s, (right_x + 350, cy + 8))
                cy += row_h

        screen.set_clip(None)

        # Scrollbar
        total_h = (len(cantrips) + len(spells) + 3) * row_h
        panel_h = SCREEN_HEIGHT - 233
        if total_h > panel_h:
            max_scroll = max(1, total_h - panel_h)
            sb_h = max(20, int(panel_h * panel_h / total_h))
            sb_y = 133 + int((panel_h - sb_h) * min(1, self.spell_scroll / max_scroll))
            pygame.draw.rect(screen, COLORS["scrollbar_thumb"],
                             (right_x + right_w - 8, sb_y, 5, sb_h), border_radius=2)

    def _draw_skills_tab(self, screen, mouse_pos):
        """Draw skill proficiency selection tab."""
        right_x = 1030
        right_w = 870
        max_skills, available = self._get_skill_choices()
        selected_count = len(self.skill_proficiencies)

        panel = Panel(right_x, 103, right_w, SCREEN_HEIGHT - 193,
                      title=f"SKILL PROFICIENCIES ({selected_count}/{max_skills})")
        panel.draw(screen)

        info_txt = f"Choose {max_skills} skills from your class list ({self.char_class})"
        is_s = fonts.small_bold.render(info_txt, True, COLORS["text_dim"])
        screen.blit(is_s, (right_x + 15, 133))

        prof = calc_proficiency(self.char_level)
        row_h = 32
        cy = 155

        for skill_name, ability in ALL_SKILLS:
            is_available = skill_name in available
            is_sel = skill_name in self.skill_proficiencies
            is_hov = pygame.Rect(right_x + 5, cy, right_w - 10, row_h - 2).collidepoint(mouse_pos)

            # Row background
            if is_sel:
                pygame.draw.rect(screen, COLORS["accent_dim"],
                                 (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)
            elif is_hov and is_available:
                pygame.draw.rect(screen, COLORS["hover"],
                                 (right_x + 5, cy, right_w - 10, row_h - 2), border_radius=3)

            # Checkbox
            cb = pygame.Rect(right_x + 12, cy + 6, 16, 16)
            cb_col = COLORS["accent"] if is_available else COLORS["disabled"]
            pygame.draw.rect(screen, cb_col if is_sel else COLORS["border"], cb, 1, border_radius=2)
            if is_sel:
                pygame.draw.rect(screen, COLORS["accent"], cb.inflate(-4, -4), border_radius=1)

            # Skill name
            name_col = COLORS["text_bright"] if is_sel else (
                COLORS["text_main"] if is_available else COLORS["text_muted"]
            )
            ns = fonts.body_font.render(skill_name, True, name_col)
            screen.blit(ns, (right_x + 35, cy + 5))

            # Ability badge
            ab_abbr = ability[:3].upper()
            Badge.draw(screen, right_x + 250, cy + 5, ab_abbr,
                       COLORS.get(self.char_class.lower(), COLORS["accent_dim"]),
                       font=fonts.tiny_font)

            # Bonus
            mod = calc_modifier(self._get_effective_score(ability))
            total = mod + (prof if is_sel else 0)
            bonus_str = f"+{total}" if total >= 0 else str(total)
            bs = fonts.body_bold.render(bonus_str, True,
                                         COLORS["accent"] if is_sel else COLORS["text_muted"])
            screen.blit(bs, (right_x + 310, cy + 5))

            # Not-available indicator
            if not is_available and not is_sel:
                na = fonts.tiny_font.render("(other class)", True, COLORS["text_muted"])
                screen.blit(na, (right_x + 370, cy + 8))

            cy += row_h

    def _draw_hero_browser(self, screen, mouse_pos):
        """Draw the hero browser overlay for editing existing heroes."""
        # Overlay background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Browser panel
        bx, by, bw, bh = 400, 80, 1120, SCREEN_HEIGHT - 160
        pygame.draw.rect(screen, COLORS["panel"], (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(screen, COLORS["border_glow"], (bx, by, bw, bh), 2, border_radius=8)

        # Title
        title = fonts.header_font.render("SELECT HERO TO EDIT", True, COLORS["text_bright"])
        screen.blit(title, (bx + bw // 2 - title.get_width() // 2, by + 10))

        # Close button
        close_rect = pygame.Rect(bx + bw - 40, by + 8, 30, 30)
        close_hover = close_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, COLORS["danger"] if close_hover else COLORS["danger_dim"],
                         close_rect, border_radius=4)
        xs = fonts.body_bold.render("X", True, COLORS["text_bright"])
        screen.blit(xs, (close_rect.centerx - xs.get_width() // 2,
                         close_rect.centery - xs.get_height() // 2))

        # Hero list
        all_heroes = list(hero_list) + [h for h in self.saved_heroes if not any(e.name == h.name for e in hero_list)]

        if not all_heroes:
            nt = fonts.body_font.render("No heroes available. Create one first, or load from disk.",
                                         True, COLORS["text_muted"])
            screen.blit(nt, (bx + 20, by + 60))
            return

        # Column headers
        hdr_y = by + 45
        headers = [("Name", bx + 20), ("Race", bx + 300), ("Class", bx + 500),
                   ("Level", bx + 680), ("HP", bx + 760), ("AC", bx + 830), ("", bx + 900)]
        for htext, hx in headers:
            hs = fonts.small_bold.render(htext, True, COLORS["text_muted"])
            screen.blit(hs, (hx, hdr_y))

        Divider.draw(screen, bx + 10, hdr_y + 20, bw - 20)

        # Hero rows
        row_h = 40
        clip_rect = pygame.Rect(bx + 5, hdr_y + 25, bw - 10, bh - 80)
        screen.set_clip(clip_rect)

        for i, hero in enumerate(all_heroes):
            fy = hdr_y + 28 + i * row_h - self.hero_browser_scroll
            if fy > by + bh - 20:
                break
            if fy + row_h < hdr_y + 25:
                continue

            item_rect = pygame.Rect(bx + 10, fy, bw - 20, row_h - 2)
            is_hov = item_rect.collidepoint(mouse_pos)

            if is_hov:
                pygame.draw.rect(screen, COLORS["hover"], item_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["accent"], item_rect, 1, border_radius=4)
            elif i % 2 == 0:
                pygame.draw.rect(screen, COLORS["panel_light"], item_rect, border_radius=4)

            # Hero info
            ns = fonts.body_bold.render(hero.name[:25], True, COLORS["text_bright"])
            screen.blit(ns, (bx + 20, fy + 8))

            rs = fonts.body_font.render(hero.race[:20], True, COLORS["text_main"])
            screen.blit(rs, (bx + 300, fy + 8))

            cls_txt = hero.character_class
            if hero.subclass:
                cls_txt += f" ({hero.subclass[:12]})"
            cs = fonts.body_font.render(cls_txt[:25], True,
                                         COLORS.get(hero.character_class.lower(), COLORS["text_main"]))
            screen.blit(cs, (bx + 500, fy + 8))

            ls = fonts.body_bold.render(str(hero.character_level), True, COLORS["accent"])
            screen.blit(ls, (bx + 700, fy + 8))

            hs = fonts.body_bold.render(str(hero.hit_points), True, COLORS["hp_full"])
            screen.blit(hs, (bx + 770, fy + 8))

            acs = fonts.body_bold.render(str(hero.armor_class), True, COLORS["accent"])
            screen.blit(acs, (bx + 840, fy + 8))

            # Delete button
            del_rect = pygame.Rect(bx + bw - 100, fy + 4, 60, 28)
            del_hov = del_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, COLORS["danger"] if del_hov else COLORS["danger_dim"],
                             del_rect, border_radius=3)
            del_txt = fonts.small_bold.render("DEL", True, COLORS["text_bright"])
            screen.blit(del_txt, (del_rect.centerx - del_txt.get_width() // 2,
                                  del_rect.centery - del_txt.get_height() // 2))

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

        # Multiclass summary in bottom bar
        if self.multiclass_levels:
            mc_str = " / ".join(f"{cls} {lv}" for cls, lv in self.multiclass_levels.items())
            mc_surf = fonts.small_font.render(f"Multiclass: {mc_str}", True, COLORS["warning"])
            screen.blit(mc_surf, (220, bar_y + 38))

        # Buttons
        self.btn_back.draw(screen, mouse_pos)
        self.btn_load.draw(screen, mouse_pos)
        self.btn_edit_hero.draw(screen, mouse_pos)
        self.btn_save.draw(screen, mouse_pos)
        self.btn_save_disk.draw(screen, mouse_pos)
        self.btn_export.draw(screen, mouse_pos)

    # ============================================================
    # Equipment Tab
    # ============================================================

    def _get_shop_items(self):
        """Get items available in the current shop category."""
        if self.equipment_category == "weapons":
            return get_all_weapons()
        elif self.equipment_category == "armor":
            return get_all_armor()
        elif self.equipment_category == "shields":
            return get_all_shields()
        elif self.equipment_category == "wondrous":
            return get_all_wondrous()
        elif self.equipment_category == "consumables":
            return get_all_consumables()
        return []

    def _add_item_to_inventory(self, item_name):
        """Add an item from the database to the inventory."""
        item = get_item(item_name)
        if item:
            self.inventory.append(item)

    def _remove_item_from_inventory(self, index):
        """Remove an item from inventory by index."""
        if 0 <= index < len(self.inventory):
            self.inventory.pop(index)

    def _toggle_equip_item(self, index):
        """Toggle equip/unequip for an inventory item."""
        if 0 <= index < len(self.inventory):
            item = self.inventory[index]
            if item.equipped:
                item.equipped = False
                item.attuned = False
            else:
                # Unequip existing item in same slot
                slot = item.slot
                if slot:
                    for other in self.inventory:
                        if other is not item and other.equipped and other.slot == slot:
                            other.equipped = False
                            other.attuned = False
                item.equipped = True
                if item.requires_attunement:
                    # Check attunement limit (3 max)
                    attuned_count = sum(1 for i in self.inventory if i.attuned)
                    if attuned_count < 3:
                        item.attuned = True

    def _draw_equipment_tab(self, screen, mouse_pos):
        """Draw equipment inventory and shop."""
        rx, rw = 1030, 870

        if self.equipment_shop_open:
            self._draw_equipment_shop(screen, mouse_pos)
            return

        # --- Equipped Items Panel ---
        panel = Panel(rx, 103, rw, 350, title="EQUIPPED ITEMS")
        panel.draw(screen)

        equipped = [(i, item) for i, item in enumerate(self.inventory) if item.equipped]
        cy = 133
        row_h = 32
        clip = pygame.Rect(rx + 5, 133, rw - 10, 310)
        screen.set_clip(clip)
        for idx, (inv_idx, item) in enumerate(equipped):
            fy = cy + idx * row_h - self.equipment_scroll
            if fy < 120 or fy > 440:
                continue
            # Slot label
            slot_str = (item.slot or item.item_type).replace("_", " ").title()
            slot_surf = fonts.small_bold.render(f"[{slot_str}]", True, COLORS["text_dim"])
            screen.blit(slot_surf, (rx + 10, fy + 2))
            # Item name with rarity color
            rarity_colors = {"common": COLORS["text_main"], "uncommon": COLORS["success"],
                             "rare": COLORS["accent"], "very_rare": COLORS["spell"],
                             "legendary": COLORS["warning"], "artifact": COLORS["danger"]}
            color = rarity_colors.get(item.rarity, COLORS["text_main"])
            name_surf = fonts.body_bold.render(item.name, True, color)
            screen.blit(name_surf, (rx + 100, fy + 1))
            # Key stat
            stat_str = ""
            if item.item_type == "weapon":
                bonus_str = f"+{item.weapon_bonus}" if item.weapon_bonus else ""
                stat_str = f"{item.weapon_damage_dice}{bonus_str} {item.weapon_damage_type}"
            elif item.item_type in ("armor", "shield"):
                stat_str = f"AC {item.base_ac + item.ac_bonus}" if item.base_ac else f"+{item.ac_bonus} AC"
            elif item.ac_bonus:
                stat_str = f"+{item.ac_bonus} AC"
            if stat_str:
                stat_surf = fonts.small_font.render(stat_str, True, COLORS["text_dim"])
                screen.blit(stat_surf, (rx + rw - 160, fy + 4))
            # Attunement indicator
            if item.requires_attunement:
                att_str = "A" if item.attuned else "a"
                att_color = COLORS["accent"] if item.attuned else COLORS["text_muted"]
                att_surf = fonts.small_bold.render(att_str, True, att_color)
                screen.blit(att_surf, (rx + rw - 30, fy + 3))
        screen.set_clip(None)

        if not equipped:
            empty_surf = fonts.body_font.render("No items equipped. Add items below.", True, COLORS["text_muted"])
            screen.blit(empty_surf, (rx + 20, 180))

        # --- Inventory Panel ---
        inv_panel = Panel(rx, 460, rw, 320, title="INVENTORY")
        inv_panel.draw(screen)

        cy = 492
        clip = pygame.Rect(rx + 5, 490, rw - 10, 260)
        screen.set_clip(clip)
        for idx, item in enumerate(self.inventory):
            fy = cy + idx * row_h - self.equipment_scroll
            if fy < 480 or fy > 760:
                continue
            # Equip status
            eq_str = "[E]" if item.equipped else "[ ]"
            eq_color = COLORS["success"] if item.equipped else COLORS["text_muted"]
            eq_surf = fonts.small_bold.render(eq_str, True, eq_color)
            screen.blit(eq_surf, (rx + 10, fy + 2))
            # Name
            rarity_colors = {"common": COLORS["text_main"], "uncommon": COLORS["success"],
                             "rare": COLORS["accent"], "very_rare": COLORS["spell"],
                             "legendary": COLORS["warning"], "artifact": COLORS["danger"]}
            color = rarity_colors.get(item.rarity, COLORS["text_main"])
            name_surf = fonts.body_font.render(item.name, True, color)
            screen.blit(name_surf, (rx + 45, fy + 2))
            # Type
            type_surf = fonts.small_font.render(item.item_type.title(), True, COLORS["text_dim"])
            screen.blit(type_surf, (rx + rw - 180, fy + 4))
            # Remove button [X]
            x_surf = fonts.small_bold.render("[X]", True, COLORS["danger"])
            screen.blit(x_surf, (rx + rw - 40, fy + 2))
        screen.set_clip(None)

        # ADD ITEM button
        add_rect = pygame.Rect(rx + 10, 785, rw - 20, 34)
        pygame.draw.rect(screen, COLORS["accent"], add_rect, border_radius=4)
        add_txt = fonts.body_bold.render("+ ADD ITEM FROM DATABASE", True, COLORS["text_bright"])
        screen.blit(add_txt, (rx + rw // 2 - add_txt.get_width() // 2, 790))

        # Attunement counter
        attuned_count = sum(1 for i in self.inventory if i.attuned)
        att_surf = fonts.small_font.render(f"Attunement: {attuned_count}/3", True,
                                           COLORS["warning"] if attuned_count >= 3 else COLORS["text_dim"])
        screen.blit(att_surf, (rx + rw - 120, 463))

    def _draw_equipment_shop(self, screen, mouse_pos):
        """Draw the item shop overlay for adding items."""
        rx, rw = 1030, 870

        panel = Panel(rx, 103, rw, 700, title="ADD EQUIPMENT")
        panel.draw(screen)

        # Category tabs
        categories = [("weapons", "Weapons"), ("armor", "Armor"), ("shields", "Shields"),
                      ("wondrous", "Wondrous"), ("consumables", "Potions")]
        cat_w = rw // len(categories)
        for i, (key, label) in enumerate(categories):
            cx = rx + i * cat_w
            color = COLORS["accent"] if self.equipment_category == key else COLORS["panel"]
            pygame.draw.rect(screen, color, (cx, 133, cat_w, 28), border_radius=3)
            lbl = fonts.small_bold.render(label, True, COLORS["text_bright"] if self.equipment_category == key else COLORS["text_dim"])
            screen.blit(lbl, (cx + cat_w // 2 - lbl.get_width() // 2, 136))

        # Item list
        items = self._get_shop_items()
        cy = 170
        row_h = 30
        clip = pygame.Rect(rx + 5, 168, rw - 10, 590)
        screen.set_clip(clip)
        for i, name in enumerate(items):
            fy = cy + i * row_h - self.shop_scroll
            if fy < 160 or fy > 760:
                continue
            item = ALL_ITEMS_DB.get(name)
            # Hover highlight
            item_rect = pygame.Rect(rx + 5, fy, rw - 10, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, COLORS["panel"], item_rect, border_radius=3)
            # Name with rarity
            rarity_colors = {"common": COLORS["text_main"], "uncommon": COLORS["success"],
                             "rare": COLORS["accent"], "very_rare": COLORS["spell"],
                             "legendary": COLORS["warning"]}
            rarity = item.rarity if item else "common"
            color = rarity_colors.get(rarity, COLORS["text_main"])
            name_surf = fonts.body_font.render(name, True, color)
            screen.blit(name_surf, (rx + 15, fy + 3))
            # Key stat
            if item:
                stat = ""
                if item.item_type == "weapon":
                    stat = f"{item.weapon_damage_dice} {item.weapon_damage_type}"
                    if item.weapon_bonus:
                        stat = f"+{item.weapon_bonus} {stat}"
                elif item.item_type in ("armor",):
                    stat = f"AC {item.base_ac}"
                    if item.ac_bonus:
                        stat += f" +{item.ac_bonus}"
                elif item.item_type == "shield":
                    stat = f"+{item.ac_bonus} AC"
                elif item.heals:
                    stat = f"Heals {item.heals}"
                elif item.ac_bonus:
                    stat = f"+{item.ac_bonus} AC"
                if stat:
                    stat_surf = fonts.small_font.render(stat, True, COLORS["text_dim"])
                    screen.blit(stat_surf, (rx + rw - 200, fy + 5))
                # Attune marker
                if item.requires_attunement:
                    att_surf = fonts.small_font.render("(A)", True, COLORS["warning"])
                    screen.blit(att_surf, (rx + rw - 50, fy + 5))
        screen.set_clip(None)

        # Close button
        close_rect = pygame.Rect(rx + rw - 140, 103, 130, 28)
        pygame.draw.rect(screen, COLORS["danger"], close_rect, border_radius=4)
        close_txt = fonts.small_bold.render("CLOSE SHOP", True, COLORS["text_bright"])
        screen.blit(close_txt, (rx + rw - 140 + 65 - close_txt.get_width() // 2, 107))

    def _handle_equipment_clicks(self, mouse_pos):
        """Handle clicks in the equipment tab."""
        rx, rw = 1030, 870

        if self.equipment_shop_open:
            # Close button
            close_rect = pygame.Rect(rx + rw - 140, 103, 130, 28)
            if close_rect.collidepoint(mouse_pos):
                self.equipment_shop_open = False
                return

            # Category tabs
            categories = ["weapons", "armor", "shields", "wondrous", "consumables"]
            cat_w = rw // len(categories)
            for i, key in enumerate(categories):
                tab_rect = pygame.Rect(rx + i * cat_w, 133, cat_w, 28)
                if tab_rect.collidepoint(mouse_pos):
                    self.equipment_category = key
                    self.shop_scroll = 0
                    return

            # Item selection
            items = self._get_shop_items()
            cy = 170
            row_h = 30
            for i, name in enumerate(items):
                fy = cy + i * row_h - self.shop_scroll
                if fy < 160 or fy > 760:
                    continue
                item_rect = pygame.Rect(rx + 5, fy, rw - 10, row_h - 2)
                if item_rect.collidepoint(mouse_pos):
                    self._add_item_to_inventory(name)
                    self.equipment_shop_open = False
                    return
            return

        # ADD ITEM button
        add_rect = pygame.Rect(rx + 10, 785, rw - 20, 34)
        if add_rect.collidepoint(mouse_pos):
            self.equipment_shop_open = True
            self.shop_scroll = 0
            return

        # Inventory item clicks
        cy = 492
        row_h = 32
        for idx, item in enumerate(self.inventory):
            fy = cy + idx * row_h - self.equipment_scroll
            if fy < 480 or fy > 760:
                continue
            # Remove button [X]
            x_rect = pygame.Rect(rx + rw - 50, fy, 40, row_h - 2)
            if x_rect.collidepoint(mouse_pos):
                self._remove_item_from_inventory(idx)
                return
            # Equip toggle (click anywhere else on the row)
            item_rect = pygame.Rect(rx + 5, fy, rw - 60, row_h - 2)
            if item_rect.collidepoint(mouse_pos):
                self._toggle_equip_item(idx)
                return

    # ============================================================
    # Multiclass Tab
    # ============================================================

    def _get_total_level(self):
        """Get total character level (primary + multiclass)."""
        return self.char_level + sum(self.multiclass_levels.values())

    def _add_multiclass(self, class_name):
        """Add a new multiclass or increment an existing one."""
        if class_name == self.char_class:
            return  # Can't multiclass into primary class
        total = self._get_total_level()
        if total >= 20:
            return  # Can't exceed level 20
        if class_name in self.multiclass_levels:
            self.multiclass_levels[class_name] += 1
        else:
            self.multiclass_levels[class_name] = 1

    def _remove_multiclass_level(self, class_name):
        """Remove a level from a multiclass."""
        if class_name in self.multiclass_levels:
            self.multiclass_levels[class_name] -= 1
            if self.multiclass_levels[class_name] <= 0:
                del self.multiclass_levels[class_name]

    def _get_multiclass_spell_slots(self):
        """Calculate combined spell slots for multiclass (PHB p.165)."""
        caster_level = 0
        # Full casters: Wizard, Cleric, Druid, Bard, Sorcerer = level
        # Half casters: Paladin, Ranger = level / 2
        # Third casters: Eldritch Knight (Fighter), Arcane Trickster (Rogue) = level / 3
        classes = {self.char_class: self.char_level}
        classes.update(self.multiclass_levels)

        for cls, lv in classes.items():
            if cls in FULL_CASTERS:
                caster_level += lv
            elif cls in HALF_CASTERS:
                caster_level += lv // 2
            elif cls == "Warlock":
                pass  # Warlock pact magic is separate
            elif cls == "Fighter":
                if self.char_subclass == "Eldritch Knight" and cls == self.char_class:
                    caster_level += lv // 3
            elif cls == "Rogue":
                if self.char_subclass == "Arcane Trickster" and cls == self.char_class:
                    caster_level += lv // 3

        if caster_level <= 0:
            return {}

        # Use the multiclass spell slot table (same as full caster table)
        slot_list = FULL_CASTER_SLOTS.get(min(20, caster_level), [])
        slots = {}
        for i, count in enumerate(slot_list):
            slots[SLOT_LEVEL_NAMES[i]] = count
        return slots

    def _draw_multiclass_tab(self, screen, mouse_pos):
        """Draw multiclass management tab."""
        rx, rw = 1030, 870

        # Primary class panel
        panel = Panel(rx, 103, rw, 200, title="CLASS LEVELS")
        panel.draw(screen)

        cy = 135
        total_level = self._get_total_level()

        # Primary class
        prim_surf = fonts.body_bold.render(
            f"{self.char_class} (Primary)", True, COLORS["text_bright"])
        screen.blit(prim_surf, (rx + 15, cy))
        lv_surf = fonts.header_font.render(str(self.char_level), True, COLORS["accent"])
        screen.blit(lv_surf, (rx + rw - 80, cy - 3))

        # Level +/- for primary
        minus_rect = pygame.Rect(rx + rw - 120, cy, 28, 28)
        plus_rect = pygame.Rect(rx + rw - 40, cy, 28, 28)
        pygame.draw.rect(screen, COLORS["danger"], minus_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["success"], plus_rect, border_radius=3)
        m_txt = fonts.body_bold.render("-", True, COLORS["text_bright"])
        p_txt = fonts.body_bold.render("+", True, COLORS["text_bright"])
        screen.blit(m_txt, (minus_rect.centerx - m_txt.get_width() // 2, minus_rect.centery - m_txt.get_height() // 2))
        screen.blit(p_txt, (plus_rect.centerx - p_txt.get_width() // 2, plus_rect.centery - p_txt.get_height() // 2))
        cy += 36

        # Multiclass entries
        for cls, lv in list(self.multiclass_levels.items()):
            cls_surf = fonts.body_bold.render(cls, True, COLORS["text_main"])
            screen.blit(cls_surf, (rx + 15, cy))
            lv_s = fonts.header_font.render(str(lv), True, COLORS["warning"])
            screen.blit(lv_s, (rx + rw - 80, cy - 3))

            minus_rect = pygame.Rect(rx + rw - 120, cy, 28, 28)
            plus_rect = pygame.Rect(rx + rw - 40, cy, 28, 28)
            pygame.draw.rect(screen, COLORS["danger"], minus_rect, border_radius=3)
            pygame.draw.rect(screen, COLORS["success"], plus_rect, border_radius=3)
            screen.blit(m_txt, (minus_rect.centerx - m_txt.get_width() // 2, minus_rect.centery - m_txt.get_height() // 2))
            screen.blit(p_txt, (plus_rect.centerx - p_txt.get_width() // 2, plus_rect.centery - p_txt.get_height() // 2))
            cy += 36

        # Total level
        total_surf = fonts.body_bold.render(f"Total Level: {total_level}/20", True,
                                            COLORS["danger"] if total_level > 20 else COLORS["accent"])
        screen.blit(total_surf, (rx + 15, cy + 5))

        # --- Add Multiclass Panel ---
        add_panel = Panel(rx, 310, rw, 240, title="ADD MULTICLASS")
        add_panel.draw(screen)

        cy = 343
        col_w = rw // 3
        for i, cls in enumerate(CLASS_LIST):
            if cls == self.char_class:
                continue  # Can't multiclass into primary
            row = i // 3
            col = i % 3
            bx = rx + 10 + col * (col_w - 3)
            by = cy + row * 34
            btn_rect = pygame.Rect(bx, by, col_w - 10, 30)

            is_hover = btn_rect.collidepoint(mouse_pos)
            already_has = cls in self.multiclass_levels
            btn_color = COLORS["warning"] if already_has else (COLORS["panel_header"] if is_hover else COLORS["panel"])
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=4)
            if is_hover or already_has:
                pygame.draw.rect(screen, COLORS["accent"], btn_rect, 1, border_radius=4)
            cls_txt = fonts.small_bold.render(cls, True, COLORS["text_bright"] if already_has else COLORS["text_main"])
            screen.blit(cls_txt, (bx + (col_w - 10) // 2 - cls_txt.get_width() // 2,
                                  by + 15 - cls_txt.get_height() // 2))

        # --- Multiclass Spell Slots ---
        if self.multiclass_levels:
            mc_slots = self._get_multiclass_spell_slots()
            if mc_slots:
                slot_panel = Panel(rx, 560, rw, 120, title="MULTICLASS SPELL SLOTS")
                slot_panel.draw(screen)
                sy = 590
                slot_str = "  ".join(f"{k}: {v}" for k, v in mc_slots.items())
                slot_surf = fonts.body_font.render(slot_str, True, COLORS["spell"])
                screen.blit(slot_surf, (rx + 15, sy))

        # --- Multiclass Features Preview ---
        feat_y = 690
        feat_panel = Panel(rx, feat_y, rw, 100, title="MULTICLASS FEATURES")
        feat_panel.draw(screen)
        fy = feat_y + 33
        for cls, lv in self.multiclass_levels.items():
            features = get_class_features(cls, lv, "")
            feat_names = [f.name for f in features[:4]]
            if feat_names:
                txt = f"{cls} {lv}: {', '.join(feat_names)}"
                if len(features) > 4:
                    txt += f" (+{len(features)-4} more)"
                f_surf = fonts.small_font.render(txt[:100], True, COLORS["text_dim"])
                screen.blit(f_surf, (rx + 15, fy))
                fy += 20

    def _handle_multiclass_clicks(self, mouse_pos):
        """Handle clicks in the multiclass tab."""
        rx, rw = 1030, 870
        total_level = self._get_total_level()

        # Primary class level +/-
        cy = 135
        minus_rect = pygame.Rect(rx + rw - 120, cy, 28, 28)
        plus_rect = pygame.Rect(rx + rw - 40, cy, 28, 28)
        if minus_rect.collidepoint(mouse_pos):
            if self.char_level > 1:
                self.char_level -= 1
            return
        if plus_rect.collidepoint(mouse_pos):
            if self._get_total_level() < 20:
                self.char_level += 1
            return
        cy += 36

        # Multiclass entry level +/-
        for cls in list(self.multiclass_levels.keys()):
            lv = self.multiclass_levels.get(cls, 0)
            minus_rect = pygame.Rect(rx + rw - 120, cy, 28, 28)
            plus_rect = pygame.Rect(rx + rw - 40, cy, 28, 28)
            if minus_rect.collidepoint(mouse_pos):
                self._remove_multiclass_level(cls)
                return
            if plus_rect.collidepoint(mouse_pos):
                if self._get_total_level() < 20:
                    self.multiclass_levels[cls] = lv + 1
                return
            cy += 36

        # Add multiclass class buttons
        cy = 343
        col_w = rw // 3
        for i, cls in enumerate(CLASS_LIST):
            if cls == self.char_class:
                continue
            row = i // 3
            col = i % 3
            bx = rx + 10 + col * (col_w - 3)
            by = cy + row * 34
            btn_rect = pygame.Rect(bx, by, col_w - 10, 30)
            if btn_rect.collidepoint(mouse_pos):
                self._add_multiclass(cls)
                return
