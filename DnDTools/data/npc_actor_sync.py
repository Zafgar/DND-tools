"""Bridge between campaign ``World.npcs`` and the shared
``ActorRegistry``.

Same idea as ``campaign_map_sync.py`` but for NPCs:

  * ``ensure_actor_for_npc(world, npc_id, registry)`` makes sure the
    NPC has a matching Actor (creates one on first call, links it
    on subsequent calls).
  * ``sync_npc_changes_to_actor(npc, registry)`` pushes changes from
    the campaign manager into the Actor (label / notes / tags) so
    the same identity across views never drifts.
  * ``unlink_npc(npc)`` clears the actor_id when the DM wants the
    NPC and the Actor decoupled.

A second concern this module handles: the user complaint that
"link an NPC" is a free-text field instead of a searchable dropdown.

  * ``search_npcs(world, query)`` returns NPCs whose name / occupation
    / tags / faction loosely match a search string — perfect for a
    UI dropdown.
  * ``search_actors(registry, query, kind=None)`` does the same for
    the Actor registry.
  * ``search_locations(world, query, kind=None)`` for settlements.

Pure logic, no pygame.
"""
from __future__ import annotations

from typing import List, Optional

from data.world import World, NPC, Location
from data.actors import Actor, ActorRegistry, ACTOR_KINDS


def ensure_actor_for_npc(world: World, npc_id: str,
                           registry: ActorRegistry) -> Optional[Actor]:
    """Return (creating if needed) the Actor bound to ``npc_id``.
    Returns None when the NPC doesn't exist."""
    if npc_id not in world.npcs:
        return None
    npc = world.npcs[npc_id]
    if npc.actor_id and npc.actor_id in registry:
        return registry.get(npc.actor_id)
    actor = registry.create(
        name=npc.name or npc_id,
        kind="npc",
        notes=(npc.notes or "")[:200],
        tags=list(npc.tags) if npc.tags else [],
    )
    npc.actor_id = actor.id
    return actor


def sync_npc_changes_to_actor(npc: NPC,
                                registry: ActorRegistry) -> Optional[Actor]:
    """Push NPC name / notes / tags into the linked Actor. Returns the
    Actor (or None when the NPC isn't linked yet)."""
    if not npc.actor_id or npc.actor_id not in registry:
        return None
    actor = registry.get(npc.actor_id)
    if actor is None:
        return None
    actor.name = npc.name or actor.name
    actor.notes = (npc.notes or "")[:200]
    actor.tags = list(npc.tags) if npc.tags else []
    return actor


def unlink_npc(npc: NPC) -> bool:
    """Drop the actor_id on ``npc``. Returns True if a link was
    cleared."""
    if not npc.actor_id:
        return False
    npc.actor_id = ""
    return True


# --------------------------------------------------------------------- #
# Searchable dropdown helpers
# --------------------------------------------------------------------- #
def _norm(s: str) -> str:
    return (s or "").strip().lower()


def search_npcs(world: World, query: str = "",
                  *, limit: int = 50) -> List[NPC]:
    """Filter ``world.npcs`` by a loose name / occupation / tag /
    faction match. Empty query → everyone, capped at ``limit``.
    Sorted alphabetically by name."""
    q = _norm(query)
    out = []
    for npc in world.npcs.values():
        if not q:
            out.append(npc)
            continue
        haystack = " ".join([
            _norm(npc.name), _norm(npc.occupation),
            _norm(npc.faction), _norm(npc.title),
            _norm(npc.race),
            _norm(" ".join(npc.tags or [])),
        ])
        if q in haystack:
            out.append(npc)
    out.sort(key=lambda n: n.name.lower())
    return out[:limit]


def search_actors(registry: ActorRegistry, query: str = "",
                    *, kind: Optional[str] = None,
                    limit: int = 50) -> List[Actor]:
    """Filter the actor registry by name / tags. Optionally restrict
    to a kind (hero / npc / monster / vehicle)."""
    q = _norm(query)
    if kind is not None and kind not in ACTOR_KINDS:
        kind = None
    out = []
    for a in registry.list_all():
        if kind is not None and a.kind != kind:
            continue
        if not q:
            out.append(a)
            continue
        haystack = " ".join([
            _norm(a.name),
            _norm(" ".join(a.tags or [])),
            _norm(a.notes),
        ])
        if q in haystack:
            out.append(a)
    return out[:limit]


def search_locations(world: World, query: str = "",
                       *, location_type: Optional[str] = None,
                       limit: int = 50) -> List[Location]:
    """Filter campaign locations by name / tags. Optionally restrict
    to a single type (city / town / etc.)."""
    q = _norm(query)
    out = []
    for loc in world.locations.values():
        if (location_type is not None
                and (loc.location_type or "").lower() != location_type.lower()):
            continue
        if not q:
            out.append(loc)
            continue
        haystack = " ".join([
            _norm(loc.name),
            _norm(loc.location_type),
            _norm(loc.description),
            _norm(" ".join(loc.tags or [])),
        ])
        if q in haystack:
            out.append(loc)
    out.sort(key=lambda l: l.name.lower())
    return out[:limit]


def search_party_members(campaign, query: str = "",
                            *, limit: int = 50) -> list:
    """Filter Campaign.party by hero name. Returns PartyMember
    instances; the caller pulls the hero name from
    ``member.hero_data.get("name", "")``."""
    q = _norm(query)
    out = []
    for member in (getattr(campaign, "party", []) or []):
        hero_data = getattr(member, "hero_data", {}) or {}
        name = hero_data.get("name", "")
        if not q:
            out.append(member)
            continue
        if q in _norm(name):
            out.append(member)
    out.sort(key=lambda m: (m.hero_data.get("name", "") or "").lower())
    return out[:limit]


def search_actors_for_npc_link(world: World,
                                  registry: ActorRegistry,
                                  query: str = "",
                                  *, exclude_npc_id: str = "") -> List[Actor]:
    """Specialised search for the "link this NPC to an Actor" UI.
    Excludes the actor_id of the NPC itself when a query is used so
    the picker doesn't suggest re-linking to the existing actor."""
    actors = search_actors(registry, query, kind="npc")
    if exclude_npc_id and exclude_npc_id in world.npcs:
        existing_aid = world.npcs[exclude_npc_id].actor_id
        if existing_aid:
            actors = [a for a in actors if a.id != existing_aid]
    return actors
