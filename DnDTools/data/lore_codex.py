"""Lore Codex — Novus Somniumin maailmanlore haettavassa muodossa.

Kampanjan syvä kosmologia (Garrutha, Veru, Tarquvas, Kristallikupu) on
liian laaja litteäksi muistiinpanolistaksi: pöydässä tieto on löydettävä
sekunneissa. Siksi lore on täällä **artikkeleina**, joilla on

  * ``key``      — vakaa tunniste (ristiviittauksiin)
  * ``title``    — otsikko
  * ``category`` — ryhmittely (kosmologia, artefaktit, historia,
                   ryhmittymät, uhat, paikat)
  * ``summary``  — yhden rivin ydin: mitä pelinjohtajan pitää tietää heti
  * ``body``     — täysi teksti kappaleina
  * ``keywords`` — hakusanat (myös suomi/englanti-synonyymit)
  * ``see_also`` — muiden artikkelien keyt
  * ``npc_ids`` / ``location_ids`` — kytkennät maailman NPC:ihin ja
                   paikkoihin, joista pääsee suoraan statlehdelle/kartalle
  * ``spoiler``  — True = pelaajilta salattava (näytetään merkittynä)

``search(query)`` hakee otsikoista, hakusanoista, tiivistelmistä ja
leipätekstistä relevanssijärjestyksessä.
"""
from dataclasses import dataclass, field
from typing import List


CATEGORIES = [
    "kosmologia", "artefaktit", "historia", "ryhmittymät", "uhat", "paikat",
]


@dataclass
class LoreEntry:
    key: str
    title: str
    category: str = "kosmologia"
    summary: str = ""
    body: str = ""
    keywords: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    npc_ids: List[str] = field(default_factory=list)
    location_ids: List[str] = field(default_factory=list)
    spoiler: bool = False


