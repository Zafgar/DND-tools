"""Suomenkieliset selitteet taistelun kyvyille, toiminnoille ja ehdoille.

Tarkoitus: pelinjohtaja voi ajaa minkä tahansa NPC:n/hirviön käsin
nopeasti ja oikein näkemällä täsmällisen suomenkielisen selityksen siitä,
miten kukin toiminto/kyky/ehto toimii (osumaheitto, vahinko, pelastus-DC,
ehto, kantama). Käytetään taistelunäkymän työkaluvihjeissä ja
tarjoaa myös AI-ehdotuksen suomeksi.

Puhdas datalogiikka — ei pygamea, joten helppo testata.
"""
from __future__ import annotations

# --------------------------------------------------------------------- #
# Käännöskartat
# --------------------------------------------------------------------- #
DAMAGE_FI = {
    "slashing": "viiltävä", "piercing": "lävistävä", "bludgeoning": "murskaava",
    "fire": "tuli", "cold": "kylmä", "lightning": "salama", "thunder": "jyrinä",
    "acid": "happo", "poison": "myrkky", "necrotic": "nekroottinen",
    "radiant": "säteilevä", "psychic": "psyykkinen", "force": "voima",
}

SAVE_FI = {
    "strength": "Voima (STR)", "str": "Voima (STR)",
    "dexterity": "Ketteryys (DEX)", "dex": "Ketteryys (DEX)",
    "constitution": "Kesto (CON)", "con": "Kesto (CON)",
    "intelligence": "Äly (INT)", "int": "Äly (INT)",
    "wisdom": "Viisaus (WIS)", "wis": "Viisaus (WIS)",
    "charisma": "Karisma (CHA)", "cha": "Karisma (CHA)",
}

ACTION_TYPE_FI = {
    "action": "toiminto", "bonus": "bonustoiminto", "reaction": "reaktio",
    "legendary": "legendaarinen toiminto", "free": "ilmainen toiminto",
}

AOE_FI = {"cone": "kartio", "sphere": "pallo", "line": "linja", "cube": "kuutio"}

SCHOOL_FI = {
    "abjuration": "suojaus (abjuration)",
    "conjuration": "manaus (conjuration)",
    "divination": "ennustus (divination)",
    "enchantment": "lumous (enchantment)",
    "evocation": "loihdinta (evocation)",
    "illusion": "harha (illusion)",
    "necromancy": "kuolonmagia (necromancy)",
    "transmutation": "muuntelu (transmutation)",
}

COMPONENT_FI = {"v": "V (puhuttu)", "s": "S (eleet)", "m": "M (materiaali)"}

LEVEL_FI = {
    0: "loitsuke (cantrip)", 1: "1. tason loitsu", 2: "2. tason loitsu",
    3: "3. tason loitsu", 4: "4. tason loitsu", 5: "5. tason loitsu",
    6: "6. tason loitsu", 7: "7. tason loitsu", 8: "8. tason loitsu",
    9: "9. tason loitsu",
}

TARGETS_FI = {
    "single": "yksi kohde", "aoe": "alue", "self": "itse",
    "all_allies": "kaikki liittolaiset", "all": "kaikki alueella",
}


def _dmg(dtype: str) -> str:
    return DAMAGE_FI.get((dtype or "").lower(), dtype or "")


def _save(ability: str) -> str:
    return SAVE_FI.get((ability or "").lower(), ability or "")


