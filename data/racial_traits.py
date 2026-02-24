"""
D&D 5e 2014 Racial Traits Database
All racial traits organized by race.
"""
from data.models import RacialTrait

# ============================================================
# HUMAN
# ============================================================
HUMAN_TRAITS = [
    RacialTrait("Human Versatility", "+1 to all ability scores",
                mechanic="human_versatility"),
    RacialTrait("Extra Language", "One extra language of choice",
                mechanic="extra_language"),
]

# Variant Human
VARIANT_HUMAN_TRAITS = [
    RacialTrait("Human Determination", "+1 to two ability scores, one skill, one feat",
                mechanic="variant_human"),
]

# ============================================================
# ELF (High Elf)
# ============================================================
HIGH_ELF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft as bright, "
                "darkness as dim light.",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Keen Senses", "Proficiency in Perception",
                mechanic="keen_senses"),
    RacialTrait("Fey Ancestry", "Advantage on saves against being Charmed. "
                "Magic can't put you to sleep.",
                mechanic="fey_ancestry"),
    RacialTrait("Trance", "Don't sleep. Meditate 4 hours instead of 8 hours sleep.",
                mechanic="trance"),
    RacialTrait("Elf Weapon Training", "Proficiency with longsword, shortsword, "
                "shortbow, longbow.",
                mechanic="elf_weapon_training"),
    RacialTrait("Cantrip", "One wizard cantrip (INT-based)",
                mechanic="high_elf_cantrip"),
]

# Wood Elf
WOOD_ELF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Keen Senses", "Proficiency in Perception",
                mechanic="keen_senses"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Trance", "4 hours meditation instead of 8 hours sleep",
                mechanic="trance"),
    RacialTrait("Elf Weapon Training", "Proficiency with longsword, shortsword, "
                "shortbow, longbow.",
                mechanic="elf_weapon_training"),
    RacialTrait("Fleet of Foot", "Base walking speed is 35 feet",
                mechanic="fleet_of_foot"),
    RacialTrait("Mask of the Wild", "Can hide when lightly obscured by natural phenomena",
                mechanic="mask_of_wild"),
]

# Dark Elf (Drow)
DROW_TRAITS = [
    RacialTrait("Superior Darkvision (120ft)", "See in dim light within 120ft",
                mechanic="darkvision", mechanic_value="120"),
    RacialTrait("Sunlight Sensitivity", "Disadvantage on attack rolls and Perception "
                "checks in direct sunlight.",
                mechanic="sunlight_sensitivity"),
    RacialTrait("Drow Magic", "Dancing Lights cantrip. Faerie Fire at 3rd, "
                "Darkness at 5th (1/day each, CHA-based).",
                mechanic="drow_magic"),
    RacialTrait("Drow Weapon Training", "Proficiency with rapiers, shortswords, hand crossbows",
                mechanic="drow_weapon_training"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
]

# ============================================================
# DWARF
# ============================================================
HILL_DWARF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Dwarven Resilience", "Advantage on saves vs poison, resistance to poison damage",
                mechanic="dwarven_resilience"),
    RacialTrait("Dwarven Combat Training", "Proficiency with battleaxe, handaxe, "
                "light hammer, warhammer.",
                mechanic="dwarven_combat_training"),
    RacialTrait("Stonecunning", "Double proficiency on History checks related to stonework",
                mechanic="stonecunning"),
    RacialTrait("Dwarven Toughness", "+1 HP per level",
                mechanic="dwarven_toughness"),
]

MOUNTAIN_DWARF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Dwarven Resilience", "Advantage on saves vs poison, resistance to poison damage",
                mechanic="dwarven_resilience"),
    RacialTrait("Dwarven Combat Training", "Proficiency with battleaxe, handaxe, "
                "light hammer, warhammer.",
                mechanic="dwarven_combat_training"),
    RacialTrait("Stonecunning", "Double proficiency on History checks related to stonework",
                mechanic="stonecunning"),
    RacialTrait("Dwarven Armor Training", "Proficiency with light and medium armor",
                mechanic="dwarven_armor_training"),
]

# ============================================================
# HALFLING
# ============================================================
LIGHTFOOT_HALFLING_TRAITS = [
    RacialTrait("Lucky", "Reroll natural 1 on attack, ability check, or save",
                mechanic="lucky"),
    RacialTrait("Brave", "Advantage on saves against being Frightened",
                mechanic="brave"),
    RacialTrait("Halfling Nimbleness", "Move through space of any creature larger than you",
                mechanic="halfling_nimbleness"),
    RacialTrait("Naturally Stealthy", "Can hide behind creatures one size larger than you",
                mechanic="naturally_stealthy"),
]

