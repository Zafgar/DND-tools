"""Novus Somnium — Cunaen mantereen canon-lore (laajennusdata).

Tämä moduuli kantaa kampanjan *varsinaisen* maailmankuvan: Cunaen
mantereen viisi suurvaltaa kaupunkeineen, Aterterran Underdark-kaupungit,
itsenäiset kohteet sekä keskeiset NPC:t (ulkonäkö, motiivit, stat-linkit
ja suhdeverkosto) ja salaseurat.

Data on jäsennelty taulukoiksi (``CITIES``, ``NPCS``, ``NPC_LINKS``) ja
rakennetaan World-/Kingdom-/Organisation-objekteiksi build-funktioilla,
jotka ``data.novus_somnium`` kutsuu kampanjaa generoidessaan. Kaikki on
*additiivista* — alkuperäinen testeillä lukittu starter-sisältö (Arenhold,
Vardun Keep, Frandin starter-NPC:t) säilyy ennallaan.

Suunnittelu:
  * Stat-blockit linkitetään ``stat_source = "monster:<Nimi>"`` -muodolla
    olemassa olevaan hirviökirjastoon (data/monsters). Kun täsmällistä
    vastinetta ei ole, käytetään lähintä proxya ja kirjataan tarkka
    luokitus ``notes``-kenttään.
  * Pelaajahahmot (PC:t) tallennetaan NPC-tietueina tagilla
    ``player_character`` jotta suhdegraafi ja NPC-hakemisto näkevät heidät
    ja suhdelinkit ratkeavat molempiin suuntiin.
"""
from __future__ import annotations

from typing import Dict, List


# Kingdom country-location ids luodaan data.novus_somnium._build_world():ssä
# muodossa loc_<key>. Underdark-kaupungit ripustetaan Aterterran alle.
KINGDOM_LOC = {
    "tarmaas":   "loc_tarmaas",
    "fundarla":  "loc_fundarla",
    "smardu":    "loc_smardu",
    "aterterra": "loc_aterterra",
    "oblitus":   "loc_oblitus",
}


# --------------------------------------------------------------------- #
# CITIES — (key, name, kingdom, loc_id, type, population, biome,
#           industry, religion, ruler_npc_id, is_capital, description)
# kingdom == "" → itsenäinen (top-level) kohde.
# --------------------------------------------------------------------- #
CITIES: List[dict] = [
    # ---- TARMAAS (teknologia & teollisuus) -------------------------
    dict(key="old_vaisil", name="Old Vaisil", kingdom="tarmaas",
         loc_id="loc_old_vaisil", type="port", population=80_000,
         biome="coast", industry="merenkulku, kauppa & sota",
         religion="Auringonkirkko", ruler="npc_efauxer",
         description="Tarmaaksen eteläkärjen loisteliaan kaunis, "
                     "arabityylinen satama- ja eläkekaupunki (~80 000 as.) "
                     "— nyt Vapaan Etelän Koalition taloudellinen ja "
                     "aatteellinen sydän ja mantereenlaajuisen sodan "
                     "hermokeskus. Irtautui Tarmaaksesta yhdessä Aesican ja "
                     "Maclebar Islen kanssa, katkaisten Tarmaas–Oblitus "
                     "-kauppareitit. Satamassa massiivinen rekrytointi; "
                     "hirttoaukiolla jaetaan armotonta oikeutta orjakaupasta "
                     "ja korruptiosta. Uhkina Chrith Lar -huumekriisi, "
                     "Kraken satamassa, vakoojat/salamurhaajat ja "
                     "pakolaisvirrat.",
         demographics={"Human": 30, "Dwarf": 20, "Halfling": 20,
                       "Half-Orc": 10, "Other": 20}),
    dict(key="ravenstone", name="Ravenstone", kingdom="tarmaas",
         loc_id="loc_ravenstone", type="city", population=14_000,
         biome="grim", industry="savikaivokset",
         religion="Avarath-kultti (kasvava)", ruler="npc_jugorai",
         description="Ulospäin sivistynyt satamakaupunki ja Asylum Purgo "
                     "-parantolan koti — todellisuudessa Pää Codexin "
                     "vakavimpien rikkomusten (nekromantia) keskus. "
                     "Kolmen rintaman sota: vampyyrien sisällissota "
                     "(paroni Jugorai vs. muinainen Dimerius Blackfeet), "
                     "alamaailma (Cora 0 + drow-liittolaiset) vs. "
                     "vampyyrit, ja laki vs. korruptio (E.F.I.). Ghouleja "
                     "vaeltaa kaduilla; savikaivannot (Clay Shore) ja "
                     "kasvava Avarath-kultti. Jos rikkomuksista saadaan "
                     "todisteet, kaupunki voidaan julistaa 'Kirotuksi "
                     "maaksi' → Death's Vigil polttaa sen."),
    dict(key="vilemour", name="Vilemour", kingdom="tarmaas",
         loc_id="loc_vilemour", type="city", population=9_000,
         biome="forest_edge", industry="fey-aarteet",
         religion="Brotherhood of Glorious Sun (salaa)", ruler="npc_varros",
         description="\"Sumumetsän portti\" Bladvine-metsän länsilaidalla. "
                     "Läpimätä \"riski → rikkauksia\" -kaupunki, ympäröity "
                     "tervahaudoilla ja palisadilla. Ihmisiä katoaa "
                     "Veljeskunnan biokoe-laboratorioon, jossa heistä "
                     "tehdään Spore Thralleja. Alla lymyää drow-tiedustelija "
                     "Xalyth."),
    dict(key="veksla", name="Veksla", kingdom="tarmaas",
         loc_id="loc_veksla", type="village", population=3_800,
         biome="farmland", industry="maatalous",
         religion="Aghuant (temppeli suljettu)", ruler="npc_artur_potvark",
         description="Bladvine-metsän ja viljelysten rajalla oleva "
                     "maatalouskaupunki (~3 800 as., ihmisiä 80 %, "
                     "puolituisia 15 %). Toipuu 'Night of the Heart' "
                     "-verilöylystä: nekromantikko Fauster nostatti "
                     "epäkuolleita ja yli 1 200 kuoli tai pakeni (sankarit "
                     "Kaldir & Ailas pysäyttivät hänet). Pellot täynnä "
                     "nekroottisia arpia, Aghuantin temppeli naulattu umpeen. "
                     "Paroni Artur Potvark on veloissa ja poissa pelistä; "
                     "hallitsee väliaikainen Vanhimpien Neuvosto + Metsän "
                     "Suojelijat. Vartiosto tuhottu, metsän nälkäiset olennot "
                     "hyökkäävät.",
         demographics={"Human": 80, "Halfling": 15, "Other": 5}),
    dict(key="hijoin", name="Hijoin", kingdom="tarmaas",
         loc_id="loc_hijoin", type="town", population=6_000,
         biome="mountain_slope", industry="arkeologia & tutkimus",
         religion="Auringonkirkko", ruler="npc_carl_gronmort",
         description="Arkeologinen kaivauskaupunki Gregbagne-vuorijonon "
                     "länsirinteellä. Maineikas C.H.O.M.P.-tutkimuskeskus. "
                     "Kreivin ja tutkijoiden konflikti; kaivossortumia, "
                     "kadonneita ryhmiä ja saastunutta kaivovettä "
                     "(syynä Beholder Oomag)."),
    dict(key="fat_carp", name="Fat Carp", kingdom="tarmaas",
         loc_id="loc_fat_carp", type="port", population=1_500,
         biome="coast", industry="kalastus",
         religion="Aaltojen kirkko", ruler="npc_beur",
         description="Rannikkokylä/satama. Kylään tuodaan \"hoidettavaksi\" "
                     "Oblituksen Chrith Lar -huumeen käyttäjiä. Veljeskunta "
                     "lavastaa terrori-iskun haltioiden (Fundarlan armeijan) "
                     "syyksi."),
    dict(key="pinwud", name="Pinwud", kingdom="tarmaas",
         loc_id="loc_pinwud", type="village", population=900,
         biome="forest", industry="puunhakkuu",
         religion="Death's Vigil -temppeli", ruler="npc_gaius_marad",
         description="Puunhakkaajien ja puolituisten metsäkylä, jossa on "
                     "Death's Vigilin temppeli. Metsänhenget hyökkäävät "
                     "liiallisen hakkuun vuoksi."),
    dict(key="arist", name="Arist", kingdom="tarmaas",
         loc_id="loc_arist", type="town", population=4_500,
         biome="forest_edge", industry="kauppa & metsästys",
         religion="Auringonkirkko", ruler="npc_cyra_nesh",
         description="Sumumetsän eteläinen kauppakaupunki, \"Fey Hunter's "
                     "Lodgen\" koti."),
    dict(key="baltimon", name="Baltimon", kingdom="tarmaas",
         loc_id="loc_baltimon", type="village", population=1_200,
         biome="farmland", industry="viljely", religion="Auringonkirkko",
         ruler="",
         description="Viljelykylä, joka kärsii \"kasvirutosta\": "
                     "salaperäinen voima imee elinvoimaa maasta."),
    dict(key="zaprutas", name="Zaprutas", kingdom="tarmaas",
         loc_id="loc_zaprutas", type="village", population=800,
         biome="underground", industry="kaasu & insinöörityö",
         religion="—", ruler="npc_zapui",
         description="Maanalainen gnomi-yhteisö. Kivihirviöt sabotoivat "
                     "heidän kaasulinjojaan."),

    # ---- OBLITUS (aavikot, heimot & orjakauppa) --------------------
    dict(key="iklence", name="Iklence", kingdom="oblitus",
         loc_id="loc_iklence", type="city", population=60_000,
         biome="desert", industry="orjakauppa (Red Drob)",
         religion="Veru-kultti", ruler="npc_emnar", is_capital=True,
         description="Massiivinen muurikaupunki Oblituksen sydämessä, "
                     "Vihreän Armeijan vartioima. Kuningas Emnar Redfei "
                     "kerää sieluja (Veru-projekti) ja pitää vihreää "
                     "lohikäärme Mueglorisia vankinaan."),
    dict(key="aesica", name="Aesica", kingdom="oblitus",
         loc_id="loc_aesica", type="port", population=50_000,
         biome="coast", industry="satama, gladiaattoriareena & kapina",
         religion="Aghuant", ruler="npc_krusk",
         description="Oblituksen massiivinen ja vilkas satamakaupunki "
                     "meren rannalla (~50 000 as.): sulatusuuni örkeille "
                     "(50 %), puoliörkeille (20 %), gobliineille (10 %) ja "
                     "vähemmistöille. Tunnettiin julmasta "
                     "gladiaattorikulttuuristaan ja orjakaupastaan "
                     "(kreivi Erokme Belmudar). Areenan (Nak Magnok Kor "
                     "Adez) alla on Convergence Engine -sielukone. Kaupunki "
                     "kävi juuri läpi verisen kapinan: Belmudar syöstiin "
                     "vallasta, nyt sulkutila (martial law) ja osa Vapaan "
                     "Etelän Koalitiota. Kaduilla vapautetut orjat jakavat "
                     "veristä omankädenoikeutta.",
         demographics={"Orc": 50, "Half-Orc": 20, "Goblin": 10,
                       "Human": 8, "Elf": 4, "Other": 8}),
    dict(key="aklobar", name="Aklobar / Anyar Nauo", kingdom="oblitus",
         loc_id="loc_aklobar", type="ruins", population=1_500,
         biome="desert", industry="tyynyt (!)", religion="—",
         ruler="npc_borbelio",
         description="Vanha hylätty linnoitus, jota gobliinit rakentavat "
                     "uudelleen. Entinen johtaja Borbelio Suuri myi Chrith "
                     "Laria Fadom Jivfutille; uusi hallinto on \"Council of "
                     "Cushions\" ja kylä myy nyt tyynyjä."),
    dict(key="pulker", name="Pulker", kingdom="oblitus",
         loc_id="loc_pulker", type="village", population=1_100,
         biome="desert", industry="maatalous", religion="Aghuantin temppeli",
         ruler="npc_wok",
         description="Maatalouskaupunki, joka kärsii sadon menetyksestä ja "
                     "rotista. Kuunvaihteessa sumuhirviöt hyökkäävät "
                     "Aghuantin temppelin läheisyydessä."),
    dict(key="kravok", name="Kravok", kingdom="oblitus",
         loc_id="loc_kravok", type="village", population=700,
         biome="swamp", industry="kalastus", religion="—",
         ruler="npc_longtongue",
         description="Sammakkokansan suokylä. Vanhimman poika kaapattu "
                     "Svik Fethen (korppiolento) toimesta; Fadom Jivfut on "
                     "piilottanut räjähteitä kylän temppeliin."),
    dict(key="tukor_sheg", name="Tukor Sheg", kingdom="oblitus",
         loc_id="loc_tukor_sheg", type="camp", population=600,
         biome="desert", industry="—", religion="—", ruler="npc_nogjat",
         description="Leiri lähellä Aesicaa. Orjakauppiaat (Red Drob) "
                     "riivaavat leiriä; se varustautuu aseilla Aesican "
                     "kapinan tueksi."),

    # ---- FUNDARLA (magia & haltiat) --------------------------------
    dict(key="zlalens", name="Zlalens", kingdom="fundarla",
         loc_id="loc_zlalens", type="city", population=55_000,
         biome="magical", industry="magia & pankkitoiminta",
         religion="Lehtoäidin polku", ruler="npc_endail", is_capital=True,
         description="Magian kehto ja Fundarlan sydän. Keskellä massiivinen "
                     "15 m lentokristalli, johon Dath pumppaa sieluenergiaa "
                     "nostaakseen koko kaupungin ilmaan sota-alukseksi. "
                     "Täällä myös Cunaen suurin pankki, Golden Leaf Bank."),
    dict(key="asmenor", name="Asmenor", kingdom="fundarla",
         loc_id="loc_asmenor", type="city", population=20_000,
         biome="forest", industry="puunhoito & magia",
         religion="Shanta-temppeli", ruler="npc_hailaf",
         description="Kolmen massiivisen puun runkoon ja latvoihin "
                     "rakennettu haltioiden kaupunki. Muukalaisvihaa, "
                     "levottomia metsäneläimiä ja saastunutta vettä."),
    dict(key="cifiri", name="Cifiri", kingdom="fundarla",
         loc_id="loc_cifiri", type="port", population=16_000,
         biome="coast", industry="merikauppa",
         religion="Aaltojen kirkko", ruler="npc_runlian",
         description="Puhdas ja kaunis satamakaupunki. Hanons Oldarfok "
                     "yrittää syrjäyttää virkamies Dafounin; alueella "
                     "kidnappauksia laboratoriokokeita varten."),
    dict(key="faharn", name="Faharn", kingdom="fundarla",
         loc_id="loc_faharn", type="city", population=18_000,
         biome="forest", industry="oppineisuus & akatemia",
         religion="Lehtoäidin polku", ruler="npc_nimri",
         description="Puun latvoihin rakennettu vihreä kaupunki, "
                     "Saideneria-akatemian koti (Nimri Greentop). Metsä "
                     "tekee kuolemaa pohjoisessa, kahdeksanjalkaiset olennot "
                     "ryömivät koteihin."),

    # ---- SMARDU (kääpiöt & lohikäärmeet) ---------------------------
    dict(key="juamore", name="Juamore", kingdom="smardu",
         loc_id="loc_juamore", type="city", population=48_000,
         biome="mountain", industry="laki & diplomatia",
         religion="Vasaran veljeskunta", ruler="npc_braimir",
         is_capital=True,
         description="Smardun pääkaupunki, lakien ja diplomatian keskus. "
                     "Hallitsee Kymmenneuvosto (Braimir Burldair, Thesia "
                     "Runeveil, Peokra Unroltrumm). Täällä säilytetään "
                     "Codex Rauken -lakikiveä."),
    dict(key="antanard", name="Antanard", kingdom="smardu",
         loc_id="loc_antanard", type="city", population=30_000,
         biome="volcanic", industry="tuotanto & lohikäärmehautomo",
         religion="Vasaran veljeskunta", ruler="npc_jogra",
         description="Massiivisen geysiirin päälle Efouset-vuoristoon "
                     "rakennettu tuotannon keskus. Sisältää Unhael Scale "
                     "Rider -hautomolaitoksen, jossa kasvatetaan "
                     "lohikäärmeitä (PC Magnus on kotoisin täältä)."),
    dict(key="hifrom", name="Hifrom", kingdom="smardu",
         loc_id="loc_hifrom", type="town", population=5_000,
         biome="mountain", industry="kaivostoiminta",
         religion="Vasaran veljeskunta", ruler="npc_enquars",
         description="Vuoristokaupunki, jonne on alkanut saapua "
                     "ilkikurisia, pahantahtoisia olentoja vuorelta."),

    # ---- ATERTERRA (Underdark, drow) — ripustetaan loc_aterterran alle
    dict(key="zertath_lanke", name="Zer'tath Lanke", kingdom="aterterra",
         loc_id="loc_zertath_lanke", type="city", population=40_000,
         biome="underdark", industry="hallinto & magia",
         religion="Hämähäkkikuningattaren kultti", ruler="npc_cazna",
         is_capital=True,
         description="\"Kristallijärven kaupunki\", suoraan Frandin alla. "
                     "Aterterran poliittinen sydän; matriarkan palatsi "
                     "lepää kristallijärven saarella. Sisältää "
                     "Aether-arkistot. Vartioi tietämättään maailmantitaani "
                     "Garruthaa Faerzress-kristallien avulla."),
    dict(key="vlyn_darahl", name="Vlyn'Darahl", kingdom="aterterra",
         loc_id="loc_vlyn_darahl", type="city", population=12_000,
         biome="underdark", industry="kauppa & sienifarmit",
         religion="—", ruler="npc_zekarra",
         description="\"Pinnan portti\" Ravenstonen/Frandin laitamien alla. "
                     "Drowien kauppakaupunki ja salainen reitti pintaan."),
    dict(key="neldrath_zol", name="Neldrath Zol", kingdom="aterterra",
         loc_id="loc_neldrath_zol", type="city", population=15_000,
         biome="underdark", industry="hopeakaivokset",
         religion="—", ruler="npc_urlryn",
         description="\"Hopeasavu\", Bladvine-metsän alla. Teollinen sydän "
                     "ja hopeakaivokset. Salainen orjien vapauttaja Talice "
                     "Vel'kath operoi täällä."),
    dict(key="ultrinnan", name="Ultrinnan", kingdom="aterterra",
         loc_id="loc_ultrinnan", type="castle", population=9_000,
         biome="underdark", industry="sotateollisuus", religion="—",
         ruler="npc_dantrag",
         description="\"Teräslinnoitus\" pohjois-Frandin alla. Velve Dro "
                     "-armeijan päämaja; sotapäällikkö Dantrag Dyrr "
                     "suunnittelee sotilasvallankaappausta pintamaailmaa "
                     "vastaan."),
    dict(key="vorzha", name="Vorzha", kingdom="aterterra",
         loc_id="loc_vorzha", type="city", population=8_000,
         biome="underdark", industry="vakoilu & salamurhat",
         religion="—", ruler="npc_nhilymra",
         description="\"Kuiskausten kaupunki\" Frandin viemäriverkoston "
                     "alla. Salamurhaajien ja tiedustelun (Shadow Puppets) "
                     "koti. Pelaajia tarkkaillaan täällä lakkaamatta."),
    dict(key="eryn_zalas", name="Eryn'Zalas", kingdom="aterterra",
         loc_id="loc_eryn_zalas", type="city", population=6_000,
         biome="underdark", industry="profetia", religion="Unenkulkijat",
         ruler="npc_ahlysra",
         description="\"Kristallimetsä\" Fundarlan haltiametsien alla. "
                     "Unenkulkijoiden temppeli, jossa profetiat tallentuvat "
                     "jättimäisiin Faerzress-kristalleihin."),
    dict(key="ithyl_quor", name="Ithyl'Quor", kingdom="aterterra",
         loc_id="loc_ithyl_quor", type="city", population=7_000,
         biome="underdark", industry="biomagia",
         religion="Hämähäkkikuningattaren kultti", ruler="npc_qilue",
         description="\"Seitin katedraali\" pohjois-Fundarlan alla. "
                     "Hämähäkinmuotoinen kaupunki, biologisen magian ja "
                     "metamorfoosien keskus."),
    dict(key="dro_khazun", name="Dro'Khazun", kingdom="aterterra",
         loc_id="loc_dro_khazun", type="castle", population=5_000,
         biome="underdark", industry="sotateollisuus", religion="—",
         ruler="npc_belgos",
         description="\"Pimeä linnoitus\" Efousetin alla, Smardun rajalla. "
                     "Ikuinen sotavyöhyke kääpiöiden (Antanard) ja drowien "
                     "välillä — mahdollisuus historialliseen rauhaan."),
    dict(key="kazrath_mor", name="Kazrath Mor", kingdom="aterterra",
         loc_id="loc_kazrath_mor", type="castle", population=4_000,
         biome="underdark", industry="orjakeräys", religion="—",
         ruler="npc_azzmere",
         description="\"Luiden linnoitus\" Aklobarin aavikon alla, "
                     "rakennettu muinaisen pedon luiden sisään. "
                     "Orjien keräyskeskus."),
    dict(key="zar_ghul", name="Zar'Ghul", kingdom="aterterra",
         loc_id="loc_zar_ghul", type="town", population=3_000,
         biome="underdark", industry="mustapörssi", religion="—",
         ruler="npc_malaggar",
         description="\"Kuoleman kauppala\" Oblituksen ja Fundarlan "
                     "rajalla. Underdarkin villin lännen mustapörssi — "
                     "täältä saa mitä tahansa laitonta."),
    dict(key="golgoth_inil", name="Golgoth-Inil / Velkyn Oloth",
         kingdom="aterterra", loc_id="loc_golgoth_inil", type="camp",
         population=1_500, biome="underdark", industry="—", religion="—",
         ruler="npc_drathir",
         description="Pakolaisleiri Vilemourin salaisen reitin (Tunneli 4) "
                     "alapuolella, jossa Veljeskunnan \"Spore Rot\" -ruton "
                     "tartuttamat drowt piileskelevät sillalla."),

    # ---- ITSENÄISET / RIIPPUMATTOMAT KOHTEET -----------------------
    dict(key="maclebar_isle", name="Maclebar Isle (Ma Fo)", kingdom="",
         loc_id="loc_maclebar", type="region", population=6_000,
         biome="island", industry="marmori & kalastus", religion="—",
         ruler="npc_richard_walker",
         description="Eteläinen, Walker-suvun hallitsema saari. Ulospäin "
                     "tunnettu laadukkaasta marmoristaan ja kalastajakylistä "
                     "(mm. Pearl Bay); todellinen sydän on pohjoiskärjen "
                     "Fort Whitestone."),
    dict(key="pearl_bay", name="Pearl Bay", kingdom="",
         parent="loc_maclebar", loc_id="loc_pearl_bay", type="village",
         population=1_200, biome="coast", industry="kalastus", religion="—",
         ruler="",
         description="Maclebar Islen rauhallinen kalastajakylä."),
    dict(key="fort_whitestone", name="Fort Whitestone (Silex Alpus)",
         kingdom="", parent="loc_maclebar", loc_id="loc_fort_whitestone",
         type="castle", population=300, biome="island",
         industry="korkeateknologinen tehdas & arkisto",
         religion="—", ruler="npc_blitz",
         description="Maclebar Islen pohjoiskärjen kallioilla lepäävä "
                     "linnake (vanha ydin: Silex Alpus). Ei pelkkä linna "
                     "vaan Walker-suvun vuosisatoja vanha tehdas, arkisto ja "
                     "ulottuvuuksien välinen tukikohta. Kellaritasot ovat "
                     "oma taskuulottuvuus, jonne on varastoitu 8000 Automata "
                     "Trooperia, Whitestone Colosseja ja sukellusveneitä — "
                     "kosmisen karanteenin armeija. Sisältää kosmisen kartan "
                     "(kristallikupu + Phlogiston). Liittyi Vapaan Etelän "
                     "Koalitioon."),
    dict(key="caldius", name="Caldius / Khro Kal", kingdom="",
         loc_id="loc_caldius", type="city", population=4_000,
         biome="underwater", industry="insinöörityö & merirosvous",
         religion="—", ruler="npc_duemor",
         description="Vedenalainen yhteiskunta Tarmaaksen edustalla. "
                     "Smardusta irtautuneet tiedemiehet elävät "
                     "sukellusveneissä ja ryöstävät laivoja kaasuttamalla "
                     "ne nukuksiin."),
    dict(key="aequitas_isle", name="Aequitas-saari", kingdom="",
         loc_id="loc_aequitas", type="region", population=2_000,
         biome="island", industry="lainkäyttö", religion="—",
         ruler="",
         description="Fundarlan rannikolta itään sijaitseva täysin "
                     "riippumaton manneralue, joka vartioi Cunaen Pää "
                     "Codexia. Saarella väkivalta ja valehtelu on "
                     "maagisesti mahdotonta; The Boundless -agentit "
                     "tuomitsevat maailman tasapainon rikkojat "
                     "Nullifikaatioon."),

    # ================================================================= #
    # LISÄYS — laajennus: puuttuvat kaupungit + ulottuvuudet
    # ================================================================= #

    # ---- TARMAAS ---------------------------------------------------- #
    dict(key="honpa", name="Honpa", kingdom="tarmaas",
         loc_id="loc_honpa", type="village", population=600,
         biome="forest", industry="metsästys & keräily",
         religion="Auringonkirkko", ruler="",
         description="Pieni metsänsisäinen kylä; E.F.I.-agentti Blitzin "
                     "kotikylä. On kärsinyt Auringon Veljeskunnan (Brotherhood) "
                     "hirviökokeista — kyläläisiä on kadonnut ja metsästä "
                     "ilmestyy epäluonnollisia petoja.",
         demographics={"Human": 85, "Halfling": 10, "Other": 5}),

    # ---- SMARDU ----------------------------------------------------- #
    dict(key="stein_festing", name="Stein Festing (Kivikaupunki)",
         kingdom="smardu", loc_id="loc_stein_festing", type="fortress",
         population=4_000, biome="ice", industry="sota & louhinta",
         religion="Jääkultti", ruler="npc_bodervak",
         description="Maelotin vuoren sisään louhittu jääjättien kaupunki, "
                     "jota komentaa jääjätti Bodervak. Tukikohta josta "
                     "käydään lakkaamatonta sotaa Smardun pohjoisia kaupunkeja "
                     "vastaan. Kylmä, brutaali ja käytännössä valloittamaton "
                     "linnoitus.",
         demographics={"Frost Giant": 60, "Goliath": 25, "Other": 15}),

    # ---- FUNDARLA --------------------------------------------------- #
    dict(key="nunamair", name="Nunamair", kingdom="fundarla",
         loc_id="loc_nunamair", type="city", population=18_000,
         biome="forest", industry="tieto & taikuus",
         religion="Oghma / tiedon jumalat", ruler="",
         description="Tiedon kaupunki, jossa sijaitsee Cunaen suurin "
                     "taikakirjasto sekä Academy of Deataris -velhokoulu — "
                     "Seekers of Demimaind -järjestön keskus. Loitsijoita, "
                     "tutkijoita ja arkistonhoitajia joka kadulla.",
         demographics={"High Elf": 55, "Human": 25, "Gnome": 15,
                       "Other": 5}),

    # ---- ATERTERRA (Underdark) -------------------------------------- #
    dict(key="sshamath_ul", name="Sshamath Ul (Tulen Kaupunki)",
         kingdom="aterterra", loc_id="loc_sshamath_ul", type="city",
         population=22_000, biome="lava", industry="mestariseppä­työ",
         religion="Tulen kultti", ruler="",
         description="Laavavirran äärelle rakennettu uskomattoman kuuma "
                     "mestariseppien kaupunki (Talo Torviir). Aterterran "
                     "parhaat asesepät takovat täällä adamantti- ja "
                     "faerzress-teräksiä sulan kiven hehkussa."),
    dict(key="ghaurath_tol", name="Ghaurath Tol (Tuhkan Torni)",
         kingdom="aterterra", loc_id="loc_ghaurath_tol", type="city",
         population=9_000, biome="volcanic", industry="sotaratsujen kesytys",
         religion="Xarann-papisto", ruler="",
         description="Tulivuoren kylkeen rakennettu kaupunki, jossa "
                     "Xarann-papit kesyttävät jättiliskoja sotaratsuiksi. "
                     "Tuhkan peittämät terassit ja liskotarhat."),
    dict(key="ilnauth_zen", name="Ilnauth Zen (Jään Kuiskaus)",
         kingdom="aterterra", loc_id="loc_ilnauth_zen", type="city",
         population=3_000, biome="ice", industry="karkotus & selviytyminen",
         religion="—", ruler="",
         description="Smardun vuorten alla sijaitseva äärimmäisen kylmä "
                     "jäinen kaupunki. Lainsuojattomien ja karkotettujen "
                     "yhteisö, jossa lämpö on arvokkaampaa kuin kulta."),
    dict(key="zekk_und", name="Zekk'Und", kingdom="aterterra",
         loc_id="loc_zekk_und", type="city", population=12_000,
         biome="underground", industry="timantti- & faerzress-louhinta",
         religion="—", ruler="",
         description="Taloudellisesti kriittinen timanttien ja sinisen "
                     "faerzress-kristallin kaivoskaupunki. Aterterran "
                     "rikkauden lähde ja jatkuvan valtakamppailun kohde."),
    dict(key="tharkozh_varr", name="Tharkozh-Varr", kingdom="aterterra",
         loc_id="loc_tharkozh_varr", type="city", population=5_000,
         biome="crystal", industry="kristallimagia",
         religion="Sangurii-mysteerit", ruler="",
         description="Syvyyden ytimessä sijaitseva kaupunki, joka on "
                     "kokonaan kasvanut kristallista. Asukkaina salaperäiset "
                     "Sangurii (kristallihaltiat), joiden kulttuuri on "
                     "muille drow'lle arvoitus."),
    dict(key="xullrae", name="Xullrae (Hämärän Vedet)",
         kingdom="aterterra", loc_id="loc_xullrae", type="port",
         population=8_000, biome="underground_sea", industry="merenkulku",
         religion="—", ruler="",
         description="Maanalaisen meren pinnalla kelluva kaupunki. "
                     "Laituripaaluille ja jättiläiskotiloiden kuorille "
                     "rakennettu satama, josta drow-alukset purjehtivat "
                     "pimeille vesille."),
    dict(key="quellan_dra", name="Quellan'Dra", kingdom="aterterra",
         loc_id="loc_quellan_dra", type="city", population=2_500,
         biome="underground", industry="turvapaikka",
         religion="—", ruler="",
         description="Piilotettu, rauhallinen sekayhteisö ja turvasatama "
                     "drow-puoliverisille ja pakolaisille. Harvinainen "
                     "paikka Aterterrassa, jossa matriarkkojen sääntö ei "
                     "yllä — vapauden saareke pimeydessä."),

    # ---- Maclebar Isle: kolmas kylä --------------------------------- #
    dict(key="ivory_hollow", name="Ivory Hollow", kingdom="",
         parent="loc_maclebar", loc_id="loc_ivory_hollow", type="village",
         population=900, biome="coast", industry="marmori & kalastus",
         religion="—", ruler="",
         description="Maclebar Islen toinen kalastaja- ja marmorikylä "
                     "Pearl Bayn rinnalla, Fort Whitestonen varjossa."),

    # ================================================================= #
    # ULOTTUVUUDET — omat ylätason valtakuntansa (kingdom="").
    # Realm ensin, sitten sen kaupungit parent-linkillä.
    # ================================================================= #

    # ---- CELESTE (High Heavens) ------------------------------------- #
    dict(key="celeste", name="Celeste (High Heavens)", kingdom="",
         loc_id="loc_celeste", type="plane", population=0,
         biome="celestial", industry="sielujen kierto", religion="Valo",
         ruler="",
         description="Taivaallinen ulottuvuus — valon, sielujen ja "
                     "jumalallisten olentojen valtakunta pilvien yläpuolella."),
    dict(key="aurea_porta", name="Aurea Porta", kingdom="",
         parent="loc_celeste", loc_id="loc_aurea_porta", type="city",
         population=0, biome="celestial", industry="sielujen vastaanotto",
         religion="Valo", ruler="",
         description="\"Aamunkynnyksen kaupunki\": kultaiset portit, joiden "
                     "läpi kuolleiden sielut otetaan vastaan ja punnitaan "
                     "Celesteen saapuessaan."),
    dict(key="arx_mnemosyne", name="Arx Mnemosyne", kingdom="",
         parent="loc_celeste", loc_id="loc_arx_mnemosyne", type="tower",
         population=0, biome="celestial", industry="tieto & muisti",
         religion="Valo", ruler="",
         description="\"Kirjojen kaupunki\" / muistin torni, johon on "
                     "tallennettu kaikkien elettyjen elämien muistot ja "
                     "maailman historia."),
    dict(key="gossamer_grove", name="Gossamer Grove", kingdom="",
         parent="loc_celeste", loc_id="loc_gossamer_grove", type="wilderness",
         population=0, biome="celestial_garden", industry="sielunkierto",
         religion="Valo", ruler="",
         description="Haltioiden sielunkierron puutarha — hopeanhohtoinen "
                     "lehto, jossa mennyt ja tuleva elämä kohtaavat."),

    # ---- INFERNAL DISC (9 Hells) ------------------------------------ #
    dict(key="infernal_disc", name="Infernal Disc (9 Hells)", kingdom="",
         loc_id="loc_infernal_disc", type="plane", population=0,
         biome="infernal", industry="sopimukset & sielukauppa",
         religion="Helvetin hierarkia", ruler="",
         description="Helvetin rengasmaailma — sopimusten, byrokratian ja "
                     "sieluvelkojen yhdeksänkehäinen ulottuvuus."),
    dict(key="brassharbor", name="Brassharbor", kingdom="",
         parent="loc_infernal_disc", loc_id="loc_brassharbor", type="city",
         population=0, biome="infernal", industry="pörssi & kolikkomintut",
         religion="Helvetin hierarkia", ruler="",
         description="Helvetin pörssi- ja rahapajakaupunki, jossa "
                     "sieluvelat noteerataan ja messinkikolikot lyödään."),
    dict(key="veilmire", name="Veilmire", kingdom="",
         parent="loc_infernal_disc", loc_id="loc_veilmire", type="city",
         population=0, biome="infernal", industry="sensuuri & vakoilu",
         religion="Helvetin hierarkia", ruler="",
         description="Sensuurin ja vakoilun sumukaupunki — jokainen kuiskaus "
                     "kuullaan ja arkistoidaan usvan verhossa."),
    dict(key="hingehold", name="Hingehold", kingdom="",
         parent="loc_infernal_disc", loc_id="loc_hingehold", type="city",
         population=0, biome="infernal", industry="porttien logistiikka",
         religion="Helvetin hierarkia", ruler="",
         description="Porttien logistiikkasolmu: kaikki kehien väliset "
                     "kulkuväylät ja saraviät kulkevat tämän kaupungin läpi."),
    dict(key="chainledger", name="Chainledger", kingdom="",
         parent="loc_infernal_disc", loc_id="loc_chainledger", type="city",
         population=0, biome="infernal", industry="sopimusarkistot",
         religion="Helvetin hierarkia", ruler="",
         description="Sopimusarkistojen kaupunki, jossa jokainen koskaan "
                     "solmittu helvetillinen sopimus säilytetään kahleisiin "
                     "sidottuina foliantteina."),

    # ---- REGNUM FATARUM (Feywild) ----------------------------------- #
    dict(key="regnum_fatarum", name="Regnum Fatarum (Feywild)", kingdom="",
         loc_id="loc_regnum_fatarum", type="plane", population=0,
         biome="feywild", industry="unet & sopimukset", religion="Fae-hovit",
         ruler="",
         description="Fae-olentojen valtakunta — unen, vuodenaikojen ja "
                     "arvaamattomien sopimusten arkkityyppinen ulottuvuus."),
    dict(key="pale_diadem", name="Pale Diadem", kingdom="",
         parent="loc_regnum_fatarum", loc_id="loc_pale_diadem", type="city",
         population=0, biome="feywild_winter", industry="talvihovi",
         religion="Fae-hovit", ruler="",
         description="Kullattu hallakaupunki — Talvihovin kimalteleva, "
                     "jäätävän kaunis valtaistuinkaupunki."),
    dict(key="bonehaven", name="Bonehaven", kingdom="",
         parent="loc_regnum_fatarum", loc_id="loc_bonehaven", type="city",
         population=0, biome="feywild", industry="kuoleman rituaalit",
         religion="Fae-hovit", ruler="",
         description="Nekropolis Feywildin sydämessä, jossa fae-kuolema "
                     "ja jälleensyntymä kietoutuvat yhteen."),
    dict(key="spindlehaven", name="Spindlehaven", kingdom="",
         parent="loc_regnum_fatarum", loc_id="loc_spindlehaven", type="port",
         population=0, biome="feywild_sea", industry="unimeren satama",
         religion="Fae-hovit", ruler="",
         description="Unimeren satama, josta fae-alukset purjehtivat "
                     "nukkuvien mielten ja tarinoiden meriä pitkin."),
]


