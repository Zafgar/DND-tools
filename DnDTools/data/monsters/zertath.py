"""Zer'tath Lanke — Aterterran drow-pääkaupungin boss-statblockit.

Ylin Valta -hahmot ja yksi slummin gladiaattori. Legendaariset toiminnot,
Legendary Resistance ja Magic Resistance käyttävät moottorin natiiveja
kenttiä; erikoismekaniikat (sielukruunu, mielenhallinta, Action Surge)
on kuvattu Feature-teksteinä pelinjohtajalle.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


monsters = [
    # ================================================================= #
    # CR 20 — Matriarkka Cazna Icharyd (mythic arch-tyranni)
    # ================================================================= #
    CreatureStats(
        name="Cazna Icharyd", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Chaotic Evil", armor_class=18,
        armor_type="Mage Armor (21) / Shield (26)", hit_points=300,
        hit_dice="34d8+136", speed=30, fly_speed=20,
        abilities=AbilityScores(strength=8, dexterity=16, constitution=18,
                                intelligence=22, wisdom=20, charisma=20),
        saving_throws={"Constitution": 11, "Intelligence": 13,
                       "Wisdom": 12, "Charisma": 12},
        skills={"Arcana": 13, "History": 13, "Insight": 12,
                "Perception": 12},
        senses="Darkvision 120 ft., Truesight 30 ft.",
        languages="Elvish, Undercommon, Deep Speech, Abyssal",
        damage_resistances=["force", "necrotic"],
        spellcasting_ability="Intelligence", spell_save_dc=21,
        spell_attack_bonus=13,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 2, "7th": 2, "8th": 1, "9th": 1},
        spell_names=[
            "Shield", "Misty Step", "Counterspell", "Dispel Magic",
            "Fireball", "Lightning Bolt", "Banishment",
            "Greater Invisibility", "Cone of Cold", "Wall of Force",
            "Synaptic Static", "Chain Lightning", "Hold Monster",
            "Telekinesis", "Power Word Stun", "Finger of Death",
        ],
        cantrip_names=["Fire Bolt", "Ray of Frost", "Mage Hand"],
        actions=[
            Action("Multiattack", "x2 Soul Lash", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Soul Lash", "Soul Lash"]),
            Action("Soul Lash", "Ranged spell", 13, "4d10", 0, "necrotic",
                   range=120),
        ],
        features=[
            Feature("Legendary Resistance", "5/day: choose to succeed on a "
                    "failed save", feature_type="passive", uses_per_day=5),
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Soul-Crown of Tarquvas", "Whenever a creature dies "
                    "within 60 ft, Cazna regains one expended spell slot "
                    "(max 5th) and 15 temp HP. Carries the imprisoned soul "
                    "of Emperor Tarquvas."),
            Feature("Crown Strain", "The screaming crown costs her: at the "
                    "start of each of her turns she takes 10 psychic damage "
                    "(ignored while she has temp HP)."),
            Feature("Lair Actions", "In the Crystal-Lake palace (init 20): "
                    "raise a faerzress wall; force a creature to make a DC "
                    "21 WIS save or be frightened; drain 3d6 necrotic from "
                    "one creature and heal herself."),
            Feature("Cantrip", "Legendary Action (1): cast a cantrip.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Shadow Step", "Legendary Action (1): teleport up to "
                    "60 ft (Misty Step).", feature_type="legendary",
                    legendary_cost=1),
            Feature("Soul Drain", "Legendary Action (2): creatures within "
                    "20 ft make a DC 21 CON save or take 6d8 necrotic (half "
                    "on success); Cazna heals for half the total.",
                    feature_type="legendary", legendary_cost=2),
            Feature("Spellcasting", "INT, DC 21, +13 to hit; full 9th-level "
                    "caster (Wizard 18 / Cleric 4). Notables: Time Stop, "
                    "Power Word Kill, Finger of Death, Chain Lightning, "
                    "Wall of Force, Banishment, Counterspell."),
        ],
        legendary_action_count=3, legendary_resistance_count=5,
        lore="Aterterran ikuinen (3500+) matriarkka, joka kantaa keisari "
             "Tarquvasin sielukruunua ja ruokkii Vanqurionin sielukonetta. "
             "Kärsii kosmisesta PTSD:stä — kuulee kahlitun titaanin huudon.",
        tactics="Taistelee palatsissaan Lair Actioneilla; Wall of Force + "
                "Banishment eristää, Chain Lightning/Cone of Cold nitistää, "
                "Soul-Crown palauttaa slotteja jokaisesta kuolemasta.",
        habitat="Underdark", challenge_rating=20.0, xp=25000,
        proficiency_bonus=6),

    # ================================================================= #
    # CR 14 — Sotapäällikkö Dantrag Dyrr (kaksoismiekka-komentaja)
    # ================================================================= #
    CreatureStats(
        name="Dantrag Dyrr", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=20,
        armor_type="Adamantine plate (no extra crit damage)",
        hit_points=230, hit_dice="20d10+120", speed=40,
        abilities=AbilityScores(strength=20, dexterity=18, constitution=20,
                                intelligence=12, wisdom=14, charisma=12),
        saving_throws={"Strength": 11, "Dexterity": 9, "Constitution": 11,
                       "Wisdom": 7},
        skills={"Athletics": 11, "Acrobatics": 9, "Intimidation": 6,
                "Perception": 7},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        actions=[
            Action("Multiattack", "x4 Adamantine Sword", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=4,
                   multiattack_targets=["Adamantine Sword",
                                        "Adamantine Sword",
                                        "Adamantine Sword",
                                        "Adamantine Sword"]),
            Action("Adamantine Sword", "Melee (drow poison)", 11, "2d6+5", 0,
                   "slashing", applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=15),
        ],
        features=[
            Feature("Indomitable", "3/day: reroll a failed saving throw "
                    "(treated as Legendary Resistance).",
                    feature_type="passive", uses_per_day=3),
            Feature("Action Surge", "Recharge 5-6: takes one additional "
                    "action on its turn (a second Multiattack).",
                    recharge="5-6"),
            Feature("Adamantine Armour", "Immune to extra damage from "
                    "critical hits."),
            Feature("Fey Ancestry", "Advantage vs Charmed",
                    mechanic="fey_ancestry"),
            Feature("Strike", "Legendary Action (1): one Adamantine Sword "
                    "attack.", feature_type="legendary", legendary_cost=1),
            Feature("Commander's Order", "Legendary Action (2): a friendly "
                    "creature within 30 ft may use its reaction to move up "
                    "to its speed and make one weapon attack.",
                    feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Talo Dyrrin sotapäällikkö, Velve Dro -armeijan komentaja; "
             "vaikuttaa raskaasti pääkaupungin politiikassa. Kahden "
             "adamanttimiekan puhdas lähitaistelutuho.",
        tactics="Ryntää kovimman uhan kimppuun, Action Surge kahdeksaan "
                "iskuun ratkaisuhetkellä, komentaa liittolaisia "
                "legendaarisilla toiminnoilla.",
        habitat="Underdark", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),

    # ================================================================= #
    # CR 13 — Nhilymra Zaer'vyn "Hämähäkin Huuli" (mastermind)
    # ================================================================= #
    CreatureStats(
        name="Nhilymra Zaer'vyn", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=17,
        armor_type="studded leather + Shield spell", hit_points=165,
        hit_dice="22d8+66", speed=30,
        abilities=AbilityScores(strength=10, dexterity=20, constitution=16,
                                intelligence=18, wisdom=16, charisma=16),
        saving_throws={"Dexterity": 10, "Intelligence": 9, "Wisdom": 8},
        skills={"Deception": 8, "Insight": 8, "Perception": 8,
                "Stealth": 10, "Sleight of Hand": 10},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon, Thieves' cant",
        damage_resistances=["poison"],
        spellcasting_ability="Intelligence", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2, "5th": 1},
        spell_names=[
            "Shield", "Misty Step", "Counterspell", "Hold Person",
            "Hypnotic Pattern", "Greater Invisibility", "Hold Monster",
        ],
        actions=[
            Action("Multiattack", "x2 Poisoned Dagger", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Poisoned Dagger", "Poisoned Dagger"]),
            Action("Poisoned Dagger", "Melee/Ranged (finesse)", 10, "1d4+5",
                   0, "piercing", range=20, applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=16),
        ],
        features=[
            Feature("Sneak Attack", "Once per turn +7d6 damage when she has "
                    "advantage or an ally is within 5 ft of the target."),
            Feature("Cunning Action", "Dash, Disengage or Hide as a bonus "
                    "action each turn."),
            Feature("Uncanny Dodge", "Reaction: halve the damage of one "
                    "attack that hits her.", feature_type="reaction"),
            Feature("Evasion", "On a successful DEX save for half damage she "
                    "takes none; half on a failure."),
            Feature("Mastermind's Web", "Legendary Action (2): one creature "
                    "she can see makes a DC 16 WIS save or is charmed and "
                    "acts on her command until the end of its next turn.",
                    feature_type="legendary", legendary_cost=2),
            Feature("Shadow Slip", "Legendary Action (1): teleport 30 ft "
                    "between shadows.", feature_type="legendary",
                    legendary_cost=1),
        ],
        legendary_action_count=3,
        lore="Vorzhan Kuiskaajakunnan johtaja ja Talo Zaer'vynin ilharess. "
             "Ei raakaa voimaa vaan myrkkyjä, reaktioita ja mielten "
             "hallintaa taistelukentällä.",
        tactics="Pysyy näkymättömänä, iskee sneak attackeja varjoista, "
                "kääntää pelaajien vahvimman hahmon heitä vastaan "
                "Mastermind's Webillä.",
        habitat="Underdark", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5),

    # ================================================================= #
    # CR 14 — Zhindia Oblodra "Hiljainen Kuningatar" (psion)
    # ================================================================= #
    CreatureStats(
        name="Zhindia Oblodra", size="Medium", creature_type="Humanoid",
        native_plane="Underdark", alignment="Lawful Evil", armor_class=16,
        armor_type="psychic barrier", hit_points=187, hit_dice="22d8+88",
        speed=30, fly_speed=30,
        abilities=AbilityScores(strength=8, dexterity=16, constitution=18,
                                intelligence=20, wisdom=18, charisma=16),
        saving_throws={"Intelligence": 10, "Wisdom": 9, "Charisma": 8},
        skills={"Arcana": 10, "Insight": 9, "Perception": 9},
        senses="Darkvision 120 ft., Telepathy 120 ft.",
        languages="Deep Speech, Undercommon, telepathy",
        damage_resistances=["psychic"],
        spellcasting_ability="Intelligence", spell_save_dc=17,
        spell_attack_bonus=10,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2,
                     "6th": 1},
        spell_names=[
            "Hold Person", "Hypnotic Pattern", "Hold Monster",
            "Telekinesis", "Synaptic Static", "Power Word Stun",
        ],
        actions=[
            Action("Multiattack", "x3 Mind Sliver", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Mind Sliver", "Mind Sliver",
                                        "Mind Sliver"]),
            Action("Mind Sliver", "Ranged psionic", 10, "3d8", 0, "psychic",
                   range=60),
            Action("Mind Blast", "60ft cone DC 17 INT or Stunned", 0, "5d8",
                   0, "psychic", range=60, aoe_radius=60, aoe_shape="cone",
                   condition_dc=17, condition_save="Intelligence",
                   applies_condition="Stunned"),
        ],
        features=[
            Feature("Psionic Fortitude", "3/day: choose to succeed on a "
                    "failed save (Legendary Resistance).",
                    feature_type="passive", uses_per_day=3),
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Telepathic Web", "Can maintain telepathic domination "
                    "over several thralls across the city."),
            Feature("Dominate", "Legendary Action (2): one creature within "
                    "60 ft makes a DC 17 WIS save or is dominated until the "
                    "end of its next turn.", feature_type="legendary",
                    legendary_cost=2),
            Feature("Psychic Lance", "Legendary Action (1): one Mind Sliver.",
                    feature_type="legendary", legendary_cost=1),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Mielenlukijoiden (Oblodra) johtaja, joka hallitsee "
             "Dusklornista mutta ulottaa telepaattisen otteensa "
             "pääkaupunkiin. Raskas psioniikka ja mielenhallinta.",
        tactics="Aloittaa Mind Blastilla (stun-cone), dominoi vahvimman "
                "hahmon, pysyy leijuen ja etäällä psyykkisen suojan takana.",
        habitat="Underdark", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),

    # ================================================================= #
    # CR 6 — "Murtunut" Thol (minotauri-gladiaattori, mahd. liittolainen)
    # ================================================================= #
    CreatureStats(
        name="\"Murtunut\" Thol", size="Large", creature_type="Monstrosity",
        native_plane="Underdark", alignment="Neutral", armor_class=14,
        armor_type="hide + shield", hit_points=126, hit_dice="12d10+60",
        speed=40,
        abilities=AbilityScores(strength=20, dexterity=11, constitution=20,
                                intelligence=8, wisdom=12, charisma=9),
        saving_throws={"Strength": 8, "Constitution": 8},
        skills={"Athletics": 8, "Intimidation": 5, "Perception": 4},
        senses="Darkvision 60 ft.", languages="Abyssal, Undercommon",
        actions=[
            Action("Multiattack", "Greataxe + Gore", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Greataxe", "Gore"]),
            Action("Greataxe", "Melee", 8, "2d12+5", 0, "slashing", reach=5),
            Action("Gore", "Melee (after 10+ ft charge: +2d8 & DC 16 STR or "
                   "pushed 10 ft/Prone)", 8, "2d8+5", 0, "piercing", reach=5,
                   applies_condition="Prone", condition_save="Strength",
                   condition_dc=16),
        ],
        features=[
            Feature("Charge", "If it moves 10+ ft straight then Gores, the "
                    "target takes an extra 2d8 and must save or be pushed/"
                    "Prone."),
            Feature("Reckless", "Can attack with advantage on its turn; "
                    "attacks against it also have advantage until its next "
                    "turn."),
            Feature("Labyrinthine Recall", "Perfectly remembers any path it "
                    "has walked."),
        ],
        lore="Dra'kielin slummin tappeluklubin kieltä puhumaton orja-kapo "
             "minotauri. Säälimätön areenalla, mutta mahdollinen "
             "liittolainen Kruskille (orjasta orjalle).",
        tactics="Ryntää ja puskee kovimman vastuksen, hyökkää holtittomasti "
                "(Reckless) suuren vahingon toivossa.",
        loot_table="Arena-panttivankien merkit, katkennut kahle.",
        habitat="Underdark", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3),
]