# ===================================================================== #
# KOSMOLOGIA — maailman perusta
# ===================================================================== #
CODEX: List[LoreEntry] = [
    LoreEntry(
        key="garrutha", title="Maailmantitaani Garrutha",
        category="kosmologia", spoiler=True,
        summary="Koko Novus Somniumin olemassaolon ja taikuuden perusta; "
                "kahlittu Keskimeren pohjaan, TÄYSIN VALVEILLA.",
        body="Ylijumala Ao ei luonut Cunaen maailmaa perinteisellä tavalla. "
             "Hän asetti Garruthan nuoreen sfääriin \"tasapainon ruumiiksi\" "
             "peilaamaan Torilin jumalten voimia — maailma on siis "
             "kirjaimellisesti rakennettu titaanin päälle.\n\n"
             "Garrutha ei kestänyt tämän kosmisen taakan aiheuttamaa "
             "mielenterveyden järkkymistä. Siksi titaani loi itsestään "
             "Vendilit (mm. Nimfritei ja Klorham) jakamaan maailman "
             "perusvoimien kuormaa.\n\n"
             "Meridian Sunderingin jälkeen Garrutha jäi kahlituksi "
             "Keskimeren pohjaan. Se on yhä täysin valveilla ja kantaa "
             "maailman taakkaa. Kaikki taikuus Cunaessa on viime kädessä "
             "sen voimaa.\n\n"
             "PELINJOHTAJALLE: tämä on kampanjan suurin salaisuus. Jos "
             "Garruthan kahleet murtuvat, Esmerin Kristallikupu romahtaa ja "
             "maailma joutuu Phlogistonin petojen ja alkuperäisten "
             "Sarrukhien armoille.",
        keywords=["garrutha", "titaani", "titan", "maailmantitaani", "ao",
                  "tasapainon ruumis", "keskimeri", "central sea",
                  "taikuuden lähde", "vendil", "vendilit", "nimfritei",
                  "klorham"],
        see_also=["vendilit", "veru", "meridian_sundering", "kristallikupu",
                  "sarrukhit"],
        location_ids=["loc_aequitas"]),

    LoreEntry(
        key="vendilit", title="Vendilit — titaanin jakamat voimat",
        category="kosmologia", spoiler=True,
        summary="Garruthan itsestään luomat olennot, jotka kantavat "
                "maailman perusvoimien kuormaa titaanin puolesta.",
        body="Kun kosmisen taakan paino järkytti Garruthan mieltä, titaani "
             "loi itsestään Vendilit jakamaan maailman perusvoimien "
             "kuormaa. Tunnettuja Vendilejä ovat Nimfritei ja Klorham.\n\n"
             "Vendilit liittoutuivat Arkkimaagi Esmerin ja "
             "Drow-Matriarkka Caznan kanssa pysäyttääkseen keisari "
             "Tarquvasin — he siis toimivat maailman tasapainon puolesta "
             "silloinkin kun jumalat eivät.",
        keywords=["vendil", "vendilit", "nimfritei", "klorham",
                  "perusvoimat", "tasapaino"],
        see_also=["garrutha", "tarquvas", "kristallikupu"]),

    LoreEntry(
        key="kristallikupu", title="Esmerin Kristallikupu",
        category="kosmologia", spoiler=True,
        summary="Cunaen ylle rakennettu kupu, joka eristää maailman "
                "Phlogistonista ja piilottaa Garruthan kosmisilta uhilta.",
        body="Noin 2 000 vuotta sitten Arkkimaagi Esmer rakensi Cunaen ylle "
             "Kristallikuvun, joka eristi maailman muusta multiversumista "
             "(Phlogistonista).\n\n"
             "Kuvun tarkoitus on PIILOTTAA GARRUTHA ulkopuolisilta "
             "kosmisilta kauhuilta ja alkuperäisiltä Sarrukheilta, jotka "
             "palaisivat vaatimaan \"generaattoriaan\" takaisin, jos Veru "
             "koskaan aktivoitaisiin uudelleen.\n\n"
             "PELINJOHTAJALLE: kupu on kampanjan kellopommi. Jokainen "
             "ryhmittymä, joka yrittää koota Verun, uhkaa rikkoa sen. "
             "Fort Whitestonen kellareissa on kosminen kartta "
             "(kristallikupu + Phlogiston), jolla Walker-suku seuraa "
             "kuvun tilaa.",
        keywords=["kristallikupu", "crystal dome", "kupu", "esmer",
                  "arkkimaagi esmer", "phlogiston", "multiversumi",
                  "eristys", "kosminen kartta"],
        see_also=["garrutha", "sarrukhit", "walker_aequitas", "veru"],
        location_ids=["loc_fort_whitestone"]),

    LoreEntry(
        key="sarrukhit", title="Sarrukhit — luojarodut",
        category="uhat", spoiler=True,
        summary="Torilista paenneet luojarodut, jotka huijasivat Garruthaa "
                "ja takoivat Verun. Palaisivat vaatimaan 'generaattoriaan'.",
        body="Torilista paenneet luojarodut (Sarrukhit) saapuivat Cunaeen ja "
             "huomasivat Garruthan valtavan potentiaalin. He päättivät "
             "valjastaa sen.\n\n"
             "Sarrukhit huijasivat hyväntahtoista titaania luovuttamaan "
             "osia itsestään — luuta, muistia ja tahtoa. Näistä osista "
             "taottiin Veru-koneisto.\n\n"
             "Meridian Sundering tuhosi suurimman osan luojarodusta, mutta "
             "alkuperäiset Sarrukhit ovat yhä jossain Phlogistonissa. Jos "
             "Veru aktivoidaan uudelleen ja kupu murtuu, he palaavat "
             "vaatimaan generaattoriaan takaisin.",
        keywords=["sarrukh", "sarrukhit", "luojarodut", "creator races",
                  "toril", "phlogiston", "generaattori"],
        see_also=["garrutha", "veru", "meridian_sundering", "kristallikupu"]),

    # ================================================================= #
    # ARTEFAKTIT — Veru-koneisto
    # ================================================================= #
    LoreEntry(
        key="veru", title="Veru-koneisto",
        category="artefaktit", spoiler=True,
        summary="Garruthan luusta, muistista ja tahdosta taottu koneisto: "
                "Clavise-miekka, Hatred of Time -kirja ja ihopalaset. "
                "Vaatii elävän Redfei-operaattorin.",
        body="Veru taottiin Garruthan osista — luusta, muistista ja "
             "tahdosta. Koneistoon kuuluvat:\n"
             "  • CLAVISE-miekka (Avain)\n"
             "  • HATRED OF TIME -kirja\n"
             "  • Ihoon kiinnittyvät tatuointikääröt (Skin shards)\n\n"
             "Veru ei ole vain kone: se vaatii toimiakseen ELÄVÄN "
             "OPERAATTORIN, jonka verilinja (Redfei) kestää titaanin "
             "energian.\n\n"
             "NYKYTILA: 3/5 ihopalasista on Kruskin selässä. Clavise on "
             "Lyran hallussa — ja Dimerius tietää sen. Kun Veru "
             "yhdistetään Clavise-miekkaan, operaattorin on tehtävä "
             "valinta (ks. 'Kruskin valinta').",
        keywords=["veru", "veru-koneisto", "clavise", "avain", "key",
                  "hatred of time", "kirja", "skin shard", "ihopalaset",
                  "tatuointikääröt", "artefakti", "operaattori", "redfei"],
        see_also=["clavise", "redfei_verilinja", "kruskin_valinta",
                  "garrutha", "sarrukhit"],
        npc_ids=["npc_krusk", "npc_dimerius"]),

    LoreEntry(
        key="clavise", title="Clavise — Avain",
        category="artefaktit",
        summary="Veru-koneiston miekka-avain. Lyran hallussa; Dimerius "
                "haluaa sen ja tietää sijainnin.",
        body="Clavise on Veru-koneiston Avain: miekka, joka yhdistää "
             "ihopalaset toimivaksi kokonaisuudeksi.\n\n"
             "Dimerius Blackfeet haluaa Clavise-miekan ja tietää sen olevan "
             "Lyran hallussa. Hän lähetti Verilähettilään testaamaan "
             "Kruskia ja toimittamaan psykologisen iskun: \"Herra "
             "Blackfeet kiittää sinua Avaimen säilyttämisestä.\"\n\n"
             "Kun Clavise yhdistetään Kruskin ihopalasiin, Veru "
             "aktivoituu ja Kruskin on valittava.",
        keywords=["clavise", "avain", "key", "miekka", "sword", "lyra",
                  "verilähettiläs", "blood herald"],
        see_also=["veru", "kruskin_valinta", "dimerius_tavoite"],
        npc_ids=["npc_dimerius", "npc_krusk"]),

    LoreEntry(
        key="redfei_verilinja", title="Redfei-verilinja (operaattorit)",
        category="artefaktit", spoiler=True,
        summary="Ainoa verilinja, joka kestää titaanin energian — Veru ei "
                "toimi ilman elävää Redfei-operaattoria.",
        body="Veru vaatii elävän operaattorin, jonka verilinja kestää "
             "titaanin energian. Se verilinja on REDFEI.\n\n"
             "Tunnetut operaattorit ja perijät:\n"
             "  • Ensimmäinen Redfei (yli 20 000 v sitten) — kieltäytyi "
             "orjuudesta, imi voiman ja räjäytti itsensä → Meridian "
             "Sundering.\n"
             "  • Keisari Tarquvas Redfei (n. 2 000 v sitten) — keräsi 3/5 "
             "ihopalasista; Cazna telkesi hänen sielunsa kruununsa "
             "kristalliin.\n"
             "  • KRUSK — Tarquvasin jälkeläinen, kantaa nyt samoja 3/5 "
             "palasia selässään.\n"
             "  • Emnar Redfei — Oblituksen diktaattori, sama suku.\n\n"
             "PELINJOHTAJALLE: Dimeriukselta PUUTTUU tämä verilinja — "
             "siksi hän tavoittelee Tarquvasin sielua Caznan kruunusta.",
        keywords=["redfei", "verilinja", "bloodline", "operaattori",
                  "operator", "tarquvas", "krusk", "emnar"],
        see_also=["veru", "tarquvas", "kruskin_valinta", "dimerius_tavoite"],
        npc_ids=["npc_krusk", "npc_emnar", "npc_dimerius"]),

    # ================================================================= #
    # HISTORIA — kataklysmit
    # ================================================================= #
    LoreEntry(
        key="meridian_sundering", title="Meridian Sundering — Ensimmäinen Tuho",
        category="historia",
        summary="Yli 20 000 v sitten ensimmäinen Redfei-operaattori "
                "räjäytti itsensä Vangurionissa: kaupunki upposi, "
                "Keskimeri syntyi ja Garrutha jäi kahleisiin.",
        body="Yli 20 000 vuotta sitten Sarrukhit yrittivät kytkeä "
             "ensimmäisen Redfein Garruthaan Vangurionin kaupungissa.\n\n"
             "Operaattori ei suostunut orjaksi: hän imi voiman ja räjäytti "
             "itsensä. Tämä kataklysmi — THE MERIDIAN SUNDERING —\n"
             "  • upotti Vangurionin,\n"
             "  • tuhosi suurimman osan luojarodusta,\n"
             "  • synnytti Cunaen Keskimeren (Central Sea),\n"
             "  • ja jätti Garruthan kahlituksi Keskimeren pohjaan.\n\n"
             "Keskimeri ei siis ole luonnollinen meri vaan räjähdyskraateri. "
             "Vanqurionin rauniot ovat sen pohjassa — ja siellä on Tower "
             "Bragenton sielukone, jota Dath tavoittelee.",
        keywords=["meridian sundering", "ensimmäinen tuho", "kataklysmi",
                  "vangurion", "vanqurion", "keskimeri", "central sea",
                  "räjähdys", "20000"],
        see_also=["garrutha", "veru", "sarrukhit", "dath_suunnitelma"]),

    LoreEntry(
        key="tarquvas", title="Keisari Tarquvas Redfei — Unohdettu Keisari",
        category="historia",
        summary="Yritti 2 000 v sitten aktivoida Verun vapauttaakseen "
                "kansansa; Cazna telkesi hänen sielunsa kruunun kristalliin.",
        body="Noin 2 000 vuotta sitten \"Unohdettu Keisari\" Tarquvas Redfei "
             "yritti toistaa historian: hän keräsi selkäänsä 3/5 "
             "Veru-ihon palasista vapauttaakseen sorretun kansansa.\n\n"
             "Suunnitelma oli katastrofaalinen — Verun aktivoiminen olisi "
             "voinut tuhota maailman uudelleen. Estääkseen tämän "
             "Arkkimaagi Esmer, Drow-Matriarkka Cazna ja Vendilit "
             "liittoutuivat:\n"
             "  • CAZNA telkesi Tarquvasin sielun kruunussaan olevaan "
             "kristalliin.\n"
             "  • ESMER rakensi Kristallikuvun maailman ylle.\n\n"
             "Tarquvasin sielu on siis YHÄ Matriarkka Caznan kruunussa "
             "Zer'tath Lankessa. Dimerius aikoo imeä sen itseensä.",
        keywords=["tarquvas", "unohdettu keisari", "forgotten emperor",
                  "keisari", "cazna", "matriarkka", "esmer", "kruunu",
                  "crown", "sielu"],
        see_also=["redfei_verilinja", "kristallikupu", "dimerius_tavoite",
                  "vendilit"],
        npc_ids=["npc_dimerius"],
        location_ids=["loc_zertath_lanke"]),

    # ================================================================= #
    # RYHMITTYMÄT JA NYKYTAVOITTEET
    # ================================================================= #
    LoreEntry(
        key="kruskin_valinta", title="Kruskin valinta — Elävä Lukko",
        category="uhat", spoiler=True,
        summary="Krusk kantaa 3/5 Veru-palasista. Clavisen kanssa hänen on "
                "valittava: vapauttaa Garrutha vai pukea sen voima ylleen.",
        body="Krusk on Tarquvasin jälkeläinen ja kantaa selässään 3/5 "
             "Veru-ihon palasista. Se tekee hänestä FYYSISEN YHTEYDEN "
             "kahlittuun titaaniin — Elävän Lukon.\n\n"
             "Koko maailman kohtalo lepää hänen harteillaan. Kun Veru "
             "yhdistetään Clavise-miekkaan, Kruskin on valittava:\n\n"
             "  1. VAPAUTTAA Garrutha → suojakupu voi tuhoutua ja "
             "ulkoiset uhat (Phlogistonin pedot, Sarrukhit) pääsevät "
             "sisään.\n"
             "  2. PUKEA titaanin voima ylleen (Inward-hallinta) → "
             "Kruskista tulee uusi absoluuttinen tyranni.\n\n"
             "PELINJOHTAJALLE: tämä on kampanjan loppuratkaisu. Kolmas tie "
             "(kahleiden vahvistaminen? Vendilien apu?) on pelaajien "
             "keksittävä — sitä ei ole valmiina.",
        keywords=["krusk", "elävä lukko", "living lock", "valinta", "choice",
                  "inward", "vapauttaa", "tyranni", "loppuratkaisu",
                  "endgame"],
        see_also=["veru", "clavise", "garrutha", "redfei_verilinja"],
        npc_ids=["npc_krusk"]),

    LoreEntry(
        key="dath_suunnitelma", title="Dath ja Veljeskunta — 300 000 sielua",
        category="ryhmittymät", spoiler=True,
        summary="Sytyttävät maailmansodan kerätäkseen 300 000 kuolleen "
                "sieluenergian Zlalensin kristalliin, lentävät "
                "Vanqurioniin ja ottavat Garruthan haltuunsa.",
        body="Radikaali haltiajärjestö DATH ja heidän sätkynukkensa "
             "LOISTAVAN AURINGON VELJESKUNTA yrittävät sytyttää massiivisen "
             "maailmansodan Tarmaaksen, Oblituksen ja Aterterran välille.\n\n"
             "Suunnitelma vaiheittain:\n"
             "  1. Sota → 300 000 kuollutta.\n"
             "  2. Kerää sieluenergia Zlalensin huippukristalliin.\n"
             "  3. Nosta koko kaupunki ilmaan.\n"
             "  4. Lennä Keskimerelle Vanqurioniin.\n"
             "  5. Käytä Tower Bragenton sielukonetta ja Verun palasia.\n"
             "  6. Ota Garrutha hallintaan → nouse Torilin jumaliksi.\n\n"
             "PELINJOHTAJALLE: tämä on kampanjan pääantagonistin juoni. "
             "Sota on jo alkanut — jokainen kohtaaminen, joka lisää "
             "kuolonuhreja, edistää Dathin suunnitelmaa.",
        keywords=["dath", "veljeskunta", "brotherhood", "loistava aurinko",
                  "glorious sun", "zlalens", "kristalli", "sieluenergia",
                  "300000", "maailmansota", "tower bragenton", "sielukone",
                  "vanqurion"],
        see_also=["garrutha", "veru", "meridian_sundering"],
        location_ids=["loc_zlalens"]),

    LoreEntry(
        key="dimerius_tavoite", title="Dimeriuksen peli — sielu ja jumaluus",
        category="ryhmittymät", spoiler=True,
        summary="Tarquvasin vampyyriksi muuttunut kenraali: imee "
                "Tarquvasin sielun Caznan kruunusta, kaappaa Veru-ihon "
                "Kruskilta ja Clavisen → maailman ainoa jumala.",
        body="Dimerius Blackfeet on Tarquvasin entinen, vampyyriksi "
             "muuttunut kenraali, joka pelaa omaa peliään.\n\n"
             "Koska häneltä PUUTTUU Redfei-verilinja, hän ei voi käyttää "
             "Verua itse. Siksi hänen suunnitelmansa on:\n"
             "  1. Imeä Matriarkka Caznan kruunusta Tarquvasin sielu "
             "itseensä (saa verilinjan).\n"
             "  2. Kaapata Veru-iho Kruskilta.\n"
             "  3. Ottaa Clavise-miekka (tietää sen olevan Lyran hallussa).\n"
             "  4. Tulla maailman ainoaksi jumalaksi.\n\n"
             "Hän manipuloi Ravenstonea varjoista kryptastaan Corvus "
             "Spelchrumissa, jota vartioivat Golbera ja Xalars.",
        keywords=["dimerius", "blackfeet", "vampyyri", "kenraali",
                  "tarquvas", "cazna", "kruunu", "jumala", "ravenstone",
                  "corvus spelchrum"],
        see_also=["tarquvas", "veru", "clavise", "redfei_verilinja"],
        npc_ids=["npc_dimerius", "npc_krusk", "npc_golbera", "npc_xalars"],
        location_ids=["loc_ravenstone", "loc_corvus_spelchrum"]),

    LoreEntry(
        key="walker_aequitas", title="Walker-suku ja Aequitas — vastavoima",
        category="ryhmittymät",
        summary="Yrittävät estää KENEN TAHANSA kokoamasta Verua; tietävät "
                "että kuvun romahdus jättää maailman Phlogistonin armoille.",
        body="Walker-suku (mukaan lukien Blitzin esi-isät, jotka loivat "
             "Fort Whitestonen tappokoneiston) ja Aequitas-saaren "
             "Boundless-agentit yrittävät epätoivoisesti estää ketään "
             "kokoamasta Verua.\n\n"
             "He tietävät, että jos Garruthan kahleet murretaan, Cunaen "
             "suojakupu romahtaa ja maailma joutuu Phlogistonin petojen ja "
             "luojarotujen armoille.\n\n"
             "Fort Whitestonen kellarit ovat oma taskuulottuvuus: 8 000 "
             "Automata Trooperia, Whitestone Colosseja ja sukellusveneitä "
             "— kosmisen karanteenin armeija. Siellä on myös kosminen "
             "kartta (kristallikupu + Phlogiston).\n\n"
             "PELINJOHTAJALLE: nämä ovat pelaajien luonnollisia "
             "liittolaisia — mutta he eivät epäröi tappaa ketään, joka "
             "kantaa Veru-palasia. Myös Kruskia.",
        keywords=["walker", "walker-suku", "aequitas", "boundless", "blitz",
                  "fort whitestone", "automata", "karanteeni",
                  "vastavoima", "codex"],
        see_also=["kristallikupu", "veru", "kruskin_valinta"],
        npc_ids=["npc_blitz"],
        location_ids=["loc_fort_whitestone", "loc_aequitas"]),
]


