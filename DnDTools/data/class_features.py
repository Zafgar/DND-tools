"""
D&D 5e 2014 Class Features Database
All class features for levels 1-20, organized by class.
Used by hero builder and AI to understand class mechanics.
"""
from data.models import Feature

# ============================================================
# BARBARIAN
# ============================================================
BARBARIAN_FEATURES = {
    1: [
        Feature("Rage", "Bonus action: Adv on STR checks/saves, rage damage bonus, "
                "resistance to bludgeoning/piercing/slashing. Lasts 1 min or until "
                "you don't attack or take damage.",
                feature_type="class", uses_per_day=2, mechanic="rage",
                short_rest_recharge=False),
        Feature("Unarmored Defense (Barbarian)", "AC = 10 + DEX + CON when not wearing armor",
                feature_type="class", mechanic="unarmored_defense_barbarian"),
    ],
    2: [
        Feature("Reckless Attack", "First attack each turn: Advantage on melee STR attacks, "
                "but attacks against you have advantage until next turn.",
                feature_type="class", mechanic="reckless_attack"),
        Feature("Danger Sense", "Advantage on DEX saves against effects you can see "
                "(not blinded/deafened/incapacitated).",
                feature_type="class", mechanic="danger_sense"),
    ],
    3: [
        Feature("Rage Damage +2", "Extra +2 melee damage while raging",
                feature_type="class", mechanic="rage_damage", mechanic_value="2"),
    ],
    5: [
        Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack"),
        Feature("Fast Movement", "+10 ft speed when not wearing heavy armor",
                feature_type="class", mechanic="fast_movement"),
    ],
    7: [
        Feature("Feral Instinct", "Advantage on initiative. Can act normally on first "
                "turn of combat even if surprised (if you rage).",
                feature_type="class", mechanic="feral_instinct"),
    ],
    9: [
        Feature("Brutal Critical", "Roll one additional weapon damage die on a critical hit",
                feature_type="class", mechanic="brutal_critical", mechanic_value="1"),
        Feature("Rage Damage +3", "Extra +3 melee damage while raging",
                feature_type="class", mechanic="rage_damage", mechanic_value="3"),
    ],
    11: [
        Feature("Relentless Rage", "If you drop to 0 HP while raging, DC 10 CON save "
                "to drop to 1 HP instead. DC increases by 5 each time.",
                feature_type="class", mechanic="relentless_rage"),
    ],
    15: [
        Feature("Persistent Rage", "Rage only ends early if you choose or fall unconscious",
                feature_type="class", mechanic="persistent_rage"),
    ],
    16: [
        Feature("Rage Damage +4", "Extra +4 melee damage while raging",
                feature_type="class", mechanic="rage_damage", mechanic_value="4"),
    ],
    20: [
        Feature("Primal Champion", "+4 STR and +4 CON (max 24)",
                feature_type="class", mechanic="primal_champion"),
    ],
}

# Totem Warrior (Bear) subclass
BARBARIAN_TOTEM_BEAR = {
    3: [Feature("Totem Spirit: Bear", "While raging, resistance to all damage except psychic",
                feature_type="class", mechanic="totem_bear")],
    6: [Feature("Aspect of the Bear", "Carrying capacity doubled, advantage on STR checks "
                "to push/pull/lift/break objects",
                feature_type="class", mechanic="aspect_bear")],
    14: [Feature("Totemic Attunement: Bear", "While raging, hostile creatures within 5ft "
                 "have disadvantage on attacks against allies",
                 feature_type="class", mechanic="totem_bear_aura", aura_radius=5)],
}

# Berserker subclass
BARBARIAN_BERSERKER = {
    3: [Feature("Frenzy", "While raging, you can make a single melee weapon attack as a "
                "bonus action each turn. When rage ends, suffer 1 level of exhaustion.",
                feature_type="class", mechanic="frenzy")],
    6: [Feature("Mindless Rage", "Can't be charmed or frightened while raging. "
                "Effect suspends until rage ends.",
                feature_type="class", mechanic="mindless_rage")],
    10: [Feature("Intimidating Presence", "Action: frighten one creature within 30ft. "
                 "Target makes WIS save (DC 8+prof+CHA) or frightened until end of next turn.",
                 feature_type="class", mechanic="intimidating_presence",
                 save_ability="Wisdom")],
    14: [Feature("Retaliation", "When you take damage from a creature within 5ft, "
                 "use reaction to make a melee weapon attack against it.",
                 feature_type="class", mechanic="retaliation")],
}