STOUT_HALFLING_TRAITS = [
    RacialTrait("Lucky", "Reroll natural 1 on attack, ability check, or save",
                mechanic="lucky"),
    RacialTrait("Brave", "Advantage on saves against being Frightened",
                mechanic="brave"),
    RacialTrait("Halfling Nimbleness", "Move through space of any creature larger than you",
                mechanic="halfling_nimbleness"),
    RacialTrait("Stout Resilience", "Advantage on saves vs poison, resistance to poison damage",
                mechanic="stout_resilience"),
]

# ============================================================
# HALF-ORC
# ============================================================
HALF_ORC_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Menacing", "Proficiency in Intimidation",
                mechanic="menacing"),
    RacialTrait("Relentless Endurance", "When reduced to 0 HP but not killed, drop to 1 HP "
                "instead. 1/long rest.",
                mechanic="relentless_endurance", uses_per_day=1),
    RacialTrait("Savage Attacks", "On critical hit with melee weapon, roll one additional "
                "weapon damage die.",
                mechanic="savage_attacks"),
]

# ============================================================
# HALF-ELF
# ============================================================
HALF_ELF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Skill Versatility", "Proficiency in two skills of choice",
                mechanic="skill_versatility"),
]

# ============================================================
# GNOME
# ============================================================
ROCK_GNOME_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Gnome Cunning", "Advantage on INT, WIS, CHA saves against magic",
                mechanic="gnome_cunning"),
    RacialTrait("Artificer's Lore", "Double proficiency on History checks related to "
                "magic items, alchemical objects, technological devices.",
                mechanic="artificers_lore"),
    RacialTrait("Tinker", "Proficiency with tinker's tools. Construct tiny clockwork devices.",
                mechanic="tinker"),
]

FOREST_GNOME_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Gnome Cunning", "Advantage on INT, WIS, CHA saves against magic",
                mechanic="gnome_cunning"),
    RacialTrait("Natural Illusionist", "Know Minor Illusion cantrip (INT-based)",
                mechanic="natural_illusionist"),
    RacialTrait("Speak with Small Beasts", "Communicate simple ideas with Small or smaller beasts",
                mechanic="speak_with_beasts"),
]

# ============================================================
# DRAGONBORN
# ============================================================
DRAGONBORN_TRAITS = [
    RacialTrait("Draconic Ancestry", "Choose a dragon type for resistance and breath weapon",
                mechanic="draconic_ancestry", mechanic_value="fire"),
    RacialTrait("Breath Weapon", "Action: exhale energy. 5x30ft line or 15ft cone. "
                "DEX/CON save DC = 8+CON+prof. Damage: 2d6 (increases at 6th, 11th, 16th). "
                "1/short rest.",
                mechanic="breath_weapon", damage_dice="2d6", damage_type="fire",
                save_ability="Dexterity", uses_per_day=1),
    RacialTrait("Damage Resistance", "Resistance to damage type of draconic ancestry",
                mechanic="draconic_resistance", mechanic_value="fire"),
]

# ============================================================
# TIEFLING
# ============================================================
TIEFLING_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Hellish Resistance", "Resistance to fire damage",
                mechanic="hellish_resistance"),
    RacialTrait("Infernal Legacy", "Thaumaturgy cantrip. Hellish Rebuke at 3rd (2d10 fire, "
                "1/day), Darkness at 5th (1/day). CHA-based.",
                mechanic="infernal_legacy"),
]


# ============================================================
# Helper to get traits by race name
# ============================================================
RACE_TRAITS_MAP = {
    "Human": HUMAN_TRAITS,
    "Variant Human": VARIANT_HUMAN_TRAITS,
    "High Elf": HIGH_ELF_TRAITS,
    "Wood Elf": WOOD_ELF_TRAITS,
    "Drow": DROW_TRAITS,
    "Hill Dwarf": HILL_DWARF_TRAITS,
    "Mountain Dwarf": MOUNTAIN_DWARF_TRAITS,
    "Lightfoot Halfling": LIGHTFOOT_HALFLING_TRAITS,
    "Stout Halfling": STOUT_HALFLING_TRAITS,
    "Half-Orc": HALF_ORC_TRAITS,
    "Half-Elf": HALF_ELF_TRAITS,
    "Rock Gnome": ROCK_GNOME_TRAITS,
    "Forest Gnome": FOREST_GNOME_TRAITS,
    "Dragonborn": DRAGONBORN_TRAITS,
    "Tiefling": TIEFLING_TRAITS,
}


def get_racial_traits(race: str) -> list[RacialTrait]:
    """Get all racial traits for a given race."""
    return list(RACE_TRAITS_MAP.get(race, []))
