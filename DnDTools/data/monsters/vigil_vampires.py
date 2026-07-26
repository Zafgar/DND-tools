"""Pinwudin Vigil-temppelin vampyyriongelma.

Dimerius Blackfeet on tehnyt vampyyrejä Death's Vigilin omasta
papistosta. Ironia on koko kohtauksen ydin: järjestö, joka polttaa
epäkuolleet ja "nullifioi" kirotun maan, kantaa nyt tartuntaa omassa
temppelissään — ja papit **piilottelevat sitä**, koska paljastuminen
tarkoittaa oman järjestön Puhdistajien rovion.

Mikä tekee näistä eri asian kuin tavalliset vampyyrit:

  * **Turmeltunut jumalallinen magia.** He ovat yhä pappeja ja heidän
    loitsunsa toimivat — mutta väärinpäin. Cure Wounds parantaa vain
    epäkuolleita, Channel Divinity komentaa hautoja avaamaan sen sijaan
    että karkottaisi niistä nousevat, ja Sacred Flame on KADONNUT
    heidän listaltaan kokonaan. Se on ensimmäinen merkki jonka
    pelaajat voivat huomata: pappi joka ei enää osaa loitsia valoa.
  * **Vigilin oma varustus.** Kulta-mustat kaavut, Requiem-terät,
    pyhät varsijouset ja vaarnat — kaikki nyt elävien käytössä
    kääntyneenä. Sama haarniska, sama medaljonki, väärä puoli.
  * **Auringonvalo on heidän salaisuutensa.** Temppelin ikkunat on
    peitetty "surunaikana", kellarikäytävät ovat uusia, ja aamumessu
    on siirretty iltaan. Nämä ovat pelinjohtajan vihjeet.

Portaikko pelinjohtajalle (CR): Verikuoro 4 → Medicus Sanguinis 5 →
Custos Nocturnus 6 → Sanguis Custos 8 → Confessor Ianus 10 →
Magister Sanguinis Vhaltor 11 → Praefectus Sanguinis Ostorius 13 →
Sanctum Abominatio 16 (temppelin oma pyhäinjäännös noussut).

Kaikilla on ``tactics``-kentässä konkreettinen kierrosjärjestys ja
``lore``-kentässä se, kuka hahmo oli ENNEN kääntymistä — pelaajien on
tarkoitus tunnistaa heidät.
"""
from data.models import CreatureStats, AbilityScores, Action, Feature, Item


# Yhteinen heikkouspaketti: jokainen vampyyri tarvitsee nämä, ja
# pelinjohtajan on nähtävä ne statlehdellä ilman kirjan selaamista.
def _vampire_weaknesses(spawn: bool = False) -> Feature:
    extra = ("" if spawn else
             " Ei voi ylittää asuintalon kynnystä ilman kutsua.")
    return Feature(
        "Vampyyrin heikkoudet",
        "Auringonvalo: 20 radiant vuoron alussa ja haitta osumaheittoihin "
        "sekä kykytesteihin. Ei voi ylittää juoksevaa vettä. Valkopihlaja"
        "vaarna sydämeen lamaantuneena tuhoaa lopullisesti. "
        "Radiant-vahinko ja auringonvalo sammuttavat regeneraation "
        "vuoron ajaksi." + extra,
        feature_type="passive")


def _corrupted_divinity(what: str) -> Feature:
    return Feature(
        "Turmeltunut jumaluus",
        "Pappeus toimii yhä, mutta väärinpäin: " + what + " Sacred Flame "
        "ja kaikki radiant-loitsut ovat kadonneet listalta kokonaan — "
        "PELINJOHTAJALLE: tämä on vihje jonka pelaajat voivat huomata "
        "ennen kuin hampaat tulevat esiin.",
        feature_type="passive")


_REGEN = "Palauttaa {n} HP vuoronsa alussa, ellei ole ottanut radiant-" \
         "vahinkoa tai ole auringonvalossa tai juoksevassa vedessä."


