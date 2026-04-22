"""Novus Somnium — the starter campaign that ships with the tool.

A small frontier setting: the port-city of **Arenhold** on the edge of
reclaimed lands, the old fortress of **Vardun Keep** guarding the
northern pass, and the misty **Silverbough Forest** to the south.

`ensure_default_campaign()` creates the campaign on disk if it doesn't
exist yet so every fresh install has something the DM can open, expand,
and use as a template. Idempotent — running it on a fresh machine
seeds it; running it again does nothing.

Also seeds a handful of Actors into the shared ActorRegistry so the
tokens have identity from day one.
"""
from __future__ import annotations

import os
from typing import Optional

from data.campaign import (
    Campaign, CampaignArea, CampaignEncounter, CampaignNote,
    save_campaign, CAMPAIGNS_DIR,
)


NOVUS_SOMNIUM_NAME = "Novus Somnium"
NOVUS_SOMNIUM_FILENAME = "Novus Somnium.json"
NOVUS_SOMNIUM_FILEPATH = os.path.join(CAMPAIGNS_DIR, NOVUS_SOMNIUM_FILENAME)


# --------------------------------------------------------------------- #
# Data builders
# --------------------------------------------------------------------- #
def _build_areas() -> list:
    return [
        CampaignArea(
            name="Arenhold, the Port-City",
            description=(
                "A wind-bitten trade port on the Greysea. Docks smell of "
                "salt and tar; the upper district is ruled by the merchant "
                "houses from marble counting-halls."
            ),
            environment="outdoor",
            lighting="bright",
            notes=(
                "Population ~8,000. Harbourmaster Jolan Ves (lawful-neutral) "
                "sets the fees. Three merchant houses (Tarn, Mellecote, "
                "Yfran) constantly jockey for shipping contracts."
            ),
            encounter_names=["Harbor Thugs"],
        ),
        CampaignArea(
            name="Vardun Keep",
            description=(
                "A half-ruined fortress straddling the only road north. "
                "Held for three generations by the Vardun line; current "
                "castellan is Lady Mira Vardun."
            ),
            environment="indoor",
            lighting="dim",
            notes=(
                "The western wall collapsed last winter; the breach is "
                "patched with timber and goblins have started probing it."
            ),
            encounter_names=["Breach Probe"],
        ),
        CampaignArea(
            name="Silverbough Forest",
            description=(
                "Old-growth silver birches, mist year-round. Local lore "
                "says the fey court of the Veiled Queen walks its hollows "
                "on moonless nights."
            ),
            environment="outdoor",
            lighting="dim",
            notes=(
                "Druids of the Greenstone Circle patrol the verges. They "
                "are watchful but not hostile to travellers who respect "
                "the circle markers."
            ),
            encounter_names=["Wolves of the Bough"],
        ),
        CampaignArea(
            name="The Greysea",
            description=(
                "Cold grey water stretching west. Pirates haunt the long "
                "trade lane to the Free Isles; winter storms kill more "
                "crews than any corsair ever did."
            ),
            environment="outdoor",
            lighting="bright",
            notes=(
                "Primary route: Arenhold → Free Isles (~480 miles). The "
                "Kraken's Tongue, a stone reef, takes one ship a decade."
            ),
            encounter_names=[],
        ),
    ]


def _build_encounters() -> list:
    # Slot type is opaque here — we keep them empty so the campaign
    # structure is valid but any pre-wired encounter details come from
    # the library during a real session.
    return [
        CampaignEncounter(
            name="Harbor Thugs",
            description=(
                "Four dock-thugs strong-arm the party in a narrow alley "
                "after they ask the wrong question about the Tarn family."
            ),
            area_name="Arenhold, the Port-City",
            difficulty_hint="Easy",
            notes="Scenario ref: bandit_crossroads (or urban variant).",
        ),
        CampaignEncounter(
            name="Breach Probe",
            description=(
                "Goblin skirmishers test the patched wall at Vardun "
                "Keep. A Worg rides with the boss."
            ),
            area_name="Vardun Keep",
            difficulty_hint="Medium",
            notes="Scenario ref: goblin_warrens.",
        ),
        CampaignEncounter(
            name="Wolves of the Bough",
            description=(
                "A pack of dire-wolves hunts fey-touched stags on the "
                "southern verge of Silverbough."
            ),
            area_name="Silverbough Forest",
            difficulty_hint="Medium",
            notes="Scenario ref: wolf_pack.",
        ),
    ]


