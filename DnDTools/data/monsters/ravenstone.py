"""Ravenstone — Dimeriuksen vampyyrihovi, kryptan vartijat ja kaupungin
keskeiset hahmot.

Aiemmin nämä NPC:t viittasivat geneerisiin pohjiin ("Vampire",
"Vampire Spellcaster", "Assassin", "Noble"), joten heidän omat kykynsä
eivät näkyneet missään. Tässä jokainen saa oman statblockin lore-kykyineen.

Lähdedata vs. täydennys:
  * **Dimerius Blackfeet** on lähteessä CR 18 (AC 20, HP 225, kykyarvot,
    Life Drain, Regeneration 20, Misty Escape, Shapechanger, Legendary
    Resistance 3). Pelinjohtajan pyynnöstä hän on **buffattu CR 20:een**:
    HP 297, kolme legendaarista toimintoa, lair-toiminnot, korkeammat
    DC:t ja uusi Crimson Command -aura, joka komentaa kaupungin
    epäkuolleita.
  * **Golbera** ja **Xalars** on rakennettu lähteen kykykuvauksista
    (Myrkkypallo + Leap-reaktio; Warp Axe -reaktio + ENRAGE).
  * Muut vampyyrit ja kaupungin hahmot on rakennettu heidän
    lore-rooleistaan (Jugorain epäkuolleiden hallinta, Polsenin
    strategia, Beatricen nopeus ja mielenhallinta, Akselin hopea-arsenaali
    ja vastalääke, Lidianin tiedonvaihtokyky).

Loitsijat viittaavat loitsuihin nimellä keskitetystä loitsukirjastosta.
Rider-vahingot on koottu moniosaisiin noppalausekkeisiin (``1d8+4d6``).
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


monsters = [
    # ================================================================= #
    # LORDI DIMERIUS BLACKFEET — CR 20 (buffattu lähteen CR 18:sta)
    # ================================================================= #
    CreatureStats(
        name="Lordi Dimerius Blackfeet", size="Small",
        creature_type="Undead", native_plane="Material",
        alignment="Lawful Evil", armor_class=20, armor_type="Natural Armor",
        hit_points=297, hit_dice="27d8+216", speed=40, climb_speed=40,
        abilities=AbilityScores(strength=20, dexterity=18, constitution=22,
                                intelligence=16, wisdom=18, charisma=22),
        saving_throws={"Dexterity": 11, "Constitution": 13, "Wisdom": 11,
                       "Charisma": 13},
        skills={"Perception": 11, "Stealth": 11, "Deception": 13,
                "Insight": 11, "Intimidation": 13, "History": 10},
        senses="Darkvision 120 ft., Passive Perception 21",
        languages="Common, Goblin, Undercommon, Abyssal",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        damage_immunities=["poison"],
        condition_immunities=["Charmed", "Frightened", "Poisoned",
                              "Exhaustion"],
        spellcasting_ability="Charisma", spell_save_dc=21,
        spell_attack_bonus=13,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 2, "7th": 1},
        spell_names=["Darkness", "Hold Person", "Counterspell", "Fireball",
                     "Blight", "Greater Invisibility", "Cloudkill",
                     "Dominate Person", "Finger of Death", "Wall of Force"],
        cantrip_names=["Toll the Dead", "Ray of Frost", "Mage Hand"],
        actions=[
            Action("Multiattack",
                   "x3 (Life Drain Bite tai Grave Claws) — vaihtoehtoisesti "
                   "yksi loitsu ja yksi isku", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Life Drain Bite", "Grave Claws",
                                        "Grave Claws"]),
            Action("Life Drain Bite",
                   "Melee (elinvoiman juonti: uhri menettää 2d10 "
                   "elinvoimapistettä ja max HP laskee saman verran; "
                   "Dimerius paranee saman verran)", 13, "1d6+2d10", 5,
                   "necrotic", range=5),
            Action("Grave Claws", "Melee", 13, "2d6+2d8", 5, "slashing",
                   range=5),
            Action("Crimson Word",
                   "30 ft (DC 21 WIS tai Charmed 24 h — kohde näkee "
                   "Dimeriuksen isäntänään)", 0, "", 0, "", range=30,
                   applies_condition="Charmed", condition_save="Wisdom",
                   condition_dc=21),
            Action("Exsanguinate",
                   "Recharge 5-6: 20 ft säde (DC 21 CON tai 8d10 necrotic "
                   "ja max HP laskee; puolet onnistuneella). Dimerius "
                   "paranee puolet kokonaisvahingosta.", 0, "8d10", 0,
                   "necrotic", range=20, aoe_radius=20, aoe_shape="sphere",
                   condition_save="Constitution", condition_dc=21),
        ],
        features=[
            Feature("Legendary Resistance", "3/päivä: valitse onnistuvasi "
                    "epäonnistuneessa pelastusheitossa.",
                    feature_type="passive", uses_per_day=3),
            Feature("Regeneration", "Palauttaa 20 HP vuoronsa alussa, ellei "
                    "ole ottanut radiant-vahinkoa tai ole auringonvalossa "
                    "tai juoksevassa vedessä.", mechanic="regeneration",
                    mechanic_value="20"),
            Feature("Life Drain", "Onnistunut purenta vie uhrilta 2d10 "
                    "elinvoimaa (max HP laskee) ja parantaa Dimeriusta "
                    "saman verran. Uhri nousee vampyyrina jos kuolee näin.",
                    feature_type="passive"),
            Feature("Misty Escape", "Kun hän putoaa 0 HP:hen, hän muuttuu "
                    "sumupilveksi (ei tuhoudu) ja pakenee leposijaansa "
                    "Corvus Spelchrumiin, jossa elpyy hitaasti. Häntä ei "
                    "voi tappaa lopullisesti kentällä.",
                    feature_type="passive"),
            Feature("Shapechanger", "Voi muuttua sumuksi tai lepakoksi "
                    "(bonustoiminto); sumumuodossa immuuni fyysiselle "
                    "vahingolle ja mahtuu jokaiseen rakoon.",
                    feature_type="bonus"),
            Feature("Spider Climb", "Kiipeää pinnoilla ja katossa vapaasti "
                    "ilman ability checkiä."),
            Feature("Crimson Command",
                    "Aura 60 ft: kaikki Dimeriukselle uskolliset "
                    "epäkuolleet saavat +2 osumaheittoihin ja etua "
                    "pelastusheittoihin Turn Undeadia vastaan. Bonuksena "
                    "hän voi komentaa yhtä niistä käyttämään reaktionsa.",
                    aura_radius=60),
            Feature("Vampire Weaknesses",
                    "Auringonvalo (20 radiant/vuoro ja disadvantage), "
                    "juokseva vesi, valkopihlaja-vaarna sydämeen "
                    "lamaantuneena, ei voi ylittää kynnystä ilman kutsua."),
            Feature("Children of the Night", "1/päivä: kutsuu 3d6 lepakkoa "
                    "tai rottaa (tai 3 susilaumaa), jotka saapuvat 1d4 "
                    "kierroksessa ja tottelevat häntä.", uses_per_day=1),
            Feature("Exsanguinate", "Recharge 5-6.", recharge="5-6"),
            Feature("Legendaarinen: Liike", "Legendaarinen toiminto (1): "
                    "liikkuu nopeutensa provosoimatta.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Purenta", "Legendaarinen toiminto (1): "
                    "yksi Life Drain Bite.", feature_type="legendary",
                    legendary_cost=1),
            Feature("Legendaarinen: Veren käsky",
                    "Legendaarinen toiminto (2): yksi Charmed-kohde 60 ft "
                    "sisällä hyökkää välittömästi valitsemaansa "
                    "liittolaistaan (ei pelastusheittoa).",
                    feature_type="legendary", legendary_cost=2),
            Feature("Lair: Kryptan kuiskaus",
                    "Lair-toiminto (init 20): kaikki Dimeriuksen viholliset "
                    "Corvus Spelchrumissa tekevät DC 21 WIS -pelastuksen tai "
                    "ottavat 3d6 psychic ja ovat Frightened vuoronsa "
                    "loppuun.", feature_type="lair"),
            Feature("Lair: Sumun seinä",
                    "Lair-toiminto (init 20): 20 ft sumumuuri nousee — "
                    "täysi näkösuoja, jonka läpi vain Dimerius näkee.",
                    feature_type="lair"),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Muinainen gobliinivampyyri ja Ravenstonen perustaja. Ei juo "
             "verta vaan uhriensa elinvoimaa. Hallitsee kaupunkia varjoista "
             "ja pitää leposijaansa Corvus Spelchrumin kryptassa, jota "
             "vartioivat Golbera ja Xalars. Haluaa Clavise-miekan ja "
             "tietää sen olevan Lyran hallussa; lähetti Verilähettilään "
             "testaamaan Kruskia. Kaupungissa käydään hänen ja paroni "
             "Jugorain välistä vampyyrien sisällissotaa.",
        tactics="Ei koskaan taistele suoraan ennen kuin on pakko: Greater "
                "Invisibility, sumumuoto ja lair-toiminnot pitävät hänet "
                "ulottumattomissa. Crimson Word kääntää ryhmän kovimman "
                "iskijän omia vastaan, sitten Veren käsky -legendaarinen "
                "pakottaa tämän lyömään liittolaistaan. Exsanguinate "
                "imee koko ryhmän elinvoimaa ja parantaa häntä. Alle "
                "puolessa HP:stä hän kutsuu kryptan vartijat ja pakenee "
                "Misty Escapella — häntä ei voi tappaa kentällä, vain "
                "ajaa leposijalleen ja tuhota siellä vaarnalla.",
        loot_table="Blackfeetin sinetti, kryptan avain, elinvoima-ampulleja.",
        habitat="Ravenstone / Corvus Spelchrum",
        challenge_rating=20.0, xp=25000, proficiency_bonus=6),

    # ================================================================= #
    # CORVUS SPELCHRUM — kryptan erikoisvartijat
    # ================================================================= #
    CreatureStats(
        name="Golbera", size="Huge", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil",
        armor_class=17, armor_type="Natural Armor",
        hit_points=250, hit_dice="20d12+120", speed=30,
        abilities=AbilityScores(strength=22, dexterity=10, constitution=22,
                                intelligence=5, wisdom=12, charisma=6),
        saving_throws={"Constitution": 11, "Strength": 11},
        skills={"Perception": 5},
        senses="Darkvision 60 ft., Passive Perception 15",
        languages="ymmärtää Common ja Goblin mutta ei puhu",
        damage_resistances=["necrotic", "cold"],
        damage_immunities=["poison"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Poisoned"],
        actions=[
            Action("Multiattack", "x2 Rotting Claw", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Rotting Claw", "Rotting Claw"]),
            Action("Rotting Claw", "Melee reach 10 ft", 10, "2d10+4d6", 6,
                   "slashing", range=10, reach=10),
            Action("Myrkkypallo",
                   "Ranged 50 ft, purskahtaa 15 ft säteelle (DC 14 DEX/CON "
                   "tai 6d8 poison; puolet onnistuneella)", 10, "6d8", 0,
                   "poison", range=50, aoe_radius=15, aoe_shape="sphere",
                   condition_save="Constitution", condition_dc=14),
        ],
        features=[
            Feature("Leap",
                   "Reaktio: hyppää 30 ft valitsemansa kohteen päälle. "
                   "Kohteen on onnistuttava DC 12 DEX -pelastuksessa tai "
                   "se kaatuu Prone JA menettää toiminnon, jonka Golbera "
                   "keskeytti.", feature_type="reaction",
                   save_dc=12, save_ability="Dexterity",
                   applies_condition="Prone"),
            Feature("Alghoulin mahtavuus", "Huge-kokoinen epäkuollut: "
                    "grapple- ja shove-yrityksiin sitä vastaan tulee "
                    "disadvantage."),
            Feature("Undead Fortitude", "Kun se putoaisi 0 HP:hen (ei "
                    "radiant eikä kriitti), DC 5 + vahinko CON -pelastus "
                    "jättää sen 1 HP:hen."),
            Feature("Kryptan vartija", "Ei koskaan poistu Corvus "
                    "Spelchrumista; hyökkää heti kun hauta häiritään."),
        ],
        lore="Corvus Spelchrumin valtava epäkuollut vartija (Alghoul), "
             "joka suojelee Dimeriuksen hautaa. 250 HP paksua kuolleen "
             "lihan panssaria.",
        tactics="Avaa Myrkkypallolla 50 ft päästä hajottaakseen "
                "muodostelman, sitten Leap-reaktiolla keskeyttää "
                "loitsijan toiminnon ja kaataa tämän. Lähitaistelussa "
                "kaksi 10 ft ulottuvaa kynsi-iskua.",
        habitat="Corvus Spelchrum", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5),

    CreatureStats(
        name="Xalars", size="Large", creature_type="Undead",
        native_plane="Material", alignment="Chaotic Evil",
        armor_class=18, armor_type="Natural Armor (kärventynyt luu)",
        hit_points=228, hit_dice="19d10+114", speed=40,
        abilities=AbilityScores(strength=23, dexterity=13, constitution=22,
                                intelligence=8, wisdom=13, charisma=14),
        saving_throws={"Strength": 12, "Constitution": 12, "Wisdom": 6},
        skills={"Perception": 6, "Intimidation": 7, "Athletics": 12},
        senses="Darkvision 120 ft., Passive Perception 16",
        languages="Abyssal, Draconic, Minotaur",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        damage_immunities=["fire", "poison"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened",
                              "Poisoned"],
        actions=[
            Action("Multiattack", "x2 Warp Axe (ENRAGE-tilassa x3)", 0, "",
                   0, "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Warp Axe", "Warp Axe"]),
            Action("Warp Axe", "Melee reach 10 ft (+ tulivahinko)", 12,
                   "2d12+2d6", 6, "slashing", range=10, reach=10,
                   properties=["heavy", "reach"]),
            Action("Gore", "Melee (sarvet; jos liikkui 20 ft suoraan, "
                   "DC 18 STR tai Prone)", 12, "2d8", 6, "piercing",
                   range=5, applies_condition="Prone",
                   condition_save="Strength", condition_dc=18),
            Action("ENRAGE",
                   "Recharge 5-6: Xalars syttyy liekkeihin ja luo "
                   "laavalammikoita. Jokainen lähitaistelija ottaa "
                   "AUTOMAATTISESTI 3d12 tulivahinkoa (ei pelastusta). "
                   "Xalars saa +30 ft liikettä ja kolme kirvesiskua tällä "
                   "vuorolla.", 0, "3d12", 0, "fire", range=10,
                   aoe_radius=10, aoe_shape="sphere"),
        ],
        features=[
            Feature("Reaction: Warp Axe",
                   "Reaktio: heittää kirveensä 40 ft päähän. Osuessaan "
                   "Xalars siirtyy VÄLITTÖMÄSTI iskun mukana kohteen "
                   "viereen (teleportti).", feature_type="reaction"),
            Feature("ENRAGE", "Recharge 5-6: liekit, laavalammikot, "
                    "+30 ft liikettä ja kolme kirvesiskua.",
                    recharge="5-6"),
            Feature("Laavalammikot", "ENRAGEn jälkeen 10 ft alueelle jää "
                    "laavaa: 2d10 tulivahinkoa jokaiselle joka aloittaa "
                    "vuoronsa siinä (3 kierrosta)."),
            Feature("Fire Absorption", "Tulivahinko ei vahingoita: se "
                    "parantaa Xalarsia saman verran."),
            Feature("Undead Dragon's Fury", "Alle puolessa HP:stä Xalars "
                    "saa +2 osumaheittoihin ja Warp Axe tekee +2d6 "
                    "tulivahinkoa."),
            Feature("Legendaarinen: Kirveenheitto",
                    "Legendaarinen toiminto (1): yksi Warp Axe -heitto "
                    "40 ft (siirtyy mukana osuessaan).",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Liekkien purkaus",
                    "Legendaarinen toiminto (2): 15 ft kartio, DC 18 DEX "
                    "tai 4d12 tulivahinkoa (puolet onnistuneella).",
                    feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=2,
        lore="Epäkuollut punaisen lohikäärmeen ja minotauruksen risteytys, "
             "Corvus Spelchrumin toinen erikoisvartija. Kirves palaa "
             "ikuisessa tulessa ja se voi teleportata iskunsa mukana.",
        tactics="Aloittaa Warp Axe -heitolla kaukaiseen loitsijaan ja "
                "teleporttaa hänen viereensä. ENRAGE polttaa kaikki "
                "lähitaistelijat automaattisesti ja antaa kolme iskua — "
                "laavalammikot estävät lähestymisen. Legendaariset "
                "kirveenheitot pitävät painetta joka kierros.",
        habitat="Corvus Spelchrum", challenge_rating=16.0, xp=15000,
        proficiency_bonus=5),

    # ================================================================= #
    # RAVENSTONEN VAMPYYRIHOVI
    # ================================================================= #
    CreatureStats(
        name="Paroni Jugorai Millwind", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Lawful Evil", armor_class=17,
        armor_type="Natural Armor + Mage Armor", hit_points=180,
        hit_dice="20d8+90", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=16, dexterity=18, constitution=18,
                                intelligence=20, wisdom=16, charisma=18),
        saving_throws={"Dexterity": 9, "Intelligence": 10, "Wisdom": 8,
                       "Charisma": 9},
        skills={"Arcana": 15, "Deception": 9, "Persuasion": 9,
                "Perception": 8, "Insight": 8},
        senses="Darkvision 120 ft., Passive Perception 18",
        languages="Common, Elvish, Abyssal",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        spellcasting_ability="Intelligence", spell_save_dc=18,
        spell_attack_bonus=10,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2,
                     "6th": 1},
        spell_names=["Shield", "Magic Missile", "Mirror Image", "Hold Person",
                     "Counterspell", "Fireball", "Animate Dead", "Blight",
                     "Greater Invisibility", "Cloudkill", "Dominate Person"],
        cantrip_names=["Toll the Dead", "Ray of Frost", "Mage Hand"],
        actions=[
            Action("Multiattack", "x2 (Unarmed Strike tai loitsu)", 0, "", 0,
                   "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Draining Touch", "Draining Touch"]),
            Action("Draining Touch", "Melee (+ necrotic; paranee saman "
                   "verran)", 10, "1d8+3d6", 4, "necrotic", range=5),
            Action("Command Undead",
                   "60 ft: yksi epäkuollut (CR 8 tai alle) tekee DC 18 CHA "
                   "-pelastuksen tai siirtyy Jugorain hallintaan 1 tunniksi",
                   0, "", 0, "", range=60, applies_condition="Charmed",
                   condition_save="Charisma", condition_dc=18),
        ],
        features=[
            Feature("Legendary Resistance", "2/päivä: onnistu "
                    "epäonnistuneessa pelastusheitossa.",
                    feature_type="passive", uses_per_day=2),
            Feature("Regeneration", "Palauttaa 15 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="15"),
            Feature("Master of the Dead", "Hänen hallitsemansa epäkuolleet "
                    "saavat +2 osumaheittoihin ja +5 HP per Hit Die."),
            Feature("Usurper's Ambition", "Hän kerää Dimeriuksen voimaa: "
                    "kun Dimeriukselle uskollinen vampyyri kuolee 60 ft "
                    "säteellä, Jugorai saa 20 tilapäistä HP."),
            Feature("Misty Escape", "0 HP:ssä muuttuu sumuksi ja pakenee "
                    "kaupungintaloonsa.", feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen; ei ylitä kynnystä ilman kutsua."),
            Feature("Legendaarinen: Loitsu",
                    "Legendaarinen toiminto (2): heittää cantripin tai "
                    "1. tason loitsun.", feature_type="legendary",
                    legendary_cost=2),
            Feature("Legendaarinen: Käsky",
                    "Legendaarinen toiminto (1): yksi hallittu epäkuollut "
                    "hyökkää välittömästi.", feature_type="legendary",
                    legendary_cost=1),
        ],
        legendary_action_count=3, legendary_resistance_count=2,
        lore="Ravenstonen nimellinen ihmisjohtaja ja vampyyriloitsija. "
             "Vahva maagi, joka kykenee hallitsemaan muita epäkuolleita ja "
             "yrittää omia Dimeriuksen voimat itselleen — kaupungin "
             "vampyyrien sisällissodan toinen osapuoli.",
        tactics="Pysyy kaukana ja komentaa: Animate Dead ja Command Undead "
                "tuovat rivit, Cloudkill ja Fireball hoitavat ryhmät. "
                "Dominate Person kääntää pelaajan. Legendaariset käskyt "
                "antavat epäkuolleille ylimääräisiä hyökkäyksiä joka "
                "kierros.",
        habitat="Ravenstone", challenge_rating=15.0, xp=13000,
        proficiency_bonus=5),

    CreatureStats(
        name="Polsen", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil",
        armor_class=19, armor_type="Natural Armor + Vampyyrilordin panssari",
        hit_points=210, hit_dice="20d8+120", speed=40, climb_speed=40,
        abilities=AbilityScores(strength=22, dexterity=18, constitution=20,
                                intelligence=18, wisdom=17, charisma=18),
        saving_throws={"Strength": 12, "Dexterity": 10, "Constitution": 11,
                       "Wisdom": 9},
        skills={"Athletics": 12, "Perception": 9, "Stealth": 10,
                "Insight": 9, "History": 10, "Intimidation": 10},
        senses="Darkvision 120 ft., Passive Perception 19",
        languages="Common, Elvish, Dwarvish, Abyssal",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened"],
        actions=[
            Action("Multiattack", "x3 (Warlord's Blade / Life Drain)", 0, "",
                   0, "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Warlord's Blade", "Warlord's Blade",
                                        "Life Drain"]),
            Action("Warlord's Blade", "Melee (muinainen miekka)", 12,
                   "1d10+2d8", 6, "slashing", range=5),
            Action("Life Drain", "Melee (paranee vahingon verran)", 12,
                   "2d10", 6, "necrotic", range=5),
            Action("Tactical Command",
                   "Bonustoiminto: kaksi liittolaista 60 ft sisällä saavat "
                   "välittömästi liikkeen ja yhden hyökkäyksen reaktiona",
                   0, "", 0, "", range=60, action_type="bonus"),
        ],
        features=[
            Feature("Legendary Resistance", "3/päivä.",
                    feature_type="passive", uses_per_day=3),
            Feature("Regeneration", "Palauttaa 20 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="20"),
            Feature("Master Strategist", "Etu aloiteheittoon; hän ja "
                    "liittolaiset 30 ft säteellä eivät voi olla "
                    "yllätettyjä.", mechanic="feral_instinct"),
            Feature("Vampyyrijoukon herra", "Johtaa laajaa vampyyriryhmää: "
                    "liittolaiset 60 ft säteellä saavat +3 osumaheittoihin "
                    "ja etua pelastusheittoihin pelkoa vastaan.",
                    aura_radius=60),
            Feature("Parry", "Reaktio: +4 AC yhtä melee-iskua vastaan.",
                    feature_type="reaction"),
            Feature("Misty Escape", "0 HP:ssä pakenee sumuna leposijalleen.",
                    feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
            Feature("Legendaarinen: Isku", "Legendaarinen toiminto (1): "
                    "yksi Warlord's Blade.", feature_type="legendary",
                    legendary_cost=1),
            Feature("Legendaarinen: Marssi", "Legendaarinen toiminto (1): "
                    "Polsen ja kaksi liittolaista liikkuvat 30 ft "
                    "provosoimatta.", feature_type="legendary",
                    legendary_cost=1),
            Feature("Legendaarinen: Verikilpi",
                    "Legendaarinen toiminto (2): Polsen puolittaa yhden "
                    "liittolaiseensa kohdistuvan vahingon ja ottaa loput "
                    "itse.", feature_type="legendary", legendary_cost=2),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Muinainen vampyyrilordi — erittäin voimakas taistelija ja "
             "strategisti. Johtaa laajaa vampyyriryhmää ja valvoo "
             "kaupunkia varjoista. Neuvonantajanaan muinainen vampyyri "
             "Beatrice (eri henkilö kuin pelaajahahmo).",
        tactics="Taistelee etulinjassa mutta ei yksin: Tactical Command ja "
                "legendaarinen Marssi liikuttavat koko vampyyrijoukkoa, "
                "Verikilpi pitää neuvonantajansa hengissä. Kolme iskua "
                "vuorossa + legendaariset tekevät hänestä jatkuvan uhan.",
        habitat="Ravenstone", challenge_rating=16.0, xp=15000,
        proficiency_bonus=5),

    CreatureStats(
        name="Beatrice Rask (vampyyri)", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Neutral Evil", armor_class=18,
        armor_type="Natural Armor", hit_points=157, hit_dice="18d8+72",
        speed=60, climb_speed=60,
        abilities=AbilityScores(strength=16, dexterity=22, constitution=18,
                                intelligence=17, wisdom=16, charisma=20),
        saving_throws={"Dexterity": 12, "Wisdom": 9, "Charisma": 11},
        skills={"Stealth": 17, "Acrobatics": 12, "Deception": 11,
                "Insight": 9, "Perception": 9},
        senses="Darkvision 120 ft., Passive Perception 19",
        languages="Common, Elvish",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        spellcasting_ability="Charisma", spell_save_dc=19,
        spell_attack_bonus=11,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
        spell_names=["Hold Person", "Darkness", "Greater Invisibility",
                     "Dominate Person", "Counterspell"],
        cantrip_names=["Mind Sliver", "Toll the Dead"],
        actions=[
            Action("Multiattack", "x3 Blurred Claws", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Blurred Claws", "Blurred Claws",
                                        "Life Drain Bite"]),
            Action("Blurred Claws", "Melee (uskomaton nopeus)", 12,
                   "2d6+2d6", 6, "slashing", range=5),
            Action("Life Drain Bite", "Melee (paranee vahingon verran)", 12,
                   "1d6+3d6", 6, "necrotic", range=5),
            Action("Mind Twist",
                   "60 ft (DC 19 WIS tai 6d8 psychic ja kohde hyökkää "
                   "liittolaistaan seuraavalla vuorollaan)", 0, "6d8", 0,
                   "psychic", range=60, applies_condition="Charmed",
                   condition_save="Wisdom", condition_dc=19),
        ],
        features=[
            Feature("Blinding Speed", "Nopeus 60 ft; hän voi käyttää Dash- "
                    "ja Disengage-toiminnot samalla bonustoiminnolla, ja "
                    "hyökkäykset häntä vastaan ovat disadvantagella jos hän "
                    "liikkui yli 30 ft tällä vuorolla."),
            Feature("Mind Manipulation", "Etu kaikkiin Charmed-tilaa "
                    "aiheuttaviin heittoihin; hallitsemansa kohde ei saa "
                    "uutta pelastusheittoa vahingosta."),
            Feature("Regeneration", "Palauttaa 15 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="15"),
            Feature("Uncanny Dodge", "Reaktio: puolita yhden osuman "
                    "vahinko.", feature_type="reaction",
                    mechanic="uncanny_dodge"),
            Feature("Misty Escape", "0 HP:ssä pakenee sumuna.",
                    feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
        ],
        lore="Kadonnut leipurin tytär, joka on nykyisin Polsenin "
             "neuvonantaja. Muinainen vampyyri, erittäin nopea ja kykenee "
             "manipuloimaan mieliä. HUOM: eri henkilö kuin pelaajahahmo "
             "Beatrice — tämä on Ravenstonen vampyyri.",
        tactics="Iskee ensin ja poistuu: Blinding Speed antaa 60 ft "
                "liikkeen ja disadvantagen häntä vastaan. Mind Twist "
                "kääntää ryhmän jäsenen toisiaan vastaan, sitten kolme "
                "kynsi-iskua eristettyyn kohteeseen.",
        habitat="Ravenstone", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5),

    CreatureStats(
        name="Vilan Norgrad", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Lawful Evil", armor_class=17,
        armor_type="Natural Armor", hit_points=150, hit_dice="17d8+68",
        speed=40, climb_speed=40,
        abilities=AbilityScores(strength=18, dexterity=18, constitution=18,
                                intelligence=15, wisdom=16, charisma=17),
        saving_throws={"Dexterity": 8, "Wisdom": 7, "Charisma": 7},
        skills={"Perception": 7, "Stealth": 8, "Intimidation": 7},
        senses="Darkvision 120 ft., Passive Perception 17",
        languages="Common, Goblin",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        actions=[
            Action("Multiattack", "x2 Claws + Life Drain", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Claws", "Claws", "Life Drain"]),
            Action("Claws", "Melee", 8, "2d6+2d6", 4, "slashing", range=5),
            Action("Life Drain", "Melee (paranee vahingon verran)", 8,
                   "2d10", 4, "necrotic", range=5),
        ],
        features=[
            Feature("Regeneration", "Palauttaa 15 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="15"),
            Feature("Loyal to the Founder", "Kun Dimerius on 60 ft "
                    "säteellä, Vilan saa +2 osumaheittoihin ja etua "
                    "pelastusheittoihin."),
            Feature("Anti-Usurper", "Etu hyökkäyksiin Jugorain joukkoja "
                    "vastaan."),
            Feature("Misty Escape", "0 HP:ssä pakenee sumuna.",
                    feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
        ],
        lore="Yli 350-vuotias vampyyri, Dimeriukselle äärimmäisen "
             "uskollinen. Taistelee paroni Jugorain aikeita vastaan. "
             "Kreivitär Vila Norgradin sukua.",
        tactics="Taistelee Dimeriuksen lähellä bonusten vuoksi; kohdistaa "
                "iskut Jugorain joukkoihin.",
        habitat="Ravenstone", challenge_rating=11.0, xp=7200,
        proficiency_bonus=4),

    CreatureStats(
        name="Herold Reggefoi", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Lawful Evil", armor_class=18,
        armor_type="Natural Armor", hit_points=172, hit_dice="18d8+90",
        speed=40, climb_speed=40,
        abilities=AbilityScores(strength=20, dexterity=18, constitution=20,
                                intelligence=16, wisdom=18, charisma=18),
        saving_throws={"Dexterity": 9, "Constitution": 10, "Wisdom": 9},
        skills={"Perception": 9, "Stealth": 9, "History": 8,
                "Intimidation": 9},
        senses="Darkvision 120 ft., Passive Perception 19",
        languages="Common, Goblin, Elvish, Abyssal",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion", "Frightened"],
        actions=[
            Action("Multiattack", "x3 (Ancient Claws / Life Drain)", 0, "",
                   0, "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Ancient Claws", "Ancient Claws",
                                        "Life Drain"]),
            Action("Ancient Claws", "Melee", 10, "2d8+3d6", 5, "slashing",
                   range=5),
            Action("Life Drain", "Melee (paranee vahingon verran)", 10,
                   "3d10", 5, "necrotic", range=5),
            Action("Elder's Gaze",
                   "30 ft (DC 18 WIS tai Paralyzed 1 min; save vuoron "
                   "lopussa)", 0, "", 0, "", range=30,
                   applies_condition="Paralyzed", condition_save="Wisdom",
                   condition_dc=18),
        ],
        features=[
            Feature("Legendary Resistance", "2/päivä.",
                    feature_type="passive", uses_per_day=2),
            Feature("Regeneration", "Palauttaa 20 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="20"),
            Feature("Eight Centuries", "Yli 800 vuotta vanha: etua "
                    "kaikkiin Wisdom- ja Charisma-pelastusheittoihin ja "
                    "immuuni tavalliseen mielenhallintaan."),
            Feature("Loyal to the Founder", "Dimeriuksen lähellä (60 ft) "
                    "+2 osumaheittoihin."),
            Feature("Misty Escape", "0 HP:ssä pakenee sumuna.",
                    feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
            Feature("Legendaarinen: Purenta",
                    "Legendaarinen toiminto (1): yksi Life Drain.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Katse",
                    "Legendaarinen toiminto (2): Elder's Gaze yhteen "
                    "kohteeseen.", feature_type="legendary",
                    legendary_cost=2),
        ],
        legendary_action_count=2, legendary_resistance_count=2,
        lore="Yli 800-vuotias vampyyri ja Dimeriuksen vanhin uskollinen. "
             "Taistelee paroni Jugorain vallankaappausta vastaan.",
        tactics="Elder's Gaze halvaannuttaa kovimman iskijän (auto-kriitit "
                "liittolaisille), sitten kolme iskua. Legendaariset katseet "
                "pitävät useamman pelaajan lukossa.",
        habitat="Ravenstone", challenge_rating=14.0, xp=11500,
        proficiency_bonus=5),

    CreatureStats(
        name="Davos Wolfbane", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil", armor_class=16,
        armor_type="Studded Leather", hit_points=112, hit_dice="15d8+45",
        speed=40, climb_speed=40,
        abilities=AbilityScores(strength=18, dexterity=18, constitution=16,
                                intelligence=11, wisdom=13, charisma=14),
        saving_throws={"Dexterity": 7, "Constitution": 6},
        skills={"Athletics": 7, "Perception": 5, "Stealth": 7},
        senses="Darkvision 120 ft., Passive Perception 15",
        languages="Common",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        actions=[
            Action("Multiattack", "x2 Wolfbane Axe + Life Drain", 0, "", 0,
                   "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Wolfbane Axe", "Wolfbane Axe",
                                        "Life Drain"]),
            Action("Wolfbane Axe", "Melee (suvun kirves)", 7, "1d12+1d6", 4,
                   "slashing", range=5, properties=["heavy"]),
            Action("Life Drain", "Melee (paranee vahingon verran)", 7,
                   "2d8", 4, "necrotic", range=5),
        ],
        features=[
            Feature("Regeneration", "Palauttaa 10 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="10"),
            Feature("Enslaved Will", "Polsenin joukoissa tai Jugorain "
                    "orjuudessa: hänen isäntänsä voi käyttää reaktionsa "
                    "antaakseen Davosille yhden ylimääräisen hyökkäyksen."),
            Feature("Brother's Sorrow", "Jos Aksel Wolfbane on näkyvissä, "
                    "Davos tekee kaikki hyökkäyksensä disadvantagella "
                    "Akselia vastaan — hän vastustaa käskyä."),
            Feature("Misty Escape", "0 HP:ssä pakenee sumuna.",
                    feature_type="passive"),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
        ],
        lore="Vampyyrisoturi, joka on joutunut Polsenin joukkoihin tai "
             "Jugorain orjuuteen. Vampyyrinmetsästäjä Aksel Wolfbanen oma "
             "veli — traaginen kohtaaminen odottaa.",
        tactics="Hyökkää kirveellä ja imee elinvoimaa, mutta epäröi "
                "veljeään vastaan (disadvantage Akselia vastaan).",
        habitat="Ravenstone", challenge_rating=8.0, xp=3900,
        proficiency_bonus=4),

    # ================================================================= #
    # KAUPUNGIN KESKEISET HAHMOT (elävät)
    # ================================================================= #
    CreatureStats(
        name="Aksel Wolfbane", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Neutral Good", armor_class=17,
        armor_type="Studded Leather + suojakaapu", hit_points=105,
        hit_dice="14d8+42", speed=30,
        abilities=AbilityScores(strength=16, dexterity=18, constitution=16,
                                intelligence=13, wisdom=16, charisma=12),
        saving_throws={"Dexterity": 8, "Wisdom": 7},
        skills={"Survival": 7, "Perception": 11, "Stealth": 8,
                "Investigation": 5, "Religion": 4},
        senses="Passive Perception 21", languages="Common, Elvish",
        actions=[
            Action("Multiattack", "x2 Hopeakirves tai varsijousi", 0, "", 0,
                   "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Hopeakirves", "Hopeakirves"]),
            Action("Hopeakirves",
                   "Melee (hopea: läpäisee vampyyrin resistanssin; "
                   "+2d6 epäkuolleisiin)", 8, "1d12+2d6", 4, "slashing",
                   range=5, properties=["heavy"]),
            Action("Raskas kuvioitu varsijousi",
                   "Ranged (hopeanuolet; +2d6 epäkuolleisiin)", 8,
                   "1d10+2d6", 4, "piercing", range=100, long_range=400,
                   properties=["heavy", "two-handed", "loading"]),
            Action("Vaarna sydämeen",
                   "Melee lamaantunutta/prone-vampyyria vastaan: 6d10 "
                   "piercing ja vampyyri lamaantuu (ei Misty Escapea "
                   "tällä kierroksella)", 8, "6d10", 4, "piercing",
                   range=5),
        ],
        features=[
            Feature("Vampyyrinmetsästäjä", "Hopea-aseet läpäisevät "
                    "vampyyrien ei-maagisen fyysisen resistanssin ja "
                    "tekevät +2d6 vahinkoa epäkuolleisiin."),
            Feature("Erikoisjuoma (vastalääke)",
                    "Kantaa 3 annosta juomaa, joka ESTÄÄ vampyyriksi "
                    "muuttumisen, jos se nautitaan kahden tunnin sisällä "
                    "puremasta.", uses_per_day=3),
            Feature("Uncanny Dodge", "Reaktio: puolita yhden osuman "
                    "vahinko.", feature_type="reaction",
                    mechanic="uncanny_dodge"),
            Feature("Hunter's Mark", "Bonustoiminto: merkitse kohde, +1d6 "
                    "vahinkoa osumista.", mechanic="hunters_mark",
                    mechanic_value="1d6"),
            Feature("Veljen taakka", "Davos Wolfbane on hänen veljensä — "
                    "Aksel ei voi vahingossa tappaa häntä (DM: hän etsii "
                    "keinoa pelastaa Davos)."),
        ],
        lore="Vampyyrinmetsästäjä, joka piileskelee Cora 0:n "
             "(Profunduksen) tiloissa. Kantaa hopeakirvestä, raskasta "
             "kuvioitua varsijousta ja hopeanuolia. Hänellä on "
             "erikoisjuoma, joka estää vampyyriksi muuttumisen jos se "
             "nautitaan kahden tunnin sisällä puremasta. Veljensä Davos "
             "on joutunut vampyyriksi.",
        tactics="Merkitsee kohteen, ampuu hopeanuolilla etäältä ja "
                "vaihtaa kirveeseen lähitaistelussa. Säästää vaarnan "
                "hetkeen jolloin vampyyri on lamaantunut — se estää "
                "Misty Escapen.",
        habitat="Ravenstone / Profundus", challenge_rating=9.0, xp=5000,
        proficiency_bonus=4),

    CreatureStats(
        name="Lidian Stramroot", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Neutral", armor_class=15,
        armor_type="Rohtokauppiaan kaapu", hit_points=88,
        hit_dice="12d8+36", speed=30,
        abilities=AbilityScores(strength=10, dexterity=14, constitution=16,
                                intelligence=18, wisdom=22, charisma=16),
        saving_throws={"Wisdom": 11, "Intelligence": 9},
        skills={"Medicine": 15, "Nature": 9, "Insight": 15, "Arcana": 9,
                "Perception": 11},
        senses="Truesight 30 ft. (kultaiset silmät), Passive Perception 21",
        languages="Common, Elvish, Sylvan, Mens",
        spellcasting_ability="Wisdom", spell_save_dc=19,
        spell_attack_bonus=11,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
        spell_names=["Cure Wounds", "Lesser Restoration", "Healing Word",
                     "Dispel Magic", "Blight", "Hold Person"],
        cantrip_names=["Guidance", "Toll the Dead"],
        actions=[
            Action("Rohtokauppiaan sauva", "Melee", 6, "1d6", 2,
                   "bludgeoning", range=5),
            Action("Muuta: anna tai ota tietoa",
                   "At Will (3/päivä): yksi olento 30 ft tekee DC 22 WIS "
                   "-pelastuksen. Epäonnistuessa Lidian joko ANTAA sille "
                   "yhden totuuden (kohde ei voi olla uskomatta) tai OTTAA "
                   "siltä yhden muiston/tiedon, jonka kohde menettää "
                   "1 tunniksi.", 0, "", 0, "", range=30,
                   condition_save="Wisdom", condition_dc=22),
        ],
        features=[
            Feature("Muuta: anna tai ota tietoa",
                    "At Will, DC 22 WIS, 3 kertaa päivässä. Äitinsä "
                    "voimakas perimä.", uses_per_day=3,
                    save_dc=22, save_ability="Wisdom"),
            Feature("Kultaiset silmät", "Mystiset kultaiset silmät antavat "
                    "Truesight 30 ft — näkee illuusiot, naamiot ja "
                    "muodonmuuttajat (myös vampyyrin sumumuodon)."),
            Feature("Mestariherbalisti", "Voi valmistaa antitoksiineja, "
                    "parannusjuomia ja vampyyrin vastalääkettä; etua "
                    "Medicine-heittoihin."),
            Feature("Mens-perimä", "Immuuni sairauksille ja etua "
                    "pelastusheittoihin mielenhallintaa vastaan."),
        ],
        lore="31-vuotias Mens-alkuperäisrotuinen rohtokauppias, jolla on "
             "mystiset kultaiset silmät. Kantaa äitinsä voimakasta "
             "perimää ja osaa loihtia 'muuta: anna tai ota tietoa' "
             "-kyvyn (At Will, WIS DC 22) kolme kertaa päivässä.",
        tactics="Ei taistelija: käyttää tiedonvaihtokykyään "
                "neuvottelussa ja parantaa ryhmää. Kultaiset silmät "
                "paljastavat naamioidut vampyyrit.",
        habitat="Ravenstone", challenge_rating=6.0, xp=2300,
        proficiency_bonus=4),

    CreatureStats(
        name="Greg Silverhand", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Chaotic Neutral",
        armor_class=13, armor_type="Laboratoriotakki", hit_points=66,
        hit_dice="12d8+12", speed=30,
        abilities=AbilityScores(strength=9, dexterity=12, constitution=12,
                                intelligence=20, wisdom=14, charisma=11),
        saving_throws={"Intelligence": 8, "Wisdom": 5},
        skills={"Medicine": 9, "Arcana": 8, "Nature": 8,
                "Investigation": 12, "Insight": 5},
        senses="Passive Perception 12", languages="Common, Elvish",
        actions=[
            Action("Kirurginveitsi", "Melee", 4, "1d4", 1, "piercing",
                   range=5),
            Action("Rauhoittava ruisku",
                   "Melee (DC 15 CON tai Unconscious 1 min; herää "
                   "vahingosta)", 4, "2d6", 1, "poison", range=5,
                   applies_condition="Unconscious",
                   condition_save="Constitution", condition_dc=15),
            Action("Kokeellinen seerumi",
                   "30 ft (DC 15 CON tai 4d6 psychic ja Confused: kohde "
                   "hyökkää satunnaista kohdetta seuraavalla vuorollaan)",
                   0, "4d6", 0, "psychic", range=30,
                   condition_save="Constitution", condition_dc=15),
        ],
        features=[
            Feature("Aivotutkimuksen asiantuntija",
                    "Tietää tarkalleen miten mieli murtuu: etua "
                    "Insight-heittoihin ja hän voi tunnistaa "
                    "mielenhallinnan tai sielunsirpaleen tutkimalla "
                    "kohdetta 1 minuutin."),
            Feature("Taitava herbalisti", "Valmistaa myrkkyjä, seerumeita "
                    "ja rauhoittavia aineita; etua Medicine- ja "
                    "Nature-heittoihin."),
            Feature("Vapiseva hullu", "Disadvantage aloiteheittoon ja "
                    "hienomotoriikkaan; hän on fyysisesti heikko mutta "
                    "hänen laitoksensa on täynnä potilaita ja vartijoita."),
            Feature("Asylum Purgon johtaja", "Voi kutsua 1d4 vartijaa tai "
                    "2d4 'potilasta' bonustoiminnolla laitoksessaan.",
                    feature_type="bonus"),
        ],
        lore="Asylum Purgon johtaja. 48-vuotias hullu professori, "
             "aivotutkimuksen asiantuntija ja taitava herbalisti. "
             "Vapiseva, valkohiuksinen, ja hänen toista silmää halkoo "
             "arpi.",
        tactics="Ei taistele itse: kutsuu vartijat ja potilaat, "
                "ruiskuttaa rauhoittavaa lähelle päässeisiin ja heittää "
                "kokeellisia seerumeita. Pakenee laboratorioonsa.",
        habitat="Asylum Purgo (Ravenstone)", challenge_rating=4.0, xp=1100,
        proficiency_bonus=3),

    CreatureStats(
        name="Gaur Rakek", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral", armor_class=17,
        armor_type="Studded Leather", hit_points=126, hit_dice="16d8+48",
        speed=40, climb_speed=30,
        abilities=AbilityScores(strength=14, dexterity=20, constitution=16,
                                intelligence=18, wisdom=16, charisma=18),
        saving_throws={"Dexterity": 9, "Intelligence": 8, "Charisma": 8},
        skills={"Deception": 12, "Insight": 11, "Perception": 11,
                "Stealth": 13, "Persuasion": 12, "Investigation": 8},
        senses="Darkvision 60 ft., Passive Perception 21",
        languages="Common, Undercommon, Elvish, Thieves' Cant",
        actions=[
            Action("Multiattack", "x3 Syndikaatin tikari", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Syndikaatin tikari",
                                        "Syndikaatin tikari",
                                        "Syndikaatin tikari"]),
            Action("Syndikaatin tikari",
                   "Melee/Thrown (myrkytetty: DC 15 CON tai Poisoned)", 9,
                   "1d4+3d6", 5, "piercing", range=20, long_range=60,
                   applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=15,
                   properties=["finesse", "light", "thrown"]),
            Action("Mark for Death",
                   "Bonustoiminto: nimeä kohde — kaikki Cora 0:n jäsenet "
                   "saavat etua hyökkäyksiin sitä vastaan taistelun "
                   "loppuun", 0, "", 0, "", range=60, action_type="bonus"),
        ],
        features=[
            Feature("Sneak Attack (1/turn)", "+4d6 vahinkoa kun hänellä on "
                    "etu tai liittolainen on 5 ft kohteesta.",
                    mechanic="sneak_attack", mechanic_value="4d6"),
            Feature("Cunning Action", "Bonustoiminto: Dash, Disengage tai "
                    "Hide.", mechanic="cunning_action"),
            Feature("Evasion", "DEX-pelastuksella puolet vahingosta: "
                    "onnistuessa ei mitään.", mechanic="evasion"),
            Feature("Uncanny Dodge", "Reaktio: puolita osuman vahinko.",
                    feature_type="reaction", mechanic="uncanny_dodge"),
            Feature("Drow-sopimus", "Voi kutsua 2 Velve Dro -soturia "
                    "lihasvoimaksi (1/päivä); Cora 0 maksaa heille "
                    "yöllisistä uhista.", uses_per_day=1),
            Feature("Tabaxi Feline Agility", "Kaksinkertaistaa nopeutensa "
                    "kierroksen ajan; ei uudelleen ennen kuin liikkuu 0 ft "
                    "yhdellä vuorolla."),
        ],
        lore="Tabaxi, joka johtaa alamaailman syndikaatti Cora 0:aa "
             "Profunduksessa. Strateginen ja laskelmoiva johtaja, joka "
             "tekee kauppaa drowien kanssa käyttääkseen näitä "
             "lihasvoimana yöllisiä uhkia (vampyyreja) vastaan.",
        tactics="Ei taistele reilusti: Hide, Sneak Attack, Mark for Death "
                "ja poistuu Cunning Actionilla. Kutsuu drow-soturit "
                "hoitamaan raskaan työn.",
        habitat="Profundus (Ravenstone)", challenge_rating=8.0, xp=3900,
        proficiency_bonus=4),

    CreatureStats(
        name="Jivin Lukom", size="Small", creature_type="Humanoid",
        native_plane="Material", alignment="Chaotic Good", armor_class=14,
        armor_type="Leather", hit_points=52, hit_dice="9d6+18", speed=25,
        abilities=AbilityScores(strength=8, dexterity=16, constitution=14,
                                intelligence=20, wisdom=15, charisma=14),
        saving_throws={"Intelligence": 8, "Dexterity": 6},
        skills={"Investigation": 12, "History": 12, "Arcana": 8,
                "Stealth": 9, "Insight": 6, "Deception": 6},
        senses="Darkvision 60 ft., Passive Perception 16",
        languages="Common, Gnomish, Undercommon, Elvish, Thieves' Cant",
        actions=[
            Action("Tikari", "Melee/Thrown", 6, "1d4", 3, "piercing",
                   range=20, long_range=60,
                   properties=["finesse", "light", "thrown"]),
            Action("Paljasta salaisuus",
                   "Toiminto: nimeä yksi olento jonka Jivin on tutkinut — "
                   "kaikki liittolaiset saavat etua sitä vastaan yhden "
                   "kierroksen (hän tietää sen heikkoudet)", 0, "", 0, "",
                   range=60),
        ],
        features=[
            Feature("Kaupungin muisti", "Tietää Ravenstonen todelliset "
                    "valtasuhteet: voi kertoa kenen palveluksessa kukin "
                    "todella on, ja etua kaikkiin History- ja "
                    "Investigation-heittoihin kaupungista."),
            Feature("Cora 0:n vakooja", "Etua Stealth- ja "
                    "Deception-heittoihin; hänellä on turvallinen reitti "
                    "Profundukseen."),
            Feature("Gnomen viekkaus", "Etua INT-, WIS- ja CHA-"
                    "pelastusheittoihin taikaa vastaan."),
            Feature("Ei taistelija", "Pakenee ensimmäisessä "
                    "tilaisuudessa; arvo on tiedossa, ei aseissa."),
        ],
        lore="Kirjastonhoitaja (gnomi) ja Cora 0:n vakoilija. Älykäs ja "
             "hyvin tietoinen kaupungin todellisista valtasuhteista ja "
             "tapahtumista — paras tiedonlähde Ravenstonessa.",
        tactics="Ei taistele: kertoo tietoa, paljastaa heikkoudet ja "
                "pakenee. Arvokkaampi liittolaisena kuin vihollisena.",
        habitat="Ravenstone", challenge_rating=2.0, xp=450,
        proficiency_bonus=2),

    CreatureStats(
        name="Fior Rask", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil", armor_class=15,
        armor_type="Natural Armor", hit_points=82, hit_dice="11d8+33",
        speed=40, climb_speed=30,
        abilities=AbilityScores(strength=16, dexterity=16, constitution=16,
                                intelligence=11, wisdom=10, charisma=14),
        saving_throws={"Dexterity": 5},
        skills={"Perception": 3, "Stealth": 5, "Deception": 4},
        senses="Darkvision 60 ft., Passive Perception 13",
        languages="Common",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        actions=[
            Action("Multiattack", "Claws + Life Drain Bite", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Claws", "Life Drain Bite"]),
            Action("Claws", "Melee", 5, "2d4", 3, "slashing", range=5),
            Action("Life Drain Bite", "Melee (paranee vahingon verran)", 5,
                   "1d6+2d6", 3, "necrotic", range=5),
        ],
        features=[
            Feature("Regeneration", "Palauttaa 10 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="10"),
            Feature("Tuore vampyyri", "Muutettu vasta hiljattain: hän "
                    "muistaa vielä ihmiselämänsä ja voi epäröidä "
                    "(DM: mahdollinen pelastettava)."),
            Feature("Majatalon tytär", "Tuntee majatalon salakäytävät ja "
                    "asiakkaat; etua Stealth-heittoihin siellä."),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
        ],
        lore="Majatalon pitäjän tytär, joka on muutettu vampyyriksi. "
             "Muistaa vielä ihmiselämänsä — mahdollisesti pelastettavissa "
             "Akselin vastalääkkeellä jos purema on tuore.",
        tactics="Vaanii majatalon käytävillä; iskee yksinäisiin.",
        habitat="Ravenstone", challenge_rating=5.0, xp=1800,
        proficiency_bonus=3),

    CreatureStats(
        name="Zemok Retana", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil", armor_class=16,
        armor_type="Natural Armor", hit_points=90, hit_dice="12d8+36",
        speed=50, climb_speed=40,
        abilities=AbilityScores(strength=15, dexterity=20, constitution=16,
                                intelligence=13, wisdom=12, charisma=15),
        saving_throws={"Dexterity": 8},
        skills={"Perception": 4, "Stealth": 11, "Deception": 5,
                "Persuasion": 5, "Acrobatics": 8},
        senses="Darkvision 60 ft., Passive Perception 14",
        languages="Common, Undercommon",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Charmed", "Exhaustion"],
        actions=[
            Action("Multiattack", "x2 Claws + Life Drain Bite", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Claws", "Claws", "Life Drain Bite"]),
            Action("Claws", "Melee (tabaxi-kynnet)", 8, "1d6+1d6", 5,
                   "slashing", range=5),
            Action("Life Drain Bite", "Melee (paranee vahingon verran)", 8,
                   "1d6+2d6", 5, "necrotic", range=5),
        ],
        features=[
            Feature("Regeneration", "Palauttaa 10 HP vuoronsa alussa, ellei "
                    "ottanut radiant-vahinkoa.", mechanic="regeneration",
                    mechanic_value="10"),
            Feature("Feline Agility (vampyyri)", "Kaksinkertaistaa "
                    "nopeutensa (50 → 100 ft) kierroksen ajan."),
            Feature("Kauppiaan verkosto", "Tuntee kaikki kaupungin "
                    "salakuljetusreitit; etua Deception- ja "
                    "Persuasion-heittoihin kaupankäynnissä."),
            Feature("Vampire Weaknesses", "Auringonvalo, juokseva vesi, "
                    "vaarna sydämeen."),
        ],
        lore="Tabaxi-kauppias, joka on muutettu vampyyriksi. Käyttää "
             "kauppaverkostoaan nyt vampyyrien hyväksi.",
        tactics="Erittäin nopea (100 ft Feline Agilityllä): iskee ja "
                "katoaa, eristää yksittäisiä kohteita.",
        habitat="Ravenstone", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3),
]
