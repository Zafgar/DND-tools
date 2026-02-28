"""
D&D 5e 2014 Racial Traits Database – ALL sourcebooks
PHB, Volo's Guide, Mordenkainen's, XGtE, SCAG, EE Player's Companion,
Eberron, Ravnica, Tortle Package.
"""
from data.models import RacialTrait

# ============================================================
# RACIAL ABILITY SCORE INCREASES
# ============================================================
RACE_ASI = {
    # --- PHB ---
    "Human":               {"strength": 1, "dexterity": 1, "constitution": 1,
                            "intelligence": 1, "wisdom": 1, "charisma": 1},
    "Variant Human":       {},  # +1 to two of choice
    "High Elf":            {"dexterity": 2, "intelligence": 1},
    "Wood Elf":            {"dexterity": 2, "wisdom": 1},
    "Drow":                {"dexterity": 2, "charisma": 1},
    "Hill Dwarf":          {"constitution": 2, "wisdom": 1},
    "Mountain Dwarf":      {"strength": 2, "constitution": 2},
    "Lightfoot Halfling":  {"dexterity": 2, "charisma": 1},
    "Stout Halfling":      {"dexterity": 2, "constitution": 1},
    "Half-Orc":            {"strength": 2, "constitution": 1},
    "Half-Elf":            {"charisma": 2},  # +1 to two others
    "Rock Gnome":          {"intelligence": 2, "constitution": 1},
    "Forest Gnome":        {"intelligence": 2, "dexterity": 1},
    "Dragonborn":          {"strength": 2, "charisma": 1},
    "Tiefling":            {"charisma": 2, "intelligence": 1},
    # --- Volo's Guide to Monsters ---
    "Aasimar (Protector)": {"charisma": 2, "wisdom": 1},
    "Aasimar (Scourge)":   {"charisma": 2, "constitution": 1},
    "Aasimar (Fallen)":    {"charisma": 2, "strength": 1},
    "Firbolg":             {"wisdom": 2, "strength": 1},
    "Goliath":             {"strength": 2, "constitution": 1},
    "Kenku":               {"dexterity": 2, "wisdom": 1},
    "Lizardfolk":          {"constitution": 2, "wisdom": 1},
    "Tabaxi":              {"dexterity": 2, "charisma": 1},
    "Triton":              {"strength": 1, "constitution": 1, "charisma": 1},
    "Bugbear":             {"strength": 2, "dexterity": 1},
    "Goblin":              {"dexterity": 2, "constitution": 1},
    "Hobgoblin":           {"constitution": 2, "intelligence": 1},
    "Kobold":              {"dexterity": 2, "strength": -2},
    "Orc":                 {"strength": 2, "constitution": 1, "intelligence": -2},
    "Yuan-ti Pureblood":   {"charisma": 2, "intelligence": 1},
    # --- SCAG / Mordenkainen's ---
    "Duergar":             {"constitution": 2, "strength": 1},
    "Deep Gnome":          {"intelligence": 2, "dexterity": 1},
    "Eladrin":             {"dexterity": 2, "charisma": 1},
    "Sea Elf":             {"dexterity": 2, "constitution": 1},
    "Shadar-kai":          {"dexterity": 2, "constitution": 1},
    "Githyanki":           {"strength": 2, "intelligence": 1},
    "Githzerai":           {"wisdom": 2, "intelligence": 1},
    # --- Elemental Evil ---
    "Aarakocra":           {"dexterity": 2, "wisdom": 1},
    "Air Genasi":          {"constitution": 2, "dexterity": 1},
    "Earth Genasi":        {"constitution": 2, "strength": 1},
    "Fire Genasi":         {"constitution": 2, "intelligence": 1},
    "Water Genasi":        {"constitution": 2, "wisdom": 1},
    # --- Eberron ---
    "Changeling":          {"charisma": 2},  # +1 to one other
    "Kalashtar":           {"wisdom": 2, "charisma": 1},
    "Shifter (Beasthide)": {"constitution": 2, "strength": 1},
    "Shifter (Longtooth)": {"strength": 2, "dexterity": 1},
    "Shifter (Swiftstride)": {"dexterity": 2, "charisma": 1},
    "Shifter (Wildhunt)":  {"wisdom": 2, "dexterity": 1},
    "Warforged":           {"constitution": 2},  # +1 to one other
    # --- Ravnica ---
    "Centaur":             {"strength": 2, "wisdom": 1},
    "Loxodon":             {"constitution": 2, "wisdom": 1},
    "Minotaur":            {"strength": 2, "constitution": 1},
    "Simic Hybrid":        {"constitution": 2},  # +1 to one other
    "Vedalken":            {"intelligence": 2, "wisdom": 1},
    # --- Tortle Package ---
    "Tortle":              {"strength": 2, "wisdom": 1},
}