_BY_KEY = {e.key: e for e in CODEX}


def all_entries() -> List[LoreEntry]:
    return list(CODEX)


def get_entry(key: str):
    return _BY_KEY.get(key)


def categories() -> List[str]:
    """Categories actually present, in the canonical order."""
    present = {e.category for e in CODEX}
    return [c for c in CATEGORIES if c in present]


def by_category(category: str) -> List[LoreEntry]:
    return [e for e in CODEX if e.category == category]


def search(query: str, category: str = "") -> List[LoreEntry]:
    """Relevance-ranked search over title, keywords, summary and body.

    Empty query returns everything (optionally filtered by category), so
    the codex doubles as a browsable index.
    """
    pool = [e for e in CODEX if not category or e.category == category]
    q = (query or "").strip().lower()
    if not q:
        return pool
    terms = [t for t in q.split() if t]
    scored = []
    for e in pool:
        title = e.title.lower()
        kws = " ".join(e.keywords).lower()
        summary = e.summary.lower()
        body = e.body.lower()
        score = 0
        for t in terms:
            if t in title:
                score += 10
            if any(t in k for k in (kw.lower() for kw in e.keywords)):
                score += 8
            if t in kws:
                score += 4
            if t in summary:
                score += 3
            if t in body:
                score += 1
        if score:
            scored.append((score, e))
    scored.sort(key=lambda pair: (-pair[0], pair[1].title))
    return [e for _s, e in scored]


def entries_for_npc(npc_id: str) -> List[LoreEntry]:
    """Codex articles that mention this NPC — powers 'why does this
    character matter?' straight from their sheet."""
    return [e for e in CODEX if npc_id in e.npc_ids]


def entries_for_location(location_id: str) -> List[LoreEntry]:
    return [e for e in CODEX if location_id in e.location_ids]


def as_campaign_notes():
    """Mirror the codex into CampaignNote objects so the lore also shows
    up in the ordinary Notes tab (searchable there too)."""
    from data.campaign import CampaignNote
    out = []
    for e in CODEX:
        tag = "[SPOILER] " if e.spoiler else ""
        out.append(CampaignNote(
            text=f"{tag}{e.title.upper()} — {e.summary}\n\n{e.body}",
            category="lore", timestamp=""))
    return out