# --------------------------------------------------------------------- #
# Ehtojen suomenkieliset säännöt (PHB liite A)
# --------------------------------------------------------------------- #
CONDITION_HELP_FI = {
    "Banished": "Karkotettu: olento on toisessa ulottuvuudessa ja "
                "toimintakyvytön (poissa ruudukolta). Palaa kun loitsu "
                "päättyy; jos kestää minuutin eikä olento ole tältä "
                "tasolta, se ei palaa.",
    "Blinded": "Sokaistu: ei näe, epäonnistuu näköä vaativat kykytestit. "
               "Hyökkäykset sitä vastaan saavat EDUN, sen omat hyökkäykset "
               "HAITAN.",
    "Charmed": "Hurmattu: ei voi hyökätä hurmaajaa vastaan tai kohdistaa "
               "tähän haitallisia efektejä. Hurmaaja saa EDUN sosiaalisiin "
               "kykytesteihin olentoa kohtaan.",
    "Deafened": "Kuuroutunut: ei kuule ja epäonnistuu kuuloa vaativat "
                "kykytestit.",
    "Exhaustion": "Uupumus (tasot kumuloituvat): 1 = haitta kykytesteihin, "
                  "2 = nopeus puoliintuu, 3 = haitta hyökkäyksiin JA "
                  "pelastusheittoihin, 4 = max-HP puoliintuu, 5 = nopeus 0, "
                  "6 = kuolema.",
    "Frightened": "Peloissaan: HAITTA hyökkäyksiin ja kykytesteihin niin "
                  "kauan kuin pelon lähde on näkökentässä. Ei voi vapaasti "
                  "liikkua lähemmäs pelon lähdettä.",
    "Grappled": "Otteessa: nopeus 0 eikä hyödy nopeusbonuksista. Päättyy "
                "jos ottaja tulee toimintakyvyttömäksi tai kohde siirtyy "
                "ottajan ulottuvilta. HUOM: otteessa+kaatuneena EI voi nousta "
                "ylös (nopeus 0).",
    "Guiding Bolt": "Guiding Bolt -merkki: seuraava hyökkäys tätä olentoa "
                    "vastaan saa EDUN (kertakäyttöinen).",
    "Outlined": "Valaistu (Faerie Fire): kohde hehkuu, jokainen hyökkäys "
                "sitä vastaan saa EDUN eikä se voi hyötyä "
                "näkymättömyydestä.",
    # Nämä kahdeksan asetettiin pelissä ilman merkintää tilataulukossa,
    # joten pelinjohtaja ei nähnyt niistä mitään. Combat audit löysi.
    "Lethargic": "Hasten jälkitila: ei voi liikkua eikä toimia ennen kuin "
                 "seuraava vuoro on ohi. EI ole Incapacitated — "
                 "keskittyminen ja painit säilyvät.",
    "Turned": "Karkotettu: epäkuolleen on paettava karkottajasta niin "
              "kauas kuin pääsee eikä se voi lähestyä 30 jalkaa "
              "lähemmäs. Ei reaktioita; toiminnoksi vain Dash tai "
              "pakoyritys. Päättyy jos se ottaa vahinkoa.",
    "Max HP Reduced": "Osumapistemaksimi laskenut otetun vahingon verran. "
                      "Palautuu vasta pitkällä levolla; jos maksimi "
                      "putoaa nollaan, olento kuolee.",
    "Cursed": "Kirottu: HAITTA kykyheittoihin ja pelastusheittoihin, eikä "
              "olento voi palauttaa osumapisteitä. Remove Curse tai "
              "Greater Restoration poistaa.",
    "Slowed": "Hidastettu: nopeus puolittuu, -2 AC:hen ja DEX-pelastuksiin, "
              "ei reaktioita. Vuorolla joko toiminto TAI bonustoiminto, "
              "ei molempia.",
    "Possessed": "Riivattu: toinen tahto ohjaa kehoa. Olento on "
                 "toimintakyvytön eikä hallitse itseään.",
    "Infernal Wound": "Helvetin haava: olento menettää osumapisteitä joka "
                      "vuoron alussa ja sen maksimi laskee saman verran. "
                      "DC 12 Medicine tai mikä tahansa taikaparannus "
                      "sulkee sen.",
    "Disadvantage": "Haitta: olennon hyökkäysheitot saavat HAITAN kunnes "
                    "vaikutus päättyy.",
    "Incapacitated": "Toimintakyvytön: ei voi tehdä toimintoja eikä "
                     "reaktioita.",
    "Invisible": "Näkymätön: hyökkäykset sitä vastaan saavat HAITAN, sen "
                 "omat hyökkäykset EDUN. Sijainti voidaan silti aavistaa "
                 "äänestä.",
    "Paralyzed": "Halvaantunut: toimintakyvytön, ei voi liikkua/puhua, "
                 "epäonnistuu automaattisesti STR- ja DEX-pelastukset. "
                 "Hyökkäykset saavat EDUN, ja 5 ft sisältä osuma on aina "
                 "KRIITTINEN.",
    "Petrified": "Kivettynyt: muuttunut kiveksi, toimintakyvytön, ei "
                 "tiedosta ympäristöä. Vastustus KAIKKEEN vahinkoon; "
                 "immuuni myrkylle ja sairaudelle; auto-epäonnistuu STR/DEX.",
    "Poisoned": "Myrkytetty: HAITTA hyökkäyksiin ja kykytesteihin.",
    "Prone": "Kaatunut: voi liikkua vain ryömimällä (tuplahinta). HAITTA "
             "omiin hyökkäyksiin. Lähihyökkäykset sitä vastaan saavat EDUN, "
             "kaukohyökkäykset HAITAN. Ylös nouseminen maksaa puolet "
             "nopeudesta.",
    "Restrained": "Sidottu: nopeus 0. Hyökkäykset sitä vastaan saavat EDUN, "
                  "sen omat hyökkäykset HAITAN. HAITTA DEX-pelastuksiin.",
    "Stunned": "Tainnutettu: toimintakyvytön, ei voi liikkua, puhuu "
               "sekavasti. Auto-epäonnistuu STR/DEX-pelastukset. "
               "Hyökkäykset sitä vastaan saavat EDUN.",
    "Unconscious": "Tajuton: toimintakyvytön, ei liiku/puhu, tiedostamaton; "
                   "pudottaa kantamansa ja kaatuu. Auto-epäonnistuu STR/DEX; "
                   "hyökkäykset saavat EDUN ja 5 ft sisältä osuma on aina "
                   "KRIITTINEN.",
    "Lethargic": "Uneliaisuus (Haste päättyi): ei voi liikkua eikä tehdä "
                 "toimintoja seuraavan vuoronsa loppuun asti (nopeus 0, "
                 "toimintakyvytön).",
}


