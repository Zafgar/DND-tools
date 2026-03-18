"""
D&D 5e Services, Lodging, Food & Drink Catalog — PHB p.157-159, DMG references.

Comprehensive price lists for everything adventurers might need:
- Lodging (inn rooms by quality tier)
- Food & drink (meals, ale, wine, spirits)
- Hirelings (skilled & unskilled labor)
- Spellcasting services
- Stabling & animal care
- Messenger & courier services
- Entertainment & bathhouse
- Property purchase/rent (houses, castles, ships)

All prices in gold pieces (gp). 1 gp = 10 sp = 100 cp.
"""
from typing import Dict, List


# ============================================================================
# LIFESTYLE EXPENSES (PHB p.157) — per day
# ============================================================================

LIFESTYLE_EXPENSES = {
    "wretched": {
        "cost_per_day_gp": 0.0,
        "description": "Elätte ulkona suojattomana, hylätty yhteiskunnasta. "
            "Asutte slummeissa, avoimissa pelloilla tai katujen varrella. "
            "Olette jatkuvasti alttiina luonnon vaaroille ja väkivallalle.",
        "quality": 0,
    },
    "squalid": {
        "cost_per_day_gp": 0.01,  # 1 cp
        "description": "Asutte vuotavassa vajassa, maatilassa tai hylätyssä talossa. "
            "Hyönteiset, kosteus ja hajut ympäröivät teitä. "
            "Altistutte sairauksille ja rikollisille. "
            "Yöpyminen: lattialla tai olkipatjalla yhteishuoneessa.",
        "quality": 1,
    },
    "poor": {
        "cost_per_day_gp": 0.02,  # 2 sp
        "description": "Vaatimaton mutta suojaisa elämäntapa. Asutte vuokrahuoneessa "
            "halpamajatalossa tai yhteismajoituksessa. Ruoka on yksinkertaista — "
            "leipää, puuroa ja satunnaista lihaa. Vaatteenne ovat kuluneet.",
        "quality": 2,
    },
    "modest": {
        "cost_per_day_gp": 0.1,  # 1 gp
        "description": "Kunnollinen elämäntapa tavalliselle kansalaiselle. "
            "Oma huone majatalossa tai pieni vuokra-asunto. "
            "Syötte yksinkertaisia mutta ravitsevia aterioita. "
            "Vaatteenne ovat siistit ja kunnossa.",
        "quality": 3,
    },
    "comfortable": {
        "cost_per_day_gp": 0.2,  # 2 gp
        "description": "Mukava elämä ilman huolia. Oma huone hyvässä majatalossa "
            "tai pieni talo. Syötte hyvin — lihaa, juustoa, viiniä. "
            "Vaatteenne ovat laadukkaat. Olette tervetullut useimpiin piireihin.",
        "quality": 4,
    },
    "wealthy": {
        "cost_per_day_gp": 0.4,  # 4 gp
        "description": "Ylellinen elämäntapa, jossa palvelijoita ja laadukasta ruokaa. "
            "Asutte hienossa talossa tai parhaassa sviitissä. "
            "Syötte gourmet-aterioita ja juotte hienoa viiniä. "
            "Olette tervetullut ylhäisön piireihin.",
        "quality": 5,
    },
    "aristocratic": {
        "cost_per_day_gp": 1.0,  # 10+ gp
        "description": "Elätteen kuten kuninkaallinen. Asutte kartanossa tai palatsin "
            "vierashuoneissa. Henkilökohtaiset palvelijat, kokit ja vartijat. "
            "Pukeudutaan silkkiin ja jalokiviin. Vaikutusvaltaa ja yhteyksiä.",
        "quality": 6,
    },
}


# ============================================================================
# LODGING — INN ROOM PRICES (PHB p.158)
# ============================================================================