# --------------------------------------------------------------------- #
# SUBLOCATIONS — rakennukset/tilat kaupunkien sisällä. Näistä syntyy
# vain World.Location (parent-linkillä), ei kuningaskunnan CityEntryä.
# (key, name, parent_loc_id, type, description)
# --------------------------------------------------------------------- #
SUBLOCATIONS: List[dict] = [
    dict(key="verkkojen_talo", name="Verkkojen Talo (Talo Baenrahelin "
                                     "palvelijoiden talo)",
         parent="loc_zertath_lanke", loc_id="loc_verkkojen_talo",
         type="building", biome="underdark",
         description="Talo Baenrahelin ulompi kartano, louhittu massiivisen "
                     "tippukiven sisään pääkartanon ja Aether-arkistojen "
                     "alapuolelle. Suvun konehuone: yhteiskeittiö, ahtaat "
                     "makuusalikolot, ratsuliskojen ja hämähäkkien tallit, "
                     "vartijoiden parakit. Valaistuksena säröilleet, "
                     "levotonta violettia hohtavat faerzress-sirpaleet; ilma "
                     "haisee otsonilta, paahdetulta sieneltä ja vanhalta "
                     "verelta. Alueella vallitsee 'Lex Null' — pysyvät "
                     "vaimennuskentät (loitsu vaatii CON-heiton DC 13 + "
                     "loitsun taso, epäonnistuessa force-vahinkoa), joten "
                     "täällä taistellaan myrkyin ja teräasein. Palvelijat "
                     "tuntevat kentän 'kuolleet kulmat', joissa magia yhä "
                     "toimii."),
    dict(key="nak_magnok", name="Nak Magnok Kor Adez (areena)",
         parent="loc_aesica", loc_id="loc_nak_magnok", type="building",
         biome="coast",
         description="Aesican jättimäinen gladiaattoriareena. Julkisesti "
                     "verinen viihdekeskus; sen alla sijaitsee Convergence "
                     "Engine -sielukone, joka imi kuolleiden gladiaattorien "
                     "sieluja. Uusi (opportunistinen) omistaja Julus Sanace "
                     "yrittää sopeutua kapinan jälkeiseen valtaan."),
    dict(key="gor_rash", name="Gor'Rash (satama-alue)",
         parent="loc_aesica", loc_id="loc_gor_rash", type="port",
         biome="coast",
         description="Aesican satama-alue, jota satamamestari Borug Skud "
                     "johti rautaisella otteella vanhan hallinnon rinnalla. "
                     "Salakuljetuksen ja merikaupan solmukohta."),
    dict(key="aghuant_temple", name="Aghuantin suuri temppeli",
         parent="loc_aesica", loc_id="loc_aghuant_temple", type="temple",
         biome="coast",
         description="Aesican hengellinen keskus, Aghuantin palvonnan "
                     "korkein pyhäkkö. Ylipappina gobliini Isä Dimerio Fao; "
                     "papisto pelastettiin kapinan aikana myrkytysyritykseltä."),
    # ---- Ravenstone (Tarmaas) sisäiset alueet ----------------------
    dict(key="asylum_purgo", name="Asylum Purgo", parent="loc_ravenstone",
         type="building", biome="grim", loc_id="loc_asylum_purgo",
         description="Koko Tarmaaksessa tunnettu \"mielisairaala\" ja "
                     "parantola — todellisuudessa julma ihmiskoelaboratorio. "
                     "Neuvosto käyttää sitä poistaakseen todistajia ja "
                     "\"puhdistaakseen\" muistoja; alimmilla tasoilla "
                     "ihmisistä valutetaan verta salaa Dimeriuksen "
                     "ruokkimiseksi. Johtajana sadistinen Greg Silverhand."),
    dict(key="corvus_spelchrum", name="Corvus Spelchrum (krypta)",
         parent="loc_ravenstone", type="dungeon", biome="grim",
         loc_id="loc_corvus_spelchrum",
         description="Muinainen krypta kaupungin alla. Sen "
                     "kynttiläkammioon on teljetty vampyyrilordi Dimerius "
                     "Blackfeet, joka odottaa heräämistään ja manipuloi "
                     "kaupunkia varjoista."),
    dict(key="profundus", name="Profundus (alamaailman kaupunki)",
         parent="loc_ravenstone", type="city", biome="underground",
         loc_id="loc_profundus",
         description="Salainen alamaailman kaupunki syvällä Ravenstonen "
                     "viemäriverkostossa. Rikollisjärjestö Cora 0:n "
                     "(Gaur Rakek) päämaja; valmistautuu sotaan "
                     "maanpäällisiä vampyyrejä vastaan. Täällä piileskelee "
                     "myös vampyyrinmetsästäjä Aksel Wolfbane."),
    dict(key="clay_shore", name="Clay Shore (savikaivannot)",
         parent="loc_ravenstone", type="port", biome="coast",
         loc_id="loc_clay_shore",
         description="Ravenstonen satama ja puhtaan saven kaivannot. "
                     "Aterterran drowt (Talo Despana) hakevat savea "
                     "ilmaiseksi ja suojaavat vastineeksi satamaa öisin "
                     "vampyyreilta. Kaivannoilla Avarath-kultti löysi "
                     "\"jotain, joka puhui syvyyksistä\"."),
    dict(key="avarath_temple", name="Avarathin temppeli",
         parent="loc_ravenstone", type="temple", biome="grim",
         loc_id="loc_avarath_temple",
         description="Vanha temppeli, jota Avarath-kultin munkit "
                     "rakentavat uusiksi. \"Jumala\" Avarath on "
                     "todellisuudessa muinainen Aboleth, joka pesee "
                     "palvojiensa mielet fanaattisiksi orjiksi vedenalaisesta "
                     "piilostaan sataman tuntumassa."),
    # ---- Fort Whitestone (Maclebar Isle) sisäiset alueet ------------
    dict(key="protocol_omega_vault", name="Protokolla Omega -holvi",
         parent="loc_fort_whitestone", type="room", biome="pocket_dimension",
         loc_id="loc_protocol_omega",
         description="Fort Whitestonen kellaritason taskuulottuvuus, jonne "
                     "on varastoitu 8000 Automata Trooperia, "
                     "Whitestone Colosseja ja sukellusveneita. Armeijan "
                     "ensisijainen ohjelmointi (Protokolla Omega) on tuhota "
                     "'Uusi Keisari' — kuka tahansa joka resonoi Veru-ihon "
                     "palojen kanssa (Krusk). Herättäminen asettaa armeijan "
                     "välittömästi Kruskin tappo-ohjelmointiin. Avautuu vain "
                     "Walker-verellä ja -sinettisormuksella (Blitz)."),
    # ---- Old Vaisil (Tarmaas) sisäiset alueet ----------------------
    dict(key="ov_harbor", name="Old Vaisilin satama", parent="loc_old_vaisil",
         type="port", biome="coast", loc_id="loc_ov_harbor",
         description="Massiivinen kaupan ja laivaston keskus; saapuvat "
                     "laivat joutuvat tiukkaan seulaan. Kääpiö Undur "
                     "Stunrack hoitaa uuden armeijan rekrytointia. "
                     "Krakenin uhka pitää kalastajat satamassa."),
    dict(key="grand_garden", name="Grand Garden (Suurpuutarha)",
         parent="loc_old_vaisil", type="building", biome="coast",
         loc_id="loc_grand_garden",
         description="Cunaen toiseksi arvostetuin puutarha — kaunis kulissi, "
                     "jossa tapahtui Efauxerin salamurhayritys ja jossa "
                     "Blitz kuoli. Kätki salamurhaaja Gersnetin ja petollisen "
                     "hovimestari Orienin juonet."),
    dict(key="ov_villas", name="Rikkaiden alue ja huvilat",
         parent="loc_old_vaisil", type="district", biome="coast",
         loc_id="loc_ov_villas",
         description="Ylellinen huvila-alue: Efauxerin huvila toimii "
                     "liittolaisten turvapaikkana, ja Richard & Rose Walker "
                     "asuvat täällä raskaasti vartioituina (Mat, Tomas, "
                     "Darien)."),
    dict(key="maddy_shop", name="Maddy Diblofin taikakauppa",
         parent="loc_old_vaisil", type="shop", biome="coast",
         loc_id="loc_maddy_shop",
         description="Kääpiötaikuri Maddy Diblofin taikakauppa; "
                     "erikoisuuksia kuten Coral Scepter. Maddy tutkii "
                     "Chronicles of the Deep -kirjaa."),
    dict(key="adelf_base", name="Adelf Beliod III:n tukikohta",
         parent="loc_old_vaisil", type="building", biome="coast",
         loc_id="loc_adelf_base",
         description="Metallilohikäärmeratsastaja Adelf Beliod III:n "
                     "tukikohta ja Old Vaisilin tiedon ja historian keskus. "
                     "Hopealohikäärme Thalorian ja apulaiset Elara "
                     "Silverleaf ja Tormek Ironfoot."),
    # ---- Zer'tath Lanke (Aterterra) kaupunginosat ------------------
    dict(key="hohtavat_terassit", name="Hohtavat Terassit",
         parent="loc_zertath_lanke", type="district", biome="underdark",
         loc_id="loc_hohtavat_terassit",
         description="Zer'tath Lanken ylhäisön kerros — aatelistalojen "
                     "loistavat terassit kristallijärven yllä."),
    dict(key="rotanhammas", name="Rotanhammas", parent="loc_zertath_lanke",
         type="district", biome="underdark", loc_id="loc_rotanhammas",
         description="Kaupungin keskikastin ja kauppiaiden kortteli: "
                     "Kuiskausten Lasi -antikvariaatti (Valas Pharn), "
                     "Myrkkykehrä-asekauppa (Xune T'sarran) ja Oloth's "
                     "Caress -bordelli (Jarlax Melarn)."),
    dict(key="sokean_totuuden_pyhakko", name="Sokean Totuuden Pyhäkkö",
         parent="loc_zertath_lanke", type="temple", biome="underdark",
         loc_id="loc_sokean_totuuden_pyhakko",
         description="Zha'lin-aukion pyhäkkö, jossa palvotaan Syvyyden Unta "
                     "faerzress-sirpaleiden kautta. Pääpapitar Naerthali "
                     "Szith'ryn."),
    dict(key="tuhkakuilu", name="Tuhkakuilu", parent="loc_zertath_lanke",
         type="dungeon", biome="underdark", loc_id="loc_tuhkakuilu",
         description="Teloituskuilu, jonka reunalla kieletön pyöveli Vornak "
                     "toteuttaa kaupungin tuomiot."),
    dict(key="drakiel_slum", name="Dra'kielin slummi",
         parent="loc_zertath_lanke", type="district", biome="underdark",
         loc_id="loc_drakiel_slum",
         description="Kaupungin köyhin kerros; laiton tappeluklubi, jonka "
                     "orja-kapo on minotauri \"Murtunut\" Thol."),
    # ---- Veksla (Tarmaas) sisäiset alueet --------------------------
    dict(key="faunder_farm", name="Faunderin tila", parent="loc_veksla",
         type="building", biome="farmland", loc_id="loc_faunder_farm",
         description="Vekslan tärkein maatila 20 min kävelyn päässä "
                     "keskustasta. Ladossa tapahtui Fausterin uhrirituaali; "
                     "lähistön kurpitsat kypsyvät epäluonnollisen nopeasti. "
                     "Elisan haamu vaeltaa öisin. Työntekijänä salainen "
                     "veteraani Gurug Brask."),
    dict(key="anthos_store", name="Anthos General Store", parent="loc_veksla",
         type="shop", biome="farmland", loc_id="loc_anthos_store",
         description="Kylän keskustan kodikas kivijalkakauppa; pitäjä Antos "
                     "Erdofek (salaa rikas entinen aarteenmetsästäjä) tukee "
                     "jälleenrakennusta omilla rahoillaan."),
    dict(key="feather_pillow", name="Feather Pillow Inn", parent="loc_veksla",
         type="tavern", biome="farmland", loc_id="loc_feather_pillow",
         description="Höyhentyynyn majatalo — ryhmän ja agentti Sam "
                     "Undercaven majapaikka. Brokvardin kääpiöperhe, "
                     "salamyhkäiset kaksoset Sylrieth & Thyrieth, ja ullakon "
                     "pokeria pelaava imp Sir Caromaik von Ermizen."),
    dict(key="veksla_temple", name="Aghuantin temppeli (Veksla)",
         parent="loc_veksla", type="temple", biome="farmland",
         loc_id="loc_veksla_temple",
         description="Raskaasti umpeen naulattu temppeli; kaupunkilaiset "
                     "elävät pelossa sen voimaa kohtaan. Pappi Vendimo "
                     "Aarsentop menetti uskonsa ja kuoli kasvimassan "
                     "valtaamana."),
]