# --------------------------------------------------------------------- #
# Erikoiskykyjen (mechanic) suomenkieliset selitteet
# --------------------------------------------------------------------- #
MECHANIC_HELP_FI = {
    "magic_resistance": "Maagivastus: ETU pelastusheittoihin loitsuja ja "
                        "muita maagisia efektejä vastaan.",
    "mage_slayer": "Maagintappaja: kun 5 ft sisällä oleva loitsii, voit "
                   "reaktiona iskeä. Loitsijalla on HAITTA "
                   "keskittymisheittoihin, jotka tämä olento aiheuttaa.",
    "magic_weapons": "Maagiset aseet: sen hyökkäykset lasketaan maagisiksi "
                     "(ohittaa ei-maagisen vahingon vastustuksen).",
    "fey_ancestry": "Fey-perimä: ETU hurmausta (Charmed) vastaan; magia ei "
                    "voi nukuttaa.",
    "gnome_cunning": "Gnomin oveluus: ETU INT-, WIS- ja CHA-pelastuksiin "
                     "magiaa vastaan.",
    "halfling_nimbleness": "Puolituisen notkeus: voi liikkua suuremman "
                           "olennon lävitse.",
    "brave": "Urhea: ETU pelastusheittoihin pelkoa (Frightened) vastaan.",
    "lucky": "Onnekas: voi heittää 1:n uudelleen hyökkäys-, pelastus- tai "
             "kykytestinopalla.",
    "channel_divinity": "Channel Divinity: papin/paladiinin pyhä voima "
                        "(esim. karkota epäkuolleet) — kertakäyttö per lepo.",
}