INN_ROOM_PRICES = {
    "common_room_floor": {
        "name": "Yhteishuone (lattia)",
        "cost_per_night_gp": 0.007,  # 7 cp
        "description": "Nukkumapaikka yhteishuoneen lattialla olkipatjalla tai omalla "
            "makuupussilla. Melua, hajuja ja vieraita ihmisiä ympärillä. "
            "Lämpöä takasta mutta ei yksityisyyttä.",
        "quality": "squalid",
        "amenities": ["Takan lämpö", "Katto pään päällä"],
    },
    "common_room_bed": {
        "name": "Yhteishuone (sänky)",
        "cost_per_night_gp": 0.05,  # 5 sp
        "description": "Yksinkertainen sänky suuressa yhteishuoneessa 4-20 muun matkustajan "
            "kanssa. Olkipatja, ohut peitto. Lukittava arkku tavaroille saatavilla "
            "pientä lisämaksua vastaan.",
        "quality": "poor",
        "amenities": ["Sänky", "Peitto", "Lukittava arkku (1 sp/yö)"],
    },
    "private_room_basic": {
        "name": "Yksityishuone (yksinkertainen)",
        "cost_per_night_gp": 0.08,  # 8 sp
        "description": "Pieni yksityishuone yhdelle tai kahdelle hengelle. "
            "Kapea sänky, pieni pöytä, koukku vaatteille. Ohut puuovi "
            "tarjoaa edes jonkin verran yksityisyyttä.",
        "quality": "modest",
        "amenities": ["Oma huone", "Sänky", "Lukko ovessa"],
    },
    "private_room_comfortable": {
        "name": "Yksityishuone (mukava)",
        "cost_per_night_gp": 0.5,  # 5 sp -> actually 5 gp? no, PHB says 5sp-2gp range. Let's use 5sp
        "description": "Tilava yksityishuone hyvällä sängyllä, pöydällä, tuolilla ja "
            "pesukannulla. Puhtaat lakanat, paksu peitto. Ikkuna pihalle tai "
            "kadulle. Hyvä yöuni taattu.",
        "quality": "comfortable",
        "amenities": ["Tilava huone", "Hyvä sänky", "Pesukannu", "Puhtaat lakanat", "Ikkuna"],
    },
    "suite": {
        "name": "Sviitti (ylellinen)",
        "cost_per_night_gp": 2.0,
        "description": "Ylellinen huoneisto kahdella tai useammalla huoneella. "
            "Suuri sänky höyhenpatjalla, takka, kylpyamme, kirjoituspöytä. "
            "Palvelija saatavilla vuorokauden ympäri. Hienot verhot ja matot.",
        "quality": "wealthy",
        "amenities": ["Useita huoneita", "Höyhenpatja", "Takka", "Kylpyamme",
                      "Kirjoituspöytä", "Palvelija"],
    },
    "royal_suite": {
        "name": "Kuninkaallinen sviitti",
        "cost_per_night_gp": 8.0,
        "description": "Paras mitä majatalolla on tarjota. Usean huoneen kokonaisuus "
            "mahonkikalusteilla, silkkivuodevaatteilla ja kristallikruunuilla. "
            "Henkilökohtainen kokki, palvelija ja vartija. Maaginen lukko ovessa.",
        "quality": "aristocratic",
        "amenities": ["Luksus-sviitti", "Silkkivuode", "Kristallikruunu", "Oma kokki",
                      "Oma palvelija", "Oma vartija", "Maaginen lukko"],
    },
}


# ============================================================================
# FOOD & DRINK PRICES (PHB p.158)
# ============================================================================