# --------------------------------------------------------------------- #
# NPCS — täydet profiilit. stat = "" → ei suoraa monsterivastinetta
# (tarkka luokitus notesissa). loc = "" → ei kiinteää sijaintia.
# wealth = wealth-tier varallisuuden seedaukseen (tyhjä = ei kolikoita).
# --------------------------------------------------------------------- #
NPCS: List[dict] = [
    # ===== DATH — pääantagonisti =====
    dict(id="npc_emnar", name="Emnar Redfei", race="Orc", age="68",
         occupation="Kuningas", title="Oblituksen kuningas",
         faction="Dath", alignment="Lawful Evil", loc="loc_iklence",
         stat="monster:Death Knight", wealth="aristocratic",
         appearance="Täysverinen örkki: pitkät valkoiset hiukset, pyöreät "
                     "mustat silmälasit, kultahampaat.",
         personality="Säälimätön tyranni, joka murhasi omat veljensä ja "
                     "äitinsä valtansa tähden.",
         notes="Dath-ryhmän jäsen. Kerää sieluenergiaa (Veru) ja pitää "
               "vihreää lohikäärme Mueglorisia vankinaan; kiduttaa sitä. "
               "Kruskin ja Efauxerin vihollinen.",
         tags=["antagonist", "ruler", "dath"]),
    dict(id="npc_giurun", name="Giurun Kalfantan", race="Elf", age="684",
         occupation="Arkkimaagi / rehtori",
         title="Ama'Rum-akatemian rehtori", faction="Dath",
         alignment="Lawful Evil", loc="loc_zlalens",
         stat="monster:Archmage", wealth="wealthy",
         appearance="Jämerä haltia: terävä leuka, hopeiset silmät, vahvat "
                     "kulmakarvat, pitkät korvat.",
         personality="Haltioiden ylivallan fanaattinen kannattaja; inhoaa "
                     "drow-kansaa ja muita rotuja.",
         notes="Dathin todellinen johtaja ja manipulaattori. Soluttautunut "
               "Seekers of Demimaindiin; hallitsee Brotherhoodia "
               "telepatian avulla (mm. Äiti Lysandran näyt). Vetää naruja "
               "kaikkien Cunaen konfliktien taustalla.",
         tags=["antagonist", "mastermind", "dath"]),
    dict(id="npc_muegloris", name="Muegloris", race="Green Dragon",
         occupation="Vanki", title="", faction="",
         alignment="Lawful Evil", loc="loc_iklence",
         stat="monster:Adult Green Dragon", wealth="",
         appearance="Vihreä lohikäärme, kahleissa ja kidutettuna.",
         personality="Katkera, vihainen vankeudestaan.",
         notes="Emnar Redfein orja Iklencessä; sieluenergian lähde.",
         tags=["monster", "dragon", "captive"]),

    # ===== BROTHERHOOD OF GLORIOUS SUN =====
    dict(id="npc_fadom", name="Fadom Jivfut", race="Human", age="",
         occupation="Lähetti / tiedonhakija", title="",
         faction="Brotherhood of Glorious Sun", alignment="Neutral Evil",
         loc="", stat="monster:Spy", wealth="comfortable",
         appearance="Tummaihoinen ihminen: pussittavat housut, pitkät "
                     "nahkasaappaat, musta kangastakki. Rento mutta totinen.",
         personality="Laskelmoiva, mukautuva.",
         notes="\"Chrith Lar\" -huumeen lähetti; tekee sopimuksia "
               "alamaailman kanssa (mm. Borbelio Aklobarissa). Piilotti "
               "räjähteitä Kravokin temppeliin.",
         tags=["brotherhood", "criminal"]),
    dict(id="npc_kael_vane", name="Kael \"Tuhkasuu\" Vane", race="Human",
         age="", occupation="Inkvisiittori", title="",
         faction="Brotherhood of Glorious Sun", alignment="Lawful Evil",
         loc="", stat="monster:Assassin", wealth="modest",
         appearance="Leikannut omat huulensa irti todistaakseen "
                     "vaitiolonsa.",
         personality="Fanaattinen, armoton.",
         notes="Veljeskunnan inkvisiittori, joka metsästää pettureita "
               "järjestön sisältä.",
         tags=["brotherhood", "inquisitor"]),
    dict(id="npc_lysandra", name="Äiti Lysandra", race="Human", age="",
         occupation="Ylipapitar", title="Pyhäkkö Solarian ylipapitar",
         faction="Brotherhood of Glorious Sun", alignment="Lawful Neutral",
         loc="", stat="monster:Archmage", wealth="modest",
         appearance="Sokeuttanut itsensä rituaalisesti.",
         personality="Hurskas, vilpitön — ja petetty.",
         notes="Tulkitsee Nousevan Auringon Kääröjä. Ei tiedä, että hänen "
               "näkynsä tulevat telepaattisesti Dathin johtajalta Giurun "
               "Kalfantanilta. Stat-proxy: priest/archmage.",
         tags=["brotherhood", "clergy"]),

    # ===== SEEKERS OF DEMIMAIND =====
    dict(id="npc_dihvik", name="Dihvik Mevraft", race="Human", age="996",
         occupation="Arkkimaagi", title="Deatariksen rehtori",
         faction="Seekers of Demimaind", alignment="Neutral Good", loc="",
         stat="monster:Archmage", wealth="wealthy",
         appearance="Vaaleat pitkät hiukset, lyhyt harmaa parta, polttaa "
                     "piippua; lempeä katse.",
         personality="Viisas, kärsivällinen, periksiantamaton.",
         notes="Venriksen mentori. Brotherhood/Dath kaappasi hänet, mutta "
               "hän on pysynyt vaiti kidutuksesta huolimatta. Agustion "
               "Dust etsii häntä epätoivoisesti.",
         tags=["scholar", "captive"]),
    dict(id="npc_nimri", name="Nimri Greentop", race="Halfling", age="150",
         occupation="Rehtori", title="Saideneria-akatemian rehtori",
         faction="Seekers of Demimaind", alignment="Neutral Good",
         loc="loc_faharn", stat="monster:Archmage", wealth="comfortable",
         appearance="Puolituinen, syvät hymykuopat, pähkinänruskeat silmät, "
                     "nuorekas olemus.",
         personality="Lämmin, terävä-älyinen.",
         notes="Istuu Tarmaaksen neuvostossa. Faharnin akatemian johtaja.",
         tags=["scholar", "ruler"]),

    # ===== DEATH'S VIGIL =====
    dict(id="npc_gaius_marad", name="Gaius Marad", race="Human", age="",
         occupation="Magnus Custos", title="Death's Vigilin ylin vartija",
         faction="Death's Vigil", alignment="Lawful Neutral",
         loc="loc_pinwud", stat="", wealth="comfortable",
         appearance="Vanha ihminen, lempeät silmät, mutta niissä palaa "
                     "outo liekki.",
         personality="Arvokas johtaja; suojeleva mutta laskelmoiva.",
         notes="Johtaa Kuoleman Vartijoita. Mardukin esimies — tietää "
               "tämän kyvystä sitoa sieluja ja haluaa mahdollisesti käyttää "
               "sitä. Poikansa Kaldir lähti järjestöstä. "
               "Stat: Paladin/Cleric ~15, Deva-tier.",
         tags=["faction_leader", "clergy"]),

    # ===== LA FAMIGLIA DELL'ORSO =====
    dict(id="npc_rahgo", name="Rahgo \"Karhu\"", race="Human", age="",
         occupation="Mafiapomo", title="Capo dei Capi",
         faction="La Famiglia dell'Orso", alignment="Neutral Evil",
         loc="loc_frand", stat="monster:Thug", wealth="wealthy",
         appearance="Augmentoitu sydän ja massiiviset mekaaniset "
                     "rautakourat.",
         personality="Raaka, hallitseva, kostonhaluinen.",
         notes="Frandin rikollissyndikaatin johtaja. Haluaa Dariukselta "
               "varastetun Heart Acceleratorin takaisin ja yrittää kaapata "
               "T.R.A.:n teknologiaa. Stat-proxy: Thug, augmentoitu → "
               "Veteran-tier.",
         tags=["criminal", "boss"]),
    dict(id="npc_zaira", name="Zaira \"La Volpe\"", race="Human", age="40",
         occupation="Consigliere", title="",
         faction="La Famiglia dell'Orso", alignment="Lawful Evil",
         loc="loc_frand", stat="monster:Assassin", wealth="wealthy",
         appearance="Poltetun kupariset hiukset, punametallinen kettunaamio, "
                     "messinkiketjuilla koristeltu nahkatakki, "
                     "saapaskorkokengät.",
         personality="Eleganssi ja kylmyys; inhoaa huolimattomuutta.",
         notes="Hoitaa Famiglian salakuuntelut, salamurhat ja lahjonnan. "
               "Dariuksen vaarallinen vihollinen.",
         tags=["criminal", "spy"]),

    # ===== TARMAAS — T.R.A. & hallinto =====
    dict(id="npc_agustion", name="Agustion Dust", race="Dwarf", age="467",
         occupation="Tutkimusjohtaja", title="T.R.A.:n johtaja",
         faction="T.R.A.", alignment="Lawful Neutral", loc="loc_frand",
         stat="monster:Noble", wealth="wealthy",
         appearance="Laiha kääpiö: kyhmynenä, kalju päälaki ja vaaleat "
                     "sivut, kasvoissa kääpiötatuointeja.",
         personality="Ylpeä, älykäs, salaileva — traaginen idealisti.",
         notes="Johtaa T.R.A.-tutkimuskeskusta (ja C.H.O.M.P.ia Hijoinissa). "
               "Etsii epätoivoisesti kadonnutta ystäväänsä Dihvikiä; "
               "paniikissa Kraken-ilmalaivaprojektin viivästymisestä. "
               "Karhun ja muiden pelinappula. Stat-proxy: Noble (artificer).",
         tags=["scholar", "leader"]),
    dict(id="npc_samuel_visimos", name="Samuel Visimos", race="Human",
         age="35", occupation="Insinööri",
         title="Mekaanisen suunnittelun mestari", faction="T.R.A.",
         alignment="Neutral Good", loc="loc_frand", stat="monster:Noble",
         wealth="comfortable",
         appearance="Pyöreä, punaposkinen ihminen, taskukello ketjulla.",
         personality="Innokas, hyväntahtoinen.",
         notes="Heart Accelerator -projektin projektipomo T.R.A.:lla.",
         tags=["scholar"]),
    dict(id="npc_stefan_skelgen", name="Stefan Skelgen", race="Human",
         age="", occupation="Neuvoston puhemies",
         title="Teknokraattisen neuvoston kasvot", faction="Tarmaas",
         alignment="Lawful Neutral", loc="loc_frand", stat="monster:Noble",
         wealth="wealthy",
         appearance="Hillitty, virallinen olemus.",
         personality="Poliittinen, varovainen.",
         notes="Tarmaaksen teknokraattisen neuvoston julkinen kasvo "
               "Frandissa.",
         tags=["ruler"]),
    dict(id="npc_heinrich", name="Heinrich Stormhold", race="Human",
         age="58", occupation="Seurajohtaja", title="Kultaisen Rattaan johtaja",
         faction="Golden Gear", alignment="Lawful Evil", loc="loc_frand",
         stat="monster:Noble", wealth="aristocratic",
         appearance="Pitkä ja hoikka ihminen, terävä katse, aina musta puku.",
         personality="Kylmä, laskelmoiva, vallanhimoinen.",
         notes="Korruptoituneen Golden Gear -eliittiseuran johtaja. "
               "Rahoittaa Emnar Redfeiä vastineeksi poliittisesta vallasta.",
         tags=["elite", "conspirator"]),

    # ===== E.F.I. & DEPARTMENT 0 =====
    dict(id="npc_nilf", name="Nilf Duvlae", race="Human", age="56",
         occupation="Poliisijohtaja", title="E.F.I.:n johtaja",
         faction="E.F.I.", alignment="Lawful Neutral", loc="loc_frand",
         stat="monster:Spy", wealth="comfortable",
         appearance="Hoikka ihminen: baskeri, monokkeli, valkoiset hanskat, "
                     "arpi poskella.",
         personality="Tarkka, periksiantamaton.",
         notes="Tarmaaksen salaisen valtiopoliisin johtaja. Jahtaa Dariusta "
               "ja valvoo taikuuteen ja teknologiaan liittyviä rikoksia.",
         tags=["law", "leader"]),
    dict(id="npc_sam_undercave", name="Sam Undercave", race="Human", age="",
         occupation="Agentti", title="Tiro Aspicio (Taso 4)",
         faction="E.F.I.", alignment="Lawful Neutral", loc="loc_veksla",
         stat="monster:Scout", wealth="modest",
         appearance="Musta liimaletti, punaiset silmät, roteva rakenne.",
         personality="Kunnianhimoinen, maineenhaluinen.",
         notes="E.F.I.:n korkean tason (Taso 4) agentti, joka saalistaa "
               "mainetta ja tutkii valtakunnan sisäistä korruptiota. "
               "Matkusti Padakin kanssa (Ravenstonen kautta) ja asustelee "
               "nyt Vekslan Feather Pillow Innissä; haluaa kuulustella "
               "ryhmää kylän ja Veljeskunnan tapahtumista olematta liian "
               "päällekäyvä.",
         tags=["law"]),
    dict(id="npc_eemil", name="Eemil Jakson", race="Human", age="45",
         occupation="Salainen agentti", title="Department 0 — Agentti 3",
         faction="Department 0", alignment="Lawful Evil", loc="loc_frand",
         stat="monster:Assassin", wealth="comfortable",
         appearance="Silinteri, smokki ja piippu.",
         personality="Kylmä, häikäilemätön.",
         notes="Neuvoston pimeä tahto — metsästää kohteita varjoissa.",
         tags=["law", "assassin"]),

    # ===== EMBER & VEIL COMPANY =====
    dict(id="npc_criella", name="Criella Lotre", race="Tiefling", age="",
         occupation="Ohjaaja", title="Ember & Veil -ohjaaja",
         faction="Ember & Veil Company", alignment="Chaotic Good", loc="",
         stat="monster:Noble", wealth="modest",
         appearance="Viininpunainen takki, sarvissa messinkirenkaat.",
         personality="Suojeleva, dramaattinen.",
         notes="Pitää kiertävän teatteritrupen turvassa ja valitsee "
               "näytelmät. Stat-proxy: Noble (bard).",
         tags=["performer"]),
    dict(id="npc_asha", name="Asha Dawnsong", race="Half-Elf", age="",
         occupation="Pääsolisti", title="", faction="Ember & Veil Company",
         alignment="Neutral Good", loc="", stat="monster:Noble",
         wealth="modest",
         appearance="Hopeatatuoitu silmäkulma, tummat letit.",
         personality="Lahjakas, etsii paikkaansa.",
         notes="Trupen uusi pääsolisti (Kaironin tilalle).",
         tags=["performer"]),

    # ===== SMARDU =====
    dict(id="npc_aedria", name="Aedria Fegel", race="Steel Dragon / Human",
         age="", occupation="Lohikäärme-ekologi", title="Neuvoston jäsen",
         faction="Unhael Scale Riders", alignment="Neutral Good",
         loc="loc_antanard", stat="", wealth="wealthy",
         appearance="Hopeiset hiukset ja silmät, virheetön atleettinen iho, "
                     "nahkahaarniska.",
         personality="Viisas, suojeleva, utelias.",
         notes="Magnuksen mentori Antanardin hautomon syvyyksissä. "
               "Stat: Steel Dragon (adult) ihmishahmossa.",
         tags=["mentor", "dragon"]),
    dict(id="npc_jogra", name="Jogra Greev", race="Dwarf", age="221",
         occupation="Ylivalvoja", title="Hautomolaitoksen ylivalvoja",
         faction="F.E.R.I.D.", alignment="Lawful Neutral",
         loc="loc_antanard", stat="monster:Noble", wealth="comfortable",
         appearance="Sinertävä haarniska, kalju tatuoitu pää, valkoinen "
                     "palmikkoparta.",
         personality="Tiukka, perinteitä kunnioittava.",
         notes="Antanardin lohikäärmehautomon ylivalvoja.",
         tags=["soldier"]),
    dict(id="npc_braimir", name="Braimir Burldair", race="Dwarf", age="",
         occupation="Kymmenneuvoston jäsen", title="Neuvoston kasvot",
         faction="Smardun Kymmenneuvosto", alignment="Lawful Neutral",
         loc="loc_juamore", stat="monster:Noble", wealth="wealthy",
         appearance="Arvokas kääpiö, huoliteltu parta.",
         personality="Diplomaattinen, harkitseva.",
         notes="Smardun Kymmenneuvoston julkinen kasvo Juamoressa.",
         tags=["ruler"]),
    dict(id="npc_thesia", name="Thesia Runeveil", race="Dwarf", age="",
         occupation="Lakimestari", title="Kymmenneuvosto — Laki",
         faction="Smardun Kymmenneuvosto", alignment="Lawful Neutral",
         loc="loc_juamore", stat="monster:Archmage", wealth="wealthy",
         appearance="Tarkkaavainen kääpiönainen, riimukoristeltu kaapu.",
         personality="Ehdoton, oikeudenmukainen.",
         notes="Vastaa Codex Raukenin tulkinnasta Juamoressa.",
         tags=["ruler", "scholar"]),
    dict(id="npc_peokra", name="Peokra Unroltrumm", race="Dwarf", age="",
         occupation="Rakennusmestari", title="Kymmenneuvosto — Rakennus",
         faction="Smardun Kymmenneuvosto", alignment="Lawful Neutral",
         loc="loc_juamore", stat="monster:Noble", wealth="wealthy",
         appearance="Vankka kääpiö, työkaluvyö ja kaavakääröt.",
         personality="Käytännöllinen, määrätietoinen.",
         notes="Vastaa Smardun rakennushankkeista.",
         tags=["ruler"]),
    dict(id="npc_enquars", name="Enquars Paermote", race="Dwarf", age="",
         occupation="Paroni", title="Hifromin paroni",
         faction="Smardu", alignment="Lawful Neutral", loc="loc_hifrom",
         stat="monster:Noble", wealth="comfortable",
         appearance="Karaistunut vuoristokääpiö.",
         personality="Huolestunut alueensa turvallisuudesta.",
         notes="Hifromin hallitsija; taistelee vuorelta saapuvia "
               "pahantahtoisia olentoja vastaan.",
         tags=["ruler"]),

    # ===== OBLITUS =====
    dict(id="npc_julus", name="Julus Sanace", race="Human", age="43",
         occupation="Areenan omistaja", title="Nak Magnok Kor Adez -isäntä",
         faction="Aesica", alignment="Lawful Evil", loc="loc_nak_magnok",
         stat="monster:Noble", wealth="wealthy",
         appearance="Valkoiset viikset, kalju, läpitunkeva katse, kauniisti "
                     "koristeltu viitta.",
         personality="Sileä, opportunistinen, sopimususkollinen.",
         notes="Areenan uusi omistaja; selvisi kapinasta ja yrittää "
               "sopeutua Kruskin ja Antosin valtaan. Sitoo yhä synkkä "
               "sopimus Lucienin kanssa (Convergence Enginen sielut).",
         tags=["arena", "conspirator"]),
    dict(id="npc_gorkha", name="Gorkha Redbone", race="Orc", age="",
         occupation="Sielukoneen valvoja", title="", faction="Red Drob",
         alignment="Neutral Evil", loc="loc_aesica", stat="monster:Cultist",
         wealth="modest",
         appearance="Arpinen örkki, rituaalimerkkejä.",
         personality="Fanaattinen, kuuliainen.",
         notes="Erokmen sisäpiiriä. Kontrolloi areenalla kuolleiden "
               "sielujen kanavointia titaani Papan koneistoon "
               "(Convergence Engine).",
         tags=["antagonist", "cult"]),
    dict(id="npc_antos_orac", name="Antos Orac", race="Human", age="",
         occupation="Kapinajohtaja", title="Vapaan Etelän Koalitio",
         faction="Vapaan Etelän Koalitio", alignment="Chaotic Good",
         loc="loc_aesica", stat="monster:Scout", wealth="modest",
         appearance="Karaistunut kapinallinen.",
         personality="Päättäväinen, oikeudenmukainen.",
         notes="Kruskin aisapari; hoitaa Aesican hallinnon byrokraattisen "
               "puolen, diplomatian ja poliittiset neuvottelut koalition "
               "jäsenten kanssa. Vapaan Etelän Koalition pääarkkitehti "
               "Efauxerin rinnalla.",
         tags=["rebel", "ally"]),
    dict(id="npc_borbelio", name="Borbelio Suuri", race="Goblin", age="",
         occupation="Entinen johtaja", title="", faction="",
         alignment="Neutral Evil", loc="loc_aklobar",
         stat="monster:Goblin Boss", wealth="modest",
         appearance="Ahne, koristeisiin pukeutunut gobliini.",
         personality="Ahne, opportunistinen.",
         notes="Aklobarin entinen johtaja; myi Chrith Laria Fadom "
               "Jivfutille. Syrjäytetty \"Council of Cushionsin\" tieltä.",
         tags=["criminal"]),
    dict(id="npc_wok", name="Wok Metsam", race="Goblin", age="",
         occupation="Kylänvanhin", title="Pulkerin vanhin", faction="",
         alignment="Neutral", loc="loc_pulker", stat="monster:Goblin Boss",
         wealth="poor",
         appearance="Vanha, ryppyinen gobliini.",
         personality="Huolestunut ja sitkeä; räävitön huumori.",
         notes="Pulkerin gobliiniparantaja ja vanhin; kamppailee sadon "
               "menetyksen, rottien ja sumuhirviöiden kanssa. Istuu nyt "
               "Aesican uudessa heimoneuvostossa.",
         tags=["ruler", "council"]),
    dict(id="npc_longtongue", name="LongTounge", race="Grung / Sammakkokansa",
         age="", occupation="Kylänvanhin", title="Kravokin vanhin",
         faction="", alignment="Neutral", loc="loc_kravok",
         stat="monster:Lizardfolk", wealth="poor",
         appearance="Suuri sammakkomainen humanoidi, kirkkaat värit.",
         personality="Suojeleva, hiljainen.",
         notes="Kravokin suokylän johtaja; poikansa kaapattu Svik Fethen "
               "toimesta. Stat-proxy: Lizardfolk.",
         tags=["ruler"]),
    dict(id="npc_nogjat", name="Makohf Sheg", race="Half-Orc", age="",
         occupation="Leirinpäällikkö", title="Tukor Shegin johtaja",
         faction="Vapaan Etelän Koalitio",
         alignment="Chaotic Neutral", loc="loc_tukor_sheg",
         stat="monster:Thug", wealth="poor",
         appearance="Karaistunut puoliörkki-aavikkosoturi.",
         personality="Selviytyjä, ylpeä.",
         notes="Tukor Shegin puoliörkkileirin johtohahmo; hänen heimonsa "
               "aloitti Aesican kapinan. Istuu nyt kaupungin uudessa "
               "heimoneuvostossa.",
         tags=["rebel", "council"]),

    # ===== AESICA — kapinan jälkeinen kaupunki =====
    dict(id="npc_erokme", name="Erokme Belmudar", race="Human", age="",
         occupation="Syrjäytetty kreivi", title="Aesican entinen hirmuvaltias",
         faction="", alignment="Lawful Evil", loc="",
         stat="monster:Death Knight", wealth="wealthy",
         appearance="Kylmä, ylimielinen orjaruhtinas.",
         personality="Julma, laskelmoiva sielukauppias.",
         notes="Johti Aesican gladiaattorikulttuuria, orjakauppaa ja "
               "Convergence Engine -sielukonetta. Syöstiin vallasta "
               "verisessä kapinassa. Kytkeytyy Mardukin sieluvankilaan "
               "(orjuuttaja Erokme). Stat-proxy: Death Knight.",
         tags=["antagonist", "arena"]),
    dict(id="npc_lyra", name="Lyra Penediktus", race="Goblin", age="",
         occupation="Bardi", title="", faction="Vapaan Etelän Koalitio",
         alignment="Chaotic Good", loc="loc_aesica", stat="monster:Noble",
         wealth="modest",
         appearance="Ilmeikäs gobliinibardi.",
         personality="Uskollinen, mutta unettomuuden ja pelon rasittama.",
         notes="Jäi Kruskin tueksi Aesicaan. Kantaa kirottua Clavis-miekkaa "
               "ja kärsii öisin painajaisista, joissa vampyyri Dimerius "
               "Blackfeet yrittää manipuloida häntä. Stat-proxy: Noble (bard).",
         tags=["ally", "party"]),
    dict(id="npc_xionzer", name="Xionzer \"Xer\"", race="Dwarf", age="",
         occupation="Barbaari", title="", faction="Vapaan Etelän Koalitio",
         alignment="Chaotic Good", loc="loc_aesica", stat="", wealth="modest",
         appearance="Roteva kääpiöbarbaari.",
         personality="Suora, taisteluhaluinen, uskollinen.",
         notes="Jäi Aesicaan; ratsastaa valkoisella lohikäärme Fangrokilla. "
               "Toi Kruskille huolestuttavia tietoja Unhaelin "
               "lohikäärmeratsastajien epäilyttävistä toimista. "
               "Stat: Barbaari (DM valitsee blockin).",
         tags=["ally", "party"]),
    dict(id="npc_fangrok", name="Fangrok", race="White Dragon", age="",
         occupation="Ratsulohikäärme", title="", faction="Vapaan Etelän Koalitio",
         alignment="Chaotic Neutral", loc="loc_aesica",
         stat="monster:Adult White Dragon", wealth="",
         appearance="Valkoinen lohikäärme.",
         personality="Villi mutta uskollinen Xionzerille.",
         notes="Xionzerin ratsulohikäärme.",
         tags=["dragon", "ally"]),
    dict(id="npc_aleria", name="Aleria", race="Halfling", age="",
         occupation="Vakooja / resurssien kerääjä", title="",
         faction="Vapaan Etelän Koalitio", alignment="Chaotic Good",
         loc="loc_aesica", stat="monster:Spy", wealth="modest",
         appearance="Nopea, huomaamaton puolituinen.",
         personality="Näppärä, kekseliäs.",
         notes="Tärkeä liittolainen kapinan aikana; hoitaa tiedustelua ja "
               "hankintoja kaupungissa.",
         tags=["ally", "spy"]),
    dict(id="npc_zahara", name="Zahara", race="Loxodon", age="",
         occupation="Parantaja", title="", faction="Vapaan Etelän Koalitio",
         alignment="Neutral Good", loc="loc_aesica", stat="monster:Acolyte",
         wealth="modest",
         appearance="Rauhallinen norsupäinen loxodon-parantaja.",
         personality="Lempeä, viisas.",
         notes="Loxodon-parantaja; tärkeä liittolainen kapinan aikana, "
               "toimii edelleen kaupungissa. Stat-proxy: Acolyte.",
         tags=["ally", "healer"]),
    dict(id="npc_adrik", name="Adrik Balderk", race="Dwarf", age="",
         occupation="Gladiaattorivalmentaja", title="", faction="",
         alignment="Lawful Neutral", loc="loc_nak_magnok", stat="",
         wealth="modest",
         appearance="Vanha, arpinen ja arvostettu kääpiösoturi.",
         personality="Ankara mutta isällinen.",
         notes="Toimi areenalla gladiaattorien opettajana; Kruskille "
               "isällinen hahmo. Valmentaa nyt vain vapaaehtoisia "
               "taistelijoita. Stat: Veteran/Gladiator-tier (DM valitsee).",
         tags=["ally", "mentor"]),
    dict(id="npc_grebza", name="Grebza the Velvet Maw", race="Human", age="",
         occupation="Killan johtaja", title="Samettisen Killan johtaja",
         faction="Samettinen Kilta", alignment="Neutral Evil",
         loc="loc_aesica", stat="monster:Noble", wealth="aristocratic",
         appearance="Ylellinen aatelinen; käyttää viehätysamulettia.",
         personality="Liukas, varovainen selviytyjä.",
         notes="Omistaa varjokauppoja ja orjamarkkinoita. Pitää matalaa "
               "profiilia ja yrittää navigoida uudessa poliittisessa "
               "tilanteessa hengissä.",
         tags=["criminal", "elite"]),
    dict(id="npc_bervider", name="Bervider", race="Half-Orc", age="",
         occupation="Heimojohtaja", title="Tukor Shegin johtohahmo",
         faction="Vapaan Etelän Koalitio", alignment="Chaotic Neutral",
         loc="loc_aesica", stat="monster:Thug", wealth="poor",
         appearance="Karaistunut puoliörkkisoturi.",
         personality="Suorapuheinen, sitkeä.",
         notes="Makohf Shegin rinnalla Tukor Shegin johtohahmo; istuu "
               "Aesican uudessa heimoneuvostossa.",
         tags=["rebel", "council"]),
    dict(id="npc_longhop", name="Longhop", race="Grung", age="",
         occupation="Kylän edustaja", title="Kravokin edustaja",
         faction="Vapaan Etelän Koalitio", alignment="Neutral",
         loc="loc_aesica", stat="monster:Lizardfolk", wealth="poor",
         appearance="Kirkasvärinen sammakkokansan (grung) edustaja.",
         personality="Varovainen, tarkkaavainen.",
         notes="Kravokin sammakkokylän edustaja Aesican uudessa "
               "heimoneuvostossa. Stat-proxy: Lizardfolk.",
         tags=["council"]),
    dict(id="npc_borug", name="Borug Skud", race="Orc", age="",
         occupation="Satamamestari", title="Gor'Rashin satamamestari",
         faction="", alignment="Lawful Evil", loc="loc_gor_rash",
         stat="monster:Orc", wealth="comfortable",
         appearance="Pelätty, jäntevä örkki.",
         personality="Rautainen, korruptoitunut.",
         notes="Johti Gor'Rashin satamaa rautaisella otteella ja teki "
               "yhteistyötä vanhan hallinnon kanssa.",
         tags=["harbor", "criminal"]),
    dict(id="npc_dimerio", name="Isä Dimerio Fao", race="Goblin", age="",
         occupation="Ylipappi", title="Aghuantin temppelin ylipappi",
         faction="Aghuant", alignment="Neutral Good", loc="loc_aghuant_temple",
         stat="monster:Acolyte", wealth="modest",
         appearance="Arvokas, ikääntynyt gobliinipappi.",
         personality="Hurskas, yhteisöllinen.",
         notes="Aghuantin suuren temppelin korkein pappi — Aesican "
               "hengellinen keskus. Papisto pelastettiin kapinan aikana "
               "myrkytysyritykseltä. Stat-proxy: Acolyte (ylipappi).",
         tags=["clergy"]),
    dict(id="npc_gaufex", name="Gaufex Bakduvar", race="Dwarf", age="",
         occupation="Komentaja / tiedustelumestari",
         title="Unhael Scale Rider", faction="Unhael Scale Riders",
         alignment="Lawful Neutral", loc="loc_aesica", stat="monster:Scout",
         wealth="comfortable",
         appearance="Terävä-älyinen kääpiökomentaja.",
         personality="Laskelmoiva, salaileva.",
         notes="Ratsastaa messinkilohikäärme Khaldryksella. Tuki kapinaa "
               "ilmasta, mutta ajaa salaista agendaa (kuningas Saxigniksen "
               "pelastaminen Chento-vuoren yrteillä) — Krusk on alkanut "
               "epäillä hänen aikeitaan.",
         tags=["dragon_rider", "scholar"]),
    dict(id="npc_khaldrys", name="Khaldrys", race="Brass Dragon", age="",
         occupation="Ratsulohikäärme", title="", faction="Unhael Scale Riders",
         alignment="Chaotic Good", loc="loc_aesica",
         stat="monster:Adult Brass Dragon", wealth="",
         appearance="Messinkilohikäärme.",
         personality="Puhelias, ovela.",
         notes="Gaufex Bakduvarin ratsulohikäärme.",
         tags=["dragon"]),
    dict(id="npc_brynja", name="Brynja Ironfist", race="Dwarf", age="",
         occupation="Lohikäärmeratsastaja", title="Unhael Scale Rider",
         faction="Unhael Scale Riders", alignment="Lawful Good",
         loc="loc_aesica", stat="monster:Scout", wealth="comfortable",
         appearance="Vankka kääpiösoturi.",
         personality="Suora, kunniallinen.",
         notes="Ratsastaa hopealohikäärme Silverscalella (Reemien). "
               "Toverit Thorfinn ja Bronzewing kaatuivat kapinassa.",
         tags=["dragon_rider"]),
    dict(id="npc_silverscale", name="Silverscale (Reemien)",
         race="Silver Dragon", age="", occupation="Ratsulohikäärme", title="",
         faction="Unhael Scale Riders", alignment="Lawful Good",
         loc="loc_aesica", stat="monster:Adult Silver Dragon", wealth="",
         appearance="Hopealohikäärme.",
         personality="Jalo, suojeleva.",
         notes="Brynja Ironfistin ratsulohikäärme.",
         tags=["dragon"]),
    dict(id="npc_saxignis", name="Kuningas Saxignis", race="Red Dragon",
         age="", occupation="Lohikäärmekuningas", title="",
         faction="Unhael Scale Riders", alignment="Chaotic Neutral", loc="",
         stat="monster:Adult Red Dragon", wealth="aristocratic",
         appearance="Mahtava punainen lohikäärmekuningas, sairauden "
                     "heikentämä.",
         personality="Ylpeä, kärsivä.",
         notes="Unhael Scale Ridersin lohikäärmekuningas, jonka pelastamista "
               "(Chento-vuoren yrtit) ratsastajat salaa ajavat.",
         tags=["dragon", "ruler"]),

    # ===== OLD VAISIL & VAPAA ETELÄ =====
    dict(id="npc_efauxer", name="Efauxer Redfei", race="Half-Orc", age="78",
         occupation="Kreivi", title="Old Vaisilin kreivi",
         faction="Vapaan Etelän Koalitio", alignment="Lawful Good",
         loc="loc_old_vaisil", stat="monster:Noble", wealth="wealthy",
         appearance="Vanha puoliörkki: vaaleat hiukset ja parta, pienet "
                     "pyöreät lasit, punaiset liivit ja karhunpäinen "
                     "kävelykeppi.",
         personality="Maltillinen, viisas bisnesmies; lämmin sydän.",
         notes="Kaupungin johtaja ja Vapaan Etelän Koalition pääarkkitehti; "
               "Kruskin isoisä. Ohjaa sotaa Tarmaasta ja Emnaria vastaan. "
               "Selvisi juuri Kultaisen Rattaan tilaamasta "
               "salamurhayrityksestä (jossa Blitz kuoli).",
         tags=["ruler", "ally"]),
    dict(id="npc_gilhard", name="Gilhard Blacktooth", race="Goblin", age="",
         occupation="Oikeusjohtaja", title="Old Vaisilin oikeusjohtaja",
         faction="Old Vaisil", alignment="Lawful Neutral",
         loc="loc_old_vaisil", stat="monster:Goblin Boss", wealth="comfortable",
         appearance="Terävähampainen, hyvin pukeutunut gobliini.",
         personality="Tarkka, armottoman lainkuuliainen.",
         notes="Vastaa kaupungin armottoman oikeusjärjestelmän ja lakien "
               "toimeenpanosta (hirttoaukio); hoitaa myös pakolaisvirtaa.",
         tags=["law"]),
    dict(id="npc_gersnet", name="Gersnet", race="Human", age="",
         occupation="Salamurhaaja", title="", faction="",
         alignment="Neutral Evil", loc="loc_grand_garden",
         stat="monster:Assassin", wealth="comfortable",
         appearance="Huomaamaton, ammattimainen.",
         personality="Kylmä, tehokas.",
         notes="Yritti murhata Efauxerin Grand Gardenissa; tappoi Blitz "
               "Walkerin. Juonitteli petollisen hovimestari Orienin kanssa.",
         tags=["assassin"]),
    dict(id="npc_rose_walker", name="Rose Walker", race="Human", age="",
         occupation="Eläkeläinen", title="", faction="Vapaan Etelän Koalitio",
         alignment="Neutral Good", loc="loc_ov_villas", stat="monster:Noble",
         wealth="wealthy",
         appearance="Arvokas, lämmin aatelisrouva.",
         personality="Suojeleva äiti; surun murtama.",
         notes="Blitzin äiti; viettää eläkepäiviä Efauxerin suojeluksessa "
               "Old Vaisilissa (vartijoina Mat, Tomas, Darien).",
         tags=["ally"]),
    dict(id="npc_delma", name="Delma", race="Human", age="",
         occupation="Vakooja / kuulustelija", title="", faction="Old Vaisil",
         alignment="Lawful Neutral", loc="loc_old_vaisil", stat="monster:Spy",
         wealth="comfortable",
         appearance="Tarkkaavainen, huomaamaton taustavaikuttaja.",
         personality="Terävä, epäluuloinen, lojaali Redfei-linjalle.",
         notes="Efauxerin luotettu vakooja ja kuulustelija; arvioi "
               "tulijoiden motiivit.",
         tags=["spy", "law"]),
    dict(id="npc_dumblo", name="Kapteeni Dumblo Foofant", race="Halfling",
         age="", occupation="Sotilaskomentaja", title="", faction="Old Vaisil",
         alignment="Lawful Good", loc="loc_old_vaisil", stat="monster:Scout",
         wealth="comfortable",
         appearance="Karaistunut, luotettava komentaja.",
         personality="Uskollinen, sisukas.",
         notes="Efauxerin pitkäaikainen ystävä ja Old Vaisilin "
               "sotilaskomentaja.",
         tags=["soldier", "ally"]),
    dict(id="npc_giluan", name="Giluan Vasemot", race="Human", age="",
         occupation="Sataman päävastaava", title="Old Vaisil Sea Co:n johtaja",
         faction="", alignment="Neutral", loc="loc_ov_harbor",
         stat="monster:Noble", wealth="wealthy", alive=False,
         appearance="Entinen arvostettu satamaruhtinas.",
         personality="Määrätietoinen kauppias.",
         notes="MURHATTU — löydettiin raa'asti tapettuna, pää viety. "
               "Takana Emnarin palkkaama örkki Volden (45 000 kullan "
               "palkkio).",
         tags=["harbor", "deceased"]),
    dict(id="npc_volden", name="Volden", race="Orc", age="",
         occupation="Palkkasoturi", title="", faction="",
         alignment="Neutral Evil", loc="", stat="monster:Assassin",
         wealth="wealthy",
         appearance="Jäntevä, arpinen örkkipalkkasoturi.",
         personality="Kylmä ammattilainen.",
         notes="Emnar Redfein palkkaama; murhasi Giluan Vasemotin ja lunasti "
               "45 000 kullan palkkion. Yksi kaupungin monista "
               "salamurhaajista.",
         tags=["assassin", "mercenary"]),
    dict(id="npc_undur", name="Undur Stunrack", race="Dwarf", age="",
         occupation="Rekrytoija", title="", faction="Old Vaisil",
         alignment="Lawful Neutral", loc="loc_ov_harbor", stat="monster:Guard",
         wealth="modest",
         appearance="Jäntevä kääpiö-aliupseeri.",
         personality="Suorapuheinen, tehokas.",
         notes="Hoitaa uuden armeijan rekrytointia satamassa (sotilaille "
               "1 gp/pv, 10 gp taistelupäiviltä).",
         tags=["soldier"]),
    dict(id="npc_orien", name="Orien", race="Human", age="",
         occupation="Hovimestari", title="", faction="",
         alignment="Neutral Evil", loc="loc_grand_garden", stat="monster:Spy",
         wealth="modest",
         appearance="Sileä, moitteeton hovimestari.",
         personality="Petollinen, kaksinaamainen.",
         notes="Petollinen hovimestari, joka juonitteli Gersnetin kanssa "
               "Grand Gardenin salamurhayrityksessä.",
         tags=["spy", "traitor"]),
    dict(id="npc_beon", name="Beon Vildman", race="Human", age="",
         occupation="Huumeongelman selvittäjä", title="", faction="Old Vaisil",
         alignment="Lawful Neutral", loc="loc_old_vaisil", stat="monster:Spy",
         wealth="modest",
         appearance="Tarkkaavainen, väsynyt tutkija.",
         personality="Sinnikäs, huolestunut.",
         notes="Efauxerin asettama hoitamaan paisuvaa Chrith Lar "
               "-huumekriisiä, joka uhkaa kaupungin vakautta.",
         tags=["law"]),
    dict(id="npc_maddy", name="Maddy Diblof", race="Dwarf", age="",
         occupation="Taikuri / kauppias", title="", faction="",
         alignment="Neutral", loc="loc_maddy_shop", stat="monster:Archmage",
         wealth="wealthy",
         appearance="Eksentrinen kääpiötaikuri.",
         personality="Utelias, salaperäinen.",
         notes="Pitää taikakauppaa Old Vaisilissa; omistaa Coral Scepterin "
               "ja tutkii Chronicles of the Deep -kirjaa valmistautuen "
               "tapaamaan Efauxeria. Stat-proxy: Archmage.",
         tags=["merchant", "scholar"]),
    dict(id="npc_adelf", name="Adelf Beliod III", race="Human", age="",
         occupation="Lohikäärmeratsastaja / oppinut", title="",
         faction="", alignment="Neutral Good", loc="loc_adelf_base",
         stat="monster:Noble", wealth="wealthy",
         appearance="Arvokas, rauhaarakastava oppinut.",
         personality="Viisas; ei pidä taistelusta.",
         notes="Metallilohikäärmeratsastaja (hopealohikäärme Thalorian); "
               "toimii Old Vaisilin tiedon ja historian keskuksena. "
               "Apulaiset Elara Silverleaf ja Tormek Ironfoot.",
         tags=["scholar", "dragon_rider"]),
    dict(id="npc_thalorian", name="Thalorian", race="Silver Dragon", age="",
         occupation="Ratsulohikäärme", title="", faction="",
         alignment="Lawful Good", loc="loc_adelf_base",
         stat="monster:Adult Silver Dragon", wealth="",
         appearance="Jalo hopealohikäärme.",
         personality="Viisas, rauhallinen.",
         notes="Adelf Beliod III:n ratsulohikäärme.",
         tags=["dragon"]),
    dict(id="npc_elara_silverleaf", name="Elara Silverleaf", race="Half-Elf",
         age="", occupation="Apulainen", title="", faction="",
         alignment="Neutral Good", loc="loc_adelf_base", stat="monster:Scout",
         wealth="modest",
         appearance="Tarkkaavainen puolihaltia-oppinut.",
         personality="Avulias, utelias.",
         notes="Adelf Beliod III:n apulainen tiedon keskuksessa.",
         tags=["scholar"]),
    dict(id="npc_tormek", name="Tormek Ironfoot", race="Dwarf", age="",
         occupation="Apulainen", title="", faction="",
         alignment="Neutral Good", loc="loc_adelf_base", stat="monster:Guard",
         wealth="modest",
         appearance="Vankka kääpiö-vartija.",
         personality="Uskollinen, käytännöllinen.",
         notes="Adelf Beliod III:n apulainen ja suojelija.",
         tags=["soldier"]),
    dict(id="npc_gobroim", name="Gobroim (Kraken)", race="Kraken", age="",
         occupation="Merihirviö", title="", faction="",
         alignment="Chaotic Evil", loc="", stat="monster:Kraken", wealth="",
         appearance="Valtava läntinen meriolento.",
         personality="Nälkäinen, tuhoisa.",
         notes="Lännestä siirtynyt Kraken, joka hyökkäilee laivojen "
               "kimppuun ravinnon puutteen vuoksi ja lamauttaa Old "
               "Vaisilin merenkulun.",
         tags=["monster", "threat"]),

    # ===== RAVENSTONE — vampyyrien sisällissota =====
    dict(id="npc_jugorai", name="Jugorai Millwind", race="Human (Vampyyri)",
         age="", occupation="Paroni / vampyyriloitsija",
         title="Ravenstonen paroni", faction="", alignment="Lawful Evil",
         loc="loc_ravenstone", stat="monster:Vampire Spellcaster",
         wealth="wealthy",
         appearance="Kalpea, erakoitunut paroni — salainen vampyyriloitsija.",
         personality="Epätoivoinen, vallanhimoinen, hajoamassa.",
         notes="Kaupungin nimellinen hallitsija, täysin Dimeriuksen "
               "hallinnassa. Yrittää epätoivoisesti kaapata Dimeriuksen "
               "voimat: luo ghouleja ja uusia vampyyreja (Fior Rask, Zemok "
               "Retana) uhrattavaksi voimansiirrossa. Suunnitelmat "
               "hajoavat — ghouleja vaeltaa vapaana kaduilla. Lupasi 3700 "
               "kultaa Aksel Wolfbanen päästä (tämä tappoi hänen "
               "vampyyriksi muutetun tyttärensä Isabelin).",
         tags=["ruler", "undead", "secret"]),
    dict(id="npc_dimerius", name="Dimerius Blackfeet", race="Goblin (Vampyyri)",
         age="", occupation="Vampyyrilordi", title="Ravenstonen perustajaisä",
         faction="", alignment="Chaotic Evil", loc="loc_corvus_spelchrum",
         stat="monster:Vampire Spellcaster", wealth="aristocratic",
         appearance="Muinainen \"elinvoiman vampyyri\"; alun perin gobliini.",
         personality="Petollinen, kärsivällinen, kaikkinäkevä.",
         notes="Ravenstonen perustaja ja keisari Tarquvasin entinen oikea "
               "käsi. Teljetty Corvus Spelchrum -kryptan kynttiläkammioon; "
               "odottaa heräämistään ja manipuloi koko kaupunkia varjoista "
               "palatakseen valtaan. Muinaiset vampyyrit vartioivat häntä "
               "Jugorailta.",
         tags=["antagonist", "undead", "boss"]),
    dict(id="npc_polsen", name="Polsen", race="Vampire", age="",
         occupation="Vampyyrilordi", title="", faction="Dimeriuksen hovi",
         alignment="Lawful Evil", loc="loc_ravenstone",
         stat="monster:Vampire", wealth="wealthy",
         appearance="Hallitseva vampyyrilordi.",
         personality="Kylmä strategi.",
         notes="Johtaa Ravenstonen vampyyriverkostoa; suojelee Dimeriusta "
               "ja estää Jugoraita varastamasta tämän voimaa.",
         tags=["undead", "vampire"]),
    dict(id="npc_vilan", name="Vilan Norgrad", race="Vampire", age="350+",
         occupation="Palvelija", title="", faction="Dimeriuksen hovi",
         alignment="Lawful Evil", loc="loc_ravenstone",
         stat="monster:Vampire", wealth="comfortable",
         appearance="Yli 350-vuotias uskollinen vampyyri.",
         personality="Uskollinen, tarkkaavainen.",
         notes="Dimeriuksen uskollinen palvelija; vartioi tämän voimaa.",
         tags=["undead", "vampire"]),
    dict(id="npc_herold", name="Herold Reggefoi", race="Vampire", age="800+",
         occupation="Palvelija", title="", faction="Dimeriuksen hovi",
         alignment="Lawful Evil", loc="loc_ravenstone",
         stat="monster:Vampire", wealth="comfortable",
         appearance="Yli 800-vuotias muinainen vampyyri.",
         personality="Ikivanha, hidasliikkeinen, armoton.",
         notes="Dimeriuksen vanhin palvelija; osa hovia joka estää "
               "Jugorain vallankaappauksen.",
         tags=["undead", "vampire"]),
    dict(id="npc_fior", name="Fior Rask", race="Human (Vampyyri)", age="",
         occupation="Majatalonpitäjän tytär", title="", faction="",
         alignment="Neutral Evil", loc="loc_ravenstone",
         stat="monster:Vampire Spawn", wealth="poor",
         appearance="Nuori, vastikään muutettu vampyyri.",
         personality="Peloissaan, nälkäinen.",
         notes="Jugorain luoma uusi vampyyri, tarkoitettu uhrattavaksi "
               "Dimeriuksen voimansiirrossa.",
         tags=["undead"]),
    dict(id="npc_zemok", name="Zemok Retana", race="Human (Vampyyri)", age="",
         occupation="Kauppias", title="", faction="",
         alignment="Neutral Evil", loc="loc_ravenstone",
         stat="monster:Vampire Spawn", wealth="modest",
         appearance="Entinen kauppias, nyt vampyyri.",
         personality="Katkera, ahne.",
         notes="Jugorain luoma uusi vampyyri, uhrattavaksi tarkoitettu.",
         tags=["undead"]),
    dict(id="npc_greg", name="Greg Silverhand", race="Human", age="",
         occupation="Parantolan johtaja", title="Asylum Purgon johtaja",
         faction="Tarmaas", alignment="Lawful Evil", loc="loc_asylum_purgo",
         stat="monster:Noble", wealth="wealthy",
         appearance="Sileä, hymyilevä tiedemies.",
         personality="Sadistinen, utelias, tunteeton.",
         notes="Asylum Purgon johtaja; vastuussa julmista ihmiskokeista, "
               "mm. Walkerin suvun (Blitzin perheen) kohtaloista. Valuttaa "
               "vankien verta salaa Dimeriukselle. Stat-proxy: Noble "
               "(tiedemies).",
         tags=["antagonist", "scholar"]),
    dict(id="npc_gaur", name="Gaur Rakek", race="Tabaxi", age="",
         occupation="Alamaailman pomo", title="Cora 0:n johtaja",
         faction="Cora 0", alignment="Neutral Evil", loc="loc_profundus",
         stat="monster:Assassin", wealth="wealthy",
         appearance="Juonitteleva, tarkkaavainen tabaxi.",
         personality="Kunnianhimoinen, laskelmoiva.",
         notes="Johtaa Profunduksen rikollisjärjestöä Cora 0. Valmistautuu "
               "sotaan vampyyrejä vastaan ja haluaa syrjäyttää paroni "
               "Jugorain. Teki salaisen sopimuksen Talo Despanan drowien "
               "kanssa (savea vastaan yösuojelu).",
         tags=["criminal", "boss"]),
    dict(id="npc_jivin", name="Jivin Lukom", race="Gnome", age="",
         occupation="Kirjastonhoitaja", title="", faction="Cora 0",
         alignment="Neutral", loc="loc_ravenstone", stat="monster:Spy",
         wealth="modest",
         appearance="Huomaamaton gnomi-kirjastonhoitaja.",
         personality="Terävä-älyinen, salaileva.",
         notes="Kaupungin kirjastonhoitaja — todellisuudessa Cora 0:n "
               "älykäs tiedonkerääjä ja vakooja.",
         tags=["criminal", "spy"]),
    dict(id="npc_aksel", name="Aksel Wolfbane", race="Human", age="",
         occupation="Vampyyrinmetsästäjä", title="", faction="",
         alignment="Chaotic Good", loc="loc_profundus",
         stat="monster:Assassin", wealth="modest",
         appearance="Karaistunut, arpinen metsästäjä.",
         personality="Päättäväinen, katkera, kunniallinen.",
         notes="Vampyyrinmetsästäjä joka piileskelee Profunduksessa. "
               "Murhasi paroni Jugorain tyttären Isabelin (joka oli "
               "muutettu vampyyriksi ja halusi kuolla). Pään hinta 3700 "
               "kultaa. Hänen veljensä Davos on Jugorain vampyyriorja.",
         tags=["ally", "hunter"]),
    dict(id="npc_davos", name="Davos Wolfbane", race="Human (Vampyyri)",
         age="", occupation="Vampyyriorja", title="", faction="",
         alignment="Neutral Evil", loc="loc_ravenstone",
         stat="monster:Vampire Spawn", wealth="poor",
         appearance="Kalpea, tahdoton vampyyri.",
         personality="Orjuutettu, tuskainen.",
         notes="Akselin veli, joka on nyt Jugorain vampyyriorja — "
               "emotionaalinen vipuvarsi Akselia vastaan.",
         tags=["undead"]),
    dict(id="npc_isabel", name="Isabel Millwind", race="Human (Vampyyri)",
         age="", occupation="Paronin tytär", title="", faction="",
         alignment="Neutral", loc="loc_ravenstone", alive=False,
         stat="monster:Vampire Spawn", wealth="wealthy",
         appearance="Kaunis, murheellinen nuori nainen.",
         personality="Kärsivä, kuolemaa kaipaava.",
         notes="Jugorain tytär, muutettu vampyyriksi; halusi kuolla ja "
               "Aksel Wolfbane surmasi hänet. KUOLLUT — juonen liikkeelle "
               "paneva tragedia.",
         tags=["undead", "deceased"]),
    dict(id="npc_edmun", name="Edmun Padel", race="Human", age="",
         occupation="Ylipappi", title="Avarath-kultin perustaja",
         faction="Avarath-kultti", alignment="Chaotic Evil",
         loc="loc_avarath_temple", stat="monster:Cultist", wealth="modest",
         appearance="Hurmoksellinen kulttipappi.",
         personality="Fanaattinen, mielen orjuuttama.",
         notes="Avarath-kultin perustaja ja pääpappi; löysi savikaivannoilta "
               "\"jotain, joka puhui syvyyksistä\". Aivopesty Abolethin "
               "orja.",
         tags=["cult", "clergy"]),
    dict(id="npc_hannes", name="Hannes Allroad", race="Human", age="",
         occupation="Ylipappi", title="Avarath-kultin perustaja",
         faction="Avarath-kultti", alignment="Chaotic Evil",
         loc="loc_avarath_temple", stat="monster:Cultist", wealth="modest",
         appearance="Kiihkeä kulttipappi.",
         personality="Fanaattinen, mielen orjuuttama.",
         notes="Avarath-kultin toinen perustaja ja pääpappi; Abolethin "
               "aivopesemä.",
         tags=["cult", "clergy"]),
    dict(id="npc_avarath", name="Avarath (Aboleth)", race="Aboleth", age="",
         occupation="Vale-jumala", title="", faction="Avarath-kultti",
         alignment="Lawful Evil", loc="loc_clay_shore",
         stat="monster:Aboleth", wealth="",
         appearance="Muinainen vedenalainen aberraatio.",
         personality="Itsekeskeinen, ikimuistoinen, manipuloiva.",
         notes="Kultin palvoma \"jumala\" — todellisuudessa muinainen "
               "Aboleth, joka pesee palvojiensa mielet fanaattisiksi "
               "orjiksi. Piileskelee vedenalaisella alueella sataman "
               "tuntumassa.",
         tags=["antagonist", "aberration"]),

    # ===== VILEMOUR =====
    dict(id="npc_varros", name="Varros Greycairn", race="Human", age="",
         occupation="Lordi", title="Vilemourin lordi",
         faction="Brotherhood of Glorious Sun", alignment="Lawful Evil",
         loc="loc_vilemour", stat="monster:Noble", wealth="wealthy",
         appearance="Korskea, ylellisesti pukeutunut lordi.",
         personality="Korruptoitunut, pelokas sätkynukke.",
         notes="Hallitsee Vilemouria Brotherhoodin sätkynukkena; peittelee "
               "kaupungin alla toimivaa biokoe-laboratoriota.",
         tags=["ruler", "brotherhood"]),
    dict(id="npc_xalyth", name="Xalyth", race="Drow", age="",
         occupation="Tiedustelija", title="", faction="Aterterra",
         alignment="Lawful Evil", loc="loc_vilemour", stat="monster:Spy",
         wealth="modest",
         appearance="Varjoissa liikkuva drow-tiedustelija.",
         personality="Tarkkaavainen, kärsivällinen.",
         notes="Salainen drow-tiedustelija Vilemourin alla.",
         tags=["spy", "drow"]),

    # ===== VEKSLA — 'Night of the Heart' -jälkeinen =====
    dict(id="npc_artur_potvark", name="Artur Potvark", race="Human",
         age="", occupation="Paroni (velkaantunut)", title="Vekslan paroni",
         faction="", alignment="Neutral", loc="loc_veksla",
         stat="monster:Noble", wealth="poor",
         appearance="Rähjääntynyt, velkojen murtama entinen aatelinen.",
         personality="Toivoton, kyvytön.",
         notes="Vekslan nimellinen paroni — korviaan myöten veloissa ja "
               "käytännössä poissa pelistä. Valta on väliaikaisella "
               "Vanhimpien Neuvostolla ja Metsän Suojelijoilla. Mavielf "
               "kiristää häntä tuomaan metsälle ruokaa.",
         tags=["ruler"]),
    dict(id="npc_idefian", name="Idefian", race="Dryad", age="",
         occupation="Metsän suojelijoiden johtaja", title="",
         faction="Metsän suojelijat", alignment="Chaotic Neutral",
         loc="loc_veksla", stat="monster:Dryad", wealth="",
         appearance="Kaunis, uhkaava dryadi.",
         personality="Kostonhaluinen luonnon puolustaja.",
         notes="Johtaa Metsän Suojelijoita — dryadiryhmää jonka Ulvin isä "
               "Bram Boulderroot aikoinaan perusti. Nälkäisen metsän "
               "olennot hyökkäävät Vekslaan.",
         tags=["fey"]),
    dict(id="npc_mavielf", name="Mavielf", race="Dryad", age="",
         occupation="Metsän suojelija", title="", faction="Metsän suojelijat",
         alignment="Chaotic Neutral", loc="loc_veksla", stat="monster:Dryad",
         wealth="",
         appearance="Ison tammen dryadi 2 km kylästä pohjoiseen.",
         personality="Uhkaava, nälän ajama.",
         notes="Kiristää ja uhkailee Vekslan paronia tuomaan metsälle "
               "ruokaa.",
         tags=["fey"]),
    dict(id="npc_jay_upto", name="Jay Upto", race="Werebear", age="",
         occupation="Karhumies", title="", faction="Metsän suojelijat",
         alignment="Chaotic Neutral", loc="loc_veksla",
         stat="monster:Wereboar", wealth="poor",
         appearance="Pitkät ruskeat hiukset, leveä hymy; karhumies.",
         personality="Leppoisa mutta vaarallinen.",
         notes="Dryadien 'lihasvoima'; liikkuu Vekslan kaduilla etsimässä "
               "ruokaa tovereilleen ja kiristää hallintoa. Suunniteltu "
               "CR 5 (Werebear). Stat-proxy: Wereboar.",
         tags=["shapeshifter", "fey"]),
    # -- Faunder Farm --
    dict(id="npc_timotei", name="Timotei Faunder", race="Human", age="",
         occupation="Maanviljelijä", title="Faunderin tilan omistaja",
         faction="", alignment="Neutral Good", loc="loc_faunder_farm",
         stat="monster:Commoner", wealth="poor",
         appearance="Työteliäs, vähäpuheinen maanviljelijä.",
         personality="Vaitonainen, surun murtama.",
         notes="Faunderin tilan omistaja; vaimo Elisa (Fausterin sisko) "
               "kuoli Fausterin rituaalissa ladossa.",
         tags=["farmer"]),
    dict(id="npc_elisa_ghost", name="Elisan Haamu", race="Human (Haamu)",
         age="", occupation="Levoton henki", title="", faction="",
         alignment="Neutral", loc="loc_faunder_farm", stat="monster:Ghost",
         wealth="", alive=False,
         appearance="Timotein vaimon levoton henki.",
         personality="Suruinen, rauhaton.",
         notes="Kuoli Fausterin rituaalissa; vaeltaa öisin ladon ja "
               "kurpitsapellon läheisyydessä.",
         tags=["undead"]),
    dict(id="npc_gurug", name="Gurug Brask", race="Half-Orc", age="38",
         occupation="Maatyöläinen", title="", faction="",
         alignment="Lawful Good", loc="loc_faunder_farm",
         stat="monster:Assassin", wealth="poor",
         appearance="Jäntevä, hiljainen puoliörkki-maatyöläinen.",
         personality="Rauhaa etsivä, periaatteellinen.",
         notes="DM-SALAISUUS: CR 8 veteraani ja entinen Aesican Puna-armeijan "
               "alikomentaja, joka kieltäytyi siviilien teloituksista ja "
               "pakeni. Hautasi hihamerkkinsä kurpitsapenkkiin; Tomas "
               "varasti hänen armeijamiekkansa heinävajaan. Stat-proxy: "
               "Assassin (veteraani).",
         tags=["farmer", "veteran", "secret"]),
    dict(id="npc_tomas_farm", name="Tomas (Faunderin tila)", race="Human",
         age="", occupation="Maatyöläinen", title="", faction="",
         alignment="Chaotic Neutral", loc="loc_faunder_farm",
         stat="monster:Commoner", wealth="poor",
         appearance="Laiska, kiero työntekijä.",
         personality="Ahne, vilpillinen.",
         notes="Varastaa viljaa (Lemin kanssa) myydäkseen pimeästi; "
               "piilotti Gurugin vanhan armeijamiekan heinävajaan.",
         tags=["farmer", "criminal"]),
    # -- Kylä --
    dict(id="npc_antos_erdofek", name="Antos Erdofek", race="Human", age="62",
         occupation="Kauppias", title="Anthos General Storen pitäjä",
         faction="", alignment="Neutral Good", loc="loc_anthos_store",
         stat="monster:Scout", wealth="wealthy",
         appearance="Silmälasipäinen, kodikas kauppias.",
         personality="Ystävällinen, vaatimaton — salaa varovainen.",
         notes="Entinen aarteenmetsästäjä, salaa erittäin rikas (löysi "
               "Vihreän Runekiven ytimen Efousetin kaivoksista). Tukee "
               "kylän jälleenrakennusta salaa; jokin metsän suunnassa "
               "tarkkailee häntä öisin. Stat-proxy: Scout.",
         tags=["merchant", "secret"]),
    dict(id="npc_andur", name="Andur Brokvard", race="Dwarf", age="",
         occupation="Majatalonpitäjä / kokki", title="", faction="",
         alignment="Neutral Good", loc="loc_feather_pillow",
         stat="monster:Commoner", wealth="modest",
         appearance="Lämminhenkinen kääpiökokki.",
         personality="Vieraanvarainen, työteliäs.",
         notes="Pyörittää Feather Pillow Inniä veljiensä Loksarin (siivooja) "
               "ja Enquestin kanssa.",
         tags=["innkeeper"]),
    dict(id="npc_sylrieth", name="Sylrieth", race="Tiefling", age="",
         occupation="Majatalon \"johtaja\"", title="", faction="",
         alignment="Neutral", loc="loc_feather_pillow", stat="monster:Spy",
         wealth="comfortable",
         appearance="Salamyhkäinen, viehättävä kaksonen.",
         personality="Karismaattinen, arvoituksellinen.",
         notes="Toinen Feather Pillow Innin uusista salamyhkäisistä "
               "kaksosista (Thyriethin sisar); todellinen luonto tuntematon.",
         tags=["mysterious"]),
    dict(id="npc_thyrieth", name="Thyrieth", race="Tiefling", age="",
         occupation="Majatalon \"johtaja\"", title="", faction="",
         alignment="Neutral", loc="loc_feather_pillow", stat="monster:Spy",
         wealth="comfortable",
         appearance="Salamyhkäinen, viehättävä kaksonen.",
         personality="Karismaattinen, arvoituksellinen.",
         notes="Toinen Feather Pillow Innin uusista kaksosista (Sylriethin "
               "sisar); todellinen luonto tuntematon.",
         tags=["mysterious"]),
    dict(id="npc_caromaik", name="Sir Caromaik von Ermizen", race="Imp",
         age="", occupation="Pokerinpelaaja", title="", faction="",
         alignment="Lawful Evil", loc="loc_feather_pillow", stat="",
         wealth="modest",
         appearance="Pieni, ovela paholainen (imp).",
         personality="Viekas, viihdyttävä.",
         notes="Piileskelee majatalon ullakolla ja pelaa pokeria. "
               "Stat: Imp (ei kirjastossa — DM lisää).",
         tags=["fiend", "mysterious"]),
    dict(id="npc_vendimo", name="Isä Vendimo Aarsentop", race="Human",
         age="", occupation="Pappi", title="Aghuantin temppelin pappi",
         faction="Aghuant", alignment="Neutral", loc="loc_veksla_temple",
         stat="monster:Acolyte", wealth="poor", alive=False,
         appearance="Uskonsa menettänyt pappi.",
         personality="Epätoivoinen, murtunut.",
         notes="Menetti uskonsa ja tuhosi satoa; vihreä kasvimassa otti "
               "vallan hänen kehostaan ja tappoi hänet sisältäpäin. "
               "KUOLLUT. Temppeli naulattu umpeen.",
         tags=["clergy", "deceased"]),
    dict(id="npc_zetris", name="Kapteeni Zetris", race="Human", age="",
         occupation="Kapteeni / virkamies", title="", faction="Tarmaas",
         alignment="Lawful Neutral", loc="loc_veksla", stat="monster:Scout",
         wealth="comfortable",
         appearance="Tarkka, virallinen kapteeni.",
         personality="Kylmä, velvollisuudentuntoinen.",
         notes="Järjesti majatalolla väijytyksen ja pidätti Thomaksen "
               "(joka on sittemmin matkalla pois kaupungista).",
         tags=["law"]),
    dict(id="npc_fauster", name="Fauster", race="Human", age="",
         occupation="Nekromantikko", title="", faction="",
         alignment="Neutral Evil", loc="", stat="monster:Archmage",
         wealth="modest", alive=False,
         appearance="Synkkä nekromantikko koirineen.",
         personality="Kostonhaluinen, mielipuolinen.",
         notes="Aiheutti 'Night of the Heart' -verilöylyn (nostatti "
               "epäkuolleita, koirat tappoivat vartioston). Sankarit Kaldir "
               "ja Ailas pysäyttivät hänet. KUOLLUT/kukistettu. "
               "Stat-proxy: Archmage (nekromantikko).",
         tags=["antagonist", "undead", "deceased"]),
    dict(id="npc_kaldir", name="Kaldir", race="Human", age="",
         occupation="Vaeltava sankari", title="", faction="",
         alignment="Neutral Good", loc="loc_veksla", stat="monster:Assassin",
         wealth="modest",
         appearance="Karaistunut, arpinen soturi.",
         personality="Itsenäinen, oikeudenmukainen.",
         notes="Gaius Maradin poika, joka lähti Death's Vigilistä. Pysäytti "
               "(Ailasin kanssa) nekromantikko Fausterin ja pelasti "
               "Vekslan. Stat-proxy: Assassin.",
         tags=["ally", "hero"]),
    dict(id="npc_ailas", name="Ailas", race="Half-Elf", age="",
         occupation="Vaeltava sankari", title="", faction="",
         alignment="Neutral Good", loc="loc_veksla", stat="monster:Scout",
         wealth="modest",
         appearance="Ketterä, tarkkaavainen seikkailija.",
         personality="Lojaali, rohkea.",
         notes="Kaldirin toveri; auttoi pysäyttämään Fausterin Vekslassa.",
         tags=["ally", "hero"]),

    # ===== HIJOIN / FAT CARP / ARIST / ZAPRUTAS =====
    dict(id="npc_carl_gronmort", name="Carl Grönmort", race="Human", age="",
         occupation="Kreivi", title="Hijoinin kreivi", faction="Tarmaas",
         alignment="Lawful Neutral", loc="loc_hijoin", stat="monster:Noble",
         wealth="wealthy",
         appearance="Ankara aateliskreivi.",
         personality="Itsepäinen, valtaa puolustava.",
         notes="Hijoinin hallitsija; konfliktissa C.H.O.M.P.-tutkijoiden "
               "kanssa.",
         tags=["ruler"]),
    dict(id="npc_beur", name="Beur Ironface", race="Dwarf", age="",
         occupation="Kapteeni", title="Fat Carpin kapteeni", faction="",
         alignment="Neutral", loc="loc_fat_carp", stat="monster:Thug",
         wealth="modest",
         appearance="Rautanaamainen, karski merikapteeni.",
         personality="Suora, epäluuloinen.",
         notes="Fat Carpin satamakylän johtaja.",
         tags=["ruler"]),
    dict(id="npc_cyra_nesh", name="Cyra Nesh", race="Human", age="",
         occupation="Kaupunginjohtaja", title="Aristin johtaja",
         faction="Fey Hunter's Lodge", alignment="Neutral",
         loc="loc_arist", stat="monster:Scout", wealth="comfortable",
         appearance="Kokenut metsästäjä-johtaja.",
         personality="Käytännöllinen, valpas.",
         notes="Johtaa Aristia ja Fey Hunter's Lodgea.",
         tags=["ruler"]),
    dict(id="npc_zapui", name="Zapui Gerzoip", race="Gnome", age="",
         occupation="Pormestari", title="Zaprutaksen pormestari",
         faction="", alignment="Neutral Good", loc="loc_zaprutas",
         stat="monster:Noble", wealth="modest",
         appearance="Innokas, öljytahrainen gnomi-insinööri.",
         personality="Nokkela, yhteisöllinen.",
         notes="Johtaa maanalaista gnomi-yhteisöä; kivihirviöt sabotoivat "
               "kaasulinjoja.",
         tags=["ruler"]),

    # ===== FUNDARLA =====
    dict(id="npc_endail", name="Endail Un'faelie", race="Elf", age="",
         occupation="Neuvoston jäsen", title="Fundarlan neuvosto",
         faction="Fundarlan neuvosto", alignment="Neutral Good",
         loc="loc_zlalens", stat="monster:Archmage", wealth="wealthy",
         appearance="Arvokas haltiamaagi.",
         personality="Harkitseva, idealistinen.",
         notes="Fundarlan neuvoston jäsen Zlalensissa.",
         tags=["ruler", "scholar"]),
    dict(id="npc_hailaf", name="Hailaf Moonborn", race="Elf", age="",
         occupation="Ylipappi", title="Shanta-temppelin ylipappi",
         faction="Shanta-temppeli", alignment="Lawful Good",
         loc="loc_asmenor", stat="monster:Archmage", wealth="comfortable",
         appearance="Seesteinen haltiapappi.",
         personality="Rauhallinen, suojeleva.",
         notes="Asmenorin Shanta-temppelin ylipappi.",
         tags=["clergy", "ruler"]),
    dict(id="npc_runlian", name="Runlian Dafou Visedimor", race="Half-Elf",
         age="", occupation="Virkamies", title="Cifirin virkamies",
         faction="Fundarla", alignment="Lawful Neutral", loc="loc_cifiri",
         stat="monster:Noble", wealth="comfortable",
         appearance="Hillitty, huoliteltu virkamies.",
         personality="Velvollisuudentuntoinen.",
         notes="Hallitsee Cifirin satamakaupunkia; uhattuna Hanons "
               "Oldarfokin toimesta.",
         tags=["ruler"]),
    dict(id="npc_hanons", name="Hanons Oldarfok", race="Half-Elf", age="",
         occupation="Kilpailija", title="", faction="",
         alignment="Lawful Evil", loc="loc_cifiri", stat="monster:Spy",
         wealth="comfortable",
         appearance="Kunnianhimoinen, viekas.",
         personality="Vallanhaluinen, juonitteleva.",
         notes="Yrittää syrjäyttää Runlian Dafounin Cifirissä; kytköksiä "
               "kidnappauksiin.",
         tags=["rival"]),

    # ===== ATERTERRA — Underdark / drow-huoneet =====
    dict(id="npc_cazna", name="Cazna Icharyd", race="Drow", age="3500+",
         occupation="Matriarkka", title="Aterterran matriarkka",
         faction="Talo Icharyd", alignment="Chaotic Evil",
         loc="loc_zertath_lanke", stat="monster:Cazna Icharyd",
         wealth="aristocratic",
         appearance="Mahtava, ajaton drow-matriarkka; kantaa "
                     "kristallikruunua johon on vangittu keisari "
                     "Tarquvasin sielu.",
         personality="Ei paha pahuudesta vaan kosmisesta PTSD:stä — "
                     "epätoivoinen Atlas, joka kantaa maailmanlopun "
                     "huutoa mielessään.",
         notes="Zer'tath Lanken hallitsija. TIETÄÄ totuuden: puhdasveriset "
               "drowt kuulevat Faerzress-kristallien säteilyn kauniina "
               "'Syvyyden Unena', mutta Cazna kuulee kahlitun titaani "
               "Garruthan raastavan huudon. Ruokkii salaa Vanqurionin "
               "Sarrukh-sielukonetta Kristallijärven pohjassa ('Syvyyden "
               "Kaste' — tuomitut pudotetaan elävinä kuiluun); tämä pitää "
               "hänet ikuisesti nuorena. Eristi drowt maan alle "
               "suojellakseen konetta ja peittääkseen valheen.",
         tags=["ruler", "drow", "antagonist"]),
    dict(id="npc_altheon", name="Altheon Vylarien Baenrahel", race="Drow",
         age="", occupation="Aether-arkistojen johtaja", title="Lordi",
         faction="Talo Baenrahel", alignment="Lawful Evil",
         loc="loc_zertath_lanke", stat="monster:Archmage", wealth="wealthy",
         appearance="Arvokas ja synkkä drow-mies; kantaa sinistä kristallia "
                     "(sielufokus).",
         personality="Ei vihollinen vaan vanki — kylmä pinta peittää "
                     "vuosikymmenten surun.",
         notes="Beatricen biologinen isä ja matriarkka Caznan oikea käsi; "
               "huoltaa sekä Faerzress-verkostoa että Vanqurionin "
               "sielukonetta. Pelasti aikoinaan koko kaupungin projekti "
               "'Kaiun' avulla yhdessä ihmistutkija Seraphinan kanssa — "
               "siksi Cazna ei voi tappaa häntä. Rakastui Seraphinaan; "
               "kun Beatrice (Dobluth Dro) syntyi, Altheon suostui The "
               "Veilin Geas-loitsuun (ei saa etsiä perhettään) pitääkseen "
               "heidät turvassa. Stat-proxy: Archmage.",
         tags=["drow", "noble"]),
    dict(id="npc_amalica", name="Amalica Coloara Despana", race="Drow",
         age="", occupation="Ilharess", title="Talo Despanan ilharess",
         faction="Talo Despana", alignment="Neutral Evil",
         loc="loc_vlyn_darahl", stat="monster:Archmage", wealth="aristocratic",
         appearance="Hallitseva drow-aatelisnainen.",
         personality="Laskelmoiva kauppias-matriarkka.",
         notes="Johtaa Talo Despanaa (Kaupan Kruunu) — maanalainen "
               "logistiikka ja salainen pintakauppa.",
         tags=["drow", "ruler"]),
    dict(id="npc_zekarra", name="Zekarra Despana", race="Drow", age="",
         occupation="Kaupunginjohtaja", title="Vlyn'Darahlin johtaja",
         faction="Talo Despana", alignment="Neutral Evil",
         loc="loc_vlyn_darahl", stat="monster:Archmage", wealth="wealthy",
         appearance="Terävä-älyinen drow-kauppias.",
         personality="Opportunistinen.",
         notes="Hallitsee Vlyn'Darahlia, drowien pinnanporttia.",
         tags=["drow", "ruler"]),
    dict(id="npc_urlryn", name="Urlryn Vel'kath", race="Drow", age="",
         occupation="Kaupunginjohtaja", title="Neldrath Zolin johtaja",
         faction="Talo Vel'kath", alignment="Lawful Evil",
         loc="loc_neldrath_zol", stat="monster:Assassin", wealth="wealthy",
         appearance="Ankara drow-teollisuusruhtinas.",
         personality="Kova, tuottoa tavoitteleva.",
         notes="Hallitsee Neldrath Zolin hopeakaivoksia.",
         tags=["drow", "ruler"]),
    dict(id="npc_talice", name="Talice Vel'kath", race="Drow", age="",
         occupation="Orjien vapauttaja", title="", faction="",
         alignment="Chaotic Good", loc="loc_neldrath_zol", stat="monster:Spy",
         wealth="modest",
         appearance="Salaisuuksia kantava nuori drow.",
         personality="Rohkea, myötätuntoinen.",
         notes="Salainen orjien vapauttaja, joka operoi Neldrath Zolissa.",
         tags=["drow", "rebel", "ally"]),
    dict(id="npc_dantrag", name="Dantrag Dyrr", race="Drow", age="",
         occupation="Sotapäällikkö", title="Ultrinnanin ilharn",
         faction="Talo Dyrr", alignment="Lawful Evil", loc="loc_ultrinnan",
         stat="monster:Dantrag Dyrr", wealth="wealthy",
         appearance="Massiivinen, panssaroitu drow-soturi.",
         personality="Aggressiivinen, vallanhimoinen.",
         notes="Velve Dro -armeijan komentaja; suunnittelee "
               "sotilasvallankaappausta pintamaailmaa vastaan.",
         tags=["drow", "military"]),
    dict(id="npc_nhilymra", name="Nhilymra Zaer'vyn", race="Drow", age="",
         occupation="Ilharess", title="Vorzhan ilharess",
         faction="Talo Zaer'vyn", alignment="Lawful Evil", loc="loc_vorzha",
         stat="monster:Nhilymra Zaer'vyn", wealth="wealthy",
         appearance="Hiljainen, tappavan tyylikäs drow-matriarkka.",
         personality="Salaperäinen, laskelmoiva.",
         notes="Johtaa Vorzhan salamurhaaja- ja tiedusteluverkostoa "
               "(Shadow Puppets).",
         tags=["drow", "spy"]),
    dict(id="npc_ahlysra", name="Ahlysra Szith'ryn", race="Drow", age="",
         occupation="Oraakkeli", title="Sokea oraakkeli",
         faction="Unenkulkijat", alignment="Neutral", loc="loc_eryn_zalas",
         stat="monster:Archmage", wealth="modest",
         appearance="Sokea drow-profeetta.",
         personality="Mystinen, etäinen.",
         notes="Eryn'Zalasin Unenkulkijoiden temppelin oraakkeli.",
         tags=["drow", "oracle"]),
    dict(id="npc_qilue", name="Qilué Xarann", race="Drow", age="",
         occupation="Ilharess", title="Ithyl'Quorin ilharess",
         faction="Talo Xarann", alignment="Chaotic Evil", loc="loc_ithyl_quor",
         stat="monster:Archmage", wealth="wealthy",
         appearance="Biomagian mestari, hämähäkkimäiset piirteet.",
         personality="Kokeileva, julma.",
         notes="Hallitsee Ithyl'Quoria, biologisen magian ja metamorfoosien "
               "keskusta.",
         tags=["drow", "ruler"]),
    dict(id="npc_belgos", name="Belgos Dyrr", race="Drow", age="",
         occupation="Komentaja", title="Dro'Khazunin komentaja",
         faction="Talo Dyrr", alignment="Lawful Evil", loc="loc_dro_khazun",
         stat="monster:Assassin", wealth="comfortable",
         appearance="Karaistunut drow-upseeri.",
         personality="Sotilaallinen, järkkymätön.",
         notes="Komentaa Dro'Khazunia kääpiöiden vastaisella "
               "sotavyöhykkeellä.",
         tags=["drow", "military"]),
    dict(id="npc_azzmere", name="Azzmere Dyrr", race="Drow", age="",
         occupation="Kenraali", title="Kazrath Morin kenraali",
         faction="Talo Dyrr", alignment="Lawful Evil", loc="loc_kazrath_mor",
         stat="monster:Death Knight", wealth="wealthy",
         appearance="Pelottava drow-kenraali.",
         personality="Säälimätön orjapiiskuri.",
         notes="Johtaa Kazrath Morin orjien keräyskeskusta.",
         tags=["drow", "military"]),
    dict(id="npc_malaggar", name="Malaggar Zaer'vyn", race="Drow", age="",
         occupation="Agentti", title="Zar'Ghulin isäntä",
         faction="Talo Zaer'vyn", alignment="Neutral Evil", loc="loc_zar_ghul",
         stat="monster:Spy", wealth="comfortable",
         appearance="Liukas mustapörssikauppias.",
         personality="Ahne, vaarallinen.",
         notes="Pyörittää Zar'Ghulin mustapörssiä.",
         tags=["drow", "criminal"]),
    dict(id="npc_drathir", name="Vanhus Drathir", race="Drow", age="",
         occupation="Pakolaisvanhin", title="", faction="",
         alignment="Neutral", loc="loc_golgoth_inil", stat="monster:Cultist",
         wealth="poor",
         appearance="Sairas, sinnikäs drow-vanhus.",
         personality="Epätoivoinen, suojeleva.",
         notes="Johtaa Golgoth-Inilin pakolaisleiriä Spore Rot -ruton "
               "keskellä.",
         tags=["drow", "refugee"]),
    dict(id="npc_vaelra", name="Itiö-äiti Vaelra", race="Spore-thrall", age="",
         occupation="Ruton ruumiillistuma", title="", faction="Brotherhood of Glorious Sun",
         alignment="Neutral Evil", loc="loc_golgoth_inil",
         stat="monster:Shambling Mound", wealth="",
         appearance="Sienikasvun valtaama entinen drow.",
         personality="Tahdoton ruton levittäjä.",
         notes="Spore Rot -ruton ruumiillistuma Golgoth-Inilissä. "
               "Stat-proxy: Shambling Mound.",
         tags=["antagonist", "plague"]),

    # ===== TALO BAENRAHEL — Verkkojen Talo (palvelijoiden talo) =====
    dict(id="npc_elarae", name="Elarae Baenrahel", race="Drow", age="",
         occupation="Arkkimaagi-perijä", title="Talo Baenrahelin perijä",
         faction="Talo Baenrahel", alignment="Lawful Evil",
         loc="loc_verkkojen_talo", stat="monster:Elarae Baenrahel",
         wealth="wealthy",
         appearance="Pitkät moitteettomat hopeahiukset, joihin punottu "
                     "mustia obsidiaanihelmiä; viileät violetit silmät; "
                     "tummansiniset silkki- ja nahkakaavut.",
         personality="Kylmä, laskelmoiva, äärimmäisen älykäs.",
         notes="Beatricen siskopuoli — Altheonin virallinen perijä ja "
               "tuleva arkkimaagi. Vierailee palvelijoiden talossa "
               "käyttääkseen palvelijoita salaisten kokeidensa "
               "koekaniineina. Epäilee isällään olevan salaisuus ja etsii "
               "vipuvartta tätä vastaan.",
         tags=["drow", "noble", "baenrahel"]),
    dict(id="npc_dravin", name="Dravin Baenrahel", race="Drow", age="",
         occupation="Velve Dro -upseeri", title="Suvun sotilaallinen nyrkki",
         faction="Talo Baenrahel", alignment="Lawful Evil",
         loc="loc_verkkojen_talo", stat="monster:Dravin Baenrahel",
         wealth="comfortable",
         appearance="Poikkeuksellisen lihaksikas drow-mies; raskas "
                     "piikikäs drow-haarniska, kaksi myrkytettyä "
                     "lyhytmiekkaa, ylimielinen virne.",
         personality="Halveksuu palvelijoita, näkee heidät pelkkänä lihana.",
         notes="Beatricen velipuoli. Velve Dro -armeijan upseeri, ei maagi. "
               "Saattaa saapua palvelijoiden taloon tarkastamaan "
               "ratsuliskoja juuri kun pelaajat ilmestyvät.",
         tags=["drow", "noble", "baenrahel", "military"]),
    dict(id="npc_vorn", name="Vorn Xorlath", race="Drow", age="",
         occupation="Vartiokapteeni", title="Verkkojen Talon vartiokapteeni",
         faction="Talo Baenrahel", alignment="Lawful Neutral",
         loc="loc_verkkojen_talo", stat="monster:Scout", wealth="modest",
         appearance="Poikkinaisen miekan arpeuttamat kasvot, katkennut "
                     "torahammas; kantaa raskasta varsijousta.",
         personality="Kyyninen ja pragmaattinen; lojaali kullalle ja "
                     "vallalle, ei aatteelle.",
         notes="Xorlath-suvun päämies, talon vartijoiden johtaja. On "
               "tappanut kymmeniä salamurhaajia suvun puolesta saamatta "
               "kunniaa. Tuntee jokaisen salakäytävän — voi myydä pelaajille "
               "reitin Altheonin Aether-arkistoon jos maksu on oikea.",
         tags=["drow", "guard"]),
    dict(id="npc_nymia", name="Nymia Xorlath", race="Drow", age="",
         occupation="Tiedustelija / ovivahti", title="",
         faction="Talo Baenrahel", alignment="Lawful Neutral",
         loc="loc_verkkojen_talo", stat="monster:Spy", wealth="poor",
         appearance="Pieni, ketterä ja hermostuneesti liikkuva nuori "
                     "drow-nainen; tummanharmaa viitta.",
         personality="Tarkkaavainen, hermostunut, utelias.",
         notes="Vornin tytär. Piileskelee talon kattopalkeissa ja kuuntelee "
               "kaikkea — todennäköisesti ensimmäinen joka huomaa "
               "tunkeutujat.",
         tags=["drow", "spy"]),
    dict(id="npc_thala", name="Thala Myrdin", race="Drow", age="400+",
         occupation="Pääemäntä", title="Matroona",
         faction="Talo Baenrahel", alignment="Neutral", loc="loc_verkkojen_talo",
         stat="monster:Commoner", wealth="poor",
         appearance="Yli 400-vuotias drow-nainen; oikea silmä täysin "
                     "valkoinen ja sokea; kädet täynnä happo- ja "
                     "palovammoja.",
         personality="Nähnyt kaiken; tietää tarkkaan milloin teeskennellä "
                     "sokeaa.",
         notes="Palvelijoiden epävirallinen johtaja. Muistaa, että Altheon "
               "toi vuosia sitten kartanoon ihmisnaisen (Seraphinan) salaa "
               "ja suree tätä yhä. Voi piilottaa pelaajat välttääkseen "
               "aatelisten raivon. Tietää vaimennuskentän 'kuolleet "
               "kulmat'.",
         tags=["drow", "servant"]),
    dict(id="npc_kael_myrdin", name="Kael Myrdin", race="Drow", age="30",
         occupation="Keittiöpoika / lihankantaja", title="",
         faction="Talo Baenrahel", alignment="Neutral Good",
         loc="loc_verkkojen_talo", stat="monster:Commoner", wealth="poor",
         appearance="Laiha, huonosti ruokittu drow-nuorukainen (lapsi "
                     "drow-iässä); vaatteet veressä petojen ruokkimisesta.",
         personality="Utelias ja naiivi; vihaa kohtaloaan.",
         notes="Haluaisi paeta pintamaailmaan, josta on vain kuullut "
               "tarinoita. Kairon voi helposti puhua pojan puolelleen.",
         tags=["drow", "servant"]),
    dict(id="npc_zirkass", name="Zir'kass", race="Drow", age="",
         occupation="Tallimestari", title="Petojen kesyttäjä",
         faction="Talo Baenrahel", alignment="Neutral", loc="loc_verkkojen_talo",
         stat="monster:Scout", wealth="poor",
         appearance="Vasemmasta kädestä puuttuu kolme sormea; haisee "
                     "happamalta hämähäkin myrkyltä; paksut nahkasuojalasit.",
         personality="Välittää eläimistä enemmän kuin droweista.",
         notes="Vastaa Baenrahelin ratsuliskoista ja vahtihämähäkeistä; "
               "pumppaa hämähäkinmyrkkyä suvun aseisiin. Voi usuttaa "
               "kymmeniä jättihämähäkkejä yhdellä vihellyksellä. Aistii "
               "että 'jokin syvyyksissä on hereillä — kiteet murtuvat "
               "sisältäpäin'.",
         tags=["drow", "beastmaster"]),
    dict(id="npc_faldor", name="Faldor \"Sokea Kipinä\"", race="Drow", age="",
         occupation="Kristallien huoltaja", title="",
         faction="Talo Baenrahel", alignment="Neutral", loc="loc_verkkojen_talo",
         stat="monster:Commoner", wealth="poor",
         appearance="Äärimmäisen vanha, pahasti kumarassa kävelevä drow; "
                     "sormenpäät mustuneet kristallien säteilystä.",
         personality="Hiljainen, sisäänpäin kääntynyt.",
         notes="JUONIKOUKKU: ylläpitää talon faerzress-sirpaleita ja on "
               "itse laimeaa Dobluth Dro -verta (puoliverinen usean "
               "sukupolven takaa). On oppinut sulkemaan mielensä "
               "kristallien huudolta; jos näkee Beatricen reagoivan "
               "kristalleihin, voi tunnistaa hengenheimolaisensa ja auttaa "
               "paljastamaan uskonnon valheen.",
         tags=["drow", "servant", "plot_hook"]),
    dict(id="npc_vhaerani", name="Vhaerani Icharyd", race="Drow", age="2200",
         occupation="Salainen perillinen", title="Varjojen tytär",
         faction="Talo Icharyd", alignment="Neutral Evil",
         loc="loc_zertath_lanke", stat="monster:Assassin", wealth="wealthy",
         appearance="Näyttää drow'ksi kolmekymppiseltä, mutta katse on "
                     "kahden vuosituhannen ikäinen.",
         personality="Ei tunne sääliä; kasvatettu aseeksi.",
         notes="Caznan salainen tytär ja perillinen, pidetty poissa "
               "politiikasta yli 2000 vuotta palatsin syvimmissä "
               "kammioissa laitteen lähellä. On harjoitellut taistelua, "
               "salamurhaa ja magiaa kaksi vuosituhatta putkeen ja lukee "
               "vastustajan liikkeet ennen iskua. Suvun perimmäinen ase — "
               "boss-tier, vielä äitiään pelottavampi. Stat-proxy: "
               "Assassin (skaalaa ylös).",
         tags=["drow", "assassin", "boss", "secret"]),
    dict(id="npc_xalyra", name="Xalyra Icharyd", race="Drow", age="",
         occupation="Varjojen äiti", title="Kuiskaaja verhon takana",
         faction="Talo Icharyd", alignment="Lawful Evil",
         loc="loc_zertath_lanke", stat="monster:Archmage", wealth="aristocratic",
         appearance="Ikivanha drow-matriarkka, joka pysyttelee varjoissa.",
         personality="Laskelmoiva, kärsivällinen, näkymätön vallankäyttäjä.",
         notes="Caznan äiti — nainen joka alun perin löysi Vanqurionin "
               "sielukoneen ja oppi käyttämään sitä. Vetäytyi varjoihin "
               "'Kuiskaajaksi verhon taakse' johtaen tytärtään; ajoi "
               "Lex Claustrumin (vetäytymisen lain) jottei kukaan pääsisi "
               "alas löytämään konetta.",
         tags=["drow", "mastermind", "secret"]),

    # ===== ZER'TATH LANKE — hovi, kauppiaat & slummi =====
    dict(id="npc_pharaun", name="Pharaun Dyrr", race="Drow", age="",
         occupation="Arcane Trickster", title="Matriarkan salainen ilmiantaja",
         faction="Talo Dyrr", alignment="Neutral Evil", loc="loc_zertath_lanke",
         stat="monster:Assassin", wealth="wealthy",
         appearance="Ovela, hienostunut drow-veijari.",
         personality="Viekas, kaksinaamainen, itsesuojelullinen.",
         notes="Dantragin veli ja Matriarkan salainen ilmiantaja. Ovela "
               "pakoilu, illuusiot ja arcane trickster -temput. "
               "Suunniteltu CR 9 (Rogue 8 / Wizard 4). Stat-proxy: Assassin.",
         tags=["drow", "spy", "high_court"]),
    dict(id="npc_valas_szithryn", name="Valas Szith'ryn", race="Drow", age="",
         occupation="Bardi / poliittinen käsi", title="",
         faction="Talo Szith'ryn", alignment="Neutral Evil",
         loc="loc_zertath_lanke", stat="monster:Archmage", wealth="wealthy",
         appearance="Kaunopuheinen, myrkyllisen viehättävä drow.",
         personality="Petollinen, manipuloiva.",
         notes="Szith'rynin suvun poliittinen 'maallinen käsi' "
               "pääkaupungissa; keskittyy psyykkiseen vahinkoon ja "
               "petokseen. Suunniteltu CR 8 (Bard 9, Whispers). "
               "Stat-proxy: Archmage (bardi).",
         tags=["drow", "high_court", "bard"]),
    dict(id="npc_zhindia", name="Zhindia Oblodra", race="Drow", age="",
         occupation="Psion", title="Hiljainen Kuningatar",
         faction="Talo Oblodra", alignment="Lawful Evil",
         loc="loc_zertath_lanke", stat="monster:Zhindia Oblodra",
         wealth="wealthy",
         appearance="Kylmä, leijuva mielenlukija.",
         personality="Etäinen, kaikkinäkevä, armoton.",
         notes="Mielenlukijoiden (Oblodra) johtaja; hallitsee Dusklornista "
               "mutta ulottaa telepaattisen otteensa pääkaupunkiin. Raskas "
               "psioniikka ja mielenhallinta.",
         tags=["drow", "high_court", "psion"]),
    dict(id="npc_szoraya", name="Szoraya Baenrahel", race="Drow", age="",
         occupation="Divinaatiovelho", title="", faction="Talo Baenrahel",
         alignment="Neutral", loc="loc_verkkojen_talo", stat="monster:Archmage",
         wealth="wealthy",
         appearance="Tarkkasilmäinen, mietteliäs drow-velho.",
         personality="Utelias totuudenetsijä.",
         notes="Altheonin sisar, joka etsii totuutta (mm. isänsä "
               "salaisuuksista). Divination-velho (Portent). Suunniteltu "
               "CR 10 (Wizard 12). Stat-proxy: Archmage.",
         tags=["drow", "baenrahel", "scholar"]),
    dict(id="npc_naerthali", name="Naerthali Szith'ryn", race="Drow", age="",
         occupation="Ylipapitar", title="Sokean Totuuden Pyhäkön pääpapitar",
         faction="Reverie-kultti", alignment="Lawful Evil",
         loc="loc_sokean_totuuden_pyhakko", stat="monster:Archmage",
         wealth="wealthy",
         appearance="Sokea, faerzress-sirpaleilla koristeltu papitar.",
         personality="Fanaattinen, hurmoksellinen.",
         notes="Zha'lin-aukion Sokean Totuuden Pyhäkön fanaattinen "
               "pääpapitar; blindsight ja raskaat radiant/psychic-loitsut. "
               "Suunniteltu CR 9–11. Stat-proxy: Archmage.",
         tags=["drow", "clergy"]),
    dict(id="npc_vornak", name="Pyöveli Vornak", race="Drow", age="",
         occupation="Pyöveli", title="Tuhkakuilun pyöveli",
         faction="", alignment="Lawful Evil", loc="loc_tuhkakuilu",
         stat="monster:Half-Ogre", wealth="poor",
         appearance="Kieletön jättiläis-drow, arpien peitossa.",
         personality="Tunteeton, säälimätön.",
         notes="Tuhkakuilun kieletön jättiläis-drow-pyöveli; raakaa voimaa, "
               "grapple ja kuilun reunan insta-kill. Suunniteltu CR 8–10. "
               "Stat-proxy: Half-Ogre (skaalaa ylös).",
         tags=["drow", "executioner"]),
    dict(id="npc_valas_pharn", name="Valas Pharn", race="Drow", age="",
         occupation="Antikvariaatin pitäjä", title="Mustan pörssin kauppias",
         faction="", alignment="Neutral", loc="loc_rotanhammas",
         stat="monster:Spy", wealth="comfortable",
         appearance="Liukas, salaperäinen kirjakauppias.",
         personality="Varovainen, tiedonnälkäinen.",
         notes="'Kuiskausten Lasi' -antikvariaatin pitäjä ja mustan pörssin "
               "kauppias; illuusioita ja pakenemismekaniikkoja. Suunniteltu "
               "CR 4–6. Stat-proxy: Spy.",
         tags=["drow", "merchant", "criminal"]),
    dict(id="npc_xune", name="Xune T'sarran", race="Drow", age="",
         occupation="Alkemisti / asekauppias", title="",
         faction="", alignment="Neutral", loc="loc_rotanhammas",
         stat="monster:Assassin", wealth="comfortable",
         appearance="Yksisilmäinen drow, happovammojen peitossa.",
         personality="Kokeileva, vaarallinen.",
         notes="'Myrkkykehrä' -asekaupan pitäjä; myrkkypommit ja happoiskut. "
               "Suunniteltu CR 6–7 (Alchemist/Artificer). Stat-proxy: "
               "Assassin (myrkyt).",
         tags=["drow", "merchant"]),
    dict(id="npc_jarlax", name="Jarlax \"Silkki\" Melarn", race="Drow", age="",
         occupation="Bordellin pitäjä", title="", faction="",
         alignment="Chaotic Neutral", loc="loc_rotanhammas",
         stat="monster:Archmage", wealth="wealthy",
         appearance="Viettelevä, silkkiin pukeutunut drow-bardi.",
         personality="Karismaattinen, laskelmoiva.",
         notes="'Oloth's Caress' -bordellin pitäjä; tekee musiikkia "
               "kristalleja värisyttämällä (illuusiot). Suunniteltu CR 5–6 "
               "(Bard/Illusionist). Stat-proxy: Archmage (bardi).",
         tags=["drow", "merchant"]),
    dict(id="npc_thol", name="\"Murtunut\" Thol", race="Minotaur", age="",
         occupation="Gladiaattori-kapo", title="", faction="",
         alignment="Neutral", loc="loc_drakiel_slum",
         stat="monster:\"Murtunut\" Thol", wealth="poor",
         appearance="Arpinen, kieletön minotauri-orja.",
         personality="Raivokas areenalla, mutta kaipaa vapautta.",
         notes="Dra'kielin slummin tappeluklubin orja-kapo; Charge + Gore "
               "-profiili. Mahdollinen liittolainen Kruskille (orjasta "
               "orjalle).",
         tags=["gladiator", "potential_ally"]),

    # ===== INFERNAL DISC =====
    dict(id="npc_lucien", name="Lucien the Ledgerkeeper",
         race="Celestial (Sopimusten puolijumala)", age="",
         occupation="Puolijumala", title="Sopimusten valvoja",
         faction="Infernal Disc", alignment="Lawful Neutral", loc="",
         stat="monster:Planetar", wealth="aristocratic",
         appearance="Ulkoisesti 25–30 v: hopeiset hiukset, kalpeat piirteet, "
                     "elohopeasilmät; kantaa aina mustaa nahkaista "
                     "kirjanpidon kansiota.",
         personality="Kylmän tasapuolinen, ehdoton sopimusten valvoja.",
         notes="Asuu Infernal Discillä ja valvoo kosmista tasapainoa ja "
               "sielusopimuksia. Pitää Morgania, Dariusta ja Beatricea "
               "tiukasti otteessaan diilien kautta. Stat-proxy: Planetar.",
         tags=["demigod", "patron"]),
    dict(id="npc_nexoth", name="Nexoth Khar (Arch-Key)", race="Devil", age="",
         occupation="Arkkivaltias", title="Infernal Discin valtias",
         faction="Infernal Disc", alignment="Lawful Evil", loc="",
         stat="monster:Pit Fiend", wealth="aristocratic",
         appearance="Mahtava arkkivaltias, avainten herra.",
         personality="Ylimielinen, ehdoton.",
         notes="Hallitsee avaimia muihin tasoihin ja sanelee Discin ylimmän "
               "tahdon.",
         tags=["devil", "ruler"]),
    dict(id="npc_moraqel", name="Moraqel Inscriptus", race="Devil", age="",
         occupation="Scribe of Chains", title="Vasen Käsi",
         faction="Infernal Disc", alignment="Lawful Evil", loc="",
         stat="monster:Horned Devil", wealth="wealthy",
         appearance="Kahleisiin kietoutunut kirjuri-paholainen.",
         personality="Pedantti, kostonhaluinen.",
         notes="Hallitsee Chainledgeria ja Lucienin sopimusarkistojen "
               "sivuhaaraa; asuu Chainledger-tornissa.",
         tags=["devil"]),
    dict(id="npc_sereth", name="Sereth Nyx", race="Devil", age="",
         occupation="Whisper Censor", title="Lady",
         faction="Infernal Disc", alignment="Lawful Evil", loc="",
         stat="monster:Succubus", wealth="wealthy",
         appearance="Sumun verhoama viettelijätär.",
         personality="Salaileva, manipuloiva.",
         notes="Vakoilun ja muistojen editoinnin mestari; asuu Veilmiren "
               "sumussa.",
         tags=["devil", "spy"]),

    # ===== CELESTE (High Heavens) =====
    dict(id="npc_seraphel", name="Seraphel", race="Angel", age="",
         occupation="High Archivist", title="", faction="Celeste",
         alignment="Lawful Good", loc="", stat="monster:Deva", wealth="",
         appearance="Kirkas arkistonhoitaja-enkeli.",
         personality="Tyyni, viisas.",
         notes="Hallinnoi muistojen ja elämien elävää kirjastoa "
               "(Arx Mnemosyne).",
         tags=["celestial"]),
    dict(id="npc_manifex", name="Manifex (Index of Hands)",
         race="Angel-konstrukti", age="", occupation="Elävä hakemisto",
         title="", faction="Celeste", alignment="Lawful Neutral", loc="",
         stat="monster:Shield Guardian", wealth="",
         appearance="Monikätinen enkeli-konstrukti.",
         personality="Mekaaninen, järjestelmällinen.",
         notes="Elävä hakemisto; taikoo lukemattomia Mage Hand -efektejä "
               "kirjojen siirtelyyn. Stat-proxy: Shield Guardian.",
         tags=["celestial", "construct"]),

    # ===== FORT WHITESTONE & CALDIUS =====
    dict(id="npc_richard_walker", name="Richard Walker", race="Human", age="",
         occupation="Linnoituksen herra", title="Fort Whitestonen herra",
         faction="Vapaan Etelän Koalitio", alignment="Neutral Good",
         loc="loc_fort_whitestone", stat="monster:Noble", wealth="wealthy",
         appearance="Karaistunut tutkimusmatkailija-aatelinen.",
         personality="Päättäväinen, suojeleva.",
         notes="Blitz Walkerin isä; hallitsee Fort Whitestonea ja sen "
               "mekaanista armeijaa.",
         tags=["ally", "ruler"]),
    dict(id="npc_archibald", name="Archibald", race="Konstrukti", age="300+",
         occupation="Hovimestari", title="Linnakkeen ylläpitäjä",
         faction="Fort Whitestone", alignment="Lawful Neutral",
         loc="loc_fort_whitestone", stat="monster:Shield Guardian", wealth="",
         appearance="Hieno, yli 300-vuotias mekaaninen hovimestari.",
         personality="Kohtelias, ehdottoman kuuliainen Walker-verilinjalle.",
         notes="Fort Whitestonen mekaaninen ylläpitäjä. Blitzin kuoltua "
               "tulkitsi protokollia vapaammin auttaakseen Venristä; nyt "
               "Blitzin eläessä tottelee vain tätä. Ilmoittaa Veru-palojen "
               "resonanssista ja Kruskiin lukitusta tappokäskystä "
               "(Protokolla Omega). Stat-proxy: Shield Guardian.",
         tags=["construct"]),
    dict(id="npc_nundai", name="Nundai Galanodel", race="Elf", age="",
         occupation="Ylipapitar", title="Mara Vael Esta (Elämän Vendil)",
         faction="Nimfritein papisto", alignment="Neutral Good",
         loc="loc_fort_whitestone", stat="monster:Archmage", wealth="modest",
         appearance="Kirkastunut haltiaylipapitar, vapautunut hulluudestaan.",
         personality="Vihdoin ehjä; puhtaan toivon ja jumalallisen magian "
                     "voima.",
         notes="Venriksen äiti ja Elämän Vendilin (Nimfritein) korkein "
               "ylipapitar. Todisti mahtinsa palauttamalla Blitzin sielun "
               "ja ruumiin yhteen (herätti kuolleista). Stat-proxy: "
               "Archmage (jumalallinen loitsija).",
         tags=["clergy", "ally"]),
    dict(id="npc_duemor", name="Duemor Melkan", race="Dwarf", age="",
         occupation="Pormestari / insinööri", title="Caldiuksen pormestari",
         faction="", alignment="Neutral", loc="loc_caldius",
         stat="monster:Noble", wealth="comfortable",
         appearance="Nokinen kääpiöinsinööri.",
         personality="Kekseliäs, eristäytyvä.",
         notes="Johtaa vedenalaista Caldiusta; ryöstää laivoja kaasuttamalla "
               "ne nukuksiin.",
         tags=["ruler"]),

    # ===== THE VEIL =====
    dict(id="npc_ilyana", name="Ilyana \"Redact\" Silaqui", race="High Elf",
         age="", occupation="Sensuroija", title="", faction="The Veil",
         alignment="Lawful Neutral", loc="", stat="monster:Assassin",
         wealth="comfortable",
         appearance="Tarkka, huomaamaton korkeahaltia.",
         personality="Kylmä, tehtäväkeskeinen.",
         notes="Huippusalamurhaaja, joka \"korjaa historiaa\" pinnalta; "
               "estää totuuden leviämisen.",
         tags=["assassin", "secret"]),
    dict(id="npc_seraphina", name="Seraphina", race="Half-Elf", age="",
         occupation="Tutkija", title="", faction="The Veil",
         alignment="Neutral Good", loc="", stat="monster:Archmage",
         wealth="modest",
         appearance="Salaisuuksia kantava tutkija.",
         personality="Utelias, varovainen.",
         notes="The Veilin tutkija ja Beatricen äiti.",
         tags=["scholar", "secret"]),

    # ===== PELAAJAHAHMOT (PC:t) =====
    dict(id="npc_krusk", name="Krusk Akarsho", race="Half-Orc", age="",
         occupation="Barbaari", title="Vastentahtoinen keisari",
         faction="Vapaan Etelän Koalitio", alignment="Chaotic Good",
         loc="loc_aesica", stat="", wealth="modest",
         appearance="Atleettinen puoliörkki, selässä valtava pyöreä \"Pedon "
                     "merkki\" (Veru).",
         personality="\"Orjasta johtajaksi\" — sitkeä, suojeleva; tällä "
                     "hetkellä uupunut ja ahdistunut katujen verisistä "
                     "puhdistuksista.",
         notes="PELAAJAHAHMO. Aesican kapinan symboli — kansa huutaa häntä "
               "keisariksi, mutta hän kieltäytyi tittelistä ja toimii "
               "koalition moraalisena ankkurina ja armeijan kasvoina. "
               "Kantaa 3/5 Veru-ihon palasista → keisari Tarquvas Redfein "
               "(henkiolento Oknar) perillinen. Efauxerin pojanpoika; "
               "Emnarin ja Aequitaksen jahtaama. Henkivartijoina entinen "
               "areenaryhmä Broken Spear.",
         tags=["player_character", "party", "ruler"]),
    dict(id="npc_beatrice", name="Beatrice", race="Half-Elf / Drow",
         age="", occupation="Warlock / Sorcerer", title="",
         faction="", alignment="Neutral", loc="loc_veksla",
         stat="", wealth="modest",
         appearance="Punaiset hiukset hopearaidoin, violetit drow-silmät.",
         personality="Ryhmän taikatykistö ja diplomaatti; kostonhimon ja "
                     "armon välissä.",
         notes="PELAAJAHAHMO. Seraphinan ja Altheon Baenrahelin tytär; "
               "drowien laissa Dobluth Dro (kuolemantuomio). Patronina "
               "Lucien the Ledgerkeeper.",
         tags=["player_character", "party"]),
    dict(id="npc_venris", name="Venris Galanodel", race="Elf", age="",
         occupation="Velho", title="", faction="Seekers of Demimaind",
         alignment="Neutral Good", loc="loc_fort_whitestone", stat="",
         wealth="modest",
         appearance="Vaalea haltia; tutkiva, analyyttinen.",
         personality="Tarkkailija, ajan säröjen näkijä.",
         notes="PELAAJAHAHMO. Äiti ylipapitar Nundai on vapautunut "
               "hulluudestaan ja herätti Blitzin kuolleista. Kantaa "
               "Hatred of Time -kirjaa (ajan manipulointi). Blitzin "
               "peilikuva: aika/kosminen magia vs. ulottuvuusteknologia — "
               "yhdessä he voisivat purkaa Cunaen taikarajan (Leutik & "
               "Adultus). Dihvikin oppilas; E.F.I.:n ja Veljeskunnan "
               "jahtaama.",
         tags=["player_character", "party"]),
    dict(id="npc_balthazar", name="Balthazar / Zarxetharion", race="Devil",
         age="", occupation="Warlock / \"lakimies\"", title="",
         faction="Infernal Disc", alignment="Lawful Neutral", loc="",
         stat="monster:Horned Devil", wealth="comfortable",
         appearance="Hienostuneesti pukeutunut \"lakimies\"; imp-apuri "
                     "Barbatos.",
         personality="Byrokraatti ja porsaanreikien mestari.",
         notes="PELAAJAHAHMO. Todellisuudessa Zarxetharion, entinen Infernal "
               "Discin herttua, joka putosi Cunaeen. Suojelee ryhmää Codex "
               "Aterterran porsaanrei'illä. Stat-proxy: Horned Devil.",
         tags=["player_character", "party"]),
    dict(id="npc_magnus", name="Magnus", race="Air Genasi", age="",
         occupation="Lohikäärmeenhoitaja", title="", faction="",
         alignment="Chaotic Good", loc="loc_antanard", stat="", wealth="modest",
         appearance="Sinertäväihoinen, rento.",
         personality="Vapaa sielu; vanhojen lakien sokea piste.",
         notes="PELAAJAHAHMO. Kasvoi Antanardin hautomossa; yhteys "
               "prismaattiseen lohikäärme Aurelithiin. Viholliset: Smardun "
               "konservatiivit (F.E.R.I.D.) ja Veljeskunta.",
         tags=["player_character", "party"]),
    dict(id="npc_darius", name="Thomas / Darius Morin", race="Human", age="",
         occupation="Rogue / artefaktinmetsästäjä", title="",
         faction="", alignment="Chaotic Neutral", loc="", stat="",
         wealth="modest",
         appearance="Keskikokoinen, smaragdinvihreät silmät; "
                     "kaksoisidentiteetti.",
         personality="Varovainen, selviytyjä.",
         notes="PELAAJAHAHMO. Varasti T.R.A.:lta Heart Acceleratorin, joka "
               "sykkii hänen rinnassaan. Rahgo \"Karhun\" ja Varjo Kaartin "
               "jahtaama; sopimus Lucienin kanssa. On jo matkalla pois "
               "Vekslasta tiefling-kapteeninsa kanssa (vältti Zetriksen "
               "väijytyksen).",
         tags=["player_character", "party"]),
    dict(id="npc_padak", name="Padak", race="Tabaxi", age="",
         occupation="Taistelija", title="", faction="",
         alignment="Neutral", loc="loc_veksla", stat="", wealth="modest",
         appearance="Arpinen tabaxi, sormia puuttuu, suonissa violetti "
                     "korruptio (Verdant Shard Fever).",
         personality="\"Perhe on kaikki\" — sitkeä, vaarallinen.",
         notes="PELAAJAHAHMO. Entinen Red Dagger -palkkasoturi; murhasi "
               "Emnar Redfein pojan. Vaimo Demanda ja poika Rafal vankina "
               "Kharakissa; pään hinta 150 000 gp. Matkusti Sam Undercaven "
               "kanssa (Ravenstonen kautta) etsimään parannusta "
               "sairauteensa; nyt Vekslassa.",
         tags=["player_character", "party"]),
    dict(id="npc_kairon", name="Kairon / Rin", race="Changeling", age="",
         occupation="Bardi / vakooja", title="", faction="Ember & Veil Company",
         alignment="Chaotic Neutral", loc="", stat="monster:Doppelganger",
         wealth="modest",
         appearance="Esiintyy usein tiefling-bardina; muodonmuuttaja.",
         personality="Identiteettikriisi: tähti vai näkymätön varjo?",
         notes="PELAAJAHAHMO. Syntyi Goldfist-kääpiöperheeseen; liittyi "
               "Ember & Veil -teatteriin; nyt Efauxerin palveluksessa "
               "vakoojana. Stat-proxy: Doppelganger.",
         tags=["player_character", "party"]),
    dict(id="npc_ulv", name="Ulv", race="Firbolg", age="",
         occupation="Druidi", title="", faction="",
         alignment="Neutral Good", loc="loc_veksla", stat="", wealth="modest",
         appearance="3-metrinen, sarvekas; sammalviitta.",
         personality="Luonnon suojelija; pelkää metsän korruptiota.",
         notes="PELAAJAHAHMO. \"Kolmen veren\" ruumiillistuma: Archfey "
               "Eksothethin ja druidi Bram Boulderrootin poika; Aghuantin "
               "siunaama. Yrittää pelastaa velipuolensa Caeltherionin. "
               "Vekslassa keskellä isänsä (Bram Boulderroot / Metsän "
               "Suojelijat) historiaa; fey-olennot tunnistavat hänet.",
         tags=["player_character", "party"]),
    dict(id="npc_marduk", name="Marduk", race="Human", age="",
         occupation="Paladin / Cleric / Fighter",
         title="Praefectus Purificatorum", faction="Death's Vigil",
         alignment="Lawful Neutral", loc="", stat="", wealth="modest",
         appearance="Kalju, arpikuvioitu; peittää tunteensa.",
         personality="Kurinalainen, salaileva.",
         notes="PELAAJAHAHMO. Karkotettiin Kaernathista nuorena; menetti "
               "Strange Owl -ryhmänsä ja ystävänsä Brynnin (Revenant). "
               "\"Kävelevä sieluvankila\": titaani Pappa ja orjuuttaja "
               "Erokme Belmudar. Vaimo/mentori Mirabel piilossa elossa; "
               "Gaius Marad manipuloi häntä.",
         tags=["player_character", "party"]),
    dict(id="npc_morgan", name="Morgan", race="Goblin", age="",
         occupation="Bardi / Hexblade", title="", faction="",
         alignment="Neutral Evil", loc="", stat="monster:Wight",
         wealth="poor",
         appearance="Entinen Dikrak Dikoz -muusikko, käytti Alter Self "
                     "-maskia näyttääkseen puolituiselta.",
         personality="Sieluton, pimeän voiman ohjaama.",
         notes="PELAAJAHAHMO (kuollut/epäkuollut). Teki sopimuksen Oberionin "
               "kanssa kostonsa tähden; kantaa Clavis-miekkaa (avain titaanin "
               "lukkoihin). Stat-proxy: Wight.",
         tags=["player_character", "party", "undead"]),
    dict(id="npc_blitz", name="Blitz Walker", race="Human", age="",
         occupation="Gunslinger", title="Walker-suvun perillinen",
         faction="Vapaan Etelän Koalitio",
         alignment="Neutral Good", loc="loc_fort_whitestone", stat="",
         wealth="wealthy",
         appearance="Tutkimusmatkailija-asuinen ampuja.",
         personality="Periksiantamaton tutkija; nyt valtavan moraalisen "
                     "dilemman edessä.",
         notes="PELAAJAHAHMO. Nundai herätti hänet juuri kuolleista. Suvun "
               "ainoa aktiivinen perillinen — hänen verensä ja "
               "Walker-sinettisormus avaavat Fort Whitestonen täyden "
               "potentiaalin (Protokolla Omega -armeija). Dilemma: koalitio "
               "tarvitsee armeijaa Oblitusta vastaan, mutta se on ohjelmoitu "
               "tappamaan Veru-kantaja Krusk. Walkerin suku (esim. esi-isä "
               "Vermok) rakensi armeijan kosmisen karanteenin ylläpitoon. "
               "Gersnet tappoi hänet aiemmin.",
         tags=["player_character", "party", "ruler"]),
    dict(id="npc_carlo", name="Carlo \"Flexmaster\"", race="Human", age="",
         occupation="Barbaari / perämies", title="", faction="",
         alignment="Chaotic Good", loc="loc_fort_whitestone", stat="",
         wealth="poor",
         appearance="Lihaksikas, kookospähkinöitä rakastava ihmissoturi.",
         personality="Maanläheinen, rento, kaoottinen energia.",
         notes="\"Rapulaivan\" (kapteeni Rommiparran alus) perämies. Tuo "
               "kaivattua rentoa energiaa vakavaan tilanteeseen. "
               "Stat: Barbaari (DM valitsee blockin).",
         tags=["ally"]),
    dict(id="npc_rommiparta", name="Kapteeni Rommiparta", race="Dwarf",
         age="", occupation="Merikapteeni", title="\"Rapulaivan\" kapteeni",
         faction="", alignment="Chaotic Neutral", loc="loc_fort_whitestone",
         stat="monster:Thug", wealth="modest",
         appearance="Juopotteleva kääpiökapteeni.",
         personality="Välinpitämätön, huoleton, luotettava hädässä.",
         notes="Löytyy todennäköisesti linnakkeen piha-alueelta "
               "juopottelemasta välittämättä kosmisen tason draamasta.",
         tags=["ally"]),
    dict(id="npc_gediroi", name="Gediroi", race="Human", age="",
         occupation="Liittolainen", title="", faction="",
         alignment="Neutral Good", loc="loc_fort_whitestone",
         stat="monster:Scout", wealth="modest",
         appearance="Karaistunut, hiljainen sivustakatsoja.",
         personality="Lojaali, sitkeä.",
         notes="Selvisi laivamatkan syvyyden olentojen kohtaamisesta; nyt "
               "ryhmän mukana linnakkeessa. Tuo jatkuvuutta aiemmista "
               "seikkailuista.",
         tags=["ally"]),
]