def _build_notes() -> list:
    return [
        CampaignNote(
            text=(
                "OPENING HOOK — Lady Mira Vardun has written to "
                "Harbourmaster Jolan asking for able hands to investigate "
                "the goblin probes. The letter reaches the party via a "
                "bounty on Arenhold's message board: 50 gp for verified "
                "goblin raid evidence."
            ),
            category="quest",
            pinned=True,
        ),
        CampaignNote(
            text=(
                "WORLD TONE — Gritty frontier, not grimdark. Magic is "
                "rare but real; priests bless harbour crews before long "
                "voyages. The fey are dangerous but not evil — they "
                "keep bargains to the letter."
            ),
            category="lore",
        ),
    ]


# Actors seeded into the shared registry. Names + colours are enough
# for tokens to render with identity; the DM adds portraits later.
_STARTER_ACTORS = [
    {"name": "Lady Mira Vardun",       "kind": "npc",
     "color": (200, 180, 80),  "notes": "Castellan of Vardun Keep."},
    {"name": "Harbourmaster Jolan Ves", "kind": "npc",
     "color": (120, 160, 200), "notes": "Rules Arenhold's docks."},
    {"name": "Elder Rhoswen",          "kind": "npc",
     "color": (100, 200, 120),
     "notes": "Druid of the Greenstone Circle, Silverbough Forest."},
    {"name": "Captain Arys Tarn",      "kind": "npc",
     "color": (180, 90, 90),
     "notes": "Head of the Tarn merchant house — ruthless."},
    {"name": "The Stormchaser",        "kind": "vehicle",
     "color": (120, 180, 220),
     "notes": "Small square-rigged brig, 12-crew, regular Arenhold "
              "↔ Free Isles run."},
]


def seed_novus_somnium_actors(registry=None):
    """Add the starter actors to ``registry``. If any already exist by
    name they are left alone (idempotent). Returns the list of Actor
    objects created or already present."""
    if registry is None:
        from data.actors import get_registry
        registry = get_registry()
    out = []
    for spec in _STARTER_ACTORS:
        existing = registry.get_by_name(spec["name"])
        if existing is not None:
            out.append(existing)
            continue
        actor = registry.create(
            name=spec["name"], kind=spec["kind"],
            color=spec["color"], notes=spec["notes"],
        )
        out.append(actor)
    return out


# --------------------------------------------------------------------- #
# Top-level build + seed
# --------------------------------------------------------------------- #
def build_novus_somnium() -> Campaign:
    return Campaign(
        name=NOVUS_SOMNIUM_NAME,
        description=(
            "A small frontier setting on the Greysea coast: the trade "
            "port Arenhold, the embattled Vardun Keep, and the "
            "fey-touched Silverbough Forest. A starter sandbox you can "
            "expand, rename, or replace."
        ),
        areas=_build_areas(),
        encounters=_build_encounters(),
        notes=_build_notes(),
        time_of_day="day",
        current_area="Arenhold, the Port-City",
        session_number=1,
    )


def ensure_default_campaign(campaigns_dir: Optional[str] = None,
                              registry=None) -> str:
    """Create Novus Somnium on disk if it isn't already there. Also
    seeds starter Actors into the registry. Idempotent — running on a
    fresh install seeds it; running again is a no-op.

    Returns the campaign file path.
    """
    campaigns_dir = campaigns_dir or CAMPAIGNS_DIR
    os.makedirs(campaigns_dir, exist_ok=True)
    path = os.path.join(campaigns_dir, NOVUS_SOMNIUM_FILENAME)
    if not os.path.isfile(path):
        camp = build_novus_somnium()
        save_campaign(camp, path)
    seed_novus_somnium_actors(registry=registry)
    return path
