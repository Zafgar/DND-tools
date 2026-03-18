"""
D&D 5e Travel System — Mounts, Vehicles, Travel Costs, Ship Passage.

Covers all forms of transportation from PHB p.155-157, DMG references:
- Mounts (horses, ponies, exotic)
- Vehicles (carts, wagons, carriages)
- Ships and water vessels
- Travel pace and daily distance
- Passage costs (land and sea)
- Random encounter chances by terrain

All prices in gold pieces (gp).
"""
from typing import Dict, List


# ============================================================================
# MOUNTS & ANIMALS (PHB p.157)
# ============================================================================

MOUNTS: Dict[str, dict] = {
    # -- Common Mounts --
    "donkey": {
        "name": "Aasi/Muuli",
        "cost_buy_gp": 8.0,
        "cost_rent_per_day_gp": 0.5,
        "speed_ft": 40,
        "carry_capacity_lb": 420,
        "description": (
            "Sitkeä ja vaatimaton kuormajuhta. Ei sovellu taisteluun mutta kantaa "
            "tavaroita väsymättä. Pärjää vähällä ruoalla ja vedellä. "
            "Itsepäinen mutta luotettava."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.05,
        "stats": "Mule",
    },
    "pony": {
        "name": "Poni",
        "cost_buy_gp": 30.0,
        "cost_rent_per_day_gp": 1.0,
        "speed_ft": 40,
        "carry_capacity_lb": 225,
        "description": (
            "Pieni ja kestävä ratsu, sopiva puoliksille ja gnomeille. "
            "Ystävällinen ja helppo käsitellä. Ei sovellu raskaaseen taisteluun. "
            "Medium-kokoiset hahmot voivat ratsastaa mutta hitaasti."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.05,
        "stats": "Pony",
    },
    "riding_horse": {
        "name": "Ratsuhevonen",
        "cost_buy_gp": 75.0,
        "cost_rent_per_day_gp": 2.0,
        "speed_ft": 60,
        "carry_capacity_lb": 480,
        "description": (
            "Yleisin ratsu seikkailijoille. Nopea ja kestävä, koulutettu "
            "kantamaan ratsastajaa ja pieniä kuormia. Säikähtää taistelun melua "
            "ellei ole koulutettu sotahevoseksi."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.05,
        "stats": "Riding Horse",
    },
    "draft_horse": {
        "name": "Vetohevonen",
        "cost_buy_gp": 50.0,
        "cost_rent_per_day_gp": 1.5,
        "speed_ft": 40,
        "carry_capacity_lb": 540,
        "description": (
            "Suuri ja voimakas hevonen vaunu- ja kuormavetotyöhön. "
            "Hitaampi kuin ratsuhevonen mutta kantaa enemmän. "
            "Rauhallinen luonne, ei pelästy helposti."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.05,
        "stats": "Draft Horse",
    },
    "warhorse": {
        "name": "Sotahevonen",
        "cost_buy_gp": 400.0,
        "cost_rent_per_day_gp": 10.0,
        "speed_ft": 60,
        "carry_capacity_lb": 540,
        "description": (
            "Jalosti kasvatettu ja taisteluun koulutettu ratsu. "
            "Ei pelästy taistelun melua, koulutettu potkimaan ja puremaan. "
            "Vaatii kokeneen ratsastajan (Animal Handling proficiency suositeltava)."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.1,
        "stats": "Warhorse",
    },
    "camel": {
        "name": "Kameli",
        "cost_buy_gp": 50.0,
        "cost_rent_per_day_gp": 1.5,
        "speed_ft": 50,
        "carry_capacity_lb": 480,
        "description": (
            "Aavikon kulkuneuvo joka kestää kuumuutta ja janoa. "
            "Voi matkustaa 5 päivää ilman vettä. Itsepäinen mutta "
            "korvaamaton aavikko-olosuhteissa."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.05,
        "stats": "Camel",
    },
    "elephant": {
        "name": "Elefantti",
        "cost_buy_gp": 200.0,
        "cost_rent_per_day_gp": 5.0,
        "speed_ft": 40,
        "carry_capacity_lb": 1320,
        "description": (
            "Valtava eläin joka voi kantaa useita matkustajia ja suuria kuormia. "
            "Vaatii paljon ruokaa ja tilaa. Älykäs ja uskollinen ohjaajalle. "
            "Voidaan varustaa taistelutornilla (howdah)."
        ),
        "category": "exotic",
        "stabling_per_day_gp": 1.0,
        "stats": "Elephant",
    },
    "mastiff": {
        "name": "Sotakoira (Mastiff)",
        "cost_buy_gp": 25.0,
        "cost_rent_per_day_gp": 1.0,
        "speed_ft": 40,
        "carry_capacity_lb": 195,
        "description": (
            "Suuri ja voimakas koira joka voi kantaa Small-kokoista ratsastajaa. "
            "Halflingien ja gnomien suosima ratsu kaupungeissa. "
            "Lojaali ja puolustaa omistajaansa."
        ),
        "category": "common",
        "stabling_per_day_gp": 0.03,
        "stats": "Mastiff",
    },

    # -- Exotic Mounts --
    "griffon": {
        "name": "Griffoni",
        "cost_buy_gp": 15000.0,
        "cost_rent_per_day_gp": 0,  # Not available for rent
        "speed_ft": 80,
        "fly_speed_ft": 80,
        "carry_capacity_lb": 480,
        "description": (
            "Majesteettinen lentävä olento — kotkan pää ja siivet, leijonan ruumis. "
            "Erittäin harvinainen ja kallis. Vaatii griffoni-kasvatusta poikasesta asti "
            "tai maagista kesyttämistä. Lentää 80 jalkaa/kierros. "
            "Arvostettua sotaratsuja kuninkaan eliittijoukkojen joukossa."
        ),
        "category": "exotic",
        "stabling_per_day_gp": 5.0,
        "stats": "Griffon",
    },
    "hippogriff": {
        "name": "Hippogrifi",
        "cost_buy_gp": 8000.0,
        "cost_rent_per_day_gp": 0,
        "speed_ft": 40,
        "fly_speed_ft": 60,
        "carry_capacity_lb": 400,
        "description": (
            "Lentävä ratsu — kotkan etupuolisko ja hevosen takapuolisko. "
            "Helpompi kesyttää kuin griffoni. Lentää 60 jalkaa/kierros. "
            "Vaatii erityistallin ja tuoretta lihaa ravinnoksi."
        ),
        "category": "exotic",
        "stabling_per_day_gp": 3.0,
        "stats": "Hippogriff",
    },
    "pegasus": {
        "name": "Pegasus",
        "cost_buy_gp": 20000.0,
        "cost_rent_per_day_gp": 0,
        "speed_ft": 60,
        "fly_speed_ft": 90,
        "carry_capacity_lb": 480,
        "description": (
            "Taivaallinen siivekäs hevonen. Erittäin harvinainen ja ei-ostettavissa "
            "tavanomaisesti — pegasuksen ystävyyden on ansaittava. Chaotic Good -luonto. "
            "Nopein tavallinen lentävä ratsu. Välttää pahoja olentoja."
        ),
        "category": "exotic",
        "stabling_per_day_gp": 5.0,
        "stats": "Pegasus",
    },
    "wyvern": {
        "name": "Wyverni",
        "cost_buy_gp": 25000.0,
        "cost_rent_per_day_gp": 0,
        "speed_ft": 20,
        "fly_speed_ft": 80,
        "carry_capacity_lb": 600,
        "description": (
            "Draakontapainen lentolisko myrkyllisellä häntäpiikillä. "
            "Vaarallinen ja vaikea kontrolloida — vaatii kokeneen ohjaajan. "
            "Käytetään sotaratsuna orkkien ja muiden brutaalien kulttuurien joukossa."
        ),
        "category": "exotic",
        "stabling_per_day_gp": 8.0,
        "stats": "Wyvern",
    },
    "phantom_steed": {
        "name": "Haamuhevonen (loitsu)",
        "cost_buy_gp": 0,
        "cost_rent_per_day_gp": 0,
        "speed_ft": 100,
        "carry_capacity_lb": 0,
        "description": (
            "Phantom Steed -loitsulla (3rd level) luotu maaginen ratsu. "
            "Nopeus 100 ft (13 mph), kestää 1 tunnin. Ei fyysinen — häviää "
            "vahingosta. Ilmainen mutta vaatii loitsupaikan ja 1 min castingin."
        ),
        "category": "magical",
        "stabling_per_day_gp": 0,
        "stats": None,
    },
}


# ============================================================================
# VEHICLES — LAND (PHB p.157)
# ============================================================================

VEHICLES_LAND: Dict[str, dict] = {
    "cart": {
        "name": "Kärryt",
        "cost_buy_gp": 15.0,
        "cost_rent_per_day_gp": 0.5,
        "speed_mph": 1,  # Depends on pulling animal
        "carry_capacity_lb": 500,
        "description": (
            "Yksinkertainen kaksipyöräinen kärryt yhdellä vetojuhdalla. "
            "Kantaa kohtuullisen kuorman. Ei sovellu vaikeaan maastoon. "
            "Vaatii vetojuhdan (yleensä aasi tai vetohevonen)."
        ),
        "animals_needed": 1,
        "terrain": "road, trail",
    },
    "wagon": {
        "name": "Vaunu",
        "cost_buy_gp": 35.0,
        "cost_rent_per_day_gp": 1.0,
        "speed_mph": 2,
        "carry_capacity_lb": 2000,
        "description": (
            "Nelipyöräinen vaunu kahdella tai neljällä vetohevosella. "
            "Mahtuu suuri kuorma tai 4-6 matkustajaa. Kestävä mutta hidas. "
            "Tarvitsee kunnollisen tien."
        ),
        "animals_needed": 2,
        "terrain": "road",
    },
    "carriage": {
        "name": "Vaunut (hienotason)",
        "cost_buy_gp": 100.0,
        "cost_rent_per_day_gp": 3.0,
        "speed_mph": 3,
        "carry_capacity_lb": 1000,
        "description": (
            "Suljetut jousitetut vaunut kahdella tai neljällä hevosella. "
            "Mukava matkustaa — suojaa sateelta ja kylmältä. "
            "4 matkustajaa + kuski. Sopii aatelistolle ja diplomaateille."
        ),
        "animals_needed": 2,
        "terrain": "road",
    },
    "chariot": {
        "name": "Sotavaunu",
        "cost_buy_gp": 250.0,
        "cost_rent_per_day_gp": 5.0,
        "speed_mph": 4,
        "carry_capacity_lb": 300,
        "description": (
            "Kaksipyöräinen sotavaunu kahdella sotahevosella. "
            "Nopea ja maneuveeraava taistelukentällä. Kantaa 1-2 taistelijaa. "
            "Vaatii War Vehicles -taidon ohjaamiseen."
        ),
        "animals_needed": 2,
        "terrain": "road, open",
    },
    "sled": {
        "name": "Reki (koiravaljaat)",
        "cost_buy_gp": 20.0,
        "cost_rent_per_day_gp": 1.0,
        "speed_mph": 3,
        "carry_capacity_lb": 600,
        "description": (
            "Koira- tai porovetoreki arktiseen maastoon. "
            "Vaatii 4-8 koiraa tai 2-4 poroa. Ainoa tehokas kulkuneuvo "
            "syvän lumen ja jään yllä."
        ),
        "animals_needed": 4,
        "terrain": "snow, ice",
    },
}


# ============================================================================
# VEHICLES — WATER (PHB p.157, DMG)
# ============================================================================

VEHICLES_WATER: Dict[str, dict] = {
    "rowboat": {
        "name": "Soutuvene",
        "cost_buy_gp": 50.0,
        "cost_rent_per_day_gp": 1.0,
        "speed_mph": 1.5,
        "passengers": 3,
        "cargo_tons": 0.25,
        "crew": 1,
        "description": (
            "Pieni puuvene yhdelle tai kahdelle soutajalle. "
            "Mahtuu 3 matkustajaa + pieni kuorma. "
            "Soveltuu jokiin, järviin ja rannikkovesiin tyynellä säällä."
        ),
        "category": "small",
    },
    "canoe": {
        "name": "Kanootti",
        "cost_buy_gp": 25.0,
        "cost_rent_per_day_gp": 0.5,
        "speed_mph": 1.5,
        "passengers": 2,
        "cargo_tons": 0.1,
        "crew": 1,
        "description": (
            "Kevyt puinen tai nahkainen vene meloilla. Nopea ja ketterä "
            "jokivedessä. Mahtuu 2 matkustajaa. Helppo kantaa maalla."
        ),
        "category": "small",
    },
    "keelboat": {
        "name": "Jokialus",
        "cost_buy_gp": 3000.0,
        "cost_rent_per_day_gp": 10.0,
        "speed_mph": 1,
        "passengers": 6,
        "cargo_tons": 0.5,
        "crew": 3,
        "description": (
            "Puinen jokialus purjeella ja airoilla. 40-60 jalkaa pitkä. "
            "Soveltuu jokiin ja rannikkovesiin. Mahtuu 6 matkustajaa ja "
            "kohtuullinen kuorma."
        ),
        "category": "medium",
    },
    "sailing_ship": {
        "name": "Purjelaiva",
        "cost_buy_gp": 10000.0,
        "cost_rent_per_day_gp": 0,  # Hire passage instead
        "speed_mph": 2,
        "passengers": 20,
        "cargo_tons": 100,
        "crew": 20,
        "description": (
            "Keskikokoinen purjelaiva avomerelle. 60-80 jalkaa pitkä. "
            "Mahtuu 20 matkustajaa ja 100 tonnia lastia. "
            "Vaatii 20 hengen miehistön. Nopeus riippuu tuulesta."
        ),
        "category": "large",
    },
    "galley": {
        "name": "Kaleeri",
        "cost_buy_gp": 30000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 4,
        "passengers": 40,
        "cargo_tons": 150,
        "crew": 80,
        "description": (
            "Suuri sotilaallinen alus airoilla ja purjeilla. 130+ jalkaa pitkä. "
            "Nopein perinteinen vesialus. Vaatii 80 soutajaa. "
            "Varustettu taisteluun: keulakuva, katapultti, rautakeula."
        ),
        "category": "large",
    },
    "longship": {
        "name": "Pitkälaiva (viikinki)",
        "cost_buy_gp": 10000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 3,
        "passengers": 150,
        "cargo_tons": 10,
        "crew": 40,
        "description": (
            "Pitkä ja matala viikinkilaiva airoilla ja purjeella. "
            "Erittäin merikelpoinen — kestää myrskyä. Voi rantautua missä tahansa. "
            "150 sotilasta + 10 tonnia lastia. Nopea ja pelätty."
        ),
        "category": "large",
    },
    "warship": {
        "name": "Sotalviva",
        "cost_buy_gp": 25000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 2.5,
        "passengers": 60,
        "cargo_tons": 200,
        "crew": 60,
        "description": (
            "Suuri sotalvia tykistöllä ja vahvalla rakenteella. "
            "100+ jalkaa pitkä, 60 miehistöjäsentä. "
            "Varustettu ballista, katapultti ja keulakuva."
        ),
        "category": "large",
    },

    # -- Exotic/Magical Vessels --
    "airship": {
        "name": "Ilmalaiva",
        "cost_buy_gp": 100000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 8,
        "passengers": 30,
        "cargo_tons": 10,
        "crew": 10,
        "description": (
            "Maagisesti lentävä alus ilmaelementaalimoottorilla. "
            "Nopein tavanomaineen kulkuneuvo — 8 mailia tunnissa (192 mailia/päivä). "
            "Erittäin harvinainen ja kallis. Vaatii maagista polttoainetta. "
            "Voi laskeutua minne tahansa tasaiselle pinnalle."
        ),
        "category": "exotic",
    },
    "apparatus_of_kwalish": {
        "name": "Kwalishin Apparaatti",
        "cost_buy_gp": 80000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 1,
        "passengers": 2,
        "cargo_tons": 0,
        "crew": 1,
        "description": (
            "Maaginen mekaaninen hummeri/sukellusvene. Legendary-tason maaginen esine. "
            "Kestää merenpohjassa, liikkuu maalla ja vedessä. 2 matkustajaa. "
            "AC 20, 200 HP. Valkea timanttikuori."
        ),
        "category": "exotic",
    },
    "folding_boat": {
        "name": "Taittuva vene",
        "cost_buy_gp": 10000.0,
        "cost_rent_per_day_gp": 0,
        "speed_mph": 2,
        "passengers": 4,
        "cargo_tons": 0.5,
        "crew": 1,
        "description": (
            "Maaginen taittuva vene joka muuttuu laatikosta 10-jalkaiseksi veneeksi "
            "tai 24-jalkaiseksi purjeveneeksi komennolla. Uncommon maaginen esine. "
            "Mahtuu taskuun kun taitettu."
        ),
        "category": "exotic",
    },
}


# ============================================================================
# TRAVEL PACE (PHB p.182)
# ============================================================================

TRAVEL_PACE = {
    "fast": {
        "name": "Nopea",
        "miles_per_hour": 4,
        "miles_per_day": 30,
        "effect": "-5 penalty passive Perception",
        "description": (
            "Pikamarssataan 30 mailia päivässä (48 km). "
            "Väsyttävää — -5 Passive Perception. "
            "Ei voi käyttää Stealth-taitoa."
        ),
    },
    "normal": {
        "name": "Normaali",
        "miles_per_hour": 3,
        "miles_per_day": 24,
        "effect": "Ei erikoisefektejä",
        "description": (
            "Normaali matkavauhti 24 mailia päivässä (38 km). "
            "Tasapainoinen vauhti pitkille matkoille."
        ),
    },
    "slow": {
        "name": "Hidas",
        "miles_per_hour": 2,
        "miles_per_day": 18,
        "effect": "Voi käyttää Stealth-taitoa",
        "description": (
            "Varovainen eteneminen 18 mailia päivässä (29 km). "
            "Voi hiiviskellä ja tarkkailla ympäristöä. "
            "Stealth mahdollista koko ryhmälle."
        ),
    },
}

# ============================================================================
# PASSAGE COSTS (PHB p.157)
# ============================================================================

PASSAGE_COSTS = {
    "coach_between_towns": {
        "name": "Postivaunut (kaupunkien välillä)",
        "cost_per_mile_gp": 0.003,  # 3 cp per mile
        "description": (
            "Julkinen postivaunulinja kaupunkien välillä. "
            "Matkustaminen yhteisessä vaunussa. Ei yksityisyyttä mutta turvallista. "
            "Nopeus n. 3 mph, pysähtyminen majataloissa yöksi."
        ),
    },
    "river_ferry": {
        "name": "Jokiferiisi/lossi",
        "cost_per_mile_gp": 0.001,  # 1 cp per mile
        "description": (
            "Jokialuksella matkustaminen myötävirtaan. Halvin matkustustapa "
            "kun joki kulkee oikeaan suuntaan. Nopeus n. 1 mph."
        ),
    },
    "ship_passage": {
        "name": "Laivamatka (tavallinen)",
        "cost_per_mile_gp": 0.001,  # 1 sp per mile -> Actually PHB says 1 sp per mile
        "description": (
            "Matkustajakansipaikka kauppalaivassa. Oma sänky ruumassa, "
            "yksinkertainen ruoka kuuluu hintaan. Nopeus n. 2 mph."
        ),
    },
    "ship_passage_cabin": {
        "name": "Laivamatka (hytti)",
        "cost_per_mile_gp": 0.02,
        "description": (
            "Yksityinen hytti kauppalaivassa tai matkustaja-aluksessa. "
            "Oma sänky, pöytä, lukittava ovi. Ruoka ja juoma kuuluvat hintaan. "
            "Huomattavasti mukavampi kuin kansipaikka."
        ),
    },
    "airship_passage": {
        "name": "Ilmalaivamatka",
        "cost_per_mile_gp": 0.1,
        "description": (
            "Matkustaminen ilmalaivalla — nopeinta mahdollista matkustamista. "
            "Erittäin kallista mutta 8x nopeampaa kuin maanteitä. "
            "Saatavilla vain suurissa kaupungeissa."
        ),
    },
    "teleportation_circle": {
        "name": "Teleportaatioympyrä",
        "cost_per_use_gp": 500.0,
        "description": (
            "Välitön teleportaatio tunnettuun teleportaatioympyrään. "
            "Kallis mutta välitön. Saatavilla velhokouluissa ja magiakiltaissa. "
            "Koko seurue mahtuu yhdellä käytöllä."
        ),
    },
}


# ============================================================================
# TERRAIN & TRAVEL MODIFIERS
# ============================================================================

TERRAIN_MODIFIERS = {
    "road": {
        "name": "Tie/Valtatie",
        "speed_modifier": 1.0,
        "encounter_chance": 0.10,
        "description": "Hyvä tie — normaali matkanopeus. Turvallisinta matkustamista.",
    },
    "trail": {
        "name": "Polku/Kärrypolku",
        "speed_modifier": 0.75,
        "encounter_chance": 0.15,
        "description": "Epätasainen polku — 75% normaalista nopeudesta.",
    },
    "forest": {
        "name": "Metsä",
        "speed_modifier": 0.5,
        "encounter_chance": 0.20,
        "description": "Tiheä metsä — 50% nopeudesta. Näkyvyys rajoitettua.",
    },
    "hills": {
        "name": "Kukkulat/Vuoret",
        "speed_modifier": 0.5,
        "encounter_chance": 0.15,
        "description": "Kukkulainen maasto — 50% nopeudesta. Paljon kiipeämistä.",
    },
    "mountains": {
        "name": "Vuoristo",
        "speed_modifier": 0.33,
        "encounter_chance": 0.20,
        "description": "Vuoristomaasto — 33% nopeudesta. Vaarallista ja hidasta.",
    },
    "swamp": {
        "name": "Suo/Räme",
        "speed_modifier": 0.5,
        "encounter_chance": 0.25,
        "description": "Soinen maasto — 50% nopeudesta. Uppoamisen vaara, sairauksia.",
    },
    "desert": {
        "name": "Aavikko",
        "speed_modifier": 0.5,
        "encounter_chance": 0.10,
        "description": "Aavikkomaasto — 50% nopeudesta. Kuumuus ja janokuolema.",
    },
    "arctic": {
        "name": "Arktinen/Jäätikkö",
        "speed_modifier": 0.5,
        "encounter_chance": 0.10,
        "description": "Jäinen arktinen maasto — 50% nopeudesta. Paleltuma ja lumisokeus.",
    },
    "jungle": {
        "name": "Viidakko",
        "speed_modifier": 0.33,
        "encounter_chance": 0.30,
        "description": "Tiheä trooppinen viidakko — 33% nopeudesta. Hyönteiset, sairaudet, petoeläimet.",
    },
    "ocean": {
        "name": "Avomeri",
        "speed_modifier": 1.0,
        "encounter_chance": 0.10,
        "description": "Avomerta purjehtimista — normaali laivan nopeus, tuulesta riippuu.",
    },
    "coastal": {
        "name": "Rannikko",
        "speed_modifier": 0.75,
        "encounter_chance": 0.15,
        "description": "Rannikonmyötäisesti — 75% nopeudesta. Kareja ja matalikoja.",
    },
    "underdark": {
        "name": "Underdark",
        "speed_modifier": 0.5,
        "encounter_chance": 0.30,
        "description": "Maanalaiset luolastot — 50% nopeudesta. Pimeää ja vaarallista.",
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_travel_time(distance_miles: float, pace: str = "normal",
                         terrain: str = "road", mounted: bool = False,
                         mount_key: str = "") -> dict:
    """
    Calculate travel time for a journey.

    Returns dict with: days, hours, encounter_checks, pace_effect
    """
    pace_info = TRAVEL_PACE.get(pace, TRAVEL_PACE["normal"])
    terrain_info = TERRAIN_MODIFIERS.get(terrain, TERRAIN_MODIFIERS["road"])

    mph = pace_info["miles_per_hour"]
    daily = pace_info["miles_per_day"]

    # Terrain modifier
    mph *= terrain_info["speed_modifier"]
    daily *= terrain_info["speed_modifier"]

    # Mounted travel (doesn't increase daily distance for long journeys per RAW,
    # but allows short bursts of speed)
    mount_note = ""
    if mounted and mount_key:
        mount = MOUNTS.get(mount_key)
        if mount:
            mount_note = f"Ratsu: {mount['name']} (nopeus {mount['speed_ft']} ft)"

    hours = distance_miles / mph if mph > 0 else float('inf')
    days = distance_miles / daily if daily > 0 else float('inf')
    encounter_checks = max(1, int(days))

    return {
        "distance_miles": distance_miles,
        "pace": pace_info["name"],
        "terrain": terrain_info["name"],
        "mph": round(mph, 1),
        "daily_miles": round(daily, 1),
        "total_hours": round(hours, 1),
        "total_days": round(days, 1),
        "encounter_checks": encounter_checks,
        "encounter_chance_per_check": terrain_info["encounter_chance"],
        "pace_effect": pace_info["effect"],
        "mount_note": mount_note,
    }


def format_travel_time(days: float) -> str:
    """Format travel days into readable string."""
    if days < 1:
        hours = days * 8  # 8-hour travel day
        if hours < 1:
            return f"{int(hours * 60)} minuuttia"
        return f"{hours:.1f} tuntia"
    if days == int(days):
        return f"{int(days)} päivää"
    return f"{days:.1f} päivää"


def get_passage_cost(distance_miles: float, passage_type: str) -> float:
    """Calculate passage cost for a journey."""
    passage = PASSAGE_COSTS.get(passage_type)
    if not passage:
        return 0.0
    if "cost_per_mile_gp" in passage:
        return distance_miles * passage["cost_per_mile_gp"]
    if "cost_per_use_gp" in passage:
        return passage["cost_per_use_gp"]
    return 0.0


def get_all_mounts() -> Dict[str, dict]:
    """Return all mounts."""
    return MOUNTS


def get_mounts_by_category(category: str) -> List[dict]:
    """Get mounts by category (common, exotic, magical)."""
    return [m for m in MOUNTS.values() if m.get("category") == category]


def get_all_vehicles() -> Dict[str, dict]:
    """Return all vehicles (land + water)."""
    combined = {}
    combined.update(VEHICLES_LAND)
    combined.update(VEHICLES_WATER)
    return combined
