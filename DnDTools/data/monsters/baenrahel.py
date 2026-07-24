"""Talo Baenrahel — Aterterran drow-suvun sotilaat, vartijat ja pomot.

Pelattavat stat blockit kampanjan Verkkojen Talo / Aether-arkisto
-kohtaamisiin. Rider-vahingot (esim. myrkkyterät) on yhdistetty yhteen
noppalausekkeeseen, koska moottorin noppaparseri tukee vain ``XdY+Z``
-muotoa; erilliset ehdot (Poisoned, Prone) on toteutettu Actionin
``applies_condition``-kentillä. Legendaariset toiminnot ja
Magic Resistance / Legendary Resistance käyttävät moottorin natiiveja
kenttiä (``action_type="legendary"``, ``legendary_resistance_count``,
Feature ``mechanic="magic_resistance"``).

Reaktiot ja "Aether Ward" -tilapäis-HP on kuvattu Feature-teksteinä
pelinjohtajaa varten; ydinmekaniikka (multiattack, vahinko, saving
throwt, ehdot, loitsut) toimii moottorissa suoraan.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature, SpellInfo


monsters = [
    # ================================================================= #
    # CR 2 — Velve Dro -jousivartija (rank-and-file soldier)
    # ================================================================= #
    CreatureStats(
        name="Velve Dro Crossbow Sentry", size="Medium",
        creature_type="Humanoid", native_plane="Underdark",
        alignment="Lawful Evil", armor_class=15, hit_points=33,
        hit_dice="6d8+6", speed=30,
        abilities=AbilityScores(strength=11, dexterity=16, constitution=12,
                                intelligence=11, wisdom=13, charisma=10),
        saving_throws={"Dexterity": 5},
        skills={"Perception": 3, "Stealth": 5},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        actions=[
            Action("Multiattack", "x2 Hand Crossbow", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Poisoned Bolt", "Poisoned Bolt"]),
            Action("Poisoned Bolt", "Ranged", 5, "1d6+5", 0, "piercing",
                   range=30, applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=13),
            Action("Short Sword", "Melee", 5, "1d6", 3, "piercing"),
        ],
        features=[
            Feature("Fey Ancestry", "Advantage vs Charmed; magic can't put "
                    "it to sleep", mechanic="fey_ancestry"),
            Feature("Drow Poison", "Bolts coated in drow venom (DC 13 CON "
                    "or Poisoned 1 min)."),
        ],
        lore="Talo Baenrahelin Velve Dro -tarkka-ampuja. Vartioi käytäviä "
             "ja ampuu myrkkynuolia varjoista.",
        tactics="Pysyy etäällä ja korkealla, keskittää tulen loitsijoihin; "
                "vetäytyy jos joutuu lähitaisteluun.",
        habitat="Underdark", challenge_rating=2.0, xp=450,
        proficiency_bonus=2),

    # ================================================================= #
    # CR 3 — Velve Dro -soturi (rank-and-file soldier)
    # ================================================================= #
    CreatureStats(
        name="Velve Dro Warrior", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=16,
        hit_points=45, hit_dice="7d8+14", speed=30,
        abilities=AbilityScores(strength=14, dexterity=16, constitution=14,
                                intelligence=10, wisdom=12, charisma=11),
        saving_throws={"Dexterity": 5, "Constitution": 4},
        skills={"Athletics": 4, "Perception": 3, "Stealth": 5},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        actions=[
            Action("Multiattack", "x2 Scimitar", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Venom Scimitar", "Venom Scimitar"]),
            Action("Venom Scimitar", "Melee", 5, "1d6+6", 0, "slashing",
                   applies_condition="Poisoned", condition_save="Constitution",
                   condition_dc=13),
            Action("Hand Crossbow", "Ranged", 5, "1d6", 3, "piercing",
                   range=30),
        ],
        features=[
            Feature("Fey Ancestry", "Advantage vs Charmed; magic can't put "
                    "it to sleep", mechanic="fey_ancestry"),
            Feature("Drow Poison", "Blades coated in drow venom (folded into "
                    "damage; DC 13 CON or Poisoned 1 min)."),
            Feature("Squad Tactics", "Advantage on attacks vs a creature "
                    "already engaged by an allied soldier."),
        ],
        lore="Talo Baenrahelin Velve Dro -jalkaväen soturi; kurinalainen "
             "myrkkyterän käyttäjä.",
        tactics="Taistelee pareittain; pyrkii ympäröimään ja pitämään "
                "kohteet Poisoned-tilassa.",
        habitat="Underdark", challenge_rating=3.0, xp=700,
        proficiency_bonus=2),

    # ================================================================= #
    # CR 7 — Baenrahel Aether-Kaartilainen (elite anti-mage guard)
    # ================================================================= #
    CreatureStats(
        name="Baenrahel Aether Vanguard", size="Medium",
        creature_type="Humanoid", native_plane="Underdark",
        alignment="Lawful Evil", armor_class=18, hit_points=112,
        hit_dice="15d8+45", speed=30,
        abilities=AbilityScores(strength=18, dexterity=14, constitution=16,
                                intelligence=11, wisdom=14, charisma=12),
        saving_throws={"Strength": 7, "Constitution": 6, "Wisdom": 5},
        skills={"Athletics": 7, "Perception": 5, "Stealth": 7},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        actions=[
            Action("Multiattack", "x3 Aether Sword", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Aether Sword", "Aether Sword",
                                        "Aether Sword"]),
            Action("Aether Sword", "Melee (poisoned longsword)", 7, "1d8+11",
                   0, "slashing"),
            Action("Shield Bash", "Bonus (DC 15 STR or Prone)", 7, "1d4", 4,
                   "bludgeoning", action_type="bonus",
                   applies_condition="Prone", condition_save="Strength",
                   condition_dc=15),
        ],
        features=[
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Mage Slayer", "Advantage on melee attacks vs a "
                    "concentrating caster; a caster damaged by this guard has "
                    "disadvantage on the concentration save",
                    mechanic="mage_slayer"),
            Feature("Aether Ward", "Starts combat with 20 temporary hit "
                    "points from the house's protective magic.",
                    feature_type="reaction"),
            Feature("Spell Disruption", "Reaction: when a creature within 5 "
                    "ft casts a spell, make one Aether Sword attack against "
                    "it.", feature_type="reaction"),
            Feature("Parry", "Reaction: +3 AC against one melee attack it "
                    "can see.", feature_type="reaction"),
            Feature("Fey Ancestry", "Advantage vs Charmed",
                    mechanic="fey_ancestry"),
        ],
        lore="Raskaasti panssaroitu, äärimmäisen kurinalainen drow-soturi, "
             "koulutettu tuhoamaan vihollismaageja. Imee itseensä taikuutta "
             "ja hyödyntää Baenrahelin suojelumagiaa.",
        tactics="Ryntää suoraan pelaajien loitsijoiden kimppuun, katkoo "
                "keskittymistä ja käyttää Spell Disruption -reaktiota.",
        loot_table="Drow-taottu rintapanssari, myrkytetty pitkämiekka.",
        habitat="Underdark", challenge_rating=7.0, xp=2900,
        proficiency_bonus=3),

    # ================================================================= #
    # CR 8 — Baenrahel Verimaagi (elite support mage)
    # ================================================================= #
    CreatureStats(
        name="Baenrahel Blood-Weaver", size="Medium",
        creature_type="Humanoid", native_plane="Underdark",
        alignment="Lawful Evil", armor_class=15, hit_points=85,
        hit_dice="13d8+26", speed=30,
        abilities=AbilityScores(strength=9, dexterity=14, constitution=14,
                                intelligence=20, wisdom=16, charisma=14),
        saving_throws={"Intelligence": 8, "Wisdom": 6, "Charisma": 5},
        skills={"Arcana": 8, "History": 8, "Insight": 6},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        spellcasting_ability="Intelligence", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
        spell_names=[
            "Mage Armor", "Hold Person", "Counterspell", "Dispel Magic",
            "Silence", "Slow", "Banishment", "Wall of Force",
        ],
        actions=[
            Action("Multiattack", "x2 Searing Blood", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Searing Blood", "Searing Blood"]),
            Action("Searing Blood", "Ranged spell (speed -10 ft)", 8, "3d10",
                   0, "necrotic", range=60),
        ],
        features=[
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Blood Price", "Once per turn may sacrifice 10 HP to give "
                    "a spell's targets disadvantage on the save.",
                    feature_type="passive"),
            Feature("Baenrahel Abjuration", "Auto-succeeds on abjurations "
                    "vs spells of 3rd level or lower; +4 vs higher-level "
                    "spells."),
            Feature("Shield", "Reaction: +5 AC for one round (AC 20).",
                    feature_type="reaction"),
            Feature("Blood Tether", "Reaction: when an allied Aether Vanguard "
                    "within 30 ft takes damage, halve it by taking the same "
                    "amount as unpreventable necrotic damage.",
                    feature_type="reaction"),
            Feature("Fey Ancestry", "Advantage vs Charmed",
                    mechanic="fey_ancestry"),
            Feature("Spellcasting", "INT, DC 16, +8 to hit. Prepared: Mage "
                    "Armor, Hold Person, Counterspell, Dispel Magic, "
                    "Silence, Slow, Banishment, Wall of Force."),
        ],
        lore="Lordi Altheonin oppilas, joka manipuloi vihollisten "
             "elinvoimaa, vaimentaa loitsuja ja suojaa Aether-kaartilaisia "
             "verirituaalein.",
        tactics="Pysyy kaartilaisten takana; Counterspell/Dispel valmiina, "
                "Hold Person + Banishment kovimpiin uhkiin, Blood Tether "
                "pitää vartijat pystyssä.",
        habitat="Underdark", challenge_rating=8.0, xp=3900,
        proficiency_bonus=3),

    # ================================================================= #
    # CR 14 — Elarae Baenrahel (boss: Aether Archmage, legendary)
    # ================================================================= #
    CreatureStats(
        name="Elarae Baenrahel", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=19,
        armor_type="Mage Armor (24 with Shield)", hit_points=175,
        hit_dice="22d8+76", speed=30, fly_speed=10,
        abilities=AbilityScores(strength=10, dexterity=16, constitution=16,
                                intelligence=22, wisdom=16, charisma=16),
        saving_throws={"Constitution": 8, "Intelligence": 11, "Wisdom": 8,
                       "Charisma": 8},
        skills={"Arcana": 11, "Deception": 8, "Investigation": 11,
                "Perception": 8},
        senses="Darkvision 120 ft., Truesight 30 ft.",
        languages="Elvish, Undercommon, Draconic",
        damage_resistances=["force"],
        spellcasting_ability="Intelligence", spell_save_dc=19,
        spell_attack_bonus=11,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 2, "7th": 2},
        spell_names=[
            "Shield", "Misty Step", "Counterspell", "Dispel Magic",
            "Banishment", "Greater Invisibility", "Synaptic Static",
            "Wall of Force", "Chain Lightning",
        ],
        cantrip_names=["Fire Bolt", "Ray of Frost", "Mage Hand"],
        actions=[
            Action("Multiattack", "x3 Aether Siphon", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Aether Siphon", "Aether Siphon",
                                        "Aether Siphon"]),
            Action("Aether Siphon", "Ranged spell (drains a spell slot on a "
                   "caster; DC 19 CHA)", 11, "4d8+4", 0, "force", range=120),
        ],
        features=[
            Feature("Legendary Resistance", "3/day: choose to succeed on a "
                    "failed save", feature_type="passive", uses_per_day=3),
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Aether Ward", "Starts combat with 45 temporary hit "
                    "points; while she has them she can't lose "
                    "concentration from taking damage."),
            Feature("Jealous Spite", "If she hits a creature that harmed her "
                    "brother Dravin on its last turn, the hit deals +18 "
                    "(4d8) psychic damage."),
            Feature("Aether Rebuke", "Reaction (on Shield/Counterspell): one "
                    "creature within 30 ft makes a DC 19 DEX save or takes "
                    "21 (6d6) force (half on success).",
                    feature_type="reaction"),
            Feature("Misty Step (Teleport)", "Legendary Action (1): teleport "
                    "up to 30 ft.", feature_type="legendary",
                    legendary_cost=1),
            Feature("Sparking Strike", "Legendary Action (1): one Aether "
                    "Siphon attack.", feature_type="legendary",
                    legendary_cost=1),
            Feature("Aether Burst", "Legendary Action (2): creatures within "
                    "10 ft make a DC 19 CON save or are pushed 20 ft and "
                    "knocked Prone.", feature_type="legendary",
                    legendary_cost=2),
            Feature("Spellcasting", "INT, DC 19, +11 to hit; no material "
                    "components. Cantrips: Fire Bolt, Ray of Frost, Mage "
                    "Hand. Notables: Shield, Counterspell, Misty Step, "
                    "Banishment, Greater Invisibility, Synaptic Static, "
                    "Chain Lightning, Forcecage, Crown of Stars."),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Talo Baenrahelin perijä ja täyden tason Aether-arkkimaagi. "
             "Beatricen siskopuoli; hänen loitsunsa repivät todellisuutta ja "
             "imevät vihollisten magian kuiviin.",
        tactics="Leijuu ulottumattomissa, lukitsee uhkia Forcecageen, syö "
                "pelaajien loitsupaikkoja Aether Siphonilla ja rankaisee "
                "loitsijoita Counterspell + Aether Rebuke -yhdistelmällä. "
                "Taistelee saumattomasti veljensä Dravinin kanssa.",
        loot_table="Aether-fokus, arkkimaagin komponenttilaukku, "
                   "Baenrahel-sinetti.",
        habitat="Underdark", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),

    # ================================================================= #
    # CR 14 — Dravin Baenrahel (boss: Velve Dro commander, legendary)
    # ================================================================= #
    CreatureStats(
        name="Dravin Baenrahel", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=20,
        armor_type="Drow adamantine plate (no extra crit damage)",
        hit_points=195, hit_dice="26d8+78", speed=40,
        abilities=AbilityScores(strength=20, dexterity=20, constitution=16,
                                intelligence=12, wisdom=14, charisma=13),
        saving_throws={"Strength": 10, "Dexterity": 10, "Constitution": 8,
                       "Wisdom": 7},
        skills={"Athletics": 10, "Acrobatics": 10, "Insight": 7,
                "Perception": 7, "Stealth": 10},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        damage_resistances=["poison"],
        actions=[
            Action("Multiattack", "x4 Velve Dro Scimitar", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=4,
                   multiattack_targets=["Velve Dro Scimitar",
                                        "Velve Dro Scimitar",
                                        "Velve Dro Scimitar",
                                        "Velve Dro Scimitar"]),
            Action("Velve Dro Scimitar", "Melee (DC 17 CON or Poisoned)", 10,
                   "5d6+10", 0, "slashing", applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=17),
        ],
        features=[
            Feature("Legendary Resistance", "3/day (Mage-Slayer's Resolve): "
                    "choose to succeed on a failed save vs a spell",
                    feature_type="passive", uses_per_day=3),
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Adamantine Plate", "Immune to extra damage from "
                    "critical hits; resistant to nonmagical B/P/S (DM "
                    "discretion vs magic weapons)."),
            Feature("Aether Devourer", "After it disrupts a spell (Spell-"
                    "Shatter), its next melee hit deals +14 (4d6) force "
                    "damage."),
            Feature("Spell-Shatter", "Reaction: when a creature within 10 ft "
                    "casts a spell, make one scimitar attack; on a hit the "
                    "caster makes a DC 18 CON save or the spell fails and the "
                    "slot is wasted.", feature_type="reaction"),
            Feature("Strike", "Legendary Action (1): one scimitar attack.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Commander's March", "Legendary Action (1): Dravin and "
                    "one ally move 20 ft without provoking opportunity "
                    "attacks.", feature_type="legendary", legendary_cost=1),
            Feature("Pressure", "Legendary Action (2): one creature within "
                    "30 ft makes a DC 17 WIS save or is Frightened of Dravin "
                    "until the end of its next turn.", feature_type="legendary",
                    legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Talo Baenrahelin sotilaallinen nyrkki ja Velve Dro -komentaja. "
             "Beatricen velipuoli; eliittisoturi joka imee taikuutta "
             "lyödäkseen kovempaa, pukeutunut adamanttihaarniskaan.",
        tactics="Ryntää loitsijoiden kimppuun (40 ft speed), katkoo loitsut "
                "Spell-Shatterilla ja iskee Aether Devourer -bonuksella; "
                "suojaa siskoaan Elaraeta ja pitää melee-hahmot Frightened- "
                "ja Poisoned-tiloissa.",
        loot_table="Drow-adamantti levypanssari, kaksi Velve Dro "
                   "-myrkkyscimitaria.",
        habitat="Underdark", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),
]