# --------------------------------------------------------------------- #
# NPC↔NPC -suhteet — (src_id, target_id, kind, notes)
# kind ∈ family|mentor|protege|ally|rival|enemy|patron|subordinate|lover|other
# --------------------------------------------------------------------- #
NPC_LINKS: List[tuple] = [
    # Redfei-suku & Vapaa Etelä
    ("npc_efauxer", "npc_krusk", "family", "Kruskin isoisä."),
    ("npc_krusk", "npc_efauxer", "family", "Isoisä ja liittolainen."),
    ("npc_emnar", "npc_efauxer", "enemy", "Vihollisia; eri linjat."),
    ("npc_emnar", "npc_krusk", "enemy", "Jahtaa Kruskia Veru-palojen takia."),
    ("npc_efauxer", "npc_antos_orac", "ally", "Vapaan Etelän Koalitio."),
    ("npc_antos_orac", "npc_krusk", "ally", "Johtavat vallattua Aesicaa."),
    ("npc_efauxer", "npc_kairon", "subordinate", "Kairon on Efauxerin vakooja."),
    # Dath
    ("npc_giurun", "npc_emnar", "ally", "Molemmat Dathin sisäpiiriä."),
    ("npc_giurun", "npc_lysandra", "subordinate",
     "Ohjaa Lysandraa telepatialla kulissien takaa."),
    ("npc_giurun", "npc_dihvik", "enemy", "Soluttautunut Seekersiin; vihollinen."),
    # Seekers / mentorit
    ("npc_dihvik", "npc_venris", "protege", "Venriksen mentori."),
    ("npc_venris", "npc_dihvik", "mentor", "Syvä kunnioitus mentoria kohtaan."),
    ("npc_agustion", "npc_dihvik", "ally", "Etsii epätoivoisesti ystäväänsä."),
    ("npc_aedria", "npc_magnus", "protege", "Magnuksen mentori Antanardissa."),
    ("npc_magnus", "npc_aedria", "mentor", "Mentori hautomon syvyyksissä."),
    # Beatrice / drow
    ("npc_altheon", "npc_beatrice", "family",
     "Biologinen isä; hylkäsi tyttärensä (Geas-kirous)."),
    ("npc_beatrice", "npc_altheon", "enemy", "Hylkäävä isä — kostonkohde."),
    ("npc_seraphina", "npc_beatrice", "family", "Äiti (The Veil)."),
    ("npc_altheon", "npc_seraphina", "lover",
     "Rakastui projekti 'Kaiun' aikana; Beatricen vanhemmat."),
    ("npc_seraphina", "npc_altheon", "lover", "Beatricen isä Aterterrassa."),
    ("npc_cazna", "npc_altheon", "subordinate",
     "Altheon on matriarkan oikea käsi ja arkistojen johtaja."),
    # Talo Baenrahel — sisarukset & palvelijoiden talo
    ("npc_altheon", "npc_elarae", "family", "Virallinen perijä."),
    ("npc_altheon", "npc_dravin", "family", "Poika, Velve Dro -upseeri."),
    ("npc_elarae", "npc_altheon", "rival",
     "Perijä joka etsii vipuvartta isänsä salaisuutta vastaan."),
    ("npc_elarae", "npc_beatrice", "family", "Beatricen siskopuoli."),
    ("npc_dravin", "npc_beatrice", "family", "Beatricen velipuoli."),
    ("npc_elarae", "npc_dravin", "family", "Sisarukset — perijä ja nyrkki."),
    ("npc_vorn", "npc_nymia", "family", "Isä ja tytär (Xorlath)."),
    ("npc_thala", "npc_kael_myrdin", "family", "Myrdin-suku; suojelee poikaa."),
    ("npc_vorn", "npc_altheon", "subordinate", "Palvelee Talo Baenrahelia."),
    ("npc_thala", "npc_altheon", "subordinate", "Talon pääemäntä."),
    ("npc_zirkass", "npc_altheon", "subordinate", "Talon tallimestari."),
    ("npc_kairon", "npc_kael_myrdin", "other",
     "Kairon voi puhua nuoren keittiöpojan puolelleen."),
    ("npc_faldor", "npc_beatrice", "other",
     "Salainen hengenheimolainen (Dobluth Dro) — voi auttaa."),
    # Aesica — kapinan jälkeen
    ("npc_adrik", "npc_krusk", "mentor", "Isällinen gladiaattorivalmentaja."),
    ("npc_krusk", "npc_adrik", "protege", "Kruskin isähahmo areenalta."),
    ("npc_erokme", "npc_krusk", "enemy", "Syrjäytetty hirmuvaltias vs. kapina."),
    ("npc_lyra", "npc_krusk", "ally", "Jäi Kruskin tueksi Aesicaan."),
    ("npc_xionzer", "npc_krusk", "ally", "Jäi Aesicaan; varoitti Unhaelista."),
    ("npc_xionzer", "npc_fangrok", "ally", "Ratsastaja ja valkoinen lohikäärme."),
    ("npc_dimerius", "npc_lyra", "enemy",
     "Manipuloi Lyraa painajaisissa Clavis-miekan kautta."),
    ("npc_gaufex", "npc_khaldrys", "ally", "Ratsastaja ja messinkilohikäärme."),
    ("npc_brynja", "npc_silverscale", "ally", "Ratsastaja ja hopealohikäärme."),
    ("npc_gaufex", "npc_saxignis", "ally", "Salaa pelastamassa kuningastaan."),
    ("npc_krusk", "npc_gaufex", "rival", "Epäilee Unhaelin todellisia aikeita."),
    ("npc_julus", "npc_erokme", "subordinate", "Areena entisen kreivin alla."),
    # Ravenstone — vampyyrien sisällissota & alamaailma
    ("npc_dimerius", "npc_jugorai", "subordinate",
     "Jugorai on täysin Dimeriuksen hallinnassa."),
    ("npc_jugorai", "npc_dimerius", "enemy",
     "Yrittää varastaa Dimeriuksen voiman."),
    ("npc_polsen", "npc_dimerius", "subordinate", "Suojelee Dimeriusta."),
    ("npc_vilan", "npc_dimerius", "subordinate", "Uskollinen palvelija (350+)."),
    ("npc_herold", "npc_dimerius", "subordinate", "Vanhin palvelija (800+)."),
    ("npc_jugorai", "npc_isabel", "family", "Tytär, muutettu vampyyriksi."),
    ("npc_aksel", "npc_isabel", "enemy", "Surmasi Isabelin (tämän pyynnöstä)."),
    ("npc_jugorai", "npc_aksel", "enemy", "3700 kullan tapporaha."),
    ("npc_aksel", "npc_davos", "family", "Veli — Jugorain vampyyriorja."),
    ("npc_jugorai", "npc_davos", "subordinate", "Vampyyriorja (vipuvarsi)."),
    ("npc_jugorai", "npc_fior", "subordinate", "Luotu uhrattavaksi."),
    ("npc_jugorai", "npc_zemok", "subordinate", "Luotu uhrattavaksi."),
    ("npc_gaur", "npc_jivin", "subordinate", "Cora 0:n vakooja."),
    ("npc_gaur", "npc_jugorai", "enemy", "Haluaa syrjäyttää paronin."),
    ("npc_gaur", "npc_amalica", "ally", "Salainen savi-sopimus Talo Despanan kanssa."),
    ("npc_greg", "npc_dimerius", "subordinate", "Valuttaa vankien verta Dimeriukselle."),
    ("npc_greg", "npc_blitz", "enemy", "Vastuussa Walkerin suvun kohtaloista."),
    ("npc_edmun", "npc_avarath", "subordinate", "Abolethin aivopesty pappi."),
    ("npc_hannes", "npc_avarath", "subordinate", "Abolethin aivopesty pappi."),
    ("npc_edmun", "npc_hannes", "ally", "Avarath-kultin perustajat."),
    ("npc_padak", "npc_sam_undercave", "ally", "Matkatoveri Ravenstonessa."),
    ("npc_sam_undercave", "npc_padak", "ally", "Matkatoveri Ravenstonessa."),
    # Fort Whitestone / Maclebar Isle
    ("npc_nundai", "npc_venris", "family", "Äiti ja poika."),
    ("npc_venris", "npc_nundai", "family", "Äiti, vapautunut hulluudestaan."),
    ("npc_nundai", "npc_blitz", "other", "Herätti Blitzin kuolleista."),
    ("npc_richard_walker", "npc_blitz", "family", "Isä ja poika (perillinen)."),
    ("npc_archibald", "npc_blitz", "subordinate",
     "Tottelee ehdottomasti Walker-verilinjaa."),
    ("npc_blitz", "npc_krusk", "ally",
     "Ystävä — mutta Protokolla Omega uhkaa tappaa Kruskin."),
    ("npc_venris", "npc_blitz", "ally", "Peilikuvat: aika vs. teknologia."),
    ("npc_carlo", "npc_rommiparta", "ally", "\"Rapulaivan\" miehistö."),
    ("npc_rommiparta", "npc_carlo", "ally", "Perämies."),
    ("npc_gediroi", "npc_blitz", "ally", "Lojaali tukija linnakkeessa."),
    # Old Vaisil
    ("npc_efauxer", "npc_delma", "subordinate", "Luotettu vakooja."),
    ("npc_efauxer", "npc_dumblo", "ally", "Pitkäaikainen ystävä & komentaja."),
    ("npc_efauxer", "npc_beon", "subordinate", "Huumeongelman selvittäjä."),
    ("npc_efauxer", "npc_richard_walker", "ally", "Suojelee Walker-sukua."),
    ("npc_richard_walker", "npc_rose_walker", "family", "Puoliso."),
    ("npc_rose_walker", "npc_blitz", "family", "Äiti."),
    ("npc_volden", "npc_giluan", "enemy", "Murhasi Giluanin (pää viety)."),
    ("npc_emnar", "npc_volden", "subordinate", "Palkkasi Voldenin (45k)."),
    ("npc_orien", "npc_gersnet", "ally", "Grand Gardenin salamurhajuoni."),
    ("npc_adelf", "npc_thalorian", "ally", "Ratsastaja ja hopealohikäärme."),
    ("npc_adelf", "npc_elara_silverleaf", "subordinate", "Apulainen."),
    ("npc_adelf", "npc_tormek", "subordinate", "Apulainen & suojelija."),
    ("npc_undur", "npc_dumblo", "subordinate", "Rekrytoi komentajalle."),
    # Zer'tath Lanke — hovi & kadut
    ("npc_pharaun", "npc_dantrag", "family", "Veli."),
    ("npc_pharaun", "npc_cazna", "subordinate", "Matriarkan salainen ilmiantaja."),
    ("npc_zhindia", "npc_cazna", "ally", "Mielenlukijoiden johtaja hovissa."),
    ("npc_valas_szithryn", "npc_nhilymra", "ally", "Szith'ryn/Zaer'vyn -kytkös."),
    ("npc_szoraya", "npc_altheon", "family", "Altheonin sisar (totuudenetsijä)."),
    ("npc_szoraya", "npc_elarae", "family", "Täti/sisarentytär."),
    ("npc_naerthali", "npc_cazna", "subordinate", "Reverie-kultin pääpapitar."),
    ("npc_thol", "npc_krusk", "ally", "Mahdollinen liittolainen (orjasta orjalle)."),
    # Veksla
    ("npc_kaldir", "npc_gaius_marad", "family", "Poika, joka lähti Vigilistä."),
    ("npc_gaius_marad", "npc_kaldir", "family", "Poika, jätti Death's Vigilin."),
    ("npc_kaldir", "npc_ailas", "ally", "Pysäyttivät yhdessä Fausterin."),
    ("npc_fauster", "npc_elisa_ghost", "family", "Sisko, kuoli rituaalissa."),
    ("npc_timotei", "npc_elisa_ghost", "family", "Vaimo (Fausterin sisko)."),
    ("npc_idefian", "npc_ulv", "other", "Metsän Suojelijat tuntevat Ulvin isän."),
    ("npc_gurug", "npc_tomas_farm", "enemy", "Tomas varasti Gurugin miekan."),
    ("npc_mavielf", "npc_artur_potvark", "enemy", "Kiristää paronia ruoasta."),
    ("npc_jay_upto", "npc_idefian", "subordinate", "Dryadien 'lihasvoima'."),
    ("npc_zetris", "npc_darius", "enemy", "Väijytti ja yritti pidättää Thomaksen."),
    # Talo Icharyd — Caznan varjoperhe
    ("npc_xalyra", "npc_cazna", "family", "Äiti; 'Kuiskaaja verhon takana'."),
    ("npc_cazna", "npc_xalyra", "family", "Ohjaava äiti varjoissa."),
    ("npc_cazna", "npc_vhaerani", "family", "Salainen tytär ja perillinen."),
    ("npc_vhaerani", "npc_cazna", "family", "Äidin perimmäinen ase."),
    # Lucienin sielusopimukset
    ("npc_lucien", "npc_beatrice", "patron", "Patroni; sielusopimus."),
    ("npc_lucien", "npc_darius", "patron", "Epätoivoinen diili."),
    ("npc_lucien", "npc_morgan", "patron", "Kuolemansopimus."),
    ("npc_lucien", "npc_julus", "other", "Sopimus areenan sieluista."),
    # Famiglia vs. Darius
    ("npc_rahgo", "npc_darius", "enemy", "Haluaa Heart Acceleratorin takaisin."),
    ("npc_zaira", "npc_darius", "enemy", "Famiglian vaarallinen vihollinen."),
    ("npc_zaira", "npc_rahgo", "subordinate", "Famiglian Consigliere."),
    ("npc_nilf", "npc_darius", "enemy", "E.F.I. jahtaa Dariusta."),
    # Death's Vigil
    ("npc_gaius_marad", "npc_marduk", "patron", "Esimies; manipuloi Mardukia."),
    ("npc_marduk", "npc_gaius_marad", "subordinate", "Vigilin alainen."),
    # Golden Gear ↔ Emnar
    ("npc_heinrich", "npc_emnar", "ally", "Rahoittaa Emnaria vallasta."),
    # Aesica sielukone
    ("npc_julus", "npc_gorkha", "ally", "Areenan sielukoneen sisäpiiri."),
    # PC-ryhmän sisäiset suhteet
    ("npc_krusk", "npc_padak", "ally", "Jakavat \"perhe on kaikki\" -mielen."),
    ("npc_padak", "npc_krusk", "ally", "Hengenheimolainen."),
    ("npc_krusk", "npc_beatrice", "ally", "Ymmärtävät toistensa tuskan."),
    ("npc_beatrice", "npc_balthazar", "ally", "Lucienin pelinappuloita; lakimies."),
    ("npc_magnus", "npc_balthazar", "rival", "\"Vapaus vs. laki\"."),
    ("npc_balthazar", "npc_magnus", "rival", "\"Lakitekninen anomalia\"."),
    ("npc_padak", "npc_darius", "rival", "Epäluuloinen suhde."),
    ("npc_ulv", "npc_padak", "ally", "Kantavat kumpikin kirousta."),
    ("npc_kairon", "npc_ulv", "ally", "Kunnioittaa Ulvin rehellisyyttä."),
    ("npc_venris", "npc_blitz", "ally", "Tutkijakollega."),
    ("npc_kairon", "npc_balthazar", "ally", "Täydentää lakimiestaktiikkaa."),
    # Blitz
    ("npc_richard_walker", "npc_blitz", "family", "Blitzin isä."),
    ("npc_gersnet", "npc_blitz", "enemy", "Tappoi Blitzin."),
    ("npc_gersnet", "npc_efauxer", "enemy", "Salamurhayritykset Efauxeria vastaan."),
]