# ============================================================
# FIGHTER
# ============================================================
FIGHTER_FEATURES = {
    1: [
        Feature("Second Wind", "Bonus action: Heal 1d10 + fighter level HP. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="second_wind",
                mechanic_value="1d10+level", short_rest_recharge=True),
        Feature("Fighting Style", "Choose a fighting style bonus",
                feature_type="class", mechanic="fighting_style"),
    ],
    2: [
        Feature("Action Surge", "Take one additional action on your turn. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="action_surge",
                short_rest_recharge=True),
    ],
    5: [
        Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack"),
    ],
    9: [
        Feature("Indomitable", "Re-roll a failed saving throw. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="indomitable"),
    ],
    11: [
        Feature("Extra Attack (2)", "Attack three times when taking the Attack action",
                feature_type="class", mechanic="extra_attack_2"),
    ],
    13: [
        Feature("Indomitable (2 uses)", "Re-roll a failed saving throw. 2/long rest.",
                feature_type="class", uses_per_day=2, mechanic="indomitable"),
    ],
    17: [
        Feature("Indomitable (3 uses)", "Re-roll a failed saving throw. 3/long rest.",
                feature_type="class", uses_per_day=3, mechanic="indomitable"),
        Feature("Action Surge (2 uses)", "Take one additional action. 2/short rest.",
                feature_type="class", uses_per_day=2, mechanic="action_surge",
                short_rest_recharge=True),
    ],
    20: [
        Feature("Extra Attack (3)", "Attack four times when taking the Attack action",
                feature_type="class", mechanic="extra_attack_3"),
    ],
}

# Champion subclass
FIGHTER_CHAMPION = {
    3: [Feature("Improved Critical", "Critical hit on 19-20",
                feature_type="class", mechanic="improved_critical")],
    7: [Feature("Remarkable Athlete", "Add half proficiency to STR/DEX/CON checks "
                "you aren't proficient in. Running long jump +STR mod ft.",
                feature_type="class", mechanic="remarkable_athlete")],
    15: [Feature("Superior Critical", "Critical hit on 18-20",
                 feature_type="class", mechanic="superior_critical")],
}

# Battle Master subclass
FIGHTER_BATTLE_MASTER = {
    3: [
        Feature("Combat Superiority", "4 superiority dice (d8). Regain on short rest. "
                "Know 3 maneuvers: Trip Attack, Riposte, Precision Attack.",
                feature_type="class", uses_per_day=4, mechanic="combat_superiority",
                mechanic_value="d8", short_rest_recharge=True),
        Feature("Trip Attack", "When you hit, spend superiority die: add to damage, "
                "Large or smaller target makes STR save or falls prone.",
                feature_type="class", mechanic="trip_attack"),
        Feature("Riposte", "Reaction when creature misses you: spend superiority die "
                "for melee attack + superiority die damage.",
                feature_type="class", mechanic="riposte"),
        Feature("Precision Attack", "When you miss an attack, spend superiority die "
                "and add it to the attack roll.",
                feature_type="class", mechanic="precision_attack"),
    ],
    7: [Feature("Know Your Enemy", "Study a creature for 1 minute to learn if it's "
                "equal/superior/inferior in two characteristics.",
                feature_type="class", mechanic="know_your_enemy")],
    10: [Feature("Improved Combat Superiority", "Superiority dice become d10",
                 feature_type="class", mechanic="combat_superiority",
                 mechanic_value="d10")],
    15: [Feature("Relentless", "If you have no superiority dice at initiative, regain 1.",
                 feature_type="class", mechanic="relentless")],
    18: [Feature("Superior Combat Superiority", "Superiority dice become d12",
                 feature_type="class", mechanic="combat_superiority",
                 mechanic_value="d12")],
}

# ============================================================
# PALADIN
# ============================================================
PALADIN_FEATURES = {
    1: [
        Feature("Divine Sense", "Detect celestial/fiend/undead within 60ft",
                feature_type="class", uses_per_day=4, mechanic="divine_sense"),
        Feature("Lay on Hands", "Touch: heal from HP pool equal to 5 x paladin level. "
                "Can also expend 5 HP from pool to cure one disease or neutralize one poison.",
                feature_type="class", uses_per_day=1, mechanic="lay_on_hands",
                mechanic_value="5*level"),
    ],
    2: [
        Feature("Fighting Style", "Choose a fighting style bonus",
                feature_type="class", mechanic="fighting_style"),
        Feature("Divine Smite", "On hit: expend spell slot for +2d8 radiant per slot level. "
                "+1d8 vs undead/fiend. Max 5d8.",
                feature_type="class", mechanic="divine_smite"),
    ],
    3: [
        Feature("Divine Health", "Immune to disease",
                feature_type="class", mechanic="divine_health"),
        Feature("Channel Divinity", "Channel divine energy 1/short rest",
                feature_type="class", uses_per_day=1, mechanic="channel_divinity",
                short_rest_recharge=True),
    ],
    5: [
        Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack"),
    ],
    6: [
        Feature("Aura of Protection", "You and allies within 10ft add CHA mod to saves",
                feature_type="class", mechanic="aura_of_protection", aura_radius=10),
    ],
    10: [
        Feature("Aura of Courage", "You and allies within 10ft immune to Frightened",
                feature_type="class", mechanic="aura_of_courage", aura_radius=10),
    ],
    11: [
        Feature("Improved Divine Smite", "All melee weapon hits deal +1d8 radiant",
                feature_type="class", mechanic="improved_divine_smite"),
    ],
    14: [
        Feature("Cleansing Touch", "Action: end one spell on you or willing creature. "
                "CHA mod times per long rest.",
                feature_type="class", uses_per_day=4, mechanic="cleansing_touch"),
    ],
}

# Oath of Devotion
PALADIN_DEVOTION = {
    3: [
        Feature("Channel Divinity: Sacred Weapon", "Action: add CHA mod to attack rolls "
                "with one weapon for 1 minute. Weapon emits bright light 20ft.",
                feature_type="class", mechanic="sacred_weapon"),
        Feature("Channel Divinity: Turn the Unholy", "Action: fiends and undead within 30ft "
                "make WIS save or flee for 1 minute.",
                feature_type="class", mechanic="turn_the_unholy",
                save_ability="Wisdom"),
    ],
    7: [
        Feature("Aura of Devotion", "You and allies within 10ft can't be charmed",
                feature_type="class", mechanic="aura_of_devotion", aura_radius=10),
    ],
    15: [
        Feature("Purity of Spirit", "Always under the effect of Protection from Evil and Good",
                feature_type="class", mechanic="purity_of_spirit"),
    ],
    20: [
        Feature("Holy Nimbus", "Action: 30ft bright light aura for 1 minute. "
                "Enemies starting turn in aura take 10 radiant. "
                "Advantage on saves vs fiend/undead spells.",
                feature_type="class", uses_per_day=1, mechanic="holy_nimbus",
                aura_radius=30, damage_dice="10", damage_type="radiant"),
    ],
}

# Oath of Vengeance
PALADIN_VENGEANCE = {
    3: [
        Feature("Channel Divinity: Abjure Enemy", "Action: one creature within 60ft makes WIS save "
                "or is frightened for 1 minute. Speed 0 on fail (fiends/undead disadv).",
                feature_type="class", mechanic="abjure_enemy",
                save_ability="Wisdom"),
        Feature("Channel Divinity: Vow of Enmity", "Bonus action: advantage on attacks against "
                "one creature within 10ft for 1 minute.",
                feature_type="class", mechanic="vow_of_enmity"),
    ],
    7: [
        Feature("Relentless Avenger", "When you hit with opportunity attack, can move up to "
                "half speed immediately after. No opportunity attacks provoked.",
                feature_type="class", mechanic="relentless_avenger"),
    ],
    15: [
        Feature("Soul of Vengeance", "When creature under Vow of Enmity attacks, use reaction "
                "to make a melee weapon attack.",
                feature_type="class", mechanic="soul_of_vengeance"),
    ],
    20: [
        Feature("Avenging Angel", "Action: transform for 1 hour. 60ft fly speed. "
                "30ft aura of menace: enemies make WIS save or frightened 1 min.",
                feature_type="class", uses_per_day=1, mechanic="avenging_angel",
                aura_radius=30, save_ability="Wisdom"),
    ],
}

# ============================================================
# ROGUE
# ============================================================
ROGUE_FEATURES = {
    1: [
        Feature("Sneak Attack", "Once per turn: extra damage when you have advantage "
                "or ally is adjacent to target. 1d6 at level 1, +1d6 every 2 levels.",
                feature_type="class", mechanic="sneak_attack", mechanic_value="1d6"),
        Feature("Expertise", "Double proficiency bonus on two skills",
                feature_type="class", mechanic="expertise"),
    ],
    2: [
        Feature("Cunning Action", "Bonus action: Dash, Disengage, or Hide",
                feature_type="class", mechanic="cunning_action"),
    ],
    3: [
        Feature("Sneak Attack 2d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="2d6"),
    ],
    5: [
        Feature("Uncanny Dodge", "Reaction: halve damage from an attack you can see",
                feature_type="class", mechanic="uncanny_dodge"),
        Feature("Sneak Attack 3d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="3d6"),
    ],
    7: [
        Feature("Evasion", "DEX saves: no damage on success, half on fail (instead of half/full)",
                feature_type="class", mechanic="evasion"),
        Feature("Sneak Attack 4d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="4d6"),
    ],
    9: [
        Feature("Sneak Attack 5d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="5d6"),
    ],
    11: [
        Feature("Reliable Talent", "Minimum 10 on ability checks with proficiency",
                feature_type="class", mechanic="reliable_talent"),
        Feature("Sneak Attack 6d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="6d6"),
    ],
    13: [
        Feature("Sneak Attack 7d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="7d6"),
    ],
    15: [
        Feature("Slippery Mind", "Proficiency in WIS saves",
                feature_type="class", mechanic="slippery_mind"),
        Feature("Sneak Attack 8d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="8d6"),
    ],
    17: [
        Feature("Sneak Attack 9d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="9d6"),
    ],
    19: [
        Feature("Sneak Attack 10d6", "", feature_type="class",
                mechanic="sneak_attack", mechanic_value="10d6"),
    ],
}

# Assassin subclass
ROGUE_ASSASSIN = {
    3: [Feature("Assassinate", "Advantage on attacks against creatures that haven't acted. "
                "Auto-crit on hit against surprised creatures.",
                feature_type="class", mechanic="assassinate")],
    9: [Feature("Infiltration Expertise", "Spend 7 days and 25 gp to create a false identity",
                feature_type="class", mechanic="infiltration_expertise")],
    13: [Feature("Impostor", "Unerringly mimic another person's speech, writing, and behavior",
                 feature_type="class", mechanic="impostor")],
    17: [Feature("Death Strike", "When you hit a surprised creature, it must make CON save "
                 "(DC 8+DEX+prof) or the damage is doubled.",
                 feature_type="class", mechanic="death_strike")],
}

# Thief subclass
ROGUE_THIEF = {
    3: [
        Feature("Fast Hands", "Cunning Action also lets you: make Sleight of Hand check, "
                "use thieves' tools, or Use an Object action.",
                feature_type="class", mechanic="fast_hands"),
        Feature("Second-Story Work", "Climbing costs no extra movement. "
                "Running jump distance +DEX mod ft.",
                feature_type="class", mechanic="second_story_work"),
    ],
    9: [Feature("Supreme Sneak", "Advantage on Stealth checks if you move no more than half speed",
                feature_type="class", mechanic="supreme_sneak")],
    13: [Feature("Use Magic Device", "Ignore all class, race, and level requirements on magic items",
                 feature_type="class", mechanic="use_magic_device")],
    17: [Feature("Thief's Reflexes", "Take two turns in the first round of combat. "
                 "Second turn at initiative minus 10.",
                 feature_type="class", mechanic="thiefs_reflexes")],
}

# ============================================================
# RANGER
# ============================================================
RANGER_FEATURES = {
    1: [
        Feature("Favored Enemy", "Advantage on WIS (Survival) checks to track, "
                "INT checks to recall info about favored enemies.",
                feature_type="class", mechanic="favored_enemy"),
        Feature("Natural Explorer", "Double proficiency on INT/WIS checks in favored terrain. "
                "Difficult terrain doesn't slow your group.",
                feature_type="class", mechanic="natural_explorer"),
    ],
    2: [
        Feature("Fighting Style", "Choose a fighting style bonus",
                feature_type="class", mechanic="fighting_style"),
    ],
    3: [
        Feature("Primeval Awareness", "Expend spell slot: sense aberrations, celestials, "
                "dragons, elementals, fey, fiends, undead within 1 mile.",
                feature_type="class", mechanic="primeval_awareness"),
    ],
    5: [
        Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack"),
    ],
    8: [
        Feature("Land's Stride", "Moving through nonmagical difficult terrain costs no extra. "
                "Advantage on saves vs magically impeding plants.",
                feature_type="class", mechanic="lands_stride"),
    ],
    10: [
        Feature("Hide in Plain Sight", "Spend 1 minute to camouflage: +10 to Stealth",
                feature_type="class", mechanic="hide_in_plain_sight"),
    ],
    14: [
        Feature("Vanish", "Hide as bonus action. Can't be tracked nonmagically.",
                feature_type="class", mechanic="vanish"),
    ],
    18: [
        Feature("Feral Senses", "No disadvantage on attacks against invisible creatures. "
                "Aware of location of invisible creatures within 30ft.",
                feature_type="class", mechanic="feral_senses"),
    ],
}

# Hunter subclass
RANGER_HUNTER = {
    3: [Feature("Colossus Slayer", "Once per turn: +1d8 damage against a creature "
                "below its HP maximum.",
                feature_type="class", mechanic="colossus_slayer", mechanic_value="1d8")],
    7: [Feature("Multiattack Defense", "After a creature hits you, gain +4 AC "
                "against subsequent attacks from it this turn.",
                feature_type="class", mechanic="multiattack_defense")],
    11: [Feature("Volley", "Action: make a ranged attack against all creatures "
                 "within 10ft of a point in range.",
                 feature_type="class", mechanic="volley")],
    15: [Feature("Evasion", "DEX saves: no damage on success, half on fail",
                 feature_type="class", mechanic="evasion")],
}

# Beast Master subclass
RANGER_BEAST_MASTER = {
    3: [Feature("Ranger's Companion", "Gain a beast companion (CR 1/4 or lower). "
                "It acts on your initiative and you command it with your action.",
                feature_type="class", mechanic="rangers_companion")],
    7: [Feature("Exceptional Training", "Companion can Dash/Disengage/Dodge/Help as bonus action. "
                "Companion attacks are magical.",
                feature_type="class", mechanic="exceptional_training")],
    11: [Feature("Bestial Fury", "Companion makes two attacks when you command it to attack",
                 feature_type="class", mechanic="bestial_fury")],
    15: [Feature("Share Spells", "When you cast a spell targeting yourself, companion also benefits "
                 "if within 30ft.",
                 feature_type="class", mechanic="share_spells")],
}

# ============================================================
# CLERIC
# ============================================================
CLERIC_FEATURES = {
    1: [
        Feature("Channel Divinity: Turn Undead", "Action: undead within 30ft make WIS save "
                "or flee for 1 minute.",
                feature_type="class", uses_per_day=1, mechanic="channel_divinity",
                short_rest_recharge=True, save_dc=0, save_ability="Wisdom"),
    ],
    2: [
        Feature("Channel Divinity (2/rest)", "Use Channel Divinity twice per short rest",
                feature_type="class", uses_per_day=2, mechanic="channel_divinity",
                short_rest_recharge=True),
    ],
    5: [
        Feature("Destroy Undead", "Turn Undead destroys CR 1/2 or lower undead",
                feature_type="class", mechanic="destroy_undead"),
    ],
    10: [
        Feature("Divine Intervention", "Pray for divine aid. Percentage roll <= cleric level.",
                feature_type="class", uses_per_day=1, mechanic="divine_intervention"),
    ],
}

# War Domain
CLERIC_WAR = {
    1: [
        Feature("War Priest", "When you use Attack action, make one weapon attack "
                "as bonus action. WIS mod times per long rest.",
                feature_type="class", uses_per_day=4, mechanic="war_priest"),
    ],
    2: [
        Feature("Channel Divinity: Guided Strike", "+10 to an attack roll",
                feature_type="class", mechanic="guided_strike"),
    ],
    6: [
        Feature("Channel Divinity: War God's Blessing", "Reaction: +10 to ally's attack "
                "within 30ft.",
                feature_type="class", mechanic="war_gods_blessing"),
    ],
    8: [
        Feature("Divine Strike", "Once per turn: +1d8 weapon damage (increases to 2d8 at 14)",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Avatar of Battle", "Resistance to bludgeoning/piercing/slashing from "
                "nonmagical attacks.",
                feature_type="class", mechanic="avatar_of_battle"),
    ],
}

# Life Domain
CLERIC_LIFE = {
    1: [
        Feature("Disciple of Life", "Healing spells heal extra 2 + spell level HP",
                feature_type="class", mechanic="disciple_of_life"),
    ],
    2: [
        Feature("Channel Divinity: Preserve Life", "Action: distribute up to 5*cleric level HP "
                "among creatures within 30ft (up to half max HP each).",
                feature_type="class", mechanic="preserve_life"),
    ],
    6: [
        Feature("Blessed Healer", "When you cast heal spell on another, heal yourself "
                "2 + spell level HP.",
                feature_type="class", mechanic="blessed_healer"),
    ],
    8: [
        Feature("Divine Strike", "Once per turn: +1d8 radiant on weapon hit",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Supreme Healing", "Maximize healing dice instead of rolling",
                feature_type="class", mechanic="supreme_healing"),
    ],
}

# Light Domain
CLERIC_LIGHT = {
    1: [Feature("Warding Flare", "Reaction when attacked: impose disadvantage on the attack. "
                "WIS mod times per long rest.",
                feature_type="class", uses_per_day=4, mechanic="warding_flare")],
    2: [Feature("Channel Divinity: Radiance of the Dawn", "Action: dispel magical darkness within 30ft. "
                "Hostile creatures within 30ft take 2d10+cleric level radiant (CON save half).",
                feature_type="class", mechanic="radiance_of_dawn",
                damage_dice="2d10", damage_type="radiant", save_ability="Constitution")],
    6: [Feature("Improved Flare", "Use Warding Flare when a creature attacks another within 30ft",
                feature_type="class", mechanic="improved_flare")],
    8: [Feature("Potent Spellcasting", "Add WIS mod to cantrip damage",
                feature_type="class", mechanic="potent_spellcasting")],
    17: [Feature("Corona of Light", "Action: 60ft bright light aura. Enemies in aura have "
                 "disadvantage on saves vs fire/radiant spells.",
                 feature_type="class", mechanic="corona_of_light", aura_radius=60)],
}

# ============================================================
# WIZARD
# ============================================================
WIZARD_FEATURES = {
    1: [
        Feature("Arcane Recovery", "Short rest: recover spell slots equal to half wizard level "
                "(rounded up). 1/day.",
                feature_type="class", uses_per_day=1, mechanic="arcane_recovery",
                short_rest_recharge=False),
    ],
    18: [
        Feature("Spell Mastery", "Choose two 1st/2nd level spells: cast at will without slots",
                feature_type="class", mechanic="spell_mastery"),
    ],
    20: [
        Feature("Signature Spells", "Choose two 3rd-level spells: cast once each without "
                "slots per short rest.",
                feature_type="class", uses_per_day=2, mechanic="signature_spells",
                short_rest_recharge=True),
    ],
}

# Evocation subclass
WIZARD_EVOCATION = {
    2: [Feature("Sculpt Spells", "When casting evocation spell, choose creatures equal to "
                "1 + spell level to auto-succeed saves and take no damage.",
                feature_type="class", mechanic="sculpt_spells")],
    6: [Feature("Potent Cantrip", "Saving throw cantrips deal half damage on success",
                feature_type="class", mechanic="potent_cantrip")],
    10: [Feature("Empowered Evocation", "Add INT mod to evocation spell damage",
                 feature_type="class", mechanic="empowered_evocation")],
    14: [Feature("Overchannel", "Maximize damage of 5th level or lower spell. "
                 "After first use, take 2d12 necrotic per level (increases each use).",
                 feature_type="class", mechanic="overchannel")],
}

# Abjuration school
WIZARD_ABJURATION = {
    2: [Feature("Arcane Ward", "When you cast an abjuration spell (1st+), create a ward "
                "with HP = 2*wizard level + INT mod. Absorbs damage for you.",
                feature_type="class", mechanic="arcane_ward")],
    6: [Feature("Projected Ward", "Reaction: when ally within 30ft takes damage, "
                "your Arcane Ward absorbs it instead.",
                feature_type="class", mechanic="projected_ward")],
    10: [Feature("Improved Abjuration", "Add proficiency bonus to ability checks for "
                 "abjuration spells (e.g., Counterspell, Dispel Magic).",
                 feature_type="class", mechanic="improved_abjuration")],
    14: [Feature("Spell Resistance", "Advantage on saves vs spells. Resistance to spell damage.",
                 feature_type="class", mechanic="spell_resistance")],
}

# Divination school
WIZARD_DIVINATION = {
    2: [Feature("Portent", "After long rest, roll 2d20 and record. Before any creature's roll, "
                "replace it with a Portent die. 2/long rest.",
                feature_type="class", uses_per_day=2, mechanic="portent")],
    6: [Feature("Expert Divination", "When you cast a divination spell (2nd+), "
                "regain a lower-level spell slot.",
                feature_type="class", mechanic="expert_divination")],
    10: [Feature("The Third Eye", "Action: gain one of: ethereal sight 60ft, "
                 "see invisible 10ft, darkvision 60ft, or read any language.",
                 feature_type="class", mechanic="the_third_eye")],
    14: [Feature("Greater Portent", "Roll 3d20 for Portent instead of 2",
                 feature_type="class", uses_per_day=3, mechanic="portent")],
}

# ============================================================
# WARLOCK
# ============================================================
WARLOCK_FEATURES = {
    1: [
        Feature("Pact Magic", "Spellcasting: fewer slots, all at highest level, "
                "recover on short rest.",
                feature_type="class", mechanic="pact_magic"),
    ],
    2: [
        Feature("Eldritch Invocations", "Gain two invocations for customization",
                feature_type="class", mechanic="eldritch_invocation"),
        Feature("Agonizing Blast", "Add CHA mod to Eldritch Blast damage",
                feature_type="class", mechanic="agonizing_blast"),
    ],
    3: [
        Feature("Pact Boon", "Choose Pact of the Chain/Blade/Tome",
                feature_type="class", mechanic="pact_boon"),
    ],
    11: [
        Feature("Mystic Arcanum (6th)", "Cast one 6th-level spell once per long rest",
                feature_type="class", uses_per_day=1, mechanic="mystic_arcanum_6"),
    ],
    20: [
        Feature("Eldritch Master", "Spend 1 minute to regain all spell slots. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="eldritch_master"),
    ],
}

# Fiend patron
WARLOCK_FIEND = {
    1: [Feature("Dark One's Blessing", "When you reduce a hostile creature to 0 HP, "
                "gain CHA mod + warlock level temporary HP.",
                feature_type="class", mechanic="dark_ones_blessing")],
    6: [Feature("Dark One's Own Luck", "When you make an ability check or save, add d10 "
                "to the roll. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="dark_ones_own_luck",
                short_rest_recharge=True)],
    10: [Feature("Fiendish Resilience", "After a short or long rest, choose a damage type: "
                 "gain resistance to it until you choose another.",
                 feature_type="class", mechanic="fiendish_resilience")],
    14: [Feature("Hurl Through Hell", "When you hit a creature, banish it through the lower planes. "
                 "It takes 10d10 psychic damage. 1/long rest.",
                 feature_type="class", uses_per_day=1, mechanic="hurl_through_hell",
                 damage_dice="10d10", damage_type="psychic")],
}

# Great Old One patron
WARLOCK_GREAT_OLD_ONE = {
    1: [Feature("Awakened Mind", "Telepathically speak to any creature within 30ft "
                "that you can see. No shared language needed.",
                feature_type="class", mechanic="awakened_mind")],
    6: [Feature("Entropic Ward", "When a creature makes an attack against you, impose "
                "disadvantage. If it misses, your next attack against it has advantage. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="entropic_ward",
                short_rest_recharge=True)],
    10: [Feature("Thought Shield", "Resistance to psychic damage. Creatures reading your thoughts "
                 "must make WIS save or take 3d6 psychic.",
                 feature_type="class", mechanic="thought_shield")],
    14: [Feature("Create Thrall", "Touch an incapacitated humanoid to charm it permanently "
                 "until Remove Curse. Telepathic link across planes.",
                 feature_type="class", mechanic="create_thrall")],
}

# ============================================================
# SORCERER
# ============================================================
SORCERER_FEATURES = {
    1: [
        Feature("Sorcerous Origin", "Choose a sorcerous origin",
                feature_type="class", mechanic="sorcerous_origin"),
    ],
    2: [
        Feature("Font of Magic", "Sorcery points for Metamagic and converting spell slots",
                feature_type="class", mechanic="font_of_magic"),
    ],
    3: [
        Feature("Metamagic", "Modify spells with sorcery points: Twinned, Quickened, etc.",
                feature_type="class", mechanic="metamagic"),
        Feature("Twinned Spell", "Spend sorcery points = spell level to target two creatures",
                feature_type="class", mechanic="twinned_spell"),
        Feature("Quickened Spell", "Spend 2 sorcery points: cast action spell as bonus action",
                feature_type="class", mechanic="quickened_spell"),
    ],
    20: [
        Feature("Sorcerous Restoration", "Short rest: regain 4 sorcery points",
                feature_type="class", mechanic="sorcerous_restoration",
                short_rest_recharge=True),
    ],
}

# Wild Magic
SORCERER_WILD_MAGIC = {
    1: [Feature("Wild Magic Surge", "After casting a sorcerer spell of 1st level or higher, "
                "DM may have you roll d20. On a 1, roll on the Wild Magic Surge table.",
                feature_type="class", mechanic="wild_magic_surge"),
        Feature("Tides of Chaos", "Gain advantage on one attack, ability check, or save. "
                "1/long rest (or DM triggers Wild Magic Surge to regain).",
                feature_type="class", uses_per_day=1, mechanic="tides_of_chaos")],
    6: [Feature("Bend Luck", "Reaction: spend 2 sorcery points to add or subtract 1d4 "
                "from another creature's attack, check, or save.",
                feature_type="class", mechanic="bend_luck")],
    14: [Feature("Controlled Chaos", "When you roll on Wild Magic Surge table, roll twice "
                 "and choose either result.",
                 feature_type="class", mechanic="controlled_chaos")],
    18: [Feature("Spell Bombardment", "When you roll damage for a spell and roll the maximum "
                 "on any dice, roll that die again and add the extra result.",
                 feature_type="class", mechanic="spell_bombardment")],
}

# Draconic Bloodline
SORCERER_DRACONIC = {
    1: [Feature("Draconic Resilience", "+1 HP per level. AC = 13 + DEX when unarmored.",
                feature_type="class", mechanic="draconic_resilience")],
    6: [Feature("Elemental Affinity", "Add CHA mod to damage of spells matching ancestry type. "
                "Spend 1 sorcery point for 1 hour resistance.",
                feature_type="class", mechanic="elemental_affinity")],
    14: [Feature("Dragon Wings", "Bonus action: sprout dragon wings. Fly speed = walking speed.",
                 feature_type="class", mechanic="dragon_wings")],
    18: [Feature("Draconic Presence", "Spend 5 sorcery points: 60ft aura of awe/fear for 1 min.",
                 feature_type="class", mechanic="draconic_presence",
                 aura_radius=60, save_ability="Wisdom")],
}

# ============================================================
# BARD
# ============================================================
BARD_FEATURES = {
    1: [
        Feature("Bardic Inspiration", "Bonus action: give ally a d6 to add to ability check, "
                "attack, or save. CHA mod uses per long rest.",
                feature_type="class", mechanic="bardic_inspiration",
                mechanic_value="1d6"),
    ],
    2: [
        Feature("Jack of All Trades", "Add half proficiency to any ability check "
                "you aren't proficient in.",
                feature_type="class", mechanic="jack_of_all_trades"),
        Feature("Song of Rest", "During short rest, allies regain extra 1d6 HP",
                feature_type="class", mechanic="song_of_rest", mechanic_value="1d6"),
    ],
    3: [
        Feature("Expertise", "Double proficiency on two skills",
                feature_type="class", mechanic="expertise"),
    ],
    5: [
        Feature("Bardic Inspiration d8", "Inspiration die increases to d8",
                feature_type="class", mechanic="bardic_inspiration", mechanic_value="1d8"),
        Feature("Font of Inspiration", "Bardic Inspiration recharges on short rest",
                feature_type="class", mechanic="font_of_inspiration",
                short_rest_recharge=True),
    ],
    6: [
        Feature("Countercharm", "Action: allies within 30ft have advantage on saves "
                "vs charm/fear for 1 round.",
                feature_type="class", mechanic="countercharm"),
    ],
    10: [
        Feature("Bardic Inspiration d10", "Inspiration die increases to d10",
                feature_type="class", mechanic="bardic_inspiration", mechanic_value="1d10"),
        Feature("Magical Secrets", "Learn two spells from any class",
                feature_type="class", mechanic="magical_secrets"),
    ],
    15: [
        Feature("Bardic Inspiration d12", "Inspiration die increases to d12",
                feature_type="class", mechanic="bardic_inspiration", mechanic_value="1d12"),
    ],
}

# College of Lore
BARD_LORE = {
    3: [Feature("Cutting Words", "Reaction: subtract Bardic Inspiration die from enemy's "
                "attack, ability check, or damage roll within 60ft.",
                feature_type="class", mechanic="cutting_words")],
    6: [Feature("Additional Magical Secrets", "Learn two spells from any class at 6th level",
                feature_type="class", mechanic="additional_magical_secrets")],
    14: [Feature("Peerless Skill", "Add Bardic Inspiration to your own ability checks",
                 feature_type="class", mechanic="peerless_skill")],
}

# College of Valor
BARD_VALOR = {
    3: [Feature("Combat Inspiration", "Bardic Inspiration can also add to damage or AC",
                feature_type="class", mechanic="combat_inspiration")],
    6: [Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack")],
    14: [Feature("Battle Magic", "When you cast a spell as action, make one weapon attack "
                 "as bonus action.",
                 feature_type="class", mechanic="battle_magic")],
}

# ============================================================
# DRUID
# ============================================================
DRUID_FEATURES = {
    1: [
        Feature("Druidic", "You know the Druidic language",
                feature_type="class", mechanic="druidic"),
    ],
    2: [
        Feature("Wild Shape", "Action: transform into beast form. 2/short rest.",
                feature_type="class", uses_per_day=2, mechanic="wild_shape",
                short_rest_recharge=True),
    ],
    18: [
        Feature("Timeless Body", "Age 10x slower. No aging penalties.",
                feature_type="class", mechanic="timeless_body"),
        Feature("Beast Spells", "Can cast spells in Wild Shape (V/S but no M)",
                feature_type="class", mechanic="beast_spells"),
    ],
    20: [
        Feature("Archdruid", "Unlimited Wild Shape uses",
                feature_type="class", mechanic="archdruid"),
    ],
}

# Circle of the Moon
DRUID_MOON = {
    2: [Feature("Combat Wild Shape", "Wild Shape as bonus action. Can spend spell slots "
                "to heal in beast form (1d8 per slot level).",
                feature_type="class", mechanic="combat_wild_shape")],
    6: [Feature("Primal Strike", "Beast form attacks count as magical",
                feature_type="class", mechanic="primal_strike")],
    10: [Feature("Elemental Wild Shape", "Expend two Wild Shape uses to become an elemental",
                 feature_type="class", mechanic="elemental_wild_shape")],
}

# Circle of the Land
DRUID_LAND = {
    2: [Feature("Natural Recovery", "Short rest: recover spell slots with combined level "
                "equal to half druid level. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="natural_recovery")],
    6: [Feature("Land's Stride", "Moving through nonmagical difficult terrain costs no extra",
                feature_type="class", mechanic="lands_stride")],
    10: [Feature("Nature's Ward", "Immune to poison, disease, charm/frighten by elementals/fey",
                 feature_type="class", mechanic="natures_ward")],
    14: [Feature("Nature's Sanctuary", "Beasts and plants must make WIS save to attack you",
                 feature_type="class", mechanic="natures_sanctuary")],
}

# ============================================================
# MONK
# ============================================================
MONK_FEATURES = {
    1: [
        Feature("Unarmored Defense (Monk)", "AC = 10 + DEX + WIS when not wearing armor/shield",
                feature_type="class", mechanic="unarmored_defense_monk"),
        Feature("Martial Arts", "Use DEX for unarmed/monk weapons. Bonus unarmed strike after Attack.",
                feature_type="class", mechanic="martial_arts", mechanic_value="1d4"),
    ],
    2: [
        Feature("Ki", "Ki points = monk level. Flurry of Blows, Patient Defense, Step of the Wind.",
                feature_type="class", mechanic="ki"),
        Feature("Flurry of Blows", "After Attack: spend 1 ki for two unarmed strikes as bonus action",
                feature_type="class", mechanic="flurry_of_blows"),
        Feature("Patient Defense", "Spend 1 ki: Dodge as bonus action",
                feature_type="class", mechanic="patient_defense"),
        Feature("Step of the Wind", "Spend 1 ki: Disengage or Dash as bonus action, "
                "jump distance doubled.",
                feature_type="class", mechanic="step_of_wind"),
        Feature("Unarmored Movement", "+10 ft speed (increases at higher levels)",
                feature_type="class", mechanic="unarmored_movement"),
    ],
    3: [
        Feature("Deflect Missiles", "Reaction: reduce ranged attack damage by 1d10+DEX+monk level. "
                "If reduced to 0, catch and throw back (1 ki).",
                feature_type="class", mechanic="deflect_missiles"),
    ],
    4: [
        Feature("Slow Fall", "Reaction: reduce falling damage by 5*monk level",
                feature_type="class", mechanic="slow_fall"),
    ],
    5: [
        Feature("Extra Attack", "Attack twice when taking the Attack action",
                feature_type="class", mechanic="extra_attack"),
        Feature("Stunning Strike", "When you hit, spend 1 ki: target CON save or Stunned "
                "until end of your next turn.",
                feature_type="class", mechanic="stunning_strike"),
        Feature("Martial Arts d6", "Martial arts die increases to d6",
                feature_type="class", mechanic="martial_arts", mechanic_value="1d6"),
    ],
    6: [
        Feature("Ki-Empowered Strikes", "Unarmed strikes count as magical",
                feature_type="class", mechanic="ki_empowered_strikes"),
    ],
    7: [
        Feature("Evasion", "DEX saves: no damage on success, half on fail",
                feature_type="class", mechanic="evasion"),
        Feature("Stillness of Mind", "Action: end one charm or frighten effect on yourself",
                feature_type="class", mechanic="stillness_of_mind"),
    ],
    10: [
        Feature("Purity of Body", "Immune to disease and poison",
                feature_type="class", mechanic="purity_of_body"),
    ],
    11: [
        Feature("Martial Arts d8", "Martial arts die increases to d8",
                feature_type="class", mechanic="martial_arts", mechanic_value="1d8"),
    ],
    13: [
        Feature("Tongue of the Sun and Moon", "Understand all spoken languages",
                feature_type="class", mechanic="tongue_of_sun_moon"),
    ],
    14: [
        Feature("Diamond Soul", "Proficiency in all saving throws. Spend 1 ki to reroll failed save.",
                feature_type="class", mechanic="diamond_soul"),
    ],
    15: [
        Feature("Timeless Body", "No aging penalties. No food/water needed.",
                feature_type="class", mechanic="timeless_body"),
    ],
    17: [
        Feature("Martial Arts d10", "Martial arts die increases to d10",
                feature_type="class", mechanic="martial_arts", mechanic_value="1d10"),
    ],
    18: [
        Feature("Empty Body", "Spend 4 ki: invisible for 1 minute. "
                "Spend 8 ki: cast Astral Projection.",
                feature_type="class", mechanic="empty_body"),
    ],
    20: [
        Feature("Perfect Self", "If you have no ki when rolling initiative, regain 4 ki.",
                feature_type="class", mechanic="perfect_self"),
    ],
}

# Way of the Open Hand
MONK_OPEN_HAND = {
    3: [Feature("Open Hand Technique", "Flurry of Blows: target must make DEX save or "
                "be knocked prone, STR save or be pushed 15ft, or can't take reactions.",
                feature_type="class", mechanic="open_hand_technique")],
    6: [Feature("Wholeness of Body", "Action: heal 3*monk level HP. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="wholeness_of_body")],
    11: [Feature("Tranquility", "At end of long rest, gain Sanctuary effect (WIS save DC)",
                 feature_type="class", mechanic="tranquility")],
    17: [Feature("Quivering Palm", "When you hit, spend 3 ki: set vibrations that can "
                 "kill later (CON save or drop to 0 HP).",
                 feature_type="class", mechanic="quivering_palm")],
}

# Way of Shadow
MONK_SHADOW = {
    3: [Feature("Shadow Arts", "Spend 2 ki to cast Darkness, Darkvision, Pass without Trace, "
                "or Silence without material components. Minor Illusion cantrip for free.",
                feature_type="class", mechanic="shadow_arts")],
    6: [Feature("Shadow Step", "Bonus action: teleport 60ft from dim light/darkness to "
                "dim light/darkness. Advantage on first melee attack after.",
                feature_type="class", mechanic="shadow_step")],
    11: [Feature("Cloak of Shadows", "Action in dim light/darkness: become invisible until "
                 "you attack, cast spell, or enter bright light.",
                 feature_type="class", mechanic="cloak_of_shadows")],
    17: [Feature("Opportunist", "When a creature within 5ft is hit by another creature's attack, "
                 "use reaction to make a melee attack against it.",
                 feature_type="class", mechanic="opportunist")],
}


# ============================================================
# Rage count by Barbarian level
# ============================================================
# ============================================================
# ADDITIONAL SUBCLASSES (XGtE, SCAG, PHB missing)
# ============================================================

# --- BARBARIAN ---
BARBARIAN_ANCESTRAL_GUARDIAN = {
    3: [
        Feature("Ancestral Protectors", "While raging, first creature you hit has disadvantage "
                "on attacks that don't target you. Others have resistance to its attacks.",
                feature_type="class", mechanic="ancestral_protectors"),
    ],
    6: [
        Feature("Spirit Shield", "Reaction: reduce damage to ally within 30ft by 2d6 while raging.",
                feature_type="class", mechanic="spirit_shield", mechanic_value="2d6"),
    ],
    10: [
        Feature("Consult the Spirits", "Clairvoyance or Augury as ritual. 1/short rest.",
                feature_type="class", mechanic="consult_spirits", uses_per_day=1,
                short_rest_recharge=True),
    ],
    14: [
        Feature("Vengeful Ancestors", "Spirit Shield also deals force damage to attacker = reduction.",
                feature_type="class", mechanic="vengeful_ancestors"),
    ],
}

BARBARIAN_STORM_HERALD = {
    3: [
        Feature("Storm Aura", "Bonus action while raging: 10ft aura. Desert=fire, Sea=lightning, "
                "Tundra=temp HP. Scales with level.",
                feature_type="class", mechanic="storm_aura"),
    ],
    6: [
        Feature("Storm Soul", "Desert=fire resistance, Sea=lightning+swim, Tundra=cold resistance.",
                feature_type="class", mechanic="storm_soul"),
    ],
    10: [
        Feature("Shielding Storm", "Allies in aura gain your damage resistance type.",
                feature_type="class", mechanic="shielding_storm"),
    ],
    14: [
        Feature("Raging Storm", "Desert=reaction fire, Sea=reaction knockdown, Tundra=speed 0.",
                feature_type="class", mechanic="raging_storm"),
    ],
}

BARBARIAN_ZEALOT = {
    3: [
        Feature("Divine Fury", "First hit each turn while raging: +1d6+half level radiant/necrotic.",
                feature_type="class", mechanic="divine_fury", mechanic_value="1d6"),
        Feature("Warrior of the Gods", "Spells to raise you from dead cost no material components.",
                feature_type="class", mechanic="warrior_of_gods"),
    ],
    6: [
        Feature("Fanatical Focus", "While raging, re-roll failed save. 1/rage.",
                feature_type="class", mechanic="fanatical_focus"),
    ],
    10: [
        Feature("Zealous Presence", "Bonus action: 10 creatures within 60ft get advantage "
                "on attacks and saves until start of next turn. 1/long rest.",
                feature_type="class", mechanic="zealous_presence", uses_per_day=1),
    ],
    14: [
        Feature("Rage Beyond Death", "While raging, you don't die from 0 HP. "
                "Still make death saves; die when rage ends if at 0.",
                feature_type="class", mechanic="rage_beyond_death"),
    ],
}

# --- FIGHTER ---
FIGHTER_ELDRITCH_KNIGHT = {
    3: [
        Feature("Spellcasting (Eldritch Knight)", "Learn wizard spells (abjuration/evocation). "
                "INT-based. Third-caster spell slots.",
                feature_type="class", mechanic="eldritch_knight_spellcasting"),
        Feature("Weapon Bond", "Bonus action: summon bonded weapon to hand. Can't be disarmed.",
                feature_type="class", mechanic="weapon_bond"),
    ],
    7: [
        Feature("War Magic", "After casting cantrip, one weapon attack as bonus action.",
                feature_type="class", mechanic="war_magic"),
    ],
    10: [
        Feature("Eldritch Strike", "After weapon hit, target has disadvantage on next save vs your spell.",
                feature_type="class", mechanic="eldritch_strike"),
    ],
    15: [
        Feature("Arcane Charge", "Teleport 30ft when you Action Surge.",
                feature_type="class", mechanic="arcane_charge"),
    ],
    18: [
        Feature("Improved War Magic", "After casting any spell, one weapon attack as bonus action.",
                feature_type="class", mechanic="improved_war_magic"),
    ],
}

FIGHTER_ARCANE_ARCHER = {
    3: [
        Feature("Arcane Shot", "2 options from Arcane Shot list. 2 uses/short rest.",
                feature_type="class", uses_per_day=2, mechanic="arcane_shot",
                short_rest_recharge=True),
        Feature("Magic Arrow", "Non-magical arrows become +1 magical.",
                feature_type="class", mechanic="magic_arrow"),
    ],
    7: [
        Feature("Curving Shot", "Bonus action: redirect missed arrow at new target within 60ft.",
                feature_type="class", mechanic="curving_shot"),
    ],
    15: [
        Feature("Ever-Ready Shot", "Regain 1 Arcane Shot use on initiative if you have 0 left.",
                feature_type="class", mechanic="ever_ready_shot"),
    ],
}

FIGHTER_CAVALIER = {
    3: [
        Feature("Born to the Saddle", "Advantage on saves to avoid falling off mount.",
                feature_type="class", mechanic="born_to_saddle"),
        Feature("Unwavering Mark", "Melee target is marked. Disadvantage on attacks not targeting "
                "you. Bonus action attack on your turn if it attacks someone else.",
                feature_type="class", mechanic="unwavering_mark"),
    ],
    7: [
        Feature("Warding Maneuver", "Reaction: +1d8 AC to ally within 5ft. STR mod/long rest.",
                feature_type="class", mechanic="warding_maneuver"),
    ],
    10: [
        Feature("Hold the Line", "Creatures provoke OA when moving within your reach (not just leaving).",
                feature_type="class", mechanic="hold_the_line"),
    ],
    15: [
        Feature("Ferocious Charger", "Move 10ft+ straight then hit: target STR save or knocked prone.",
                feature_type="class", mechanic="ferocious_charger"),
    ],
    18: [
        Feature("Vigilant Defender", "Special reaction each turn (not your own) for OA.",
                feature_type="class", mechanic="vigilant_defender"),
    ],
}

FIGHTER_SAMURAI = {
    3: [
        Feature("Fighting Spirit", "Bonus action: advantage on all attacks + 5 temp HP. "
                "3/long rest.",
                feature_type="class", uses_per_day=3, mechanic="fighting_spirit"),
    ],
    7: [
        Feature("Elegant Courtier", "Add WIS mod to persuasion. Proficiency in WIS saves.",
                feature_type="class", mechanic="elegant_courtier"),
    ],
    10: [
        Feature("Tireless Spirit", "Regain 1 Fighting Spirit use on initiative if you have 0.",
                feature_type="class", mechanic="tireless_spirit"),
    ],
    15: [
        Feature("Rapid Strike", "Forgo advantage on one attack to make an extra attack.",
                feature_type="class", mechanic="rapid_strike"),
    ],
    18: [
        Feature("Strength Before Death", "On reaching 0 HP, take an extra turn immediately. "
                "1/long rest.",
                feature_type="class", mechanic="strength_before_death", uses_per_day=1),
    ],
}

# --- PALADIN ---
PALADIN_ANCIENTS = {
    3: [
        Feature("Channel Divinity: Nature's Wrath", "Restrain creature within 10ft (STR/DEX save).",
                feature_type="class", mechanic="natures_wrath"),
        Feature("Channel Divinity: Turn the Faithless", "Fey/fiend within 30ft flee (WIS save).",
                feature_type="class", mechanic="turn_faithless"),
    ],
    7: [
        Feature("Aura of Warding", "You + allies within 10ft: resistance to spell damage.",
                feature_type="class", mechanic="aura_of_warding", aura_radius=10),
    ],
    15: [
        Feature("Undying Sentinel", "When reduced to 0 HP, drop to 1 instead. 1/long rest.",
                feature_type="class", mechanic="undying_sentinel", uses_per_day=1),
    ],
    20: [
        Feature("Elder Champion", "Action: transform for 1 min. Regain 10 HP per turn, "
                "cast paladin spells as bonus action, enemies within 10ft have disadvantage "
                "on saves vs your spells.",
                feature_type="class", mechanic="elder_champion", uses_per_day=1),
    ],
}

PALADIN_CONQUEST = {
    3: [
        Feature("Channel Divinity: Conquering Presence", "Each creature of choice within 30ft: "
                "WIS save or Frightened for 1 min.",
                feature_type="class", mechanic="conquering_presence"),
        Feature("Channel Divinity: Guided Strike", "+10 to one attack roll.",
                feature_type="class", mechanic="guided_strike"),
    ],
    7: [
        Feature("Aura of Conquest", "Frightened creatures within 10ft: speed 0, take psychic "
                "damage = half paladin level at start of turn.",
                feature_type="class", mechanic="aura_of_conquest", aura_radius=10),
    ],
    15: [
        Feature("Scornful Rebuke", "When hit by attack, attacker takes psychic = CHA mod.",
                feature_type="class", mechanic="scornful_rebuke"),
    ],
    20: [
        Feature("Invincible Conqueror", "Action: 1 min, resistance to all damage, extra attack, "
                "crit on 19-20. 1/long rest.",
                feature_type="class", mechanic="invincible_conqueror", uses_per_day=1),
    ],
}

PALADIN_REDEMPTION = {
    3: [
        Feature("Channel Divinity: Emissary of Peace", "+5 to Persuasion for 10 min.",
                feature_type="class", mechanic="emissary_peace"),
        Feature("Channel Divinity: Rebuke the Violent", "When enemy damages ally within 30ft, "
                "attacker takes same radiant damage (WIS save for half).",
                feature_type="class", mechanic="rebuke_violent"),
    ],
    7: [
        Feature("Aura of the Guardian", "Reaction: take damage instead of ally within 10ft.",
                feature_type="class", mechanic="aura_of_guardian", aura_radius=10),
    ],
    15: [
        Feature("Protective Spirit", "Regain 1d6+half paladin level HP at end of turn if below half HP.",
                feature_type="class", mechanic="protective_spirit"),
    ],
    20: [
        Feature("Emissary of Redemption", "Resistance to all damage from other creatures. "
                "Attacker takes radiant = half the damage they dealt.",
                feature_type="class", mechanic="emissary_redemption", uses_per_day=1),
    ],
}

PALADIN_CROWN = {
    3: [
        Feature("Channel Divinity: Champion Challenge", "Each creature within 30ft: "
                "can't move more than 30ft away (WIS save).",
                feature_type="class", mechanic="champion_challenge"),
        Feature("Channel Divinity: Turn the Tide", "Each creature within 30ft that can hear you "
                "regains 1d6+CHA HP (if at half HP or below).",
                feature_type="class", mechanic="turn_the_tide"),
    ],
    7: [
        Feature("Divine Allegiance", "Reaction: take damage instead of ally within 5ft.",
                feature_type="class", mechanic="divine_allegiance"),
    ],
    15: [
        Feature("Unyielding Spirit", "Advantage on saves vs paralyzed and stunned.",
                feature_type="class", mechanic="unyielding_spirit"),
    ],
    20: [
        Feature("Exalted Champion", "Action: 1 hour. Resistance to B/P/S, allies within 30ft "
                "have advantage on death saves and WIS saves. 1/long rest.",
                feature_type="class", mechanic="exalted_champion", uses_per_day=1),
    ],
}

# --- ROGUE ---
ROGUE_ARCANE_TRICKSTER = {
    3: [
        Feature("Spellcasting (Arcane Trickster)", "Learn wizard spells (enchantment/illusion). "
                "INT-based. Third-caster.",
                feature_type="class", mechanic="arcane_trickster_spellcasting"),
        Feature("Mage Hand Legerdemain", "Invisible Mage Hand. Use to steal, pick locks, disarm traps.",
                feature_type="class", mechanic="mage_hand_legerdemain"),
    ],
    9: [
        Feature("Magical Ambush", "Cast spell while hidden: target has disadvantage on save.",
                feature_type="class", mechanic="magical_ambush"),
    ],
    13: [
        Feature("Versatile Trickster", "Bonus action: Mage Hand gives you advantage on attack.",
                feature_type="class", mechanic="versatile_trickster"),
    ],
    17: [
        Feature("Spell Thief", "Reaction: steal spell from caster (save DC 8+INT+prof). 1/long rest.",
                feature_type="class", mechanic="spell_thief", uses_per_day=1),
    ],
}

ROGUE_SWASHBUCKLER = {
    3: [
        Feature("Fancy Footwork", "Melee attack target can't make OA against you that turn.",
                feature_type="class", mechanic="fancy_footwork"),
        Feature("Rakish Audacity", "Add CHA to initiative. Sneak Attack without advantage if "
                "no other creature within 5ft of you (1-on-1).",
                feature_type="class", mechanic="rakish_audacity"),
    ],
    9: [
        Feature("Panache", "WIS (Persuasion) vs WIS (Insight): charmed or goaded.",
                feature_type="class", mechanic="panache"),
    ],
    13: [
        Feature("Elegant Maneuver", "Bonus action: advantage on next Acrobatics or Athletics check.",
                feature_type="class", mechanic="elegant_maneuver"),
    ],
    17: [
        Feature("Master Duelist", "Miss an attack: re-roll with advantage. 1/short rest.",
                feature_type="class", mechanic="master_duelist", uses_per_day=1,
                short_rest_recharge=True),
    ],
}

ROGUE_SCOUT = {
    3: [
        Feature("Skirmisher", "Reaction: move half speed without OA when enemy ends turn within 5ft.",
                feature_type="class", mechanic="skirmisher"),
        Feature("Survivalist", "Proficiency (expertise) in Nature and Survival.",
                feature_type="class", mechanic="survivalist"),
    ],
    9: [
        Feature("Superior Mobility", "+10ft to speed.",
                feature_type="class", mechanic="superior_mobility"),
    ],
    13: [
        Feature("Ambush Master", "Advantage on initiative. First creature you hit in first round "
                "gives allies advantage on attacks vs it.",
                feature_type="class", mechanic="ambush_master"),
    ],
    17: [
        Feature("Sudden Strike", "Extra Sneak Attack damage on a second creature in same turn.",
                feature_type="class", mechanic="sudden_strike"),
    ],
}

ROGUE_INQUISITIVE = {
    3: [
        Feature("Ear for Deceit", "Minimum 8 on Insight checks.",
                feature_type="class", mechanic="ear_for_deceit"),
        Feature("Eye for Detail", "Bonus action: Perception or Investigation check.",
                feature_type="class", mechanic="eye_for_detail"),
        Feature("Insightful Fighting", "Bonus action: Insight vs Deception. Success: Sneak Attack "
                "that target for 1 min without advantage.",
                feature_type="class", mechanic="insightful_fighting"),
    ],
    9: [
        Feature("Steady Eye", "Advantage on Perception/Investigation if moved half speed or less.",
                feature_type="class", mechanic="steady_eye"),
    ],
    13: [
        Feature("Unerring Eye", "Action: sense illusions, shapechangers, etc. WIS mod/long rest.",
                feature_type="class", mechanic="unerring_eye"),
    ],
    17: [
        Feature("Eye for Weakness", "Insightful Fighting Sneak Attack: +3d6 damage.",
                feature_type="class", mechanic="eye_for_weakness"),
    ],
}

ROGUE_MASTERMIND = {
    3: [
        Feature("Master of Intrigue", "Mimic speech patterns. Proficiency with disguise kit, "
                "forgery kit, one gaming set.",
                feature_type="class", mechanic="master_of_intrigue"),
        Feature("Master of Tactics", "Help action as bonus action, 30ft range.",
                feature_type="class", mechanic="master_of_tactics"),
    ],
    9: [
        Feature("Insightful Manipulator", "1 min study: learn two of creature's INT/WIS/CHA/levels "
                "relative to yours.",
                feature_type="class", mechanic="insightful_manipulator"),
    ],
    13: [
        Feature("Misdirection", "Reaction: redirect attack from you to creature providing cover.",
                feature_type="class", mechanic="misdirection"),
    ],
    17: [
        Feature("Soul of Deceit", "Thoughts can't be read. Deception always succeeds vs truth magic.",
                feature_type="class", mechanic="soul_of_deceit"),
    ],
}

# --- RANGER ---
RANGER_GLOOM_STALKER = {
    3: [
        Feature("Dread Ambusher", "+WIS to initiative. First turn: +10ft speed, extra attack "
                "for +1d8 damage.",
                feature_type="class", mechanic="dread_ambusher"),
        Feature("Umbral Sight", "Darkvision 60ft (or +30ft). Invisible to creatures using darkvision.",
                feature_type="class", mechanic="umbral_sight"),
    ],
    7: [
        Feature("Iron Mind", "Proficiency in WIS saves.",
                feature_type="class", mechanic="iron_mind"),
    ],
    11: [
        Feature("Stalker's Flurry", "Miss an attack: make another weapon attack as part of same action.",
                feature_type="class", mechanic="stalkers_flurry"),
    ],
    15: [
        Feature("Shadowy Dodge", "Reaction: impose disadvantage on attack against you (no advantage).",
                feature_type="class", mechanic="shadowy_dodge"),
    ],
}

RANGER_HORIZON_WALKER = {
    3: [
        Feature("Detect Portal", "Action: sense nearest planar portal within 1 mile. 1/short rest.",
                feature_type="class", mechanic="detect_portal", uses_per_day=1,
                short_rest_recharge=True),
        Feature("Planar Warrior", "Bonus action: mark creature. Next hit deals +1d8 force.",
                feature_type="class", mechanic="planar_warrior", mechanic_value="1d8"),
    ],
    7: [
        Feature("Ethereal Step", "Bonus action: step into Ethereal Plane until end of turn. "
                "1/short rest.",
                feature_type="class", mechanic="ethereal_step", uses_per_day=1,
                short_rest_recharge=True),
    ],
    11: [
        Feature("Distant Strike", "Teleport 10ft before each attack. If attack 2+ targets, "
                "make one extra attack.",
                feature_type="class", mechanic="distant_strike"),
    ],
    15: [
        Feature("Spectral Defense", "Reaction: resistance to all damage from an attack.",
                feature_type="class", mechanic="spectral_defense"),
    ],
}

RANGER_MONSTER_SLAYER = {
    3: [
        Feature("Hunter's Sense", "Action: learn immunities, resistances, vulnerabilities. "
                "WIS mod/long rest.",
                feature_type="class", mechanic="hunters_sense"),
        Feature("Slayer's Prey", "Bonus action: mark creature. +1d6 damage once per turn.",
                feature_type="class", mechanic="slayers_prey", mechanic_value="1d6"),
    ],
    7: [
        Feature("Supernatural Defense", "+1d6 to saves and grapple escapes from Slayer's Prey target.",
                feature_type="class", mechanic="supernatural_defense"),
    ],
    11: [
        Feature("Magic-User's Nemesis", "Reaction: force concentration check or counter teleport/plane shift.",
                feature_type="class", mechanic="magic_users_nemesis"),
    ],
    15: [
        Feature("Slayer's Counter", "Reaction: on target forcing a save, make a weapon attack. "
                "Hit = auto-succeed the save.",
                feature_type="class", mechanic="slayers_counter"),
    ],
}

# --- CLERIC ---
CLERIC_KNOWLEDGE = {
    1: [
        Feature("Blessings of Knowledge", "Proficiency (expertise) in two knowledge skills.",
                feature_type="class", mechanic="blessings_of_knowledge"),
    ],
    2: [
        Feature("Channel Divinity: Knowledge of the Ages", "10 min proficiency with one skill or tool.",
                feature_type="class", mechanic="knowledge_of_ages"),
    ],
    6: [
        Feature("Channel Divinity: Read Thoughts", "Read surface thoughts (WIS save). Then Suggestion.",
                feature_type="class", mechanic="read_thoughts"),
    ],
    8: [
        Feature("Potent Spellcasting", "Add WIS mod to cleric cantrip damage.",
                feature_type="class", mechanic="potent_spellcasting"),
    ],
    17: [
        Feature("Visions of the Past", "Meditate to see past events. 1/short rest.",
                feature_type="class", mechanic="visions_past", uses_per_day=1,
                short_rest_recharge=True),
    ],
}

CLERIC_NATURE = {
    1: [
        Feature("Acolyte of Nature", "Learn one druid cantrip and proficiency in one of "
                "Animal Handling, Nature, Survival.",
                feature_type="class", mechanic="acolyte_of_nature"),
    ],
    2: [
        Feature("Channel Divinity: Charm Animals/Plants", "Charm beasts/plants within 30ft (WIS save).",
                feature_type="class", mechanic="charm_animals_plants"),
    ],
    6: [
        Feature("Dampen Elements", "Reaction: grant resistance to acid/cold/fire/lightning/thunder "
                "to ally within 30ft.",
                feature_type="class", mechanic="dampen_elements"),
    ],
    8: [
        Feature("Divine Strike", "+1d8 cold/fire/lightning damage once per turn.",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Master of Nature", "Command charmed beasts/plants as bonus action.",
                feature_type="class", mechanic="master_of_nature"),
    ],
}

CLERIC_TEMPEST = {
    1: [
        Feature("Wrath of the Storm", "Reaction: when hit by creature within 5ft, 2d8 lightning/thunder "
                "(DEX save for half). WIS mod/long rest.",
                feature_type="class", mechanic="wrath_of_storm"),
    ],
    2: [
        Feature("Channel Divinity: Destructive Wrath", "Max lightning/thunder damage instead of rolling.",
                feature_type="class", mechanic="destructive_wrath"),
    ],
    6: [
        Feature("Thunderbolt Strike", "Lightning damage pushes Large or smaller 10ft.",
                feature_type="class", mechanic="thunderbolt_strike"),
    ],
    8: [
        Feature("Divine Strike", "+1d8 thunder damage once per turn.",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Stormborn", "Fly speed = walking speed when outdoors.",
                feature_type="class", mechanic="stormborn"),
    ],
}

CLERIC_TRICKERY = {
    1: [
        Feature("Blessing of the Trickster", "Touch: advantage on Stealth for 1 hour.",
                feature_type="class", mechanic="blessing_trickster"),
    ],
    2: [
        Feature("Channel Divinity: Invoke Duplicity", "Create illusory double for 1 min. "
                "Advantage on attacks when you and duplicate are within 5ft of target.",
                feature_type="class", mechanic="invoke_duplicity"),
    ],
    6: [
        Feature("Channel Divinity: Cloak of Shadows", "Invisible until end of next turn.",
                feature_type="class", mechanic="cloak_of_shadows"),
    ],
    8: [
        Feature("Divine Strike", "+1d8 poison damage once per turn.",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Improved Duplicity", "Create 4 duplicates instead of 1.",
                feature_type="class", mechanic="improved_duplicity"),
    ],
}

CLERIC_FORGE = {
    1: [
        Feature("Blessing of the Forge", "Long rest: enchant one weapon or armor to +1. Lasts until next long rest.",
                feature_type="class", mechanic="blessing_forge"),
    ],
    2: [
        Feature("Channel Divinity: Artisan's Blessing", "Ritual: create simple metal item up to 100gp.",
                feature_type="class", mechanic="artisans_blessing"),
    ],
    6: [
        Feature("Soul of the Forge", "+1 AC in heavy armor. Resistance to fire damage.",
                feature_type="class", mechanic="soul_of_forge"),
    ],
    8: [
        Feature("Divine Strike", "+1d8 fire damage once per turn.",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8"),
    ],
    17: [
        Feature("Saint of Forge and Fire", "Immune to fire. Resistance to nonmagical B/P/S in heavy armor.",
                feature_type="class", mechanic="saint_forge_fire"),
    ],
}

CLERIC_GRAVE = {
    1: [
        Feature("Circle of Mortality", "Healing spells on 0 HP targets: use max dice. "
                "Spare the Dying as bonus action with 30ft range.",
                feature_type="class", mechanic="circle_of_mortality"),
        Feature("Eyes of the Grave", "Detect undead within 60ft. WIS mod/long rest.",
                feature_type="class", mechanic="eyes_of_grave"),
    ],
    2: [
        Feature("Channel Divinity: Path to the Grave", "Action: mark creature. "
                "Next attack against it has vulnerability to all damage.",
                feature_type="class", mechanic="path_to_grave"),
    ],
    6: [
        Feature("Sentinel at Death's Door", "Reaction: turn critical hit against ally within 30ft "
                "into normal hit. WIS mod/long rest.",
                feature_type="class", mechanic="sentinel_at_deaths_door"),
    ],
    8: [
        Feature("Potent Spellcasting", "Add WIS mod to cleric cantrip damage.",
                feature_type="class", mechanic="potent_spellcasting"),
    ],
    17: [
        Feature("Keeper of Souls", "When a creature within 60ft dies, you or ally within 60ft "
                "regains HP = creature's number of hit dice.",
                feature_type="class", mechanic="keeper_of_souls"),
    ],
}

# --- WIZARD ---
WIZARD_CONJURATION = {
    2: [
        Feature("Minor Conjuration", "Action: conjure non-magical object up to 3ft, 10lbs for 1 hour.",
                feature_type="class", mechanic="minor_conjuration"),
    ],
    6: [
        Feature("Benign Transposition", "Teleport 30ft or swap with willing ally. 1/long rest "
                "or spend conjuration spell slot.",
                feature_type="class", mechanic="benign_transposition"),
    ],
    10: [
        Feature("Focused Conjuration", "Concentration on conjuration spells can't be broken by damage.",
                feature_type="class", mechanic="focused_conjuration"),
    ],
    14: [
        Feature("Durable Summons", "Conjured creatures gain +30 temp HP.",
                feature_type="class", mechanic="durable_summons"),
    ],
}

WIZARD_ENCHANTMENT = {
    2: [
        Feature("Hypnotic Gaze", "Action: charm adjacent creature (WIS save each turn). "
                "Incapacitated and 0 speed.",
                feature_type="class", mechanic="hypnotic_gaze"),
    ],
    6: [
        Feature("Instinctive Charm", "Reaction: redirect attack to another creature (WIS save). 1/long rest.",
                feature_type="class", mechanic="instinctive_charm", uses_per_day=1),
    ],
    10: [
        Feature("Split Enchantment", "Single-target enchantment spells target 2 creatures.",
                feature_type="class", mechanic="split_enchantment"),
    ],
    14: [
        Feature("Alter Memories", "Charmed creature doesn't remember being charmed.",
                feature_type="class", mechanic="alter_memories"),
    ],
}

WIZARD_ILLUSION = {
    2: [
        Feature("Improved Minor Illusion", "Minor Illusion: both sound and image.",
                feature_type="class", mechanic="improved_minor_illusion"),
    ],
    6: [
        Feature("Malleable Illusions", "Action: change the nature of an active illusion.",
                feature_type="class", mechanic="malleable_illusions"),
    ],
    10: [
        Feature("Illusory Self", "Reaction: create illusory double causing attack to miss. 1/short rest.",
                feature_type="class", mechanic="illusory_self", uses_per_day=1,
                short_rest_recharge=True),
    ],
    14: [
        Feature("Illusory Reality", "Bonus action: one inanimate illusory object becomes real for 1 min.",
                feature_type="class", mechanic="illusory_reality"),
    ],
}

WIZARD_NECROMANCY = {
    2: [
        Feature("Grim Harvest", "Kill with spell: regain HP = 2x spell level (3x for necromancy).",
                feature_type="class", mechanic="grim_harvest"),
    ],
    6: [
        Feature("Undead Thralls", "Animate Dead: extra undead. +level HP, +prof to damage.",
                feature_type="class", mechanic="undead_thralls"),
    ],
    10: [
        Feature("Inured to Undeath", "Resistance to necrotic. Max HP can't be reduced.",
                feature_type="class", mechanic="inured_to_undeath"),
    ],
    14: [
        Feature("Command Undead", "Use action to control undead (CHA save for INT 8+).",
                feature_type="class", mechanic="command_undead"),
    ],
}

WIZARD_TRANSMUTATION = {
    2: [
        Feature("Minor Alchemy", "Transform material to another material (wood/stone/iron/copper/silver) "
                "for 1 hour.",
                feature_type="class", mechanic="minor_alchemy"),
    ],
    6: [
        Feature("Transmuter's Stone", "Create a stone granting: darkvision 60ft, +10ft speed, "
                "CON proficiency, or resistance to one element.",
                feature_type="class", mechanic="transmuters_stone"),
    ],
    10: [
        Feature("Shapechanger", "Cast Polymorph on self without spell slot. 1/short rest.",
                feature_type="class", mechanic="shapechanger_wizard", uses_per_day=1,
                short_rest_recharge=True),
    ],
    14: [
        Feature("Master Transmuter", "Destroy Transmuter's Stone for: transform, restore life, "
                "raise dead, or restore youth.",
                feature_type="class", mechanic="master_transmuter"),
    ],
}

WIZARD_WAR_MAGIC = {
    2: [
        Feature("Arcane Deflection", "Reaction: +2 AC or +4 save. Can only cast cantrips next turn.",
                feature_type="class", mechanic="arcane_deflection"),
        Feature("Tactical Wit", "Add INT mod to initiative.",
                feature_type="class", mechanic="tactical_wit"),
    ],
    6: [
        Feature("Power Surge", "Deal +half wizard level force damage once per turn. INT mod charges.",
                feature_type="class", mechanic="power_surge"),
    ],
    10: [
        Feature("Durable Magic", "+2 AC and saves while concentrating.",
                feature_type="class", mechanic="durable_magic"),
    ],
    14: [
        Feature("Deflecting Shroud", "Arcane Deflection: deal 2x wizard level force damage "
                "to up to 3 creatures within 60ft.",
                feature_type="class", mechanic="deflecting_shroud"),
    ],
}

WIZARD_BLADESINGING = {
    2: [
        Feature("Bladesong", "Bonus action: AC + INT, speed + 10, advantage on Acrobatics, "
                "concentration checks + INT. 2/short rest.",
                feature_type="class", uses_per_day=2, mechanic="bladesong",
                short_rest_recharge=True),
    ],
    6: [
        Feature("Extra Attack", "Attack twice when taking the Attack action.",
                feature_type="class", mechanic="extra_attack"),
    ],
    10: [
        Feature("Song of Defense", "While Bladesinging, spend spell slot to reduce damage "
                "by 5x slot level.",
                feature_type="class", mechanic="song_of_defense"),
    ],
    14: [
        Feature("Song of Victory", "While Bladesinging, add INT mod to melee damage.",
                feature_type="class", mechanic="song_of_victory"),
    ],
}

# --- WARLOCK ---
WARLOCK_ARCHFEY = {
    1: [
        Feature("Fey Presence", "Action: charm or frighten creatures in 10ft cube (WIS save). "
                "1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="fey_presence",
                short_rest_recharge=True),
    ],
    6: [
        Feature("Misty Escape", "Reaction: turn invisible and teleport 60ft when damaged. "
                "1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="misty_escape",
                short_rest_recharge=True),
    ],
    10: [
        Feature("Beguiling Defenses", "Immune to charmed. Redirect charm back (WIS save).",
                feature_type="class", mechanic="beguiling_defenses"),
    ],
    14: [
        Feature("Dark Delirium", "Action: charm or frighten one creature for 1 min (WIS save). "
                "1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="dark_delirium",
                short_rest_recharge=True),
    ],
}

WARLOCK_HEXBLADE = {
    1: [
        Feature("Hexblade's Curse", "Bonus action: curse target for 1 min. +prof to damage, "
                "crit on 19-20, regain HP on kill = warlock level + CHA. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="hexblades_curse",
                short_rest_recharge=True),
        Feature("Hex Warrior", "Use CHA for weapon attacks with one weapon (or pact weapon).",
                feature_type="class", mechanic="hex_warrior"),
    ],
    6: [
        Feature("Accursed Specter", "When you kill humanoid, raise as specter ally. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="accursed_specter"),
    ],
    10: [
        Feature("Armor of Hexes", "Cursed target: 4+ on d6, attack misses you.",
                feature_type="class", mechanic="armor_of_hexes"),
    ],
    14: [
        Feature("Master of Hexes", "When cursed target dies, transfer curse to new creature.",
                feature_type="class", mechanic="master_of_hexes"),
    ],
}

WARLOCK_CELESTIAL = {
    1: [
        Feature("Healing Light", "Bonus action: heal creature within 60ft. Pool of d6s = "
                "1 + warlock level.",
                feature_type="class", mechanic="healing_light"),
    ],
    6: [
        Feature("Radiant Soul", "Resistance to radiant. Add CHA mod to radiant/fire spell damage.",
                feature_type="class", mechanic="radiant_soul_warlock"),
    ],
    10: [
        Feature("Celestial Resilience", "You and up to 5 allies gain temp HP = warlock level + CHA "
                "at end of short/long rest.",
                feature_type="class", mechanic="celestial_resilience"),
    ],
    14: [
        Feature("Searing Vengeance", "When making death save, regain half max HP, stand up, "
                "deal 2d8 + CHA radiant to creatures of choice within 30ft. 1/long rest.",
                feature_type="class", mechanic="searing_vengeance", uses_per_day=1),
    ],
}

# --- SORCERER ---
SORCERER_DIVINE_SOUL = {
    1: [
        Feature("Divine Magic", "Learn cleric spells. Bonus spell from affinity.",
                feature_type="class", mechanic="divine_magic"),
        Feature("Favored by the Gods", "Failed save or missed attack: +2d4. 1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="favored_by_gods",
                short_rest_recharge=True),
    ],
    6: [
        Feature("Empowered Healing", "1 sorcery point: re-roll healing dice for self or ally within 5ft.",
                feature_type="class", mechanic="empowered_healing"),
    ],
    14: [
        Feature("Otherworldly Wings", "Bonus action: spectral wings, fly speed 30ft.",
                feature_type="class", mechanic="otherworldly_wings"),
    ],
    18: [
        Feature("Unearthly Recovery", "Bonus action: regain HP = half max HP when below half. 1/long rest.",
                feature_type="class", mechanic="unearthly_recovery", uses_per_day=1),
    ],
}

SORCERER_SHADOW = {
    1: [
        Feature("Eyes of the Dark", "Darkvision 120ft. Darkness spell for 2 sorcery points at 3rd.",
                feature_type="class", mechanic="eyes_of_dark"),
        Feature("Strength of the Grave", "Drop to 1 HP instead of 0 (CHA save DC = 5 + damage). "
                "Not radiant damage. 1/long rest.",
                feature_type="class", uses_per_day=1, mechanic="strength_of_grave"),
    ],
    6: [
        Feature("Hound of Ill Omen", "3 sorcery points: summon shadow hound.",
                feature_type="class", mechanic="hound_of_ill_omen"),
    ],
    14: [
        Feature("Shadow Walk", "Bonus action: teleport 120ft between dim light/darkness.",
                feature_type="class", mechanic="shadow_walk"),
    ],
    18: [
        Feature("Umbral Form", "6 sorcery points: shadow form for 1 min. Resistance to all damage "
                "except force/radiant. Move through objects.",
                feature_type="class", mechanic="umbral_form"),
    ],
}

SORCERER_STORM = {
    1: [
        Feature("Wind Speaker", "Speak Primordial and its dialects.",
                feature_type="class", mechanic="wind_speaker"),
        Feature("Tempestuous Magic", "Bonus action: fly 10ft without OA after casting leveled spell.",
                feature_type="class", mechanic="tempestuous_magic"),
    ],
    6: [
        Feature("Heart of the Storm", "Resistance to lightning and thunder. When casting spell that "
                "deals lightning/thunder, deal level/2 lightning/thunder to creatures of choice within 10ft.",
                feature_type="class", mechanic="heart_of_storm"),
        Feature("Storm Guide", "Bonus action: control rain/wind direction in 20ft radius.",
                feature_type="class", mechanic="storm_guide"),
    ],
    14: [
        Feature("Storm's Fury", "Reaction: when hit by melee, deal lightning = sorcerer level. "
                "STR save or pushed 20ft.",
                feature_type="class", mechanic="storms_fury"),
    ],
    18: [
        Feature("Wind Soul", "Immunity to lightning and thunder. Fly speed 60ft. "
                "Action: 30ft fly speed to 3+CHA allies for 1 hour. 1/short rest.",
                feature_type="class", mechanic="wind_soul", uses_per_day=1,
                short_rest_recharge=True),
    ],
}

# --- BARD ---
BARD_SWORDS = {
    3: [
        Feature("Blade Flourish", "Attack action: +10ft speed. Expend Bardic Inspiration for "
                "Defensive (AC), Slashing (extra damage+target), Mobile (push 5ft+disengage).",
                feature_type="class", mechanic="blade_flourish"),
        Feature("Fighting Style", "Dueling or Two-Weapon Fighting.",
                feature_type="class", mechanic="fighting_style_bard"),
    ],
    6: [
        Feature("Extra Attack", "Attack twice when taking the Attack action.",
                feature_type="class", mechanic="extra_attack"),
    ],
    14: [
        Feature("Master's Flourish", "Use d6 instead of Bardic Inspiration die for Flourish (no cost).",
                feature_type="class", mechanic="masters_flourish"),
    ],
}

BARD_WHISPERS = {
    3: [
        Feature("Psychic Blades", "Expend Bardic Inspiration: +2d6 psychic on weapon hit (3d6@5, "
                "5d6@10, 8d6@15).",
                feature_type="class", mechanic="psychic_blades"),
    ],
    6: [
        Feature("Mantle of Whispers", "Reaction: capture dying humanoid's shadow. "
                "Assume their appearance.",
                feature_type="class", mechanic="mantle_of_whispers"),
    ],
    14: [
        Feature("Shadow Lore", "Action: whisper to creature. Charmed for 8 hours, obeys (WIS save). "
                "1/long rest.",
                feature_type="class", mechanic="shadow_lore", uses_per_day=1),
    ],
}

BARD_GLAMOUR = {
    3: [
        Feature("Mantle of Inspiration", "Bonus action: spend Bardic Inspiration. "
                "CHA mod creatures gain 5 temp HP and move reaction without OA.",
                feature_type="class", mechanic="mantle_of_inspiration"),
        Feature("Enthralling Performance", "Perform 1 min: charm humanoids (WIS save). "
                "1/short rest.",
                feature_type="class", mechanic="enthralling_performance", uses_per_day=1,
                short_rest_recharge=True),
    ],
    6: [
        Feature("Mantle of Majesty", "Bonus action: Command as bonus action for 1 min. "
                "1/long rest.",
                feature_type="class", mechanic="mantle_of_majesty", uses_per_day=1),
    ],
    14: [
        Feature("Unbreakable Majesty", "Bonus action: creatures must CHA save to attack you "
                "or pick another target. 1 min. 1/short rest.",
                feature_type="class", mechanic="unbreakable_majesty", uses_per_day=1,
                short_rest_recharge=True),
    ],
}

# --- DRUID ---
DRUID_DREAMS = {
    2: [
        Feature("Balm of the Summer Court", "Bonus action: heal ally within 120ft. "
                "Pool of d6s = druid level.",
                feature_type="class", mechanic="balm_summer_court"),
    ],
    6: [
        Feature("Hearth of Moonlight and Shadow", "Short/long rest: 30ft invisible sphere. "
                "+5 to Stealth and Perception.",
                feature_type="class", mechanic="hearth_moonlight"),
    ],
    10: [
        Feature("Hidden Paths", "Bonus action: teleport 60ft or teleport willing ally 30ft. "
                "WIS mod/long rest.",
                feature_type="class", mechanic="hidden_paths"),
    ],
    14: [
        Feature("Walker in Dreams", "After short rest: Dream, Scrying, or Teleportation Circle. "
                "1/long rest.",
                feature_type="class", mechanic="walker_in_dreams", uses_per_day=1),
    ],
}

DRUID_SHEPHERD = {
    2: [
        Feature("Spirit Totem", "Bonus action: 60ft spirit aura for 1 min. "
                "Bear=temp HP, Hawk=advantage on perception/advantage on attacks, Unicorn=heal. "
                "1/short rest.",
                feature_type="class", uses_per_day=1, mechanic="spirit_totem",
                short_rest_recharge=True),
    ],
    6: [
        Feature("Mighty Summoner", "Summoned creatures: +2 HP per hit die, attacks are magical.",
                feature_type="class", mechanic="mighty_summoner"),
    ],
    10: [
        Feature("Guardian Spirit", "Summoned/created beasts/fey within aura regain half druid level HP.",
                feature_type="class", mechanic="guardian_spirit"),
    ],
    14: [
        Feature("Faithful Summons", "When reduced to 0 HP, Conjure Animals (8 beasts CR 1/4). "
                "1/long rest.",
                feature_type="class", mechanic="faithful_summons", uses_per_day=1),
    ],
}

DRUID_SPORES = {
    2: [
        Feature("Halo of Spores", "Reaction: creature within 10ft takes 1d4 necrotic (CON save).",
                feature_type="class", mechanic="halo_of_spores", mechanic_value="1d4"),
        Feature("Symbiotic Entity", "Action: spend Wild Shape. 4 x druid level temp HP. "
                "Halo of Spores +1d6, melee +1d6 poison.",
                feature_type="class", mechanic="symbiotic_entity"),
    ],
    6: [
        Feature("Fungal Infestation", "Reaction: animate dead humanoid with 1 HP for 1 hour. "
                "WIS mod/long rest.",
                feature_type="class", mechanic="fungal_infestation"),
    ],
    10: [
        Feature("Spreading Spores", "Bonus action: Halo of Spores in 10ft cube within 30ft.",
                feature_type="class", mechanic="spreading_spores"),
    ],
    14: [
        Feature("Fungal Body", "Can't be blinded, deafened, frightened, or poisoned. "
                "Crits are normal hits.",
                feature_type="class", mechanic="fungal_body"),
    ],
}

# --- MONK ---
MONK_FOUR_ELEMENTS = {
    3: [
        Feature("Disciple of the Elements", "Spend ki for elemental disciplines. "
                "Learn Elemental Attunement + one discipline.",
                feature_type="class", mechanic="elemental_disciplines"),
    ],
    6: [
        Feature("Extra Discipline", "Learn one additional elemental discipline.",
                feature_type="class", mechanic="extra_discipline_6"),
    ],
    11: [
        Feature("Extra Discipline", "Learn one additional elemental discipline.",
                feature_type="class", mechanic="extra_discipline_11"),
    ],
    17: [
        Feature("Extra Discipline", "Learn one additional elemental discipline.",
                feature_type="class", mechanic="extra_discipline_17"),
    ],
}

MONK_DRUNKEN_MASTER = {
    3: [
        Feature("Drunken Technique", "Flurry of Blows: Disengage and +10ft speed.",
                feature_type="class", mechanic="drunken_technique"),
    ],
    6: [
        Feature("Tipsy Sway", "Redirect missed melee attack to adjacent creature. "
                "Stand up for 5ft movement.",
                feature_type="class", mechanic="tipsy_sway"),
    ],
    11: [
        Feature("Drunkard's Luck", "Spend 2 ki: cancel disadvantage on roll.",
                feature_type="class", mechanic="drunkards_luck"),
    ],
    17: [
        Feature("Intoxicated Frenzy", "Flurry of Blows: up to 5 attacks (each different target).",
                feature_type="class", mechanic="intoxicated_frenzy"),
    ],
}

MONK_KENSEI = {
    3: [
        Feature("Path of the Kensei", "Choose 2 kensei weapons (1 melee, 1 ranged). +2 AC on "
                "unarmed attack while holding kensei melee. +1d4 on ranged kensei weapon.",
                feature_type="class", mechanic="path_of_kensei"),
    ],
    6: [
        Feature("One with the Blade", "Kensei weapons count as magical. "
                "Deft Strike: 1 ki for +martial arts die damage.",
                feature_type="class", mechanic="one_with_blade"),
    ],
    11: [
        Feature("Sharpen the Blade", "Bonus action: 1-3 ki for +1 to +3 weapon. 1 min.",
                feature_type="class", mechanic="sharpen_blade"),
    ],
    17: [
        Feature("Unerring Accuracy", "Miss with monk weapon: re-roll. 1/turn.",
                feature_type="class", mechanic="unerring_accuracy"),
    ],
}

MONK_SUN_SOUL = {
    3: [
        Feature("Radiant Sun Bolt", "Ranged attack (30ft): 1d4+DEX radiant. "
                "Can replace unarmed strike.",
                feature_type="class", mechanic="radiant_sun_bolt"),
    ],
    6: [
        Feature("Searing Arc Strike", "After Attack: spend 2+ ki for Burning Hands at that level.",
                feature_type="class", mechanic="searing_arc_strike"),
    ],
    11: [
        Feature("Searing Sunburst", "Action: 20ft radius, 150ft range. 2d6 radiant (CON save). "
                "Spend 1-3 ki for +2d6 each.",
                feature_type="class", mechanic="searing_sunburst"),
    ],
    17: [
        Feature("Sun Shield", "Shed 30ft bright light (toggle). When hit by melee while glowing: "
                "5+WIS radiant damage.",
                feature_type="class", mechanic="sun_shield"),
    ],
}

MONK_LONG_DEATH = {
    3: [
        Feature("Touch of Death", "When you reduce a creature to 0 HP within 5ft, "
                "gain temp HP = WIS mod + monk level.",
                feature_type="class", mechanic="touch_of_death"),
    ],
    6: [
        Feature("Hour of Reaping", "Action: frighten creatures that can see you within 30ft (WIS save).",
                feature_type="class", mechanic="hour_of_reaping"),
    ],
    11: [
        Feature("Mastery of Death", "Spend 1 ki: drop to 1 HP instead of 0.",
                feature_type="class", mechanic="mastery_of_death"),
    ],
    17: [
        Feature("Touch of the Long Death", "10 ki max: 2d10 necrotic per ki point (CON save for half).",
                feature_type="class", mechanic="touch_long_death"),
    ],
}

# ============================================================
# TASHA'S CAULDRON OF EVERYTHING (TCoE) SUBCLASSES
# ============================================================

# --- BARBARIAN (TCoE) ---
BARBARIAN_BEAST = {
    3: [
        Feature("Form of the Beast", "When you rage, choose: Bite (1d8 piercing, regain HP = prof bonus "
                "when below half HP), Claws (1d6 slashing, extra claw attack when you attack), or "
                "Tail (1d8 piercing, +1d8 AC reaction).",
                feature_type="class", mechanic="form_of_the_beast"),
    ],
    6: [
        Feature("Bestial Soul", "Natural weapons count as magical. Choose: swimming (= walk speed), "
                "climbing (= walk speed), or jump distance increases.",
                feature_type="class", mechanic="bestial_soul"),
    ],
    10: [
        Feature("Infectious Fury", "When you hit with natural weapons, target makes WIS save "
                "(DC 8+prof+CON) or uses reaction to attack an ally, or takes 2d12 psychic. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="infectious_fury",
                save_ability="Wisdom", damage_dice="2d12", damage_type="psychic"),
    ],
    14: [
        Feature("Call the Hunt", "When you rage, choose prof bonus allies within 30ft. Each gains +1d6 "
                "damage once per turn. You gain 5 temp HP per ally.",
                feature_type="class", mechanic="call_the_hunt"),
    ],
}

BARBARIAN_WILD_MAGIC_BARB = {
    3: [
        Feature("Magic Awareness", "Action: detect spells/magic items within 60ft. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="magic_awareness"),
        Feature("Wild Surge", "When you rage, roll d8 for a random magical effect: "
                "teleport, AoE burst, weapon flare, etc.",
                feature_type="class", mechanic="wild_surge"),
    ],
    6: [
        Feature("Bolstering Magic", "Action: touch ally for +1d3 to attacks/checks for 10 min, "
                "or restore an expended spell slot (up to 3rd level). Prof bonus uses/long rest.",
                feature_type="class", mechanic="bolstering_magic"),
    ],
    10: [
        Feature("Unstable Backlash", "Reaction when damaged or failing save while raging: "
                "replace current Wild Surge effect with a new one (roll new d8).",
                feature_type="class", mechanic="unstable_backlash"),
    ],
    14: [
        Feature("Controlled Surge", "When you roll on Wild Magic table, roll twice and choose "
                "which effect to use.",
                feature_type="class", mechanic="controlled_surge"),
    ],
}

# --- FIGHTER (TCoE) ---
FIGHTER_PSI_WARRIOR = {
    3: [
        Feature("Psionic Power", "Psionic Energy dice (d6, = prof bonus dice). "
                "Protective Field (reaction: reduce damage to self/ally within 30ft by 1d6+INT), "
                "Psionic Strike (+1d6 force on weapon hit), "
                "Telekinetic Movement (move object/creature 30ft).",
                feature_type="class", mechanic="psionic_power", mechanic_value="1d6"),
    ],
    7: [
        Feature("Telekinetic Adept", "Psi-Powered Leap (fly speed = 2x walk, bonus action), "
                "Telekinetic Thrust (push target 10ft + knock prone on Psionic Strike, STR save).",
                feature_type="class", mechanic="telekinetic_adept"),
    ],
    10: [
        Feature("Guarded Mind", "Resistance to psychic damage. Spend Psionic Energy die to end "
                "Charmed/Frightened on yourself.",
                feature_type="class", mechanic="guarded_mind"),
    ],
    15: [
        Feature("Bulwark of Force", "Bonus action: create half cover for prof bonus creatures "
                "within 30ft. Lasts 1 minute. 1/long rest or spend Psionic Energy die.",
                feature_type="class", mechanic="bulwark_of_force"),
    ],
    18: [
        Feature("Telekinetic Master", "Cast Telekinesis (no components). 1/long rest or spend "
                "Psionic Energy die. While concentrating, bonus action telekinetic weapon attack.",
                feature_type="class", mechanic="telekinetic_master"),
    ],
}

FIGHTER_RUNE_KNIGHT = {
    3: [
        Feature("Rune Carver", "Learn 2 runes (from: Cloud, Fire, Frost, Stone, Hill, Storm). "
                "Each has a passive effect + 1/short rest activation.",
                feature_type="class", mechanic="rune_carver"),
        Feature("Giant's Might", "Bonus action: become Large for 1 min, advantage on STR checks/saves, "
                "+1d6 damage once per turn. Prof bonus uses/long rest.",
                feature_type="class", mechanic="giants_might", mechanic_value="1d6"),
    ],
    7: [
        Feature("Runic Shield", "Reaction: when ally within 60ft is hit, force reroll of attack. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="runic_shield"),
    ],
    10: [
        Feature("Great Stature", "Height increases 3d4 inches. Giant's Might bonus becomes 1d8.",
                feature_type="class", mechanic="giants_might", mechanic_value="1d8"),
    ],
    15: [
        Feature("Master of Runes", "Each rune can be invoked twice per short rest.",
                feature_type="class", mechanic="master_of_runes"),
    ],
    18: [
        Feature("Runic Juggernaut", "Giant's Might makes you Huge. Bonus becomes 1d10. "
                "+5 reach when Large/Huge.",
                feature_type="class", mechanic="giants_might", mechanic_value="1d10"),
    ],
}

# --- PALADIN (TCoE) ---
PALADIN_GLORY = {
    3: [
        Feature("Peerless Athlete", "Channel Divinity: bonus action, 10 min. Advantage on Athletics "
                "and Acrobatics. Carry/push/lift doubled. Long/high jump +10ft.",
                feature_type="class", mechanic="channel_divinity", uses_per_day=1,
                short_rest_recharge=True),
        Feature("Inspiring Smite", "Channel Divinity: after Divine Smite, distribute 2d8+paladin level "
                "temp HP among creatures within 30ft.",
                feature_type="class", mechanic="inspiring_smite"),
    ],
    7: [
        Feature("Aura of Alacrity", "Your walking speed increases by 10ft. Allies within 5ft "
                "(10ft at 18th) gain +10ft speed.",
                feature_type="class", mechanic="aura_of_alacrity", aura_radius=5),
    ],
    15: [
        Feature("Glorious Defense", "Reaction: when you or ally within 10ft is hit, add CHA mod to AC. "
                "If attack misses, melee weapon attack against attacker. CHA mod uses/long rest.",
                feature_type="class", mechanic="glorious_defense"),
    ],
    20: [
        Feature("Living Legend", "Bonus action: 1 minute. Advantage on CHA checks, misses become hits "
                "once per turn, gain Haste-like emanation. 1/long rest.",
                feature_type="class", mechanic="living_legend"),
    ],
}

PALADIN_WATCHERS = {
    3: [
        Feature("Watcher's Will", "Channel Divinity: action, choose prof bonus creatures within 30ft. "
                "Advantage on INT/WIS/CHA saves for 1 minute.",
                feature_type="class", mechanic="channel_divinity", uses_per_day=1,
                short_rest_recharge=True),
        Feature("Abjure the Extraplanar", "Channel Divinity: action, each aberration/celestial/"
                "elemental/fey/fiend within 30ft makes WIS save or turned for 1 minute.",
                feature_type="class", mechanic="abjure_extraplanar",
                save_ability="Wisdom"),
    ],
    7: [
        Feature("Aura of the Sentinel", "You and allies within 10ft gain +prof bonus to initiative.",
                feature_type="class", mechanic="aura_of_sentinel", aura_radius=10),
    ],
    15: [
        Feature("Vigilant Rebuke", "Reaction: when you or ally within 30ft succeeds on INT/WIS/CHA save, "
                "deal 2d8+CHA mod force damage to the creature that forced the save.",
                feature_type="class", mechanic="vigilant_rebuke",
                damage_dice="2d8", damage_type="force"),
    ],
    20: [
        Feature("Mortal Bulwark", "Bonus action: 1 minute. Truesight 120ft, advantage on attacks "
                "vs aberrations/celestials/elementals/fey/fiends, banish on hit (CHA save).",
                feature_type="class", mechanic="mortal_bulwark"),
    ],
}

# --- ROGUE (TCoE) ---
ROGUE_PHANTOM = {
    3: [
        Feature("Whispers of the Dead", "After rest, gain proficiency in one skill or tool. "
                "Changes after next rest.",
                feature_type="class", mechanic="whispers_of_dead"),
        Feature("Wails from the Grave", "After Sneak Attack, deal half Sneak Attack dice "
                "as necrotic damage to a second creature within 30ft of first target. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="wails_from_grave"),
    ],
    9: [
        Feature("Tokens of the Departed", "When a creature within 30ft dies, reaction to capture "
                "soul trinket. Advantage on death saves and CON saves while you have one. "
                "Destroy to ask one question of the spirit.",
                feature_type="class", mechanic="tokens_of_departed"),
    ],
    13: [
        Feature("Ghost Walk", "Bonus action: spectral form for 10 min. Fly 10ft, move through "
                "creatures/objects. 1/long rest or destroy soul trinket.",
                feature_type="class", mechanic="ghost_walk"),
    ],
    17: [
        Feature("Death's Friend", "Wails from the Grave no longer limited by uses. "
                "If you don't have a soul trinket at end of long rest, one appears.",
                feature_type="class", mechanic="deaths_friend"),
    ],
}

ROGUE_SOULKNIFE = {
    3: [
        Feature("Psionic Power (Soulknife)", "Psi Energy dice (d6 = prof bonus). "
                "Psi-Bolstered Knack: add die to failed skill check. "
                "Psychic Whispers: telepathy with prof bonus creatures for hours.",
                feature_type="class", mechanic="psionic_power_rogue", mechanic_value="1d6"),
        Feature("Psychic Blades", "Manifest psychic blades as simple melee weapons. "
                "Attack: 1d6+ability mod psychic. Bonus action: 1d4+ability mod psychic second blade. "
                "60ft thrown range. Vanish after use.",
                feature_type="class", mechanic="psychic_blades"),
    ],
    9: [
        Feature("Soul Blades", "Homing Strikes: spend Psi die to add to missed attack roll. "
                "Psychic Teleportation: bonus action, throw blade and teleport to it (Psi die x10 ft).",
                feature_type="class", mechanic="soul_blades"),
    ],
    13: [
        Feature("Psychic Veil", "Bonus action: invisible for 1 hour or until you damage/force save. "
                "1/long rest or spend Psi die.",
                feature_type="class", mechanic="psychic_veil"),
    ],
    17: [
        Feature("Rend Mind", "After Psychic Blades hit, force WIS save (DC 8+prof+DEX) or "
                "Stunned for 1 minute (repeat save end of turns). 1/long rest or spend 3 Psi dice.",
                feature_type="class", mechanic="rend_mind",
                save_ability="Wisdom", applies_condition="Stunned"),
    ],
}

# --- RANGER (TCoE) ---
RANGER_FEY_WANDERER = {
    3: [
        Feature("Dreadful Strikes", "Once per turn, weapon attacks deal extra 1d4 psychic damage "
                "(1d6 at 11th level). Each creature can only take this once per turn.",
                feature_type="class", mechanic="dreadful_strikes", mechanic_value="1d4"),
        Feature("Otherworldly Glamour", "Add WIS mod to CHA checks. Gain one CHA skill proficiency.",
                feature_type="class", mechanic="otherworldly_glamour"),
    ],
    7: [
        Feature("Beguiling Twist", "Reaction: when you or ally within 120ft saves vs Charmed/Frightened, "
                "redirect to different creature within 120ft. WIS save or Charmed/Frightened for 1 minute.",
                feature_type="class", mechanic="beguiling_twist",
                save_ability="Wisdom"),
    ],
    11: [
        Feature("Fey Reinforcements", "Cast Summon Fey (no material component, concentration). "
                "1/long rest or spend spell slot of 3rd+.",
                feature_type="class", mechanic="fey_reinforcements"),
        Feature("Dreadful Strikes (Improved)", "Dreadful Strikes damage increases to 1d6.",
                feature_type="class", mechanic="dreadful_strikes", mechanic_value="1d6"),
    ],
    15: [
        Feature("Misty Wanderer", "Cast Misty Step without slot, WIS mod times/long rest. "
                "Can bring willing ally within 5ft.",
                feature_type="class", mechanic="misty_wanderer"),
    ],
}

RANGER_SWARMKEEPER = {
    3: [
        Feature("Gathered Swarm", "Once per turn on hit: deal extra 1d6 piercing, OR "
                "move target 15ft horizontally (STR save), OR move yourself 5ft (no OA). "
                "Swarm is fey spirits/tiny beasts.",
                feature_type="class", mechanic="gathered_swarm", mechanic_value="1d6"),
    ],
    7: [
        Feature("Writhing Tide", "Bonus action: gain hover fly speed 10ft for 1 minute. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="writhing_tide"),
    ],
    11: [
        Feature("Mighty Swarm", "Gathered Swarm damage becomes 1d8. Push now knocks Prone. "
                "Self-move gains half cover until start of next turn.",
                feature_type="class", mechanic="gathered_swarm", mechanic_value="1d8"),
    ],
    15: [
        Feature("Swarming Dispersal", "Reaction when hit: become swarm, teleport 30ft, "
                "resistance to attack damage. Prof bonus uses/long rest.",
                feature_type="class", mechanic="swarming_dispersal"),
    ],
}

# --- CLERIC (TCoE) ---
CLERIC_ORDER = {
    1: [
        Feature("Voice of Authority", "When you cast a spell with a slot targeting an ally, "
                "that ally can use reaction to make one weapon attack.",
                feature_type="class", mechanic="voice_of_authority"),
    ],
    2: [
        Feature("Order's Demand", "Channel Divinity: each creature of your choice within 30ft "
                "makes WIS save or Charmed until end of your next turn or takes damage. "
                "You can also drop Charmed creatures Prone.",
                feature_type="class", mechanic="channel_divinity", uses_per_day=1,
                short_rest_recharge=True, save_ability="Wisdom",
                applies_condition="Charmed"),
    ],
    6: [
        Feature("Embodiment of the Law", "When you cast an Enchantment spell of 1st level or higher, "
                "change casting time from action to bonus action. WIS mod uses/long rest.",
                feature_type="class", mechanic="embodiment_of_law"),
    ],
    8: [
        Feature("Divine Strike (Order)", "Once per turn, +1d8 psychic damage on weapon hit (2d8 at 14th).",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8",
                damage_type="psychic"),
    ],
    17: [
        Feature("Order's Wrath", "When you deal Divine Strike damage, curse target. "
                "Next ally attack deals extra 2d8 psychic damage. Once per turn.",
                feature_type="class", mechanic="orders_wrath",
                damage_dice="2d8", damage_type="psychic"),
    ],
}

CLERIC_PEACE = {
    1: [
        Feature("Emboldening Bond", "Action: bond prof bonus creatures within 30ft for 10 min. "
                "Once per turn, bonded creature within 30ft of another can add 1d4 to attack/check/save. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="emboldening_bond"),
    ],
    2: [
        Feature("Balm of Peace", "Channel Divinity: move up to your speed without provoking OA. "
                "Heal each creature within 5ft that you pass by 2d6+WIS mod.",
                feature_type="class", mechanic="channel_divinity", uses_per_day=1,
                short_rest_recharge=True),
    ],
    6: [
        Feature("Protective Bond", "Bonded creature can use reaction to teleport to within 5ft "
                "of bonded ally that takes damage, taking all the damage instead. "
                "At 17th, creature gains resistance to transferred damage.",
                feature_type="class", mechanic="protective_bond"),
    ],
    8: [
        Feature("Potent Spellcasting (Peace)", "Add WIS mod to cantrip damage.",
                feature_type="class", mechanic="potent_spellcasting"),
    ],
    17: [
        Feature("Expansive Bond", "Bond range increases to 60ft. When bonded creature takes damage, "
                "any bonded creature can teleport to absorb (with resistance).",
                feature_type="class", mechanic="expansive_bond"),
    ],
}

CLERIC_TWILIGHT = {
    1: [
        Feature("Eyes of Night", "Darkvision 300ft, share with WIS mod creatures within 10ft. "
                "1/long rest (or spell slot).",
                feature_type="class", mechanic="eyes_of_night"),
    ],
    2: [
        Feature("Twilight Sanctuary", "Channel Divinity: action, create 30ft sphere of dim light "
                "centered on you. Each turn, allies in sphere gain 1d6+cleric level temp HP, "
                "or end Charmed/Frightened. Lasts 1 minute.",
                feature_type="class", mechanic="channel_divinity", uses_per_day=1,
                short_rest_recharge=True, aura_radius=30),
    ],
    6: [
        Feature("Steps of Night", "Bonus action: fly speed = walk speed in dim light/darkness for 1 min. "
                "Prof bonus uses/long rest.",
                feature_type="class", mechanic="steps_of_night"),
    ],
    8: [
        Feature("Divine Strike (Twilight)", "Once per turn, +1d8 radiant damage on weapon hit (2d8 at 14th).",
                feature_type="class", mechanic="divine_strike", mechanic_value="1d8",
                damage_type="radiant"),
    ],
    17: [
        Feature("Twilight Shroud", "Twilight Sanctuary also grants half cover to allies within it.",
                feature_type="class", mechanic="twilight_shroud"),
    ],
}

# --- WIZARD (TCoE) ---
WIZARD_ORDER_OF_SCRIBES = {
    2: [
        Feature("Wizardly Quill", "Bonus action: create Tiny quill. Write spells in 2 min/level "
                "(instead of 2 hours). Erase anything you write.",
                feature_type="class", mechanic="wizardly_quill"),
        Feature("Awakened Spellbook", "Replace damage type of a spell with another from your spellbook "
                "(must be same level). Cast ritual spells in normal casting time.",
                feature_type="class", mechanic="awakened_spellbook"),
    ],
    6: [
        Feature("Manifest Mind", "Bonus action: manifest spellbook as Tiny spectral within 60ft. "
                "Cast spells from its location. Move it 30ft/bonus action. Prof bonus casts/long rest.",
                feature_type="class", mechanic="manifest_mind"),
    ],
    10: [
        Feature("Master Scrivener", "Create spell scroll of 1st or 2nd level (1 min, 1/long rest). "
                "Scroll is cast at minimum level +1. Scroll doesn't use slot to cast.",
                feature_type="class", mechanic="master_scrivener"),
    ],
    14: [
        Feature("One with the Word", "Advantage on Arcana checks. Reaction when you take damage: "
                "reduce to 0 and lose spells from spellbook (3d6 levels worth). "
                "1/long rest. Needs 1st-level spell per lost level to restore.",
                feature_type="class", mechanic="one_with_the_word"),
    ],
}

# --- WARLOCK (TCoE) ---
WARLOCK_FATHOMLESS = {
    1: [
        Feature("Tentacle of the Deeps", "Bonus action: create 10ft tentacle within 60ft. "
                "When created + bonus action each turn: melee spell attack, 1d8 cold, "
                "reduce speed by 10ft. Prof bonus uses/long rest.",
                feature_type="class", mechanic="tentacle_of_deeps",
                damage_dice="1d8", damage_type="cold"),
    ],
    6: [
        Feature("Oceanic Soul", "Resistance to cold damage. Breathe underwater, swim speed = walk.",
                feature_type="class", mechanic="oceanic_soul"),
        Feature("Guardian Coil", "Reaction: when you or ally within 10ft of tentacle takes damage, "
                "reduce by 1d8.",
                feature_type="class", mechanic="guardian_coil"),
    ],
    10: [
        Feature("Grasping Tentacles", "Cast Evard's Black Tentacles 1/long rest without a slot. "
                "While concentrating on it, gain temp HP = warlock level at start of each turn. "
                "Tentacle of the Deeps damage increases to 2d8.",
                feature_type="class", mechanic="grasping_tentacles",
                damage_dice="2d8"),
    ],
    14: [
        Feature("Fathomless Plunge", "Action: teleport yourself and up to 5 willing creatures "
                "within 30ft to a body of water you've seen (up to 1 mile). 1/short rest.",
                feature_type="class", mechanic="fathomless_plunge"),
    ],
}

WARLOCK_GENIE = {
    1: [
        Feature("Genie's Vessel", "Bonus action: enter Tiny vessel (extradimensional space) for "
                "prof bonus x2 hours. Genie's Wrath: once per turn, deal extra prof bonus damage "
                "of your genie type on hit.",
                feature_type="class", mechanic="genies_wrath"),
    ],
    6: [
        Feature("Elemental Gift", "Resistance to genie's damage type. Bonus action: fly speed 30ft "
                "for 10 min. Prof bonus uses/long rest.",
                feature_type="class", mechanic="elemental_gift"),
    ],
    10: [
        Feature("Sanctuary Vessel", "When you enter vessel, choose 5 willing creatures within 30ft. "
                "All gain benefits of short rest when you exit. Bonus: +prof bonus to HP restored.",
                feature_type="class", mechanic="sanctuary_vessel"),
    ],
    14: [
        Feature("Limited Wish", "Request the effect of a 6th-level or lower spell with casting time "
                "of 1 action. No material components needed. 1d4 long rests to recharge.",
                feature_type="class", mechanic="limited_wish"),
    ],
}

# --- SORCERER (TCoE) ---
SORCERER_ABERRANT_MIND = {
    1: [
        Feature("Psionic Spells", "Learn extra spells: Arms of Hadar, Dissonant Whispers, Mind Sliver. "
                "At higher levels: Calm Emotions, Detect Thoughts, Hunger of Hadar, Sending, "
                "Evard's Black Tentacles, Summon Aberration, Telekinesis, Modify Memory.",
                feature_type="class", mechanic="psionic_spells"),
        Feature("Telepathic Speech", "Bonus action: telepathy with one creature within 30ft "
                "for sorcerer level minutes. Shared language not required.",
                feature_type="class", mechanic="telepathic_speech"),
    ],
    6: [
        Feature("Psionic Sorcery", "Cast Psionic Spell spells using sorcery points (= spell level) "
                "instead of spell slots. No verbal/somatic components when casting this way.",
                feature_type="class", mechanic="psionic_sorcery"),
    ],
    14: [
        Feature("Revelation in Flesh", "Bonus action, spend 1+ sorcery points: gain one benefit "
                "per point for 10 min. See Invisible 60ft, fly speed = walk, swim+breathe, "
                "squeeze through 1-inch spaces.",
                feature_type="class", mechanic="revelation_in_flesh"),
    ],
    18: [
        Feature("Warping Implosion", "Action: teleport 120ft. Each creature within 30ft of vacated space "
                "makes STR save or 3d10 force damage + pulled to space. Half on save. 1/long rest "
                "or 5 sorcery points.",
                feature_type="class", mechanic="warping_implosion",
                save_ability="Strength", damage_dice="3d10", damage_type="force"),
    ],
}

SORCERER_CLOCKWORK_SOUL = {
    1: [
        Feature("Clockwork Magic", "Learn extra spells: Alarm, Protection from Evil and Good. "
                "At higher levels: Aid, Lesser Restoration, Dispel Magic, Protection from Energy, "
                "Freedom of Movement, Summon Construct, Greater Restoration, Wall of Force.",
                feature_type="class", mechanic="clockwork_magic"),
        Feature("Restore Balance", "Reaction: when a creature within 60ft rolls with adv/disadv, "
                "cancel the adv/disadv. Prof bonus uses/long rest.",
                feature_type="class", mechanic="restore_balance"),
    ],
    6: [
        Feature("Bastion of Law", "Action: spend 1-5 sorcery points. Target creature gains "
                "that many d8 as ward dice. When creature takes damage, spend any number of "
                "ward dice to reduce damage by total rolled.",
                feature_type="class", mechanic="bastion_of_law"),
    ],
    14: [
        Feature("Trance of Order", "Bonus action: 1 minute. Attack rolls, checks, saves can't "
                "roll below 10 on d20. 1/long rest or 7 sorcery points.",
                feature_type="class", mechanic="trance_of_order"),
    ],
    18: [
        Feature("Clockwork Cavalcade", "Action: 30ft cube. Restore up to 100 HP (divided), "
                "repair damaged objects, end 6th level or lower spells. 1/long rest or 7 SP.",
                feature_type="class", mechanic="clockwork_cavalcade"),
    ],
}

# --- BARD (TCoE) ---
BARD_CREATION = {
    3: [
        Feature("Mote of Potential", "When you grant Bardic Inspiration, mote orbits target. "
                "On ability check: roll twice, use higher. On attack: 2d6 thunder to target+adjacent. "
                "On save: gain die roll as temp HP.",
                feature_type="class", mechanic="mote_of_potential"),
        Feature("Performance of Creation", "Action: create nonmagical item within 10ft worth "
                "up to 20xBard level GP. Size up to Medium (Large at 6, Huge at 14). "
                "Lasts prof bonus hours. 1/long rest or 2nd-level slot.",
                feature_type="class", mechanic="performance_of_creation"),
    ],
    6: [
        Feature("Animating Performance", "Action: animate Large or smaller nonmagical item as creature "
                "for 1 hour. Dancing Item has AC 16, HP 10+5xBard level, +8 attack, 1d10+prof force. "
                "1/long rest or 3rd-level slot.",
                feature_type="class", mechanic="animating_performance"),
    ],
    14: [
        Feature("Creative Crescendo", "Performance of Creation: create prof bonus items simultaneously. "
                "One item can be up to one size larger than normal.",
                feature_type="class", mechanic="creative_crescendo"),
    ],
}

BARD_ELOQUENCE = {
    3: [
        Feature("Silver Tongue", "Treat Persuasion/Deception rolls of 9 or lower as 10.",
                feature_type="class", mechanic="silver_tongue"),
        Feature("Unsettling Words", "Bonus action: spend Bardic Inspiration. Target within 60ft "
                "subtracts die from next save before start of your next turn.",
                feature_type="class", mechanic="unsettling_words"),
    ],
    6: [
        Feature("Unfailing Inspiration", "When creature uses your Bardic Inspiration and fails, "
                "they keep the die instead of losing it.",
                feature_type="class", mechanic="unfailing_inspiration"),
        Feature("Universal Speech", "Action: choose prof bonus creatures within 60ft. "
                "They understand you for 1 hour regardless of language. 1/long rest or spell slot.",
                feature_type="class", mechanic="universal_speech"),
    ],
    14: [
        Feature("Infectious Inspiration", "Reaction: when creature uses your Bardic Inspiration "
                "and succeeds, give Bardic Inspiration to another creature within 60ft (no use cost). "
                "CHA mod times/long rest.",
                feature_type="class", mechanic="infectious_inspiration"),
    ],
}

# --- DRUID (TCoE) ---
DRUID_STARS = {
    2: [
        Feature("Star Map", "Free cast of Guiding Bolt, prof bonus times/long rest. "
                "Learn Guidance cantrip.",
                feature_type="class", mechanic="star_map"),
        Feature("Starry Form", "Bonus action when you Wild Shape: enter starry form instead. "
                "Choose constellation: Archer (ranged 60ft, 1d8+WIS radiant as bonus action), "
                "Chalice (heal 1d8+WIS to creature within 30ft when you cast heal spell), "
                "Dragon (minimum 10 on concentration saves, fly speed 20ft hover).",
                feature_type="class", mechanic="starry_form"),
    ],
    6: [
        Feature("Cosmic Omen", "After long rest, roll d6. Woe (even) or Weal (odd). "
                "Reaction: creature within 30ft making attack/save/check subtracts (woe) or "
                "adds (weal) 1d6. Prof bonus uses/long rest.",
                feature_type="class", mechanic="cosmic_omen"),
    ],
    10: [
        Feature("Twinkling Constellations", "Change starry form constellation at start of each turn. "
                "Archer/Chalice dice become 2d8.",
                feature_type="class", mechanic="twinkling_constellations"),
    ],
    14: [
        Feature("Full of Stars", "While in starry form, resistance to bludgeoning/piercing/slashing.",
                feature_type="class", mechanic="full_of_stars"),
    ],
}

DRUID_WILDFIRE = {
    2: [
        Feature("Summon Wildfire Spirit", "Expend Wild Shape use to summon Wildfire Spirit within 30ft. "
                "HP = 5 + 5x druid level. On summon, each creature within 10ft makes DEX save: "
                "2d6 fire damage (half on save). Commands: bonus action dodge/Flame Seed (60ft, "
                "1d6+prof fire) /Fiery Teleportation (teleport self+allies 15ft, 1d6+prof fire AoE).",
                feature_type="class", mechanic="wildfire_spirit",
                damage_dice="2d6", damage_type="fire"),
    ],
    6: [
        Feature("Enhanced Bond", "When you cast a damage/healing spell through wildfire spirit's space, "
                "+1d8 to one roll. Can cast through spirit's space (spells originate from it).",
                feature_type="class", mechanic="enhanced_bond"),
    ],
    10: [
        Feature("Cauterizing Flames", "Reaction: when Small+ creature dies within 30ft of you or spirit, "
                "spectral flame heals or damages creature within 30ft of dying creature: "
                "2d10+WIS mod. Prof bonus uses/long rest.",
                feature_type="class", mechanic="cauterizing_flames",
                damage_dice="2d10"),
    ],
    14: [
        Feature("Blazing Revival", "If wildfire spirit drops to 0 HP while you're within 120ft and "
                "you have 0 HP, regain half HP and rise (end Prone). Spirit then dies. 1/long rest.",
                feature_type="class", mechanic="blazing_revival"),
    ],
}

# --- MONK (TCoE) ---
MONK_ASTRAL_SELF = {
    3: [
        Feature("Arms of the Astral Self", "Bonus action, 1 ki: summon spectral arms for 10 min. "
                "Reach 10ft, +WIS to attacks/damage (force), +5 reach unarmed attacks. "
                "On summon: each creature in 10ft makes DEX save or 2xMartial Arts die force.",
                feature_type="class", mechanic="arms_of_astral_self"),
    ],
    6: [
        Feature("Visage of the Astral Self", "Bonus action, 1 ki: astral visage for 10 min. "
                "Astral Sight (darkvision 120ft, see into Ethereal 60ft), "
                "Wisdom of the Spirit (advantage on Insight/Intimidation), "
                "Word of the Spirit (voice audible to 600ft).",
                feature_type="class", mechanic="visage_of_astral_self"),
    ],
    11: [
        Feature("Body of the Astral Self", "When you have both arms and visage active, spectral body "
                "surrounds you. Reaction: reduce acid/cold/fire/force/lightning damage by 1d10+WIS. "
                "Extra +1d10 arms damage once per turn.",
                feature_type="class", mechanic="body_of_astral_self"),
    ],
    17: [
        Feature("Awakened Astral Self", "Spend 5 ki (instead of separate costs) for full astral self. "
                "+2 to AC while active. Third arms attack on Attack action.",
                feature_type="class", mechanic="awakened_astral_self"),
    ],
}

MONK_MERCY = {
    3: [
        Feature("Implements of Mercy", "Proficiency in Insight and Medicine, plus herbalism kit.",
                feature_type="class", mechanic="implements_of_mercy"),
        Feature("Hand of Healing", "Action or replace Flurry of Blows attack: spend 1 ki, "
                "heal 1d6+WIS (increases: 1d8 at 5th, 1d10 at 11th, 1d12 at 17th). "
                "Also removes Blinded/Deafened/Paralyzed/Poisoned/Stunned at 6th+.",
                feature_type="class", mechanic="hand_of_healing"),
        Feature("Hand of Harm", "Once per turn when you hit with unarmed strike: spend 1 ki, "
                "deal extra 1d6+WIS necrotic (increases with Martial Arts die). "
                "Target must succeed CON save or Poisoned until end of your next turn.",
                feature_type="class", mechanic="hand_of_harm",
                damage_type="necrotic", save_ability="Constitution",
                applies_condition="Poisoned"),
    ],
    6: [
        Feature("Physician's Touch", "Hand of Healing also ends one: Blinded, Deafened, "
                "Paralyzed, Poisoned, or Stunned condition on target. "
                "Hand of Harm Poisoned condition doesn't require ki.",
                feature_type="class", mechanic="physicians_touch"),
    ],
    11: [
        Feature("Flurry of Healing and Harm", "Replace each Flurry of Blows attack with "
                "Hand of Healing (no extra ki). On Flurry: can use Hand of Harm on each "
                "hit without spending ki (once per turn for free).",
                feature_type="class", mechanic="flurry_healing_harm"),
    ],
    17: [
        Feature("Hand of Ultimate Mercy", "Action: touch dead creature (died within 24h), "
                "spend 5 ki. Creature returns with 4d10+WIS HP, cured of conditions. "
                "1/long rest.",
                feature_type="class", mechanic="hand_of_ultimate_mercy"),
    ],
}

# ============================================================
# END OF TASHA'S CAULDRON SUBCLASSES
# ============================================================

# ============================================================
# END OF ADDITIONAL SUBCLASSES
# ============================================================

BARBARIAN_RAGE_COUNT = {
    1: 2, 2: 2, 3: 3, 4: 3, 5: 3, 6: 4, 7: 4, 8: 4, 9: 4, 10: 4,
    11: 4, 12: 5, 13: 5, 14: 5, 15: 5, 16: 5, 17: 6, 18: 6, 19: 6, 20: -1  # unlimited
}

# Ki points = monk level
# Sorcery points = sorcerer level
# Lay on Hands pool = 5 * paladin level
# Bardic Inspiration uses = CHA mod (min 1)


def get_class_features(character_class: str, level: int, subclass: str = "") -> list[Feature]:
    """Get all class features for a given class/subclass up to the specified level."""
    features = []

    # Map class names to feature dicts
    class_map = {
        "Barbarian": BARBARIAN_FEATURES,
        "Fighter": FIGHTER_FEATURES,
        "Paladin": PALADIN_FEATURES,
        "Rogue": ROGUE_FEATURES,
        "Ranger": RANGER_FEATURES,
        "Cleric": CLERIC_FEATURES,
        "Wizard": WIZARD_FEATURES,
        "Warlock": WARLOCK_FEATURES,
        "Sorcerer": SORCERER_FEATURES,
        "Bard": BARD_FEATURES,
        "Druid": DRUID_FEATURES,
        "Monk": MONK_FEATURES,
    }

    subclass_map = {
        # Barbarian
        "Totem Warrior": BARBARIAN_TOTEM_BEAR,
        "Berserker": BARBARIAN_BERSERKER,
        "Ancestral Guardian": BARBARIAN_ANCESTRAL_GUARDIAN,
        "Storm Herald": BARBARIAN_STORM_HERALD,
        "Zealot": BARBARIAN_ZEALOT,
        # Fighter
        "Champion": FIGHTER_CHAMPION,
        "Battle Master": FIGHTER_BATTLE_MASTER,
        "Eldritch Knight": FIGHTER_ELDRITCH_KNIGHT,
        "Arcane Archer": FIGHTER_ARCANE_ARCHER,
        "Cavalier": FIGHTER_CAVALIER,
        "Samurai": FIGHTER_SAMURAI,
        # Paladin
        "Devotion": PALADIN_DEVOTION,
        "Vengeance": PALADIN_VENGEANCE,
        "Ancients": PALADIN_ANCIENTS,
        "Conquest": PALADIN_CONQUEST,
        "Redemption": PALADIN_REDEMPTION,
        "Crown": PALADIN_CROWN,
        # Rogue
        "Assassin": ROGUE_ASSASSIN,
        "Thief": ROGUE_THIEF,
        "Arcane Trickster": ROGUE_ARCANE_TRICKSTER,
        "Swashbuckler": ROGUE_SWASHBUCKLER,
        "Scout": ROGUE_SCOUT,
        "Inquisitive": ROGUE_INQUISITIVE,
        "Mastermind": ROGUE_MASTERMIND,
        # Ranger
        "Hunter": RANGER_HUNTER,
        "Beast Master": RANGER_BEAST_MASTER,
        "Gloom Stalker": RANGER_GLOOM_STALKER,
        "Horizon Walker": RANGER_HORIZON_WALKER,
        "Monster Slayer": RANGER_MONSTER_SLAYER,
        # Cleric
        "War": CLERIC_WAR,
        "Life": CLERIC_LIFE,
        "Light": CLERIC_LIGHT,
        "Knowledge": CLERIC_KNOWLEDGE,
        "Nature": CLERIC_NATURE,
        "Tempest": CLERIC_TEMPEST,
        "Trickery": CLERIC_TRICKERY,
        "Forge": CLERIC_FORGE,
        "Grave": CLERIC_GRAVE,
        # Wizard
        "Evocation": WIZARD_EVOCATION,
        "Abjuration": WIZARD_ABJURATION,
        "Divination": WIZARD_DIVINATION,
        "Conjuration": WIZARD_CONJURATION,
        "Enchantment": WIZARD_ENCHANTMENT,
        "Illusion": WIZARD_ILLUSION,
        "Necromancy": WIZARD_NECROMANCY,
        "Transmutation": WIZARD_TRANSMUTATION,
        "War Magic": WIZARD_WAR_MAGIC,
        "Bladesinging": WIZARD_BLADESINGING,
        # Warlock
        "Fiend": WARLOCK_FIEND,
        "Great Old One": WARLOCK_GREAT_OLD_ONE,
        "Archfey": WARLOCK_ARCHFEY,
        "Hexblade": WARLOCK_HEXBLADE,
        "Celestial": WARLOCK_CELESTIAL,
        # Sorcerer
        "Draconic Bloodline": SORCERER_DRACONIC,
        "Wild Magic": SORCERER_WILD_MAGIC,
        "Divine Soul": SORCERER_DIVINE_SOUL,
        "Shadow Magic": SORCERER_SHADOW,
        "Storm Sorcery": SORCERER_STORM,
        # Bard
        "College of Lore": BARD_LORE,
        "College of Valor": BARD_VALOR,
        "College of Swords": BARD_SWORDS,
        "College of Whispers": BARD_WHISPERS,
        "College of Glamour": BARD_GLAMOUR,
        # Druid
        "Circle of the Moon": DRUID_MOON,
        "Circle of the Land": DRUID_LAND,
        "Circle of Dreams": DRUID_DREAMS,
        "Circle of the Shepherd": DRUID_SHEPHERD,
        "Circle of Spores": DRUID_SPORES,
        # Monk
        "Way of the Open Hand": MONK_OPEN_HAND,
        "Way of Shadow": MONK_SHADOW,
        "Way of the Four Elements": MONK_FOUR_ELEMENTS,
        "Way of the Drunken Master": MONK_DRUNKEN_MASTER,
        "Way of the Kensei": MONK_KENSEI,
        "Way of the Sun Soul": MONK_SUN_SOUL,
        "Way of the Long Death": MONK_LONG_DEATH,
        # Tasha's Cauldron of Everything (TCoE)
        # Barbarian
        "Path of the Beast": BARBARIAN_BEAST,
        "Path of Wild Magic": BARBARIAN_WILD_MAGIC_BARB,
        # Fighter
        "Psi Warrior": FIGHTER_PSI_WARRIOR,
        "Rune Knight": FIGHTER_RUNE_KNIGHT,
        # Paladin
        "Oath of Glory": PALADIN_GLORY,
        "Oath of the Watchers": PALADIN_WATCHERS,
        # Rogue
        "Phantom": ROGUE_PHANTOM,
        "Soulknife": ROGUE_SOULKNIFE,
        # Ranger
        "Fey Wanderer": RANGER_FEY_WANDERER,
        "Swarmkeeper": RANGER_SWARMKEEPER,
        # Cleric
        "Order": CLERIC_ORDER,
        "Peace": CLERIC_PEACE,
        "Twilight": CLERIC_TWILIGHT,
        # Wizard
        "Order of Scribes": WIZARD_ORDER_OF_SCRIBES,
        # Warlock
        "Fathomless": WARLOCK_FATHOMLESS,
        "Genie": WARLOCK_GENIE,
        # Sorcerer
        "Aberrant Mind": SORCERER_ABERRANT_MIND,
        "Clockwork Soul": SORCERER_CLOCKWORK_SOUL,
        # Bard
        "College of Creation": BARD_CREATION,
        "College of Eloquence": BARD_ELOQUENCE,
        # Druid
        "Circle of Stars": DRUID_STARS,
        "Circle of Wildfire": DRUID_WILDFIRE,
        # Monk
        "Way of the Astral Self": MONK_ASTRAL_SELF,
        "Way of Mercy": MONK_MERCY,
    }

    # Gather base class features
    base_feats = class_map.get(character_class, {})
    for feat_level, feat_list in sorted(base_feats.items()):
        if feat_level <= level:
            features.extend(feat_list)

    # Gather subclass features
    sub_feats = subclass_map.get(subclass, {})
    for feat_level, feat_list in sorted(sub_feats.items()):
        if feat_level <= level:
            features.extend(feat_list)

    # Deduplicate by mechanic (higher level versions replace lower)
    # For features like sneak_attack, rage_damage where value scales
    seen_mechanics = {}
    final = []
    for feat in reversed(features):  # Reverse so higher level wins
        if feat.mechanic and feat.mechanic in seen_mechanics:
            continue
        if feat.mechanic:
            seen_mechanics[feat.mechanic] = True
        final.append(feat)
    final.reverse()

    return final