def get_racial_asi(race: str) -> dict:
    """Get the fixed ability score increases for a race."""
    return dict(RACE_ASI.get(race, {}))


# ============================================================
# PHB RACES
# ============================================================
HUMAN_TRAITS = [
    RacialTrait("Human Versatility", "+1 to all ability scores",
                mechanic="human_versatility"),
    RacialTrait("Extra Language", "One extra language of choice",
                mechanic="extra_language"),
]

VARIANT_HUMAN_TRAITS = [
    RacialTrait("Human Determination", "+1 to two ability scores, one skill, one feat",
                mechanic="variant_human"),
]

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

HALF_ELF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Skill Versatility", "Proficiency in two skills of choice",
                mechanic="skill_versatility"),
]

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
# VOLO'S GUIDE TO MONSTERS
# ============================================================
AASIMAR_PROTECTOR_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Celestial Resistance", "Resistance to necrotic and radiant damage",
                mechanic="celestial_resistance"),
    RacialTrait("Healing Hands", "Touch: heal HP = your level. 1/long rest.",
                mechanic="healing_hands", uses_per_day=1),
    RacialTrait("Light Bearer", "Know the Light cantrip (CHA-based)",
                mechanic="light_bearer"),
    RacialTrait("Radiant Soul", "At 3rd level, action: sprout wings (fly 30ft) and "
                "deal extra radiant damage = level for 1 min. 1/long rest.",
                mechanic="radiant_soul", uses_per_day=1),
]

AASIMAR_SCOURGE_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Celestial Resistance", "Resistance to necrotic and radiant damage",
                mechanic="celestial_resistance"),
    RacialTrait("Healing Hands", "Touch: heal HP = your level. 1/long rest.",
                mechanic="healing_hands", uses_per_day=1),
    RacialTrait("Light Bearer", "Know the Light cantrip (CHA-based)",
                mechanic="light_bearer"),
    RacialTrait("Radiant Consumption", "At 3rd level, action: searing light. Each creature "
                "within 10ft takes radiant damage = half level. +level radiant to one "
                "attack/spell per turn. 1 min, 1/long rest.",
                mechanic="radiant_consumption", uses_per_day=1),
]

AASIMAR_FALLEN_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Celestial Resistance", "Resistance to necrotic and radiant damage",
                mechanic="celestial_resistance"),
    RacialTrait("Healing Hands", "Touch: heal HP = your level. 1/long rest.",
                mechanic="healing_hands", uses_per_day=1),
    RacialTrait("Light Bearer", "Know the Light cantrip (CHA-based)",
                mechanic="light_bearer"),
    RacialTrait("Necrotic Shroud", "At 3rd level, action: frighten creatures within 10ft "
                "(CHA save). +level necrotic to one attack/spell per turn. 1 min, 1/long rest.",
                mechanic="necrotic_shroud", uses_per_day=1),
]

FIRBOLG_TRAITS = [
    RacialTrait("Firbolg Magic", "Detect Magic and Disguise Self 1/short rest each (WIS-based)",
                mechanic="firbolg_magic"),
    RacialTrait("Hidden Step", "Bonus action: invisible until start of next turn. 1/short rest.",
                mechanic="hidden_step", uses_per_day=1),
    RacialTrait("Powerful Build", "Count as Large for carrying capacity and push/drag/lift",
                mechanic="powerful_build"),
    RacialTrait("Speech of Beast and Leaf", "Communicate with beasts and plants",
                mechanic="speech_beast_leaf"),
]

