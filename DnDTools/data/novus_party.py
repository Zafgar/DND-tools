"""Novus Somnium -kampanjan pelaajahahmot (taso 11).

Viisi pelaajahahmoa D&D Beyond -lomakkeista pelattaviksi työkalussa:
Magnus Dragonius, Balthazar, Venris Galanodel, Padak Onslaught ja Krusk.
Nämä liitetään ``hero_list``-listaan, joten ne näkyvät heroina
encounter setup -näkymässä ja voi asettaa kentälle pelaajien puolelle.

Loitsijat viittaavat loitsuihin nimellä (``spell_names`` /
``cantrip_names``) keskitetystä loitsukirjastosta — ei omia holdereita.
Luokkakyvyt käyttävät moottorin mekaniikka-avaimia (rage, extra_attack,
action_surge, second_wind jne.), jotta AI osaa käyttää niitä. Homebrew-
/reflavored-kyvyt (Slowing Beam, Drake's Breath, Genie's Wrath) on
mallinnettu Actioneina tai Feature-teksteinä pöytäpeliä varten.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature
from data.racial_traits import get_racial_traits


novus_party = [
    # ================================================================= #
    # MAGNUS DRAGONIUS — Air Genasi Ranger 11 (Drakewarden)
    # ================================================================= #
    CreatureStats(
        name="Magnus Dragonius",
        character_class="Ranger", character_level=11, race="Air Genasi",
        subclass="Drakewarden",
        hit_points=81, armor_class=17, speed=40,
        climb_speed=40, swim_speed=40, hit_dice="11d10",
        abilities=AbilityScores(strength=8, dexterity=16, constitution=12,
                                intelligence=12, wisdom=16, charisma=10),
        senses="Darkvision 60 ft.",
        languages="Common, Celestial, Draconic, Dwarvish, Elvish, Orc, "
                  "Undercommon",
        damage_resistances=["fire", "lightning", "cold"],
        spellcasting_ability="Wisdom", spell_save_dc=15, spell_attack_bonus=7,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3},
        spell_names=["Hunter's Mark", "Fog Cloud", "Silence", "Wind Wall",
                     "Absorb Elements", "Revivify"],
        cantrip_names=["Fire Bolt", "Shocking Grasp"],
        actions=[
            Action("Multiattack", "x2 (Extra Attack)", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Longbow", "Longbow"]),
            Action("Longbow", "Ranged (Archery)", 9, "1d8+3", 0, "piercing",
                   range=150, long_range=600,
                   properties=["heavy", "two-handed", "ammunition"]),
            Action("Scimitar", "Melee", 7, "1d6+3", 0, "slashing",
                   properties=["finesse", "light"]),
            Action("Shortsword", "Melee", 7, "1d6+3", 0, "piercing",
                   properties=["finesse", "light"]),
            Action("Drake's Breath", "30 ft Cone (DC 15 DEX, half on save)",
                   0, "8d6", 0, "cold", range=30, aoe_radius=30,
                   aoe_shape="cone", condition_save="Dexterity",
                   condition_dc=15),
        ],
        features=[
            Feature("Favored Foe", "On a hit, mark a target (concentration, "
                    "1 min); first hit each turn deals +1d6. 4/long rest.",
                    feature_type="class", uses_per_day=4,
                    mechanic="hunters_mark", mechanic_value="1d6"),
            Feature("Fighting Style: Archery", "+2 to ranged weapon attacks "
                    "(folded into Longbow).", feature_type="class",
                    mechanic="fighting_style"),
            Feature("Extra Attack", "2 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Drake Companion (Cold)", "Summon a bonded drake (AC 18, "
                    "Bite +7 1d6+4 + 1d6 cold; shares your initiative). "
                    "Command with a bonus action.", feature_type="class"),
            Feature("Nature's Veil", "Bonus Action: become invisible until "
                    "the start of your next turn. 4/long rest.",
                    feature_type="class", uses_per_day=4),
            Feature("Drake's Breath", "30 ft cone, 8d6 (DC 15 DEX half); "
                    "1/long rest (or a 3rd+ spell slot).", feature_type="class",
                    uses_per_day=1),
            Feature("Deft Explorer: Tireless", "Action: gain 1d8+3 temp HP. "
                    "4/long rest.", feature_type="class", uses_per_day=4),
            Feature("Land's Stride", "Nonmagical difficult terrain costs no "
                    "extra movement; advantage vs plant-based restraint.",
                    feature_type="class"),
        ],
        racial_traits=get_racial_traits("Air Genasi"),
        saving_throws={"Strength": 3, "Dexterity": 7},
        skills={"Perception": 11, "Survival": 7, "Athletics": 3,
                "Nature": 5, "Stealth": 7},
        challenge_rating=6.0, proficiency_bonus=4,
        alignment="Lawful Good",
        lore="Air Genasi -kääpiöklaanin kasvatti ja Drakewarden-tarkka-"
             "ampuja; kylmädraken sitoja, joka juoksi 25 mailia varoittaakseen "
             "klaaniaan örkkilaumasta.",
        tactics="Merkitsee kovimman uhan Favored Foella, ampuu Longbow'lla "
                "kahdesti; kutsuu draken tankiksi ja käyttää Drake's Breathin "
                "ryhmiin. Nature's Veil paetakseen tulilinjalta.",
    ),

    # ================================================================= #
    # BALTHAZAR — Levistus Tiefling Fighter 1 / Warlock 10 (The Genie/Dao)
    # ================================================================= #
    CreatureStats(
        name="Balthazar",
        character_class="Warlock", character_level=11, race="Levistus Tiefling",
        subclass="The Genie (Dao)",
        hit_points=93, armor_class=18, speed=30, hit_dice="1d10+10d8",
        abilities=AbilityScores(strength=8, dexterity=14, constitution=16,
                                intelligence=10, wisdom=10, charisma=19),
        senses="Darkvision 60 ft.",
        languages="Common, Celestial, Infernal",
        damage_resistances=["cold", "fire", "bludgeoning"],
        damage_immunities=["poison"],
        spellcasting_ability="Charisma", spell_save_dc=16, spell_attack_bonus=8,
        spell_slots={"5th": 2},   # Pact Magic: two 5th-level slots
        spell_names=["Hex", "Armor of Agathys", "Darkness", "Counterspell",
                     "Banishment", "Dimension Door", "Sickening Radiance"],
        cantrip_names=["Eldritch Blast", "Ray of Frost", "Mind Sliver",
                       "Mage Hand"],
        actions=[
            Action("Eldritch Blast", "Ranged (3 beams, Agonizing +CHA)", 8,
                   "1d10+4", 0, "force", range=120, is_multiattack=True,
                   multiattack_count=3,
                   multiattack_targets=["Eldritch Blast Beam",
                                        "Eldritch Blast Beam",
                                        "Eldritch Blast Beam"]),
            Action("Eldritch Blast Beam", "Ranged spell", 8, "1d10+4", 0,
                   "force", range=120),
            Action("Rapier", "Melee", 6, "1d8+2", 0, "piercing",
                   properties=["finesse"]),
        ],
        features=[
            Feature("Pact Magic", "CHA, DC 16, +8 to hit. Two 5th-level pact "
                    "slots (recover on a short rest).", feature_type="class"),
            Feature("Agonizing Blast", "Add CHA (+4) to each Eldritch Blast "
                    "beam (folded in).", feature_type="class"),
            Feature("Genie's Wrath (Dao)", "Once per turn on a hit, deal +4 "
                    "(proficiency) bludgeoning damage.", feature_type="class"),
            Feature("Genie's Vessel: Bottled Respite", "Action: vanish into "
                    "your vessel for up to 8 hours. 1/long rest.",
                    feature_type="class", uses_per_day=1),
            Feature("Elemental Gift: Flight", "Bonus Action: 30 ft flying "
                    "speed for 10 min. 4/long rest.", feature_type="class",
                    uses_per_day=4),
            Feature("Second Wind", "Bonus Action: regain 1d10+1 HP. "
                    "1/short rest.", feature_type="class", uses_per_day=1,
                    mechanic="second_wind", mechanic_value="1d10+1",
                    short_rest_recharge=True),
            Feature("Telekinetic: Shove", "Bonus Action: DC 16 STR save or "
                    "move a creature within 30 ft 5 ft.", feature_type="class"),
        ],
        racial_traits=get_racial_traits("Tiefling"),
        saving_throws={"Constitution": 7, "Charisma": 8},
        skills={"Arcana": 4, "Deception": 8, "Persuasion": 8,
                "Intimidation": 8},
        challenge_rating=6.0, proficiency_bonus=4,
        alignment="Chaotic Neutral",
        lore="Levistus-tiefling ja Dao-genien sopimusvelho; kylmän ja tulen "
             "kestävä loitsijasoturi, jonka Eldritch Blast repii kolmella "
             "säteellä.",
        tactics="Eldritch Blast (3 sädettä) pääaseena; Hex kovimpaan uhkaan, "
                "Counterspell/Banishment loitsijoihin, Armor of Agathys "
                "puolustukseksi. Elemental Gift -lento tulilinjan yli.",
    ),

    # ================================================================= #
    # VENRIS GALANODEL — High Elf Wizard 11 (Chronurgy)
    # ================================================================= #
    CreatureStats(
        name="Venris Galanodel",
        character_class="Wizard", character_level=11, race="High Elf",
        subclass="Chronurgy Magic",
        hit_points=68, armor_class=15, speed=30, hit_dice="11d6",
        abilities=AbilityScores(strength=10, dexterity=16, constitution=14,
                                intelligence=18, wisdom=12, charisma=8),
        senses="Darkvision 60 ft.",
        languages="Common, Draconic, Elvish, Orc, Sylvan",
        condition_immunities=["Magical Sleep"],
        spellcasting_ability="Intelligence", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2,
                     "6th": 1},
        spell_names=["Magic Missile", "Shield", "Mage Armor", "Absorb Elements",
                     "Web", "Misty Step", "Mirror Image", "Invisibility",
                     "Fireball", "Counterspell", "Slow", "Dispel Magic",
                     "Fly", "Haste", "Polymorph", "Sickening Radiance",
                     "Wall of Force", "Telekinesis", "Disintegrate"],
        cantrip_names=["Ray of Frost", "Toll the Dead", "Mage Hand",
                       "Message", "Minor Illusion"],
        actions=[
            Action("Slowing Beam", "Ranged spell (reflavored Ray of Frost; "
                   "speed -10 ft)", 8, "3d8", 0, "force", range=60),
            Action("Dagger +1", "Melee / Thrown", 8, "1d4+4", 0, "piercing",
                   range=20, long_range=60,
                   properties=["finesse", "light", "thrown"]),
            Action("Dagger", "Melee / Thrown", 7, "1d4+3", 0, "piercing",
                   range=20, long_range=60,
                   properties=["finesse", "light", "thrown"]),
        ],
        features=[
            Feature("Spellcasting", "INT, DC 16, +8 to hit. Slots 4/3/3/3/2/1. "
                    "Fireball, Counterspell, Haste, Slow, Polymorph, Wall of "
                    "Force, Telekinesis, Disintegrate.", feature_type="class"),
            Feature("Arcane Recovery", "Short rest: recover spell slots "
                    "(combined level up to 6).", feature_type="class"),
            Feature("Momentary Stasis", "Action: a Large or smaller creature "
                    "within 60 ft makes a DC 16 CON save or is incapacitated "
                    "(speed 0) until the end of your next turn. 4/long rest.",
                    feature_type="class", uses_per_day=4,
                    save_dc=16, save_ability="Constitution",
                    applies_condition="Incapacitated"),
            Feature("Chronal Shift", "Reaction: force a reroll of an attack, "
                    "check, or save (yours or within 30 ft). 2/long rest.",
                    feature_type="reaction", uses_per_day=2),
            Feature("Fey Ancestry", "Advantage vs Charmed; immune to magical "
                    "sleep.", mechanic="fey_ancestry"),
        ],
        racial_traits=get_racial_traits("High Elf"),
        saving_throws={"Intelligence": 8, "Wisdom": 5},
        skills={"Arcana": 8, "History": 8, "Investigation": 8, "Insight": 5},
        challenge_rating=6.0, proficiency_bonus=4,
        alignment="Neutral",
        lore="High Elf -oppinut ja Chronurgy-maagi Sage-taustalla; hallitsee "
             "aikaa Momentary Stasisilla ja Chronal Shiftillä.",
        tactics="Aloittaa Mage Armor/Shield-puolustuksella; Fireball ja "
                "Sickening Radiance ryhmiin, Slow/Momentary Stasis kovimpiin "
                "uhkiin, Counterspell vihollisloitsijoihin. Misty Step "
                "etäisyyden pitoon.",
    ),

    # ================================================================= #
    # PADAK ONSLAUGHT — Tabaxi Fighter 11 (Battle Master)
    # ================================================================= #
    CreatureStats(
        name="Padak Onslaught",
        character_class="Fighter", character_level=11, race="Tabaxi",
        subclass="Battle Master",
        hit_points=82, armor_class=15, speed=30, climb_speed=20,
        hit_dice="11d10",
        abilities=AbilityScores(strength=14, dexterity=19, constitution=14,
                                intelligence=8, wisdom=12, charisma=10),
        senses="Darkvision 60 ft.",
        languages="Common, Elvish",
        damage_resistances=["fire"],
        actions=[
            Action("Multiattack", "x3 (Extra Attack 2)", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Rapier +1", "Rapier +1", "Rapier +1"]),
            Action("Rapier +1", "Melee", 9, "1d8+5", 0, "piercing",
                   properties=["finesse"]),
            Action("Shortbow", "Ranged", 8, "1d6+4", 0, "piercing",
                   range=80, long_range=320,
                   properties=["ammunition", "two-handed"]),
            Action("Dagger", "Melee / Thrown", 8, "1d4+4", 0, "piercing",
                   range=20, long_range=60,
                   properties=["finesse", "light", "thrown"]),
            Action("Claws", "Melee (Tabaxi)", 6, "1d4+2", 0, "slashing"),
        ],
        features=[
            Feature("Action Surge", "Take one additional action. "
                    "1/short rest.", feature_type="class", uses_per_day=1,
                    mechanic="action_surge", short_rest_recharge=True),
            Feature("Second Wind", "Bonus Action: regain 1d10+11 HP. "
                    "1/short rest.", feature_type="class", uses_per_day=1,
                    mechanic="second_wind", mechanic_value="1d10+11",
                    short_rest_recharge=True),
            Feature("Extra Attack (2)", "3 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack_2"),
            Feature("Combat Superiority", "5d10 superiority dice; maneuvers "
                    "(Commander's Strike, Grappling Strike, Trip, Disarm) at "
                    "DC 16. Recover on a short rest.", feature_type="class"),
            Feature("Indomitable", "Reroll a failed save. 1/long rest.",
                    feature_type="class", uses_per_day=1,
                    mechanic="indomitable"),
            Feature("Feline Agility", "Double your speed until you don't move "
                    "on a turn.", feature_type="racial"),
            Feature("Shield Master", "Bonus Action shove; add shield AC to DEX "
                    "saves vs single-target effects.", feature_type="feat"),
        ],
        racial_traits=get_racial_traits("Tabaxi"),
        saving_throws={"Strength": 6, "Constitution": 6},
        skills={"Acrobatics": 8, "Stealth": 8, "Perception": 5,
                "Athletics": 6, "Survival": 5},
        challenge_rating=6.0, proficiency_bonus=4,
        alignment="Chaotic Neutral",
        lore="Tabaxi-palkkionmetsästäjä ja Battle Master -kaksintaistelija; "
             "nopea kynsi-isku ja rapieri-taktiikka Ravenstonen kaduilla.",
        tactics="Feline Agility lähelle, kolme Rapier +1 -iskua; maneuvereja "
                "(Trip/Disarm) hallintaan ja Commander's Strike liittolaisen "
                "reaktioon. Action Surge tappoiskun varmistamiseen.",
    ),

    # ================================================================= #
    # KRUSK — Half-Orc Barbarian 11
    # ================================================================= #
    CreatureStats(
        name="Krusk",
        character_class="Barbarian", character_level=11, race="Half-Orc",
        subclass="Path of the Berserker",
        hit_points=115, armor_class=15, speed=40, hit_dice="11d12",
        abilities=AbilityScores(strength=18, dexterity=14, constitution=16,
                                intelligence=10, wisdom=10, charisma=8),
        senses="Darkvision 60 ft.",
        languages="Common, Orc, Old tongue",
        actions=[
            Action("Multiattack", "x2 (Extra Attack)", 0, "", 0, "", range=5,
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Maul of the Titans",
                                        "Maul of the Titans"]),
            Action("Maul of the Titans", "Melee (Topple; +3 magic, rage "
                   "folded in)", 11, "2d6+7", 0, "bludgeoning",
                   properties=["heavy", "two-handed"]),
            Action("Unarmed Strike", "Melee", 8, "1d1+4", 0, "bludgeoning"),
        ],
        features=[
            Feature("Rage", "Bonus Action: +3 melee damage, resistance to "
                    "B/P/S, advantage on STR checks/saves. 4/long rest.",
                    feature_type="class", uses_per_day=4, mechanic="rage"),
            Feature("Rage Damage +3", "+3 melee damage while raging",
                    feature_type="class", mechanic="rage_damage",
                    mechanic_value="3"),
            Feature("Reckless Attack", "First attack: advantage on melee STR "
                    "attacks, but attacks against you have advantage.",
                    feature_type="class", mechanic="reckless_attack"),
            Feature("Danger Sense", "Advantage on DEX saves you can see",
                    feature_type="class", mechanic="danger_sense"),
            Feature("Extra Attack", "2 attacks per Attack action",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Fast Movement", "+10 ft speed",
                    feature_type="class", mechanic="fast_movement"),
            Feature("Feral Instinct", "Advantage on initiative",
                    feature_type="class", mechanic="feral_instinct"),
            Feature("Brutal Critical", "Roll 1 extra weapon die on a crit",
                    feature_type="class", mechanic="brutal_critical",
                    mechanic_value="1"),
            Feature("Relentless Rage", "Drop to 1 HP instead of 0 (DC 10+ "
                    "CON save) while raging.", feature_type="class"),
            Feature("Unarmored Defense", "AC = 10 + DEX + CON",
                    feature_type="class",
                    mechanic="unarmored_defense_barbarian"),
            Feature("Great Weapon Master", "Bonus Action attack on crit/kill; "
                    "-5 to hit for +10 damage option.", feature_type="feat"),
            Feature("Sentinel", "Opportunity attacks reduce speed to 0; "
                    "reaction hit when an ally is attacked nearby.",
                    feature_type="feat"),
            Feature("Relentless Endurance", "Drop to 1 HP instead of 0 once "
                    "per long rest.", feature_type="racial",
                    mechanic="relentless_endurance"),
        ],
        racial_traits=get_racial_traits("Half-Orc"),
        rage_count=4,
        saving_throws={"Strength": 8, "Constitution": 7},
        skills={"Athletics": 8, "Intimidation": 3, "Perception": 4,
                "Survival": 4},
        challenge_rating=6.0, proficiency_bonus=4,
        alignment="Chaotic Good",
        lore="Akarsho Eagle Wing -kylän half-orc-gladiaattori, jonka klaanin "
             "Red Drop tuhosi; raivon voimalla iskevä Maul of the Titans "
             "-jättiläismurskaaja.",
        tactics="Feral Instinct -aloite, Rage heti; Reckless Attack + kaksi "
                "Maul-iskua (Topple kaataa), Great Weapon Master bonus-isku "
                "tapoista. Sentinel lukitsee viholliset liittolaisten luo.",
    ),
]