# Ominaisuuksien nimien avainsanat → suomiselite (kun mechanic puuttuu)
FEATURE_KEYWORD_FI = [
    ("legendary resistance", "Legendaarinen vastus: kun epäonnistut "
     "pelastusheitossa, voit valita onnistuvasi sen sijaan (rajattu määrä "
     "per päivä)."),
    ("sneak attack", "Salahyökkäys: kerran vuorossa ylimääräistä vahinkoa, "
     "kun sinulla on ETU tai liittolainen on 5 ft kohteesta (eikä sinulla "
     "ole haittaa); vaatii finesse- tai kaukoaseen."),
    ("pack tactics", "Laumataktiikka: ETU hyökkäykseen, jos liittolainen on "
     "5 ft kohteesta eikä ole toimintakyvytön."),
    ("action surge", "Action Surge: yksi ylimääräinen toiminto vuorollasi "
     "(kertakäyttö per lepo)."),
    ("multiattack", "Multiattack: tekee useita hyökkäyksiä yhdellä "
     "toiminnolla (ks. määrä)."),
    ("regeneration", "Regeneraatio: palauttaa kestopisteitä vuoronsa alussa "
     "(usein estyy tietyltä vahinkotyypiltä)."),
    ("rampage", "Rampage: kun pudottaa olennon, voi bonustoimintona liikkua "
     "ja purra uudelleen."),
    ("charge", "Rynnäkkö: jos liikkuu suoraan väh. 10 ft ennen iskua, "
     "ylimääräistä vahinkoa ja kohde voi kaatua/työntyä."),
    ("reckless", "Holtiton hyökkäys: hyökkää EDULLA, mutta hyökkäykset sitä "
     "vastaan saavat myös EDUN sen seuraavaan vuoroon asti."),
    ("divine smite", "Divine Smite: osuessa lähiaseella voi polttaa "
     "loitsupaikan lisävahinkoon (säteilevä; +1d8 epäkuolleita/pahoja "
     "vastaan)."),
    ("rage", "Raivo: bonustoiminto; lisävahinko lähi-STR-iskuihin ja "
     "vastustus murskaavaan/lävistävään/viiltävään."),
    ("parry", "Torjunta: reaktio, joka lisää AC:tä yhtä näkemäänsä "
     "lähihyökkäystä vastaan."),
    ("spellcasting", "Loitsiminen: katso loitsulista, loitsu-DC ja "
     "osumabonus stat-lehdeltä."),
    ("immutable form", "Muuttumaton muoto: immuuni efekteille, jotka "
     "muuttaisivat sen muotoa."),
    ("siege monster", "Piirityshirviö: tekee kaksinkertaisen vahingon "
     "esineille ja rakenteille."),
    ("keen", "Terävät aistit: ETU havainnointiin (haju/kuulo/näkö)."),
    ("aura", "Aura: jatkuva vaikutus tietyllä säteellä (ks. teksti)."),
]


# --------------------------------------------------------------------- #
# Julkiset selittäjät
# --------------------------------------------------------------------- #
def explain_condition(name: str) -> str:
    """Palauta ehdon suomenkielinen sääntöselite."""
    return CONDITION_HELP_FI.get(name, "")


def explain_feature(feature) -> str:
    """Palauta piirteen suomenkielinen selite. Käyttää ensin mechanic-
    avainta, sitten nimen avainsanoja, sitten alkuperäistä kuvausta."""
    mech = getattr(feature, "mechanic", "") or ""
    if mech in MECHANIC_HELP_FI:
        base = MECHANIC_HELP_FI[mech]
    else:
        name_l = (getattr(feature, "name", "") or "").lower()
        base = ""
        for kw, txt in FEATURE_KEYWORD_FI:
            if kw in name_l:
                base = txt
                break
        if not base:
            base = getattr(feature, "description", "") or "(ei selitettä)"
    # Käyttökerrat / recharge
    extra = []
    upd = getattr(feature, "uses_per_day", -1)
    if isinstance(upd, int) and upd > 0:
        extra.append(f"{upd}/päivä")
    rech = getattr(feature, "recharge", "") or ""
    if rech:
        extra.append(f"lataus {rech}")
    if extra:
        base += f"  [{', '.join(extra)}]"
    return base