GOLIATH_TRAITS = [
    RacialTrait("Natural Athlete", "Proficiency in Athletics",
                mechanic="natural_athlete"),
    RacialTrait("Stone's Endurance", "Reaction: reduce damage by 1d12+CON mod. 1/short rest.",
                mechanic="stones_endurance", uses_per_day=1),
    RacialTrait("Powerful Build", "Count as Large for carrying capacity",
                mechanic="powerful_build"),
    RacialTrait("Mountain Born", "Acclimated to high altitude and cold weather",
                mechanic="mountain_born"),
]

KENKU_TRAITS = [
    RacialTrait("Expert Forgery", "Advantage on checks to produce forgeries or duplicates",
                mechanic="expert_forgery"),
    RacialTrait("Kenku Training", "Proficiency in two of: Acrobatics, Deception, Stealth, "
                "Sleight of Hand",
                mechanic="kenku_training"),
    RacialTrait("Mimicry", "Mimic sounds and voices. WIS (Insight) check to determine fake.",
                mechanic="mimicry"),
]

LIZARDFOLK_TRAITS = [
    RacialTrait("Bite", "Natural weapon: 1d6+STR piercing. Can use as bonus action after attack.",
                mechanic="bite", damage_dice="1d6", damage_type="piercing"),
    RacialTrait("Cunning Artisan", "Craft weapons/shields from creature corpses during short rest",
                mechanic="cunning_artisan"),
    RacialTrait("Hold Breath", "Hold breath up to 15 minutes",
                mechanic="hold_breath"),
    RacialTrait("Hunter's Lore", "Proficiency in two of: Animal Handling, Nature, Perception, "
                "Stealth, Survival",
                mechanic="hunters_lore"),
    RacialTrait("Natural Armor", "AC = 13 + DEX when not wearing armor",
                mechanic="natural_armor"),
    RacialTrait("Hungry Jaws", "Bonus action bite: gain temp HP = CON mod. 1/short rest.",
                mechanic="hungry_jaws", uses_per_day=1),
]

TABAXI_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Feline Agility", "Double speed until end of turn (must not move next turn to reuse)",
                mechanic="feline_agility"),
    RacialTrait("Cat's Claws", "Climb speed 20ft. Unarmed strike: 1d4+STR slashing.",
                mechanic="cats_claws"),
    RacialTrait("Cat's Talent", "Proficiency in Perception and Stealth",
                mechanic="cats_talent"),
]

TRITON_TRAITS = [
    RacialTrait("Amphibious", "Breathe air and water",
                mechanic="amphibious"),
    RacialTrait("Control Air and Water", "Fog Cloud at 1st, Gust of Wind at 3rd, "
                "Wall of Water at 5th. 1/long rest each. CHA-based.",
                mechanic="control_air_water"),
    RacialTrait("Emissary of the Sea", "Communicate with water-breathing beasts",
                mechanic="emissary_sea"),
    RacialTrait("Guardians of the Depths", "Resistance to cold damage",
                mechanic="guardians_depths"),
    RacialTrait("Swim Speed", "Swim speed 30ft",
                mechanic="swim_speed"),
]

BUGBEAR_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Long-Limbed", "Melee attacks have +5ft reach on your turn",
                mechanic="long_limbed"),
    RacialTrait("Powerful Build", "Count as Large for carrying capacity",
                mechanic="powerful_build"),
    RacialTrait("Sneaky", "Proficiency in Stealth",
                mechanic="sneaky"),
    RacialTrait("Surprise Attack", "Extra 2d6 damage if target is surprised (first round)",
                mechanic="surprise_attack", damage_dice="2d6"),
]

GOBLIN_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fury of the Small", "Extra damage = level to creature larger than you. "
                "1/short rest.",
                mechanic="fury_of_small", uses_per_day=1),
    RacialTrait("Nimble Escape", "Disengage or Hide as bonus action each turn",
                mechanic="nimble_escape"),
]

HOBGOBLIN_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Martial Training", "Proficiency with two martial weapons and light armor",
                mechanic="martial_training"),
    RacialTrait("Saving Face", "Add bonus = # allies within 30ft to failed roll. 1/short rest.",
                mechanic="saving_face", uses_per_day=1),
]

