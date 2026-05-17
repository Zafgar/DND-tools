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
            name="Frand",
            description=(
                "Tarmaasin pääkaupunki ja partyn aloituspaikka. "
                "Suuri muurikaupunki Auringonkirkon emäkatedraalin "
                "varjossa; kauppakillat alakaupungissa, kruunu "
                "yläkaupungissa. Brotherhood of Glorious Sun "
                "rekrytoi salaa köyhälistöstä."
            ),
            environment="outdoor",
            lighting="bright",
            notes=(
                "Population ~42,000. Garek Hammerfall pitää Anvil & "
                "Star -pajaa, Counting House toimii kauppakiltojen "
                "pankkina. Salaisuus orpokodin takana -tehtävä "
                "saatavilla."
            ),
            encounter_names=[],
        ),
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
def _build_world():
    """Phase 28 — build the World container that backs the starter
    campaign: top-level kingdom regions, their starter cities as
    locations, a few named NPCs, one starter shop in Frand and one
    starter quest. This is what wires Novus Somnium to all the
    living-world subsystems (wealth aggregator, kingdom navigator,
    organisation member jumps, quest log).
    """
    from data.world import (
        World, Location, NPC, Shop, ShopItem, Quest,
        QuestObjective, QuestLogEntry,
    )
    from data.shop_preset_library import apply_preset_to_shop
    from data.wealth import set_npc_coins, suggest_coins_for_wealth_tier

    w = World(name=NOVUS_SOMNIUM_NAME)

    # ---- Top-level: one country region per kingdom -----------------
    kingdom_loc_ids = {}
    for key, name, biome, gov in [
        ("tarmaas",   "Tarmaas",   "human_heartland", "Monarchy"),
        ("fundarla",  "Fundarla",  "forest",          "Druidic Council"),
        ("smardu",    "Smardu",    "mountain",        "Dwarven Holds"),
        ("aterterra", "Aterterra", "coast",           "Merchant Republic"),
        ("oblitus",   "Oblitus",   "desert",          "Shadow Theocracy"),
    ]:
        loc = Location(
            id=f"loc_{key}", name=name, location_type="country",
            description=f"Suurvalta {name} — {biome}.",
            government=gov, tags=[key, "kingdom"],
        )
        w.locations[loc.id] = loc
        kingdom_loc_ids[key] = loc.id

    # ---- Frand (Tarmaas capital) ----------------------------------
    frand = Location(
        id="loc_frand", name="Frand", location_type="city",
        parent_id=kingdom_loc_ids["tarmaas"],
        description=(
            "Tarmaasin pääkaupunki — suuri muurikaupunki "
            "Auringonkirkon emäkatedraalin varjossa. "
            "Kauppakillat hallitsevat alakaupunkia, kruunu yläkaupunkia."
        ),
        population=42_000, wealth_level="comfortable",
        government="Monarchy", religion="Auringonkirkko",
        known_for="Steel, grain, the High Cathedral of the Dawn",
        defenses="Triple curtain walls, 600-strong city watch",
        environment="outdoor", lighting="bright",
        tags=["frand", "tarmaas", "capital"],
    )
    w.locations[frand.id] = frand
    w.locations[kingdom_loc_ids["tarmaas"]].children_ids.append(frand.id)

    # ---- Frand starter NPCs ---------------------------------------
    # Use stable ids so the Brotherhood seed can link to them.
    npc_specs = [
        ("npc_calistro", "Radiant Calistro", "Human", "Noble patron",
            "noble", "wealthy", "Lawful Evil",
            "Brotherhood of Glorious Sun",
            "Charming patron of the arts who runs the Brotherhood's "
            "spy network from a townhouse in the upper district."),
        ("npc_vela", "Lightbringer Vela", "Half-Elf", "Missionary",
            "priest", "modest", "Lawful Evil",
            "Brotherhood of Glorious Sun",
            "Public face of the Brotherhood — preaches in the slum "
            "wards, takes in 'lost' orphans."),
        ("npc_jolan", "Harbourmaster Jolan Ves", "Human", "Harbourmaster",
            "official", "comfortable", "Lawful Neutral", "Crown",
            "Sets the dock fees and arbitrates trade disputes."),
        ("npc_mira", "Lady Mira Vardun", "Human", "Castellan",
            "noble", "comfortable", "Lawful Good", "House Vardun",
            "Castellan of Vardun Keep, holds the northern road."),
        ("npc_arys", "Captain Arys Tarn", "Human", "Merchant captain",
            "merchant", "wealthy", "Neutral Evil", "House Tarn",
            "Ruthless head of the Tarn merchant house."),
        ("npc_rhoswen", "Elder Rhoswen", "Wood Elf", "Druid",
            "druid", "modest", "Neutral", "Greenstone Circle",
            "Senior druid of the Silverbough Greenstone Circle."),
        ("npc_smith",  "Garek Hammerfall", "Dwarf", "Blacksmith",
            "blacksmith", "comfortable", "Lawful Neutral", "",
            "Frand's most reputable smith, runs the Anvil & Star forge."),
    ]
    for nid, name, race, occ, title, wealth, align, faction, notes in npc_specs:
        loc_id = (frand.id if nid in (
            "npc_calistro", "npc_vela", "npc_jolan",
            "npc_arys", "npc_smith") else "")
        npc = NPC(
            id=nid, name=name, race=race, occupation=occ,
            title=title, alignment=align, faction=faction,
            notes=notes, location_id=loc_id, alive=True, active=True,
        )
        set_npc_coins(npc, suggest_coins_for_wealth_tier(wealth))
        w.npcs[nid] = npc
        if loc_id and nid not in frand.npc_ids:
            frand.npc_ids.append(nid)

    # ---- Frand starter shop: Anvil & Star Forge -------------------
    shop = Shop(
        id="shop_anvil_star",
        name="Anvil & Star Forge",
        shop_type="blacksmith",
        location_id=frand.id,
        owner_npc_id="npc_smith",
        description="Frandin nimekkäin paja — tilauksia myös retkikunnille.",
        sell_markup=1.0, buy_markup=0.5,
        gold=150.0,
    )
    apply_preset_to_shop(shop, "basic")
    w.shops[shop.id] = shop

    # ---- Frand bank: the Counting House ---------------------------
    bank = Shop(
        id="shop_counting_house",
        name="The Counting House",
        shop_type="bank",
        location_id=frand.id,
        description="Frandin kauppakiltojen yhteinen pankki.",
        is_bank=True, bank_holdings_gp=12_000.0,
        gold=400.0,
    )
    w.shops[bank.id] = bank

    # ---- Starter quest ---------------------------------------------
    q = Quest(
        id="quest_anvil_blade",
        name="Anvil & Star: Custom blade",
        description=(
            "Garek Hammerfall on suostunut takomaan partyn fighterille "
            "räätälöidyn longsword +1:n. Käsiraha 100 gp on maksettu; "
            "miekka on valmis viiden päivän kuluttua."
        ),
        status="active", priority="normal", quest_type="side",
        giver_npc_id="npc_smith",
        npc_ids=["npc_smith"],
        shop_ids=["shop_anvil_star"],
        location_ids=[frand.id],
        map_pin_location_id=frand.id,
        reward_items=["Longsword +1"],
        objectives=[
            QuestObjective(description="Vie käsiraha Garekille",
                            completed=True,
                            target_npc_id="npc_smith"),
            QuestObjective(description="Hae valmis miekka 5 päivän kuluttua",
                            target_npc_id="npc_smith"),
        ],
        log=[QuestLogEntry(
            timestamp="S1 D1", kind="transaction",
            description="Käsiraha: Longsword +1",
            gold_delta=-100.0, npc_id="npc_smith",
            shop_id="shop_anvil_star",
        )],
        session_given=1,
        level_range="3-5",
    )
    w.quests[q.id] = q

    # ---- Brotherhood plot hook quest ------------------------------
    q2 = Quest(
        id="quest_brotherhood_recruits",
        name="Salaisuus orpokodin takana",
        description=(
            "Köyhälistö Frandin etelälaidalla puhuu kadonneista "
            "lapsista. Lightbringer Velan 'turvakoti' on Brotherhood "
            "of Glorious Sunin värväyspiste — pelaajien tehtävä on "
            "ottaa selvää."
        ),
        status="not_started", priority="high", quest_type="main",
        giver_npc_id="npc_jolan",
        npc_ids=["npc_jolan", "npc_vela", "npc_calistro"],
        location_ids=[frand.id],
        map_pin_location_id=frand.id,
        monster_names=["Cult Acolyte"],
        reward_xp=400, reward_gold=150.0,
        reward_notes="Harbourmaster maksaa hiljaa, ei haluta huomiota.",
        objectives=[
            QuestObjective(description="Puhu harbourmaster Jolanin kanssa",
                            target_npc_id="npc_jolan"),
            QuestObjective(description="Tarkkaile Lightbringer Velaa",
                            target_npc_id="npc_vela"),
            QuestObjective(description="Selvitä Radiant Calistron rooli",
                            target_npc_id="npc_calistro"),
        ],
        session_given=1,
        level_range="3-5",
    )
    w.quests[q2.id] = q2

    return w