def explain_action(action) -> str:
    """Palauta toiminnon täsmällinen suomenkielinen käyttöohje: tyyppi,
    kantama, osumaheitto, vahinko, pelastus, ehto, AoE."""
    parts = []
    atype = ACTION_TYPE_FI.get(getattr(action, "action_type", "action"),
                               "toiminto")

    # Multiattack
    if getattr(action, "is_multiattack", False):
        n = getattr(action, "multiattack_count", 1)
        tgts = getattr(action, "multiattack_targets", []) or []
        seg = f"Multiattack ({atype}): tee {n} hyökkäystä"
        if tgts:
            seg += f" — {', '.join(tgts)}"
        seg += " tällä toiminnolla."
        return seg

    parts.append(f"Tyyppi: {atype}.")

    # Kantama / ulottuvuus
    rng = getattr(action, "range", 5) or 5
    reach = getattr(action, "reach", 5)
    if rng and rng > 5:
        long_r = getattr(action, "long_range", 0)
        parts.append(f"Kantama {rng} ft" +
                     (f" (pitkä {long_r} ft, HAITTA)." if long_r else "."))
    else:
        parts.append(f"Ulottuvuus {reach} ft.")

    # Osumaheitto + vahinko
    ab = getattr(action, "attack_bonus", 0)
    dice = getattr(action, "damage_dice", "") or ""
    dbon = getattr(action, "damage_bonus", 0)
    dtype = _dmg(getattr(action, "damage_type", ""))
    if ab:
        parts.append(f"Osumaheitto: 1d20+{ab} vs kohteen AC.")
        if dice:
            dmg = dice + (f"+{dbon}" if dbon else "")
            parts.append(f"Osuma: {dmg} {dtype} vahinkoa "
                         f"(krit 20:llä = vahinkonopat tuplana).")

    # Pelastusheittopohjainen (ei osumabonusta)
    cdc = getattr(action, "condition_dc", 0)
    csave = getattr(action, "condition_save", "")
    if not ab and dice and cdc and csave:
        parts.append(f"Pelastus: kohde heittää {_save(csave)} DC {cdc}. "
                     f"Epäonnistuessa {dice} {dtype} vahinkoa, onnistuessa "
                     f"puolet.")
    elif not ab and dice:
        parts.append(f"Vahinko: {dice} {dtype}.")

    # AoE
    aoe = getattr(action, "aoe_radius", 0)
    shape = AOE_FI.get(getattr(action, "aoe_shape", ""), "")
    if aoe:
        parts.append(f"Alue: {aoe} ft {shape}".strip() + ".")

    # Ehto
    cond = getattr(action, "applies_condition", "")
    if cond:
        c = f"Aiheuttaa tilan: {cond}"
        fi = CONDITION_HELP_FI.get(cond, "")
        if cdc and csave:
            c += f" (DC {cdc} {_save(csave)})"
        c += "."
        if fi:
            c += f" → {fi}"
        parts.append(c)

    return " ".join(parts)


