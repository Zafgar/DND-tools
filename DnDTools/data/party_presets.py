"""Sijaintipohjaiset party-presetit — nopea "lataa oikeat hahmot kentälle".

Kampanjan pelaajahahmot eivät aina ole yhdessä: osa on Aterterrassa, osa
Maclebar Islella, osa Ravenstonessa ja osa Aesicassa. Näiden presettien
avulla pelinjohtaja lataa yhdellä klikkauksella juuri sen porukan, joka
kyseisessä paikassa taistelee — nopeaa "sokeaa" pöytäpeliä varten.

Jäsenlistat viittaavat heroihin nimellä (``data.heroes.hero_list``).
``preset_as_entities`` ohittaa hiljaa nimet joita ei vielä ole lisätty
kirjastoon, joten tulevat hahmot (esim. Beatrice, Carlo, Blitz) voi
listata jo nyt — preset täydentyy automaattisesti heti kun ne lisätään
heroihin. Listat on tarkoitettu helposti muokattaviksi.
"""
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class PartyPreset:
    id: str
    name: str
    location: str
    description: str
    members: List[str] = field(default_factory=list)


# --------------------------------------------------------------------- #
# Presetit (muokattavissa: lisää/poista nimiä ``members``-listasta).
# Vielä lisäämättömät hahmot voi listata nyt — ne aktivoituvat kun ne
# lisätään heroihin.
# --------------------------------------------------------------------- #
PARTY_PRESETS: List[PartyPreset] = [
    PartyPreset(
        id="full",
        name="Koko seurue",
        location="Kaikki",
        description="Kaikki tunnetut pelaajahahmot yhdessä kentälle.",
        members=["Magnus Dragonius", "Balthazar", "Kairon", "Beatrice",
                 "Venris Galanodel", "Carlo", "Blitz Walker", "Padak Onslaught",
                 "Krusk", "Marduk", "Darius \"Slick\" Morin", "ULV"],
    ),
    PartyPreset(
        id="aterterra",
        name="Aterterra — Velve Dro",
        location="Aterterra / Zer'tath Lanke",
        description="Drow-eliittipartiota vastaan iskevä ryhmä.",
        members=["Magnus Dragonius", "Balthazar", "Kairon", "Beatrice"],
    ),
    PartyPreset(
        id="maclebar",
        name="Maclebar Isle — Fort Whitestone",
        location="Maclebar Isle",
        description="Walker-suvun automaatiota (A.E.G.I.S.) tutkiva ryhmä.",
        members=["Venris Galanodel", "Carlo", "Blitz Walker"],
    ),
    PartyPreset(
        id="ravenstone",
        name="Ravenstone — Padak",
        location="Ravenstone",
        description="Padak yksin Ravenstonen kauhujen keskellä (1 vs 1).",
        members=["Padak Onslaught"],
    ),
    PartyPreset(
        id="aesica",
        name="Aesica — Krusk",
        location="Aesica",
        description="Krusk yksin Death's Vigilin haastajia vastaan (1 vs 1).",
        members=["Krusk"],
    ),
    PartyPreset(
        id="pinvud_vigil",
        name="Pinvud Vigil — Marduk",
        location="Pinvud Vigil (päämaja)",
        description="Marduk Death's Vigilin päämajassa.",
        members=["Marduk"],
    ),
]

_BY_ID = {p.id: p for p in PARTY_PRESETS}


def list_presets() -> List[PartyPreset]:
    return list(PARTY_PRESETS)


def get_preset(pid: str) -> PartyPreset:
    if pid not in _BY_ID:
        raise KeyError(f"Party preset {pid!r} not found. "
                       f"Available: {list(_BY_ID)}")
    return _BY_ID[pid]


def resolve_members(preset: PartyPreset) -> Tuple[list, List[str]]:
    """Return (found_hero_stats, missing_names) for a preset.

    Names are matched case-insensitively against ``hero_list``. Names not
    (yet) present are returned as ``missing_names`` so callers can note
    which future characters still need adding.
    """
    from data.heroes import hero_list
    by_name = {h.name.lower(): h for h in hero_list}
    found, missing = [], []
    for name in preset.members:
        h = by_name.get(name.lower())
        if h is not None:
            found.append(h)
        else:
            missing.append(name)
    return found, missing


def preset_as_entities(preset: PartyPreset, existing_roster=None) -> list:
    """Build player ``Entity`` objects for a preset's available members.

    Skips names not found in ``hero_list`` and any hero already present
    (by name) in ``existing_roster``. Places them on the player side
    (west columns), stacking below whatever players are already there.
    """
    from engine.entities import Entity
    existing_roster = existing_roster or []
    present = {e.name.lower() for e in existing_roster if e.is_player}
    start = len([e for e in existing_roster if e.is_player])
    found, _missing = resolve_members(preset)
    ents = []
    i = start
    for h in found:
        if h.name.lower() in present:
            continue
        ents.append(Entity(h, 3, 2 + i * 2, is_player=True))
        present.add(h.name.lower())
        i += 1
    return ents
