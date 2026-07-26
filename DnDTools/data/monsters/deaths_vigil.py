"""Death's Vigil — Kuoleman Vartio (Pinwud, Tarmaas).

Mortem Aeternusta palvelevan pappis- ja sotilasjärjestön pelattavat
stat blockit: kolmen hengen ylin johto (Senatorum), Puhdistajat
(Purificatores) ja Sielun Parantajat (Medici Animae).

Lähdedata vs. täydennys:
  * **Gaius Marad** on lähteessä täydellisenä (HP 140, AC 20, kykyarvot,
    saving throwt, Channel Divinity: Path to the Grave, Eyes of the
    Grave, Sentinel at Death's Door, Keeper of Souls) — toteutettu
    sellaisenaan.
  * **Aurelia Valtar** on lähteessä vain "Paladin 14 / Fighter 6, taso
    20, tuplasmitet, maata järisyttävä raivo". Numerot on rakennettu
    tästä: Action Surge + Divine Smite -piikki, Aura of Protection,
    Improved Divine Smite ja maanjäristysisku.
  * **Thalgrum** on lähteessä ilman numeroita, mutta Padakin arvio on
    yksiselitteinen: "aivan eri tason uhka" kuin taso 15 ja 20 -johtajat.
    Siksi hän on rakennettu järjestön salaa vaarallisimmaksi: sielumagian
    arkkimestari legendaarisin toiminnoin ja Legendary Resistancella.
  * Rivijäsenet (kapteeni, puhdistaja, arkkiparantaja, parantaja) on
    rakennettu doktriinin *Tria Membra Mortis* ympärille.

Loitsijat viittaavat loitsuihin nimellä keskitetystä loitsukirjastosta
(``spell_names`` / ``cantrip_names``) — omia holdereita ei luoda.
Rider-vahingot on koottu moniosaisiin noppalausekkeisiin (esim.
``2d6+4d8``), joita moottorin noppaparseri tukee.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature


monsters = [
    # ================================================================= #
    # SENATORUM — ylin johto (3)
    # ================================================================= #

    # ---- Gaius Marad (lähdedata sellaisenaan) ---------------------- #
    CreatureStats(
        name="Gaius Marad", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=20, armor_type="Splint Armor + Shield",
        hit_points=140, hit_dice="15d8+60", speed=30,
        abilities=AbilityScores(strength=12, dexterity=12, constitution=18,
                                intelligence=14, wisdom=20, charisma=16),
        saving_throws={"Wisdom": 10, "Charisma": 8},
        skills={"Insight": 10, "Religion": 7, "Medicine": 10,
                "Persuasion": 8, "History": 7},
        senses="Passive Perception 15", languages="Common, Celestial",
        spellcasting_ability="Wisdom", spell_save_dc=18,
        spell_attack_bonus=10,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2,
                     "6th": 1, "7th": 1, "8th": 1},
        spell_names=["Bless", "Command", "Cure Wounds", "Healing Word",
                     "Guiding Bolt", "Spiritual Weapon", "Hold Person",
                     "Spirit Guardians", "Revivify", "Dispel Magic",
                     "Blight", "Death Ward", "Banishment", "Mass Cure Wounds",
                     "Harm"],
        cantrip_names=["Sacred Flame", "Toll the Dead", "Guidance"],
        actions=[
            Action("Multiattack", "x2 Mortem's Mace", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Mortem's Mace", "Mortem's Mace"]),
            Action("Mortem's Mace", "Melee (+ radiant)", 9, "1d8+2d8", 1,
                   "bludgeoning", range=5),
            Action("Path to the Grave",
                   "Channel Divinity: kiroa kohde 30 ft — seuraava osuma "
                   "siihen tekee TUPLAVAHINGON (2/päivä)", 0, "", 0, "",
                   range=30, action_type="action"),
        ],
        features=[
            Feature("Channel Divinity: Path to the Grave",
                    "1/kierros, 2/päivä: kiroa yksi kohde 30 ft säteellä. "
                    "Seuraava hyökkäys tähän kohteeseen (ennen Gaiuksen "
                    "seuraavaa vuoroa) tekee kaksinkertaisen vahingon.",
                    feature_type="class", uses_per_day=2,
                    mechanic="channel_divinity"),
            Feature("Eyes of the Grave",
                    "Tunnistaa kaikki epäkuolleet 60 ft säteellä, vaikka "
                    "ne olisivat piilossa.", feature_type="class"),
            Feature("Sentinel at Death's Door",
                    "Reaktio (5/kierros): estä kriittinen osuma keneen "
                    "tahansa näkökentässä — siitä tulee tavallinen osuma.",
                    feature_type="reaction", uses_per_day=5),
            Feature("Keeper of Souls",
                    "1/kierros: kun vihollinen kuolee 60 ft säteellä, "
                    "Gaius parantaa yhtä olentoa (enintään 15 HP).",
                    feature_type="passive"),
            Feature("Circle of Mortality",
                    "0 HP:ssä olevaan kohteeseen kohdistuvat "
                    "parannusloitsut antavat maksimiarvon.",
                    feature_type="class"),
            Feature("Spellcasting", "15. tason Grave Domain -cleric "
                    "(WIS, DC 18, +10 osumaan)."),
        ],
        lore="Death's Vigilin Magnus Custos — ylin hengellinen ja "
             "strateginen johtaja. Vaikuttaa lempeältä ja otti Mardukin "
             "siipiensä alle, mutta on kylmä pragmaatikko: hän näkee "
             "Mardukin 'sielumagneettina' ja täydellisenä astiana "
             "(Infracta Animae) maailman vaarallisimmille sieluille.",
        tactics="Avaa Path to the Gravella kovimpaan uhkaan ja antaa "
                "Aurelian purkaa tuplasmiten kirottuun kohteeseen — "
                "yhdistelmä tappaa pomon kierroksessa. Spirit Guardians "
                "ympärilleen, Sentinel at Death's Door suojaa omia "
                "kriittisiltä, Keeper of Souls pitää rivit pystyssä.",
        loot_table="Mortem-mace, Magnus Custoksen sinetti, kultainen "
                   "aurinko-pääkallo -medaljonki.",
        habitat="Pinwud", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5),

    # ---- Aurelia Valtar (rakennettu Pal 14 / Ftr 6 -pohjalta) ------ #
    CreatureStats(
        name="Aurelia Valtar", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=21, armor_type="Plate + Shield of Requiem",
        hit_points=190, hit_dice="14d10+6d10+60", speed=30,
        abilities=AbilityScores(strength=20, dexterity=12, constitution=18,
                                intelligence=11, wisdom=14, charisma=20),
        saving_throws={"Strength": 11, "Constitution": 10, "Wisdom": 13,
                       "Charisma": 16},
        skills={"Athletics": 11, "Intimidation": 11, "Perception": 8,
                "Religion": 5},
        senses="Passive Perception 18", languages="Common, Celestial",
        damage_resistances=["necrotic"],
        condition_immunities=["Frightened", "Diseased"],
        spellcasting_ability="Charisma", spell_save_dc=18,
        spell_attack_bonus=10,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
        spell_names=["Bless", "Divine Favor", "Shield of Faith",
                     "Compelled Duel", "Hold Person", "Magic Weapon",
                     "Dispel Magic", "Aura of Vitality", "Banishment",
                     "Staggering Smite"],
        actions=[
            Action("Multiattack", "x2 Requiem Greatsword", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Requiem Greatsword",
                                        "Requiem Greatsword"]),
            Action("Requiem Greatsword",
                   "Melee (+1 miekka; Improved Divine Smite sisältyy)", 12,
                   "2d6+1d8", 6, "slashing", range=5,
                   properties=["heavy", "two-handed"]),
            Action("Divine Smite",
                   "Osuman jälkeen: polta loitsupaikka (2d8 + 1d8/taso yli "
                   "1., +1d8 epäkuolleisiin) radiant-vahinkoa", 0, "4d8", 0,
                   "radiant", range=5, action_type="free"),
            Action("Earthshaking Wrath",
                   "15 ft säde (DC 18 STR tai Prone + puolet vahingosta "
                   "onnistuneella)", 0, "4d8", 0, "thunder", range=15,
                   aoe_radius=15, aoe_shape="sphere",
                   applies_condition="Prone", condition_save="Strength",
                   condition_dc=18),
        ],
        features=[
            Feature("Action Surge", "1/short rest: ota yksi ylimääräinen "
                    "toiminto — tämä on 'tuplasmiten' ydin (kaksi "
                    "Attack-toimintoa, molemmat Divine Smitellä).",
                    feature_type="class", uses_per_day=1,
                    mechanic="action_surge", short_rest_recharge=True),
            Feature("Divine Smite", "Osuessaan melee-aseella: polta "
                    "loitsupaikka 2d8 radiant (+1d8 per taso yli 1., +1d8 "
                    "epäkuolleisiin). Maksimi 5d8.",
                    feature_type="class", mechanic="divine_smite"),
            Feature("Improved Divine Smite", "Kaikki melee-osumat tekevät "
                    "+1d8 radiant (laskettu miekan vahinkoon).",
                    feature_type="class", mechanic="improved_divine_smite"),
            Feature("Extra Attack", "2 hyökkäystä Attack-toiminnolla",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Aura of Protection", "Hän ja liittolaiset 10 ft "
                    "säteellä saavat +5 (CHA) kaikkiin pelastusheittoihin.",
                    feature_type="class", mechanic="aura_of_protection",
                    aura_radius=10),
            Feature("Aura of Courage", "Hän ja liittolaiset 10 ft säteellä "
                    "ovat immuuneja Frightened-tilalle.",
                    feature_type="class", mechanic="aura_of_courage",
                    aura_radius=10),
            Feature("Cleansing Touch", "3/päivä: päätä yksi loitsu "
                    "itsestään tai koskettamastaan olennosta.",
                    feature_type="class", uses_per_day=3),
            Feature("Lay on Hands", "70 HP:n parannusvaranto; 5 HP "
                    "parantaa sairauden tai myrkyn.", feature_type="class",
                    mechanic="lay_on_hands", mechanic_value="70"),
            Feature("Indomitable", "2/päivä: heitä epäonnistunut "
                    "pelastusheitto uudelleen.", feature_type="class",
                    uses_per_day=2, mechanic="indomitable"),
            Feature("Second Wind", "Bonustoiminto: palauta 1d10+6 HP. "
                    "1/short rest.", feature_type="class", uses_per_day=1,
                    mechanic="second_wind", mechanic_value="1d10+6",
                    short_rest_recharge=True),
            Feature("Earthshaking Wrath", "Recharge 5-6: maa halkeaa "
                    "hänen iskustaan (15 ft, DC 18 STR).", recharge="5-6"),
            Feature("Sotilaan haavat", "Aesican taistelun jäljiltä: "
                    "vakavasti haavoittunut (DM voi aloittaa hänet "
                    "vähentyneillä HP:illa, esim. 140/190).",
                    feature_type="passive"),
        ],
        legendary_action_count=0,
        lore="Praetor Purificator — Puhdistuksen Kenraali ja Death's "
             "Vigilin sotilaallisen siiven johtaja. Taso 20 (Paladin 14 / "
             "Fighter 6), armoton kenttäkomentaja, jonka taistelutyyli on "
             "suoraa tuhoa: 'tuplasmitet'. Hän otti Mardukin siipiensä "
             "alle ja painosti tämän kovakouraisesti puhdistajan tielle. "
             "Padak arvioi ryhmän pärjäävän Aurelialle ja Gaiukselle "
             "yhdessä. Omin sanoin: \"Kun otan miekkaani maa tärisee.\"",
        tactics="Kierros 1: Attack (2 iskua) + Action Surge (2 iskua) ja "
                "Divine Smite jokaiseen osumaan — jos Gaius on kironnut "
                "kohteen Path to the Gravella, vahinko tuplaantuu ja pomo "
                "kuolee kierroksessa. Earthshaking Wrath kaataa "
                "muodostelman; Aura of Protection tekee ryhmän "
                "pelastusheitoista lähes varmoja.",
        loot_table="Requiem-suurmiekka (+1), Puhdistajan levyhaarniska, "
                   "Praetorin sinetti.",
        habitat="Pinwud", challenge_rating=17.0, xp=18000,
        proficiency_bonus=6),

    # ---- Thalgrum (rakennettu: "aivan eri tason uhka") ------------- #
    CreatureStats(
        name="Thalgrum", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=19, armor_type="Mage Armor + Kaavun kirjoitukset",
        hit_points=225, hit_dice="24d8+120", speed=30, fly_speed=30,
        abilities=AbilityScores(strength=10, dexterity=16, constitution=20,
                                intelligence=24, wisdom=18, charisma=14),
        saving_throws={"Intelligence": 14, "Wisdom": 11, "Constitution": 12,
                       "Dexterity": 10},
        skills={"Arcana": 21, "History": 21, "Religion": 18,
                "Investigation": 14, "Insight": 11},
        senses="Truesight 60 ft., Passive Perception 14",
        languages="Common, Celestial, Infernal, Abyssal, Deep Speech, "
                  "muinaiset kielet",
        damage_resistances=["necrotic", "psychic"],
        damage_immunities=["poison"],
        condition_immunities=["Charmed", "Frightened", "Poisoned"],
        spellcasting_ability="Intelligence", spell_save_dc=22,
        spell_attack_bonus=14,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 2, "7th": 2, "8th": 1, "9th": 1},
        spell_names=["Shield", "Absorb Elements", "Magic Missile",
                     "Mirror Image", "Hold Person", "Counterspell",
                     "Dispel Magic", "Blight", "Banishment",
                     "Greater Invisibility", "Wall of Force", "Telekinesis",
                     "Cloudkill", "Disintegrate", "Finger of Death",
                     "Forcecage", "Feeblemind", "Power Word Kill"],
        cantrip_names=["Toll the Dead", "Ray of Frost", "Mind Sliver",
                       "Mage Hand"],
        actions=[
            Action("Multiattack", "x3 Soul Siphon", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Soul Siphon", "Soul Siphon",
                                        "Soul Siphon"]),
            Action("Soul Siphon",
                   "Ranged spell (imee sielunsirpaleen; Thalgrum parantaa "
                   "puolet vahingosta)", 14, "4d8+2d6", 0, "necrotic",
                   range=120),
            Action("Unwrite the Soul",
                   "Yksi kohde 60 ft (DC 22 CHA tai 8d10 psychic ja "
                   "muistin/identiteetin osittainen pyyhkiytyminen)", 0,
                   "8d10", 0, "psychic", range=60,
                   applies_condition="Stunned", condition_save="Charisma",
                   condition_dc=22),
            Action("Grey Codex Ritual",
                   "Recharge 5-6: sivu avautuu — 20 ft säde, DC 22 WIS tai "
                   "9d8 necrotic ja Frightened 1 min (puolet onnistuneella)",
                   0, "9d8", 0, "necrotic", range=60, aoe_radius=20,
                   aoe_shape="sphere", applies_condition="Frightened",
                   condition_save="Wisdom", condition_dc=22),
        ],
        features=[
            Feature("Legendary Resistance", "3/päivä: valitse onnistuvasi "
                    "epäonnistuneessa pelastusheitossa.",
                    feature_type="passive", uses_per_day=3),
            Feature("Magic Resistance", "Etu pelastusheittoihin loitsuja ja "
                    "taikaefektejä vastaan.", mechanic="magic_resistance"),
            Feature("Master of the Unclean Library",
                    "Tuntee jokaisen takavarikoidun nekroottisen "
                    "artefaktin: voi kerran taistelussa aktivoida yhden "
                    "(DM valitsee tehon).", feature_type="passive"),
            Feature("Soul as Data", "Kun olento kuolee 60 ft säteellä, "
                    "Thalgrum tallentaa sen sielunsirpaleen: hän saa 20 "
                    "tilapäistä HP ja +1 loitsu-DC:hen (max +3) "
                    "taistelun loppuun.", feature_type="passive"),
            Feature("Counterspell Mastery",
                    "Reaktio: Counterspell ilman loitsupaikkaa 3/päivä, ja "
                    "hän onnistuu automaattisesti 5. tason tai matalampia "
                    "loitsuja vastaan.", feature_type="reaction",
                    uses_per_day=3),
            Feature("Grey Codex Ritual", "Recharge 5-6.", recharge="5-6"),
            Feature("Ritual Step", "Bonustoiminto: teleportoituu 60 ft "
                    "näkemäänsä paikkaan (Misty Step ilman slottia).",
                    feature_type="bonus"),
            Feature("Contingency: Vault Recall",
                    "Kun hän putoaa alle 50 HP, hän teleportautuu "
                    "automaattisesti Pinwudin holviin (pakenee) — ellei "
                    "Forcecage/Banishment estä.", feature_type="reaction"),
            Feature("Sieluvarasto", "Ei paranna itseään tavanomaisesti; "
                    "Soul Siphon ja Soul as Data pitävät hänet pystyssä."),
            Feature("Legendaarinen: Sana arkistosta",
                    "Legendaarinen toiminto (1): yksi Soul Siphon.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Vaimenna",
                    "Legendaarinen toiminto (2): yksi olento 60 ft tekee "
                    "DC 22 CHA -pelastuksen tai ei voi loitsia ennen "
                    "seuraavan vuoronsa loppua.", feature_type="legendary",
                    legendary_cost=2),
            Feature("Legendaarinen: Kirjoita uudelleen",
                    "Legendaarinen toiminto (3): Thalgrum peruu yhden juuri "
                    "tapahtuneen hyökkäyksen tai loitsun vaikutuksen — "
                    "ikään kuin sitä ei olisi kirjoitettu.",
                    feature_type="legendary", legendary_cost=3),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        lore="Magister Librorum — Kirjaston Mestari. Harmaakaapuinen "
             "arkistonhoitaja, joka vastaa muinaisista teksteistä, "
             "rituaaleista ja takavarikoiduista nekroottisista "
             "artefakteista järjestön 'epäpuhtaassa kirjastossa'. Pitää "
             "Mardukia 'kävelevänä tutkimuskohteena' eikä ihmisenä ja "
             "voisi löytää rituaalin sielun siirtämiseksi esineeseen — "
             "mutta uhraisi Mardukin silmääkään räpäyttämättä, jos tämän "
             "sisällä oleva data on arvokkaampaa kuin henki. "
             "Padakin arvio: ryhmä voisi pärjätä Aurelialle ja Gaiukselle "
             "yhdessä, mutta \"Thalgrum on aivan eri tason uhka\" — hän on "
             "salaa koko järjestön vaarallisin yksilö.",
        tactics="Ei koskaan aloita etulinjasta: Greater Invisibility ja "
                "Ritual Step pitävät hänet ulottumattomissa, Forcecage tai "
                "Wall of Force eristää ryhmän kovimman iskijän. "
                "Counterspell Mastery vaimentaa loitsijat, Unwrite the Soul "
                "poistaa yhden pelaajan pelistä ja Soul as Data tekee "
                "hänestä sitä vahvemman mitä enemmän kentällä kuollaan. "
                "Alle 50 HP hän pakenee holviin — häntä ei voi tappaa "
                "vahingossa, vain loukkuun.",
        loot_table="Harmaa Codex (epäpuhdas kirjasto), sielunsirpale-"
                   "ampulleja, holvin avain.",
        habitat="Pinwud", challenge_rating=21.0, xp=33000,
        proficiency_bonus=7),

    # ================================================================= #
    # PURIFICATORES — Puhdistajat (30)
    # ================================================================= #
    CreatureStats(
        name="Praefectus Purificatorum", size="Medium",
        creature_type="Humanoid", native_plane="Material",
        alignment="Lawful Neutral", armor_class=19,
        armor_type="Plate + Shield", hit_points=136, hit_dice="16d8+64",
        speed=30,
        abilities=AbilityScores(strength=18, dexterity=12, constitution=18,
                                intelligence=11, wisdom=16, charisma=14),
        saving_throws={"Strength": 8, "Constitution": 8, "Wisdom": 7},
        skills={"Athletics": 8, "Religion": 4, "Intimidation": 6,
                "Perception": 7},
        senses="Passive Perception 17", languages="Common, Celestial",
        spellcasting_ability="Wisdom", spell_save_dc=15,
        spell_attack_bonus=7,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 2},
        spell_names=["Bless", "Command", "Cure Wounds", "Guiding Bolt",
                     "Spiritual Weapon", "Spirit Guardians", "Revivify"],
        cantrip_names=["Sacred Flame", "Toll the Dead"],
        actions=[
            Action("Multiattack", "x2 Vigil Warhammer", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Vigil Warhammer",
                                        "Vigil Warhammer"]),
            Action("Vigil Warhammer", "Melee (+ radiant epäkuolleisiin)", 8,
                   "1d8+2d6", 4, "bludgeoning", range=5),
            Action("Expurgo", "Välitön teloitus: epäkuollut kohde alle "
                   "puolessa HP:stä tekee DC 15 CON -pelastuksen tai "
                   "tuhoutuu", 0, "6d8", 0, "radiant", range=5),
        ],
        features=[
            Feature("Action Surge", "1/short rest: yksi ylimääräinen "
                    "toiminto.", feature_type="class", uses_per_day=1,
                    mechanic="action_surge", short_rest_recharge=True),
            Feature("Divine Smite", "Osuessaan: polta loitsupaikka 2d8 "
                    "radiant (+1d8 epäkuolleisiin).", feature_type="class",
                    mechanic="divine_smite"),
            Feature("Extra Attack", "2 hyökkäystä",
                    feature_type="class", mechanic="extra_attack"),
            Feature("Second Wind", "Bonustoiminto: 1d10+5 HP. 1/short rest.",
                    feature_type="class", uses_per_day=1,
                    mechanic="second_wind", mechanic_value="1d10+5",
                    short_rest_recharge=True),
            Feature("Turn Undead", "Channel Divinity: epäkuolleet 30 ft "
                    "tekevät DC 15 WIS -pelastuksen tai pakenevat 1 min.",
                    feature_type="class", uses_per_day=2,
                    mechanic="channel_divinity"),
            Feature("Aura of Requiem", "Liittolaiset 10 ft säteellä saavat "
                    "+2 pelastusheittoihin epäkuolleiden kykyjä vastaan.",
                    aura_radius=10),
        ],
        lore="Puhdistajien kenttäkomentaja (3 kpl). Poikkeuksellisen "
             "raskas Fighter/Cleric/Paladin-moniluokka. Pelaajahahmo "
             "Marduk toimii yhtenä näistä kapteeneista.",
        tactics="Ryntää epäkuolleiden joukkoon, Turn Undead hajottaa rivit, "
                "Action Surge + Divine Smite kaataa nostajan. Spirit "
                "Guardians pitää alueen puhtaana.",
        habitat="Pinwud", challenge_rating=9.0, xp=5000,
        proficiency_bonus=4),

    CreatureStats(
        name="Purificator", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=18, armor_type="Splint Armor", hit_points=85,
        hit_dice="10d8+40", speed=30,
        abilities=AbilityScores(strength=16, dexterity=12, constitution=18,
                                intelligence=10, wisdom=14, charisma=11),
        saving_throws={"Constitution": 7, "Wisdom": 5},
        skills={"Athletics": 6, "Religion": 3, "Perception": 5},
        senses="Passive Perception 15", languages="Common",
        actions=[
            Action("Multiattack", "x2 Consecrated Halberd", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Consecrated Halberd",
                                        "Consecrated Halberd"]),
            Action("Consecrated Halberd", "Melee reach 10 ft (+ radiant)", 7,
                   "1d10+1d6", 3, "slashing", range=10, reach=10,
                   properties=["heavy", "reach", "two-handed"]),
            Action("Censer of Ash", "15 ft kartio (DC 14 CON tai 3d6 "
                   "radiant; epäkuolleet myös Blinded)", 0, "3d6", 0,
                   "radiant", range=15, aoe_radius=15, aoe_shape="cone",
                   applies_condition="Blinded", condition_save="Constitution",
                   condition_dc=14),
        ],
        features=[
            Feature("Undead Hunter", "+1d6 radiant osuessaan epäkuolleeseen "
                    "(laskettu hilparin vahinkoon)."),
            Feature("Formation Fighter", "Etu hyökkäyksiin, jos toinen "
                    "Purificator on 5 ft päässä samasta kohteesta."),
            Feature("Requiem Discipline", "Etu pelastusheittoihin "
                    "Frightened-tilaa vastaan."),
        ],
        lore="Rivipuhdistaja (27 kpl). Eliittisoturi, joka lähetetään "
             "tuhoamaan voimakkaita nekromantikkoja ja epäkuolleiden "
             "joukkoja. Kalju, otsassa pyhät tatuoinnit, kulta-musta "
             "tunikka.",
        tactics="Taistelee pareittain muodostelmassa; hilpari pitää "
                "vihollisen 10 ft päässä, Censer of Ash sokaisee "
                "epäkuolleet.",
        habitat="Pinwud", challenge_rating=5.0, xp=1800,
        proficiency_bonus=3),

    # ================================================================= #
    # MEDICI ANIMAE — Sielun Parantajat (167)
    # ================================================================= #
    CreatureStats(
        name="Archimedicus", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=16, armor_type="Chain Mail", hit_points=97,
        hit_dice="13d8+39", speed=30,
        abilities=AbilityScores(strength=11, dexterity=12, constitution=16,
                                intelligence=13, wisdom=19, charisma=15),
        saving_throws={"Wisdom": 8, "Charisma": 6},
        skills={"Medicine": 12, "Religion": 5, "Insight": 8,
                "Persuasion": 6},
        senses="Passive Perception 18", languages="Common, Celestial",
        spellcasting_ability="Wisdom", spell_save_dc=16,
        spell_attack_bonus=8,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 2, "5th": 1},
        spell_names=["Bless", "Cure Wounds", "Healing Word", "Lesser Restoration",
                     "Spiritual Weapon", "Revivify", "Death Ward",
                     "Mass Cure Wounds", "Guiding Bolt"],
        cantrip_names=["Sacred Flame", "Toll the Dead", "Guidance"],
        actions=[
            Action("Requiem Staff", "Melee", 4, "1d6", 0, "bludgeoning",
                   range=5),
            Action("Sacred Flame", "Ranged spell (DC 16 DEX, ei suojaa)", 0,
                   "3d8", 0, "radiant", range=60,
                   condition_save="Dexterity", condition_dc=16),
        ],
        features=[
            Feature("Last Rites", "Toiminto: yksi kuollut olento ei voi "
                    "nousta epäkuolleena, ja sen sielu ohjataan lepoon "
                    "(Pacare)."),
            Feature("Blessed Healer", "Kun hän parantaa toista 1. tason tai "
                    "korkeammalla loitsulla, hän parantaa itseään "
                    "2 + loitsun taso HP."),
            Feature("Disciple of Life", "Parannusloitsut antavat "
                    "lisäksi 2 + loitsun taso HP.", feature_type="class"),
            Feature("Soul Audit", "Voi tunnistaa kirouksia, "
                    "sielunsirpaleita ja epäkuolleisuutta koskettamalla "
                    "(Pää Codexin valtuutus)."),
        ],
        lore="Arkkiparantaja (7 kpl) — johtaa Sielun Parantajia. Kiertää "
             "maailmaa hautajaisia hoitaen ja surevia lohduttaen, mutta "
             "hinnoittelee palvelunsa armottomasti kriisiaikoina.",
        tactics="Pysyy takana, pitää Puhdistajat pystyssä Mass Cure "
                "Woundsilla ja Death Wardilla; Last Rites estää vihollisen "
                "nekromantikon nostamasta kaatuneita.",
        habitat="Pinwud", challenge_rating=7.0, xp=2900,
        proficiency_bonus=4),

    CreatureStats(
        name="Medicus Animae", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Lawful Neutral",
        armor_class=15, armor_type="Scale Mail", hit_points=44,
        hit_dice="8d8+8", speed=30,
        abilities=AbilityScores(strength=10, dexterity=11, constitution=12,
                                intelligence=12, wisdom=16, charisma=13),
        saving_throws={"Wisdom": 5},
        skills={"Medicine": 7, "Religion": 3, "Insight": 5},
        senses="Passive Perception 15", languages="Common",
        spellcasting_ability="Wisdom", spell_save_dc=13,
        spell_attack_bonus=5,
        spell_slots={"1st": 4, "2nd": 2},
        spell_names=["Bless", "Cure Wounds", "Healing Word",
                     "Lesser Restoration", "Spiritual Weapon"],
        cantrip_names=["Sacred Flame", "Guidance"],
        actions=[
            Action("Mace", "Melee", 2, "1d6", 0, "bludgeoning", range=5),
            Action("Sacred Flame", "Ranged spell (DC 13 DEX)", 0, "2d8", 0,
                   "radiant", range=60, condition_save="Dexterity",
                   condition_dc=13),
        ],
        features=[
            Feature("Last Rites", "Toiminto: kuollut olento ei voi nousta "
                    "epäkuolleena."),
            Feature("Comfort the Grieving", "Etu Insight- ja "
                    "Persuasion-heittoihin surevien kanssa."),
        ],
        lore="Sielun Parantaja — 83,5 % järjestön jäsenistä. Hoitaa "
             "hautajaisia, siunaa hautoja ja lohduttaa surevia.",
        tactics="Ei etsi taistelua: parantaa, siunaa ja suorittaa "
                "viimeiset riitit. Puolustautuu Sacred Flamella.",
        habitat="Pinwud", challenge_rating=2.0, xp=450,
        proficiency_bonus=2),

    # ================================================================= #
    # Yleiskäyttöinen sivuhahmopohja. Useat kampanjan maalais- ja
    # kaupunkilais-NPC:t viittasivat "monster:Commoner"-pohjaan, jota ei
    # ollut kirjastossa — se rikkoi heidän statlehtensä. Tässä se on.
    # ================================================================= #
    CreatureStats(
        name="Commoner", size="Medium", creature_type="Humanoid",
        native_plane="Material", alignment="Any", armor_class=10,
        armor_type="Vaatteet", hit_points=4, hit_dice="1d8", speed=30,
        abilities=AbilityScores(strength=10, dexterity=10, constitution=10,
                                intelligence=10, wisdom=10, charisma=10),
        senses="Passive Perception 10", languages="Common",
        actions=[
            Action("Club", "Melee", 2, "1d4", 0, "bludgeoning", range=5),
            Action("Improvised Weapon", "Melee (työkalu, kivi, tuoli)", 2,
                   "1d4", 0, "bludgeoning", range=5),
        ],
        features=[
            Feature("Ei taistelija", "Pakenee heti kun on vaarassa; "
                    "auttaa mieluummin tiedolla kuin aseella."),
        ],
        lore="Tavallinen kaupunkilainen, maanviljelijä tai käsityöläinen.",
        tactics="Pakenee. Ei hyökkää ellei ole pakotettu.",
        habitat="Any", challenge_rating=0.0, xp=10,
        proficiency_bonus=2),
]