def explain_spell(spell, caster=None) -> str:
    """Loitsun koko sääntöselite suomeksi, riveittäin.

    Pöydässä tarvitaan aina samat asiat: mikä taso, mikä toiminto, mihin
    yltää, ketä se osuu, mitä heitetään, mitä tapahtuu onnistuessa ja
    epäonnistuessa, kestääkö se keskittymistä ja kuinka kauan. Ne ovat
    tässä yhtenä listana eikä hajallaan englanninkielisessä
    kuvauskentässä.
    """
    L = []
    lvl = getattr(spell, "level", 0) or 0
    head = LEVEL_FI.get(lvl, f"{lvl}. tason loitsu")
    # Koulukuntaa ei näytetä: kenttä on oletusarvoltaan "Evocation" eikä
    # sitä ole täytetty loitsukirjastoon, joten se väittäisi Hold
    # Personin olevan loihdintaa. Väärä tieto on huonompi kuin ei tietoa.
    if getattr(spell, "ritual", False):
        head += " · rituaali (10 min lisää, ei loitsupaikkaa)"
    L.append(head)

    atype = ACTION_TYPE_FI.get(getattr(spell, "action_type", "action"),
                               "toiminto")
    line = f"Käyttö: {atype}"
    comps = (getattr(spell, "components", "") or "").replace(" ", "")
    if comps:
        got = [COMPONENT_FI.get(c.lower(), c)
               for c in comps.split(",") if c]
        line += " · komponentit " + ", ".join(got)
    L.append(line)

    rng = getattr(spell, "range", 0) or 0
    tgt = TARGETS_FI.get(getattr(spell, "targets", "single"),
                         getattr(spell, "targets", ""))
    L.append(f"Kantama: {'itse' if rng == 0 else f'{rng} ft'} · kohde: {tgt}")

    aoe = getattr(spell, "aoe_radius", 0) or 0
    if aoe:
        shape = AOE_FI.get(getattr(spell, "aoe_shape", ""), "alue")
        L.append(f"Alue: {aoe} ft {shape} — kaikki alueella osuu, myös "
                 f"omat, ellei loitsu erikseen säästä heitä")

    dice = getattr(spell, "damage_dice", "") or ""
    dtype = _dmg(getattr(spell, "damage_type", ""))
    save = getattr(spell, "save_ability", "") or ""
    if dice and save:
        half = getattr(spell, "half_on_save", True)
        dc = getattr(spell, "save_dc_fixed", 0)
        dcs = f"DC {dc}" if dc else "DC = loitsijan loitsu-DC"
        L.append(f"Pelastus: {_save(save)}, {dcs}")
        L.append(f"Epäonnistuu: {dice} {dtype} vahinkoa" +
                 (f" · onnistuu: puolet" if half
                  else " · onnistuu: ei vaikutusta"))
    elif dice:
        fixed = getattr(spell, "attack_bonus_fixed", 0)
        if fixed or getattr(spell, "targets", "") == "single":
            L.append("Osumaheitto: 1d20 + loitsuhyökkäysbonus vs kohteen AC "
                     "(luonnollinen 20 = vahinkonopat tuplana)")
        L.append(f"Vahinko: {dice} {dtype}")

    scaling = getattr(spell, "damage_scaling", "") or ""
    if scaling:
        L.append(f"Korkeammalla paikalla: +{scaling} jokaista tasoa kohti "
                 f"perustason yli")

    heals = getattr(spell, "heals", "") or ""
    if heals:
        L.append(f"Parannus: {heals} osumapistettä")

    cond = getattr(spell, "applies_condition", "") or ""
    if cond:
        line = f"Aiheuttaa tilan: {cond}"
        if getattr(spell, "condition_on_save", False):
            line += " (myös onnistuneella pelastuksella)"
        L.append(line)
        fi = CONDITION_HELP_FI.get(cond, "")
        if fi:
            L.append(f"   → {fi}")
        if getattr(spell, "repeat_save", True) and save:
            L.append(f"   → kohde saa uuden {_save(save)}-pelastuksen "
                     f"jokaisen vuoronsa lopussa")

    bd = getattr(spell, "bonus_damage_dice", "") or ""
    if bd:
        bt = _dmg(getattr(spell, "bonus_damage_type", ""))
        L.append(f"Merkintä: osumat tähän kohteeseen tekevät +{bd}"
                 + (f" {bt}" if bt else "") + " vahinkoa")

    summon = getattr(spell, "summon_name", "") or ""
    if summon:
        shp = getattr(spell, "summon_hp", 0)
        sdd = getattr(spell, "summon_damage_dice", "") or ""
        line = f"Kutsuu: {summon}"
        if shp:
            line += f" ({shp} hp, AC {getattr(spell, 'summon_ac', 10)})"
        if sdd:
            line += f", hyökkäys {sdd} " \
                    f"{_dmg(getattr(spell, 'summon_damage_type', ''))}"
        L.append(line)

    terr = getattr(spell, "creates_terrain", "") or ""
    if terr:
        L.append(f"Jättää kentälle: {terr} — vaikuttaa siihen astuviin "
                 f"kunnes loitsu päättyy")

    if getattr(spell, "concentration", False):
        L.append("KESKITTYMINEN: päättyy jos otat vahinkoa etkä läpäise "
                 "CON-pelastusta (DC 10 tai puolet vahingosta, kumpi "
                 "suurempi), tai jos aloitat uuden keskittymisloitsun")
    dur = getattr(spell, "duration", "") or ""
    if dur:
        L.append(f"Kesto: {dur}")
    if getattr(spell, "innate", False):
        n = getattr(spell, "innate_uses_per_day", -1)
        L.append("Synnynnäinen: ei kuluta loitsupaikkaa"
                 + (f" ({n}/päivä)" if n and n > 0 else " (rajattomasti)"))

    desc = (getattr(spell, "description", "") or "").strip()
    if desc:
        L.append("")
        L.append(desc)
    return "\n".join(L)


RARITY_FI = {
    "common": "tavallinen", "uncommon": "epätavallinen", "rare": "harvinainen",
    "very_rare": "hyvin harvinainen", "legendary": "legendaarinen",
    "artifact": "artefakti",
}

SLOT_FI = {
    "main_hand": "pääkäsi", "off_hand": "toinen käsi", "armor": "haarniska",
    "shield": "kilpi", "helm": "kypärä", "cloak": "viitta",
    "amulet": "amuletti", "ring1": "sormus 1", "ring2": "sormus 2",
    "gloves": "hanskat", "boots": "saappaat", "belt": "vyö",
}


