"""
D&D 5e Premade Shop Templates — Ready-to-use shop configurations by level tier.

Each template creates a complete shop with:
- Name, description, inventory appropriate for party level
- Staff NPC (shopkeeper and assistants)
- Special features and flavor
- Level-appropriate items with D&D 5e pricing

Tiers match party level ranges:
- Tier 1 (Levels 1-4): Local Heroes — mundane + common magic
- Tier 2 (Levels 5-10): Heroes of the Realm — uncommon magic, better mundane
- Tier 3 (Levels 11-16): Masters of the Realm — rare magic, exotic goods
- Tier 4 (Levels 17-20): Masters of the World — very rare/legendary items

Usage:
    from data.shop_templates import SHOP_TEMPLATES, get_shop_template, apply_shop_template
"""
from typing import Dict, List, Optional


# ============================================================================
# SHOP TEMPLATES
# ============================================================================

SHOP_TEMPLATES: Dict[str, dict] = {

    # ========================================================================
    # GENERAL STORES
    # ========================================================================

    "general_store_tier1": {
        "name": "Matkamiehen Tavaratalo",
        "tier": 1,
        "level_range": "1-4",
        "shop_type": "general_store",
        "description": (
            "Pieni mutta hyvin varusteltu yleiskauppa tien varrella tai kylässä. "
            "Seinät on vuorattu hyllyillä täynnä köysiä, kynttilöitä, kuivamuonaa "
            "ja seikkailijoiden perustarpeita. Tiskin takana roikkuu kartta lähialueesta."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Backpack", "price_gp": 2.0, "qty": 5, "desc": "Nahkainen reppu, mahtuu 30 lb tavaraa."},
            {"name": "Bedroll", "price_gp": 1.0, "qty": 5, "desc": "Lämpimästi vuorattu makuupussi."},
            {"name": "Rations (1 day)", "price_gp": 0.5, "qty": 50, "desc": "Päivän kuivamuona — kuivattua lihaa, pähkinöitä, leipää."},
            {"name": "Rope (50 ft)", "price_gp": 1.0, "qty": 5, "desc": "Hamppuköysi, 50 jalkaa. Kestää 3,000 lb."},
            {"name": "Silk Rope (50 ft)", "price_gp": 10.0, "qty": 2, "desc": "Silkkiköysi, vahvempi ja kevyempi kuin hamppu."},
            {"name": "Torch", "price_gp": 0.01, "qty": 20, "desc": "Soihtu, palaa 1 tunnin, valaisee 20 ft."},
            {"name": "Lantern (hooded)", "price_gp": 5.0, "qty": 3, "desc": "Lyhty säädettävällä valolla. Palaa 6h per öljypullo."},
            {"name": "Oil Flask", "price_gp": 0.1, "qty": 10, "desc": "Öljypullo lyhtyyn tai heittämiseen."},
            {"name": "Tinderbox", "price_gp": 0.5, "qty": 5, "desc": "Tulukset — sytytä tuli minuutissa."},
            {"name": "Waterskin", "price_gp": 0.2, "qty": 8, "desc": "Nahkainen vesipullo, mahtuu 4 pintiä."},
            {"name": "Healer's Kit", "price_gp": 5.0, "qty": 3, "desc": "10 käyttökertaa — stabiloi kuoleva ilman Medicine-chekkiä."},
            {"name": "Piton", "price_gp": 0.05, "qty": 20, "desc": "Rautapiikki kiipeilyyn ja ankkurointiin."},
            {"name": "Grappling Hook", "price_gp": 2.0, "qty": 2, "desc": "Koukku köyden päähän kiipeilyyn."},
            {"name": "Crowbar", "price_gp": 2.0, "qty": 2, "desc": "Rautakanki — advantage Strength chekkeihin avattaessa."},
            {"name": "Chain (10 ft)", "price_gp": 5.0, "qty": 3, "desc": "Rautaketju, AC 20, 10 HP."},
            {"name": "Caltrops", "price_gp": 1.0, "qty": 5, "desc": "Rautanauloja — hidastaa ja vahingoittaa kulkijoita."},
            {"name": "Ball Bearings", "price_gp": 1.0, "qty": 5, "desc": "1000 pientä metallikuulaa — luo liukas alue."},
            {"name": "Ink Bottle", "price_gp": 10.0, "qty": 2, "desc": "1 unssi mustaa mustetta."},
            {"name": "Paper (1 sheet)", "price_gp": 0.2, "qty": 20, "desc": "Paperia kirjoittamiseen."},
            {"name": "Sealing Wax", "price_gp": 0.5, "qty": 3, "desc": "Sinettivahaa kirjeiden sulkemiseen."},
        ],
        "staff": [
            {"name": "Hilda Koivu", "role": "Kauppias", "race": "Human", "gender": "Female",
             "appearance": "Keski-ikäinen, pyöreä, aina laskee rahoja",
             "personality": "Ahkera ja tinkimätön hinnoissa. Tietää mitä seikkailijat tarvitsevat.",
             "occupation": "Shopkeeper", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Lähialueen kartta saatavilla (2 gp)",
            "Voi tilata erikoistuotteita — toimitusaika 1d4 päivää",
        ],
    },

    "general_store_tier2": {
        "name": "Seikkailijan Varustamo",
        "tier": 2,
        "level_range": "5-10",
        "shop_type": "general_store",
        "description": (
            "Suuri kauppa kaupungin keskustassa, erikoistunut seikkailijoiden "
            "varusteisiin. Laaja valikoima tavallisista tarvikkeista harvinaisempiin "
            "erikoistyökaluihin. Myyjät osaavat neuvoa oikean varusteen valinnassa."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Explorer's Pack", "price_gp": 10.0, "qty": 5, "desc": "Täydellinen seikkailupakkaus: reppu, makuupussi, muona, vesi, soihdut, köysi."},
            {"name": "Climber's Kit", "price_gp": 25.0, "qty": 3, "desc": "Kiipeilysetti: piikit, hanskat, valjaat. Estää putoamisen."},
            {"name": "Healer's Kit", "price_gp": 5.0, "qty": 10, "desc": "10 käyttökertaa — stabiloi kuoleva ilman Medicine-chekkiä."},
            {"name": "Antitoxin", "price_gp": 50.0, "qty": 5, "desc": "Advantage myrkkyjen saving throwiin 1 tunnin ajan."},
            {"name": "Spyglass", "price_gp": 1000.0, "qty": 1, "desc": "Kaukoputki — näkee kauas kuin lähelle."},
            {"name": "Magnifying Glass", "price_gp": 100.0, "qty": 2, "desc": "Suurennuslasi tutkimiseen ja tulen sytyttämiseen."},
            {"name": "Holy Water", "price_gp": 25.0, "qty": 5, "desc": "Pyhitettyä vettä — 2d6 radiant damage undeadille/fiendille."},
            {"name": "Alchemist's Fire", "price_gp": 50.0, "qty": 5, "desc": "Heittopullo — 1d4 fire damage per kierros kunnes sammutettu."},
            {"name": "Acid Vial", "price_gp": 25.0, "qty": 5, "desc": "Happopullo — 2d6 acid damage heitettäessä."},
            {"name": "Manacles", "price_gp": 2.0, "qty": 3, "desc": "Rautakäsiraudat — DC 20 Strength tai DC 15 Dexterity avattaessa."},
            {"name": "Signal Whistle", "price_gp": 0.05, "qty": 10, "desc": "Pilli joka kuuluu 600 jalan päähän."},
            {"name": "Tent (2-person)", "price_gp": 2.0, "qty": 3, "desc": "Kankainen teltta kahdelle. Suojaa sateelta."},
            {"name": "Portable Ram", "price_gp": 4.0, "qty": 1, "desc": "Murtopukki — +4 Strength chekkiin ovien avaamiseen."},
            {"name": "Potion of Healing", "price_gp": 50.0, "qty": 5, "desc": "Parantaa 2d4+2 HP. Punainen neste."},
            {"name": "Potion of Greater Healing", "price_gp": 200.0, "qty": 2, "desc": "Parantaa 4d4+4 HP. Kirkkaan punainen."},
        ],
        "staff": [
            {"name": "Doran Kivisydän", "role": "Kauppias", "race": "Dwarf", "gender": "Male",
             "appearance": "Leveä, punapartainen, aina sormushaarniskakäsineet kädessä",
             "personality": "Tietää kaiken varusteista. Kertoo mielellään sotakertomuksia.",
             "occupation": "Shopkeeper", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Voi tilata uncommon-tason maagisia esineitä (1d6 päivän toimitusaika, kaksinkertainen hinta)",
            "Varusteiden korjauspalvelu (50% alkuperäisestä hinnasta)",
            "Karttoja myytävänä lähialueista (5-50 gp riippuen laajuudesta)",
        ],
    },

    # ========================================================================
    # BLACKSMITHS / WEAPON SHOPS
    # ========================================================================

    "blacksmith_tier1": {
        "name": "Ahjon Lapsi — Kyläseppä",
        "tier": 1,
        "level_range": "1-4",
        "shop_type": "blacksmith",
        "description": (
            "Pieni kyläpaja kuumuudessa hehkuvalla ahjolla. Seppä takoo "
            "maataloustyökaluja, hevosenkenkiä ja yksinkertaisia aseita. "
            "Laatu on kunnollista mutta ei mitään erikoista."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Dagger", "price_gp": 2.0, "qty": 5, "desc": "Lyhyt pistoveitsi, 1d4 piercing. Finesse, light, thrown (20/60)."},
            {"name": "Handaxe", "price_gp": 5.0, "qty": 3, "desc": "Yksikätinen kirves, 1d6 slashing. Light, thrown (20/60)."},
            {"name": "Shortsword", "price_gp": 10.0, "qty": 2, "desc": "Lyhyt miekka, 1d6 piercing. Finesse, light."},
            {"name": "Longsword", "price_gp": 15.0, "qty": 2, "desc": "Pitkä miekka, 1d8/1d10 slashing. Versatile."},
            {"name": "Spear", "price_gp": 1.0, "qty": 5, "desc": "Keihäs, 1d6/1d8 piercing. Thrown (20/60), versatile."},
            {"name": "Mace", "price_gp": 5.0, "qty": 2, "desc": "Nuija, 1d6 bludgeoning. Yksinkertainen ja tehokas."},
            {"name": "Shield", "price_gp": 10.0, "qty": 3, "desc": "Puinen tai metallinen kilpi, +2 AC."},
            {"name": "Chain Mail", "price_gp": 75.0, "qty": 1, "desc": "Rengaspanssari, AC 16. Haittaa hiiviskely."},
            {"name": "Scale Mail", "price_gp": 50.0, "qty": 1, "desc": "Suomupanssari, AC 14 + Dex (max 2). Haittaa hiiviskely."},
            {"name": "Leather Armor", "price_gp": 10.0, "qty": 3, "desc": "Nahka-panssari, AC 11 + Dex."},
            {"name": "Arrows (20)", "price_gp": 1.0, "qty": 10, "desc": "20 nuolta jouselle."},
            {"name": "Bolts (20)", "price_gp": 1.0, "qty": 5, "desc": "20 pulttia varsijouselle."},
        ],
        "staff": [
            {"name": "Gunnar Rautanen", "role": "Seppä", "race": "Human", "gender": "Male",
             "appearance": "Harteikas, hikoileva, palaneet käsivarret, valtava vasara",
             "personality": "Vähäpuheinen mutta ylpeä työstään. Kunnioittaa sota-aseiden taitajia.",
             "occupation": "Blacksmith", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Korjaa aseet ja haarniskat (25% hinnasta, 1 päivä)",
            "Teroittaa miekat (5 sp, +1 damage seuraavaan osumaan)",
        ],
    },

    "blacksmith_tier2": {
        "name": "Terässusi — Aseseppä",
        "tier": 2,
        "level_range": "5-10",
        "shop_type": "blacksmith",
        "description": (
            "Tunnettu aseseppä jonka tuotteet ovat haluttuja koko alueella. "
            "Laaja valikoima aseita ja haarniskoja, mukaan lukien joitain "
            "masterwork-tason tuotteita. Seppä on oppinut kääpiöiden tekniikoita."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Greatsword", "price_gp": 50.0, "qty": 2, "desc": "Kaksikätinen suuri miekka, 2d6 slashing. Heavy, two-handed."},
            {"name": "Rapier", "price_gp": 25.0, "qty": 3, "desc": "Florettimiekka, 1d8 piercing. Finesse."},
            {"name": "Battleaxe", "price_gp": 10.0, "qty": 3, "desc": "Taistelukirves, 1d8/1d10 slashing. Versatile."},
            {"name": "Warhammer", "price_gp": 15.0, "qty": 2, "desc": "Sotavasara, 1d8/1d10 bludgeoning. Versatile."},
            {"name": "Halberd", "price_gp": 20.0, "qty": 2, "desc": "Hilpari, 1d10 slashing. Heavy, reach, two-handed."},
            {"name": "Heavy Crossbow", "price_gp": 50.0, "qty": 2, "desc": "Raskas varsijousi, 1d10 piercing. Heavy, two-handed."},
            {"name": "Longbow", "price_gp": 50.0, "qty": 2, "desc": "Pitkäjousi, 1d8 piercing. Heavy, two-handed. Range 150/600."},
            {"name": "Half Plate", "price_gp": 750.0, "qty": 1, "desc": "Puolipanssari, AC 15 + Dex (max 2). Paras keskipanssari."},
            {"name": "Splint Armor", "price_gp": 200.0, "qty": 1, "desc": "Kiskopanssari, AC 17. Haittaa hiiviskely."},
            {"name": "Breastplate", "price_gp": 400.0, "qty": 1, "desc": "Rintapanssari, AC 14 + Dex (max 2). Ei haittaa hiiviskelyä."},
            {"name": "Studded Leather", "price_gp": 45.0, "qty": 3, "desc": "Niitattu nahka, AC 12 + Dex. Paras kevyt panssari."},
            {"name": "Silvered Longsword", "price_gp": 115.0, "qty": 1, "desc": "Hopeoitu pitkä miekka — ohittaa joidenkin olentojen resistanssin."},
            {"name": "Silvered Arrows (10)", "price_gp": 50.5, "qty": 3, "desc": "Hopeakärkisiä nuolia, tehokkaat wereolentoja vastaan."},
            {"name": "Adamantine Arrows (10)", "price_gp": 60.5, "qty": 1, "desc": "Adamantiitikärkiset nuolet — automaattinen kriittinen osuma esineisiin."},
        ],
        "staff": [
            {"name": "Thorin Terässusi", "role": "Mestari-aseseppä", "race": "Dwarf", "gender": "Male",
             "appearance": "Vanha kääpiö, harmaa parta, vahvat kädet, kääpiötaottu esiliina",
             "personality": "Vaativa perfektionisti. Halveksii huonoa työtä. Kunnioittaa taitavia taistelijoita.",
             "occupation": "Master Blacksmith", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
            {"name": "Kira", "role": "Oppipoika", "race": "Human", "gender": "Female",
             "appearance": "Nuori, lihaksikas, nokinen, innostunut",
             "personality": "Innokas oppimaan. Ihailee seikkailijoiden aseita.",
             "occupation": "Apprentice", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Hopeoi aseet (100 gp + aseen hinta, 3 päivää)",
            "Masterwork-tuotteet tilauksesta (+50% hinta, +1 to hit ensimmäisellä iskulla/päivä)",
            "Korjaa maagisia aseita (500 gp, 1 viikko)",
        ],
    },

    "blacksmith_tier3": {
        "name": "Draakon Ahjo — Mestariseppä",
        "tier": 3,
        "level_range": "11-16",
        "shop_type": "blacksmith",
        "description": (
            "Legendaarinen sepän paja jossa ahjo kuumennetaan draakontulella. "
            "Mestari-seppä valmistaa maagisia aseita ja haarniskoja harvoille "
            "ja valituille. Jonotuslista on kuukausia. Laatu on vertaansa vailla."
        ),
        "price_modifier": "expensive",
        "inventory": [
            {"name": "Plate Armor", "price_gp": 1500.0, "qty": 2, "desc": "Täyspanssari, AC 18. Paras haarniska. Heavy, Str 15 vaaditaan."},
            {"name": "+1 Longsword", "price_gp": 1000.0, "qty": 1, "desc": "Maaginen pitkä miekka, +1 to hit ja damage. Uncommon."},
            {"name": "+1 Shield", "price_gp": 1000.0, "qty": 1, "desc": "Maaginen kilpi, +3 AC yhteensä. Uncommon."},
            {"name": "+1 Chain Mail", "price_gp": 1500.0, "qty": 1, "desc": "Maaginen rengaspanssari, AC 17. Uncommon."},
            {"name": "Adamantine Plate Armor", "price_gp": 2500.0, "qty": 1, "desc": "Adamantiittipanssari — ei kriittisiä osumia kantajaan. Uncommon."},
            {"name": "Mithral Half Plate", "price_gp": 1250.0, "qty": 1, "desc": "Mithriili puolipanssari — ei haittaa hiiviskelyä, ei vaadi Str. Uncommon."},
            {"name": "Flame Tongue Greatsword", "price_gp": 5000.0, "qty": 1, "desc": "Liekki-miekka: +2d6 fire damage kun aktivoitu. Rare, attunement."},
        ],
        "staff": [
            {"name": "Mastari Volund", "role": "Legendaarinen seppä", "race": "Fire Genasi", "gender": "Male",
             "appearance": "Punainen iho, tuliset silmät, metalliset tatuoinnit, valtava hahmo",
             "personality": "Ylpeä ja mystinen. Puhuu aseista kuin eläville olennoille.",
             "occupation": "Legendary Blacksmith", "attitude": "neutral",
             "stat_source": "monster:Veteran"},
        ],
        "special_features": [
            "Valmistaa +1 ja +2 maagisia aseita tilauksesta",
            "Adamantiitti- ja mithriilityöt saatavilla",
            "Erityismateriaalit: draakonluuta, elementaalirautaa, taivaanterästä",
            "Voi tulienkestäväksi käsitellä haarniskan (fire resistance, 5000 gp)",
        ],
    },

    # ========================================================================
    # POTION SHOPS / ALCHEMISTS
    # ========================================================================

    "alchemist_tier1": {
        "name": "Yrttimummon Puoti",
        "tier": 1,
        "level_range": "1-4",
        "shop_type": "alchemist",
        "description": (
            "Pieni yrttipuoti joka tuoksuu voimakkaasti kuivatuilta yrtellä ja "
            "mausteita. Kattoon roikkuu sidottuja yrttikimppuja ja hyllyt ovat "
            "täynnä lasipurkkeja mysteerisillä jauhella ja nesteillä."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Potion of Healing", "price_gp": 50.0, "qty": 5, "desc": "Parantaa 2d4+2 HP. Punainen neste."},
            {"name": "Antitoxin", "price_gp": 50.0, "qty": 3, "desc": "Advantage myrkkyjen saving throwiin 1 tunniksi."},
            {"name": "Alchemist's Fire", "price_gp": 50.0, "qty": 3, "desc": "Syttyy palamaan osuessaan — 1d4 fire damage/kierros."},
            {"name": "Acid Vial", "price_gp": 25.0, "qty": 3, "desc": "Happopullo — 2d6 acid damage heitettäessä."},
            {"name": "Healer's Kit", "price_gp": 5.0, "qty": 5, "desc": "Siteitä ja yrttejä — stabiloi kuoleva."},
            {"name": "Perfume (vial)", "price_gp": 5.0, "qty": 2, "desc": "Hieno hajuvesi sosiaalisiin tilanteisiin."},
            {"name": "Herbalism Kit", "price_gp": 5.0, "qty": 2, "desc": "Yrttien keräys- ja käsittelyvälineet."},
        ],
        "staff": [
            {"name": "Mummo Sage", "role": "Yrttimummo", "race": "Human", "gender": "Female",
             "appearance": "Vanha, ryppyinen, terävät silmät, yrttien tuoksu",
             "personality": "Viisas ja mystinen. Puhuu arvoituksin. Tietää paljon luonnosta.",
             "occupation": "Herbalist", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Tunnistaa myrkyt ja yrtit (5 gp)",
            "Valmistaa custom-rohtoja tilauksesta (1d4 päivää)",
            "Myy alueen yrttikartaa (2 gp)",
        ],
    },

    "alchemist_tier2": {
        "name": "Taikajuomien Torni",
        "tier": 2,
        "level_range": "5-10",
        "shop_type": "alchemist",
        "description": (
            "Kaksikerroksinen laboratorio jossa pullot kuplii, putket höyryävät "
            "ja oudot tuoksut leijuvat ilmassa. Alchemisti on oppinut yhdistämään "
            "magiaa ja kemiaa harvinaisiksi taikajuomiksi."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Potion of Healing", "price_gp": 50.0, "qty": 10, "desc": "Parantaa 2d4+2 HP."},
            {"name": "Potion of Greater Healing", "price_gp": 200.0, "qty": 5, "desc": "Parantaa 4d4+4 HP."},
            {"name": "Potion of Fire Resistance", "price_gp": 300.0, "qty": 2, "desc": "Fire resistance 1 tunniksi."},
            {"name": "Potion of Water Breathing", "price_gp": 180.0, "qty": 2, "desc": "Hengitä veden alla 1 tunti."},
            {"name": "Potion of Climbing", "price_gp": 180.0, "qty": 2, "desc": "Climbing speed = walking speed, advantage Athletics kiipeilyyn, 1h."},
            {"name": "Potion of Heroism", "price_gp": 300.0, "qty": 1, "desc": "10 temp HP + bless-efekti 1 tunniksi."},
            {"name": "Potion of Animal Friendship", "price_gp": 200.0, "qty": 2, "desc": "Animal Friendship (DC 13) 24 tunniksi."},
            {"name": "Oil of Slipperiness", "price_gp": 480.0, "qty": 1, "desc": "Freedom of Movement 8 tunniksi tai grease-efekti maahan."},
            {"name": "Antitoxin", "price_gp": 50.0, "qty": 5, "desc": "Advantage myrkky-saving throwiin 1 tunniksi."},
            {"name": "Alchemist's Fire", "price_gp": 50.0, "qty": 5, "desc": "1d4 fire damage per kierros."},
            {"name": "Potion of Growth", "price_gp": 270.0, "qty": 1, "desc": "Enlarge/Reduce (enlarge) 1d4 tuntia."},
        ],
        "staff": [
            {"name": "Alchemisti Fenwick", "role": "Alchemisti", "race": "Gnome", "gender": "Male",
             "appearance": "Pieni, räjähtäneet hiukset, isot silmälasit, tahraiset kädet",
             "personality": "Nerokas mutta hajamielinen. Räjäytyksiä sattuu usein.",
             "occupation": "Alchemist", "attitude": "friendly",
             "stat_source": "monster:Mage"},
        ],
        "special_features": [
            "Tilaa räätälöityjä taikajuomia (1-2 viikkoa, kaksinkertainen hinta)",
            "Tunnistaa maagisia nesteitä (25 gp, 1 tunti)",
            "Myrkky-analyysi (25 gp, tunnistaa myrkyn ja vastalääkkeen)",
        ],
    },

    # ========================================================================
    # MAGIC SHOPS / ENCHANTER
    # ========================================================================

    "magic_shop_tier2": {
        "name": "Mystiikan Makasiini",
        "tier": 2,
        "level_range": "5-10",
        "shop_type": "enchanter",
        "description": (
            "Mystinen kauppa sinisellä maagisella valolla. Lasivitriinit täynnä "
            "hohtavia esineitä ja ilmassa leijuu maaginen energia. Myyjä on "
            "kokenut velho joka tuntee maagisten esineiden salat."
        ),
        "price_modifier": "expensive",
        "inventory": [
            {"name": "Bag of Holding", "price_gp": 4000.0, "qty": 1, "desc": "Maaginen laukku joka mahtuu 500 lb / 64 kuutiojalkaa. Painaa aina 15 lb. Uncommon."},
            {"name": "Cloak of Protection", "price_gp": 3500.0, "qty": 1, "desc": "+1 AC ja saving throweihin. Uncommon, attunement."},
            {"name": "Goggles of Night", "price_gp": 1500.0, "qty": 1, "desc": "Darkvision 60 ft. Uncommon."},
            {"name": "Ring of Warmth", "price_gp": 1000.0, "qty": 1, "desc": "Cold resistance + comfortable -50°F asti. Uncommon, attunement."},
            {"name": "Immovable Rod", "price_gp": 5000.0, "qty": 1, "desc": "Painaa nappia → liikkumaton ilmassa. Kestää 8000 lb. Uncommon."},
            {"name": "Decanter of Endless Water", "price_gp": 2000.0, "qty": 1, "desc": "Tuottaa rajattomasti makeaa vettä kolmessa tilassa. Uncommon."},
            {"name": "Driftglobe", "price_gp": 750.0, "qty": 2, "desc": "Hohtava pallo — Light tai Daylight 1/päivä. Uncommon."},
            {"name": "Wand of Magic Detection", "price_gp": 1500.0, "qty": 1, "desc": "Detect Magic 3 chargella/päivä. Uncommon."},
            {"name": "Pearl of Power", "price_gp": 6000.0, "qty": 1, "desc": "Palauttaa yhden 3. tason tai alemman spell slotin. Uncommon, attunement."},
            {"name": "Spell Scroll (1st level)", "price_gp": 75.0, "qty": 3, "desc": "Kertakäyttöinen käärö 1. tason loitsulle."},
            {"name": "Spell Scroll (2nd level)", "price_gp": 200.0, "qty": 2, "desc": "Kertakäyttöinen käärö 2. tason loitsulle."},
            {"name": "Spell Scroll (3rd level)", "price_gp": 500.0, "qty": 1, "desc": "Kertakäyttöinen käärö 3. tason loitsulle."},
        ],
        "staff": [
            {"name": "Archon Vaaleansininen", "role": "Enchantteri", "race": "High Elf", "gender": "Male",
             "appearance": "Pitkä, vanha haltija, hopeahiukset, siniset silmät jotka hohtavat",
             "personality": "Rauhallinen ja mystinen. Puhuu hitaasti ja painokkaasti.",
             "occupation": "Enchanter", "attitude": "neutral",
             "stat_source": "monster:Mage"},
        ],
        "special_features": [
            "Tunnistaa maagisia esineitä (Identify, 20 gp)",
            "Tilaa uncommon-tason maagisia esineitä (1d4 viikkoa)",
            "Maagisten esineiden vaihtopalvelu (vaihda uncommon ↔ uncommon)",
            "Enchantoi aseen +1 ominaisuudella (1500 gp + 1 viikko, vaatii ase)",
        ],
    },

    "magic_shop_tier3": {
        "name": "Arkaanitornin Aarrekammio",
        "tier": 3,
        "level_range": "11-16",
        "shop_type": "enchanter",
        "description": (
            "Velhokoulun alainen maagisten esineiden kauppa, täynnä harvinaisia "
            "ja voimakkaita artefakteja. Jokaisella esineellä on turvasuojaus "
            "ja vain luotetut asiakkaat pääsevät katsomaan kalleimpia esineitä."
        ),
        "price_modifier": "very_expensive",
        "inventory": [
            {"name": "+2 Weapon (any)", "price_gp": 10000.0, "qty": 1, "desc": "+2 to hit ja damage mihin tahansa aseeseen. Rare, attunement."},
            {"name": "+2 Shield", "price_gp": 6000.0, "qty": 1, "desc": "+4 AC yhteensä. Rare."},
            {"name": "Cloak of Displacement", "price_gp": 12000.0, "qty": 1, "desc": "Illuusio saa hyökkäykset disadvantagella kunnes osut. Rare, attunement."},
            {"name": "Ring of Protection", "price_gp": 8000.0, "qty": 1, "desc": "+1 AC ja saving throweihin. Rare, attunement."},
            {"name": "Amulet of Health", "price_gp": 8000.0, "qty": 1, "desc": "Con nousee 19:ään. Rare, attunement."},
            {"name": "Boots of Speed", "price_gp": 8000.0, "qty": 1, "desc": "Tuplaa walking speed bonus actionilla, 10 min/päivä. Rare, attunement."},
            {"name": "Staff of Healing", "price_gp": 13000.0, "qty": 1, "desc": "10 chargea — Cure Wounds, Lesser Restoration, Mass Cure. Rare, attunement (cleric/druid/bard)."},
            {"name": "Wand of Fireballs", "price_gp": 16000.0, "qty": 1, "desc": "7 chargea Fireball. Rare, attunement (spellcaster)."},
            {"name": "Spell Scroll (5th level)", "price_gp": 2500.0, "qty": 2, "desc": "Kertakäyttöinen käärö 5. tason loitsulle."},
        ],
        "staff": [
            {"name": "Arkkimaagi Isolde", "role": "Kaupan johtaja", "race": "Human", "gender": "Female",
             "appearance": "Keski-ikäinen, viisaat silmät, maaginen sinetti otsassa",
             "personality": "Ankara mutta reilu. Vaatii kunnioitusta maagisia esineitä kohtaan.",
             "occupation": "Archmage Merchant", "attitude": "neutral",
             "stat_source": "monster:Archmage"},
        ],
        "special_features": [
            "Tunnistaa kaikki maagisten esineet (50 gp per esine)",
            "Kirouksien poisto maagisista esineistä (500-5000 gp riippuen voimakkuudesta)",
            "Tilaa rare-tason esineitä (1d4+1 viikkoa, ennakkomaksu)",
            "Maagisten esineiden huutokauppa kerran kuussa",
        ],
    },

    # ========================================================================
    # CLOTHING / JEWELER
    # ========================================================================

    "clothier_tier1": {
        "name": "Lankakerän Ompelimo",
        "tier": 1,
        "level_range": "1-4",
        "shop_type": "clothier",
        "description": (
            "Pieni ompelimo ja kangaskauppa. Valmistaa ja korjaa vaatteita "
            "tavallisille kansalaisille ja seikkailijoille. Valikoimassa myös "
            "matkaviittoja ja suojavaatteita."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Traveler's Clothes", "price_gp": 2.0, "qty": 5, "desc": "Kestävät matkavaatteet: saappaat, housut, paita, viitta."},
            {"name": "Common Clothes", "price_gp": 0.5, "qty": 10, "desc": "Tavalliset vaatteet: paita, housut, vyö, kengät."},
            {"name": "Fine Clothes", "price_gp": 15.0, "qty": 2, "desc": "Hienot vaatteet aatelisten piireihin."},
            {"name": "Costume Clothes", "price_gp": 5.0, "qty": 3, "desc": "Naamiaispuku tai rooliasu."},
            {"name": "Cloak (heavy)", "price_gp": 1.0, "qty": 5, "desc": "Paksu viitta sateelta ja tuulelta suojaava."},
            {"name": "Robes", "price_gp": 1.0, "qty": 5, "desc": "Kaavut velhon tai papin tarpeisiin."},
            {"name": "Disguise Kit", "price_gp": 25.0, "qty": 1, "desc": "Naamioitumisvälineet: meikit, peruukit, vaatteet."},
        ],
        "staff": [
            {"name": "Madame Silkkinen", "role": "Ompelija", "race": "Halfling", "gender": "Female",
             "appearance": "Pieni, tarkat silmät, aina neula kädessä, silkkihuivi",
             "personality": "Tarkkasilmäinen ja juoruileva. Tietää kaikkien salaisuudet.",
             "occupation": "Tailor", "attitude": "friendly",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Korjaa vaatteita (5 cp - 5 sp riippuen vahingosta)",
            "Valmistaa mittatilauspukuja (2-7 päivää, kaksinkertainen hinta)",
        ],
    },

    "jeweler_tier2": {
        "name": "Kultasepän Kultala",
        "tier": 2,
        "level_range": "5-10",
        "shop_type": "jeweler",
        "description": (
            "Hieno kultasepänliike lasivitriineillä täynnä kimaltelevaa kultaa, "
            "hopeaa ja jalokiviä. Mestari-kultaseppä valmistaa koruja, sinettpitejä "
            "ja taivaallisen kauniita esineitä."
        ),
        "price_modifier": "expensive",
        "inventory": [
            {"name": "Gold Ring", "price_gp": 25.0, "qty": 5, "desc": "Yksinkertainen kultasormus."},
            {"name": "Silver Necklace", "price_gp": 50.0, "qty": 3, "desc": "Hopeinen kaulakoru."},
            {"name": "Gold Necklace", "price_gp": 250.0, "qty": 2, "desc": "Kultainen kaulakoru jalokivikoristeilla."},
            {"name": "Signet Ring", "price_gp": 5.0, "qty": 5, "desc": "Sinettisoimaus — voi painaa sinettivahaan."},
            {"name": "Gemstone (50 gp)", "price_gp": 50.0, "qty": 5, "desc": "Jalokivi: ametisti, jadi, zirkoni tai vastaava."},
            {"name": "Gemstone (100 gp)", "price_gp": 100.0, "qty": 3, "desc": "Jalokivi: granaatti, opaali, topaasi tai vastaava."},
            {"name": "Gemstone (500 gp)", "price_gp": 500.0, "qty": 1, "desc": "Jalokivi: safiiri, rubiini, smaragdi tai vastaava."},
            {"name": "Crown (simple)", "price_gp": 500.0, "qty": 1, "desc": "Yksinkertainen kulta- tai hopeakruunu."},
        ],
        "staff": [
            {"name": "Mestari Aurum", "role": "Kultaseppä", "race": "Gnome", "gender": "Male",
             "appearance": "Pieni, luupit otsalla, kultaiset sormukset joka sormessa",
             "personality": "Intohimoinen kauniista esineistä. Arvioi kaiken arvon kultana.",
             "occupation": "Jeweler", "attitude": "neutral",
             "stat_source": "monster:Commoner"},
        ],
        "special_features": [
            "Jalokivien arviointi (5 gp, tarkka hinta-arvio)",
            "Valmistaa tilauskoruja (1d6 päivää, materiaali + 50% työ)",
            "Ostaa jalokiviä 80% markkinahinnasta",
        ],
    },

    # ========================================================================
    # TEMPLE / RELIGIOUS GOODS
    # ========================================================================

    "temple_shop_tier1": {
        "name": "Temppelin Puoti",
        "tier": 1,
        "level_range": "1-4",
        "shop_type": "general_store",
        "description": (
            "Temppelin yhteydessä toimiva pieni kauppa pyhillä esineillä ja "
            "parantamistuotteilla. Tuotto menee temppelin ylläpitoon."
        ),
        "price_modifier": "normal",
        "inventory": [
            {"name": "Holy Water", "price_gp": 25.0, "qty": 10, "desc": "Pyhitetty vesi — 2d6 radiant damage undead/fiend."},
            {"name": "Healer's Kit", "price_gp": 5.0, "qty": 5, "desc": "10 käyttöä — stabiloi kuoleva."},
            {"name": "Potion of Healing", "price_gp": 50.0, "qty": 5, "desc": "Parantaa 2d4+2 HP."},
            {"name": "Holy Symbol (amulet)", "price_gp": 5.0, "qty": 3, "desc": "Pyhä symboli riipuksena."},
            {"name": "Holy Symbol (emblem)", "price_gp": 5.0, "qty": 3, "desc": "Pyhä symboli kilpeen kiinnitettynä."},
            {"name": "Candle", "price_gp": 0.01, "qty": 50, "desc": "Kynttilä — 5 ft valo 1 tunniksi."},
            {"name": "Incense", "price_gp": 0.01, "qty": 20, "desc": "Suitsuke meditaatioon ja rituaaleihin."},
        ],
        "staff": [
            {"name": "Sisar Miriam", "role": "Temppelin kauppias", "race": "Human", "gender": "Female",
             "appearance": "Rauhallinen, valkoinen kaapu, pyhä symboli kaulassa",
             "personality": "Lempeä ja avulias. Antaa neuvoja ilmaiseksi.",
             "occupation": "Priestess", "attitude": "friendly",
             "stat_source": "monster:Priest"},
        ],
        "special_features": [
            "Parantamispalvelut saatavilla (Cure Wounds 10 gp, Lesser Restoration 40 gp)",
            "Siunaukset matkaan (Bless-rituaali ilmaiseksi lahjoitusta vastaan)",
            "Undead-suojausetsimet (Protection from Evil 50 gp rituaali)",
        ],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_shop_template(template_key: str) -> Optional[dict]:
    """Get a shop template by key."""
    return SHOP_TEMPLATES.get(template_key)


def get_shop_templates_by_tier(tier: int) -> List[dict]:
    """Get all shop templates for a given tier (1-4)."""
    return [t for t in SHOP_TEMPLATES.values() if t["tier"] == tier]


def get_shop_templates_by_type(shop_type: str) -> List[dict]:
    """Get all shop templates for a given shop type."""
    return [t for t in SHOP_TEMPLATES.values() if t["shop_type"] == shop_type]


def get_all_shop_template_names() -> Dict[str, str]:
    """Get dict of template_key -> display name."""
    return {k: f"{v['name']} (Tier {v['tier']})" for k, v in SHOP_TEMPLATES.items()}


def apply_shop_template(world, parent_location_id: str, template: dict,
                        custom_name: str = "") -> dict:
    """
    Apply a shop template to the world, creating location and NPCs.

    Returns dict with created IDs: {"location_id": ..., "npc_ids": [...]}
    """
    from data.world import add_location, add_npc, ShopItem

    name = custom_name or template["name"]
    loc = add_location(
        world, name,
        location_type="shop",
        parent_id=parent_location_id,
        description=template["description"],
    )
    loc.tags = [f"tier{template['tier']}", template["shop_type"]]

    # Add special features to notes
    if template.get("special_features"):
        notes_parts = ["Erikoisuudet:"]
        for feat in template["special_features"]:
            notes_parts.append(f"  - {feat}")
        loc.notes = "\n".join(notes_parts)

    # Create staff NPCs
    created_npcs = []
    for i, staff in enumerate(template.get("staff", [])):
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
        npc.tags = [f"tier{template['tier']}", template["shop_type"], staff.get("role", "staff")]
        created_npcs.append(npc.id)

        # First staff member is the shopkeeper
        if i == 0:
            npc.is_shopkeeper = True
            npc.shop_name = name
            npc.shop_type = template["shop_type"]
            npc.price_modifier = template.get("price_modifier", "normal")
            npc.target_party_level = template["tier"] * 4  # Approximate

            for item in template.get("inventory", []):
                npc.shop_items.append(ShopItem(
                    item_name=item["name"],
                    base_price_gp=item["price_gp"],
                    current_price_gp=item["price_gp"],
                    quantity=item.get("qty", -1),
                    notes=item.get("desc", ""),
                ))

    return {"location_id": loc.id, "npc_ids": created_npcs}