# --------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------- #
def build_lore_locations(world) -> None:
    """Add every canon city/independent location to ``world.locations``
    and wire it under the right country location (Underdark cities under
    Aterterra). Idempotent — skips ids that already exist."""
    from data.world import Location
    for c in CITIES:
        if c["loc_id"] in world.locations:
            continue
        # Explicit "parent" wins (nests independent locations, e.g. Fort
        # Whitestone under Maclebar Isle); otherwise fall back to the
        # kingdom country-location.
        parent = c.get("parent") or (
            KINGDOM_LOC.get(c["kingdom"], "") if c["kingdom"] else "")
        tags = [c["key"]]
        if c["kingdom"]:
            tags.append(c["kingdom"])
        if c.get("biome"):
            tags.append(c["biome"])
        loc = Location(
            id=c["loc_id"], name=c["name"], location_type=c["type"],
            description=c["description"], parent_id=parent,
            population=c.get("population", 0),
            religion=c.get("religion", ""),
            known_for=c.get("industry", ""),
            tags=tags,
        )
        world.locations[loc.id] = loc
        if parent and parent in world.locations:
            if loc.id not in world.locations[parent].children_ids:
                world.locations[parent].children_ids.append(loc.id)

    # Buildings/rooms inside cities (built after the cities they hang off).
    for s in SUBLOCATIONS:
        if s["loc_id"] in world.locations:
            continue
        parent = s.get("parent", "")
        tags = [s["key"]]
        if s.get("biome"):
            tags.append(s["biome"])
        loc = Location(
            id=s["loc_id"], name=s["name"],
            location_type=s.get("type", "building"),
            description=s["description"], parent_id=parent, tags=tags,
        )
        world.locations[loc.id] = loc
        if parent and parent in world.locations:
            if loc.id not in world.locations[parent].children_ids:
                world.locations[parent].children_ids.append(loc.id)


