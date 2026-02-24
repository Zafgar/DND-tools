from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo, Item, RacialTrait
from data.spells import get_spell
from data.racial_traits import get_racial_traits

# ============================================================================
# D&D 5e 2014 Pre-built Heroes (Level 10)
# Each hero has proper class features with mechanic keys so the AI knows
# exactly how to use Rage, Sneak Attack, Divine Smite, Hunter's Mark, etc.
# ============================================================================

hero_list = [
    # ====================================================================
    # BARBARIAN (Totem Warrior - Bear) - Level 10 - Half-Orc
    # ====================================================================
    CreatureStats(
        name="Grukk Barbarian",
        character_class="Barbarian", character_level=10, race="Half-Orc",
        subclass="Totem Warrior",
        hit_points=115, armor_class=17, speed=40, hit_dice="10d12+30",
        # AC = 10 + DEX(2) + CON(3) + Shield(2) = 17
        abilities=AbilityScores(strength=20, dexterity=14, constitution=16,
                                intelligence=8, wisdom=12, charisma=10),
        actions=[
            Action("Multiattack", "2 attacks", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Greataxe", "Greataxe"]),
            Action("Greataxe", "Melee", 9, "1d12", 5, "slashing"),
            Action("Javelin", "Ranged", 9, "1d6", 5, "piercing", range=30),
        ],
        features=[
            Feature("Rage", "Bonus action: resistance to B/P/S, +3 melee damage, "
                    "advantage on STR checks/saves. Must attack or take damage each turn.",
                    feature_type="class", uses_per_day=4, mechanic="rage"),
            Feature("Rage Damage +3", "+3 melee damage while raging",
                    feature_type="class", mechanic="rage_damage", mechanic_value="3"),
            Feature("Reckless Attack", "First attack: advantage on melee STR attacks, "
                    "but attacks against you have advantage.",
                    feature_type="class", mechanic="reckless_attack"),
            Feature("Danger Sense", "Advantage on DEX saves you can see",
                    feature_type="class", mechanic="danger_sense"),
            Feature("Totem Spirit: Bear", "While raging, resistance to all damage except psychic",
                    feature_type="class", mechanic="totem_bear"),
            Feature("Extra Attack", "2 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Fast Movement", "+10 ft speed",
                    feature_type="class", mechanic="fast_movement"),
            Feature("Feral Instinct", "Advantage on initiative",
                    feature_type="class", mechanic="feral_instinct"),
            Feature("Brutal Critical", "Roll 1 extra weapon die on crit",
                    feature_type="class", mechanic="brutal_critical", mechanic_value="1"),
            Feature("Unarmored Defense (Barbarian)", "AC = 10 + DEX + CON",
                    feature_type="class", mechanic="unarmored_defense_barbarian"),
        ],
        racial_traits=get_racial_traits("Half-Orc"),
        rage_count=4,
        saving_throws={"Strength": 9, "Constitution": 7},
        skills={"Athletics": 9, "Intimidation": 4, "Perception": 5, "Survival": 5},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # FIGHTER (Champion) - Level 10 - Human
    # ====================================================================
    CreatureStats(
        name="Veteran Fighter",
        character_class="Fighter", character_level=10, race="Human",
        subclass="Champion",
        hit_points=94, armor_class=18, speed=30, hit_dice="10d10+30",
        abilities=AbilityScores(strength=18, dexterity=14, constitution=16,
                                intelligence=10, wisdom=12, charisma=10),
        actions=[
            Action("Multiattack", "3 attacks", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Longsword", "Longsword", "Longsword"]),
            Action("Longsword", "Melee", 8, "1d8", 4, "slashing"),
            Action("Shield Bash", "Melee", 8, "1d4", 4, "bludgeoning",
                   applies_condition="Prone", condition_dc=16, condition_save="Strength"),
            Action("Heavy Crossbow", "Ranged", 6, "1d10", 2, "piercing", range=100),
        ],
        features=[
            Feature("Action Surge", "Take one additional action. 1/short rest.",
                    feature_type="class", uses_per_day=1, mechanic="action_surge",
                    short_rest_recharge=True),
            Feature("Second Wind", "Bonus action: heal 1d10+10 HP. 1/short rest.",
                    feature_type="class", uses_per_day=1, mechanic="second_wind",
                    mechanic_value="1d10+10", short_rest_recharge=True),
            Feature("Indomitable", "Re-roll a failed save. 2/long rest.",
                    feature_type="class", uses_per_day=2, mechanic="indomitable"),
            Feature("Improved Critical", "Critical hit on 19-20",
                    feature_type="class", mechanic="improved_critical"),
            Feature("Extra Attack (2)", "3 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack_2"),
            Feature("Fighting Style: Defense", "+1 AC when wearing armor",
                    feature_type="class", mechanic="fighting_style"),
        ],
        racial_traits=get_racial_traits("Human"),
        saving_throws={"Strength": 8, "Constitution": 7},
        skills={"Athletics": 8, "Intimidation": 4, "Perception": 5},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # PALADIN (Oath of Devotion) - Level 10 - Human
    # ====================================================================
    CreatureStats(
        name="Holy Paladin",
        character_class="Paladin", character_level=10, race="Human",
        subclass="Devotion",
        hit_points=85, armor_class=20, speed=30, hit_dice="10d10+20",
        abilities=AbilityScores(strength=18, dexterity=10, constitution=14,
                                intelligence=10, wisdom=12, charisma=18),
        actions=[
            Action("Multiattack", "2 attacks", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Longsword", "Longsword"]),
            Action("Longsword", "Melee", 8, "1d8", 4, "slashing"),
        ],
        features=[
            Feature("Divine Smite", "On melee hit: expend spell slot for 2d8 radiant "
                    "(+1d8 per slot level above 1st, +1d8 vs undead/fiend). Max 5d8.",
                    feature_type="class", mechanic="divine_smite"),
            Feature("Improved Divine Smite", "All melee weapon hits deal +1d8 radiant",
                    feature_type="class", mechanic="improved_divine_smite"),
            Feature("Lay on Hands", "Touch: heal from 50 HP pool",
                    feature_type="class", uses_per_day=1, mechanic="lay_on_hands",
                    mechanic_value="50"),
            Feature("Aura of Protection", "You + allies within 10ft: +4 to all saves",
                    feature_type="class", mechanic="aura_of_protection", aura_radius=10),
            Feature("Aura of Courage", "You + allies within 10ft: immune to Frightened",
                    feature_type="class", mechanic="aura_of_courage", aura_radius=10),
            Feature("Channel Divinity", "1/short rest", feature_type="class",
                    uses_per_day=1, mechanic="channel_divinity",
                    short_rest_recharge=True),
            Feature("Extra Attack", "2 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack"),
        ],
        racial_traits=get_racial_traits("Human"),
        lay_on_hands_pool=50,
        spellcasting_ability="Charisma", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 2},
        spells_known=[
            get_spell("Bless"),
            get_spell("Divine Favor"),
            get_spell("Shield of Faith"),
            get_spell("Cure Wounds"),
            get_spell("Revivify"),
        ],
        saving_throws={"Wisdom": 8, "Charisma": 8},
        skills={"Athletics": 8, "Insight": 5, "Persuasion": 8},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # WIZARD (Evocation) - Level 10 - High Elf
    # ====================================================================
    CreatureStats(
        name="Arcane Wizard",
        character_class="Wizard", character_level=10, race="High Elf",
        subclass="Evocation",
        hit_points=52, armor_class=13, speed=30, hit_dice="10d6+10",
        abilities=AbilityScores(strength=8, dexterity=16, constitution=12,
                                intelligence=20, wisdom=14, charisma=10),
        actions=[
            Action("Quarterstaff", "Melee", 3, "1d6", -1, "bludgeoning"),
        ],
        spellcasting_ability="Intelligence", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        spells_known=[
            get_spell("Fireball"),
            get_spell("Cone of Cold"),
            get_spell("Hold Person"),
            get_spell("Lightning Bolt"),
            get_spell("Magic Missile"),
            get_spell("Shield"),
            get_spell("Counterspell"),
            get_spell("Misty Step"),
            get_spell("Banishment"),
            get_spell("Wall of Fire"),
            get_spell("Mage Armor"),
        ],
        cantrips=[
            get_spell("Fire Bolt", attack_bonus_fixed=9),
            get_spell("Chill Touch", attack_bonus_fixed=9),
            get_spell("Ray of Frost", attack_bonus_fixed=9),
            get_spell("Shocking Grasp", attack_bonus_fixed=9),
        ],
        features=[
            Feature("Arcane Recovery", "Short rest: recover up to 5 levels of spell slots. 1/day.",
                    feature_type="class", uses_per_day=1, mechanic="arcane_recovery",
                    short_rest_recharge=False),
            Feature("Sculpt Spells", "Evocation AoE: choose 1+spell level creatures to auto-save "
                    "and take no damage.",
                    feature_type="class", mechanic="sculpt_spells"),
            Feature("Empowered Evocation", "Add INT mod (+5) to evocation spell damage",
                    feature_type="class", mechanic="empowered_evocation"),
        ],
        racial_traits=get_racial_traits("High Elf"),
        saving_throws={"Intelligence": 9, "Wisdom": 6},
        skills={"Arcana": 13, "History": 9, "Investigation": 9},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # CLERIC (War Domain) - Level 10 - Hill Dwarf
    # ====================================================================
    CreatureStats(
        name="War Cleric",
        character_class="Cleric", character_level=10, race="Hill Dwarf",
        subclass="War",
        hit_points=86, armor_class=18, speed=25, hit_dice="10d8+30",
        # Hill Dwarf: +1 HP per level = +10
        abilities=AbilityScores(strength=14, dexterity=10, constitution=16,
                                intelligence=10, wisdom=18, charisma=14),
        actions=[
            Action("Multiattack", "2 attacks", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Warhammer", "Warhammer"]),
            Action("Warhammer", "Melee", 6, "1d8", 2, "bludgeoning"),
        ],
        bonus_actions=[
            Action("War Priest Strike", description="Bonus weapon attack",
                   action_type="bonus", attack_bonus=6, damage_dice="1d8",
                   damage_bonus=2, damage_type="bludgeoning"),
        ],
        spellcasting_ability="Wisdom", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        spells_known=[
            get_spell("Cure Wounds"),
            get_spell("Mass Cure Wounds"),
            get_spell("Healing Word"),
            get_spell("Guiding Bolt", attack_bonus_fixed=8),
            get_spell("Sacred Flame"),
            get_spell("Spirit Guardians"),
            get_spell("Banishment"),
            get_spell("Hold Person"),
            get_spell("Spiritual Weapon"),
            get_spell("Flame Strike"),
        ],
        features=[
            Feature("Channel Divinity: Turn Undead",
                    "Undead within 30ft: WIS save or flee 1 min",
                    feature_type="class", uses_per_day=2, mechanic="channel_divinity",
                    short_rest_recharge=True),
            Feature("Channel Divinity: Guided Strike", "+10 to one attack roll",
                    feature_type="class", mechanic="guided_strike"),
            Feature("War Priest", "Bonus weapon attack after Attack action. WIS mod/long rest.",
                    feature_type="class", uses_per_day=4, mechanic="war_priest"),
            Feature("Divine Strike", "+1d8 weapon damage once per turn",
                    feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
            Feature("Divine Intervention", "Percentage roll <= 10 for divine aid",
                    feature_type="class", uses_per_day=1, mechanic="divine_intervention"),
        ],
        racial_traits=get_racial_traits("Hill Dwarf"),
        saving_throws={"Wisdom": 8, "Charisma": 6},
        skills={"Insight": 8, "Medicine": 8, "Persuasion": 6},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # ROGUE (Assassin) - Level 10 - Lightfoot Halfling
    # ====================================================================
    CreatureStats(
        name="Shadow Rogue",
        character_class="Rogue", character_level=10, race="Lightfoot Halfling",
        subclass="Assassin",
        hit_points=66, armor_class=16, speed=25, hit_dice="10d8+20",
        abilities=AbilityScores(strength=10, dexterity=20, constitution=14,
                                intelligence=14, wisdom=12, charisma=12),
        actions=[
            Action("Multiattack", "2 attacks", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Rapier", "Rapier"]),
            Action("Rapier", "Melee finesse", 9, "1d8", 5, "piercing"),
            Action("Hand Crossbow", "Ranged", 9, "1d6", 5, "piercing", range=30),
        ],
        features=[
            Feature("Sneak Attack", "Once per turn: +5d6 damage when advantage or "
                    "ally adjacent to target. Finesse/ranged weapon required.",
                    feature_type="class", mechanic="sneak_attack", mechanic_value="5d6"),
            Feature("Cunning Action", "Bonus action: Dash, Disengage, or Hide",
                    feature_type="class", mechanic="cunning_action"),
            Feature("Uncanny Dodge", "Reaction: halve damage from an attack you can see",
                    feature_type="class", mechanic="uncanny_dodge"),
            Feature("Evasion", "DEX save success: no damage. Fail: half damage.",
                    feature_type="class", mechanic="evasion"),
            Feature("Assassinate", "Advantage on attacks vs creatures that haven't acted. "
                    "Auto-crit on surprised creatures.",
                    feature_type="class", mechanic="assassinate"),
        ],
        racial_traits=get_racial_traits("Lightfoot Halfling"),
        saving_throws={"Dexterity": 9, "Intelligence": 6},
        skills={"Acrobatics": 9, "Deception": 5, "Perception": 9,
                "Sleight of Hand": 9, "Stealth": 13},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # RANGER (Hunter) - Level 10 - Wood Elf
    # ====================================================================
    CreatureStats(
        name="Elven Ranger",
        character_class="Ranger", character_level=10, race="Wood Elf",
        subclass="Hunter",
        hit_points=74, armor_class=16, speed=35, hit_dice="10d10+10",
        abilities=AbilityScores(strength=12, dexterity=18, constitution=13,
                                intelligence=12, wisdom=16, charisma=11),
        actions=[
            Action("Multiattack", "3 Longbow or 2 Shortsword", 0, "", 0, "",
                   range=150, is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Longbow", "Longbow", "Longbow"]),
            Action("Longbow", "Ranged", 8, "1d8", 4, "piercing", range=150),
            Action("Shortsword", "Melee finesse", 8, "1d6", 4, "piercing"),
        ],
        spellcasting_ability="Wisdom", spell_save_dc=15, spell_attack_bonus=7,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 2},
        spells_known=[
            get_spell("Hunter's Mark"),
            get_spell("Hail of Thorns"),
            get_spell("Cure Wounds"),
        ],
        features=[
            Feature("Colossus Slayer", "Once per turn: +1d8 damage against a creature "
                    "below its HP maximum.",
                    feature_type="class", mechanic="colossus_slayer", mechanic_value="1d8"),
            Feature("Extra Attack", "2 attacks per Attack action (3 with multiattack subclass)",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Favored Enemy", "Advantage on Survival to track, INT to recall info",
                    feature_type="class", mechanic="favored_enemy"),
            Feature("Natural Explorer", "Difficult terrain doesn't slow group in favored terrain",
                    feature_type="class", mechanic="natural_explorer"),
            Feature("Multiattack Defense", "+4 AC after being hit (vs that creature this turn)",
                    feature_type="class", mechanic="multiattack_defense"),
        ],
        racial_traits=get_racial_traits("Wood Elf"),
        saving_throws={"Strength": 5, "Dexterity": 8},
        skills={"Animal Handling": 7, "Nature": 5, "Perception": 11,
                "Stealth": 8, "Survival": 11},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # WARLOCK (Fiend Pact) - Level 10 - Tiefling
    # ====================================================================
    CreatureStats(
        name="Fiend Warlock",
        character_class="Warlock", character_level=10, race="Tiefling",
        subclass="Fiend",
        hit_points=63, armor_class=14, speed=30, hit_dice="10d8+10",
        # Studded leather + DEX
        abilities=AbilityScores(strength=8, dexterity=14, constitution=12,
                                intelligence=12, wisdom=10, charisma=20),
        actions=[
            Action("Dagger", "Melee finesse", 6, "1d4", 2, "piercing"),
        ],
        spellcasting_ability="Charisma", spell_save_dc=17, spell_attack_bonus=9,
        # Warlock: 2 slots at 5th level (Pact Magic), recharge on short rest
        spell_slots={"5th": 2},
        spells_known=[
            get_spell("Hex"),
            get_spell("Hellish Rebuke"),
            get_spell("Hold Person"),
            get_spell("Counterspell"),
            get_spell("Banishment"),
            get_spell("Fireball"),  # Fiend expanded spell
            get_spell("Scorching Ray"),
        ],
        cantrips=[
            get_spell("Eldritch Blast", attack_bonus_fixed=9),
            get_spell("Chill Touch", attack_bonus_fixed=9),
            get_spell("Mage Hand"),
        ],
        features=[
            Feature("Agonizing Blast", "Add CHA mod (+5) to each Eldritch Blast beam",
                    feature_type="class", mechanic="agonizing_blast"),
            Feature("Pact Magic", "2 spell slots (5th level), recharge on short rest",
                    feature_type="class", mechanic="pact_magic",
                    short_rest_recharge=True),
            Feature("Dark One's Blessing", "When you reduce a hostile to 0 HP, "
                    "gain CHA mod + warlock level temp HP.",
                    feature_type="class", mechanic="dark_ones_blessing"),
            Feature("Dark One's Own Luck", "Add d10 to ability check or save. 1/short rest.",
                    feature_type="class", uses_per_day=1, mechanic="dark_ones_own_luck",
                    short_rest_recharge=True),
        ],
        racial_traits=get_racial_traits("Tiefling"),
        damage_resistances=["fire"],  # Tiefling + Fiend
        saving_throws={"Wisdom": 4, "Charisma": 9},
        skills={"Arcana": 5, "Deception": 9, "Intimidation": 9, "Persuasion": 9},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # SORCERER (Draconic Bloodline - Fire) - Level 10 - Half-Elf
    # ====================================================================
    CreatureStats(
        name="Draconic Sorcerer",
        character_class="Sorcerer", character_level=10, race="Half-Elf",
        subclass="Draconic Bloodline",
        hit_points=72, armor_class=16, speed=30, hit_dice="10d6+20",
        # Draconic Resilience: 13 + DEX(3) = 16 AC, +1 HP/level
        abilities=AbilityScores(strength=8, dexterity=16, constitution=14,
                                intelligence=10, wisdom=12, charisma=20),
        actions=[
            Action("Dagger", "Melee/Ranged", 7, "1d4", 3, "piercing", range=20),
        ],
        spellcasting_ability="Charisma", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        sorcery_points=10,
        spells_known=[
            get_spell("Fireball"),
            get_spell("Scorching Ray"),
            get_spell("Shield"),
            get_spell("Misty Step"),
            get_spell("Counterspell"),
            get_spell("Haste"),
            get_spell("Greater Invisibility"),
            get_spell("Wall of Fire"),
        ],
        cantrips=[
            get_spell("Fire Bolt", attack_bonus_fixed=9),
            get_spell("Ray of Frost", attack_bonus_fixed=9),
            get_spell("Shocking Grasp", attack_bonus_fixed=9),
            get_spell("Mage Hand"),
        ],
        features=[
            Feature("Draconic Resilience", "AC = 13 + DEX when unarmored. +1 HP per level.",
                    feature_type="class", mechanic="draconic_resilience"),
            Feature("Elemental Affinity (Fire)", "Add CHA mod (+5) to fire spell damage. "
                    "Spend 1 sorcery point for 1 hour fire resistance.",
                    feature_type="class", mechanic="elemental_affinity"),
            Feature("Metamagic: Twinned Spell", "Spend sorcery points = spell level to "
                    "target two creatures with single-target spell.",
                    feature_type="class", mechanic="twinned_spell"),
            Feature("Metamagic: Quickened Spell", "Spend 2 sorcery points: cast action "
                    "spell as bonus action.",
                    feature_type="class", mechanic="quickened_spell"),
            Feature("Font of Magic", "Convert sorcery points <-> spell slots",
                    feature_type="class", mechanic="font_of_magic"),
        ],
        racial_traits=get_racial_traits("Half-Elf"),
        damage_resistances=["fire"],  # Draconic ancestry
        saving_throws={"Constitution": 6, "Charisma": 9},
        skills={"Arcana": 4, "Deception": 9, "Persuasion": 9, "Insight": 5},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # BARD (College of Lore) - Level 10 - Half-Elf
    # ====================================================================
    CreatureStats(
        name="Lore Bard",
        character_class="Bard", character_level=10, race="Half-Elf",
        subclass="College of Lore",
        hit_points=63, armor_class=15, speed=30, hit_dice="10d8+10",
        # Studded leather + DEX
        abilities=AbilityScores(strength=8, dexterity=16, constitution=12,
                                intelligence=14, wisdom=12, charisma=20),
        actions=[
            Action("Rapier", "Melee finesse", 7, "1d8", 3, "piercing"),
        ],
        spellcasting_ability="Charisma", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        bardic_inspiration_dice="1d10", bardic_inspiration_count=5,
        spells_known=[
            get_spell("Healing Word"),
            get_spell("Dissonant Whispers"),
            get_spell("Tasha's Hideous Laughter"),
            get_spell("Hold Person"),
            get_spell("Shatter"),
            get_spell("Counterspell"),  # Magical Secrets
            get_spell("Fireball"),      # Magical Secrets
            get_spell("Greater Invisibility"),
            get_spell("Mass Cure Wounds"),
        ],
        cantrips=[
            get_spell("Vicious Mockery"),
            get_spell("Mage Hand"),
        ],
        features=[
            Feature("Bardic Inspiration", "Bonus action: ally adds d10 to attack/check/save. "
                    "CHA mod uses, recharges on short rest.",
                    feature_type="class", mechanic="bardic_inspiration",
                    mechanic_value="1d10", short_rest_recharge=True),
            Feature("Cutting Words", "Reaction: subtract d10 from enemy attack/check/damage "
                    "within 60ft. Uses Bardic Inspiration die.",
                    feature_type="class", mechanic="cutting_words"),
            Feature("Jack of All Trades", "Add half proficiency (+2) to non-proficient checks",
                    feature_type="class", mechanic="jack_of_all_trades"),
            Feature("Song of Rest", "Short rest: allies regain extra 1d8 HP",
                    feature_type="class", mechanic="song_of_rest", mechanic_value="1d8"),
            Feature("Countercharm", "Action: allies within 30ft advantage vs charm/fear",
                    feature_type="class", mechanic="countercharm"),
            Feature("Magical Secrets", "Learned Counterspell and Fireball from other classes",
                    feature_type="class", mechanic="magical_secrets"),
        ],
        racial_traits=get_racial_traits("Half-Elf"),
        saving_throws={"Dexterity": 7, "Charisma": 9},
        skills={"Acrobatics": 7, "Arcana": 6, "Deception": 9, "History": 6,
                "Insight": 5, "Perception": 5, "Performance": 9, "Persuasion": 9},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # DRUID (Circle of the Moon) - Level 10 - Wood Elf
    # ====================================================================
    CreatureStats(
        name="Moon Druid",
        character_class="Druid", character_level=10, race="Wood Elf",
        subclass="Circle of the Moon",
        hit_points=63, armor_class=16, speed=35, hit_dice="10d8+10",
        # Hide armor + shield + DEX or natural
        abilities=AbilityScores(strength=10, dexterity=14, constitution=12,
                                intelligence=12, wisdom=20, charisma=10),
        actions=[
            Action("Scimitar", "Melee", 6, "1d6", 2, "slashing"),
            Action("Produce Flame", "Ranged spell", 9, "2d8", 0, "fire", range=30),
        ],
        spellcasting_ability="Wisdom", spell_save_dc=17, spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        spells_known=[
            get_spell("Cure Wounds"),
            get_spell("Healing Word"),
            get_spell("Entangle"),
            get_spell("Call Lightning"),
            get_spell("Moonbeam"),
            get_spell("Conjure Animals"),  # placeholder
            get_spell("Wall of Fire"),
        ],
        cantrips=[
            get_spell("Poison Spray"),
        ],
        features=[
            Feature("Wild Shape", "Bonus action: transform into beast (CR 3 max at Moon 10). "
                    "2/short rest.",
                    feature_type="class", uses_per_day=2, mechanic="wild_shape",
                    short_rest_recharge=True),
            Feature("Combat Wild Shape", "Wild Shape as bonus action. Spend spell slots to "
                    "heal in beast form (1d8 per slot level).",
                    feature_type="class", mechanic="combat_wild_shape"),
            Feature("Primal Strike", "Beast form attacks count as magical",
                    feature_type="class", mechanic="primal_strike"),
            Feature("Elemental Wild Shape", "Spend 2 Wild Shape uses to become an elemental",
                    feature_type="class", mechanic="elemental_wild_shape"),
        ],
        racial_traits=get_racial_traits("Wood Elf"),
        saving_throws={"Intelligence": 5, "Wisdom": 9},
        skills={"Animal Handling": 9, "Insight": 9, "Medicine": 9,
                "Nature": 5, "Perception": 9},
        challenge_rating=5.0, proficiency_bonus=4,
    ),

    # ====================================================================
    # MONK (Way of the Open Hand) - Level 10 - Wood Elf
    # ====================================================================
    CreatureStats(
        name="Open Hand Monk",
        character_class="Monk", character_level=10, race="Wood Elf",
        subclass="Way of the Open Hand",
        hit_points=63, armor_class=18, speed=55, hit_dice="10d8+10",
        # Unarmored Defense: 10 + DEX(4) + WIS(4) = 18
        # Speed: 35 (elf) + 20 (monk 10) = 55
        abilities=AbilityScores(strength=10, dexterity=18, constitution=12,
                                intelligence=10, wisdom=18, charisma=8),
        actions=[
            Action("Multiattack", "2 attacks + bonus unarmed/flurry", 0, "", 0, "",
                   range=5, is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Unarmed Strike", "Unarmed Strike"]),
            Action("Unarmed Strike", "Melee", 8, "1d8", 4, "bludgeoning"),
            Action("Dart", "Ranged", 8, "1d4", 4, "piercing", range=20),
        ],
        bonus_actions=[
            Action("Bonus Unarmed Strike", "Martial Arts bonus attack",
                   action_type="bonus", attack_bonus=8, damage_dice="1d8",
                   damage_bonus=4, damage_type="bludgeoning"),
        ],
        features=[
            Feature("Martial Arts", "Use DEX for monk weapons/unarmed. Martial arts die d8.",
                    feature_type="class", mechanic="martial_arts", mechanic_value="1d8"),
            Feature("Ki", "10 ki points. Flurry of Blows, Patient Defense, Step of the Wind.",
                    feature_type="class", mechanic="ki"),
            Feature("Flurry of Blows", "After Attack: 1 ki for 2 bonus unarmed strikes",
                    feature_type="class", mechanic="flurry_of_blows"),
            Feature("Patient Defense", "1 ki: Dodge as bonus action",
                    feature_type="class", mechanic="patient_defense"),
            Feature("Step of the Wind", "1 ki: Disengage or Dash as bonus, jump doubled",
                    feature_type="class", mechanic="step_of_wind"),
            Feature("Stunning Strike", "On hit: 1 ki, target CON save DC 16 or Stunned",
                    feature_type="class", mechanic="stunning_strike"),
            Feature("Deflect Missiles", "Reaction: reduce ranged damage by 1d10+14. "
                    "If 0, catch and throw back (1 ki).",
                    feature_type="class", mechanic="deflect_missiles"),
            Feature("Extra Attack", "2 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Evasion", "DEX save success: no damage. Fail: half damage.",
                    feature_type="class", mechanic="evasion"),
            Feature("Purity of Body", "Immune to disease and poison",
                    feature_type="class", mechanic="purity_of_body"),
            Feature("Open Hand Technique", "Flurry of Blows: target DEX save or Prone, "
                    "STR save or pushed 15ft, or can't take reactions.",
                    feature_type="class", mechanic="open_hand_technique"),
            Feature("Unarmored Defense (Monk)", "AC = 10 + DEX + WIS",
                    feature_type="class", mechanic="unarmored_defense_monk"),
            Feature("Unarmored Movement", "+20 ft speed",
                    feature_type="class", mechanic="unarmored_movement"),
        ],
        racial_traits=get_racial_traits("Wood Elf"),
        ki_points=10,
        condition_immunities=["Poisoned"],  # Purity of Body
        saving_throws={"Strength": 4, "Dexterity": 8},
        skills={"Acrobatics": 8, "Athletics": 4, "Insight": 8, "Stealth": 8},
        challenge_rating=5.0, proficiency_bonus=4,
    ),
]