def _wire_brotherhood_npcs(camp):
    """Phase 28 — link the seed Brotherhood members to the actual
    Frand NPCs so the organisation panel's "→ avaa NPC" navigation
    has somewhere to go.
    """
    from data import organizations as orgs_mod
    b = orgs_mod.find_organisation(camp, "brotherhood_of_glorious_sun")
    if b is None:
        return
    name_to_id = {
        "Radiant Calistro":    "npc_calistro",
        "Lightbringer Vela":   "npc_vela",
    }
    for m in b.members:
        if not m.npc_id and m.npc_name in name_to_id:
            m.npc_id = name_to_id[m.npc_name]


def _serialize_world_for_campaign(world):
    """Phase 28 — same serialisation path the campaign manager uses
    to persist the World, mirrored so build_novus_somnium() can drop
    the result straight into Campaign.world_data."""
    from data.world import (
        _serialize_location, _serialize_npc, _serialize_route,
        _serialize_quest, _serialize_shop, _serialize_service,
    )
    return {
        "name": world.name,
        "description": world.description,
        "created": world.created,
        "last_modified": world.last_modified,
        "locations": {k: _serialize_location(v)
                       for k, v in world.locations.items()},
        "npcs": {k: _serialize_npc(v) for k, v in world.npcs.items()},
        "quests": {k: _serialize_quest(v)
                     for k, v in world.quests.items()},
        "shops": {k: _serialize_shop(v) for k, v in world.shops.items()},
        "services": {k: _serialize_service(v)
                       for k, v in world.services.items()},
        "next_id": world.next_id,
        "map_routes": [_serialize_route(r) for r in world.map_routes],
        "map_image_path": world.map_image_path,
        "map_positions": world.map_positions,
    }