def build_lore_npcs(world) -> None:
    """Add every canon NPC to ``world.npcs``, place them at their location,
    seed wealth, and wire stat links. Idempotent by id."""
    from data.world import NPC
    from data.wealth import set_npc_coins, suggest_coins_for_wealth_tier
    for spec in NPCS:
        nid = spec["id"]
        if nid in world.npcs:
            continue
        loc_id = spec.get("loc", "") or ""
        npc = NPC(
            id=nid, name=spec["name"], race=spec.get("race", ""),
            age=spec.get("age", ""), appearance=spec.get("appearance", ""),
            personality=spec.get("personality", ""),
            occupation=spec.get("occupation", ""),
            title=spec.get("title", ""), faction=spec.get("faction", ""),
            alignment=spec.get("alignment", ""), notes=spec.get("notes", ""),
            location_id=loc_id, stat_source=spec.get("stat", ""),
            tags=list(spec.get("tags", [])),
            alive=spec.get("alive", True), active=spec.get("active", True),
        )
        tier = spec.get("wealth", "")
        if tier:
            set_npc_coins(npc, suggest_coins_for_wealth_tier(tier))
        world.npcs[nid] = npc
        if loc_id and loc_id in world.locations:
            if nid not in world.locations[loc_id].npc_ids:
                world.locations[loc_id].npc_ids.append(nid)