KOBOLD_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Grovel, Cower, and Beg", "Action: give allies advantage on attacks vs "
                "enemies within 10ft of you until end of next turn. 1/short rest.",
                mechanic="grovel_cower_beg", uses_per_day=1),
    RacialTrait("Pack Tactics", "Advantage on attack if ally is within 5ft of target",
                mechanic="pack_tactics"),
    RacialTrait("Sunlight Sensitivity", "Disadvantage on attacks and Perception in sunlight",
                mechanic="sunlight_sensitivity"),
]

ORC_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Aggressive", "Bonus action: move up to speed toward hostile creature",
                mechanic="aggressive"),
    RacialTrait("Menacing", "Proficiency in Intimidation",
                mechanic="menacing"),
    RacialTrait("Powerful Build", "Count as Large for carrying capacity",
                mechanic="powerful_build"),
]

YUAN_TI_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Innate Spellcasting", "Poison Spray cantrip. Animal Friendship (snakes) at will. "
                "Suggestion 1/long rest. CHA-based.",
                mechanic="yuan_ti_spellcasting"),
    RacialTrait("Magic Resistance", "Advantage on saves against spells and magical effects",
                mechanic="magic_resistance"),
    RacialTrait("Poison Immunity", "Immune to poison damage and Poisoned condition",
                mechanic="poison_immunity"),
]

# ============================================================
# SCAG / MORDENKAINEN'S
# ============================================================
DUERGAR_TRAITS = [
    RacialTrait("Superior Darkvision (120ft)", "See in dim light within 120ft",
                mechanic="darkvision", mechanic_value="120"),
    RacialTrait("Duergar Resilience", "Advantage on saves vs illusions, charmed, paralyzed",
                mechanic="duergar_resilience"),
    RacialTrait("Duergar Magic", "Enlarge/Reduce at 3rd, Invisibility at 5th. 1/long rest each.",
                mechanic="duergar_magic"),
    RacialTrait("Sunlight Sensitivity", "Disadvantage on attacks and Perception in sunlight",
                mechanic="sunlight_sensitivity"),
    RacialTrait("Dwarven Resilience", "Advantage on saves vs poison, resistance to poison damage",
                mechanic="dwarven_resilience"),
]

DEEP_GNOME_TRAITS = [
    RacialTrait("Superior Darkvision (120ft)", "See in dim light within 120ft",
                mechanic="darkvision", mechanic_value="120"),
    RacialTrait("Gnome Cunning", "Advantage on INT, WIS, CHA saves against magic",
                mechanic="gnome_cunning"),
    RacialTrait("Stone Camouflage", "Advantage on Stealth in rocky terrain",
                mechanic="stone_camouflage"),
]

ELADRIN_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Trance", "4 hours meditation instead of 8 hours sleep",
                mechanic="trance"),
    RacialTrait("Fey Step", "Bonus action: teleport 30ft. 1/short rest. "
                "Season effect: Spring=charm, Summer=fire, Autumn=charm, Winter=frighten.",
                mechanic="fey_step", uses_per_day=1),
]

SEA_ELF_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Trance", "4 hours meditation instead of 8 hours sleep",
                mechanic="trance"),
    RacialTrait("Sea Elf Training", "Proficiency with spear, trident, light crossbow, net",
                mechanic="sea_elf_training"),
    RacialTrait("Child of the Sea", "Swim speed 30ft, breathe underwater",
                mechanic="child_of_sea"),
    RacialTrait("Friend of the Sea", "Communicate with sea creatures",
                mechanic="friend_of_sea"),
]

SHADAR_KAI_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fey Ancestry", "Advantage on saves vs Charmed, immune to magical sleep",
                mechanic="fey_ancestry"),
    RacialTrait("Trance", "4 hours meditation instead of 8 hours sleep",
                mechanic="trance"),
    RacialTrait("Necrotic Resistance", "Resistance to necrotic damage",
                mechanic="necrotic_resistance"),
    RacialTrait("Blessing of the Raven Queen", "Bonus action: teleport 30ft. "
                "Resistance to all damage until start of next turn. 1/long rest.",
                mechanic="blessing_raven_queen", uses_per_day=1),
]