FOOD_AND_DRINK = {
    # -- Meals --
    "bread_chunk": {
        "name": "Leipäpala",
        "cost_gp": 0.002,  # 2 cp
        "category": "food",
        "description": "Karkea ruisleipäpala, tavallisen köyhän perusruokaa.",
    },
    "cheese_chunk": {
        "name": "Juustopalat",
        "cost_gp": 0.001,  # 1 cp
        "category": "food",
        "description": "Pala kovaa kypsytettyä juustoa, säilyy hyvin matkoilla.",
    },
    "meal_poor": {
        "name": "Köyhän ateria",
        "cost_gp": 0.006,  # 6 cp
        "category": "food",
        "description": "Puuroa tai ohutta keittoa. Kenties hieman leipää ja sipulia. "
            "Täyttää vatsan mutta ei miellytä makuhermoja.",
    },
    "meal_modest": {
        "name": "Vaatimaton ateria",
        "cost_gp": 0.03,  # 3 sp
        "category": "food",
        "description": "Muhennosta lihan ja juuresten kanssa, tuoretta leipää ja voita. "
            "Yksinkertaista mutta ravitsevaa ruokaa.",
    },
    "meal_comfortable": {
        "name": "Mukava ateria",
        "cost_gp": 0.05,  # 5 sp
        "category": "food",
        "description": "Paistettua lihaa tai kalaa, vihanneksia, tuoretta leipää, "
            "juustoa ja hedelmiä. Mahdollisesti jälkiruoka.",
    },
    "meal_wealthy": {
        "name": "Ylellinen ateria",
        "cost_gp": 0.08,  # 8 sp
        "category": "food",
        "description": "Useita ruokalajeja: alkupalat, pääruoka (hirvenliha, fasaani, "
            "tuore lohi), jälkiruoka ja juustolautanen. Mausteilla höystetty.",
    },
    "banquet": {
        "name": "Juhla-ateria (per henkilö)",
        "cost_gp": 1.0,
        "category": "food",
        "description": "Seitsemän ruokalajin illallinen parhaista raaka-aineista. "
            "Paahdettu villisika, tryffeleitä, eksoottisia hedelmiä, "
            "harvinaisia mausteita. Tarjoilu ja musiikki kuuluvat hintaan.",
    },
    "rations_1day": {
        "name": "Matkamuona (1 päivä)",
        "cost_gp": 0.05,  # 5 sp
        "category": "food",
        "description": "Kuivattua lihaa, kovaa leipää, pähkinöitä ja kuivattuja hedelmiä. "
            "Pitkään säilyvää ja helppo kantaa mukana. Paino 2 lb.",
    },

    # -- Drinks --
    "water_pitcher": {
        "name": "Vesikannu",
        "cost_gp": 0.0,  # free
        "category": "drink",
        "description": "Kannu puhdasta vettä. Useimmissa majataloissa ilmaista.",
    },
    "ale_mug": {
        "name": "Tuoppi olutta",
        "cost_gp": 0.004,  # 4 cp
        "category": "drink",
        "description": "Tuoppi paikallista olutta. Tummaa, vaaleaa tai ruskeaa — "
            "riippuu paikallisesta panijasta. Perus janojuoma.",
    },
    "ale_gallon": {
        "name": "Gallona olutta",
        "cost_gp": 0.02,  # 2 sp
        "category": "drink",
        "description": "Gallona (n. 4 litraa) olutta. Riittää pienelle seurueelle "
            "tai yhdelle janoiselle kääpiölle.",
    },
    "mead": {
        "name": "Sima/Mead",
        "cost_gp": 0.05,  # 5 sp
        "category": "drink",
        "description": "Makeaa hunajajuomaa, perinteinen pohjolan juhla juoma. "
            "Alkoholin määrä vaihtelee.",
    },
    "wine_common": {
        "name": "Viini (tavallinen)",
        "cost_gp": 0.02,  # 2 sp
        "category": "drink",
        "description": "Tavallista punaista tai valkoista viiniä paikalliselta viinitilalta. "
            "Hapanta mutta juotavaa.",
    },
    "wine_fine": {
        "name": "Viini (hieno)",
        "cost_gp": 1.0,
        "category": "drink",
        "description": "Laadukas viini tunnetulta viinitilalta. Täyteläinen maku, "
            "pitkä jälkimaku. Tarjoillaan kristalilaseissa.",
    },
    "wine_elven": {
        "name": "Haltiaviini",
        "cost_gp": 5.0,
        "category": "drink",
        "description": "Harvinaista haltijoiden valmistamaa viiniä, kypsytetty vuosisatoja. "
            "Kultainen väri, ylimaallinen maku. Sanotaan tuovan hyviä unia.",
    },
    "spirits_common": {
        "name": "Väkijuoma (tavallinen)",
        "cost_gp": 0.05,  # 5 sp
        "category": "drink",
        "description": "Viski, rommi, vodka tai vastaava paikallinen väkijuoma. "
            "Polttaa kurkkua mutta lämmittää sisältä.",
    },
    "spirits_fine": {
        "name": "Väkijuoma (hieno)",
        "cost_gp": 1.0,
        "category": "drink",
        "description": "Premium-luokan tislattua juomaa. Kääpiöiden tynnyriviski, "
            "merirosvon kultainen rommi tai haltijoiden hedelmälikööri.",
    },
    "dwarven_stout": {
        "name": "Kääpiöstout",
        "cost_gp": 0.1,  # 1 sp extra
        "category": "drink",
        "description": "Kääpiöiden valmistama erittäin vahva ja tumma olut. "
            "Paksu, maltainen ja niin vahva että vain kääpiöt juovat sitä "
            "ilman seurauksia. Con save DC 10 tai humalassa.",
    },
}


# ============================================================================
# HIRELING & SERVICE PRICES (PHB p.159, DMG p.127-129)
# ============================================================================

