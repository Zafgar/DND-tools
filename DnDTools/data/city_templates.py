"""
D&D 5e Premade City/Town Templates — Ready-to-use settlement configurations.

Each template creates a complete settlement with:
- Districts, key buildings, shops, temples, taverns
- Key NPCs (mayor, guards, merchants)
- Adventure hooks and settlement features
- Level-appropriate for D&D 5e 2014

Usage:
    from data.city_templates import CITY_TEMPLATES, get_city_template, apply_city_template
"""
from typing import Dict, List, Optional


# ============================================================================
# CITY / TOWN TEMPLATES
# ============================================================================

CITY_TEMPLATES: Dict[str, dict] = {

    # ========================================================================
    # VILLAGES (Tier 1, levels 1-4, pop 50-300)
    # ========================================================================

    "village_farming": {
        "name": "Viljapelto",
        "tier": 1,
        "settlement_type": "village",
        "population": 120,
        "description": (
            "Pieni maanviljelyskylä jokirannan hedelmällisellä tasangolla. "
            "Kylää ympäröivät vehnäpellot ja laidunmaat. Keskellä on vanha tammi, "
            "jonka alla kyläläiset kokoontuvat juhlapyhinä. Kylällä ei ole muuria, "
            "mutta kyläpäällikkö ja vapaaehtoiset vartijat pitävät järjestystä."
        ),
        "districts": [
            {
                "name": "Kylänaukio", "type": "district",
                "description": "Kylän keskusaukio vanhan tammen ympärillä. Täällä pidetään markkinat ja kokoukset.",
                "buildings": [
                    {"name": "Kyläpäällikön Talo", "type": "building",
                     "description": "Kylän suurin talo, toimii myös kokoontumispaikkana."},
                    {"name": "Kylänkaivo", "type": "building",
                     "description": "Kylän ainoa puhtaan veden lähde."},
                ],
            },
        ],
        "key_npcs": [
            {"name": "Eero Tamminen", "role": "Kyläpäällikkö", "race": "Human", "gender": "Male",
             "appearance": "Vankka, auringonpolttama maanviljelijä, harmaat ohimoilla",
             "personality": "Rehellinen ja perinteikäs. Epäilee muukalaisia mutta kunnioittaa rohkeutta.",
             "occupation": "Village Elder", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
            {"name": "Siiri Koivunen", "role": "Kylähän parantaja", "race": "Human", "gender": "Female",
             "appearance": "Vanha nainen, kävelee kepin kanssa, tuoksuu yrtit",
             "personality": "Viisas ja lempeä. Tuntee jokaisen kylän asukkaan.",
             "occupation": "Herbalist", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "shops": ["general_store_tier1"],
        "inns": ["modest_roadside"],
        "special_features": [
            "Vanhan tammen juurella on ikivanha pakanallinen alttari (DC 12 Religion tunnistaa)",
            "Kyläläisiltä voi vuokrata hevosen tai kärryn edullisesti",
            "Joen rannalla on pieniä kalastusveneitä vapaaseen käyttöön",
        ],
        "hooks": [
            "Pedot ovat alkaneet hyökkäillä karjaa vastaan — jäljet johtavat metsään",
            "Vanha kaivo on alkanut tuottaa outoihin maistuvaa vettä",
            "Kauppias ei ole palannut naapurikylästä viikkoon",
            "Kyläläiset kertovat näkevänsä valoja metsässä öisin",
        ],
        "defenses": "Ei muureja. 4 vapaaehtoista vartijaa (Commoner), kyläpäällikkö (Veteran).",
    },

    "village_fishing": {
        "name": "Verkkoranta",
        "tier": 1,
        "settlement_type": "village",
        "population": 85,
        "description": (
            "Pieni kalastajakylä merenrannalla tai suuren järven laidalla. "
            "Tuore kalantuoksu täyttää ilman. Veneet kiikkuvat laiturissa "
            "ja verkot roikkuvat kuivumassa auringossa. Kylä elää kalasta "
            "ja saa satunnaisesti kauppiaita rannikkolaivasta."
        ),
        "districts": [
            {
                "name": "Satama", "type": "port",
                "description": "Pieni puulaituri ja venevaja. Kalasaaliit käsitellään täällä.",
                "buildings": [
                    {"name": "Venevaja", "type": "building",
                     "description": "Suojaa kymmenkunta pientä kalastusvenettä."},
                    {"name": "Kalapöytä", "type": "building",
                     "description": "Ulkotiski jossa kala myydään ja perkataan."},
                ],
            },
        ],
        "key_npcs": [
            {"name": "Risto Aalto", "role": "Kalastajamestari", "race": "Human", "gender": "Male",
             "appearance": "Leveähartiainen, parta suolaisessa tuulessa, tumma iho",
             "personality": "Hiljainen ja periksiantamaton. Kunnioittaa merta.",
             "occupation": "Fisher Elder", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "shops": [],
        "inns": ["modest_roadside"],
        "special_features": [
            "Voi vuokrata kalastusveneen (1 gp/päivä)",
            "Kalastajat tietävät rannikon vaaralliset kohdat",
            "Rannikkolaiva pysähtyy kerran kuussa tuomaan tarvikkeita",
        ],
        "hooks": [
            "Kalastajat ovat nähneet valtavan varjon veden alla",
            "Yksi vene palasi tyhjänä — miehistö kadonnut",
            "Myrsky paljasti hylyn rannalla — sen ruumassa on jotain outoa",
        ],
        "defenses": "Ei muureja. Kalastajat taistelevat tarpeen tullen (Commoner + harpuunat).",
    },

    # ========================================================================
    # TOWNS (Tier 2, levels 5-10, pop 500-5000)
    # ========================================================================

    "town_market": {
        "name": "Kauppakaari",
        "tier": 2,
        "settlement_type": "town",
        "population": 2200,
        "description": (
            "Vilkas markkinakaupunki kahden tärkeän kauppareitin risteyksessä. "
            "Matalan kivimuurin ympäröimä kaupunki on tunnettu viikkomarkkinoistaan "
            "ja käsityöläisistään. Kaupungissa on merkittävä kauppiaiden kilta ja "
            "pieni garnisooni porttien luona."
        ),
        "districts": [
            {
                "name": "Toriaukio", "type": "district",
                "description": "Kaupungin sydän — suuri avoin aukio jossa markkinat pidetään.",
                "buildings": [
                    {"name": "Kaupunginlämpiö", "type": "building",
                     "description": "Kaupungintalo ja killan kokoushuone."},
                    {"name": "Kauppiaiden Kiltatalo", "type": "building",
                     "description": "Killan pääkonttori, kauppasopimukset ja varastot."},
                ],
            },
            {
                "name": "Käsityöläiskortteli", "type": "district",
                "description": "Seppiä, nahkureita, puuseppiä ja muita mestareita.",
                "buildings": [
                    {"name": "Mestarin Ahjo", "type": "building",
                     "description": "Kaupungin paras seppä, tekee tilaustyötä."},
                ],
            },
            {
                "name": "Porttialue", "type": "district",
                "description": "Muurien sisäpuolella porttien läheisyydessä. Vartioston kasarmi.",
                "buildings": [
                    {"name": "Vartiokasarmi", "type": "building",
                     "description": "Kaupunginvartion päämajaksi. 20 vartijaa."},
                    {"name": "Vankityrmä", "type": "building",
                     "description": "Pieni vankila kaupungin sääntöjen rikkojille."},
                ],
            },
        ],
        "key_npcs": [
            {"name": "Pormestari Aleksi Rautio", "role": "Pormestari", "race": "Human", "gender": "Male",
             "appearance": "Huoliteltu, kalliit vaatteet, kultatäpläinen silmälasi",
             "personality": "Diplomaattinen ja kaupallisesti ajatteleva. Kaikella on hinta.",
             "occupation": "Mayor", "attitude": "neutral",
             "stat_source": "monster:Noble"},
            {"name": "Kapteeni Helmi Teräs", "role": "Vartiostopäällikkö", "race": "Human", "gender": "Female",
             "appearance": "Lyhyt mutta voimakas, arpi oikealla poskella, kiillotettu haarniska",
             "personality": "Tiukka mutta oikeudenmukainen. Ei siedä rikollisia.",
             "occupation": "Guard Captain", "attitude": "neutral",
             "stat_source": "monster:Veteran"},
        ],
        "shops": ["general_store_tier2", "blacksmith_tier2", "alchemist_tier1"],
        "inns": ["comfortable_golden", "modest_roadside"],
        "special_features": [
            "Viikkomarkkinat joka sunnuntai — erikoistuotteet ja kaukaiset kauppiaat",
            "Kauppiaiden kilta voi järjestää kuljetuksia ja kauppareittejä",
            "Kaupunginvartio partioi öisin — turvallinen yöpyä",
            "Ilmoitustaulu porttien luona — tehtäväntarjoajat ja etsintäkuulutukset",
        ],
        "hooks": [
            "Kauppiaiden kilta epäilee vakoojaa killan sisällä",
            "Kauppakaravaani katosi matkalla läheiseen kaupunkiin",
            "Vartiosto etsii apua peikon pesän tuhoamiseen lähitienoilla",
            "Mystinen kauppias myy esineitä liian halvalla — niissä on kirous",
        ],
        "defenses": "Kivimuuri (30 ft), 20 vartijaa (Guard), kapteeni (Veteran), 2 porttia.",
    },

    "town_fortress": {
        "name": "Rautamäki",
        "tier": 2,
        "settlement_type": "town",
        "population": 1500,
        "description": (
            "Linnoituskaupunki strategisella kukkulalla rajaseudulla. "
            "Kaupunki rakennettiin suojaamaan rajaa ja kauppareittejä. "
            "Linnake hallitsee kukkulan huippua ja kaupunki levittäytyy "
            "sen juurelle. Sotilaallinen tunnelma on käsin kosketeltava."
        ),
        "districts": [
            {
                "name": "Linnake", "type": "castle",
                "description": "Kukkulan huipulla oleva kivilinnake. Komentajan päämaja.",
                "buildings": [
                    {"name": "Komentajan Torni", "type": "building",
                     "description": "Linnakkeen päätorni, kartanlakohuone ja asevarasto."},
                    {"name": "Kasarmit", "type": "building",
                     "description": "Garnisoonin kasarmi. 50 sotilasta."},
                ],
            },
            {
                "name": "Alakaupunki", "type": "district",
                "description": "Linnakkeen alapuolella oleva asutusalue kauppoineen.",
                "buildings": [],
            },
        ],
        "key_npcs": [
            {"name": "Komentaja Väinö Kivi", "role": "Garnisooninkomentaja", "race": "Human", "gender": "Male",
             "appearance": "Harmaantunut soturi, arpia kasvoissa, kireä katse",
             "personality": "Ankara ja strateginen. Turvallisuus ennen kaikkea.",
             "occupation": "Commander", "attitude": "neutral",
             "stat_source": "monster:Knight"},
        ],
        "shops": ["blacksmith_tier2", "general_store_tier1"],
        "inns": ["modest_roadside"],
        "special_features": [
            "Garnisooni voi tarjota saattajia vaarallisille alueille (50 gp/päivä)",
            "Linnakkeen asevarastosta voi ostaa sotilasvarusteita",
            "Strategiset kartat rajaseudusta (DC 15 Persuasion nähdäkseen)",
        ],
        "hooks": [
            "Partio ei palannut rajalta — komentaja tarvitsee tiedustelijoita",
            "Vihollismaa lähettää salamurhaajia rajalle",
            "Linnakkeen kellarista on löytynyt vanha salainen tunneli",
        ],
        "defenses": "Kivimuuri (40 ft), linnake, 50 sotilasta (Guard), 5 veteraania, komentaja (Knight).",
    },

    # ========================================================================
    # CITIES (Tier 3, levels 11-16, pop 5000-25000)
    # ========================================================================

    "city_trade_hub": {
        "name": "Kultasatama",
        "tier": 3,
        "settlement_type": "city",
        "population": 15000,
        "description": (
            "Suuri satamakaupunki ja kaupankäynnin keskus. Laivat tulevat ja menevät "
            "joka päivä tuoden eksoottisia tavaroita kaukaisilta mailta. Kaupunki on "
            "monikulttuurinen ja varakas, mutta myös korruption ja rikollisuuden vaivaaminen. "
            "Korkeat kivimuuri ja mahtavat porttitornit suojaavat kaupunkia."
        ),
        "districts": [
            {
                "name": "Satama-alue", "type": "port",
                "description": "Valtava satama laitureineen, varastoineen ja kauppakonttorineen.",
                "buildings": [
                    {"name": "Satamamestarin Konttori", "type": "building",
                     "description": "Satamaliikenteen valvonta ja tullimaksut."},
                    {"name": "Suurvarastot", "type": "building",
                     "description": "Kiltojen varastot tuontitavaroille."},
                ],
            },
            {
                "name": "Kauppiaiden Kortteli", "type": "district",
                "description": "Hienot kaupat ja kiltojen pääkonttorit. Rikkain alue.",
                "buildings": [],
            },
            {
                "name": "Vanha Kaupunki", "type": "district",
                "description": "Historiallinen keskusta temppelineen ja palatsineen.",
                "buildings": [
                    {"name": "Suuri Temppeli", "type": "temple",
                     "description": "Monijumalainen temppeli — papiston pääpaikka."},
                    {"name": "Kuvernöörin Palatsi", "type": "castle",
                     "description": "Kaupungin hallitsijan palatsi."},
                ],
            },
            {
                "name": "Varjokortteli", "type": "district",
                "description": "Köyhien ja rikollisten alue. Varokaa taskuvarkaita ja pahempaa.",
                "buildings": [
                    {"name": "Varkaiden Kiltatalo", "type": "building",
                     "description": "Salaisesti toimiva rikollisorganisaatio (DC 18 Investigation löytää)."},
                ],
            },
            {
                "name": "Maagikkojen Torni", "type": "building",
                "description": "Taikaakatemian ja loitsujentekijöiden torni. Maagisia palveluita tarjolla.",
                "buildings": [],
            },
        ],
        "key_npcs": [
            {"name": "Kuvernööri Astrid Kultakilpi", "role": "Kuvernööri", "race": "Human", "gender": "Female",
             "appearance": "Komea nainen, kultakruunu, silkkivaatteet, kylmä katse",
             "personality": "Älykäs ja kunnianhimoinen. Manipuloi taitavasti.",
             "occupation": "Governor", "attitude": "neutral",
             "stat_source": "monster:Noble"},
            {"name": "Arkkimaagi Otso Salamanteri", "role": "Maagikkojen johtaja", "race": "Half-Elf", "gender": "Male",
             "appearance": "Pitkä, hopeainen parta, hohtavat siniset silmät, tähtikuvioinen viitta",
             "personality": "Utelias ja etäinen. Kiinnostunut vain tiedosta ja magiasta.",
             "occupation": "Archmage", "attitude": "neutral",
             "stat_source": "monster:Archmage"},
            {"name": "Varjomestari Kaapo", "role": "Varkaiden killan johtaja", "race": "Halfling", "gender": "Male",
             "appearance": "Pieni, huomaamaton, aina hymyilee, sormissa kultasormuksia",
             "personality": "Hurmaava ja vaarallinen. Tietää kaiken mitä kaupungissa tapahtuu.",
             "occupation": "Thieves Guild Master", "attitude": "unfriendly",
             "stat_source": "monster:Assassin"},
        ],
        "shops": ["general_store_tier2", "blacksmith_tier3", "alchemist_tier2", "magic_shop_tier2", "magic_shop_tier3"],
        "inns": ["wealthy_spring", "comfortable_golden", "squalid_dockside"],
        "special_features": [
            "Maagikkojen torni tarjoaa loitsupalveluita (Spellcasting Services)",
            "Satama — voi vuokrata laivan tai matkustaa rannikkolinjalla",
            "Varkaiden kilta — voi ostaa tietoa tai palkata 'asiantuntijoita'",
            "Suurtemppeli — parantaminen, kirouksen poisto, ylösnousemus (palveluhinnastolla)",
            "Akateeminen kirjasto — Arcana, History, Religion tutkimus advantage",
        ],
        "hooks": [
            "Kuvernööri on korruptoitunut — oppositio etsii todisteita",
            "Merirosvot uhkaavat kauppareittejä — laivasto tarvitsee apua",
            "Varjokorttelin alla on muinainen luolasto täynnä unohtuneita aarteita",
            "Maagikkojen tornissa on tapahtunut räjähdys — jotain pakeni",
            "Kilpailevat kauppiaat palkkaavat seikkailijoita sabotoimaan toisiaan",
        ],
        "defenses": "Kivimuuri (50 ft), 200 vartijaa (Guard), 20 veteraania, 5 ritaria, arkkimaagi.",
    },

    "city_holy": {
        "name": "Pyhä Valonlähde",
        "tier": 3,
        "settlement_type": "city",
        "population": 8000,
        "description": (
            "Pyhiinvaelluskaupunki joka on rakennettu pyhän lähteen ympärille. "
            "Kymmenittäin temppelejä ja luostareita palvelee eri jumalia. "
            "Papisto hallitsee kaupunkia teokraattisesti. Kaupunki on tunnettu "
            "parannusihmeistään ja pyhäinjäännöksistään."
        ),
        "districts": [
            {
                "name": "Pyhä Alue", "type": "district",
                "description": "Temppelit ja luostarit. Vain puhtaat saavat astua sisään.",
                "buildings": [
                    {"name": "Valon Katedraali", "type": "temple",
                     "description": "Valtava katedraali — pyhiinvaelluksen päämäärä."},
                    {"name": "Pyhä Lähde", "type": "temple",
                     "description": "Parantava lähde (Lesser Restoration 1/päivä ilmaiseksi)."},
                ],
            },
            {
                "name": "Pyhiinvaeltajien Kortteli", "type": "district",
                "description": "Majoitusta ja palveluita pyhiinvaeltajille.",
                "buildings": [],
            },
        ],
        "key_npcs": [
            {"name": "Ylipiispa Valo Aurinkonen", "role": "Teokraatti", "race": "Human", "gender": "Male",
             "appearance": "Vanha, valkopartainen, hohtava kultainen sauva, lempeä hymy",
             "personality": "Hyvätahtoinen mutta dogmaattinen. Uskoo vakaasti jumalalliseen järjestykseen.",
             "occupation": "High Priest", "attitude": "friendly",
             "stat_source": "monster:Priest"},
        ],
        "shops": ["general_store_tier1", "temple_shop_tier1"],
        "inns": ["comfortable_golden", "modest_roadside"],
        "special_features": [
            "Pyhä lähde: Lesser Restoration ilmaiseksi 1/pv (ensimmäiselle pyhiinvaeltajalle)",
            "Temppelipalvelut alennettuun hintaan (-25%)",
            "Pyhät maaperän vaikutukset: Undead disadvantage saves pyhällä alueella",
            "Kirjasto pyhistä teksteistä — Religion tutkimus advantage",
        ],
        "hooks": [
            "Pyhä lähde on alkanut kuivua — syy tuntematon",
            "Kulttijäsen soluttautui temppeliin — kuka on petturi?",
            "Pyhäinjäännös varastettiin — se pitää löytää ennen kuin sitä käytetään väärin",
        ],
        "defenses": "Pyhitetyt muurit, 30 temppelisoturi (Guard), 5 paladin (Knight), ylipiispa.",
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_city_template(key: str) -> Optional[dict]:
    """Get a city template by key."""
    return CITY_TEMPLATES.get(key)


def get_city_templates_by_tier(tier: int) -> Dict[str, dict]:
    """Get all city templates for a given tier."""
    return {k: v for k, v in CITY_TEMPLATES.items() if v["tier"] == tier}


def get_city_templates_by_type(settlement_type: str) -> Dict[str, dict]:
    """Get all city templates for a given settlement type."""
    return {k: v for k, v in CITY_TEMPLATES.items() if v["settlement_type"] == settlement_type}


def get_all_settlement_types() -> List[str]:
    """Get unique settlement types."""
    return sorted(set(v["settlement_type"] for v in CITY_TEMPLATES.values()))


def apply_city_template(world, parent_location_id: str, template: dict,
                        custom_name: str = "") -> dict:
    """
    Apply a city template to the world, creating locations, districts, and NPCs.

    Returns dict with created IDs:
    {"location_id": ..., "district_ids": [...], "building_ids": [...], "npc_ids": [...]}
    """
    from data.world import add_location, add_npc

    name = custom_name or template["name"]

    # Create the main settlement location
    main_loc = add_location(
        world, name,
        location_type=template["settlement_type"],
        parent_id=parent_location_id,
        description=template["description"],
    )
    main_loc.population = template.get("population", 0)
    main_loc.tags = [f"tier{template['tier']}", template["settlement_type"]]

    # Notes: features, hooks, defenses
    notes_parts = []
    if template.get("defenses"):
        notes_parts.append(f"Puolustus: {template['defenses']}")
    if template.get("special_features"):
        notes_parts.append("\nErikoisuudet:")
        for feat in template["special_features"]:
            notes_parts.append(f"  - {feat}")
    if template.get("hooks"):
        notes_parts.append("\nSeikkailukoukut:")
        for hook in template["hooks"]:
            notes_parts.append(f"  - {hook}")
    main_loc.notes = "\n".join(notes_parts)

    district_ids = []
    building_ids = []
    npc_ids = []

    # Create districts
    for dist_data in template.get("districts", []):
        dist = add_location(
            world, dist_data["name"],
            location_type=dist_data.get("type", "district"),
            parent_id=main_loc.id,
            description=dist_data.get("description", ""),
        )
        district_ids.append(dist.id)

        # Create buildings within districts
        for bld_data in dist_data.get("buildings", []):
            bld = add_location(
                world, bld_data["name"],
                location_type=bld_data.get("type", "building"),
                parent_id=dist.id,
                description=bld_data.get("description", ""),
            )
            building_ids.append(bld.id)

    # Create key NPCs at the main location
    for npc_data in template.get("key_npcs", []):
        npc = add_npc(
            world, npc_data["name"],
            location_id=main_loc.id,
            race=npc_data.get("race", "Human"),
            gender=npc_data.get("gender", ""),
            appearance=npc_data.get("appearance", ""),
            personality=npc_data.get("personality", ""),
            occupation=npc_data.get("occupation", npc_data.get("role", "")),
            attitude=npc_data.get("attitude", "neutral"),
            stat_source=npc_data.get("stat_source", ""),
        )
        npc.tags = [f"tier{template['tier']}", npc_data.get("role", "")]
        npc_ids.append(npc.id)

    return {
        "location_id": main_loc.id,
        "district_ids": district_ids,
        "building_ids": building_ids,
        "npc_ids": npc_ids,
    }
