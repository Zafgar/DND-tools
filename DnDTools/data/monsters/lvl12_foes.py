"""Lvl 12 -vastukset — mökkisession tasapainotetut kohtaamiset.

Kahdeksan nimettyä kohtaamista tason 12 ryhmälle (Beatrice, Magnus,
Balthazar, Thomas, Kairon) sekä Kruskin/Padakin 1 vs 1 -taistelut.
Nämä pohjat on suunniteltu haastaviksi ja taktisiksi; ne kytkeytyvät
Novus Somnium -kampanjan Aterterran drow'hin, Ravenstonen epäkuolleisiin,
Maclebar Islen automaatioon, Emnarin vihreään armeijaan ja Red Dagger
-salamurhaajakiltaan.

Rider-vahingot (esim. myrkkyterät, necrotic-purennat) on koottu yhteen
moniosaiseen noppalausekkeeseen (``1d8+3d6``), jota moottorin
noppaparseri nyt tukee; ``damage_bonus`` kantaa kiinteän osan.
Loitsijat viittaavat loitsuihin nimellä (``spell_names`` /
``cantrip_names``) keskitetystä loitsukirjastosta — omia holdereita ei
luoda. Legendaariset toiminnot, Magic Resistance ja Legendary
Resistance käyttävät moottorin natiiveja kenttiä. Muutamia puhtaasti
tunnelmallisia cantrippeja (Dancing Lights, Produce Flame, Thaumaturgy)
ei ole loitsukirjastossa; ne on kuvattu Feature-tekstissä.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


monsters = [
    # ================================================================= #
    # Kohtaaminen 1 — Aterterra: Velve Dro -Eliittipartio
    # ================================================================= #
    CreatureStats(
        name="Velve Dro Invisiittori", size="Medium",
        creature_type="Humanoid", native_plane="Underdark",
        alignment="Lawful Evil", armor_class=17, armor_type="Studded Leather",
        hit_points=135, hit_dice="18d8+54", speed=30,
        abilities=AbilityScores(strength=11, dexterity=20, constitution=16,
                                intelligence=14, wisdom=16, charisma=18),
        saving_throws={"Dexterity": 9, "Wisdom": 7, "Charisma": 8},
        skills={"Perception": 7, "Stealth": 13, "Insight": 7},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        spellcasting_ability="Charisma", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_names=["Darkness", "Faerie Fire", "Dispel Magic", "Silence"],
        actions=[
            Action("Multiattack", "x3 Faerzress Rapier tai Hand Crossbow", 0,
                   "", 0, "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Faerzress Rapier", "Faerzress Rapier",
                                        "Faerzress Rapier"]),
            Action("Faerzress Rapier", "Melee (myrkkyterä)", 9, "1d8+3d6", 5,
                   "piercing", range=5),
            Action("Hand Crossbow", "Ranged (DC 15 CON tai Poisoned 1h; "
                   "epäonnistuu 5:llä -> Unconscious)", 9, "1d6", 5,
                   "piercing", range=30, long_range=120,
                   applies_condition="Poisoned", condition_save="Constitution",
                   condition_dc=15),
        ],
        features=[
            Feature("Innate Spellcasting", "CHA, DC 16. At will: Dancing "
                    "Lights. 1/day each: Darkness, Faerie Fire, Dispel Magic, "
                    "Silence."),
            Feature("Fey Ancestry", "Advantage vs Charmed; magic can't put it "
                    "to sleep", mechanic="fey_ancestry"),
            Feature("Sunlight Sensitivity", "Disadvantage on attacks and "
                    "Perception (sight) in sunlight."),
            Feature("Parry", "Reaction: +3 AC against one melee attack it can "
                    "see.", feature_type="reaction"),
        ],
        lore="Kenraali Dantrag Dyrrin fanaattinen Velve Dro -kapteeni. "
             "Eristää ryhmän loitsijat Silence- ja Darkness-loitsuilla.",
        tactics="Avaa Silencellä pelaajien loitsijoiden päälle, sitten "
                "Faerie Fire kohteisiin joita liskot iskevät; kolme "
                "rapieri-iskua kovimpaan lähiuhkaan, Parry säästöön.",
        habitat="Underdark", challenge_rating=8.0, xp=3900,
        proficiency_bonus=3),

    CreatureStats(
        name="Velve Dro Varjoterä", size="Medium",
        creature_type="Humanoid", native_plane="Underdark",
        alignment="Lawful Evil", armor_class=16, armor_type="Studded Leather",
        hit_points=84, hit_dice="13d8+26", speed=30,
        abilities=AbilityScores(strength=12, dexterity=18, constitution=14,
                                intelligence=13, wisdom=14, charisma=12),
        skills={"Stealth": 10, "Acrobatics": 7},
        senses="Darkvision 120 ft.", languages="Elvish, Undercommon",
        actions=[
            Action("Multiattack", "x2 Poisoned Shortsword", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Poisoned Shortsword",
                                        "Poisoned Shortsword"]),
            Action("Poisoned Shortsword", "Melee (myrkkyterä)", 7, "1d6+2d6",
                   4, "piercing", range=5),
        ],
        features=[
            Feature("Sneak Attack (1/turn)", "+14 (4d6) damage on a hit with "
                    "advantage or when an ally is within 5 ft of the target.",
                    mechanic="sneak_attack", mechanic_value="4d6"),
            Feature("Assassinate", "Advantage vs creatures that haven't acted; "
                    "hits vs surprised targets are critical."),
            Feature("Fey Ancestry", "Advantage vs Charmed",
                    mechanic="fey_ancestry"),
        ],
        lore="Velve Dro -salamurhaaja joka iskee varjoista Assassinate-edulla.",
        tactics="Pysyy piilossa ensimmäiseen iskuun asti, kohdistaa "
                "Sneak Attack + Assassinate loitsijoihin.",
        habitat="Underdark", challenge_rating=5.0, xp=1800,
        proficiency_bonus=3),

    CreatureStats(
        name="Faerzress-Kiipeilijalisko", size="Large",
        creature_type="Monstrosity", native_plane="Underdark",
        alignment="Unaligned", armor_class=16, armor_type="Natural Armor",
        hit_points=90, hit_dice="12d10+24", speed=40, climb_speed=40,
        abilities=AbilityScores(strength=18, dexterity=14, constitution=14,
                                intelligence=3, wisdom=12, charisma=7),
        senses="Darkvision 60 ft.", languages="—",
        actions=[
            Action("Multiattack", "x2 Claw", 0, "", 0, "", is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Claw", "Claw"]),
            Action("Claw", "Melee", 7, "2d8+4", 0, "slashing", range=5),
            Action("Adhesive Filament", "Ranged (Grappled, Escape DC 14; voi "
                   "vetää 25 ft)", 7, "", 0, "", range=60,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=14),
        ],
        features=[
            Feature("Spider Climb", "Climbs difficult surfaces and ceilings "
                    "without an ability check."),
            Feature("Faerzress Camouflage", "Advantage on Stealth in "
                    "crystal-lit underground terrain."),
            Feature("Adhesive Filament", "Recharge 5-6.", recharge="5-6"),
        ],
        lore="Cave Fisher -variantti joka iskee katosta ja vetää kohteet "
             "irti ryhmästä.",
        tactics="Ampuu filamentin eristääkseen Thomaksen tai Kaironin ja "
                "vetää heidät katoksen alle, sitten claw-hyökkäykset.",
        habitat="Underdark", challenge_rating=4.0, xp=1100,
        proficiency_bonus=2),

    # ================================================================= #
    # Kohtaaminen 2 — Ravenstone: Dimeriuksen Pimeä Verho
    # ================================================================= #
    CreatureStats(
        name="Kreivitar Vila Norgrad", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Lawful Evil", armor_class=16, armor_type="Natural Armor",
        hit_points=144, hit_dice="17d8+68", speed=30,
        abilities=AbilityScores(strength=18, dexterity=18, constitution=18,
                                intelligence=17, wisdom=15, charisma=18),
        saving_throws={"Dexterity": 9, "Wisdom": 7, "Charisma": 9},
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        senses="Darkvision 120 ft.", languages="Common, Elvish",
        spellcasting_ability="Intelligence", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 1},
        spell_names=["Shield", "Magic Missile", "Mirror Image", "Hold Person",
                     "Counterspell", "Fireball", "Blight",
                     "Greater Invisibility", "Cloudkill"],
        cantrip_names=["Mage Hand", "Ray of Frost"],
        actions=[
            Action("Multiattack", "x2 Unarmed Strike", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Unarmed Strike", "Unarmed Strike"]),
            Action("Unarmed Strike", "Melee (+ necrotic)", 9, "1d8+4d6", 4,
                   "bludgeoning", range=5),
            Action("Charm", "30 ft (DC 17 WIS tai charmed 24h)", 0, "", 0, "",
                   range=30, applies_condition="Charmed",
                   condition_save="Wisdom", condition_dc=17),
        ],
        features=[
            Feature("Spellcasting", "9th-level caster (INT, DC 16, +8 to "
                    "hit). Cantrips: Mage Hand, Ray of Frost. Notables: "
                    "Shield, Magic Missile, Mirror Image, Hold Person, "
                    "Counterspell, Fireball, Blight, Greater Invisibility, "
                    "Cloudkill."),
            Feature("Regeneration", "Regains 20 HP at the start of its turn "
                    "unless it took radiant damage since its last turn."),
            Feature("Vampire Weaknesses", "Sunlight, running water (as a "
                    "standard vampire)."),
            Feature("Legendary Move", "Legendary Action (1): moves its speed "
                    "without provoking opportunity attacks.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendary Strike", "Legendary Action (1): one Unarmed "
                    "Strike.", feature_type="legendary", legendary_cost=1),
            Feature("Legendary Cantrip", "Legendary Action (1): casts one "
                    "cantrip.", feature_type="legendary", legendary_cost=1),
        ],
        legendary_action_count=3,
        lore="Dimerius Blackfeetin vampyyri-kreivitär, joka valvoo "
             "Ravenstonen kattojen rajassa ja kääntää eläviä toisiaan vastaan.",
        tactics="Aloittaa Greater Invisibilityllä, heittää Fireball/Cloudkill "
                "ryhmiin, Charm kovimpaan lähitaistelijaan, Counterspell "
                "pelaajien avainloitsuihin; legendaariset liikkeet pitävät "
                "sen ulottumattomissa.",
        habitat="Ravenstone", challenge_rating=11.0, xp=7200,
        proficiency_bonus=4),

    CreatureStats(
        name="Ravenstonen Ghoul-murskaaja", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Chaotic Evil", armor_class=14, armor_type="Natural Armor",
        hit_points=65, hit_dice="10d8+20", speed=40,
        abilities=AbilityScores(strength=16, dexterity=15, constitution=14,
                                intelligence=7, wisdom=10, charisma=8),
        damage_immunities=["poison"],
        condition_immunities=["Charmed", "Exhaustion", "Poisoned"],
        senses="Darkvision 60 ft.", languages="Common",
        actions=[
            Action("Multiattack", "Bite + Claws", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Bite", "Claws"]),
            Action("Bite", "Melee", 5, "2d8+3", 0, "piercing", range=5),
            Action("Claws", "Melee (DC 13 CON tai Paralyzed 1 min)", 5,
                   "2d6+3", 0, "slashing", range=5,
                   applies_condition="Paralyzed", condition_save="Constitution",
                   condition_dc=13),
        ],
        features=[
            Feature("Paralyzing Claws", "A non-elf, non-undead creature hit by "
                    "Claws must succeed on a DC 13 CON save or be Paralyzed "
                    "for 1 minute (save again at end of each of its turns)."),
        ],
        lore="Dimeriuksen henkilökohtainen ghoul-murskaaja; hyökkää sokeasti "
             "ja halvaannuttaa saaliinsa.",
        tactics="Rynnii Magnuksen ja Kaironin kimppuun, yrittää halvaannuttaa "
                "heidät kreivittären iskuja varten.",
        habitat="Ravenstone", challenge_rating=3.0, xp=700,
        proficiency_bonus=2),

    # ================================================================= #
    # Kohtaaminen 3 — Maclebar Isle: Riskin Eliminointi -Protokolla
    # ================================================================= #
    CreatureStats(
        name="A.E.G.I.S. Titaani", size="Large",
        creature_type="Construct", native_plane="Material",
        alignment="Unaligned", armor_class=20, armor_type="Natural Armor",
        hit_points=210, hit_dice="20d10+100", speed=30,
        abilities=AbilityScores(strength=24, dexterity=9, constitution=20,
                                intelligence=3, wisdom=11, charisma=1),
        damage_immunities=["fire", "poison", "psychic",
                           "bludgeoning, piercing, slashing from nonmagical "
                           "attacks not made with adamantine weapons"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Paralyzed", "Petrified", "Poisoned"],
        senses="Darkvision 120 ft.", languages="—",
        actions=[
            Action("Multiattack", "x2 Slam", 0, "", 0, "", is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Slam", "Slam"]),
            Action("Slam", "Melee", 11, "3d8+7", 0, "bludgeoning", range=5),
            Action("Poison Breath", "15 ft Cone (DC 19 CON, half on save)", 0,
                   "10d8", 0, "poison", range=15, aoe_radius=15,
                   aoe_shape="cone", condition_save="Constitution",
                   condition_dc=19),
        ],
        features=[
            Feature("Magic Resistance", "Advantage on saving throws against "
                    "spells and other magical effects",
                    mechanic="magic_resistance"),
            Feature("Fire Absorption", "Takes no fire damage; instead regains "
                    "HP equal to the fire damage dealt."),
            Feature("Poison Breath", "Recharge 5-6.", recharge="5-6"),
        ],
        lore="Walker-suvun rautagolem-variantti, joka aktivoituu Fort "
             "Whitestonen 'Riskin Eliminointi' -protokollasta.",
        tactics="Raaka tankki: Poison Breath hallitsee tilaa, muuten kaksi "
                "slam-iskua lähimpään; tulivahinko vain parantaa sitä.",
        habitat="Maclebar Isle", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5),

    CreatureStats(
        name="Kellopeli-Eliminoija", size="Medium",
        creature_type="Construct", native_plane="Material",
        alignment="Unaligned", armor_class=17, armor_type="Natural Armor",
        hit_points=93, hit_dice="11d8+44", speed=40,
        abilities=AbilityScores(strength=14, dexterity=20, constitution=18,
                                intelligence=10, wisdom=14, charisma=1),
        skills={"Acrobatics": 8, "Stealth": 11},
        damage_immunities=["poison", "psychic"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Paralyzed", "Poisoned"],
        senses="Darkvision 60 ft.", languages="—",
        actions=[
            Action("Multiattack", "x3 Electrified Blade", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Electrified Blade",
                                        "Electrified Blade",
                                        "Electrified Blade"]),
            Action("Electrified Blade", "Melee (+ lightning)", 8, "1d8+2d6", 5,
                   "slashing", range=5),
        ],
        features=[
            Feature("Evasion", "On a Dex save for half damage, takes no damage "
                    "on success and half on failure.", mechanic="evasion"),
        ],
        lore="Clockwork Assassin, joka liikkuu piilosta ja tappaa ryhmän "
             "heikoimmat.",
        tactics="Liikkuu nopeasti Balthazarin/Kaironin kimppuun, kolme "
                "salamaterä-iskua; Evasion suojaa AoE-loitsuilta.",
        habitat="Maclebar Isle", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3),

    # ================================================================= #
    # Kohtaaminen 4 — Oblitus: Emnarin Vihreän Armeijan Iskujoukko
    # ================================================================= #
    CreatureStats(
        name="Shug Orgar -Sotapaallikko", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Chaotic Evil", armor_class=18, armor_type="Plate Armor",
        hit_points=153, hit_dice="18d8+72", speed=30,
        abilities=AbilityScores(strength=20, dexterity=12, constitution=18,
                                intelligence=11, wisdom=11, charisma=16),
        saving_throws={"Strength": 9, "Constitution": 8, "Wisdom": 4},
        senses="Darkvision 60 ft.", languages="Common, Orc",
        actions=[
            Action("Multiattack", "x3 Greataxe", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Greataxe", "Greataxe", "Greataxe"]),
            Action("Greataxe", "Melee (Gruumsh's Fury sisältyy)", 9, "1d12", 9,
                   "slashing", range=5),
            Action("Battle Cry", "1/day: orcs & monsters 30 ft get advantage "
                   "on attacks until end of next turn", 0, "", 0, "", range=30,
                   action_type="bonus"),
        ],
        features=[
            Feature("Aggressive", "Bonus Action: move up to its speed toward a "
                    "hostile creature it can see."),
            Feature("Gruumsh's Fury", "+4 damage on melee weapon hits (folded "
                    "into damage)."),
            Feature("Battle Cry", "1/day.", uses_per_day=1),
        ],
        lore="Emnarin vihreän armeijan raskaasti panssaroitu sotapäällikkö.",
        tactics="Aggressive-liike suoraan lähelle, Battle Cry avaamaan "
                "joukkojen edun, kolme greataxe-iskua kovimpaan hahmoon.",
        habitat="Oblitus", challenge_rating=9.0, xp=5000,
        proficiency_bonus=4),

    CreatureStats(
        name="Emnarin Verimaagi", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Chaotic Evil", armor_class=14, armor_type="Hide Armor",
        hit_points=90, hit_dice="12d8+36", speed=30,
        abilities=AbilityScores(strength=14, dexterity=14, constitution=16,
                                intelligence=10, wisdom=16, charisma=12),
        senses="Darkvision 60 ft.", languages="Common, Orc",
        spellcasting_ability="Wisdom", spell_save_dc=14, spell_attack_bonus=6,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 1},
        spell_names=["Command", "Cure Wounds", "Hold Person",
                     "Spiritual Weapon", "Haste", "Dispel Magic", "Blight"],
        cantrip_names=["Resistance"],
        actions=[
            Action("Spear", "Melee", 5, "1d6", 2, "piercing", range=5),
        ],
        features=[
            Feature("Spellcasting", "7th-level caster (WIS, DC 14, +6 to "
                    "hit). Cantrips: Produce Flame, Resistance. Notables: "
                    "Command, Cure Wounds, Hold Person, Spiritual Weapon, "
                    "Haste, Dispel Magic, Blight."),
            Feature("Blood Magic Sacrifice", "Bonus Action: lose 10 HP to "
                    "regain one 1st- or 2nd-level spell slot.",
                    feature_type="passive"),
        ],
        lore="Örkkien verishamaani joka tukee iskujoukkoa Hastella ja "
             "rankaisee Blightillä.",
        tactics="Haste sotapäällikölle heti, sitten Blight ja Spiritual "
                "Weapon; Blood Magic Sacrifice pitää slotit käytössä.",
        habitat="Oblitus", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3),

    CreatureStats(
        name="Panssaroitu Sota-Bulette", size="Large",
        creature_type="Monstrosity", native_plane="Material",
        alignment="Unaligned", armor_class=19, armor_type="Metal Plating",
        hit_points=114, hit_dice="12d10+48", speed=40, burrow_speed=40,
        abilities=AbilityScores(strength=19, dexterity=11, constitution=21,
                                intelligence=2, wisdom=10, charisma=5),
        senses="Darkvision 60 ft., Tremorsense 60 ft.", languages="—",
        actions=[
            Action("Bite", "Melee", 7, "4d12+4", 0, "piercing", range=5),
            Action("Deadly Leap", "15 ft radius (DC 16 STR/DEX, half & no "
                   "prone on save)", 0, "3d6+3d6", 8, "bludgeoning", range=5,
                   aoe_radius=15, aoe_shape="sphere",
                   applies_condition="Prone", condition_save="Dexterity",
                   condition_dc=16),
        ],
        features=[
            Feature("Tremorsense", "Senses vibrations within 60 ft."),
            Feature("Deadly Leap", "Lands in a 15 ft radius; each creature "
                    "there makes a DC 16 Str or Dex save, taking 14 (3d6+4) "
                    "bludgeoning + 14 (3d6+4) slashing and knocked Prone on a "
                    "failure, half and no prone on a success."),
        ],
        lore="Panssaroitu bulette-piirityskone, joka kaivautuu ja hyökkää "
             "altapäin rikkoen muodostelman.",
        tactics="Burrow lähelle, Deadly Leap ryhmän keskelle kaataen useita, "
                "sitten bite kaatuneisiin.",
        habitat="Oblitus", challenge_rating=7.0, xp=2900,
        proficiency_bonus=3),

    # ================================================================= #
    # 1 vs 1 — Krusk vs. Death's Vigilin Puhdistaja
    # ================================================================= #
    CreatureStats(
        name="Vigilin Puhdistaja", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Lawful Evil", armor_class=18, armor_type="Plate Armor",
        hit_points=135, hit_dice="18d8+54", speed=30,
        abilities=AbilityScores(strength=18, dexterity=10, constitution=16,
                                intelligence=12, wisdom=18, charisma=14),
        saving_throws={"Constitution": 7, "Wisdom": 8, "Charisma": 6},
        condition_immunities=["Frightened"],
        senses="Passive Perception 14", languages="Common",
        spellcasting_ability="Wisdom", spell_save_dc=16, spell_attack_bonus=8,
        spell_names=["Toll the Dead", "Spirit Guardians", "Hold Person",
                     "Command"],
        actions=[
            Action("Multiattack", "x2 Radiant Mace", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Radiant Mace", "Radiant Mace"]),
            Action("Radiant Mace", "Melee (+ radiant)", 8, "1d8+3d8", 4,
                   "bludgeoning", range=5),
            Action("Condemn the Heretic", "30 ft (DC 16 CHA tai 6d8 necrotic "
                   "+ Frightened 1 min)", 0, "6d8", 0, "necrotic", range=30,
                   applies_condition="Frightened", condition_save="Charisma",
                   condition_dc=16),
        ],
        features=[
            Feature("Divine Vengeance", "When hit by a melee attack, the "
                    "attacker takes 5 (1d10) radiant damage."),
            Feature("Spellcasting", "9th-level caster (WIS, DC 16). At will: "
                    "Toll the Dead, Thaumaturgy. 1/day each: Spirit Guardians "
                    "(4th level, 4d8 radiant, 15 ft), Hold Person, Command."),
            Feature("Condemn the Heretic", "Recharge 5-6.", recharge="5-6"),
        ],
        lore="Mortem-jumalan fanaattinen inkvisiittori, joka haastaa Kruskin "
             "kaksintaisteluun.",
        tactics="Spirit Guardians heti rajoittamaan Kruskin liikettä, sitten "
                "kaksi Radiant Mace -iskua; Condemn the Heretic murtamaan "
                "raivon Frightenilla. Ei pelkää kuolemaa.",
        habitat="Aesica", challenge_rating=10.0, xp=5900,
        proficiency_bonus=4),

    # ================================================================= #
    # 1 vs 1 — Krusk vs. Dimeriuksen Verilähettiläs
    # ================================================================= #
    CreatureStats(
        name="Verilahettilas", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Chaotic Evil", armor_class=16, armor_type="Natural Armor",
        hit_points=114, hit_dice="12d8+60", speed=40, climb_speed=30,
        abilities=AbilityScores(strength=16, dexterity=18, constitution=20,
                                intelligence=14, wisdom=12, charisma=16),
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        senses="Darkvision 60 ft.", languages="Common",
        actions=[
            Action("Multiattack", "Bite + x2 Claws", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Vampiric Bite", "Claws", "Claws"]),
            Action("Claws", "Melee", 8, "2d6+4", 0, "slashing", range=5),
            Action("Vampiric Bite", "Melee (+ necrotic; heals self)", 8,
                   "1d10+4d6", 4, "piercing", range=5),
            Action("Mist Step", "Bonus: teleport 30 ft as red mist", 0, "", 0,
                   "", range=30, action_type="bonus"),
        ],
        features=[
            Feature("Regeneration", "Regains 10 HP at the start of its turn."),
            Feature("Vampiric Bite", "Heals HP equal to the necrotic damage "
                    "dealt."),
            Feature("Mist Step", "Bonus Action: teleport up to 30 ft to an "
                    "unoccupied space it can see.", feature_type="bonus"),
            Feature("Mocking Blood-Burst", "Reaction (on dropping to 0 HP): "
                    "each creature within 10 ft makes a DC 16 DEX save or "
                    "takes 21 (6d6) necrotic damage.", feature_type="reaction"),
        ],
        lore="Dimeriuksen kammottava vampyyri-luomus, joka ei yritä voittaa "
             "vaan nöyryyttää.",
        tactics="Mist Step Kruskin taakse, Vampiric Bite parantamaan itseään; "
                "kuollessaan räjähtää veripilveksi Mocking Blood-Burstilla.",
        habitat="Aesica", challenge_rating=8.0, xp=3900,
        proficiency_bonus=3),

    # ================================================================= #
    # 1 vs 1 — Padak vs. Ravenstonen Yövaanija
    # ================================================================= #
    CreatureStats(
        name="Crimson Night-Stalker", size="Large",
        creature_type="Undead", native_plane="Material",
        alignment="Neutral Evil", armor_class=16, armor_type="Natural Armor",
        hit_points=142, hit_dice="15d10+60", speed=50, climb_speed=50,
        abilities=AbilityScores(strength=20, dexterity=16, constitution=18,
                                intelligence=6, wisdom=14, charisma=8),
        skills={"Stealth": 11, "Perception": 6},
        senses="Darkvision 120 ft.", languages="—",
        actions=[
            Action("Multiattack", "x2 Claw", 0, "", 0, "", is_multiattack=True,
                   multiattack_count=2, multiattack_targets=["Claw", "Claw"]),
            Action("Claw", "Melee", 9, "2d8+5", 0, "slashing", range=5),
            Action("Bite", "Melee", 9, "2d10+5", 0, "piercing", range=5),
            Action("Terrifying Howl", "30 ft (DC 15 WIS tai Frightened 1 min, "
                   "speed 0 near it)", 0, "", 0, "", range=30, aoe_radius=30,
                   aoe_shape="sphere", applies_condition="Frightened",
                   condition_save="Wisdom", condition_dc=15),
        ],
        features=[
            Feature("Pounce", "If it moves 20+ ft straight toward a target and "
                    "hits with a Claw, the target makes a DC 17 Str save or is "
                    "knocked Prone; if Prone, it can make one Bite as a Bonus "
                    "Action."),
            Feature("Terrifying Howl", "Recharge 5-6.", recharge="5-6"),
        ],
        lore="Gargoylen ja vampyyrin risteytys, joka metsästää tunkeilijoita "
             "Ravenstonessa.",
        tactics="Pounce katosta kaataakseen Padakin, Terrifying Howl "
                "estämään pakoa (speed 0), sitten claw + bite kaatuneeseen.",
        habitat="Ravenstone", challenge_rating=9.0, xp=5000,
        proficiency_bonus=4),

    # ================================================================= #
    # Ryhmä vs. Red Dagger -Salamurhaajat
    # ================================================================= #
    CreatureStats(
        name="Red Dagger -Pyoveli", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Lawful Evil", armor_class=17, armor_type="Half Plate",
        hit_points=150, hit_dice="20d8+60", speed=30,
        abilities=AbilityScores(strength=18, dexterity=16, constitution=16,
                                intelligence=12, wisdom=14, charisma=10),
        saving_throws={"Strength": 8, "Dexterity": 7, "Constitution": 7},
        senses="Passive Perception 12", languages="Common, Thieves' Cant",
        actions=[
            Action("Multiattack", "x3 Red Dagger Halberd", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Red Dagger Halberd",
                                        "Red Dagger Halberd",
                                        "Red Dagger Halberd"]),
            Action("Red Dagger Halberd", "Melee reach 10 ft (Brute sisältyy; "
                   "DC 15 CON tai 3d6 poison)", 8, "2d10", 4, "slashing",
                   range=10, reach=10, applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=15),
        ],
        features=[
            Feature("Brute", "Melee weapons deal one extra damage die (folded "
                    "into damage)."),
            Feature("Executioner's Mark", "Chooses one target; attacks against "
                    "it score a critical hit on a d20 roll of 18-20."),
            Feature("Parry", "Reaction: +3 AC against one melee attack it can "
                    "see.", feature_type="reaction"),
        ],
        lore="Red Dagger -killan pyöveli, joka sitoo ryhmän raskaat iskijät "
             "lähitaisteluun 10 ft ulottuvalla hilparilla.",
        tactics="Executioner's Mark kohteeseen (esim. Padak), sitten kolme "
                "hilpari-iskua reach 10:llä; Parry säästämään osumia.",
        habitat="Frand", challenge_rating=10.0, xp=5900,
        proficiency_bonus=4),

    CreatureStats(
        name="Red Dagger -Varjokulkija", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Lawful Evil", armor_class=16, armor_type="Studded Leather",
        hit_points=90, hit_dice="12d8+36", speed=40,
        abilities=AbilityScores(strength=12, dexterity=18, constitution=14,
                                intelligence=11, wisdom=14, charisma=12),
        skills={"Stealth": 10, "Acrobatics": 8},
        senses="Passive Perception 12", languages="Common, Thieves' Cant",
        actions=[
            Action("Multiattack", "x2 Serrated Shortsword", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Serrated Shortsword",
                                        "Serrated Shortsword"]),
            Action("Serrated Shortsword", "Melee", 8, "1d6+4", 0, "piercing",
                   range=5),
            Action("Throwing Dagger", "Ranged", 8, "1d4+4", 0, "piercing",
                   range=20, long_range=60),
            Action("Blinding Powder", "15 ft Cone (DC 15 DEX tai Blinded)", 0,
                   "", 0, "", range=15, aoe_radius=15, aoe_shape="cone",
                   applies_condition="Blinded", condition_save="Dexterity",
                   condition_dc=15),
        ],
        features=[
            Feature("Sneak Attack (1/turn)", "+14 (4d6) damage on a hit with "
                    "advantage or when an ally is within 5 ft of the target.",
                    mechanic="sneak_attack", mechanic_value="4d6"),
            Feature("Cunning Action", "Bonus Action: Dash, Disengage, or "
                    "Hide.", mechanic="cunning_action"),
            Feature("Blinding Powder", "Recharge 5-6.", recharge="5-6"),
        ],
        lore="Red Dagger -killan varjokulkija, joka iskee kattojen ja "
             "varjojen kautta ryhmän loitsijoihin.",
        tactics="Cunning Action Hide -> Sneak Attack loitsijoihin (Kairon, "
                "Balthazar, Beatrice); Blinding Powder sokaisemaan puolustajat.",
        habitat="Frand", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3),
]