HIRELINGS = {
    # -- Unskilled Labor --
    "laborer": {
        "name": "Työmies (taitamaton)",
        "cost_per_day_gp": 0.02,  # 2 sp/day
        "description": "Kantaja, kaivaja, siivooja tai muu yksinkertainen työ. "
            "Ei osaa taistella eikä käytä erikoistaitoja.",
        "category": "unskilled",
        "stats": "Commoner",
    },
    "torchbearer": {
        "name": "Soihdunkantaja",
        "cost_per_day_gp": 0.02,
        "description": "Kantaa soihtua, lyhtyä tai muuta valoa seikkailun aikana. "
            "Voi kantaa pieniä tavaroita. Pakenee vaaraa.",
        "category": "unskilled",
        "stats": "Commoner",
    },
    "porter": {
        "name": "Kantaja",
        "cost_per_day_gp": 0.02,
        "description": "Kantaa tavaroita, aarteita ja varusteita. Voi kantaa 150 lb. "
            "Ei taistele. Hidastuu raskaassa maastossa.",
        "category": "unskilled",
        "stats": "Commoner",
    },
    "cook": {
        "name": "Kokki",
        "cost_per_day_gp": 0.03,  # 3 sp/day
        "description": "Valmistaa aterioita seurueelle matkoilla ja leirissä. "
            "Hyvä kokki voi parantaa moraalia ja nopeuttaa toipumista.",
        "category": "unskilled",
        "stats": "Commoner",
    },

    # -- Skilled Labor --
    "mercenary": {
        "name": "Palkkasoturi",
        "cost_per_day_gp": 2.0,
        "description": "Koulutettu taistelija joka taistelee rahasta. Tyypillisesti "
            "Guard- tai Veteran-tason taistelija. Vaatii palkkansa etukäteen "
            "ja voi paeta jos tilanne näyttää toivottomalta.",
        "category": "skilled",
        "stats": "Guard",
    },
    "veteran_mercenary": {
        "name": "Veteraanipalkkasoturi",
        "cost_per_day_gp": 5.0,
        "description": "Kokenut taistelija, useita sotia ja seikkailuja takanaan. "
            "Luotettavampi kuin tavallinen palkkasoturi. "
            "Veteran-tason statsit.",
        "category": "skilled",
        "stats": "Veteran",
    },
    "guide": {
        "name": "Opas",
        "cost_per_day_gp": 2.0,
        "description": "Tuntee alueen maastot, reitit ja vaarat. "
            "Voi auttaa navigoinnissa (advantage Survival-chekkiin). "
            "Tietää paikallisia tarinoita ja salaisuuksia.",
        "category": "skilled",
        "stats": "Scout",
    },
    "translator": {
        "name": "Tulkki",
        "cost_per_day_gp": 2.0,
        "description": "Osaa 2-5 kieltä ja voi toimia tulkkina neuvotteluissa. "
            "Hyödyllinen vieraissa kulttuureissa ja diplomatissa.",
        "category": "skilled",
        "stats": "Commoner",
    },
    "healer": {
        "name": "Parantaja",
        "cost_per_day_gp": 3.0,
        "description": "Ammattimainen parantaja joka osaa käyttää healer's kitiä. "
            "Voi stabiloida kuolevan hahmon ja hoitaa sairauksia. "
            "Ei käytä magiaa.",
        "category": "skilled",
        "stats": "Commoner",
    },
    "sage_researcher": {
        "name": "Oppinut/Tutkija",
        "cost_per_day_gp": 5.0,
        "description": "Tutkii tietoa kirjastoista, arkistoista ja muinaisista teksteistä. "
            "Voi tunnistaa maagisia esineitä (Arcana), historiallisia artefakteja "
            "(History) tai outoja olentoja (Nature/Religion).",
        "category": "skilled",
        "stats": "Commoner",
    },
    "blacksmith": {
        "name": "Seppä",
        "cost_per_day_gp": 3.0,
        "description": "Voi korjata aseita ja haarniskoja, valmistaa yksinkertaisia "
            "metalliesineitä. Tarvitsee pajaa ja materiaaleja.",
        "category": "skilled",
        "stats": "Commoner",
    },
    "architect": {
        "name": "Arkkitehti",
        "cost_per_day_gp": 5.0,
        "description": "Suunnittelee ja valvoo rakennusprojekteja: tornit, linnat, "
            "sillat ja muut rakennelmat. Tarvitaan isommissa projekteissa.",
        "category": "skilled",
        "stats": "Commoner",
    },
    "spy": {
        "name": "Vakooja",
        "cost_per_day_gp": 10.0,
        "description": "Kerää tietoa kohteista salaa. Osaa varjostaa, kuunnella "
            "ja murtautua. Epäluotettava — voi myydä tietoa molemmille puolille.",
        "category": "skilled",
        "stats": "Spy",
    },
    "assassin": {
        "name": "Salamurhaaja",
        "cost_per_day_gp": 50.0,
        "description": "Ammattimainen tappaja joka eliminoi kohteita hiljaisesti. "
            "Erittäin kallis mutta tehokas. Vaarallinen palkata — "
            "voi kääntyä tilaajaa vastaan.",
        "category": "skilled",
        "stats": "Assassin",
    },
}


# ============================================================================
# SPELLCASTING SERVICES (PHB p.159, DMG p.129)
# ============================================================================