def explain_item(item) -> str:
    """Esineen selite suomeksi: mihin se menee, mitä se tekee ja mitä sen
    käyttäminen vaatii."""
    L = [f"{getattr(item, 'name', '?')} — "
         f"{RARITY_FI.get(getattr(item, 'rarity', ''), getattr(item, 'rarity', ''))}"]
    slot = SLOT_FI.get(getattr(item, "slot", ""), getattr(item, "slot", ""))
    if slot:
        L.append(f"Paikka: {slot}"
                 + (" · varustettuna" if getattr(item, "equipped", False)
                    else " · ei varustettuna"))
    if getattr(item, "requires_attunement", False):
        L.append("Vaatii virittämisen (attunement)"
                 + (" — viritetty" if getattr(item, "attuned", False)
                    else " — EI viritetty, maagiset ominaisuudet eivät toimi"))
    wd = getattr(item, "weapon_damage_dice", "") or ""
    if wd:
        L.append(f"Vahinko: {wd} "
                 f"{_dmg(getattr(item, 'weapon_damage_type', ''))}"
                 + (f" · kantama {item.weapon_range} ft"
                    if getattr(item, "weapon_range", 5) > 5 else ""))
    props = getattr(item, "weapon_properties", None) or []
    if props:
        L.append("Ominaisuudet: " + ", ".join(props))
    if getattr(item, "base_ac", 0):
        L.append(f"Perus-AC: {item.base_ac}"
                 + (f" (DEX enintään +{item.max_dex_bonus})"
                    if getattr(item, "max_dex_bonus", -1) >= 0 else ""))
    if getattr(item, "ac_bonus", 0):
        L.append(f"AC-bonus: +{item.ac_bonus}")
    if getattr(item, "stealth_disadvantage", False):
        L.append("Haitta hiiviskelyyn (Stealth)")
    if getattr(item, "strength_required", 0):
        L.append(f"Vaatii STR {item.strength_required} — muuten nopeus -10 ft")
    if getattr(item, "heals", ""):
        L.append(f"Parantaa: {item.heals}")
    if getattr(item, "damage_dice", ""):
        L.append(f"Vahinko käytettäessä: {item.damage_dice}")
    if getattr(item, "applies_condition", ""):
        cond = item.applies_condition
        L.append(f"Aiheuttaa tilan: {cond}")
        fi = CONDITION_HELP_FI.get(cond, "")
        if fi:
            L.append(f"   → {fi}")
    if getattr(item, "buff", ""):
        L.append(f"Vaikutus: {item.buff}")
    uses = getattr(item, "uses", -1)
    if isinstance(uses, int) and uses > 0:
        L.append(f"Käyttökertoja jäljellä: {uses}")
    desc = (getattr(item, "description", "") or "").strip()
    if desc:
        L.append("")
        L.append(desc)
    return "\n".join(L)


def explain_any(thing, kind="") -> str:
    """Yksi sisäänkäynti kaikelle: loitsu, toiminto, piirre tai ehto.

    Käyttöliittymä ei aina tiedä kumpaa sillä on kädessä, ja ilman tätä
    puolet hover-selitteistä jäi englanninkieliseksi raakadataksi.
    """
    if isinstance(thing, str):
        return explain_condition(thing) or thing
    if kind == "spell" or hasattr(thing, "concentration"):
        return explain_spell(thing)
    if kind == "action" or hasattr(thing, "is_multiattack"):
        return explain_action(thing)
    if kind == "feature" or hasattr(thing, "feature_type"):
        return explain_feature(thing)
    return str(getattr(thing, "description", "") or thing)


# --------------------------------------------------------------------- #
# AI-ehdotus suomeksi
# --------------------------------------------------------------------- #
def _hp_pct(e) -> float:
    mx = getattr(e, "max_hp", 0) or 0
    return (getattr(e, "hp", 0) / mx) if mx > 0 else 0.0


def _threat_score(e) -> float:
    """Karkea uhka-arvo: kuinka vaarallinen olento on juuri nyt."""
    try:
        cr = getattr(e.stats, "challenge_rating", 0) or 0
    except Exception:
        cr = 0
    lvl = getattr(getattr(e, "stats", None), "character_level", 0) or 0
    caster = 1.5 if getattr(getattr(e, "stats", None), "spell_slots", None) else 1.0
    conc = 1.3 if getattr(e, "concentrating_on", None) else 1.0
    return (cr + lvl) * caster * conc