monsters = [
    # ================================================================= #
    # CR 4 — VERIKUORO (Chorus Mortis) — käännytetyt kuoroakolyytit
    # ================================================================= #
    CreatureStats(
        name="Verikuoron akolyytti", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil",
        armor_class=14, armor_type="Kaapu + luonnollinen panssari",
        hit_points=52, hit_dice="8d8+16", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=14, dexterity=16, constitution=14,
                                intelligence=10, wisdom=14, charisma=14),
        saving_throws={"Dexterity": 5, "Wisdom": 4},
        skills={"Perception": 4, "Stealth": 5, "Performance": 4,
                "Religion": 2},
        senses="Darkvision 60 ft., Passive Perception 14",
        languages="Common, Celestial (rukoukset ulkoa)",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion"],
        spellcasting_ability="Wisdom", spell_save_dc=12,
        spell_attack_bonus=4,
        spell_slots={"1st": 3, "2nd": 2},
        spell_names=["Inflict Wounds", "Bane", "Silence", "Blindness/Deafness"],
        cantrip_names=["Toll the Dead", "Chill Touch"],
        actions=[
            Action("Multiattack", "x2 Kynnet — tai Purenta yhtä "
                   "lamaantunutta kohdetta", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Kynnet", "Kynnet"]),
            Action("Kynnet", "Melee", 5, "2d4", 3, "slashing", range=5),
            Action("Purenta",
                   "Melee, vain kohteeseen joka on Grappled, "
                   "Incapacitated tai Restrained. Uhri menettää 1d6 "
                   "elinvoimaa (max HP laskee) ja akolyytti paranee "
                   "saman verran.",
                   5, "1d6+1d6", 3, "necrotic", range=5),
            Action("Kuolinvirsi",
                   "Verikuoro laulaa. 30 ft: DC 12 WIS tai Frightened "
                   "vuoron loppuun. JOS kaksi tai useampi Verikuoron "
                   "akolyyttiä laulaa samalla kierroksella, DC on 15 ja "
                   "kohde on Frightened minuutin (save vuoron lopussa).",
                   0, "", 0, "", range=30, aoe_radius=30, aoe_shape="sphere",
                   applies_condition="Frightened", condition_save="Wisdom",
                   condition_dc=12),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=10),
                    mechanic="regeneration", mechanic_value="10"),
            _vampire_weaknesses(spawn=True),
            _corrupted_divinity("Inflict Wounds parantaa läheistä "
                                "epäkuollutta jos kohde kuolee siihen."),
            Feature("Kuoron voima",
                    "Etu osumaheittoihin kohteeseen, jonka 5 ft sisällä on "
                    "toinen Verikuoron akolyytti (Pack Tactics). Nämä "
                    "eivät koskaan esiinny yksin.",
                    mechanic="pack_tactics"),
            Feature("Spider Climb",
                    "Kiipeää seinillä ja katossa vapaasti — temppelin "
                    "holvikatto on heidän maastoaan."),
        ],
        items=[
            Item("Vigilin kuorokaapu", item_type="armor", slot="armor",
                 equipped=True, rarity="common", armor_category="light",
                 base_ac=12,
                 description="Kulta-musta kaapu, hihansuut tummuneet "
                             "kuivuneesta verestä."),
            Item("Aurinko-pääkallo -medaljonki", item_type="amulet",
                 slot="amulet", equipped=True, rarity="common",
                 description="Järjestön tunnus. Kääntyneillä metalli on "
                             "musta ja aurinko-osa on hangattu pois."),
        ],
        lore="Temppelin kuoro lauloi kuolleiden saattovirret. Dimerius "
             "käänsi heidät ensimmäisinä, koska kuoro laulaa iltamessussa "
             "eikä kukaan ihmettele että he eivät enää tule aamuun. He ovat "
             "yhä nuoria, yhä peloissaan, ja tottelevat Ostoriusta koska "
             "eivät osaa muuta.",
        tactics="Aina 3-6 kappaletta. Kierros 1: kaikki laulavat "
                "Kuolinvirren samalla kierroksella — DC nousee 15:een ja "
                "pelko kestää minuutin. Sen jälkeen kiipeävät katolle, "
                "pudottautuvat pelästyneen kohteen päälle ja purevat. "
                "Pakenevat heti kun kaksi kaatuu.",
        loot_table="Vigilin kuorokaapu, mustunut medaljonki, virsikirja "
                   "jonka viimeisiltä sivuilta on raavittu radiant-rukoukset.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=4.0, xp=1100,
        proficiency_bonus=2,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 5 — MEDICUS SANGUINIS — sairaanhoitaja josta tuli imijä
    # ================================================================= #
    CreatureStats(
        name="Medicus Sanguinis", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Lawful Evil",
        armor_class=15, armor_type="Nahkainen esiliina + luonnollinen",
        hit_points=68, hit_dice="9d8+27", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=12, dexterity=16, constitution=16,
                                intelligence=14, wisdom=18, charisma=14),
        saving_throws={"Constitution": 6, "Wisdom": 7},
        skills={"Medicine": 10, "Insight": 7, "Deception": 5,
                "Perception": 7},
        senses="Darkvision 60 ft., Passive Perception 17",
        languages="Common, Celestial",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Poisoned"],
        spellcasting_ability="Wisdom", spell_save_dc=15,
        spell_attack_bonus=7,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3},
        spell_names=["Cure Wounds", "Healing Word", "Inflict Wounds",
                     "Lesser Restoration", "Warding Bond", "Silence",
                     "Vampiric Touch", "Life Transference", "Revivify"],
        cantrip_names=["Toll the Dead", "Chill Touch", "Mage Hand"],
        actions=[
            Action("Multiattack",
                   "Yksi loitsu ja yksi Verilansetti — tai x2 Verilansetti",
                   0, "", 0, "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Verilansetti", "Verilansetti"]),
            Action("Verilansetti",
                   "Melee, hoitovälineeksi tehty veitsi. Osumalla kohde "
                   "vuotaa: 1d6 necrotic sen vuoron alussa kunnes joku "
                   "käyttää toiminnon sitoakseen haavan (DC 13 Medicine).",
                   7, "1d6+2d6", 3, "necrotic", range=5,
                   properties=["finesse", "light"]),
            Action("Purenta",
                   "Melee, kohteeseen joka on Grappled, Incapacitated tai "
                   "Restrained: uhri menettää 2d6 elinvoimaa ja Medicus "
                   "paranee saman verran.",
                   7, "1d6+2d6", 3, "necrotic", range=5),
            Action("Armollinen uni",
                   "Medicus tarjoaa 'kipulääkettä'. Yksi olento 5 ft "
                   "sisällä: DC 15 WIS tai Poisoned ja Incapacitated "
                   "minuutin ajan (save vuoron lopussa). Autettu tai "
                   "tajuton kohde epäonnistuu automaattisesti.",
                   0, "", 0, "", range=5, applies_condition="Poisoned",
                   condition_save="Wisdom", condition_dc=15),
        ],
        bonus_actions=[
            Action("Vuodatus",
                   "Bonustoiminto: Medicus siirtää 3d6 elinvoimaa yhdeltä "
                   "haavoittuneelta olennolta 30 ft sisällä yhdelle "
                   "epäkuolleelle liittolaiselle (DC 15 CON puolittaa).",
                   0, "3d6", 0, "necrotic", range=30, action_type="bonus",
                   condition_save="Constitution", condition_dc=15),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=10),
                    mechanic="regeneration", mechanic_value="10"),
            _vampire_weaknesses(spawn=True),
            _corrupted_divinity("Cure Wounds ja Healing Word parantavat "
                               "VAIN epäkuolleita; elävään kohdistettuna ne "
                               "tekevät saman verran necrotic-vahinkoa. "
                               "Revivify nostaa kohteen vampyyrina."),
            Feature("Sairastuvan isäntä",
                    "Medicus tietää tarkalleen kuka temppelissä on heikko. "
                    "Hän saa edun osumaheittoihin kohteeseen, jonka HP on "
                    "alle puolet, ja hänen purentansa on kriittinen osuma "
                    "kohteeseen joka on Unconscious.",
                    feature_type="passive"),
            Feature("Uskottava",
                    "Hän on yhä temppelin lääkäri ja hoitaa oikeasti "
                    "eläviä — juuri sen verran ettei kukaan epäile. "
                    "Insight-tarkistus häntä vastaan on DC 20, ja häntä "
                    "vastaan puhuvia ei uskota.",
                    feature_type="passive"),
        ],
        items=[
            Item("Vigilin hoitolaukku", item_type="wondrous", equipped=True,
                 rarity="uncommon",
                 description="Aitoja sidetarpeita päällimmäisenä, "
                             "verilasipulloja pohjalla."),
            Item("Verilansetti", item_type="weapon", slot="main_hand",
                 equipped=True, rarity="uncommon", damage_dice="1d6+2d6",
                 description="Kirurginveitsi jonka terään on syövytetty "
                             "nekroottinen riimu."),
        ],
        lore="Temppelin Medicus Animae hoiti kuolevia ja lohdutti heitä "
             "viimeisillä hetkillä. Dimerius ei tarvinnut häntä sotilaana "
             "vaan portinvartijana: kääntynyt lääkäri päättää kuka "
             "'ei selvinnyt yöstä'. Hän on yhä ystävällinen. Se on pahin "
             "osa.",
        tactics="Ei taistele etulinjassa. Kierros 1: Vuodatus "
                "bonustoimintona pitämään Ostorius pystyssä + Silence "
                "ryhmän loitsijan päälle. Sen jälkeen Life Transference ja "
                "Vampiric Touch. Jos pelaaja kaatuu 0 HP:hen, hän rientää "
                "'auttamaan' ja käyttää Armollisen unen. Antautuu heti kun "
                "on yksin — ja valehtelee vakuuttavasti.",
        loot_table="Hoitolaukku (5 healer's kit -käyttöä), verilansetti, "
                   "potilaskirja jossa on 14 nimeä yliviivattuna.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=5.0, xp=1800,
        proficiency_bonus=3,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 6 — CUSTOS NOCTURNUS — yövartija, Vigilin varusteet väärinpäin
    # ================================================================= #
    CreatureStats(
        name="Custos Nocturnus", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Lawful Evil",
        armor_class=17, armor_type="Vigilin ketjupaita + kilpi",
        hit_points=90, hit_dice="12d8+36", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=16, dexterity=18, constitution=16,
                                intelligence=11, wisdom=14, charisma=12),
        saving_throws={"Dexterity": 7, "Constitution": 6, "Wisdom": 5},
        skills={"Stealth": 10, "Perception": 8, "Athletics": 6},
        senses="Darkvision 120 ft., Passive Perception 18",
        languages="Common",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Charmed", "Frightened"],
        actions=[
            Action("Multiattack",
                   "x2 Requiem-terä, tai x2 Pyhä varsijousi, tai yksi "
                   "kummastakin", 0, "", 0, "", is_multiattack=True,
                   multiattack_count=2,
                   multiattack_targets=["Requiem-terä", "Requiem-terä"]),
            Action("Requiem-terä",
                   "Melee, Vigilin oma pyhitetty miekka — pyhitys on "
                   "kuollut mutta terä on yhä hyvä.",
                   7, "1d8+3d6", 3, "slashing", range=5,
                   properties=["versatile"]),
            Action("Pyhä varsijousi",
                   "Kaukotaistelu 80/320 ft. Vaarnanuolet: kriittisellä "
                   "osumalla elävä kohde on Restrained (naulattu; DC 15 "
                   "STR irrottautuu).",
                   7, "1d10+2d6", 3, "piercing", range=80, long_range=320,
                   applies_condition="Restrained", condition_save="Strength",
                   condition_dc=15),
            Action("Vaarnaheitto",
                   "Heittää valkopihlajavaarnan (20/60 ft). Vampyyrin "
                   "vaarna elävää vastaan: 2d6 piercing ja DC 15 CON tai "
                   "kohde ei voi saada healingia minuutin ajan.",
                   7, "2d6", 3, "piercing", range=20, long_range=60,
                   condition_save="Constitution", condition_dc=15),
        ],
        bonus_actions=[
            Action("Varjoon",
                   "Bonustoiminto: piiloutuu missä tahansa hämärässä tai "
                   "pimeässä (Cunning Action -tyylinen Hide) ja liikkuu "
                   "puolet nopeudestaan.",
                   0, "", 0, "", action_type="bonus"),
        ],
        reactions=[
            Action("Kilven torjunta",
                   "Reaktio: +3 AC yhtä osumaa vastaan. Jos isku menee "
                   "silti ohi, hän saa tehdä yhden Requiem-terä-iskun.",
                   0, "", 0, "", action_type="reaction", range=5),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=15),
                    mechanic="regeneration", mechanic_value="15"),
            _vampire_weaknesses(spawn=True),
            Feature("Yön vartiovuoro",
                    "Custos Nocturnus tuntee temppelin joka käytävän. "
                    "Hän ei koskaan joudu yllätetyksi temppelissä, ja hän "
                    "saa edun aloiteheittoon siellä. Ensimmäinen isku "
                    "vuorolla, jolla hän tulee näkymättömyydestä tai "
                    "piilosta, tekee ylimääräiset 3d6 (Sneak Attack).",
                    mechanic="sneak_attack", mechanic_value="3d6"),
            Feature("Vartijan vihellys",
                    "Bonustoiminto 1/taistelu: kutsuu 2 Verikuoron "
                    "akolyyttiä paikalle 1d4 kierroksen kuluessa.",
                    feature_type="bonus", uses_per_day=1),
            Feature("Reaktio: Kilven torjunta",
                    "Ks. reaktiot.", feature_type="reaction"),
            Feature("Spider Climb",
                    "Kiipeää pinnoilla ja katossa vapaasti."),
        ],
        items=[
            Item("Requiem-terä", item_type="weapon", slot="main_hand",
                 equipped=True, rarity="uncommon", damage_dice="1d8+3d6",
                 description="Vigilin pyhitetty pitkämiekka. Pyhitysriimut "
                             "on tahallaan raavittu rikki, jotta terä ei "
                             "polttaisi kantajansa kättä."),
            Item("Pyhä varsijousi", item_type="weapon", slot="off_hand",
                 equipped=True, rarity="uncommon", damage_dice="1d10+2d6",
                 description="Ladattu vaarnanuolilla — samoilla joilla "
                             "hänen oma vartiovuoronsa oli määrä tappaa "
                             "vampyyrejä."),
            Item("Vigilin ketjupaita ja kilpi", item_type="armor",
                 slot="armor", equipped=True, rarity="common",
                 armor_category="medium", base_ac=13, max_dex_bonus=2,
                 description="Kulta-musta, kolhuinen. Kilvessä on aurinko "
                             "jonka päälle on maalattu tervalla risti."),
        ],
        lore="Temppelin yövartio oli se joka ilmoitti epäkuolleista. "
             "Dimerius käänsi vartion ensin, jotta kukaan ei ilmoittaisi "
             "hänestä. Nyt he tekevät saman vuoron samoissa varusteissa "
             "samalla reitillä — ja Pinwudissa on kadonnut yhdeksän "
             "puunhakkaajaa.",
        tactics="Ei koskaan aloita avoimesti. Piiloutuu, ampuu vaarnanuolen "
                "(kriittisellä naulaa kohteen paikoilleen), Varjoon "
                "bonustoimintona, ampuu uudelleen Sneak Attackilla. "
                "Lähitaistelussa Kilven torjunta joka kierros. Vihellys "
                "heti kun HP alle puolet.",
        loot_table="Requiem-terä, pyhä varsijousi + 12 vaarnanuolta, "
                   "Vigilin ketjupaita, temppelin pohjapiirros ja "
                   "vartiovuorolista jossa on kolme nimeä kahdesti.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=6.0, xp=2300,
        proficiency_bonus=3,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 8 — SANGUIS CUSTOS — käännytetty Puhdistaja, etulinja
    # ================================================================= #
    CreatureStats(
        name="Sanguis Custos", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Lawful Evil",
        armor_class=18, armor_type="Vigilin levyhaarniska",
        hit_points=136, hit_dice="16d8+64", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=20, dexterity=14, constitution=18,
                                intelligence=10, wisdom=14, charisma=16),
        saving_throws={"Strength": 8, "Constitution": 7, "Wisdom": 5,
                       "Charisma": 6},
        skills={"Athletics": 8, "Intimidation": 6, "Perception": 5},
        senses="Darkvision 120 ft., Passive Perception 15",
        languages="Common, Celestial",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Charmed", "Frightened"],
        spellcasting_ability="Charisma", spell_save_dc=14,
        spell_attack_bonus=6,
        spell_slots={"1st": 4, "2nd": 2},
        spell_names=["Inflict Wounds", "Command", "Shield of Faith",
                     "Darkness", "Misty Step"],
        actions=[
            Action("Multiattack",
                   "x3: Requiem-suurmiekka tai Kynnet; yksi niistä voidaan "
                   "korvata Purennalla lamaantuneeseen kohteeseen",
                   0, "", 0, "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Requiem-suurmiekka",
                                        "Requiem-suurmiekka", "Kynnet"]),
            Action("Requiem-suurmiekka",
                   "Melee, kahden käden. Vigilin puhdistajanmiekka, jonka "
                   "radiant-riimut ovat sammuneet ja tilalle on vuotanut "
                   "nekroosi.",
                   8, "2d6+3d6", 5, "slashing", range=5,
                   properties=["heavy", "two-handed"]),
            Action("Kynnet",
                   "Melee. Osumalla kohde on Grappled (escape DC 18) jos "
                   "se on Large tai pienempi.",
                   8, "2d6", 5, "slashing", range=5,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=18),
            Action("Purenta",
                   "Melee, kohteeseen joka on Grappled, Incapacitated tai "
                   "Restrained: 3d6 elinvoimaa pois (max HP laskee) ja "
                   "Sanguis Custos paranee saman verran. Näin kaatunut "
                   "nousee vampyyrina Ostoriuksen palvelukseen.",
                   8, "1d6+3d6", 5, "necrotic", range=5),
            Action("Turmeltunut smite",
                   "Recharge 5-6. Custos purkaa Vigilin smiten "
                   "väärinpäin: seuraava osuma tekee 6d8 necrotic "
                   "ylimääräistä, ja kohde ei voi saada healingia "
                   "kierroksen loppuun (DC 14 CON puolittaa vahingon).",
                   0, "6d8", 0, "necrotic", range=5,
                   condition_save="Constitution", condition_dc=14),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=15),
                    mechanic="regeneration", mechanic_value="15"),
            _vampire_weaknesses(spawn=True),
            _corrupted_divinity("Divine Smite tekee necrotic-vahinkoa "
                               "radiantin sijaan, ja Command toimii vain "
                               "elävään."),
            Feature("Puhdistajan kuri",
                    "Hän harjoitteli tappamaan epäkuolleita ja tietää nyt "
                    "miten häntä tullaan tappamaan: hänellä on ETU "
                    "pelastusheittoihin karkotusta (Turn Undead) ja "
                    "radiant-loitsujen vaikutuksia vastaan, ja hän kohdistaa "
                    "aina ensin sen pelaajan, joka käytti radiant-vahinkoa.",
                    feature_type="passive"),
            Feature("Turmeltunut smite", "Recharge 5-6.", recharge="5-6"),
            Feature("Spider Climb",
                    "Kiipeää pinnoilla ja katossa vapaasti."),
        ],
        items=[
            Item("Requiem-suurmiekka", item_type="weapon", slot="main_hand",
                 equipped=True, rarity="rare", damage_dice="2d6+3d6",
                 requires_attunement=True, attuned=True,
                 description="Puhdistajan suurmiekka. Riimut hehkuivat "
                             "ennen kultaisina; nyt ne ovat mustia ja "
                             "terästä nousee ohut savu."),
            Item("Vigilin levyhaarniska", item_type="armor", slot="armor",
                 equipped=True, rarity="uncommon", armor_category="heavy",
                 base_ac=18, max_dex_bonus=0, stealth_disadvantage=True,
                 description="Kulta-musta levyhaarniska. Rintapanssarin "
                             "aurinkoreliefi on lyöty sisäänpäin."),
        ],
        lore="Puhdistajat ovat Vigilin sotilaallinen siipi — Aurelia "
             "Valtarin omia. Kun yksi heistä kääntyy, järjestö menettää "
             "sekä sotilaan että salaisuuden: Puhdistaja tuntee kaikki "
             "Vigilin vasta-rituaalit. Ostorius käyttää heitä "
             "ovenvartijoina, koska Puhdistaja tunnetaan kasvoista ja "
             "kukaan ei kysy häneltä mitään.",
        tactics="Etulinja. Kierros 1: Misty Step ryhmän takalinjaan, "
                "Kynnet grapplaamaan loitsijan, sitten Purenta (grapplattu "
                "kohde = automaattinen elinvoiman imu). Turmeltunut smite "
                "heti kun joku on alle puolessa HP:ssä — healing-esto "
                "estää nostamisen. Kohdistaa aina sen, joka teki "
                "radiant-vahinkoa: se on hänen ainoa oikea uhkansa.",
        loot_table="Requiem-suurmiekka (rare), Vigilin levyhaarniska, "
                   "Puhdistajan sinetti (pääsy temppelin kryptaan), "
                   "kaksi valkopihlajavaarnaa joita hän ei enää voi käyttää.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=8.0, xp=3900,
        proficiency_bonus=3,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 10 — CONFESSOR IANUS — se joka esittää yhä elävää
    # ================================================================= #
    CreatureStats(
        name="Confessor Ianus", size="Medium", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil",
        armor_class=16, armor_type="Kaapu + luonnollinen panssari",
        hit_points=127, hit_dice="15d8+60", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=14, dexterity=18, constitution=18,
                                intelligence=16, wisdom=18, charisma=20),
        saving_throws={"Dexterity": 8, "Wisdom": 8, "Charisma": 9},
        skills={"Deception": 13, "Persuasion": 13, "Insight": 12,
                "Perception": 8, "Religion": 7},
        senses="Darkvision 120 ft., Passive Perception 18",
        languages="Common, Celestial, Abyssal, Sylvan",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Charmed", "Frightened"],
        spellcasting_ability="Charisma", spell_save_dc=17,
        spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        spell_names=["Charm Person", "Command", "Hold Person", "Silence",
                     "Hypnotic Pattern", "Fear", "Counterspell",
                     "Blindness/Deafness", "Confusion", "Greater Invisibility",
                     "Dominate Person", "Hold Monster", "Mirror Image"],
        cantrip_names=["Toll the Dead", "Mind Sliver", "Mage Hand",
                       "Vicious Mockery"],
        actions=[
            Action("Multiattack",
                   "Yksi loitsu ja yksi Kynnet — tai x2 Kynnet",
                   0, "", 0, "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Kynnet", "Kynnet"]),
            Action("Kynnet",
                   "Melee. Osumalla Grappled (escape DC 16).",
                   9, "2d6+2d6", 4, "slashing", range=5,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=16),
            Action("Purenta",
                   "Melee lamaantuneeseen kohteeseen: 3d6 elinvoimaa pois, "
                   "Ianus paranee saman verran.",
                   9, "1d6+3d6", 4, "necrotic", range=5),
            Action("Ripin sinetti",
                   "Ianus kuulee kohteen synnit. Yksi olento 30 ft sisällä: "
                   "DC 17 WIS tai Charmed tunnin ajan. Charmed kohde pitää "
                   "Ianusta luotettuna rippi-isänään, kertoo hänelle "
                   "totuuden ja EI KERRO KENELLEKÄÄN mitä temppelissä näki. "
                   "Tämä on koko infestaation syy siihen, ettei kukaan "
                   "Pinwudissa ole vielä puhunut.",
                   0, "", 0, "", range=30, applies_condition="Charmed",
                   condition_save="Wisdom", condition_dc=17),
            Action("Katuva sana",
                   "Recharge 5-6. 30 ft säde: DC 17 WIS tai 8d6 psychic ja "
                   "Frightened vuoron loppuun (puolet onnistuneella, ei "
                   "pelkoa). Kohteet kuulevat oman pahimman tekonsa "
                   "sanottuna ääneen.",
                   0, "8d6", 0, "psychic", range=30, aoe_radius=30,
                   aoe_shape="sphere", applies_condition="Frightened",
                   condition_save="Wisdom", condition_dc=17),
        ],
        bonus_actions=[
            Action("Siunaava kosketus",
                   "Bonustoiminto: Ianus 'siunaa' Charmed-kohteen. Kohde "
                   "menettää 2d8 HP ja Ianus paranee saman verran; kohde "
                   "kokee sen lämpönä eikä huomaa mitään "
                   "(ei pelastusheittoa Charmed-tilassa).",
                   0, "2d8", 0, "necrotic", range=5, action_type="bonus"),
        ],
        reactions=[
            Action("Counterspell",
                   "Reaktio: peruuttaa loitsun (DC 17 kun taso on "
                   "korkeampi kuin slotti).",
                   0, "", 0, "", action_type="reaction", range=60),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=20),
                    mechanic="regeneration", mechanic_value="20"),
            _vampire_weaknesses(),
            _corrupted_divinity("Hänen rippinsä ei anna anteeksi vaan "
                               "sitoo: jokainen tunnustus antaa hänelle "
                               "otteen kohteeseen."),
            Feature("Elävän naamio",
                    "Ianus SYÖ, hengittää näkyvästi, käy päivämessussa "
                    "verhotussa kirkossa ja hänellä on lämmin kädenpuristus "
                    "(hän juo verta juuri ennen). Insight- tai "
                    "Medicine-tarkistus hänen tunnistamiseksi on DC 25. "
                    "Detect Evil and Good ja See Invisibility EIVÄT "
                    "paljasta häntä — vain peili, kynnys tai auringonvalo. "
                    "PELINJOHTAJALLE: hän on tarkoitettu sosiaaliseksi "
                    "kohtaamiseksi, ei taisteluksi. Anna pelaajien "
                    "epäonnistua tunnistamisessa ainakin kertaalleen.",
                    feature_type="passive"),
            Feature("Ei kynnystä ilman kutsua",
                    "Kuten kaikki todelliset vampyyrit, Ianus ei voi astua "
                    "asuintaloon kutsumatta. Hän on hoitanut tämän "
                    "kutsuttamalla itsensä sisään pappina — mutta pelaajien "
                    "leiri, vaunu tai vuokrattu huone on turvassa, jos he "
                    "eivät kutsu häntä.",
                    feature_type="passive"),
            Feature("Misty Escape",
                    "Kun hän putoaa 0 HP:hen, hän muuttuu sumuksi eikä "
                    "tuhoudu: pakenee temppelin kryptan arkkuunsa ja elpyy "
                    "1 HP:llä 2 tunnissa. Hänet voi tappaa lopullisesti "
                    "vain arkussa, lamaantuneena, vaarna sydämeen.",
                    feature_type="passive"),
            Feature("Katuva sana", "Recharge 5-6.", recharge="5-6"),
            Feature("Reaktio: Counterspell", "Ks. reaktiot.",
                    feature_type="reaction"),
            Feature("Spider Climb", "Kiipeää pinnoilla ja katossa."),
            Feature("Legendaarinen: Kuiskaus",
                    "Legendaarinen toiminto (1): yksi Charmed-kohde 60 ft "
                    "sisällä käyttää reaktionsa siirtyäkseen Ianuksen "
                    "eteen ja ottaa hänelle tarkoitetun osuman.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Sumuaskel",
                    "Legendaarinen toiminto (1): muuttuu hetkeksi sumuksi "
                    "ja liikkuu 30 ft provosoimatta, myös rakojen läpi.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Tunnusta",
                    "Legendaarinen toiminto (2): yksi olento 30 ft sisällä "
                    "tekee DC 17 WIS -pelastuksen tai kertoo ääneen yhden "
                    "salaisuutensa ja ottaa 4d6 psychic.",
                    feature_type="legendary", legendary_cost=2,
                    damage_dice="4d6", damage_type="psychic", save_dc=17,
                    save_ability="Wisdom"),
        ],
        legendary_action_count=2, legendary_resistance_count=1,
        items=[
            Item("Rippikaapu", item_type="armor", slot="armor",
                 equipped=True, rarity="uncommon", armor_category="light",
                 base_ac=13,
                 description="Puhdas kulta-musta kaapu. Hihansuut ovat "
                             "tahrattomat, koska hän on huolellinen."),
            Item("Aurinko-pääkallo -medaljonki (aito)", item_type="amulet",
                 slot="amulet", equipped=True, rarity="uncommon",
                 description="Hänen medaljonkinsa on kiillotettu ja aito — "
                             "hän kestää sitä, koska hänen uskonsa ei "
                             "koskaan ollutkaan aitoa."),
            Item("Rippikirja", item_type="wondrous", equipped=True,
                 rarity="rare",
                 description="Jokaisen Pinwudin asukkaan tunnustukset. "
                             "Aseeksi kelpaava kiristysmateriaali — ja "
                             "todiste siitä, kuka on jo hänen otteessaan."),
        ],
        lore="Confessor Ianus otti vastaan Pinwudin ripit. Dimerius ei "
             "käännyttänyt häntä väkisin: Ianus pyysi sitä itse, kun "
             "kuuli tarpeeksi monta kuolemanpelkoa. Hän on ainoa "
             "kääntyneistä joka esiintyy yhä elävänä, ja siksi hän on "
             "vaarallisin — hän on se joka lähetetään puhumaan pelaajien "
             "kanssa, ja hän auttaa heitä vilpittömän oloisesti väärään "
             "suuntaan.",
        tactics="ENSIN sosiaalinen kohtaaminen: hän tarjoutuu auttamaan, "
                "kertoo tosia asioita ja ohjaa ryhmän pois kryptasta. "
                "Ripin sinetti yhteen pelaajaan heti kun saa tämän "
                "kahden kesken. Taistelussa: Greater Invisibility, "
                "Counterspell kaikkeen, Katuva sana kun ryhmä kokoontuu, "
                "ja Kuiskaus-legendaarinen pakottaa Charmed-pelaajan "
                "ottamaan iskut. 0 HP:ssä Misty Escape — hän EI kuole "
                "ensimmäisessä taistelussa, ja sen on tarkoitus turhauttaa.",
        loot_table="Rippikirja (koko kylän salaisuudet), aito medaljonki, "
                   "kryptan avain, kirjeenvaihto jossa Dimeriuksen sinetti.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=10.0, xp=5900,
        proficiency_bonus=4,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 11 — MAGISTER SANGUINIS VHALTOR — kirjaston apulainen
    # ================================================================= #
    CreatureStats(
        name="Magister Sanguinis Vhaltor", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Neutral Evil", armor_class=17,
        armor_type="Mage Armor + luonnollinen panssari",
        hit_points=144, hit_dice="17d8+68", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=13, dexterity=17, constitution=18,
                                intelligence=20, wisdom=16, charisma=16),
        saving_throws={"Intelligence": 9, "Constitution": 8, "Wisdom": 7},
        skills={"Arcana": 13, "History": 13, "Religion": 9,
                "Investigation": 13, "Perception": 7},
        senses="Darkvision 120 ft., Passive Perception 17",
        languages="Common, Celestial, Abyssal, Deep Speech, Draconic",
        damage_resistances=["necrotic", "cold",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Charmed", "Frightened"],
        spellcasting_ability="Intelligence", spell_save_dc=17,
        spell_attack_bonus=9,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2,
                     "6th": 1},
        spell_names=["Mage Armor", "Shield", "Silvery Barbs",
                     "Misty Step", "Mirror Image", "Counterspell",
                     "Animate Dead", "Vampiric Touch", "Blight",
                     "Shadow of Moil", "Danse Macabre", "Enervation",
                     "Contagion", "Cloudkill", "Summon Shadowspawn",
                     "Harm"],
        cantrip_names=["Toll the Dead", "Chill Touch", "Mind Sliver",
                       "Mage Hand"],
        actions=[
            Action("Multiattack",
                   "Yksi loitsu ja yksi Kynnet — tai x2 Kynnet",
                   0, "", 0, "", is_multiattack=True, multiattack_count=2,
                   multiattack_targets=["Kynnet", "Kynnet"]),
            Action("Kynnet",
                   "Melee. Osumalla Grappled (escape DC 15).",
                   9, "2d4+2d6", 1, "slashing", range=5,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=15),
            Action("Purenta",
                   "Melee lamaantuneeseen kohteeseen: 3d6 elinvoimaa pois, "
                   "Vhaltor paranee saman verran.",
                   9, "1d6+3d6", 1, "necrotic", range=5),
            Action("Epäpuhtaan kirjaston avaus",
                   "Recharge 5-6. Vhaltor lukee ääneen takavarikoidusta "
                   "nekroottisesta artefaktista: 20 ft säde 60 ft päässä, "
                   "DC 17 CON tai 10d6 necrotic ja kohteen max HP laskee "
                   "vahingon verran (puolet onnistuneella, ei max HP "
                   "-laskua). Kaikki alueella kuolleet nousevat "
                   "zombeina Vhaltorin komentoon seuraavan kierroksen "
                   "alussa.",
                   0, "10d6", 0, "necrotic", range=60, aoe_radius=20,
                   aoe_shape="sphere", condition_save="Constitution",
                   condition_dc=17),
        ],
        bonus_actions=[
            Action("Sivunkäännös",
                   "Bonustoiminto: Vhaltor vaihtaa yhden valmistellun "
                   "loitsun toiseen samalta tasolta (hän kantaa koko "
                   "kirjastoa päässään). Mekaanisesti: hän voi loitsia "
                   "minkä tahansa listansa loitsun ilman valmistelua.",
                   0, "", 0, "", action_type="bonus"),
        ],
        reactions=[
            Action("Counterspell", "Reaktio: peruuttaa loitsun.",
                   0, "", 0, "", action_type="reaction", range=60),
            Action("Silvery Barbs",
                   "Reaktio: pakottaa onnistuneen heiton uusiksi.",
                   0, "", 0, "", action_type="reaction", range=60),
        ],
        features=[
            Feature("Regeneration", _REGEN.format(n=20),
                    mechanic="regeneration", mechanic_value="20"),
            _vampire_weaknesses(),
            _corrupted_divinity("Hän ei ollut pappi vaan tutkija — ja "
                               "hänen mielestään kääntyminen oli paras "
                               "asia joka hänen tutkimukselleen on "
                               "tapahtunut."),
            Feature("Epäpuhdas kirjasto",
                    "Vhaltorilla on pääsy Thalgrumin takavarikoituihin "
                    "nekroottisiin artefakteihin. 3/päivä hän voi loitsia "
                    "yhden 5. tason tai matalamman nekromantialoitsun "
                    "ILMAN loitsupaikkaa, lukemalla suoraan artefaktista.",
                    feature_type="passive", uses_per_day=3),
            Feature("Sielut datana",
                    "Thalgrumin oppilas: Vhaltor tietää tarkalleen mitä "
                    "kohde on. Hän saa edun osumaheittoihin ja +2 "
                    "loitsu-DC:hen sitä olentotyyppiä vastaan, jota hän on "
                    "tutkinut (pelinjohtaja valitsee taistelun alussa — "
                    "yleensä ryhmän yleisin luokka).",
                    feature_type="passive"),
            Feature("Misty Escape",
                    "0 HP:ssä muuttuu sumuksi ja pakenee arkkuunsa "
                    "kirjaston alle; elpyy 1 HP:llä 2 tunnissa.",
                    feature_type="passive"),
            Feature("Epäpuhtaan kirjaston avaus", "Recharge 5-6.",
                    recharge="5-6"),
            Feature("Reaktio: Counterspell", "Ks. reaktiot.",
                    feature_type="reaction"),
            Feature("Spider Climb", "Kiipeää pinnoilla ja katossa."),
        ],
        items=[
            Item("Vhaltorin muistikirja", item_type="wondrous",
                 equipped=True, rarity="rare",
                 description="Vampyrismin muutokset kirjattuna tunneittain "
                             "— hänen omasta kääntymisestään. Tämä on "
                             "pelaajien paras vihje siitä, kuka kääntyi "
                             "ensin ja milloin."),
            Item("Takavarikoitu nekroottinen reliikki", item_type="wand",
                 slot="off_hand", equipped=True, rarity="very_rare",
                 requires_attunement=True, attuned=True,
                 description="Vigilin omasta 'epäpuhtaasta kirjastosta' "
                             "varastettu esine. Kolme latausta päivässä: "
                             "5. tason tai matalampi nekromantialoitsu "
                             "ilman loitsupaikkaa."),
        ],
        lore="Vhaltor oli Magister Librorum Thalgrumin apulainen ja "
             "vastasi takavarikoidusta 'epäpuhtaasta kirjastosta'. Hän "
             "käänsi itsensä tarkoituksella: hän halusi tietää miltä "
             "kuolemattomuus tuntuu sisältä ja kirjasi jokaisen tunnin. "
             "Thalgrum ei ole huomannut — tai ei välitä.",
        tactics="Kaukana, korkealla, mieluiten katonrajassa (Spider Climb). "
                "Kierros 1: Shadow of Moil (haitta osumiin, "
                "necrotic-vastaisku) + Mirror Image. Kierros 2: Epäpuhtaan "
                "kirjaston avaus ryhmän tiiviimpään kohtaan — max HP "
                "-lasku on se mikä tekee siitä pelottavan. Sen jälkeen "
                "Danse Macabre / Animate Dead kaatuneista. Counterspell ja "
                "Silvery Barbs reaktioina joka kierros. Ei koskaan tule "
                "lähitaisteluun; Misty Step pois heti jos joku pääsee "
                "viereen.",
        loot_table="Vhaltorin muistikirja, takavarikoitu nekroottinen "
                   "reliikki (very rare), kirjaston luettelo josta puuttuu "
                   "kolme sivua, Thalgrumin allekirjoittama lupa.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=11.0, xp=7200,
        proficiency_bonus=4,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 13 — PRAEFECTUS SANGUINIS OSTORIUS — infestaation johtaja
    # ================================================================= #
    CreatureStats(
        name="Praefectus Sanguinis Ostorius", size="Medium",
        creature_type="Undead", native_plane="Material",
        alignment="Lawful Evil", armor_class=19,
        armor_type="Vigilin levyhaarniska + Shield of Faith",
        hit_points=204, hit_dice="24d8+96", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=18, dexterity=16, constitution=18,
                                intelligence=14, wisdom=20, charisma=18),
        saving_throws={"Strength": 8, "Constitution": 9, "Wisdom": 10,
                       "Charisma": 9},
        skills={"Religion": 12, "Insight": 15, "Intimidation": 9,
                "Perception": 10, "Deception": 9},
        senses="Darkvision 120 ft., Passive Perception 20",
        languages="Common, Celestial, Abyssal",
        damage_resistances=["necrotic",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        condition_immunities=["Exhaustion", "Charmed", "Frightened",
                              "Poisoned"],
        spellcasting_ability="Wisdom", spell_save_dc=18,
        spell_attack_bonus=10,
        spell_slots={"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 3,
                     "6th": 1, "7th": 1},
        spell_names=["Inflict Wounds", "Command", "Shield of Faith",
                     "Silence", "Hold Person", "Spirit Guardians",
                     "Vampiric Touch", "Animate Dead", "Death Ward",
                     "Blight", "Contagion", "Danse Macabre",
                     "Dominate Person", "Enervation", "Harm",
                     "Finger of Death"],
        cantrip_names=["Toll the Dead", "Chill Touch", "Mage Hand",
                       "Mind Sliver"],
        actions=[
            Action("Multiattack",
                   "x3: Requiem-sauva tai Kynnet; yksi voidaan korvata "
                   "Elinvoiman purennalla",
                   0, "", 0, "", is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Requiem-sauva", "Kynnet",
                                        "Kynnet"]),
            Action("Requiem-sauva",
                   "Melee, Praefectuksen virkasauva. Osumalla kohde tekee "
                   "DC 18 CON -pelastuksen tai ei voi saada healingia "
                   "vuoronsa loppuun.",
                   10, "2d6+3d8", 4, "necrotic", range=5,
                   properties=["versatile"],
                   condition_save="Constitution", condition_dc=18),
            Action("Kynnet",
                   "Melee. Osumalla Grappled (escape DC 18).",
                   10, "2d6", 4, "slashing", range=5,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=18),
            Action("Elinvoiman purenta",
                   "Melee lamaantuneeseen kohteeseen: uhri menettää 4d6 "
                   "elinvoimaa (max HP laskee) ja Ostorius paranee saman "
                   "verran. Näin kuollut nousee vampyyrina hänen "
                   "komentoonsa — juuri näin koko temppeli kääntyi.",
                   10, "1d6+4d6", 4, "necrotic", range=5),
            Action("Hauta avautuu",
                   "Turmeltunut Channel Divinity, 3/päivä (Path to the "
                   "Grave väärinpäin): Ostorius merkitsee yhden olennon "
                   "30 ft sisällä. Seuraava osuma merkittyyn kohteeseen "
                   "tekee TUPLAVAHINGON — ja jos kohde on epäkuollut, se "
                   "sen sijaan paranee tuplasti. Ei pelastusheittoa.",
                   0, "", 0, "", range=30),
            Action("Verimessu",
                   "Recharge 5-6. Ostorius pitää messun: 30 ft säde, "
                   "DC 18 CON tai 8d8 necrotic ja kohde on Poisoned "
                   "minuutin (puolet onnistuneella). Ostorius ja kaikki "
                   "epäkuolleet 30 ft sisällä paranevat puolet "
                   "kokonaisvahingosta.",
                   0, "8d8", 0, "necrotic", range=30, aoe_radius=30,
                   aoe_shape="sphere", applies_condition="Poisoned",
                   condition_save="Constitution", condition_dc=18),
        ],
        bonus_actions=[
            Action("Isännän käsky",
                   "Bonustoiminto: yksi Ostoriuksen tekemä vampyyri 60 ft "
                   "sisällä käyttää reaktionsa tehdäkseen yhden iskun tai "
                   "siirtyäkseen ottamaan Ostoriukselle tarkoitetun osuman.",
                   0, "", 0, "", action_type="bonus", range=60),
        ],
        reactions=[
            Action("Sijaiskärsijä",
                   "Reaktio: kun Ostorius ottaisi vahinkoa, yksi hänen "
                   "tekemänsä vampyyri 30 ft sisällä ottaa sen sijaan "
                   "koko vahingon.",
                   0, "", 0, "", action_type="reaction", range=30),
        ],
        features=[
            Feature("Legendary Resistance",
                    "3/päivä: valitse onnistuvasi epäonnistuneessa "
                    "pelastusheitossa.",
                    feature_type="passive", uses_per_day=3),
            Feature("Regeneration", _REGEN.format(n=20),
                    mechanic="regeneration", mechanic_value="20"),
            _vampire_weaknesses(),
            _corrupted_divinity("Path to the Grave avaa haudan sen sijaan "
                               "että sulkisi sen, Sentinel at Death's Door "
                               "suojaa nyt epäkuolleita, ja Keeper of Souls "
                               "kerää elävien sielut hänelle itselleen."),
            Feature("Sentinel at Death's Door (käännetty)",
                    "Reaktio: Ostorius muuttaa kriittisen osuman "
                    "tavalliseksi osumaksi itseään tai yhtä hänen "
                    "vampyyriään vastaan. 5/päivä (WIS-modifikaattori).",
                    feature_type="reaction", uses_per_day=5),
            Feature("Keeper of Souls (käännetty)",
                    "Kun ELÄVÄ olento kuolee 60 ft sisällä, Ostorius "
                    "palauttaa 25 HP ja yhden käytetyn loitsupaikan "
                    "(max 5. taso).",
                    feature_type="passive"),
            Feature("Isäntä",
                    "Kaikki Ostoriuksen tekemät vampyyrit (Verikuoro, "
                    "Custos Nocturnus, Sanguis Custos, Medicus Sanguinis) "
                    "saavat +2 osumaheittoihin ja immuniteetin Frightenediin "
                    "60 ft säteellä hänestä. JOS OSTORIUS TUHOTAAN "
                    "LOPULLISESTI, hänen tekemänsä vampyyrit menettävät "
                    "tämän ja tekevät DC 15 WIS -pelastuksen tai pakenevat.",
                    aura_radius=60),
            Feature("Misty Escape",
                    "0 HP:ssä muuttuu verisumuksi eikä tuhoudu: pakenee "
                    "temppelin alttarin alle muurattuun arkkuunsa ja elpyy "
                    "1 HP:llä 2 tunnissa. Vain arkussa, lamaantuneena, "
                    "vaarna sydämeen tappaa lopullisesti. PELINJOHTAJALLE: "
                    "arkku on muurattu Vigilin oman alttarin sisään — "
                    "pelaajien on rikottava temppelinsä pyhin kohta.",
                    feature_type="passive"),
            Feature("Verimessu", "Recharge 5-6.", recharge="5-6"),
            Feature("Reaktio: Sijaiskärsijä", "Ks. reaktiot.",
                    feature_type="reaction"),
            Feature("Spider Climb", "Kiipeää pinnoilla ja katossa."),
            Feature("Children of the Night",
                    "1/päivä: kutsuu 3d6 lepakkoa tai rottaa (tai 3 sutta), "
                    "jotka saapuvat 1d4 kierroksessa.",
                    uses_per_day=1),
            Feature("Legendaarinen: Liike",
                    "Legendaarinen toiminto (1): liikkuu nopeutensa "
                    "provosoimatta.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Purenta",
                    "Legendaarinen toiminto (1): yksi Elinvoiman purenta "
                    "lamaantuneeseen kohteeseen.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Hauta avautuu",
                    "Legendaarinen toiminto (2): merkitsee kohteen "
                    "(tuplavahinko seuraavasta osumasta).",
                    feature_type="legendary", legendary_cost=2),
            Feature("Lair: Peitetyt ikkunat",
                    "Lair-toiminto (init 20), vain temppelissä: "
                    "surunauhat lehahtavat kaikkien ikkunoiden yli. "
                    "Kaikki auringonvalo katkeaa kierroksen ajaksi ja "
                    "temppeli on hämärä (haitta Perception-tarkistuksiin).",
                    feature_type="lair"),
            Feature("Lair: Alttarin kuiskaus",
                    "Lair-toiminto (init 20): temppelin oma alttari puhuu. "
                    "Kaikki elävät 30 ft sisällä alttarista tekevät DC 18 "
                    "WIS -pelastuksen tai ottavat 3d6 psychic ja kuulevat "
                    "oman kuolinpäivänsä.",
                    feature_type="lair"),
            Feature("Lair: Kryptan ovi",
                    "Lair-toiminto (init 20): kryptan ovi avautuu ja 4 "
                    "Verikuoron akolyyttiä saapuu kentälle 20 ft päähän "
                    "Ostoriuksesta.",
                    feature_type="lair"),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        items=[
            Item("Requiem-sauva", item_type="weapon", slot="main_hand",
                 equipped=True, rarity="very_rare", damage_dice="2d6+3d8",
                 requires_attunement=True, attuned=True,
                 description="Praefectus Purificatorumin virkasauva. "
                             "Kärjessä oleva aurinko-pääkallo on kääntynyt "
                             "ympäri niin että pääkallo on ylöspäin. "
                             "Osuma estää healingin."),
            Item("Vigilin levyhaarniska (Praefectus)", item_type="armor",
                 slot="armor", equipped=True, rarity="rare",
                 armor_category="heavy", base_ac=18, ac_bonus=1,
                 max_dex_bonus=0, stealth_disadvantage=True,
                 description="Kulta-musta, kaiverrettu virkahaarniska. "
                             "Sisäpuolelle on raavittu Dimeriuksen sinetti."),
            Item("Dimeriuksen sinettikirje", item_type="wondrous",
                 equipped=True, rarity="legendary",
                 description="\"Sinä pidät temppelin. Minä pidän kaupungin. "
                             "Kun keisari herää, me olemme jo sisällä.\" — "
                             "SUORA TODISTE siitä että Ravenstonen "
                             "vampyyrilordi on Vigilin sisällä. Tämä on "
                             "kampanjan käännekohta jos pelaajat saavat "
                             "sen Aurelialle tai Gaiukselle."),
            Item("Kryptan pääavain", item_type="key", equipped=True,
                 rarity="uncommon",
                 description="Avaa alttarin alle muuratun arkkuhuoneen."),
        ],
        lore="Ostorius oli Vigilin Praefectus Purificatorum Pinwudissa — "
             "keskijohtoa, kunnianhimoinen, ohitettu ylennyksissä kolmesti. "
             "Dimerius ei tarjonnut hänelle valtaa vaan AIKAA: ikuisuuden "
             "todistaa olevansa parempi kuin Aurelia Valtar. Hän kääntyi "
             "vapaaehtoisesti ja käänsi sitten temppelinsä ylhäältä alas "
             "— kuoro ensin, sitten yövartio, sitten lääkäri. Hän uskoo "
             "yhä palvelevansa järjestöä: hänen mielestään Death's Vigil "
             "on aina ollut väärässä siitä, kummalla puolella kuolemaa "
             "kannattaa seistä.",
        tactics="Ei tule esiin ennen kuin muut on kaadettu. Kierros 1: "
                "Spirit Guardians (necrotic-versio) + Shield of Faith, "
                "Isännän käsky bonustoimintona. Kierros 2: Hauta avautuu "
                "ryhmän kestävimpään hahmoon, sitten kaikki iskut siihen — "
                "tuplavahinko kolmella iskulla tappaa tason 10 hahmon. "
                "Verimessu kun ryhmä on koossa (parantaa myös hänen "
                "vampyyrinsä). Reaktiot: Sijaiskärsijä ja Sentinel joka "
                "kierros. 0 HP:ssä Misty Escape alttarin alle — pelaajien "
                "ON murrettava Vigilin oma alttari. Jos he tekevät sen, "
                "koko infestaatio hajoaa (Isäntä-aura katoaa).",
        loot_table="Requiem-sauva (very rare), Praefectuksen levyhaarniska, "
                   "DIMERIUKSEN SINETTIKIRJE (kampanjan käännekohta), "
                   "kryptan pääavain, 14 nimen lista jotka hän käänsi.",
        habitat="Pinwudin Vigil-temppeli", challenge_rating=13.0, xp=10000,
        proficiency_bonus=5,
        sources="Novus Somnium — Vigilin vampyyriongelma"),

    # ================================================================= #
    # CR 16 — SANCTUM ABOMINATIO — temppelin oma pyhäinjäännös noussut
    # ================================================================= #
    CreatureStats(
        name="Sanctum Abominatio", size="Huge", creature_type="Undead",
        native_plane="Material", alignment="Neutral Evil",
        armor_class=18, armor_type="Pyhitetty luu ja kulta",
        hit_points=252, hit_dice="24d12+96", speed=30, climb_speed=30,
        abilities=AbilityScores(strength=24, dexterity=12, constitution=20,
                                intelligence=8, wisdom=18, charisma=16),
        saving_throws={"Constitution": 11, "Wisdom": 10},
        skills={"Perception": 10, "Athletics": 13},
        senses="Blindsight 60 ft., Darkvision 120 ft., "
               "Passive Perception 20",
        languages="ymmärtää Common ja Celestial, ei puhu — vain messuaa",
        damage_resistances=["necrotic", "cold", "fire",
                            "bludgeoning, piercing, slashing from nonmagical "
                            "attacks"],
        damage_immunities=["poison"],
        condition_immunities=["Charmed", "Frightened", "Poisoned",
                              "Exhaustion", "Prone", "Blinded", "Deafened"],
        actions=[
            Action("Multiattack",
                   "x3: Reliikkikäsi tai Luupiiska", 0, "", 0, "",
                   is_multiattack=True, multiattack_count=3,
                   multiattack_targets=["Reliikkikäsi", "Luupiiska",
                                        "Luupiiska"]),
            Action("Reliikkikäsi",
                   "Melee (reach 15 ft), kymmenien pyhien luiden "
                   "yhteenkasvanut käsi. Osumalla Grappled (escape DC 19).",
                   12, "3d10", 7, "bludgeoning", range=15, reach=15,
                   applies_condition="Grappled", condition_save="Strength",
                   condition_dc=19),
            Action("Luupiiska",
                   "Melee (reach 20 ft), rukousnauhaksi punottu selkäranka.",
                   12, "2d8+2d6", 7, "necrotic", range=20, reach=20,
                   properties=["reach"]),
            Action("Kirottu messu",
                   "Recharge 5-6. Reliikki messuaa Vigilin omalla "
                   "kuolinvirrellä: 60 ft säde, DC 19 WIS tai 12d8 psychic "
                   "ja Frightened minuutin (puolet onnistuneella, ei "
                   "pelkoa). Jokainen tähän kuoleva nousee seuraavan "
                   "kierroksen alussa Verikuoron akolyyttinä.",
                   0, "12d8", 0, "psychic", range=60, aoe_radius=60,
                   aoe_shape="sphere", applies_condition="Frightened",
                   condition_save="Wisdom", condition_dc=19),
            Action("Pyhäinjäännöksen nielu",
                   "Melee Grappled-kohteeseen: reliikki sulkee kohteen "
                   "sisäänsä. Kohde on Restrained, ei näe eikä kuule, ja "
                   "ottaa 6d10 necrotic vuoronsa alussa. DC 19 STR "
                   "irtoaa. Jos kohde kuolee sisällä, sen luut liittyvät "
                   "reliikkiin (Sanctum Abominatio saa 30 temp HP).",
                   12, "6d10", 7, "necrotic", range=5,
                   applies_condition="Restrained",
                   condition_save="Strength", condition_dc=19),
        ],
        features=[
            Feature("Legendary Resistance",
                    "3/päivä: valitse onnistuvasi epäonnistuneessa "
                    "pelastusheitossa.",
                    feature_type="passive", uses_per_day=3),
            Feature("Regeneration", _REGEN.format(n=20),
                    mechanic="regeneration", mechanic_value="20"),
            Feature("Pyhitetty runko",
                    "Reliikki on koottu Death's Vigilin omista pyhistä "
                    "luista, joten sen VASTUSTUS RADIANTILLE on "
                    "kaksiteräinen: radiant-vahinko ei sammuta sen "
                    "regeneraatiota (toisin kuin vampyyreillä), mutta "
                    "Vigilin oma pyhitetty ase (Requiem-terä, "
                    "-suurmiekka tai -sauva) tekee sille "
                    "TUPLAVAHINGON ja sammuttaa regeneraation. "
                    "PELINJOHTAJALLE: ratkaisu on ottaa kaatuneiden "
                    "vampyyripappien aseet käyttöön.",
                    feature_type="passive"),
            Feature("Auringonvalo ei pure",
                    "Tämä ei ole vampyyri vaan pyhäinjäännös. "
                    "Auringonvalo, kynnykset, juokseva vesi ja vaarnat "
                    "eivät vaikuta siihen mitään — älä anna pelaajien "
                    "luottaa vampyyrisuunnitelmaansa.",
                    feature_type="passive"),
            Feature("Kirottu messu", "Recharge 5-6.", recharge="5-6"),
            Feature("Siege Monster",
                    "Kaksinkertainen vahinko rakenteille. Reliikki "
                    "kaataa temppelin seinän jos se haluaa."),
            Feature("Legendaarinen: Luupiiska",
                    "Legendaarinen toiminto (1): yksi Luupiiska-isku.",
                    feature_type="legendary", legendary_cost=1),
            Feature("Legendaarinen: Rukous",
                    "Legendaarinen toiminto (2): kaikki epäkuolleet 60 ft "
                    "sisällä palauttavat 20 HP ja saavat edun seuraavaan "
                    "osumaheittoonsa.",
                    feature_type="legendary", legendary_cost=2),
            Feature("Legendaarinen: Nielu",
                    "Legendaarinen toiminto (2): yksi Pyhäinjäännöksen "
                    "nielu Grappled-kohteeseen.",
                    feature_type="legendary", legendary_cost=2),
            Feature("Lair: Katto romahtaa",
                    "Lair-toiminto (init 20): temppelin holvi murtuu. "
                    "20 ft säde, DC 19 DEX tai 6d10 bludgeoning ja "
                    "Prone; alue muuttuu vaikeaksi maastoksi. Jos ulkona "
                    "on päivä, romahdus päästää AURINGONVALON sisään — "
                    "kaikki vampyyrit alueella ottavat 20 radiant vuoron "
                    "alussa.",
                    feature_type="lair"),
        ],
        legendary_action_count=3, legendary_resistance_count=3,
        items=[
            Item("Vigilin pyhäinjäännösarkku (rikki)",
                 item_type="wondrous", rarity="artifact",
                 description="Se mistä reliikki nousi. Sisällä on 40 "
                             "vuosisadan aikana kerättyjä 'pyhiä kuolleita' "
                             "— järjestön perustajien luita. Ostorius "
                             "avasi arkun tarkoituksella."),
            Item("Kultapunottu rukousnauha", item_type="wondrous",
                 rarity="very_rare",
                 description="Selkärangasta ja kullasta punottu nauha, "
                             "jota reliikki käyttää piiskana. Puhdistettuna "
                             "(Greater Restoration + 8 h rituaali) siitä "
                             "tulee +2 pyhitetty ase epäkuolleita vastaan."),
        ],
        lore="Death's Vigil on kerännyt neljänsadan vuoden ajan omien "
             "pyhiensä luut Pinwudin temppelin alle. Ostorius avasi arkun "
             "todistaakseen pointtinsa: jos järjestö on oikeassa siitä että "
             "kuolema on pyhä, sen omat pyhät eivät nouse. Ne nousivat. "
             "Sanctum Abominatio on nyt kymmenien pyhien miesten "
             "yhteenkasvanut ruumis, joka messuaa yhä oikeat rukoukset "
             "väärään suuntaan — ja se on teologinen katastrofi, ei vain "
             "hirviö.",
        tactics="Boss vain jos pelinjohtaja haluaa ison lopun. Ei liiku "
                "paljon: reach 20 ft ja legendaariset riittävät. Kierros 1: "
                "Kirottu messu heti (12d8 psychic koko ryhmälle). Sen "
                "jälkeen Reliikkikäsi grapplaa kestävimmän ja "
                "Pyhäinjäännöksen nielu sulkee sen sisäänsä — se on "
                "kohtaamisen kellon käynnistys. Legendaarinen Rukous "
                "nostaa kaikki muut vampyyrit takaisin. Muista että "
                "auringonvalo EI auta tähän: pelaajien on tajuttava "
                "käyttää kaatuneiden pappien Requiem-aseita "
                "(tuplavahinko + regeneraatio sammuu).",
        loot_table="Rikkinäinen pyhäinjäännösarkku, kultapunottu "
                   "rukousnauha (puhdistettuna +2 ase epäkuolleita "
                   "vastaan), järjestön perustajien nimikilvet — Vigilin "
                   "koko historia todisteena siitä, että he olivat väärässä.",
        habitat="Pinwudin Vigil-temppelin krypta",
        challenge_rating=16.0, xp=15000, proficiency_bonus=5,
        sources="Novus Somnium — Vigilin vampyyriongelma"),
]