SPELLCASTING_SERVICES = {
    "cure_wounds": {
        "name": "Cure Wounds",
        "spell_level": 1,
        "cost_gp": 10.0,
        "description": "Parantaa 1d8+3 HP. Saatavilla useimmissa temppeleissä ja "
            "parantajien luona. Vaatii yleensä pienen lahjoituksen.",
        "caster": "Pappi/Temppeli",
    },
    "lesser_restoration": {
        "name": "Lesser Restoration",
        "spell_level": 2,
        "cost_gp": 40.0,
        "description": "Poistaa yhden sairauden tai tilan: sokeuden, kuurouden, "
            "halvaantumisen tai myrkytyksen. Yleinen temppelien palvelu.",
        "caster": "Pappi/Temppeli",
    },
    "remove_curse": {
        "name": "Remove Curse",
        "spell_level": 3,
        "cost_gp": 90.0,
        "description": "Poistaa kirouksen kohteesta tai esineestä. "
            "Vahvemmat kiroukset voivat vaatia korkeamman tason loitsijan.",
        "caster": "Pappi/Temppeli",
    },
    "greater_restoration": {
        "name": "Greater Restoration",
        "spell_level": 5,
        "cost_gp": 350.0,
        "description": "Poistaa yhden tason exhaustionin, charmin, petrification-tilan, "
            "curse-tilan, ability score -vähennyksen tai HP maximum -vähennyksen. "
            "Vaatii 100 gp materiaalikomponentin.",
        "caster": "Korkea-pappi/Katedraali",
    },
    "raise_dead": {
        "name": "Raise Dead",
        "spell_level": 5,
        "cost_gp": 500.0,
        "description": "Herättää henkiin olennon joka on kuollut enintään 10 päivää sitten. "
            "Vaatii 500 gp timanttia. Ei toimi jos ruumis on tuhoutunut. "
            "Kohde saa -4 penalty kaikkiin d20-heittoihin 4 päiväksi.",
        "caster": "Korkea-pappi/Katedraali",
    },
    "resurrection": {
        "name": "Resurrection",
        "spell_level": 7,
        "cost_gp": 3000.0,
        "description": "Herättää olennon joka on kuollut enintään 100 vuotta sitten. "
            "Vaatii 1000 gp timantin. Luo uuden ruumiin jos vanha on tuhoutunut. "
            "Erittäin harvinainen palvelu — vain suurissa kaupungeissa.",
        "caster": "Arkkipappi/Pyhäkkö",
    },
    "true_resurrection": {
        "name": "True Resurrection",
        "spell_level": 9,
        "cost_gp": 25000.0,
        "description": "Herättää minkä tahansa olennon joka on kuollut enintään 200 vuotta "
            "sitten. Vaatii 25000 gp timantin. Luo täydellisen ruumiin. "
            "Äärettömän harvinainen — kenties vain yksi loitsija mantereella.",
        "caster": "Arkkimaagi/Legenda",
    },
    "identify": {
        "name": "Identify",
        "spell_level": 1,
        "cost_gp": 20.0,
        "description": "Tunnistaa maagisen esineen ominaisuudet, loitsut ja kiroukset. "
            "Vaatii 100 gp helmen (ei kulu). Saatavilla maagisissa kaupoissa.",
        "caster": "Velho/Maaginen kauppa",
    },
    "dispel_magic": {
        "name": "Dispel Magic",
        "spell_level": 3,
        "cost_gp": 150.0,
        "description": "Poistaa maagisen efektin kohteesta. Automaattinen 3. tason "
            "tai alemman loitsun poisto, korkeammat vaativat ability checkin.",
        "caster": "Velho/Maaginen kilta",
    },
    "teleportation_circle": {
        "name": "Teleportation Circle",
        "spell_level": 5,
        "cost_gp": 500.0,
        "description": "Teleporttaa seurueen tunnettuun teleportaatioympyrään. "
            "Saatavilla suurissa velhokouluissa ja magian killoissa. "
            "Vaatii 50 gp raaka-aineita.",
        "caster": "Velho/Magian kilta",
    },
    "sending": {
        "name": "Sending",
        "spell_level": 3,
        "cost_gp": 75.0,
        "description": "Lähettää 25 sanan viestin kenelle tahansa tunnetulle olennolle "
            "missä tahansa samalla tasolla. Kohde voi vastata 25 sanalla.",
        "caster": "Velho/Viestinviejä-kilta",
    },
    "detect_magic": {
        "name": "Detect Magic",
        "spell_level": 1,
        "cost_gp": 15.0,
        "description": "Havaitsee magian 30 jalan säteellä 10 minuutin ajan. "
            "Paljastaa maagisten esineiden ja alueiden koulun (school).",
        "caster": "Velho/Maaginen kauppa",
    },
    "continual_flame": {
        "name": "Continual Flame",
        "spell_level": 2,
        "cost_gp": 75.0,
        "description": "Luo pysyvän maagisen liekin joka valaisee kuin soihtu. "
            "Ei tuota lämpöä eikä kulu polttoainetta. Vaatii 50 gp rubiinitomua.",
        "caster": "Pappi/Velho",
    },
}


# ============================================================================
# MISC SERVICES
# ============================================================================