def target_rationale_fi(target, battle) -> str:
    """Selitä suomeksi miksi juuri tämä kohde on paras valinta — katsoen
    koko kenttää (matalin HP, loitsija/keskittyjä, suurin uhka)."""
    if target is None:
        return ""
    reasons = []
    pct = _hp_pct(target)
    if pct <= 0.35:
        reasons.append("matala HP (viimeistely irrottaa vihollisen toiminnasta)")
    if getattr(target, "concentrating_on", None):
        sp = getattr(target.concentrating_on, "name", "loitsu")
        reasons.append(f"keskittyy loitsuun ({sp}) — vahinko voi katkaista sen")
    if getattr(getattr(target, "stats", None), "spell_slots", None):
        reasons.append("loitsija (suuri uhka, kannattaa poistaa ajoissa)")
    # Onko tämä kentän vaarallisin vihollinen?
    try:
        foes = [e for e in battle.entities
                if e.is_player != target.is_player and e.hp > 0]
        if foes and target is max(foes, key=_threat_score):
            reasons.append("kentän vaarallisin vastustaja")
    except Exception:
        pass
    if not reasons:
        reasons.append("paras osumatodennäköisyys/vahinko tällä hetkellä")
    return "; ".join(reasons)


# Voittotodennäköisyyden suomennos (pelaajien näkökulmasta)
_PROB_LABEL_FI = [
    (0.85, "pelaajilla ratkaiseva etu — helppo"),
    (0.70, "pelaajilla vahva etu"),
    (0.55, "pelaajilla lievä etu"),
    (0.45, "tasainen taisto"),
    (0.30, "pelaajilla lievä alakynsi"),
    (0.15, "pelaajilla vahva alakynsi — vaarallinen"),
    (0.0,  "pelaajille tuhoisa asetelma"),
]


def difficulty_read_fi(battle) -> str:
    """Palauta suomenkielinen vaikeusarvio asetelmalle (voitto-% +
    sanallinen tulkinta). Katsoo koko kenttää."""
    try:
        from engine.win_probability import WinProbabilityCalculator
        res = WinProbabilityCalculator().calculate(battle)
    except Exception:
        return ""
    if not res:
        return ""
    pct = res.get("percentage", 0.0)
    prob = res.get("probability", 0.0)
    label = next(t for thr, t in _PROB_LABEL_FI if prob >= thr)
    return f"Voitto-% (pelaajat): {pct:.0f}% — {label}"


def summarize_ai_plan_fi(plan) -> list:
    """Tiivistä AI:n TurnPlan suomenkielisiksi riveiksi ('mitä AI "
    tekisi'). Palauttaa listan lyhyitä rivejä."""
    if plan is None:
        return ["AI-ehdotus ei saatavilla."]
    if getattr(plan, "skipped", False):
        reason = getattr(plan, "skip_reason", "") or "ei toimintaa"
        return [f"AI ohittaisi vuoron: {reason}"]
    lines = []
    for st in getattr(plan, "steps", []) or []:
        stype = getattr(st, "step_type", "")
        tgt = getattr(st, "target", None)
        tname = getattr(tgt, "name", "") if tgt else ""
        aname = getattr(st, "action_name", "") or ""
        spell = getattr(st, "spell", None)
        sname = getattr(spell, "name", "") if spell else ""
        if stype in ("move", "movement"):
            ft = getattr(st, "movement_ft", 0)
            lines.append(f"Liiku {int(ft)} ft" if ft else "Liiku parempaan asemaan")
        elif stype == "spell":
            lines.append(f"Loitsi {sname or aname}" +
                         (f" → {tname}" if tname else ""))
        elif stype in ("attack", "multiattack", "bonus_attack", "legendary"):
            lines.append(f"Hyökkää: {aname or 'ase'}" +
                         (f" → {tname}" if tname else ""))
        elif stype == "transform":
            lines.append("Muuntaudu (Wild Shape)")
        elif stype == "summon":
            lines.append(f"Kutsu {getattr(st,'summon_name','olento')}")
        else:
            desc = getattr(st, "description", "") or aname or stype
            if desc:
                lines.append(desc)
    return lines or ["AI odottaisi / ei selkeää siirtoa."]