GITHYANKI_TRAITS = [
    RacialTrait("Githyanki Psionics", "Mage Hand cantrip. Jump at 3rd, Misty Step at 5th. "
                "1/long rest each. INT-based.",
                mechanic="githyanki_psionics"),
    RacialTrait("Martial Prodigy", "Proficiency with light/medium armor, shortswords, "
                "longswords, greatswords.",
                mechanic="martial_prodigy"),
]

GITHZERAI_TRAITS = [
    RacialTrait("Githzerai Psionics", "Mage Hand cantrip. Shield at 3rd, Detect Thoughts at 5th. "
                "1/long rest each. WIS-based.",
                mechanic="githzerai_psionics"),
    RacialTrait("Mental Discipline", "Advantage on saves against charmed and frightened",
                mechanic="mental_discipline"),
]

# ============================================================
# ELEMENTAL EVIL
# ============================================================
AARAKOCRA_TRAITS = [
    RacialTrait("Flight", "Fly speed 50ft. Cannot wear medium or heavy armor.",
                mechanic="flight", mechanic_value="50"),
    RacialTrait("Talons", "Unarmed strike: 1d4+STR slashing",
                mechanic="talons", damage_dice="1d4", damage_type="slashing"),
]

AIR_GENASI_TRAITS = [
    RacialTrait("Unending Breath", "Hold breath indefinitely while not incapacitated",
                mechanic="unending_breath"),
    RacialTrait("Mingle with the Wind", "Levitate 1/long rest. CON-based.",
                mechanic="mingle_wind", uses_per_day=1),
]

EARTH_GENASI_TRAITS = [
    RacialTrait("Earth Walk", "Move across difficult terrain of earth/stone without extra cost",
                mechanic="earth_walk"),
    RacialTrait("Merge with Stone", "Pass without Trace 1/long rest. CON-based.",
                mechanic="merge_stone", uses_per_day=1),
]

FIRE_GENASI_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Fire Resistance", "Resistance to fire damage",
                mechanic="fire_resistance"),
    RacialTrait("Reach to the Blaze", "Produce Flame cantrip. Burning Hands 1/long rest. CON-based.",
                mechanic="reach_blaze"),
]

WATER_GENASI_TRAITS = [
    RacialTrait("Amphibious", "Breathe air and water",
                mechanic="amphibious"),
    RacialTrait("Swim", "Swim speed 30ft",
                mechanic="swim_speed"),
    RacialTrait("Call to the Wave", "Shape Water cantrip. Create/Destroy Water 1/long rest. CON-based.",
                mechanic="call_wave"),
    RacialTrait("Acid Resistance", "Resistance to acid damage",
                mechanic="acid_resistance"),
]

# ============================================================
# EBERRON
# ============================================================
CHANGELING_TRAITS = [
    RacialTrait("Shapechanger", "Action: change appearance (humanoid forms). "
                "Revert on death.",
                mechanic="shapechanger"),
    RacialTrait("Changeling Instincts", "Proficiency in two of: Deception, Insight, "
                "Intimidation, Persuasion",
                mechanic="changeling_instincts"),
]

KALASHTAR_TRAITS = [
    RacialTrait("Dual Mind", "Advantage on WIS saves",
                mechanic="dual_mind"),
    RacialTrait("Mental Discipline", "Resistance to psychic damage",
                mechanic="mental_discipline_kalashtar"),
    RacialTrait("Mind Link", "Telepathy 10x level ft with one creature",
                mechanic="mind_link"),
    RacialTrait("Severed from Dreams", "Immune to dream-based effects, can't be put to sleep",
                mechanic="severed_dreams"),
]

SHIFTER_BEASTHIDE_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Shifting", "Bonus action: gain temp HP = level + CON mod. "
                "+1 AC while shifted. 1 min duration. 1/short rest.",
                mechanic="shifting_beasthide", uses_per_day=1),
    RacialTrait("Natural Athlete", "Proficiency in Athletics",
                mechanic="natural_athlete"),
]

SHIFTER_LONGTOOTH_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Shifting", "Bonus action: gain temp HP = level + CON mod. "
                "Bonus action bite: 1d6+STR piercing. 1 min. 1/short rest.",
                mechanic="shifting_longtooth", uses_per_day=1),
    RacialTrait("Fierce", "Proficiency in Intimidation",
                mechanic="fierce"),
]