MISC_SERVICES = {
    "stabling": {
        "name": "Hevosen tallihoito",
        "cost_per_day_gp": 0.05,  # 5 sp/day
        "description": "Hevosen tai muun ratsun tallihoito sisältäen ruokinnan, "
            "juottamisen, harjauksen ja kengityksen tarkistuksen. "
            "Useimmat majatalot ja tallimiehet tarjoavat tätä.",
    },
    "stabling_exotic": {
        "name": "Eksoottisen ratsun tallihoito",
        "cost_per_day_gp": 1.0,
        "description": "Epätavallisen ratsun hoito: griffoni, hippogrifi, pegasus tai "
            "vastaava. Vaatii erikoisruokaa ja isomman tilan.",
    },
    "messenger_local": {
        "name": "Viestinviejä (kaupunki)",
        "cost_gp": 0.002,  # 2 cp
        "description": "Paikallinen viestinviejäpoika kuljettaa kirjeen tai pienen "
            "paketin kaupungin sisällä. Perillä tunnissa.",
    },
    "messenger_long": {
        "name": "Viestinviejä (kaukokulku)",
        "cost_per_mile_gp": 0.02,  # 2 cp/mile
        "description": "Ratsastava viestinviejä kuljettaa viestin kaupunkien välillä. "
            "Nopeus n. 24 mailia/päivä. Hinta per maili.",
    },
    "bath_basic": {
        "name": "Kylpy (perus)",
        "cost_gp": 0.003,  # 3 cp
        "description": "Lämmin vesikylpy yksinkertaisessa kylpylässä tai majatalon "
            "takahuoneessa. Saippua ja pyyhe kuuluvat hintaan.",
    },
    "bath_luxury": {
        "name": "Kylpy (ylellinen)",
        "cost_gp": 0.1,
        "description": "Ylellinen kylpy tuoksuvilla öljyillä, yrteillä ja maagisesti "
            "lämmitetyllä vedellä. Hieronta ja rentoutus kuuluvat hintaan.",
    },
    "ferry_crossing": {
        "name": "Lossimatka (joen yli)",
        "cost_gp": 0.01,  # 1 cp
        "description": "Lossi tai lautta kuljettaa joen tai järven yli. "
            "Hinta per henkilö. Ratsuista lisämaksu.",
    },
    "laundry": {
        "name": "Pyykkipalvelu",
        "cost_gp": 0.001,  # 1 cp
        "description": "Vaatteiden pesu ja kuivaus. Valmis seuraavana päivänä.",
    },
    "entertainment_common": {
        "name": "Viihde (yhteishuone)",
        "cost_gp": 0.0,  # free
        "description": "Ilmainen viihde majatalon yhteishuoneessa: bardi, tarinaniskijä "
            "tai noppapeli. Laatu vaihtelee.",
    },
    "entertainment_theater": {
        "name": "Teatteriesitys",
        "cost_gp": 0.03,  # 3 sp
        "description": "Näytelmä, ooppera tai muu esitys paikallisessa teatterissa. "
            "Laadukkaat esitykset voivat maksaa 1-5 gp.",
    },
    "training_language": {
        "name": "Kielenopetus (per viikko)",
        "cost_gp": 5.0,
        "description": "Yksityisopetusta uudessa kielessä. Vaatii n. 10 viikkoa (250 tuntia) "
            "uuden kielen oppimiseen. Opettaja osaa kielen sujuvasti.",
    },
    "training_tool": {
        "name": "Työkalukoulutus (per viikko)",
        "cost_gp": 5.0,
        "description": "Yksityisopetusta uuden työkalun käytössä. Vaatii n. 10 viikkoa. "
            "Opettaja on alan mestari.",
    },
    "document_forgery": {
        "name": "Asiakirjaväärennös",
        "cost_gp": 15.0,
        "description": "Väärennä matkustuskirja, aateliskirje tai muu virallinen asiakirja. "
            "Laatu riippuu väärentäjän taidosta. Kiinni jääminen = vankila.",
    },
}


# ============================================================================
# PROPERTY PRICES (DMG p.127-128)
# ============================================================================

