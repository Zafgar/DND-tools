"""Organisations — guilds, churches, criminal brotherhoods, knightly orders.

A campaign's NPCs already carry a free-form ``faction`` string (see
``data.world.NPC``).  That works for casual flavour but breaks down when
the DM wants to ask questions like:

  * *"Who are the high-ranking members of the Brotherhood of Glorious Sun?"*
  * *"Which cities does this organisation operate in?"*
  * *"What is this NPC's role inside that group?"*

This module adds a structured :class:`Organisation` record on top:
ranks (hierarchy), roles (functional), members (linked by NPC id or by
free-form name), areas of operation (kingdom keys), and a stable identity
key so other systems (UI, quests, relationship sync) can reference it.

Storage: persisted under ``Campaign.organisations_data`` as a list of
dicts, with the runtime list re-hydrated on first access via
:func:`ensure_organisations_on_campaign`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ----------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------

# Common kinds — UI uses these as filter chips. Free-form strings allowed.
ORGANISATION_KINDS: List[str] = [
    "guild", "church", "order", "brotherhood", "cult", "syndicate",
    "noble_house", "merchant_company", "mercenary_band", "academy",
    "other",
]


@dataclass
class OrganisationRank:
    """A vertical rank inside an organisation, lowest to highest order
    indicated by ``tier`` (1 = leader, larger = lower)."""
    key: str
    name: str
    tier: int = 5
    description: str = ""


@dataclass
class OrganisationRole:
    """A horizontal role (functional job) inside the organisation —
    e.g. "Quartermaster", "Inquisitor", "Spymaster". Not tied to rank."""
    key: str
    name: str
    description: str = ""


@dataclass
class OrganisationMember:
    """One NPC's membership in an organisation.

    ``npc_id`` is the canonical link (matches ``World.npcs`` keys / the
    ActorRegistry); ``npc_name`` is a fallback when no character sheet
    exists yet — the navigator will still display it as a placeholder
    chip and the DM can promote it to a full NPC later.
    """
    npc_id: str = ""
    npc_name: str = ""           # fallback display name
    rank_key: str = ""
    role_keys: List[str] = field(default_factory=list)
    city_key: str = ""           # where this member operates
    kingdom_key: str = ""
    notes: str = ""
    active: bool = True


@dataclass
class OrganisationOperation:
    """Phase 27d — a recorded operation the organisation runs.

    Each entry has a kind ("recruit", "sabotage", "extort",
    "conversion", "raid", "intelligence", "ritual", "diplomacy",
    "other"), a target city/kingdom, severity (1=low / 5=catastrophic),
    a status (planned / active / completed / aborted), a timestamp
    (e.g. ``"S3 D5"``), an optional ``npc_member_id`` (whose handler
    among the members) and a free-form description.

    The organisation panel renders these as a chronological timeline.
    """
    id: str = ""
    name: str = ""
    kind: str = "other"          # see OPERATION_KINDS
    target_city_key: str = ""
    target_kingdom_key: str = ""
    severity: int = 1            # 1..5
    status: str = "planned"      # planned, active, completed, aborted
    timestamp: str = ""
    description: str = ""
    npc_member_id: str = ""
    quest_id: str = ""           # Optional Quest link


OPERATION_KINDS: List[str] = [
    "recruit", "sabotage", "extort", "conversion", "raid",
    "intelligence", "ritual", "diplomacy", "other",
]

OPERATION_STATUSES: List[str] = [
    "planned", "active", "completed", "aborted",
]


@dataclass
class Organisation:
    key: str
    name: str
    kind: str = "other"          # ORGANISATION_KINDS entry
    description: str = ""
    motto: str = ""
    secret: bool = False          # publicly known vs. covert
    alignment: str = ""           # "lawful evil" etc.
    headquarters_city: str = ""   # city_key — primary base
    headquarters_kingdom: str = ""
    operating_kingdoms: List[str] = field(default_factory=list)
    operating_cities: List[str] = field(default_factory=list)
    ranks: List[OrganisationRank] = field(default_factory=list)
    roles: List[OrganisationRole] = field(default_factory=list)
    members: List[OrganisationMember] = field(default_factory=list)
    operations: List[OrganisationOperation] = field(default_factory=list)
    relations: Dict[str, str] = field(default_factory=dict)  # org_key → attitude
    color: tuple = (160, 160, 160)
    tags: List[str] = field(default_factory=list)

    # ------- convenience -----------------------------------------------
    def rank(self, key: str) -> Optional[OrganisationRank]:
        for r in self.ranks:
            if r.key == key:
                return r
        return None

    def role(self, key: str) -> Optional[OrganisationRole]:
        for r in self.roles:
            if r.key == key:
                return r
        return None

    def members_in_city(self, city_key: str) -> List[OrganisationMember]:
        return [m for m in self.members
                 if m.active and m.city_key == city_key]

    def members_in_kingdom(self, kingdom_key: str
                            ) -> List[OrganisationMember]:
        return [m for m in self.members
                 if m.active and m.kingdom_key == kingdom_key]

    def members_at_rank(self, rank_key: str) -> List[OrganisationMember]:
        return [m for m in self.members
                 if m.active and m.rank_key == rank_key]

    def member_for_npc(self, npc_id: str) -> Optional[OrganisationMember]:
        for m in self.members:
            if m.active and m.npc_id and m.npc_id == npc_id:
                return m
        return None


# ----------------------------------------------------------------------
# Serialisation
# ----------------------------------------------------------------------

def _rank_from_dict(d: Dict) -> OrganisationRank:
    return OrganisationRank(
        key=d.get("key", ""), name=d.get("name", ""),
        tier=int(d.get("tier", 5) or 5),
        description=d.get("description", ""),
    )


def _rank_to_dict(r: OrganisationRank) -> Dict:
    return {"key": r.key, "name": r.name, "tier": r.tier,
            "description": r.description}


def _role_from_dict(d: Dict) -> OrganisationRole:
    return OrganisationRole(
        key=d.get("key", ""), name=d.get("name", ""),
        description=d.get("description", ""),
    )


def _role_to_dict(r: OrganisationRole) -> Dict:
    return {"key": r.key, "name": r.name, "description": r.description}


def _member_from_dict(d: Dict) -> OrganisationMember:
    return OrganisationMember(
        npc_id=d.get("npc_id", ""), npc_name=d.get("npc_name", ""),
        rank_key=d.get("rank_key", ""),
        role_keys=list(d.get("role_keys", []) or []),
        city_key=d.get("city_key", ""),
        kingdom_key=d.get("kingdom_key", ""),
        notes=d.get("notes", ""),
        active=bool(d.get("active", True)),
    )


def _member_to_dict(m: OrganisationMember) -> Dict:
    return {
        "npc_id": m.npc_id, "npc_name": m.npc_name,
        "rank_key": m.rank_key, "role_keys": list(m.role_keys),
        "city_key": m.city_key, "kingdom_key": m.kingdom_key,
        "notes": m.notes, "active": m.active,
    }


def _operation_from_dict(d: Dict) -> OrganisationOperation:
    return OrganisationOperation(
        id=d.get("id", ""), name=d.get("name", ""),
        kind=d.get("kind", "other"),
        target_city_key=d.get("target_city_key", ""),
        target_kingdom_key=d.get("target_kingdom_key", ""),
        severity=int(d.get("severity", 1) or 1),
        status=d.get("status", "planned"),
        timestamp=d.get("timestamp", ""),
        description=d.get("description", ""),
        npc_member_id=d.get("npc_member_id", ""),
        quest_id=d.get("quest_id", ""),
    )


def _operation_to_dict(op: OrganisationOperation) -> Dict:
    return {
        "id": op.id, "name": op.name, "kind": op.kind,
        "target_city_key": op.target_city_key,
        "target_kingdom_key": op.target_kingdom_key,
        "severity": op.severity, "status": op.status,
        "timestamp": op.timestamp, "description": op.description,
        "npc_member_id": op.npc_member_id, "quest_id": op.quest_id,
    }


def _org_from_dict(d: Dict) -> Organisation:
    color = d.get("color", (160, 160, 160))
    if isinstance(color, list):
        color = tuple(color)
    return Organisation(
        key=d.get("key", ""), name=d.get("name", ""),
        kind=d.get("kind", "other"),
        description=d.get("description", ""),
        motto=d.get("motto", ""),
        secret=bool(d.get("secret", False)),
        alignment=d.get("alignment", ""),
        headquarters_city=d.get("headquarters_city", ""),
        headquarters_kingdom=d.get("headquarters_kingdom", ""),
        operating_kingdoms=list(d.get("operating_kingdoms", []) or []),
        operating_cities=list(d.get("operating_cities", []) or []),
        ranks=[_rank_from_dict(r) for r in d.get("ranks", [])],
        roles=[_role_from_dict(r) for r in d.get("roles", [])],
        members=[_member_from_dict(m) for m in d.get("members", [])],
        operations=[_operation_from_dict(op)
                      for op in d.get("operations", []) or []],
        relations=dict(d.get("relations", {}) or {}),
        color=color if isinstance(color, tuple) else (160, 160, 160),
        tags=list(d.get("tags", []) or []),
    )


def _org_to_dict(o: Organisation) -> Dict:
    return {
        "key": o.key, "name": o.name, "kind": o.kind,
        "description": o.description, "motto": o.motto,
        "secret": o.secret, "alignment": o.alignment,
        "headquarters_city": o.headquarters_city,
        "headquarters_kingdom": o.headquarters_kingdom,
        "operating_kingdoms": list(o.operating_kingdoms),
        "operating_cities": list(o.operating_cities),
        "ranks": [_rank_to_dict(r) for r in o.ranks],
        "roles": [_role_to_dict(r) for r in o.roles],
        "members": [_member_to_dict(m) for m in o.members],
        "operations": [_operation_to_dict(op) for op in o.operations],
        "relations": dict(o.relations),
        "color": list(o.color),
        "tags": list(o.tags),
    }


# ----------------------------------------------------------------------
# Seed organisations — Novus Somnium starter
# ----------------------------------------------------------------------

def _brotherhood_of_glorious_sun() -> Organisation:
    """Phase 22d seed — the campaign's flagship antagonist faction.

    The Brotherhood appears in Tarmaas (publicly, masquerading as a
    reform movement of the Auringonkirkko) and in Oblitus (openly, as
    a ruling cult).  Smardu chapter is quiet and infiltrative.
    """
    ranks = [
        OrganisationRank(key="dawn_father", name="Dawn Father", tier=1,
                          description="Supreme leader; identity hidden."),
        OrganisationRank(key="radiant", name="Radiant", tier=2,
                          description="Inner circle — five members."),
        OrganisationRank(key="lightbringer", name="Lightbringer", tier=3,
                          description="Senior agent in a city."),
        OrganisationRank(key="sun_blade", name="Sun Blade", tier=4,
                          description="Trained warrior cell."),
        OrganisationRank(key="acolyte", name="Acolyte", tier=5,
                          description="Initiate, often unaware of true aims."),
    ]
    roles = [
        OrganisationRole(key="inquisitor", name="Inquisitor",
                          description="Hunts apostates and rivals."),
        OrganisationRole(key="quartermaster", name="Quartermaster",
                          description="Handles relics, weapons, gold."),
        OrganisationRole(key="spymaster", name="Spymaster",
                          description="Runs informant networks."),
        OrganisationRole(key="missionary", name="Missionary",
                          description="Public face — recruits, preaches."),
        OrganisationRole(key="executioner", name="Executioner",
                          description="Quiet removal of obstacles."),
    ]
    members = [
        OrganisationMember(
            npc_name="The Dawn Father (unknown)",
            rank_key="dawn_father",
            role_keys=[],
            kingdom_key="oblitus",
            notes="Identity unknown; rumoured to be a former Auringonkirkko "
                  "archbishop. PCs must investigate.",
        ),
        OrganisationMember(
            npc_name="Radiant Calistro",
            rank_key="radiant",
            role_keys=["spymaster"],
            kingdom_key="tarmaas", city_key="frand",
            notes="Operates under cover as a noble patron of the arts.",
        ),
        OrganisationMember(
            npc_name="Radiant Mavrek",
            rank_key="radiant",
            role_keys=["inquisitor", "executioner"],
            kingdom_key="oblitus",
            notes="Public enforcer in Oblitus.",
        ),
        OrganisationMember(
            npc_name="Lightbringer Vela",
            rank_key="lightbringer",
            role_keys=["missionary"],
            kingdom_key="tarmaas", city_key="frand",
            notes="Recruits among Frand's urban poor.",
        ),
        OrganisationMember(
            npc_name="Lightbringer Doran",
            rank_key="lightbringer",
            role_keys=["quartermaster"],
            kingdom_key="smardu",
            notes="Quiet chapter inside Smardu's mining guilds.",
        ),
    ]
    operations = [
        OrganisationOperation(
            id="op_recruit_frand", name="Frandin värväyskenttä",
            kind="recruit", target_city_key="frand",
            target_kingdom_key="tarmaas", severity=2, status="active",
            timestamp="S1 D1",
            description="Lightbringer Vela rekrytoi kaupungin "
                        "köyhälistöstä \"valon palvelijoiksi\".",
        ),
        OrganisationOperation(
            id="op_smardu_quiet", name="Smardun hiljainen sijoittuminen",
            kind="intelligence", target_kingdom_key="smardu",
            severity=2, status="planned", timestamp="S1 D1",
            description="Lightbringer Doran solutaa Brotherhoodin "
                        "tukijoita kääpiöiden kaivosseuroihin.",
        ),
        OrganisationOperation(
            id="op_dawn_ritual", name="Aamunkoiton rituaali",
            kind="ritual", target_kingdom_key="oblitus",
            severity=5, status="planned", timestamp="S1 D1",
            description="Radiant Mavrek valmistelee suurriittiä "
                        "Oblituksen autiomaassa — pysäytys olisi "
                        "kampanjan pääkliimaksia.",
        ),
    ]
    return Organisation(
        key="brotherhood_of_glorious_sun",
        name="Brotherhood of Glorious Sun",
        kind="brotherhood",
        description="Veljeskunta, joka väittää kantavansa "
                    "Auringonkirkon todellista valoa — todellisuudessa "
                    "varjojen ja sopimusten kultti, joka kerää valtaa "
                    "Tarmaasin, Smardun ja Oblituksen rajoilla.",
        motto="Loiston alla varjot palvelevat.",
        secret=True,
        alignment="lawful evil",
        headquarters_city="",
        headquarters_kingdom="oblitus",
        operating_kingdoms=["tarmaas", "smardu", "oblitus"],
        operating_cities=["frand"],
        ranks=ranks, roles=roles, members=members,
        operations=operations,
        relations={},
        color=(200, 160, 60),
        tags=["antagonist", "religion", "secret_society"],
    )


SEED_ORGANISATIONS: List[Organisation] = [
    _brotherhood_of_glorious_sun(),
]


# ----------------------------------------------------------------------
# Campaign integration
# ----------------------------------------------------------------------

def ensure_organisations_on_campaign(campaign) -> List[Organisation]:
    """Rehydrate ``campaign.organisations`` from persisted dicts on first
    access. Empty campaigns are seeded from :data:`SEED_ORGANISATIONS`."""
    import copy
    runtime = getattr(campaign, "organisations", None)
    if isinstance(runtime, list) and runtime:
        return runtime
    persisted = getattr(campaign, "organisations_data", None) or []
    if persisted:
        runtime = [_org_from_dict(d) for d in persisted]
    else:
        runtime = copy.deepcopy(SEED_ORGANISATIONS)
    campaign.organisations = runtime
    return runtime


def sync_organisations_to_campaign(campaign) -> None:
    runtime = getattr(campaign, "organisations", None) or []
    campaign.organisations_data = [_org_to_dict(o) for o in runtime]


def find_organisation(campaign, key: str) -> Optional[Organisation]:
    for o in ensure_organisations_on_campaign(campaign):
        if o.key == key:
            return o
    return None


def add_organisation(campaign, key: str, name: str, **kw) -> Organisation:
    o = Organisation(key=key, name=name, **kw)
    ensure_organisations_on_campaign(campaign).append(o)
    return o


def organisations_for_npc(campaign, npc_id: str) -> List[Organisation]:
    """Every organisation that lists this NPC id as an active member."""
    if not npc_id:
        return []
    out: List[Organisation] = []
    for o in ensure_organisations_on_campaign(campaign):
        if o.member_for_npc(npc_id) is not None:
            out.append(o)
    return out


def organisations_for_npc_name(campaign, npc_name: str
                                 ) -> List[Organisation]:
    """Match by free-form name when no NPC id is set yet. Case-insensitive."""
    if not npc_name:
        return []
    needle = npc_name.lower().strip()
    out: List[Organisation] = []
    for o in ensure_organisations_on_campaign(campaign):
        for m in o.members:
            if not m.active:
                continue
            if m.npc_name and m.npc_name.lower().strip() == needle:
                out.append(o)
                break
    return out


def organisations_in_city(campaign, city_key: str) -> List[Organisation]:
    if not city_key:
        return []
    return [o for o in ensure_organisations_on_campaign(campaign)
            if city_key in o.operating_cities
            or o.headquarters_city == city_key
            or any(m.active and m.city_key == city_key for m in o.members)]


def organisations_in_kingdom(campaign, kingdom_key: str
                              ) -> List[Organisation]:
    if not kingdom_key:
        return []
    return [o for o in ensure_organisations_on_campaign(campaign)
            if kingdom_key in o.operating_kingdoms
            or o.headquarters_kingdom == kingdom_key
            or any(m.active and m.kingdom_key == kingdom_key
                   for m in o.members)]


def add_member(campaign, org_key: str, *, npc_id: str = "",
                npc_name: str = "", rank_key: str = "",
                role_keys: Optional[List[str]] = None,
                city_key: str = "", kingdom_key: str = "",
                notes: str = "") -> Optional[OrganisationMember]:
    """Add a member to an organisation. Returns the member, or None if
    the organisation does not exist."""
    o = find_organisation(campaign, org_key)
    if o is None:
        return None
    m = OrganisationMember(
        npc_id=npc_id, npc_name=npc_name, rank_key=rank_key,
        role_keys=list(role_keys or []),
        city_key=city_key, kingdom_key=kingdom_key, notes=notes,
    )
    o.members.append(m)
    return m


def add_operation(campaign, org_key: str, *, name: str,
                    kind: str = "other", target_city_key: str = "",
                    target_kingdom_key: str = "",
                    severity: int = 1, status: str = "planned",
                    timestamp: str = "", description: str = "",
                    npc_member_id: str = "",
                    quest_id: str = "") -> Optional[OrganisationOperation]:
    o = find_organisation(campaign, org_key)
    if o is None:
        return None
    op = OrganisationOperation(
        id=f"op_{len(o.operations) + 1}", name=name, kind=kind,
        target_city_key=target_city_key,
        target_kingdom_key=target_kingdom_key,
        severity=max(1, min(5, int(severity))),
        status=status, timestamp=timestamp,
        description=description, npc_member_id=npc_member_id,
        quest_id=quest_id,
    )
    o.operations.append(op)
    return op


def operations_in_city(campaign, city_key: str
                         ) -> List[OrganisationOperation]:
    """Every active or planned operation that targets a city."""
    out: List[OrganisationOperation] = []
    for o in ensure_organisations_on_campaign(campaign):
        for op in o.operations:
            if op.target_city_key == city_key and op.status in (
                    "planned", "active"):
                out.append(op)
    return out


def operations_in_kingdom(campaign, kingdom_key: str
                            ) -> List[OrganisationOperation]:
    out: List[OrganisationOperation] = []
    for o in ensure_organisations_on_campaign(campaign):
        for op in o.operations:
            if op.target_kingdom_key == kingdom_key and op.status in (
                    "planned", "active"):
                out.append(op)
    return out


def remove_member(campaign, org_key: str, npc_id: str = "",
                    npc_name: str = "") -> bool:
    """Mark a member inactive (soft delete). Returns True if removed."""
    o = find_organisation(campaign, org_key)
    if o is None:
        return False
    for m in o.members:
        if not m.active:
            continue
        if npc_id and m.npc_id == npc_id:
            m.active = False
            return True
        if npc_name and m.npc_name == npc_name:
            m.active = False
            return True
    return False