SHIFTER_SWIFTSTRIDE_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Shifting", "Bonus action: gain temp HP = level + CON mod. "
                "+10ft speed while shifted. 1 min. 1/short rest.",
                mechanic="shifting_swiftstride", uses_per_day=1),
    RacialTrait("Graceful", "Proficiency in Acrobatics",
                mechanic="graceful"),
]

SHIFTER_WILDHUNT_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Shifting", "Bonus action: gain temp HP = level + CON mod. "
                "No creature within 30ft can have advantage on you. 1 min. 1/short rest.",
                mechanic="shifting_wildhunt", uses_per_day=1),
    RacialTrait("Natural Tracker", "Proficiency in Survival",
                mechanic="natural_tracker"),
]

WARFORGED_TRAITS = [
    RacialTrait("Constructed Resilience", "Advantage on saves vs poison, resistance to poison. "
                "No need to eat, drink, breathe, or sleep. Immune to disease.",
                mechanic="constructed_resilience"),
    RacialTrait("Sentry's Rest", "Inactive but conscious during 6-hour long rest",
                mechanic="sentrys_rest"),
    RacialTrait("Integrated Protection", "+1 AC bonus. Can don/doff armor in 1 hour.",
                mechanic="integrated_protection"),
]

# ============================================================
# RAVNICA
# ============================================================
CENTAUR_TRAITS = [
    RacialTrait("Fey", "Creature type is Fey, not Humanoid",
                mechanic="fey_type"),
    RacialTrait("Charge", "If you move 30ft+ straight toward target, bonus action: "
                "hooves attack for 1d4+STR bludgeoning.",
                mechanic="charge", damage_dice="1d4", damage_type="bludgeoning"),
    RacialTrait("Hooves", "Natural weapon: 1d4+STR bludgeoning",
                mechanic="hooves", damage_dice="1d4", damage_type="bludgeoning"),
    RacialTrait("Equine Build", "Count as one size larger. Climb costs extra movement.",
                mechanic="equine_build"),
]

LOXODON_TRAITS = [
    RacialTrait("Powerful Build", "Count as Large for carrying capacity",
                mechanic="powerful_build"),
    RacialTrait("Loxodon Serenity", "Advantage on saves vs charmed and frightened",
                mechanic="loxodon_serenity"),
    RacialTrait("Natural Armor", "AC = 12 + CON when not wearing armor",
                mechanic="natural_armor_loxodon"),
    RacialTrait("Trunk", "Grapple, lift (5x STR lbs), interact with objects",
                mechanic="trunk"),
    RacialTrait("Keen Smell", "Advantage on Perception, Investigation, Survival using smell",
                mechanic="keen_smell"),
]

MINOTAUR_TRAITS = [
    RacialTrait("Horns", "Natural weapon: 1d6+STR piercing",
                mechanic="horns", damage_dice="1d6", damage_type="piercing"),
    RacialTrait("Goring Rush", "Dash action: bonus action horn attack",
                mechanic="goring_rush"),
    RacialTrait("Hammering Horns", "After melee hit: bonus action shove 10ft (STR save)",
                mechanic="hammering_horns"),
    RacialTrait("Imposing Presence", "Proficiency in Intimidation or Persuasion",
                mechanic="imposing_presence"),
]

SIMIC_HYBRID_TRAITS = [
    RacialTrait("Darkvision (60ft)", "See in dim light within 60ft",
                mechanic="darkvision", mechanic_value="60"),
    RacialTrait("Animal Enhancement (1st)", "Manta Glide, Nimble Climber, or "
                "Underwater Adaptation at 1st level.",
                mechanic="animal_enhancement_1"),
    RacialTrait("Animal Enhancement (5th)", "Grappling Appendages (1d6+STR), Carapace (+1 AC), "
                "or Acid Spit (2d10 acid, 30ft) at 5th level.",
                mechanic="animal_enhancement_5"),
]