PROPERTY_PRICES = {
    # -- Purchase --
    "hovel": {
        "name": "Hökkeli/Mökki",
        "cost_gp": 50.0,
        "cost_rent_per_month_gp": 1.0,
        "description": "Yksihuoneinen puumökki tai savitiilitalo. Katto vuotaa, "
            "ovet eivät kunnolla sulkeudu. Riittää yhden tai kahden hengen majoitukseen.",
        "size": "small",
        "upkeep_per_day_gp": 0.01,
    },
    "cottage": {
        "name": "Talo/Cottage",
        "cost_gp": 500.0,
        "cost_rent_per_month_gp": 5.0,
        "description": "Pieni kivirunkoinen talo kahdella tai kolmella huoneella, "
            "takka ja pieni piha. Sopiva perheelle tai pienelle seurueelle.",
        "size": "medium",
        "upkeep_per_day_gp": 0.05,
    },
    "townhouse": {
        "name": "Kaupunkitalo",
        "cost_gp": 2500.0,
        "cost_rent_per_month_gp": 25.0,
        "description": "Kaksikerroksinen kivitalo kaupungin keskustassa. "
            "4-6 huonetta, kellari, pieni piha. Sopiva varakkaalle perheelle "
            "tai pienelle kauppaliikkeelle.",
        "size": "large",
        "upkeep_per_day_gp": 0.1,
    },
    "manor": {
        "name": "Kartano",
        "cost_gp": 25000.0,
        "cost_rent_per_month_gp": 100.0,
        "description": "Suuri kivikartano mailla ja piharakennuksilla. "
            "10-20 huonetta, juhlasali, keittiö, tallit, palvelijoiden asunnot. "
            "Vaatii 5-10 palvelijaa ylläpitoon.",
        "size": "estate",
        "upkeep_per_day_gp": 1.0,
    },
    "keep": {
        "name": "Linnoitus/Keep",
        "cost_gp": 50000.0,
        "description": "Pieni kivilinnoitus tornilla, muurilla ja portilla. "
            "Puolustettava. Vaatii 10-20 miehen varuskuntaa.",
        "size": "fortress",
        "upkeep_per_day_gp": 2.0,
    },
    "castle": {
        "name": "Linna",
        "cost_gp": 500000.0,
        "description": "Suuri linna useilla torneilla, vallihaudalla, sisäpihalla "
            "ja puolustusrakenteilla. Vaatii 50-200 hengen varuskuntaa. "
            "Kuninkaan tai ruhtinaan asuinsija.",
        "size": "castle",
        "upkeep_per_day_gp": 10.0,
    },
    "shop_property": {
        "name": "Kauppa/Liike (rakennus)",
        "cost_gp": 2000.0,
        "cost_rent_per_month_gp": 20.0,
        "description": "Liikerakennus kaupungin kadulle. Myyntitila alakerrassa, "
            "varasto ja/tai asunto yläkerrassa. Sopii kaikenlaisille kaupoille.",
        "size": "medium",
        "upkeep_per_day_gp": 0.1,
    },
    "warehouse": {
        "name": "Varasto",
        "cost_gp": 1000.0,
        "cost_rent_per_month_gp": 10.0,
        "description": "Suuri varastorakennus satamassa tai kauppakorttelissa. "
            "Tilaa tavaroille ja materiaaleille.",
        "size": "large",
        "upkeep_per_day_gp": 0.05,
    },
    "inn_property": {
        "name": "Majatalo (rakennus)",
        "cost_gp": 5000.0,
        "cost_rent_per_month_gp": 50.0,
        "description": "Majatalorakennus 5-15 vierashuoneella, yhteishuone, keittiö, "
            "kellari ja talli. Tuottaa voittoa jos hyvin hoidettu.",
        "size": "large",
        "upkeep_per_day_gp": 0.5,
    },
    "tower": {
        "name": "Torni",
        "cost_gp": 15000.0,
        "description": "Kivitorni 3-5 kerroksella. Velhon laboratorio, vartiointitorni "
            "tai majakka. Puolustettava ja yksityinen.",
        "size": "tower",
        "upkeep_per_day_gp": 0.5,
    },
    "temple_small": {
        "name": "Pieni temppeli",
        "cost_gp": 5000.0,
        "description": "Pieni rukoushuone tai kappeli yhdelle jumaluudelle. "
            "Alttari, rukouspenkki, pieni kirjasto. 1-3 pappia.",
        "size": "medium",
        "upkeep_per_day_gp": 0.2,
    },
    "temple_large": {
        "name": "Suuri temppeli/Katedraali",
        "cost_gp": 50000.0,
        "description": "Suuri pyhäkkö monimutkaisella arkkitehtuurilla. "
            "Useita kappeleita, kirjasto, luostari, parantola. "
            "10-50 pappia ja munkkia.",
        "size": "cathedral",
        "upkeep_per_day_gp": 3.0,
    },

    # -- Furniture & Decor --
    "table_basic": {
        "name": "Pöytä (perus)",
        "cost_gp": 1.0,
        "description": "Yksinkertainen puupöytä, sopii majataloon tai kotiin.",
        "size": "furniture",
    },
    "table_fine": {
        "name": "Pöytä (hieno)",
        "cost_gp": 25.0,
        "description": "Hienosti veistetty tammi- tai mahonkipöytä koristekuvioin.",
        "size": "furniture",
    },
    "chair_basic": {
        "name": "Tuoli (perus)",
        "cost_gp": 0.2,
        "description": "Yksinkertainen puutuoli ilman pehmustusta.",
        "size": "furniture",
    },
    "chair_comfortable": {
        "name": "Nojatuoli (pehmustettu)",
        "cost_gp": 5.0,
        "description": "Pehmustettu nojatuoli nahalla tai kankaalla verhoiltu.",
        "size": "furniture",
    },
    "bed_simple": {
        "name": "Sänky (yksinkertainen)",
        "cost_gp": 2.0,
        "description": "Puuframeen ja olkipatjan sänky. Perus mutta toimiva.",
        "size": "furniture",
    },
    "bed_comfortable": {
        "name": "Sänky (mukava)",
        "cost_gp": 25.0,
        "description": "Hyvä sänky höyhen- tai villapatjalla ja laadukkailla lakanoilla.",
        "size": "furniture",
    },
    "bed_luxury": {
        "name": "Sänky (ylellinen)",
        "cost_gp": 100.0,
        "description": "Veistetty nelipylväinen sänky silkkiverhoin ja höyhenpatjalla.",
        "size": "furniture",
    },
    "throne": {
        "name": "Valtaistuin",
        "cost_gp": 500.0,
        "description": "Koristeellinen istuin kullalla, jalokivillä ja veistoksin. "
            "Symboloi valtaa ja auktoriteettia.",
        "size": "furniture",
    },
    "tapestry": {
        "name": "Seinävaate/Kuvakudos",
        "cost_gp": 25.0,
        "description": "Kudottu seinävaate historiallisella tai mytologisella kuvalla.",
        "size": "furniture",
    },
    "chandelier": {
        "name": "Kattokruunu",
        "cost_gp": 50.0,
        "description": "Rautainen tai kristallinen kattokruunu kynttilöille. "
            "Valaisee suuren huoneen.",
        "size": "furniture",
    },
    "carpet_fine": {
        "name": "Hieno matto",
        "cost_gp": 25.0,
        "description": "Käsin kudottu itämainen tai haltijatyylinen matto.",
        "size": "furniture",
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_services() -> Dict[str, dict]:
    """Return combined dict of all service categories."""
    return {
        "lifestyle": LIFESTYLE_EXPENSES,
        "lodging": INN_ROOM_PRICES,
        "food_drink": FOOD_AND_DRINK,
        "hirelings": HIRELINGS,
        "spellcasting": SPELLCASTING_SERVICES,
        "misc_services": MISC_SERVICES,
        "property": PROPERTY_PRICES,
    }


SERVICE_CATEGORIES = {
    "lifestyle": "Elintaso (per päivä)",
    "lodging": "Majoitus (per yö)",
    "food_drink": "Ruoka & Juomat",
    "hirelings": "Palkatut (per päivä)",
    "spellcasting": "Loitsupalvelut",
    "misc_services": "Muut palvelut",
    "property": "Kiinteistöt & Huonekalut",
}


def get_service_price(category: str, service_key: str) -> float:
    """Get the price of a service."""
    cats = get_all_services()
    cat = cats.get(category, {})
    svc = cat.get(service_key, {})
    # Different categories use different price fields
    for field in ["cost_gp", "cost_per_day_gp", "cost_per_night_gp", "cost_per_mile_gp"]:
        if field in svc:
            return svc[field]
    return 0.0


def format_price(gp: float) -> str:
    """Format a gold piece amount into a readable string with appropriate units."""
    if gp <= 0:
        return "Ilmainen"
    if gp >= 1.0:
        if gp == int(gp):
            return f"{int(gp)} gp"
        return f"{gp:.1f} gp"
    sp = gp * 10
    if sp >= 1.0:
        if sp == int(sp):
            return f"{int(sp)} sp"
        return f"{sp:.1f} sp"
    cp = gp * 100
    if cp == int(cp):
        return f"{int(cp)} cp"
    return f"{cp:.1f} cp"


def get_services_for_location_type(location_type: str) -> List[str]:
    """Get relevant service categories for a location type."""
    mapping = {
        "tavern": ["lodging", "food_drink", "misc_services"],
        "shop": ["misc_services"],
        "temple": ["spellcasting", "misc_services"],
        "city": ["lifestyle", "lodging", "food_drink", "hirelings", "spellcasting", "misc_services", "property"],
        "town": ["lifestyle", "lodging", "food_drink", "hirelings", "misc_services"],
        "village": ["lodging", "food_drink", "misc_services"],
        "castle": ["lodging", "food_drink", "hirelings", "property"],
        "port": ["lodging", "food_drink", "hirelings", "misc_services"],
        "camp": ["food_drink", "misc_services"],
    }
    return mapping.get(location_type, ["misc_services"])