# --------------------------------------------------------------------- #
# Top-level build + seed
# --------------------------------------------------------------------- #
def build_novus_somnium() -> Campaign:
    camp = Campaign(
        name=NOVUS_SOMNIUM_NAME,
        description=(
            "Päämanner viidellä suurvallalla (Tarmaas, Fundarla, "
            "Smardu, Aterterra, Oblitus). Aloituspaikka on Tarmaasin "
            "pääkaupunki Frand, jossa Brotherhood of Glorious Sun "
            "kerää salaa väkeä. Lisäalueina pohjoinen rannikko "
            "(Arenhold-portti), Vardun Keep ja Silverbough-metsä."
        ),
        areas=_build_areas(),
        encounters=_build_encounters(),
        notes=_build_notes(),
        time_of_day="day",
        current_area="Frand",
        session_number=1,
        party_gold=120.0,
    )
    # Phase 22 — pre-seed the living-world structures (5 kingdoms +
    # the Brotherhood of Glorious Sun) so the on-disk save already
    # carries them and the DM can browse them without first opening
    # the navigator.
    from data import kingdoms as _kg
    from data import organizations as _orgs
    _kg.ensure_kingdoms_on_campaign(camp)

    # Phase 28 — populate the World container and wire kingdom cities
    # to their actual Location ids so the wealth aggregator,
    # organisation navigation and quest log all have data on day one.
    world = _build_world()
    camp.world_data = _serialize_world_for_campaign(world)
    # Cross-link: Frand city → world location id
    tarmaas = _kg.find_kingdom(camp, "tarmaas")
    if tarmaas:
        for c in tarmaas.cities:
            if c.key == "frand":
                c.location_id = "loc_frand"
    _kg.sync_kingdoms_to_campaign(camp)

    _orgs.ensure_organisations_on_campaign(camp)
    _wire_brotherhood_npcs(camp)
    _orgs.sync_organisations_to_campaign(camp)
    return camp


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