VEDALKEN_TRAITS = [
    RacialTrait("Vedalken Dispassion", "Advantage on INT, WIS, CHA saves",
                mechanic="vedalken_dispassion"),
    RacialTrait("Tireless Precision", "Proficiency with one tool and one skill of choice. "
                "Add 1d4 to checks with those.",
                mechanic="tireless_precision"),
    RacialTrait("Partially Amphibious", "Breathe underwater for 1 hour, then 1 hour surface rest",
                mechanic="partially_amphibious"),
]

# ============================================================
# TORTLE PACKAGE
# ============================================================
TORTLE_TRAITS = [
    RacialTrait("Claws", "Natural weapon: 1d4+STR slashing",
                mechanic="claws", damage_dice="1d4", damage_type="slashing"),
    RacialTrait("Hold Breath", "Hold breath for 1 hour",
                mechanic="hold_breath"),
    RacialTrait("Natural Armor", "AC = 17 (can't wear armor). Shield still works.",
                mechanic="natural_armor_tortle"),
    RacialTrait("Shell Defense", "Action: withdraw into shell. +4 AC, advantage on STR/CON "
                "saves, but prone, speed 0, disadvantage on DEX saves.",
                mechanic="shell_defense"),
    RacialTrait("Survival Instinct", "Proficiency in Survival",
                mechanic="survival_instinct"),
]


# ============================================================
# MASTER MAP
# ============================================================
RACE_TRAITS_MAP = {
    # PHB
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
    # Volo's Guide
    "Aasimar (Protector)": AASIMAR_PROTECTOR_TRAITS,
    "Aasimar (Scourge)": AASIMAR_SCOURGE_TRAITS,
    "Aasimar (Fallen)": AASIMAR_FALLEN_TRAITS,
    "Firbolg": FIRBOLG_TRAITS,
    "Goliath": GOLIATH_TRAITS,
    "Kenku": KENKU_TRAITS,
    "Lizardfolk": LIZARDFOLK_TRAITS,
    "Tabaxi": TABAXI_TRAITS,
    "Triton": TRITON_TRAITS,
    "Bugbear": BUGBEAR_TRAITS,
    "Goblin": GOBLIN_TRAITS,
    "Hobgoblin": HOBGOBLIN_TRAITS,
    "Kobold": KOBOLD_TRAITS,
    "Orc": ORC_TRAITS,
    "Yuan-ti Pureblood": YUAN_TI_TRAITS,
    # SCAG / Mordenkainen's
    "Duergar": DUERGAR_TRAITS,
    "Deep Gnome": DEEP_GNOME_TRAITS,
    "Eladrin": ELADRIN_TRAITS,
    "Sea Elf": SEA_ELF_TRAITS,
    "Shadar-kai": SHADAR_KAI_TRAITS,
    "Githyanki": GITHYANKI_TRAITS,
    "Githzerai": GITHZERAI_TRAITS,
    # Elemental Evil
    "Aarakocra": AARAKOCRA_TRAITS,
    "Air Genasi": AIR_GENASI_TRAITS,
    "Earth Genasi": EARTH_GENASI_TRAITS,
    "Fire Genasi": FIRE_GENASI_TRAITS,
    "Water Genasi": WATER_GENASI_TRAITS,
    # Eberron
    "Changeling": CHANGELING_TRAITS,
    "Kalashtar": KALASHTAR_TRAITS,
    "Shifter (Beasthide)": SHIFTER_BEASTHIDE_TRAITS,
    "Shifter (Longtooth)": SHIFTER_LONGTOOTH_TRAITS,
    "Shifter (Swiftstride)": SHIFTER_SWIFTSTRIDE_TRAITS,
    "Shifter (Wildhunt)": SHIFTER_WILDHUNT_TRAITS,
    "Warforged": WARFORGED_TRAITS,
    # Ravnica
    "Centaur": CENTAUR_TRAITS,
    "Loxodon": LOXODON_TRAITS,
    "Minotaur": MINOTAUR_TRAITS,
    "Simic Hybrid": SIMIC_HYBRID_TRAITS,
    "Vedalken": VEDALKEN_TRAITS,
    # Tortle Package
    "Tortle": TORTLE_TRAITS,
}


def get_racial_traits(race: str) -> list[RacialTrait]:
    """Get all racial traits for a given race."""
    return list(RACE_TRAITS_MAP.get(race, []))