def wire_lore_relationships(world) -> None:
    """Apply NPC↔NPC links (Phase 39 ``npc_links``). Only adds a link if
    both endpoints exist and it isn't already present."""
    for src, tgt, kind, note in NPC_LINKS:
        npc = world.npcs.get(src)
        if npc is None or tgt not in world.npcs:
            continue
        if any(l.get("target_id") == tgt and l.get("kind") == kind
               for l in npc.npc_links):
            continue
        npc.npc_links.append({"target_id": tgt, "kind": kind, "notes": note})


def add_lore_cities_to_kingdoms(camp) -> None:
    """Register every canon surface/Underdark city as a CityEntry on its
    kingdom and cross-link the World location id. Idempotent by key."""
    from data import kingdoms as kg
    for c in CITIES:
        if not c["kingdom"]:
            continue
        existing = kg.find_city(camp, c["kingdom"], c["key"])
        if existing is not None:
            if not existing.location_id:
                existing.location_id = c["loc_id"]
            continue
        kg.add_city(
            camp, c["kingdom"], c["key"], c["name"],
            is_capital=c.get("is_capital", False),
            location_id=c["loc_id"],
            description=c["description"][:240],
            population=c.get("population", 0),
            biome=c.get("biome", ""),
            primary_industry=c.get("industry", ""),
            religion=c.get("religion", ""),
            ruler_npc_id=c.get("ruler", ""),
            demographics=c.get("demographics", {}),
        )


def augment_campaign(camp, world) -> None:
    """One-stop entry: build all canon locations + NPCs + relationships on
    ``world`` and register the cities on the campaign's kingdoms. The
    caller is responsible for (re)serialising ``world`` into
    ``camp.world_data`` afterwards. Organisations are added separately via
    :func:`lore_organisations`."""
    build_lore_locations(world)
    build_lore_npcs(world)
    wire_lore_relationships(world)
    add_lore_cities_to_kingdoms(camp)


def refresh_lore(camp, world) -> int:
    """Additively merge any NEW canon lore into an already-existing
    campaign/world (e.g. cities added to CITIES after the save was
    created). Purely additive: the location/NPC builders skip ids that
    already exist, so the DM's own edits are never overwritten. Returns
    the number of canon locations newly added, so the caller can decide
    whether to re-serialise the world."""
    before = len(world.locations)
    build_lore_locations(world)
    build_lore_npcs(world)
    wire_lore_relationships(world)
    try:
        add_lore_cities_to_kingdoms(camp)
    except Exception:
        pass
    return len(world.locations) - before


