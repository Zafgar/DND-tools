"""Fort Whitestone — Walker-suvun mekaaninen armeija (Protokolla Omega).

Pelattavat konstruktistat kampanjan Maclebar Isle / Fort Whitestone
-kohtaamisiin. Nämä ovat kosmisen karanteenin vartijoita: niiden
ensisijainen ohjelmointi (Protokolla Omega) on tuhota "Uusi Keisari" eli
kuka tahansa joka resonoi muinaisten Veru-ihonpalojen kanssa (mm. Krusk).

Magic Resistance / Legendary Resistance käyttävät moottorin natiiveja
kenttiä; Protokolla Omega on kuvattu Feature-tekstinä (DM soveltaa
etu-/priorisointisääntöä Veru-kantajia vastaan).
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


monsters = [
    # ================================================================= #
    # CR 4 — Automata Trooper (mekaaninen jalkaväki, 8000 yksikköä)
    # ================================================================= #
    CreatureStats(
        name="Automata Trooper", size="Medium", creature_type="Construct",
        native_plane="Material Plane", alignment="Lawful Neutral",
        armor_class=16, hit_points=52, hit_dice="8d8+16", speed=30,
        abilities=AbilityScores(strength=15, dexterity=12, constitution=14,
                                intelligence=6, wisdom=10, charisma=1),
        saving_throws={"Constitution": 4},
        senses="Darkvision 60 ft.", languages="understands Walker-command "
                                               "cant, can't speak",
        damage_immunities=["poison", "psychic"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Paralyzed", "Petrified", "Poisoned"],
        actions=[
            Action("Multiattack", "x2 Integrated Rifle", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Integrated Rifle",
                                        "Integrated Rifle"]),
            Action("Integrated Rifle", "Ranged", 5, "2d6+1", 0, "piercing",
                   range=80, long_range=240),
            Action("Slam", "Melee", 5, "2d6", 2, "bludgeoning"),
        ],
        features=[
            Feature("Constructed Resilience", "Immune to poison/psychic and "
                    "to charm, exhaustion, fear, paralysis, petrification, "
                    "poison; doesn't need to breathe, eat or sleep."),
            Feature("Protocol Omega", "Prioritises and has advantage on "
                    "attacks against any creature resonating with the Veru "
                    "skin-shards (the 'New Emperor', e.g. Krusk)."),
        ],
        lore="Walker-suvun mekaaninen jalkaväkirobotti. Fort Whitestonen "
             "taskuulottuvuudessa on varastoituna 8000 yksikköä.",
        tactics="Liikkuu tarkoissa muodostelmissa, keskittää tulen "
                "Protokolla Omegan osoittamaan kohteeseen.",
        habitat="Fort Whitestone", challenge_rating=4.0, xp=1100,
        proficiency_bonus=2),

    # ================================================================= #
    # CR 14 — Whitestone Colossus (muuria vartioiva jättigolem)
    # ================================================================= #
    CreatureStats(
        name="Whitestone Colossus", size="Huge", creature_type="Construct",
        native_plane="Material Plane", alignment="Lawful Neutral",
        armor_class=18, armor_type="marble & adamantine plating",
        hit_points=210, hit_dice="20d12+80", speed=30,
        abilities=AbilityScores(strength=24, dexterity=9, constitution=18,
                                intelligence=3, wisdom=11, charisma=1),
        saving_throws={"Strength": 12, "Constitution": 9},
        senses="Darkvision 120 ft.", languages="understands Walker-command "
                                                "cant, can't speak",
        damage_immunities=["poison", "psychic",
                           "bludgeoning piercing slashing (non-magic)"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Paralyzed", "Petrified", "Poisoned"],
        actions=[
            Action("Multiattack", "x2 Slam", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Slam", "Slam"]),
            Action("Slam", "Melee", 11, "3d10+7", 0, "bludgeoning", reach=10),
            Action("Siege Cannon", "60ft line DC 17 DEX half", 8, "8d6", 0,
                   "force", range=60, aoe_radius=60, aoe_shape="line",
                   condition_dc=17, condition_save="Dexterity"),
            # Legendary
            Action("Ground Slam", "AoE 10ft DC 17 STR or Prone", 11, "2d10+7",
                   0, "bludgeoning", action_type="legendary", aoe_radius=10,
                   aoe_shape="sphere", condition_dc=17,
                   condition_save="Strength", applies_condition="Prone"),
        ],
        features=[
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Immutable Form", "Immune to any effect that would alter "
                    "its form."),
            Feature("Siege Monster", "Deals double damage to objects and "
                    "structures."),
            Feature("Protocol Omega", "Prioritises the 'New Emperor' — any "
                    "Veru-shard bearer (e.g. Krusk) — as its designated "
                    "kill target."),
            Feature("Stomp", "Legendary Action (1): one Ground Slam.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Siege Volley", "Legendary Action (2): recharge and fire "
                    "the Siege Cannon.", feature_type="legendary",
                    legendary_cost=2),
        ],
        legendary_action_count=3,
        lore="Fort Whitestonen muureja vartioiva marmori- ja "
             "adamanttigolem. Osa Walker-suvun kosmista karanteenia "
             "kahlittua Garrutha-titaania vastaan.",
        tactics="Vartioi kiinteää asemaa; murskaa lähelle tulevat, tulittaa "
                "Siege Cannonilla ja priorisoi Veru-kantajaa.",
        loot_table="Adamanttiromu, Walker-teknologian sirpaleet.",
        habitat="Fort Whitestone", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),
]