# ============================================================
# RACE SPEED TABLE (All races)
# ============================================================
RACE_SPEED = {
    # PHB
    "Human": 30, "Variant Human": 30, "High Elf": 30, "Wood Elf": 35, "Drow": 30,
    "Hill Dwarf": 25, "Mountain Dwarf": 25, "Lightfoot Halfling": 25,
    "Stout Halfling": 25, "Half-Orc": 30, "Half-Elf": 30,
    "Rock Gnome": 25, "Forest Gnome": 25, "Dragonborn": 30, "Tiefling": 30,
    # Volo's
    "Aasimar (Protector)": 30, "Aasimar (Scourge)": 30, "Aasimar (Fallen)": 30,
    "Firbolg": 30, "Goliath": 30, "Kenku": 30, "Lizardfolk": 30,
    "Tabaxi": 30, "Triton": 30, "Bugbear": 30, "Goblin": 30,
    "Hobgoblin": 30, "Kobold": 30, "Orc": 30, "Yuan-ti Pureblood": 30,
    # SCAG/Mordenkainen's
    "Duergar": 25, "Deep Gnome": 25, "Eladrin": 30, "Sea Elf": 30,
    "Shadar-kai": 30, "Githyanki": 30, "Githzerai": 30,
    # Elemental Evil
    "Aarakocra": 25, "Air Genasi": 30, "Earth Genasi": 30,
    "Fire Genasi": 30, "Water Genasi": 30,
    # Eberron
    "Changeling": 30, "Kalashtar": 30, "Shifter (Beasthide)": 30,
    "Shifter (Longtooth)": 30, "Shifter (Swiftstride)": 30,
    "Shifter (Wildhunt)": 30, "Warforged": 30,
    # Ravnica
    "Centaur": 40, "Loxodon": 30, "Minotaur": 30, "Simic Hybrid": 30, "Vedalken": 30,
    # Tortle
    "Tortle": 30,
}


# ============================================================
# RACE SIZE TABLE (All races)
# ============================================================
RACE_SIZE = {
    # PHB - all Medium except halflings/gnomes
    "Lightfoot Halfling": "Small", "Stout Halfling": "Small",
    "Rock Gnome": "Small", "Forest Gnome": "Small", "Deep Gnome": "Small",
    "Goblin": "Small", "Kobold": "Small",
    # All others default Medium
}


def get_race_size(race: str) -> str:
    """Get size for a race. Default Medium."""
    return RACE_SIZE.get(race, "Medium")


# ============================================================
# Ordered lists for hero creator UI - grouped by source book
# ============================================================
RACE_LIST_GROUPED = {
    "PHB": [
        "Human", "Variant Human", "High Elf", "Wood Elf", "Drow",
        "Hill Dwarf", "Mountain Dwarf", "Lightfoot Halfling", "Stout Halfling",
        "Half-Orc", "Half-Elf", "Rock Gnome", "Forest Gnome", "Dragonborn", "Tiefling",
    ],
    "Volo's Guide": [
        "Aasimar (Protector)", "Aasimar (Scourge)", "Aasimar (Fallen)",
        "Firbolg", "Goliath", "Kenku", "Lizardfolk", "Tabaxi", "Triton",
        "Bugbear", "Goblin", "Hobgoblin", "Kobold", "Orc", "Yuan-ti Pureblood",
    ],
    "SCAG / Mordenkainen's": [
        "Duergar", "Deep Gnome", "Eladrin", "Sea Elf", "Shadar-kai",
        "Githyanki", "Githzerai",
    ],
    "Elemental Evil": [
        "Aarakocra", "Air Genasi", "Earth Genasi", "Fire Genasi", "Water Genasi",
    ],
    "Eberron": [
        "Changeling", "Kalashtar", "Shifter (Beasthide)", "Shifter (Longtooth)",
        "Shifter (Swiftstride)", "Shifter (Wildhunt)", "Warforged",
    ],
    "Ravnica": [
        "Centaur", "Loxodon", "Minotaur", "Simic Hybrid", "Vedalken",
    ],
    "Other": [
        "Tortle",
    ],
}

# Flat list of all races (for dropdown)
ALL_RACES = []
for _races in RACE_LIST_GROUPED.values():
    ALL_RACES.extend(_races)
