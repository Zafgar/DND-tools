"""Novus Somniumin oikeat kartat ja niiden paikkamerkit.

Pelinjohtajan piirtämät kartat elävät ``data/maps/world/`` -kansiossa ja
ovat tässä rekisteröitynä niin, että ne ovat käytettävissä pelissä eivätkä
vain kuvatiedostoina levyllä:

  * **cunae** — koko mantereen yleiskartta mittakaavajanoineen. Tämä on
    maailman oletustausta (``world.map_image_path``).
  * **smardu**, **tarmaas**, **oblitus**, **fundarla** — valtakuntien
    tarkat kartat. Nämä asetetaan myös vastaavan valtakunnan
    ``Location.map_image_path`` -kenttään, joten paikkakortti näyttää
    kartan suoraan.

Jokaisella kartalla on oma joukko **paikkamerkkejä** (``MapPin``), joiden
koordinaatit ovat prosentteja kuvan leveydestä ja korkeudesta — sama
yksikkö jota maailmankartan katselin jo käyttää, joten merkit pysyvät
paikallaan zoomatessa. Merkit on kytketty olemassa oleviin
``loc_*``-tunnuksiin, joten kartalta pääsee suoraan paikan tietoihin.

Merkkien koordinaatit on luettu kartoista käsin. Ne ovat tarkoituksella
likimääräisiä: tarkkuus riittää siihen, että pelinjohtaja löytää
kaupungin kartalta, eikä karttoja ole tehty ruudukolle.

``apply_world_maps(world)`` on **idempotentti** — sen voi ajaa vanhalle
tallennukselle uudestaan, eikä se monista merkkejä eikä ylikirjoita
pelinjohtajan itse siirtämiä merkkejä.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Kansio jossa kartat ovat, projektin juuresta.
MAP_DIR = os.path.join("data", "maps", "world")


@dataclass
class WorldMap:
    """Yksi rekisteröity kartta."""
    key: str
    name: str
    filename: str
    description: str = ""
    location_id: str = ""      # valtakunta jonka kartta tämä on
    scale_note: str = ""       # mittakaava pelinjohtajalle
    parent_key: str = ""       # yleiskartta johon tämä kuuluu

    @property
    def path(self) -> str:
        """Projektisuhteellinen polku (sama muoto kuin muu karttadata)."""
        return os.path.join(MAP_DIR, self.filename)

    def abs_path(self, base_dir: str = "") -> str:
        base = base_dir or os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        return os.path.join(base, self.path)

    def exists(self, base_dir: str = "") -> bool:
        return os.path.isfile(self.abs_path(base_dir))


WORLD_MAPS: List[WorldMap] = [
    WorldMap(
        key="cunae", name="Cunae (koko manner)", filename="cunae.jpg",
        description="Mantereen yleiskartta: Smardu, Tarmaas, Oblitus, "
                    "Fundarla, Lenora ja Jaimaras sekä Aterterran "
                    "jääsaari pohjoisessa. Mittakaavajana ja kompassiruusu "
                    "mukana.",
        scale_note="Jana: 32/64/96/128/160 mailia (20/40/60/80/100 km)."),
    WorldMap(
        key="smardu", name="Smardu — Khrum Daar Nozkron",
        filename="smardu.jpg", location_id="loc_smardu", parent_key="cunae",
        description="Pohjoinen kääpiövaltakunta: Maelot-jäätiköt, "
                    "Dumadarak-vuoristo, Efouset, Juamore ja tulivuori "
                    "Fubna. Azwyr Nogaak lännessä."),
    WorldMap(
        key="tarmaas", name="Tarmaas — Gerontocracy of Tarmaas",
        filename="tarmaas.jpg", location_id="loc_tarmaas", parent_key="cunae",
        description="Kampanjan sydänmaa: Frand, Faharn, Hijoin, Matin, "
                    "Ravenstone, Old Vaisil, Veksla ja Pinwud. Suolajärvi "
                    "ja Greenwold Frontier etelässä; Scarlet Canopy "
                    "Forest koillisessa.",
        scale_note="Matka-jana: 1 päivä jalan / hevosella / lentoratsulla / "
                   "lohikäärmeellä / zeppeliinillä."),
    WorldMap(
        key="oblitus", name="Oblitus — autiomaavaltakunta",
        filename="oblitus.jpg", location_id="loc_oblitus", parent_key="cunae",
        description="Etelän autiomaa: Iklence, Chento, Mors-laavakentät, "
                    "Tharkozh-Varrin kivimetsä, Ovla ja Fort High Rock. "
                    "Aesica ja Tyrusa lännessä, Xokroks etelärannikolla."),
    WorldMap(
        key="fundarla", name="Fundarla — haltiavaltakunta (kesken)",
        filename="fundarla.jpg", location_id="loc_fundarla",
        parent_key="cunae",
        description="Haltioiden valtakunta. KESKEN — kartalla on vasta "
                    "Zlalens, Oufa, Cifiri, Lunoni, Nunamair, Drim Rum ja "
                    "Lilien; suuri osa maasta on vielä nimeämättä."),
]

_BY_KEY = {m.key: m for m in WORLD_MAPS}

DEFAULT_MAP_KEY = "cunae"


def all_maps() -> List[WorldMap]:
    return list(WORLD_MAPS)


def get_map(key: str) -> Optional[WorldMap]:
    return _BY_KEY.get(key)


def map_for_location(location_id: str) -> Optional[WorldMap]:
    """Valtakunnan oma kartta, jos sellainen on."""
    for m in WORLD_MAPS:
        if m.location_id and m.location_id == location_id:
            return m
    return None


def key_for_path(path: str) -> str:
    """Mikä rekisteröity kartta tämä polku on (tyhjä jos ei mikään)."""
    if not path:
        return ""
    base = os.path.basename(str(path).replace("\\", "/"))
    for m in WORLD_MAPS:
        if m.filename == base:
            return m.key
    return ""


# ===================================================================== #
# PAIKKAMERKIT
# ===================================================================== #
# (nimi, x%, y%, tyyppi, loc_id, kuvaus)
_PinSpec = Tuple[str, float, float, str, str, str]


def _pct(x_px: float, y_px: float, w: float, h: float) -> Tuple[float, float]:
    return round(x_px / w * 100.0, 2), round(y_px / h * 100.0, 2)


# --- Cunae, luettu 2000x1500 -esikatselusta -------------------------- #
_CUNAE_PX: List[Tuple[str, float, float, str, str, str]] = [
    # Valtakunnat
    ("Smardu", 355, 300, "poi", "loc_smardu",
     "Pohjoinen kääpiövaltakunta. Oma tarkka kartta saatavilla."),
    ("Tarmaas", 455, 800, "poi", "loc_tarmaas",
     "Gerontocracy of Tarmaas — kampanjan sydänmaa."),
    ("Oblitus", 1160, 1290, "poi", "loc_oblitus",
     "Etelän autiomaavaltakunta."),
    ("Fundarla", 1450, 340, "poi", "loc_fundarla",
     "Haltiavaltakunta. Kartta on vielä kesken."),
    ("Aterterra", 1130, 220, "danger", "loc_aterterra",
     "Jääsaari pohjoisessa — ja sen alla drow-Underdark. "
     "Matriarkka Cazna Icharydin valtakunta."),
    ("Maclebar Isle", 630, 1190, "poi", "loc_maclebar",
     "Marblecrag Isle. Walker-suvun saari."),
    ("Caldius", 855, 710, "poi", "loc_caldius", "Khro Kal, Keskimeren saari."),
    # Smardu
    ("Antanard", 630, 425, "note", "loc_antanard", ""),
    ("Juamore", 810, 465, "note", "loc_juamore", ""),
    ("Hifrom", 370, 545, "note", "loc_hifrom", ""),
    # Tarmaas
    ("Frand", 690, 845, "poi", "loc_frand", "Tarmaaksen pääkaupunki."),
    ("Faharn", 535, 845, "note", "loc_faharn", ""),
    ("Hijoin", 545, 885, "note", "loc_hijoin", ""),
    ("Honpa", 805, 850, "note", "loc_honpa", ""),
    ("Fat Carp", 830, 930, "note", "loc_fat_carp", ""),
    ("Veksla", 630, 940, "note", "loc_veksla", ""),
    ("Ravenstone", 735, 980, "danger", "loc_ravenstone",
     "Dimerius Blackfeetin kaupunki. Vampyyrien sisällissota."),
    ("Old Vaisil", 720, 1073, "poi", "loc_old_vaisil", ""),
    ("Fort Whitestone", 660, 1146, "poi", "loc_fort_whitestone",
     "Silex Alpus — Walker-suvun tappokoneisto ja Protokolla Omega."),
    # Oblitus
    ("Aesica", 750, 1085, "poi", "loc_aesica",
     "Aghuantin suuri temppeli ja areena."),
    ("Iklence", 1575, 1010, "poi", "loc_iklence", ""),
    ("Xokroks", 1010, 1235, "note", "", "Oblituksen etelärannikko."),
    ("Mors", 1365, 1245, "danger", "", "Laavakentät."),
    # Fundarla
    ("Zlalens", 1270, 520, "danger", "loc_zlalens",
     "Dath'in Veljeskunnan kristallitorni."),
    ("Cifiri", 1245, 660, "note", "loc_cifiri", ""),
    ("Nunamair", 1330, 655, "note", "loc_nunamair", ""),
    ("Asmenor", 1565, 465, "note", "loc_asmenor", ""),
    # Merkittävät maastot ja meret
    ("Midle Sea", 920, 770, "note", "", "Keskimeri."),
    ("Firgus", 965, 675, "note", "", "Jäinen saari Keskimerellä."),
    ("Viridis", 1105, 745, "note", "", "Vihreä saari."),
    ("Refugium", 945, 880, "note", "", "Turvasaari Keskimerellä."),
    ("Lenora", 1540, 490, "note", "", "Fundarlan itäinen metsämaa."),
    ("Jaimaras", 1790, 800, "note", "", "Itäinen saarivaltakunta."),
]

# --- Smardu, luettu 2000x1500 -esikatselusta ------------------------- #
_SMARDU_PX = [
    ("Maelot", 1140, 100, "note", "", "Jäätiköt ja jääkarhujen maa."),
    ("Atsin Festing", 1075, 143, "poi", "loc_stein_festing",
     "Stein Festing — Kivikaupunki."),
    ("Dumadarak", 300, 540, "note", "", "Läntinen vuorijono."),
    ("Duamdok", 570, 420, "note", "", ""),
    ("Hifrom", 345, 770, "note", "loc_hifrom", ""),
    ("Efouset", 1040, 540, "note", "", "Keskinen vuoristo."),
    ("Ruins of Bargento", 875, 682, "danger", "", "Rauniot."),
    ("Antanard", 1125, 710, "poi", "loc_antanard", ""),
    ("Juamore", 1450, 723, "poi", "loc_juamore", "Saarikaupunki."),
    ("Hgnara", 1605, 563, "note", "", ""),
    ("Halvar", 1595, 410, "note", "", ""),
    ("Asav", 1240, 905, "note", "", "Yksinäinen vuori."),
    ("F.Erid", 1215, 997, "note", "", ""),
    ("Lous", 1570, 925, "note", "", ""),
    ("Jiv", 1620, 1042, "note", "", ""),
    ("Unboil", 585, 963, "note", "", ""),
    ("Turno", 655, 953, "note", "", ""),
    ("Fubna", 375, 1195, "danger", "", "Tulivuorialue."),
    ("Kacemo", 1020, 1160, "note", "", ""),
    ("Port Kai", 1325, 1290, "note", "", ""),
    ("Azwyr Nogaak", 305, 40, "note", "", "Luoteinen jäävuoristo."),
]

# --- Tarmaas, luettu 2000x1500 -esikatselusta ------------------------ #
_TARMAAS_PX = [
    ("Frand", 1355, 492, "poi", "loc_frand", "Tarmaaksen pääkaupunki."),
    ("Matin", 1225, 402, "poi", "", "Vuoristokaupunki."),
    ("Faharn", 795, 572, "poi", "loc_faharn", ""),
    ("Hijoin", 865, 625, "poi", "loc_hijoin", ""),
    ("Veksla", 1120, 878, "note", "loc_veksla", ""),
    ("Ravenstone", 1490, 925, "danger", "loc_ravenstone",
     "Dimeriuksen kaupunki ja Corvus Spelchrum -krypta."),
    ("Arist", 1370, 975, "note", "loc_arist", ""),
    ("Baltimon", 1320, 865, "note", "loc_baltimon", ""),
    ("Pinwud", 1420, 1043, "danger", "loc_pinwud",
     "Death's Vigilin temppeli — vampyyriongelma."),
    ("Old Vaisil", 1495, 1272, "poi", "loc_old_vaisil", ""),
    ("Fat Carp", 1740, 750, "note", "loc_fat_carp", ""),
    ("Teneos", 1700, 900, "note", "", ""),
    ("Old Hein", 1690, 992, "note", "", ""),
    ("Ravenstone (tie)", 1495, 897, "note", "", "Tienristeys."),
    ("Old Town Jaxlo", 880, 955, "note", "", ""),
    ("Grebagne", 1095, 348, "note", "", "Vuorijono."),
    ("Bladvine", 1105, 520, "note", "", "Viiniviljelmät."),
    ("Salt Lake", 690, 1105, "note", "", "Suolajärvi."),
    ("Gran'O'thar", 800, 1135, "note", "", ""),
    ("Shar Zalith", 625, 1020, "note", "", ""),
    ("Greenwold Frontier", 555, 1180, "note", "", "Eteläinen rajaseutu."),
    ("Sculptor's Expanse", 590, 825, "note", "", ""),
    ("Silkweaver's Thicket", 700, 520, "note", "", ""),
    ("Scarlet Canopy Forest", 1590, 190, "danger", "",
     "Punainen metsä koillisessa."),
    ("Inuvi", 1245, 1075, "note", "", ""),
    ("Wheaton", 1500, 1000, "note", "", ""),
    ("Hayup", 1530, 1043, "note", "", ""),
    ("Smold", 1555, 1160, "note", "", ""),
    ("Mistmug", 1345, 1110, "note", "", ""),
    ("Onemud", 1435, 1122, "note", "", ""),
    ("Hamhild", 1390, 1170, "note", "", ""),
    ("Honza", 1710, 650, "note", "", ""),
    ("Unda", 105, 175, "note", "", "Läntinen naapuri."),
    ("Arrn'Alu", 1890, 550, "note", "", "Itäinen naapuri."),
    ("Jatnar Kaat", 1755, 1400, "note", "", "Kaakkoinen naapuri."),
]

# --- Oblitus, luettu 2000x1500 -esikatselusta ------------------------ #
_OBLITUS_PX = [
    ("Iklence", 1790, 650, "poi", "loc_iklence", "Autiomaan suurkaupunki."),
    ("Chento", 1490, 483, "note", "", "Vihreä vuoristo."),
    ("Tharkozh-Varr", 1040, 855, "danger", "loc_tharkozh_varr",
     "Kivimetsä ja salamamyrskyt."),
    ("Mors", 1165, 1063, "danger", "", "Laavakentät ja Morgul-Dur."),
    ("Ovla", 615, 655, "poi", "", "Vuoristokaupunki."),
    ("Fort High Rock", 765, 578, "poi", "", ""),
    ("Vrakk'taal Ruins", 715, 787, "danger", "", "Rauniot."),
    ("Tyrusa", 370, 993, "note", "", ""),
    ("Aesica", 75, 1148, "poi", "loc_aesica",
     "Aghuantin temppeli ja Nak Magnok -areena."),
    ("Maelomar", 265, 1155, "note", "", ""),
    ("Xokroks", 665, 1338, "note", "", ""),
    ("Kuljak", 1140, 1290, "note", "", ""),
    ("Okjai", 1520, 1305, "note", "", ""),
    ("Blufmag", 1855, 1295, "note", "", ""),
    ("Hyv", 1615, 1055, "note", "", ""),
    ("Ruksno", 1375, 890, "note", "", ""),
    ("Khakar", 1545, 680, "note", "", ""),
    ("Khomon", 1325, 655, "note", "", ""),
    ("Bukoti", 1515, 385, "note", "", ""),
    ("Ök'sara", 1015, 358, "note", "", ""),
    ("Lenag Gug", 320, 890, "note", "", "Sisämeri."),
    ("Gravenest", 545, 1268, "danger", "", ""),
    ("Khaz Varduuk", 750, 1338, "danger", "", ""),
    ("Hakama", 990, 1240, "note", "", ""),
]

# --- Fundarla, luettu 2000x1500 -esikatselusta ----------------------- #
_FUNDARLA_PX = [
    ("Zlalens", 748, 522, "danger", "loc_zlalens",
     "Dath'in Veljeskunnan kristallitorni. 300 000 sielua."),
    ("Oufa", 860, 452, "note", "", "Vuoristoasutus."),
    ("Cifiri", 680, 795, "note", "loc_cifiri", ""),
    ("Lunoni", 688, 905, "note", "", ""),
    ("Nunamair", 862, 868, "poi", "loc_nunamair", ""),
    ("Drim Rum", 808, 967, "note", "", "Vesiputouskaupunki."),
    ("Lilien", 902, 993, "note", "", ""),
    ("Kristallikenttä", 545, 700, "poi", "",
     "Jäätynyt kristallialue Zlalensin länsipuolella."),
]


def _build(specs, w=2000.0, h=1500.0, map_key="") -> List[dict]:
    out = []
    for name, x, y, ptype, loc_id, desc in specs:
        px, py = _pct(x, y, w, h)
        out.append({
            "name": name, "map_x": px, "map_y": py, "pin_type": ptype,
            "location_id": loc_id, "description": desc, "map_key": map_key,
        })
    return out


MAP_PINS: Dict[str, List[dict]] = {
    "cunae": _build(_CUNAE_PX, map_key="cunae"),
    "smardu": _build(_SMARDU_PX, map_key="smardu"),
    "tarmaas": _build(_TARMAAS_PX, map_key="tarmaas"),
    "oblitus": _build(_OBLITUS_PX, map_key="oblitus"),
    "fundarla": _build(_FUNDARLA_PX, map_key="fundarla"),
}


def pins_for(map_key: str) -> List[dict]:
    return list(MAP_PINS.get(map_key, []))


def pin_id(map_key: str, name: str) -> str:
    """Vakaa tunniste, jotta uudelleenajo ei monista merkkejä."""
    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    return f"pin_{map_key}_{slug}"


# ===================================================================== #
# ASENNUS MAAILMAAN
# ===================================================================== #
def apply_world_maps(world, *, base_dir: str = "") -> dict:
    """Kytke kartat ja paikkamerkit maailmaan. Idempotentti.

    * ``world.map_image_path`` osoittaa Cunae-yleiskarttaan (ellei
      pelinjohtaja ole itse asettanut jotain muuta).
    * Valtakuntien ``Location.map_image_path`` osoittaa niiden omaan
      karttaan.
    * Puuttuvat paikkamerkit lisätään. Olemassa olevaa merkkiä EI
      siirretä eikä nimetä uudelleen — jos pelinjohtaja on raahannut sen
      paremmalle kohdalle, se pysyy siellä.

    Palauttaa yhteenvedon siitä mitä tehtiin.
    """
    from data.world import MapPin

    added_pins = 0
    linked_maps = 0
    missing_files = []

    for wm in WORLD_MAPS:
        if not wm.exists(base_dir):
            missing_files.append(wm.filename)
            continue
        if wm.location_id:
            loc = (world.locations or {}).get(wm.location_id)
            if loc is not None and not loc.map_image_path:
                loc.map_image_path = wm.path
                linked_maps += 1

    # Yleiskartta maailman taustaksi
    cunae = get_map(DEFAULT_MAP_KEY)
    if cunae is not None and cunae.exists(base_dir):
        if not world.map_image_path:
            world.map_image_path = cunae.path
            linked_maps += 1

    existing = {p.id for p in world.map_pins}
    for wm in WORLD_MAPS:
        if not wm.exists(base_dir):
            continue
        for spec in pins_for(wm.key):
            pid = pin_id(wm.key, spec["name"])
            if pid in existing:
                continue
            # Älä luo merkkiä paikalle jota ei ole olemassa — kuollut
            # linkki kartalla on pahempi kuin puuttuva merkki.
            loc_id = spec["location_id"]
            if loc_id and loc_id not in (world.locations or {}):
                loc_id = ""
            world.map_pins.append(MapPin(
                id=pid,
                name=spec["name"],
                pin_type=spec["pin_type"],
                description=spec["description"],
                map_x=spec["map_x"],
                map_y=spec["map_y"],
                map_key=wm.key,
                location_id=loc_id,
            ))
            existing.add(pid)
            added_pins += 1

    return {
        "added_pins": added_pins,
        "linked_maps": linked_maps,
        "missing_files": missing_files,
    }
