"""
D&D 5e Inn & Tavern Premade Templates — Ready-to-use location templates.

Each template creates a complete inn/tavern with:
- Name, description, atmosphere
- Room types & prices
- Menu (food & drink with prices)
- Staff NPCs (innkeeper, cook, barmaid, bouncer, etc.)
- Special features and hooks
- Appropriate for different quality tiers (squalid → aristocratic)

Usage:
    from data.inn_templates import INN_TEMPLATES, get_inn_template, apply_inn_template
    template = get_inn_template("modest_roadside")
    apply_inn_template(world, parent_location_id, template)
"""
from typing import Dict, List, Optional


# ============================================================================
# INN / TAVERN TEMPLATES
# ============================================================================

INN_TEMPLATES: Dict[str, dict] = {

    # ---- SQUALID TIER ----
    "squalid_rathole": {
        "name": "Rotan Kolo",
        "tier": "squalid",
        "location_type": "tavern",
        "description": (
            "Likainen ja ahdas luukku slummikorttelin kellarissa. Katto vuotaa, "
            "lattia on likainen maa, ja rottia näkee enemmän kuin asiakkaita. "
            "Olut on laimeaa ja ruoka epäilyttävää, mutta hinta on oikea "
            "ja kysymyksiä ei esitetä. Täällä kaupitellaan varastettua tavaraa, "
            "suunnitellaan ryöstöjä ja piileskeliään lain pitkää kättä."
        ),
        "atmosphere": "Pimeä, kostea ja epäilyttävä. Hämähäkinverkkoja ja rottien rapinaa.",
        "rooms": {
            "floor_space": {"name": "Lattiapaikka", "price_gp": 0.005, "count": 10,
                "description": "Paikka lattialla olkien joukossa. Varokaa taskuvarkaita."},
        },
        "menu": {
            "watery_ale": {"name": "Laimea olut", "price_gp": 0.002, "description": "Enemmän vettä kuin olutta."},
            "mystery_stew": {"name": "Mysteerikeitto", "price_gp": 0.004,
                "description": "Parempi olla kysymättä mitä padassa on. Täyttää vatsan."},
            "stale_bread": {"name": "Kuiva leipä", "price_gp": 0.001, "description": "Kova kuin kivi, mutta syötävä."},
        },
        "staff": [
            {"name": "Kiero Ratkka", "role": "Majatalonpitäjä", "race": "Human", "gender": "Male",
             "appearance": "Laiha, arpinaama, puuttuvat hampaat, hikoilee jatkuvasti",
             "personality": "Pelkuri mutta ovela. Myy tietoa halvalla.",
             "occupation": "Innkeeper", "attitude": "unfriendly",
             "stat_source": "monster:Bandit"},
        ],
        "special_features": [
            "Salainen tunneli viemäreihin (DC 15 Perception)",
            "Rotan Kolon vakioasiakkaat tietävät kaupungin alamaailman juorut",
            "Voi ostaa varastettua tavaraa 50% alennuksella (50% todennäköisyys huijaukselle)",
        ],
        "hooks": [
            "Taskuvaras vie jonkun reppun yöllä",
            "Kapakkatappelu syttyy mistä tahansa syystä",
            "Epäilyttävä tyyppi tarjoaa 'helppoa rahaa'",
        ],
    },

    "squalid_dockside": {
        "name": "Merirosvojen Lepo",
        "tier": "squalid",
        "location_type": "tavern",
        "description": (
            "Sataman rähjäisin kapakka, tuoksuu kalalle, hielle ja rommille. "
            "Seinät on vuorattu laivojen hylyistä pelastetuilla laudoilla. "
            "Täällä kokoontuvat merirosvojen jämät, salakuljettajat ja "
            "karkulaiset. Tappeluita puhkeaa lähes joka ilta."
        ),
        "atmosphere": "Merimies-tunnelma, kalanhaju, rommin roiske, voimakas melu.",
        "rooms": {
            "hammock": {"name": "Riippumatto (ruuma)", "price_gp": 0.01, "count": 8,
                "description": "Riippumatto varastohuoneessa kalasäkkien joukossa."},
        },
        "menu": {
            "grog": {"name": "Grogi", "price_gp": 0.003, "description": "Rommi sekoitettuna veteen. Merimiesstandardi."},
            "salted_fish": {"name": "Suolakala", "price_gp": 0.003, "description": "Kuivattua turskaa, kestää ikuisesti."},
            "rum_shot": {"name": "Rommishotti", "price_gp": 0.02, "description": "Polttaa kurkkua, lämmittää vatsan."},
            "seaweed_soup": {"name": "Merileväkeitto", "price_gp": 0.005, "description": "Suolaista ja tahmeaa, mutta ravitsevaa."},
        },
        "staff": [
            {"name": "Yksisilmä Marge", "role": "Majatalonpitäjä", "race": "Human", "gender": "Female",
             "appearance": "Tukeva nainen, silmälappu, ankkuri-tatuointi, kultahammas",
             "personality": "Kovaääninen ja karski. Kunnioittaa vahvuutta.",
             "occupation": "Innkeeper", "attitude": "neutral",
             "stat_source": "monster:Bandit Captain"},
        ],
        "special_features": [
            "Salakuljettajien tapauspaikka — voi löytää harvinaisia tavaroita",
            "Ilmoitustaulu merityötarjouksille ja palkkionmetsästäjille",
            "Takahuoneessa pelataan korttipilejä suurilla panoksilla",
        ],
        "hooks": [
            "Merirosvokapteeni etsii miehistöä vaaralliselle matkalle",
            "Merihirviö-huhuila kiertävät satamassa",
            "Salakuljettaja tarvitsee apua tullin ohittamisessa",
        ],
    },

    # ---- POOR TIER ----
    "poor_village_inn": {
        "name": "Kyläkapakka",
        "tier": "poor",
        "location_type": "tavern",
        "description": (
            "Pieni ja vaatimaton mutta siisti kylämajatalo päätien varrella. "
            "Paikallisten kokoontumispaikka iltaisin. Isännän vaimo keittää "
            "hyvää muhennosta ja olut on kotitekoista. Täällä kuulee kylän "
            "juorut ja maantien uutiset."
        ),
        "atmosphere": "Kodikas, savuinen, hiljainen jutustelu ja takan ritinä.",
        "rooms": {
            "shared_room": {"name": "Jaettu huone (4 sänkyä)", "price_gp": 0.04, "count": 2,
                "description": "Yksinkertainen huone neljällä olkipatjaisella sängyllä."},
            "private_room_small": {"name": "Pieni yksityishuone", "price_gp": 0.08, "count": 1,
                "description": "Pieni huone yhdellä sängyllä ja naulalla vaatteille."},
        },
        "menu": {
            "local_ale": {"name": "Kotiolut", "price_gp": 0.003, "description": "Majatalon omaa olutta, reilun maltainen."},
            "stew": {"name": "Muhennos", "price_gp": 0.01, "description": "Päivän muhennos — perunaa, juureksia ja silloin tällöin lihaa."},
            "bread_butter": {"name": "Leipää ja voita", "price_gp": 0.005, "description": "Tuoretta ruisleipää ja voita."},
            "porridge": {"name": "Puuro", "price_gp": 0.005, "description": "Täyttävä kaurapuuro aamiaiseksi."},
        },
        "staff": [
            {"name": "Eero Lehminen", "role": "Majatalonpitäjä", "race": "Human", "gender": "Male",
             "appearance": "Roteva maalaismies, punanenäinen, ystävälliset silmät",
             "personality": "Puhelias ja utelias. Tietää kaikki kylän juorut.",
             "occupation": "Innkeeper", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
            {"name": "Marjatta Lehminen", "role": "Kokki", "race": "Human", "gender": "Female",
             "appearance": "Pyöreähkö, aina jauhoinen esiliina, lämmin hymy",
             "personality": "Äidillinen ja huolehtivainen. Tuputtaa ruokaa.",
             "occupation": "Cook", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Hyvä paikallinen muhennos — +1 temp HP pitkän levon jälkeen",
            "Ilmoitustaulu kyläläisten pienille tehtäville",
            "Majatalonpitäjä tietää lähialueen tiet ja vaarat",
        ],
        "hooks": [
            "Susi on tappanut kyläläisten lampaita",
            "Matkaaja ei koskaan saapunut naapurikylästä",
            "Kylän kaivo maistuu oudolle",
        ],
    },

    # ---- MODEST TIER ----
    "modest_roadside": {
        "name": "Tienristeyksen Majatalo",
        "tier": "modest",
        "location_type": "tavern",
        "description": (
            "Vilkas majatalo kahden kauppatien risteyksessä. Kaksikerroksinen "
            "puurakennus suurella tallilla. Kauppamatkustajat, seikkailijat "
            "ja sotilaspartiot käyvät säännöllisesti. Hyvä ruoka, reilut "
            "hinnat ja turvallinen yöpaikka."
        ),
        "atmosphere": "Vilkas ja meluisa iltaisin, rauhallinen aamuisin. Tulen loimu ja naurun remakka.",
        "rooms": {
            "common_bed": {"name": "Yhteishuoneen sänky", "price_gp": 0.05, "count": 6,
                "description": "Sänky suuressa yhteishuoneessa kuuden muun matkaajan kanssa."},
            "private_room": {"name": "Yksityishuone", "price_gp": 0.1, "count": 4,
                "description": "Oma huone hyvällä sängyllä, pöydällä ja pesukannulla."},
            "double_room": {"name": "Parisänky-huone", "price_gp": 0.15, "count": 2,
                "description": "Tilava huone leveällä sängyllä kahdelle."},
        },
        "menu": {
            "house_ale": {"name": "Talon olut", "price_gp": 0.004, "description": "Raikas ja hyvin humaloitu paikallinen olut."},
            "cider": {"name": "Siideri", "price_gp": 0.004, "description": "Omenasta valmistettu siideri, raikas ja makea."},
            "wine_house": {"name": "Talon viini", "price_gp": 0.02, "description": "Tavallista punaviiniä, juotavaa."},
            "meal_hearty": {"name": "Tukeva ateria", "price_gp": 0.03,
                "description": "Paistettua kanaa tai possua, perunoita, leipää ja juustoa."},
            "soup_bread": {"name": "Keitto ja leipä", "price_gp": 0.01, "description": "Päivän keitto tuoreen leivän kera."},
            "breakfast": {"name": "Aamiainen", "price_gp": 0.02, "description": "Munat, pekoni, leipä ja kahvi."},
            "pie_slice": {"name": "Piiras", "price_gp": 0.005, "description": "Liha- tai hedelmäpiiras, tuore ja lämmin."},
        },
        "staff": [
            {"name": "Torvald Mäkinen", "role": "Majatalonpitäjä", "race": "Human", "gender": "Male",
             "appearance": "Pitkä, harteikas, viikset, nahkaesiliina",
             "personality": "Reilu ja suorapuheinen. Ei siedä häiriköitä.",
             "occupation": "Innkeeper", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
            {"name": "Liisa", "role": "Tarjoilija", "race": "Human", "gender": "Female",
             "appearance": "Nuori, ruskeat kiharat, iloinen hymy",
             "personality": "Nopea, tehokas ja flirttaileva. Muistaa vakioasiakkaat.",
             "occupation": "Barmaid", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
            {"name": "Vanha Pekka", "role": "Tallimies", "race": "Human", "gender": "Male",
             "appearance": "Vanha, kumaraisella selällä, puhuu hevosille",
             "personality": "Hiljainen ja luotettava. Rakastaa hevosia enemmän kuin ihmisiä.",
             "occupation": "Stablehand", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Ilmoitustaulu seikkailijoiden tehtäville",
            "Tallitilat 12 hevoselle (5 sp/yö)",
            "Kauppias käy kerran viikossa tuoden kaupungin tavaroita",
        ],
        "hooks": [
            "Kauppias on myöhässä eikä kuulu mitään",
            "Sotilas kertoo bandiittiongelmista tiellä",
            "Salaperäinen matkustaja maksaa kultakolikolla eikä puhu kenellekään",
        ],
    },

    "modest_town_tavern": {
        "name": "Hopeatynnyri",
        "tier": "modest",
        "location_type": "tavern",
        "description": (
            "Suosittu kaupunkikapakka torin laidalla. Tunnettu hyvästä oluestaan "
            "ja eloisasta tunnelmastaan. Bardi esiintyy useimpina iltoina. "
            "Käsityöläiset, kauppiaat ja kaupunginvartijat ovat vakioasiakkaita."
        ),
        "atmosphere": "Eloisa, musiikkia, naurua. Lämmin ja kutsuva.",
        "rooms": {
            "shared_room": {"name": "Jaettu huone", "price_gp": 0.05, "count": 3,
                "description": "Yhteishuone kolmella sängyllä, siisti ja lämmin."},
            "private_room": {"name": "Yksityishuone", "price_gp": 0.1, "count": 3,
                "description": "Mukava yksityishuone pöytineen ja pesukannulla."},
        },
        "menu": {
            "silver_ale": {"name": "Hopeaolut (talon erikoisuus)", "price_gp": 0.005,
                "description": "Majatalon oma resepti — kirpeä, hieman hopean värinen olut."},
            "roast_dinner": {"name": "Paistiateria", "price_gp": 0.04,
                "description": "Paistettua lihaa, kasviksia ja tuoretta leipää."},
            "cheese_platter": {"name": "Juustolautanen", "price_gp": 0.02,
                "description": "Valikoima paikallisia juustoja hunajan ja pähkinöiden kera."},
        },
        "staff": [
            {"name": "Helmi Hopeinen", "role": "Majatalonpitäjä", "race": "Halfling", "gender": "Female",
             "appearance": "Pieni, pyöreä, aina hymyilevä, hopeiset hiukset",
             "personality": "Sydämellinen ja vieraanvarainen. Muistaa jokaisen nimen.",
             "occupation": "Innkeeper", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
            {"name": "Melodia", "role": "Bardi", "race": "Half-Elf", "gender": "Female",
             "appearance": "Pitkä, tummat kiharat, soittaa luuttua",
             "personality": "Taiteellinen ja romanttinen. Kerää tarinoita matkoilta.",
             "occupation": "Bard", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Bardi esiintyy illailla — tietää vanhoja tarinoita ja legendoja",
            "Ilmoitustaulu seikkailijoiden tehtäville",
            "Takahuone yksityisille tapaamisille (1 gp/tunti)",
        ],
        "hooks": [
            "Bardi kertoo tarinan läheisestä luolasta jossa asuu 'jotain'",
            "Kauppias tarjoaa työtä: kuljeta paketti naapurikaupunkiin",
            "Kaupunginvartija varoittaa oudoista tapahtumista öisin",
        ],
    },

    # ---- COMFORTABLE TIER ----
    "comfortable_merchant_inn": {
        "name": "Kultahirvi",
        "tier": "comfortable",
        "location_type": "tavern",
        "description": (
            "Arvostettu majatalo kauppiaiden ja varakkaiden matkaajien suosiossa. "
            "Kolmikerroksinen kivirunkoinen rakennus kauniilla puuleikkauksilla. "
            "Tunnettu erinomaisesta keittiöstään ja laajasta viinivalikoimastaan. "
            "Yöpyminen täällä on merkki hyvästä mausta."
        ),
        "atmosphere": "Tyylikäs mutta rento. Kynttilänvalo, hiljaiset keskustelut, hyvää musiikkia.",
        "rooms": {
            "standard_room": {"name": "Vakiohuone", "price_gp": 0.5, "count": 6,
                "description": "Tilava huone hyvällä sängyllä, kirjoituspöydällä ja pesunurkkauksella."},
            "deluxe_room": {"name": "Ylellinen huone", "price_gp": 1.0, "count": 3,
                "description": "Suuri huone takan kera, isolla sängyllä ja kylpyammella."},
            "suite": {"name": "Sviitti", "price_gp": 2.0, "count": 1,
                "description": "Kahden huoneen kokonaisuus olohuoneella ja makuuhuoneella."},
        },
        "menu": {
            "golden_stag_ale": {"name": "Kultahirvi-olut", "price_gp": 0.008,
                "description": "Talon panimolla valmistettu lager, kullanvärinen ja sileä."},
            "wine_selection": {"name": "Viini (valikoima)", "price_gp": 0.1,
                "description": "Valikoima alueen parhaita viinejä — kysy viinilistaa."},
            "roast_venison": {"name": "Peuranpaisti", "price_gp": 0.08,
                "description": "Hitaasti paistettu peuranliha yrttikastikkeella ja juureksilla."},
            "salmon_grilled": {"name": "Grillattu lohi", "price_gp": 0.06,
                "description": "Tuoretta lohta sitruunalla ja yrteillä grillattuna."},
            "apple_pie": {"name": "Omenapiirakka", "price_gp": 0.02,
                "description": "Kotitekoinen omenapiirakka vaniljakastikkeella."},
            "fine_breakfast": {"name": "Aamiaisbuffet", "price_gp": 0.05,
                "description": "Munat, pekoni, tuore leipä, juustot, hedelmät ja tee."},
        },
        "staff": [
            {"name": "Alaric von Stein", "role": "Majatalonpitäjä", "race": "Human", "gender": "Male",
             "appearance": "Siististi pukeutunut, harmaantuva ohimolta, tarkka katse",
             "personality": "Ammattitaitoinen ja kohtelias. Arvostaa hyviä tapoja ja rahaa.",
             "occupation": "Innkeeper", "attitude": "neutral",
             "stat_source": "monster:Noble"},
            {"name": "Raoul", "role": "Kokki", "race": "Halfling", "gender": "Male",
             "appearance": "Pieni, pyöreä, punaposket, taitavat kädet",
             "personality": "Intohimoinen ruoasta. Loukkaantuu kritiikistä.",
             "occupation": "Chef", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
            {"name": "Bran Jyrkinen", "role": "Portsari", "race": "Half-Orc", "gender": "Male",
             "appearance": "Valtava, ystävälliset silmät, käsivartta paksumpi kaula",
             "personality": "Kiltti jättiläinen, mutta ei kannata provoisoida.",
             "occupation": "Bouncer", "attitude": "neutral",
             "stat_source": "monster:Guard"},
            {"name": "Elianne", "role": "Tarjoilija", "race": "Elf", "gender": "Female",
             "appearance": "Siro, pitkät vaaleat hiukset, elegantti liikkuminen",
             "personality": "Hieno ja tarkka. Muistaa jokaisen tilauksen.",
             "occupation": "Server", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Erinomainen keittiö — talon erikoisruoat antavat +2 temp HP pitkän levon jälkeen",
            "Viiniluettelo 30+ viinillä eri alueilta",
            "Yksityinen kokoushuone kauppiaille (2 gp/päivä)",
            "Tallitilat 20 hevoselle (5 sp/yö, sisältää ruokinnan)",
            "Pesupalvelu vaatteille (1 sp)",
        ],
        "hooks": [
            "Varakas kauppias tarjoaa työstä, mutta ei kerro kaikkea",
            "Toinen seikkailijaryhmä majoittuu samaan aikaan — kilpailu vai liittolaisuus?",
            "Hovimestari mainitsee huhuja vanhoista raunioista lähiseudulla",
        ],
    },

    # ---- WEALTHY TIER ----
    "wealthy_noble_inn": {
        "name": "Kuninkaanlähde",
        "tier": "wealthy",
        "location_type": "tavern",
        "description": (
            "Ylellinen majatalo kaupungin parhaalla paikalla. Marmoriportaikko, "
            "kristallikruunut ja silkkiverhot. Palvelu on impeccable ja ruoka "
            "vertaansa vailla. Aateliston, diplomaattien ja rikkaiden kauppiaiden "
            "suosima. Sisäänpääsy vain kutsutuille tai erittäin varakkaille."
        ),
        "atmosphere": "Ylellinen, hiljainen eleganssi. Kynttilänvalo, harpunsoitto, silkin kahina.",
        "rooms": {
            "luxury_room": {"name": "Luksushuone", "price_gp": 2.0, "count": 8,
                "description": "Suuri huone silkkivuoteella, takalla, kylpyammella ja palvelijalla."},
            "noble_suite": {"name": "Aatelissviitti", "price_gp": 5.0, "count": 3,
                "description": "Kolmen huoneen kokonaisuus: olohuone, makuuhuone ja työhuone. "
                    "Henkilökohtainen palvelija ja maaginen lukko."},
            "royal_suite": {"name": "Kuninkaallinen sviitti", "price_gp": 10.0, "count": 1,
                "description": "Palatsimainen viiden huoneen sviitti omalla parvekkeella, "
                    "kylpylällä ja palvelijoiden kamarilla. Kultakoristeet ja silkkiverhot."},
        },
        "menu": {
            "champagne": {"name": "Kuohuviini", "price_gp": 2.0,
                "description": "Tuontimaasta tuotua kuohuviiniä kristallilaseissa."},
            "elven_wine": {"name": "Haltiaviini", "price_gp": 5.0,
                "description": "Harvinaista vuosisataista haltiaviiniä."},
            "seven_course": {"name": "Seitsemän ruokalajia", "price_gp": 2.0,
                "description": "Monipuolinen gourmet-illallinen huippukokin käsissä: "
                    "alkupalat, keitot, kala, liha, juusto, jälkiruoka ja petit fours."},
            "exotic_fruit": {"name": "Eksoottinen hedelmälautanen", "price_gp": 1.0,
                "description": "Trooppisia hedelmiä kaukaisista maista, maagisesti tuoreina."},
            "dwarven_aged_whisky": {"name": "Kääpiöiden vuosikertaviski", "price_gp": 3.0,
                "description": "100 vuotta tammitynnyrissä kypsytetty viski. Sileä ja savuinen."},
        },
        "staff": [
            {"name": "Lady Cassandra Vane", "role": "Omistaja/Emäntä", "race": "Human", "gender": "Female",
             "appearance": "Elegant, hopeiset hiukset kampauksen, kalliit korut",
             "personality": "Jäätävän kohtelias. Tuntee kaikki tärkeät ihmiset.",
             "occupation": "Owner", "attitude": "neutral",
             "stat_source": "monster:Noble"},
            {"name": "Marcel", "role": "Hovimestari", "race": "Human", "gender": "Male",
             "appearance": "Pitkä, laiha, moitteeton pukeutuminen, nenä pystyssä",
             "personality": "Ylimielinen mutta tehokas. Muistaa jokaisen vieraan.",
             "occupation": "Butler", "attitude": "unfriendly",
             "stat_source": "monster:Noble"},
            {"name": "Kael Aurinkokivi", "role": "Kokki", "race": "High Elf", "gender": "Male",
             "appearance": "Pitkä, hoikka, kultaiset silmät, aina puhdas kokinhattu",
             "personality": "Perfektionisti joka ei siedä huonoja raaka-aineita.",
             "occupation": "Master Chef", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
            {"name": "Gareth & Mira", "role": "Henkivartijat", "race": "Human", "gender": "Mixed",
             "appearance": "Kaksi vahvaa vartijaa täydessä varustuksessa",
             "personality": "Ammattimaiset ja vähäpuheiset.",
             "occupation": "Guards", "attitude": "neutral",
             "stat_source": "monster:Guard"},
        ],
        "special_features": [
            "Maagisesti lämmitetty kylpylä joka parantaa exhaustion-tason pitkällä levolla",
            "Viiniluettelo 100+ viinillä ympäri maailmaa",
            "Yksityiset juhlahuoneet 10-50 hengelle",
            "Henkilökohtainen palvelija jokaiselle vieraalle",
            "Maaginen turvallisuusjärjestelmä (Alarm spell kaikissa huoneissa)",
            "Herbalistinen spa ja hierontapalvelut",
        ],
        "hooks": [
            "Kreivi järjestää gaalaillallisen johon seikkailijat kutsutaan",
            "Jalokivi varastetaan vieraan huoneesta — kuka on varas?",
            "Diplomaattiset neuvottelut viereisessä huoneessa — salakuuntelu mahdollista",
        ],
    },

    # ---- ARISTOCRATIC TIER ----
    "aristocratic_palace_guest": {
        "name": "Aurinkokuningas Palatsi (vierasrakennus)",
        "tier": "aristocratic",
        "location_type": "tavern",
        "description": (
            "Kuninkaallisen palatsin vierasrakennus, varattu kuninkaan henkilökohtaisille "
            "vieraille ja korkeimmille diplomaateille. Jokainen huone on taideteos — "
            "freskot katossa, marmorialattiat, kultakoristeet ja maaginen valaistus. "
            "Palvelijoita on enemmän kuin vieraita ja turvallisuus on ehdoton."
        ),
        "atmosphere": "Ylenpalttinen ylellisyys. Hiljaisuus, parfyymin tuoksu, maaginen valo.",
        "rooms": {
            "ambassador_suite": {"name": "Lähettilään sviitti", "price_gp": 20.0, "count": 5,
                "description": "Viiden huoneen kokonaisuus omalla palvelijakunnalla, "
                    "kylpylällä ja turvamiehillä. Kaikki kalusteet ovat antiikkia."},
            "royal_apartment": {"name": "Kuninkaallinen asunto", "price_gp": 50.0, "count": 2,
                "description": "Palatsimainen kymmenen huoneen kokonaisuus omalla puutarhalla, "
                    "kirjastolla ja ruokasalilla. Maaginen suojaus kaikessa."},
        },
        "menu": {
            "royal_feast": {"name": "Kuninkaallinen juhla-ateria", "price_gp": 10.0,
                "description": "Kymmenen ruokalajin illallinen kuninkaan kokeilta: "
                    "tryffeleitä, kultaista kaviaaria, draakoon lihaa ja taivaallista jälkiruokaa."},
            "ambrosia_wine": {"name": "Ambrosia-viini", "price_gp": 25.0,
                "description": "Maagisesti valmistettu viini joka palauttaa 1d4 HP juodessa."},
        },
        "staff": [
            {"name": "Lord Chamberlain Aldric", "role": "Hovimestari", "race": "Human", "gender": "Male",
             "appearance": "Vanha, arvokas, kultainen ketju, kuninkaallinen sinetti",
             "personality": "Äärimmäisen muodollinen ja perinteisiin uskollinen.",
             "occupation": "Chamberlain", "attitude": "neutral",
             "stat_source": "monster:Noble"},
        ],
        "special_features": [
            "Täydellinen turvallisuus — maaginen ja fyysinen",
            "Pääsy kuninkaalliseen kirjastoon (harvinaisia tekstejä)",
            "Henkilökohtainen kokki, palvelija, turvahenkilö jokaiselle",
            "Maaginen viestintäjärjestelmä (Sending stones)",
            "Parantaja päivystää vuorokauden ympäri",
        ],
        "hooks": [
            "Kuningas pyytää yksityistä palvelusta",
            "Hovijuonittelu — kuka yrittää myrkyttää lähettilään?",
            "Salainen käytävä löytyy sviitistä",
        ],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_inn_template(template_key: str) -> Optional[dict]:
    """Get an inn template by key."""
    return INN_TEMPLATES.get(template_key)


def get_inn_templates_by_tier(tier: str) -> List[dict]:
    """Get all inn templates for a given quality tier."""
    return [t for t in INN_TEMPLATES.values() if t["tier"] == tier]


def get_all_inn_tiers() -> List[str]:
    """Get all available quality tiers."""
    return ["squalid", "poor", "modest", "comfortable", "wealthy", "aristocratic"]


def get_inn_template_names() -> Dict[str, str]:
    """Get dict of template_key -> display name."""
    return {k: v["name"] for k, v in INN_TEMPLATES.items()}


def apply_inn_template(world, parent_location_id: str, template: dict,
                       custom_name: str = "") -> dict:
    """
    Apply an inn template to the world, creating location and NPCs.

    Returns dict with created IDs: {"location_id": ..., "npc_ids": [...]}
    """
    from data.world import add_location, add_npc

    name = custom_name or template["name"]
    loc = add_location(
        world, name,
        location_type=template.get("location_type", "tavern"),
        parent_id=parent_location_id,
        description=template["description"],
    )
    loc.tags = [template["tier"], "inn", "tavern"]
    if template.get("atmosphere"):
        loc.notes = f"Tunnelma: {template['atmosphere']}"

    # Add special features and hooks to notes
    notes_parts = [loc.notes] if loc.notes else []
    if template.get("special_features"):
        notes_parts.append("\nErikoisuudet:")
        for feat in template["special_features"]:
            notes_parts.append(f"  - {feat}")
    if template.get("hooks"):
        notes_parts.append("\nSeikkailukoukut:")
        for hook in template["hooks"]:
            notes_parts.append(f"  - {hook}")
    loc.notes = "\n".join(notes_parts)

    # Create staff NPCs
    created_npcs = []
    for staff in template.get("staff", []):
        npc = add_npc(
            world, staff["name"],
            location_id=loc.id,
            race=staff.get("race", "Human"),
            gender=staff.get("gender", ""),
            appearance=staff.get("appearance", ""),
            personality=staff.get("personality", ""),
            occupation=staff.get("occupation", staff.get("role", "")),
            attitude=staff.get("attitude", "neutral"),
            stat_source=staff.get("stat_source", ""),
        )
        npc.tags = [template["tier"], staff.get("role", "staff")]
        created_npcs.append(npc.id)

        # Make first NPC the shopkeeper with the inn's menu
        if staff["role"] in ("Majatalonpitäjä", "Omistaja/Emäntä", "Hovimestari"):
            npc.is_shopkeeper = True
            npc.shop_name = name
            npc.shop_type = "tavern"
            # Add menu items as shop items
            from data.world import ShopItem
            for item_key, item_data in template.get("menu", {}).items():
                npc.shop_items.append(ShopItem(
                    item_name=item_data["name"],
                    base_price_gp=item_data["price_gp"],
                    current_price_gp=item_data["price_gp"],
                    quantity=-1,
                    notes=item_data.get("description", ""),
                ))
            # Add room prices as shop items
            for room_key, room_data in template.get("rooms", {}).items():
                npc.shop_items.append(ShopItem(
                    item_name=f"{room_data['name']} ({room_data.get('count', '?')} kpl)",
                    base_price_gp=room_data["price_gp"],
                    current_price_gp=room_data["price_gp"],
                    quantity=room_data.get("count", -1),
                    notes=room_data.get("description", ""),
                ))

    return {"location_id": loc.id, "npc_ids": created_npcs}
