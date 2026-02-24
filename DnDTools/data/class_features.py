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
        # Fighter
        "Champion": FIGHTER_CHAMPION,
        "Battle Master": FIGHTER_BATTLE_MASTER,
        # Paladin
        "Devotion": PALADIN_DEVOTION,
        "Vengeance": PALADIN_VENGEANCE,
        # Rogue
        "Assassin": ROGUE_ASSASSIN,
        "Thief": ROGUE_THIEF,
        # Ranger
        "Hunter": RANGER_HUNTER,
        "Beast Master": RANGER_BEAST_MASTER,
        # Cleric
        "War": CLERIC_WAR,
        "Life": CLERIC_LIFE,
        "Light": CLERIC_LIGHT,
        # Wizard
        "Evocation": WIZARD_EVOCATION,
        "Abjuration": WIZARD_ABJURATION,
        "Divination": WIZARD_DIVINATION,
        # Warlock
        "Fiend": WARLOCK_FIEND,
        "Great Old One": WARLOCK_GREAT_OLD_ONE,
        # Sorcerer
        "Draconic Bloodline": SORCERER_DRACONIC,
        "Wild Magic": SORCERER_WILD_MAGIC,
        # Bard
        "College of Lore": BARD_LORE,
        "College of Valor": BARD_VALOR,
        # Druid
        "Circle of the Moon": DRUID_MOON,
        "Circle of the Land": DRUID_LAND,
        # Monk
        "Way of the Open Hand": MONK_OPEN_HAND,
        "Way of Shadow": MONK_SHADOW,
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