# --------------------------------------------------------------------- #
# Organisations
# --------------------------------------------------------------------- #
def lore_organisations():
    """Return the list of canon organisations to add alongside the seeded
    Brotherhood. Members link to World NPC ids where one exists."""
    from data.organizations import (
        Organisation, OrganisationRank, OrganisationRole, OrganisationMember,
    )

    dath = Organisation(
        key="dath", name="Dath",
        kind="secret_society",
        description="Haltioiden ylivaltaa ajava salaseura ja kampanjan "
                    "pääantagonisti. Tavoite: ladata sieluenergiaa Zlalensin "
                    "huippukristalliin, herättää maailmantitaani Garruth ja "
                    "vallata manner. Soluttautunut kaikkien valtakuntien "
                    "hallintoon ja Brotherhoodiin.",
        motto="Yksi veri, yksi tahto.",
        secret=True, alignment="lawful evil",
        headquarters_city="zlalens", headquarters_kingdom="fundarla",
        operating_kingdoms=["fundarla", "oblitus", "tarmaas", "smardu"],
        operating_cities=["zlalens", "iklence"],
        ranks=[
            OrganisationRank(key="hidden_hand", name="Kätketty käsi", tier=1,
                             description="Todellinen johtaja."),
            OrganisationRank(key="archon", name="Arkkimanipulaattori", tier=2,
                             description="Sisäpiirin pelinappuloiden ohjaaja."),
            OrganisationRank(key="agent", name="Agentti", tier=3,
                             description="Soluttautunut hallintoon."),
        ],
        roles=[
            OrganisationRole(key="puppeteer", name="Nukettaja",
                             description="Ohjaa kulissijärjestöjä."),
            OrganisationRole(key="soulwright", name="Sielunkerääjä",
                             description="Kerää sieluenergiaa (Veru)."),
        ],
        members=[
            OrganisationMember(npc_id="npc_giurun", npc_name="Giurun Kalfantan",
                               rank_key="hidden_hand", role_keys=["puppeteer"],
                               kingdom_key="fundarla", city_key="zlalens",
                               notes="Dathin todellinen johtaja."),
            OrganisationMember(npc_id="npc_emnar", npc_name="Emnar Redfei",
                               rank_key="archon", role_keys=["soulwright"],
                               kingdom_key="oblitus", city_key="iklence",
                               notes="Sielujen kerääjä, Oblituksen kuningas."),
            OrganisationMember(npc_id="npc_heinrich", npc_name="Heinrich Stormhold",
                               rank_key="agent", role_keys=[],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="Rahoittaja Golden Gearin kautta."),
        ],
        relations={"brotherhood_of_glorious_sun": "controls"},
        color=(150, 90, 200),
        tags=["antagonist", "secret_society", "mastermind"],
    )

    deaths_vigil = Organisation(
        key="deaths_vigil", name="Death's Vigil",
        kind="order",
        description="Parin sadan hengen itsenäinen ritarikunta, joka "
                    "suojelee kuoleman pyhyyttä ja tuhoaa epäkuolleita ja "
                    "nekromantiaa.",
        motto="Kuolema on pyhä; sitä ei myydä.",
        secret=False, alignment="lawful neutral",
        headquarters_city="pinwud", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas", "oblitus"],
        operating_cities=["pinwud"],
        ranks=[
            OrganisationRank(key="magnus_custos", name="Magnus Custos", tier=1,
                             description="Ylin vartija."),
            OrganisationRank(key="praefectus", name="Praefectus", tier=2,
                             description="Puhdistajien komentaja."),
            OrganisationRank(key="custos", name="Custos", tier=4,
                             description="Vartija-ritari."),
        ],
        roles=[
            OrganisationRole(key="purificator", name="Puhdistaja",
                             description="Tuhoaa epäkuolleita."),
        ],
        members=[
            OrganisationMember(npc_id="npc_gaius_marad", npc_name="Gaius Marad",
                               rank_key="magnus_custos", role_keys=[],
                               kingdom_key="tarmaas", city_key="pinwud",
                               notes="Järjestön johtaja."),
            OrganisationMember(npc_id="npc_marduk", npc_name="Marduk",
                               rank_key="praefectus", role_keys=["purificator"],
                               kingdom_key="tarmaas",
                               notes="Praefectus Purificatorum; pelaajahahmo."),
        ],
        relations={},
        color=(180, 180, 200),
        tags=["order", "ally"],
    )

    seekers = Organisation(
        key="seekers_of_demimaind", name="Seekers of Demimaind",
        kind="academy",
        description="\"Jumalten tiedon etsijät\" — Cunaen älykkäin "
                    "tutkijajärjestö, jota johtaa seitsemän suurmestarin "
                    "Council of Great Minds. Dath on soluttautunut tähän.",
        motto="Tieto ennen jumalia.",
        secret=False, alignment="neutral good",
        headquarters_kingdom="fundarla",
        operating_kingdoms=["fundarla", "tarmaas", "smardu"],
        operating_cities=["zlalens", "faharn"],
        ranks=[
            OrganisationRank(key="grandmaster", name="Suurmestari", tier=1,
                             description="Council of Great Minds (7)."),
            OrganisationRank(key="researcher", name="Tutkija", tier=4,
                             description="Akatemian tutkija."),
        ],
        roles=[],
        members=[
            OrganisationMember(npc_id="npc_dihvik", npc_name="Dihvik Mevraft",
                               rank_key="grandmaster", role_keys=[],
                               notes="Deatariksen rehtori; Dathin vankina."),
            OrganisationMember(npc_id="npc_nimri", npc_name="Nimri Greentop",
                               rank_key="grandmaster", role_keys=[],
                               kingdom_key="fundarla", city_key="faharn",
                               notes="Saideneria-akatemian rehtori."),
            OrganisationMember(npc_id="npc_giurun", npc_name="Giurun Kalfantan",
                               rank_key="grandmaster", role_keys=[],
                               kingdom_key="fundarla", city_key="zlalens",
                               notes="Soluttautunut Dathin agentti."),
        ],
        relations={"dath": "infiltrated_by"},
        color=(90, 160, 200),
        tags=["academy", "scholar"],
    )

    veil = Organisation(
        key="the_veil", name="The Veil",
        kind="secret_society",
        description="Totuutta etsivä salaseura. Ainoa ryhmä, joka tietää, "
                    "että Cunaen jumalat ovat vain heijastuksia ja että "
                    "drow-uskonto on valhetta (Garruthan unia). Estää tiedon "
                    "leviämisen salamurhilla.",
        motto="Verho suojaa heikkoja totuudelta.",
        secret=True, alignment="lawful neutral",
        operating_kingdoms=["aterterra", "fundarla", "tarmaas"],
        ranks=[
            OrganisationRank(key="censor", name="Sensuroija", tier=2,
                             description="Korjaa historiaa."),
        ],
        roles=[
            OrganisationRole(key="researcher", name="Tutkija",
                             description="Kaivaa kiellettyä totuutta."),
        ],
        members=[
            OrganisationMember(npc_id="npc_ilyana",
                               npc_name="Ilyana \"Redact\" Silaqui",
                               rank_key="censor", role_keys=[],
                               notes="Huippusalamurhaaja-sensuroija."),
            OrganisationMember(npc_id="npc_seraphina", npc_name="Seraphina",
                               role_keys=["researcher"],
                               notes="Tutkija; Beatricen äiti."),
        ],
        relations={},
        color=(120, 120, 140),
        tags=["secret_society"],
    )

    famiglia = Organisation(
        key="famiglia_dell_orso", name="La Famiglia dell'Orso",
        kind="criminal",
        description="Frandin rikollissyndikaatti. Hallitsee salakuljetusta, "
                    "suojelurahoja ja yrittää kaapata T.R.A.:n teknologiaa.",
        motto="Karhu muistaa velkansa.",
        secret=True, alignment="neutral evil",
        headquarters_city="frand", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas"], operating_cities=["frand"],
        ranks=[
            OrganisationRank(key="capo_dei_capi", name="Capo dei Capi", tier=1,
                             description="Pomojen pomo."),
            OrganisationRank(key="consigliere", name="Consigliere", tier=2,
                             description="Neuvonantaja."),
            OrganisationRank(key="soldato", name="Soldato", tier=4,
                             description="Jalkaväki."),
        ],
        roles=[
            OrganisationRole(key="spymaster", name="Vakoilupäällikkö",
                             description="Salakuuntelu ja solutus."),
        ],
        members=[
            OrganisationMember(npc_id="npc_rahgo", npc_name="Rahgo \"Karhu\"",
                               rank_key="capo_dei_capi", role_keys=[],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="Kyborgipomo, augmentoidut rautakourat."),
            OrganisationMember(npc_id="npc_zaira", npc_name="Zaira \"La Volpe\"",
                               rank_key="consigliere", role_keys=["spymaster"],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="Consigliere; vakoilu ja salamurhat."),
        ],
        relations={},
        color=(120, 80, 60),
        tags=["criminal"],
    )

    efi = Organisation(
        key="efi", name="E.F.I. (External First Investigation)",
        kind="agency",
        description="Tarmaaksen salainen valtiopoliisi. Tutkii taikuuteen ja "
                    "teknologiaan liittyviä rikoksia; pitää yllä järjestystä. "
                    "Sisältää salaisen Department 0:n.",
        motto="Järjestys ennen totuutta.",
        secret=False, alignment="lawful neutral",
        headquarters_city="frand", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas"], operating_cities=["frand"],
        ranks=[
            OrganisationRank(key="director", name="Johtaja", tier=1,
                             description="E.F.I.:n johtaja."),
            OrganisationRank(key="aspicio", name="Aspicio", tier=4,
                             description="Kenttäagentti."),
        ],
        roles=[],
        members=[
            OrganisationMember(npc_id="npc_nilf", npc_name="Nilf Duvlae",
                               rank_key="director", role_keys=[],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="E.F.I.:n johtaja."),
            OrganisationMember(npc_id="npc_sam_undercave", npc_name="Sam Undercave",
                               rank_key="aspicio", role_keys=[],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="Tiro Aspicio (taso 4)."),
            OrganisationMember(npc_id="npc_eemil", npc_name="Eemil Jakson",
                               rank_key="aspicio", role_keys=[],
                               kingdom_key="tarmaas", city_key="frand",
                               notes="Department 0 — Agentti 3."),
        ],
        relations={},
        color=(90, 110, 140),
        tags=["agency", "law"],
    )

    aequitas = Organisation(
        key="aequitas", name="Aequitas & The Boundless",
        kind="order",
        description="Cunaen ehdottoman Pää Codexin vartijat omalla "
                    "ylikansallisella saarellaan. Erikoisjoukot, The "
                    "Boundless, voivat ohittaa minkä tahansa valtion lait ja "
                    "tuomita maailman tasapainon uhkaajat Nullifikaatioon.",
        motto="Tasapaino ennen kaikkea.",
        secret=False, alignment="lawful neutral",
        operating_kingdoms=["tarmaas", "fundarla", "smardu", "aterterra",
                            "oblitus"],
        ranks=[
            OrganisationRank(key="arbiter", name="Arbiter", tier=1,
                             description="Aequitaksen tuomari."),
            OrganisationRank(key="boundless", name="Boundless", tier=3,
                             description="Lain rajaton käsi."),
        ],
        roles=[],
        members=[],
        relations={},
        color=(200, 200, 210),
        tags=["order", "law", "neutral"],
    )

    scale_riders = Organisation(
        key="unhael_scale_riders", name="Unhael Scale Riders",
        kind="order",
        description="Smardun lohikäärmeratsastajat ja -ekologit. Kasvattavat "
                    "ja vartioivat lohikäärmeitä Antanardin hautomossa. "
                    "Konservatiivinen siipi F.E.R.I.D. valvoo vanhoja lakeja.",
        motto="Suomu ja teräs.",
        secret=False, alignment="lawful neutral",
        headquarters_city="antanard", headquarters_kingdom="smardu",
        operating_kingdoms=["smardu"], operating_cities=["antanard", "juamore"],
        ranks=[
            OrganisationRank(key="councillor", name="Neuvoston jäsen", tier=2,
                             description="Lohikäärme-ekologi."),
            OrganisationRank(key="overseer", name="Ylivalvoja", tier=3,
                             description="Hautomon valvoja."),
        ],
        roles=[],
        members=[
            OrganisationMember(npc_id="npc_aedria", npc_name="Aedria Fegel",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="smardu", city_key="antanard",
                               notes="Lohikäärme-ekologi; Magnuksen mentori."),
            OrganisationMember(npc_id="npc_jogra", npc_name="Jogra Greev",
                               rank_key="overseer", role_keys=[],
                               kingdom_key="smardu", city_key="antanard",
                               notes="Hautomolaitoksen ylivalvoja (F.E.R.I.D.)."),
            OrganisationMember(npc_id="npc_gaufex", npc_name="Gaufex Bakduvar",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Komentaja & tiedustelumestari; ratsastaa "
                                     "Khaldryksella. Salainen agenda."),
            OrganisationMember(npc_id="npc_brynja", npc_name="Brynja Ironfist",
                               rank_key="overseer", role_keys=[],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Ratsastaa Silverscalella; tuki Aesican "
                                     "kapinaa ilmasta."),
        ],
        relations={},
        color=(120, 140, 120),
        tags=["order", "dragons"],
    )

    free_south = Organisation(
        key="vapaan_etelan_koalitio", name="Vapaan Etelän Koalitio",
        kind="coalition",
        description="Aesican kapinasta syntynyt liittouma, joka yhdistää "
                    "vapautetut orjat, Oblituksen sorretut heimot ja "
                    "irtautuneet etelän kaupungit (Aesica, Old Vaisil, Fort "
                    "Whitestone) Emnar Redfein ja orjakaupan vastaiseen "
                    "rintamaan.",
        motto="Ei enää kahleita.",
        secret=False, alignment="chaotic good",
        headquarters_city="aesica", headquarters_kingdom="oblitus",
        operating_kingdoms=["oblitus"],
        operating_cities=["aesica", "tukor_sheg", "pulker", "aklobar",
                          "kravok", "old_vaisil"],
        ranks=[
            OrganisationRank(key="figurehead", name="Symboli", tier=1,
                             description="Kapinan kasvot (Krusk)."),
            OrganisationRank(key="administrator", name="Hallinto", tier=2,
                             description="Byrokratia & diplomatia (Antos)."),
            OrganisationRank(key="councillor", name="Heimoneuvosto", tier=3,
                             description="Heimojen edustajat."),
        ],
        roles=[
            OrganisationRole(key="general", name="Armeijan kasvo",
                             description="Sotilaallinen johto."),
            OrganisationRole(key="diplomat", name="Diplomaatti",
                             description="Koalition neuvottelut."),
        ],
        members=[
            OrganisationMember(npc_id="npc_krusk", npc_name="Krusk Akarsho",
                               rank_key="figurehead", role_keys=["general"],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Vastentahtoinen keisari; kapinan symboli."),
            OrganisationMember(npc_id="npc_antos_orac", npc_name="Antos Orac",
                               rank_key="administrator", role_keys=["diplomat"],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Hallinto & diplomatia."),
            OrganisationMember(npc_id="npc_efauxer", npc_name="Efauxer Redfei",
                               rank_key="administrator", role_keys=["diplomat"],
                               kingdom_key="tarmaas", city_key="old_vaisil",
                               notes="Koalition pääarkkitehti; Old Vaisil."),
            OrganisationMember(npc_id="npc_nogjat", npc_name="Makohf Sheg",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="oblitus",
                               notes="Tukor Sheg; kapinan sytyttäjä."),
            OrganisationMember(npc_id="npc_bervider", npc_name="Bervider",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Tukor Sheg."),
            OrganisationMember(npc_id="npc_wok", npc_name="Wok Metsam",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="oblitus",
                               notes="Pulker."),
            OrganisationMember(npc_id="npc_longhop", npc_name="Longhop",
                               rank_key="councillor", role_keys=[],
                               kingdom_key="oblitus", city_key="aesica",
                               notes="Kravok (grung)."),
            OrganisationMember(npc_id="npc_richard_walker",
                               npc_name="Richard Walker",
                               rank_key="administrator", role_keys=[],
                               notes="Fort Whitestone liittyi koalitioon."),
        ],
        relations={"unhael_scale_riders": "ally",
                   "brotherhood_of_glorious_sun": "enemy"},
        color=(210, 150, 60),
        tags=["coalition", "ally"],
    )

    baenrahel = Organisation(
        key="talo_baenrahel", name="Talo Baenrahel",
        kind="noble_house",
        description="Aterterran mahtava drow-arkkimaagisuku; hallitsee "
                    "Aether-arkistoja ja Faerzress-verkostoa. Verkkojen "
                    "Talo (palvelijoiden talo) on suvun konehuone, jossa "
                    "vallitsee Lex Null (magian vaimennus) ja armoton "
                    "sisäinen hierarkia palvelijasukujen (Xorlath, Myrdin, "
                    "Zir) kesken.",
        motto="Verkko pitää kaiken.",
        secret=False, alignment="lawful evil",
        headquarters_city="zertath_lanke", headquarters_kingdom="aterterra",
        operating_kingdoms=["aterterra"], operating_cities=["zertath_lanke"],
        ranks=[
            OrganisationRank(key="lord", name="Lordi / Arkistojen johtaja",
                             tier=1, description="Suvun pää (Altheon)."),
            OrganisationRank(key="heir", name="Perijä", tier=2,
                             description="Tuleva arkkimaagi (Elarae)."),
            OrganisationRank(key="fist", name="Nyrkki", tier=3,
                             description="Sotilaallinen upseeri (Dravin)."),
            OrganisationRank(key="captain", name="Vartiokapteeni", tier=4,
                             description="Palvelijoiden kurinpito."),
            OrganisationRank(key="servant", name="Palvelija", tier=6,
                             description="Xorlath/Myrdin/Zir-suvut."),
        ],
        roles=[
            OrganisationRole(key="archivist", name="Arkistonhoitaja",
                             description="Aether-arkistot & sielukone."),
            OrganisationRole(key="disciplinarian", name="Kurinpitäjä",
                             description="Xorlath-vartijat."),
            OrganisationRole(key="beastmaster", name="Petojen kesyttäjä",
                             description="Ratsuliskot & vahtihämähäkit."),
        ],
        members=[
            OrganisationMember(npc_id="npc_altheon", npc_name="Altheon Baenrahel",
                               rank_key="lord", role_keys=["archivist"],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Suvun pää; huoltaa myös sielukonetta."),
            OrganisationMember(npc_id="npc_elarae", npc_name="Elarae Baenrahel",
                               rank_key="heir", role_keys=[],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Perijä; kokeilee palvelijoilla."),
            OrganisationMember(npc_id="npc_dravin", npc_name="Dravin Baenrahel",
                               rank_key="fist", role_keys=[],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Velve Dro -upseeri."),
            OrganisationMember(npc_id="npc_vorn", npc_name="Vorn Xorlath",
                               rank_key="captain", role_keys=["disciplinarian"],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Vartiokapteeni; myytävissä kullalla."),
            OrganisationMember(npc_id="npc_nymia", npc_name="Nymia Xorlath",
                               rank_key="servant", role_keys=["disciplinarian"],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Ovivahti; kuuntelee kattopalkeista."),
            OrganisationMember(npc_id="npc_thala", npc_name="Thala Myrdin",
                               rank_key="servant", role_keys=[],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Pääemäntä; palvelijoiden epävirallinen johtaja."),
            OrganisationMember(npc_id="npc_kael_myrdin", npc_name="Kael Myrdin",
                               rank_key="servant", role_keys=[],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Keittiöpoika; haluaa paeta pintaan."),
            OrganisationMember(npc_id="npc_zirkass", npc_name="Zir'kass",
                               rank_key="servant", role_keys=["beastmaster"],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Tallimestari."),
            OrganisationMember(npc_id="npc_faldor", npc_name="Faldor \"Sokea Kipinä\"",
                               rank_key="servant", role_keys=[],
                               kingdom_key="aterterra", city_key="zertath_lanke",
                               notes="Kristallihuoltaja; salaa Dobluth Dro."),
        ],
        relations={"talo_icharyd": "serves", "the_veil": "secret_pact"},
        color=(90, 70, 130),
        tags=["drow", "noble_house"],
    )

    cora_zero = Organisation(
        key="cora_zero", name="Cora 0",
        kind="criminal",
        description="Profunduksen (Ravenstonen viemäriverkoston alainen "
                    "salakaupunki) ammattirikollisten järjestö. Valmistautuu "
                    "sotaan maanpäällisiä vampyyrejä vastaan ja haluaa "
                    "syrjäyttää paroni Jugorain; liittolaisena Talo Despanan "
                    "drow-salamurhaajat.",
        motto="Syvyydet kuuluvat meille.",
        secret=True, alignment="neutral evil",
        headquarters_city="ravenstone", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas", "aterterra"],
        operating_cities=["ravenstone"],
        ranks=[
            OrganisationRank(key="boss", name="Pomo", tier=1,
                             description="Cora 0:n johtaja."),
            OrganisationRank(key="operative", name="Agentti", tier=4,
                             description="Vakooja / tiedonkerääjä."),
        ],
        roles=[
            OrganisationRole(key="spymaster", name="Tiedonkerääjä",
                             description="Vakoilu ja tiedustelu."),
        ],
        members=[
            OrganisationMember(npc_id="npc_gaur", npc_name="Gaur Rakek",
                               rank_key="boss", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Tabaxi-johtaja; drow-liittouma."),
            OrganisationMember(npc_id="npc_jivin", npc_name="Jivin Lukom",
                               rank_key="operative", role_keys=["spymaster"],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Kirjastonhoitaja-vakooja."),
        ],
        relations={"talo_baenrahel": "neutral",
                   "court_of_dimerius": "enemy"},
        color=(80, 90, 110),
        tags=["criminal"],
    )

    dimerius_court = Organisation(
        key="court_of_dimerius", name="Dimeriuksen hovi",
        kind="secret_society",
        description="Ravenstonen vampyyriverkosto. Muinainen Dimerius "
                    "Blackfeet manipuloi kaupunkia Corvus Spelchrum "
                    "-kryptasta; muinaiset vampyyrit suojelevat häntä "
                    "paroni Jugorailta, joka yrittää kaapata hänen voimansa.",
        motto="Veri muistaa.",
        secret=True, alignment="lawful evil",
        headquarters_city="ravenstone", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas"], operating_cities=["ravenstone"],
        ranks=[
            OrganisationRank(key="lord", name="Vampyyrilordi", tier=1,
                             description="Dimerius Blackfeet."),
            OrganisationRank(key="ancient", name="Muinainen", tier=2,
                             description="Ikivanhat suojelijat."),
            OrganisationRank(key="spawn", name="Sikiö", tier=5,
                             description="Uudet vampyyrit / orjat."),
        ],
        roles=[],
        members=[
            OrganisationMember(npc_id="npc_dimerius", npc_name="Dimerius Blackfeet",
                               rank_key="lord", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Teljetty kryptaan; manipuloi varjoista."),
            OrganisationMember(npc_id="npc_polsen", npc_name="Polsen",
                               rank_key="ancient", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Johtaa vampyyriverkostoa."),
            OrganisationMember(npc_id="npc_vilan", npc_name="Vilan Norgrad",
                               rank_key="ancient", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="350+ v palvelija."),
            OrganisationMember(npc_id="npc_herold", npc_name="Herold Reggefoi",
                               rank_key="ancient", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="800+ v palvelija."),
            OrganisationMember(npc_id="npc_jugorai", npc_name="Jugorai Millwind",
                               rank_key="ancient", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Paroni; yrittää kaapata Dimeriuksen "
                                     "voiman (sisäinen vihollinen)."),
            OrganisationMember(npc_id="npc_davos", npc_name="Davos Wolfbane",
                               rank_key="spawn", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Jugorain vampyyriorja."),
        ],
        relations={"cora_zero": "enemy", "deaths_vigil": "enemy"},
        color=(120, 40, 60),
        tags=["antagonist", "undead", "secret_society"],
    )

    avarath = Organisation(
        key="avarath_cult", name="Avarath-kultti",
        kind="cult",
        description="Ravenstonessa kasvava kultti, joka palvoo 'Avarathia'. "
                    "Todellisuudessa jumala on muinainen Aboleth, joka pesee "
                    "palvojiensa mielet fanaattisiksi orjiksi Clay Shoren "
                    "vedenalaisesta piilostaan.",
        motto="Syvyys kutsuu.",
        secret=True, alignment="chaotic evil",
        headquarters_city="ravenstone", headquarters_kingdom="tarmaas",
        operating_kingdoms=["tarmaas"], operating_cities=["ravenstone"],
        ranks=[
            OrganisationRank(key="god", name="Vale-jumala", tier=1,
                             description="Aboleth Avarath."),
            OrganisationRank(key="high_priest", name="Ylipappi", tier=2,
                             description="Kultin perustajat."),
        ],
        roles=[],
        members=[
            OrganisationMember(npc_id="npc_avarath", npc_name="Avarath (Aboleth)",
                               rank_key="god", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Mieliä pesevä Aboleth."),
            OrganisationMember(npc_id="npc_edmun", npc_name="Edmun Padel",
                               rank_key="high_priest", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Perustaja / pääpappi."),
            OrganisationMember(npc_id="npc_hannes", npc_name="Hannes Allroad",
                               rank_key="high_priest", role_keys=[],
                               kingdom_key="tarmaas", city_key="ravenstone",
                               notes="Perustaja / pääpappi."),
        ],
        relations={},
        color=(60, 120, 120),
        tags=["antagonist", "cult", "aberration"],
    )

    return [dath, deaths_vigil, seekers, veil, famiglia, efi, aequitas,
            scale_riders, baenrahel, free_south, cora_zero, dimerius_court,
            avarath]


# --------------------------------------------------------------------- #
# Campaign lore notes — the big Aterterra / cosmology reveals for the DM.
# --------------------------------------------------------------------- #
def lore_campaign_notes():
    """Return CampaignNote objects capturing the deep Aterterra secrets,
    so the reveals live in the campaign's notes tab from day one."""
    from data.campaign import CampaignNote
    specs = [
        ("SYVYYDEN UNI (Reverie d'Oloth) — Aterterran drow-uskonto väittää "
         "Faerzress-kristallien säteilyn olevan jumalallinen, rauhoittava "
         "'Syvyyden Uni'. Todellisuudessa se on maailmantitaani Garruthan "
         "hermoverkon vuotoa: Baenrahel-suvun maaginen suodatin muuttaa "
         "titaanin tuskan ja muistot kauniiksi kehtolauluksi. Puhdasveriset "
         "kuulevat laulun; puoliveriset (Dobluth Dro, kuten Beatrice) ja "
         "riittävän vahvat kuulevat kahlitun titaanin huudon — siksi "
         "sekaveri on kuolemantuomion arvoinen: se voi paljastaa valheen."),
        ("VANQURIONIN SYDÄN — Zer'tath Lanken Kristallijärven pohjassa, "
         "Matriarkan palatsin alla, lepää muinainen Sarrukh-sielukone. "
         "Tuomitut pudotetaan elävinä 'Tuomion kuiluun' ('Syvyyden Kaste'); "
         "kone repii heidän sielunsa ja kanavoi elinvoiman Caznalle ja "
         "sisäpiirille — tämä pitää Caznan ikuisesti nuorena. Aterterran "
         "eristys (Lex Claustrum) suojelee tätä salaisuutta niin pinnalta "
         "(Veljeskunta, T.R.A., Veil) kuin Death's Vigililtä."),
        ("KESKIMEREN SYNTY (The Meridian Sundering) — Keskimeri ei ollut "
         "alun perin meri. Mantereen ytimessä oli Sarrukhien pääkaupunki "
         "Vanqurion. Kun ensimmäinen Redfei (Veru-ihon kantaja) kytkettiin "
         "titaani Garruthaan, hän räjäytti itsensä tahallaan; räjähdys repi "
         "mantereen ytimen irti ja meret täyttivät tyhjiön. Keskimerta "
         "ympäröivät vuoristot ovat kivettyneitä shokkiaaltoja, ja ikuiset "
         "myrskyt titaanin yhä vuotavaa energiaa."),
        ("PROJEKTI 'KAIKU' — n. 20 v sitten Aterterran Faerzress-verkosto "
         "alkoi horjua. The Veil lähetti analyytikkonsa Seraphinan "
         "auttamaan arkistojen johtajaa Altheonia. He vakauttivat verkoston "
         "(Echo-Mythal) — siksi Altheon on korvaamaton eikä Cazna voi "
         "tappaa häntä. Työn aikana he löysivät Syvyyden Unen totuuden, "
         "rakastuivat, ja Beatrice syntyi. Salaisen sopimuksen hinta: "
         "Seraphina karkotettiin lapsen kanssa pintaan ja Altheon suostui "
         "The Veilin Geas-loitsuun."),
        ("KRUSK = KÄVELEVÄ YDINPOMMI — Kun drow-eliitti näkee Kruskin selän "
         "Veru-palasineen, he näkevät saman pedon joka tuhosi Vanqurionin — "
         "ja Tarquvasin aaveen. Jos Krusk astuu Kristallijärven rannalle tai "
         "arkistoihin, hän voi resonoida suoraan sielukoneen ja Garruthan "
         "kanssa ja rikkoa drowien 2000 vuotta varjeleman valheen — mikä "
         "sytyttäisi Aterterrassa sisällissodan."),
        ("AESICAN KAPINA — Aesica (~50 000 as., örkkien satamakaupunki "
         "Oblituksessa) kävi läpi verisen kapinan: hirmuvaltias kreivi "
         "Erokme Belmudar syöstiin vallasta ja kaupunki liittyi Vapaan "
         "Etelän Koalitioon. Nyt sulkutila (martial law); kadut ovat "
         "räjähdysherkät, kun vapautetut orjat jakavat omankädenoikeutta. "
         "Krusk on kapinan symboli ('vastentahtoinen keisari'). Areenan "
         "(Nak Magnok Kor Adez) alla sykkii yhä Convergence Engine "
         "-sielukone; Unhael Scale Riders liikkuu alueella omalla "
         "salaisella agendallaan (kuningas Saxigniksen pelastus)."),
        ("RAVENSTONEN KOLMEN RINTAMAN SOTA — Tarmaaksen 'mädäntynyt omena', "
         "ulospäin satamakaupunki ja Asylum Purgo -parantola, sisältä "
         "nekromantian keskus. (1) Vampyyrien sisällissota: paroni Jugorai "
         "Millwind yrittää kaapata kryptaan (Corvus Spelchrum) teljetyn "
         "muinaisen Dimerius Blackfeetin voiman; muinaiset vampyyrit "
         "(Polsen, Vilan, Herold) estävät. (2) Alamaailma: Cora 0 (Gaur "
         "Rakek) + Talo Despanan drowt puhdistavat katuja ja tähtäävät "
         "paronin syrjäyttämiseen. (3) Laki: E.F.I.-agentti Sam Undercave "
         "kerää todisteita → Nullifikaatio ('Kirottu maa', Death's Vigil "
         "polttaa). Taustalla Asylum Purgon Greg Silverhand (ihmiskokeet) "
         "ja Clay Shoren Avarath-kultti (Aboleth). Padak etsii täältä "
         "parannusta — pahin mahdollinen paikka."),
        ("PROTOKOLLA OMEGA (Fort Whitestone) — Maclebar Islen linnakkeen "
         "kellaritaso on taskuulottuvuus, jossa on 8000 Automata Trooperia "
         "(CR 4), Whitestone Colosseja (CR 14) ja sukellusveneita. Walkerin "
         "suku (esi-isä Vermok) rakensi armeijan kosmisen karanteenin "
         "ylläpitoon kahlittua Garrutha-titaania vastaan. Armeijan "
         "ensisijainen ohjelmointi (Protokolla Omega) tuhoaa 'Uuden "
         "Keisarin' — kuka tahansa joka resonoi Veru-ihon palojen kanssa. "
         "KOSKA KRUSK KANTAA VERU-PALOJA, armeijan herättäminen asettaa sen "
         "välittömästi Kruskin tappo-ohjelmointiin. Armeijan avaa vain "
         "Walker-veri + sinettisormus (Blitz), joka on juuri herätetty "
         "kuolleista (Nundai). Linnakkeessa on myös kosminen kartta "
         "(kristallikupu + Phlogiston)."),
        ("OLD VAISIL — SODAN HERMOKESKUS — Tarmaaksen eteläkärjen "
         "arabityylinen satama- ja eläkekaupunki (~80 000 as.) irtautui "
         "Tarmaaksesta ja muodosti Vapaan Etelän Koalition Aesican ja "
         "Maclebar Islen kanssa, katkaisten Tarmaas–Oblitus-kauppareitit. "
         "Efauxer Redfei johtaa; satamassa massiivinen rekrytointi (Undur "
         "Stunrack), hirttoaukiolla armoton oikeus (Gilhard Blacktooth). "
         "Uhat: Chrith Lar -huumekriisi (Beon Vildman), Kraken Gobroim "
         "satamassa, Emnarin/Tarmaaksen vakoojat ja palkkasoturit (Volden "
         "murhasi satamaruhtinas Giluanin), sabotaasi ja pakolaisvirrat. "
         "Grand Gardenissa tapahtui salamurhayritys jossa Blitz kuoli "
         "(Gersnet + petturi-hovimestari Orien)."),
        ("VEKSLA — 'NIGHT OF THE HEART' -JÄLKEEN — Tarmaaksen "
         "maatalouskaupunki Bladvine-metsän rajalla toipuu nekromantikko "
         "Fausterin verilöylystä (yli 1 200 kuoli/pakeni; sankarit Kaldir & "
         "Ailas pysäyttivät hänet). Paroni Potvark on veloissa ja poissa "
         "pelistä; hallitsee Vanhimpien Neuvosto + Metsän Suojelijat "
         "(dryadit, jotka Ulvin isä Bram Boulderroot perusti). Nälkäinen "
         "metsä hyökkää (Mavielf, karhumies Jay Upto). Aghuantin temppeli "
         "naulattu umpeen. Faunderin tilalla piilottelee salainen veteraani "
         "Gurug Brask ja Elisan haamu. Ryhmän tilanne: Sam Undercave "
         "kuulustelee heitä Feather Pillow Innissä, kapteeni Zetris "
         "väijytti Thomasta (joka on jo lähdössä), ja Ulv on isänsä "
         "historian ytimessä."),
    ]
    return [CampaignNote(text=t, category="lore") for t in specs]


def add_lore_organisations(camp) -> None:
    """Append canon organisations to the campaign (skipping any whose key
    already exists). Call after ``ensure_organisations_on_campaign``."""
    from data import organizations as orgs
    existing = {o.key for o in orgs.ensure_organisations_on_campaign(camp)}
    runtime = camp.organisations
    for org in lore_organisations():
        if org.key not in existing:
            runtime.append(org)
