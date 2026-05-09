"""One-step NPC creation — wraps NPC creation, ActorRegistry binding,
and optional portrait import in a single helper.

Replaces the legacy three-click flow:
  1. Click "+ NPC" → NPC row appears, no actor link.
  2. Click "Suhteet" → ensure_actor_for_npc creates actor.
  3. Click "NPC-portretti..." → file dialog → import_portrait_file.

With ``quick_create_npc`` the DM does all three at once and gets a
populated NPC + linked Actor + portrait_path in one transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from data.world import World, NPC, generate_id
from data.actors import ActorRegistry
from data.npc_actor_sync import ensure_actor_for_npc


@dataclass
class QuickCreateResult:
    npc_id: str = ""
    actor_id: str = ""
    portrait_path: str = ""
    warnings: List[str] = None  # type: ignore

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def quick_create_npc(world: World, *,
                       name: str,
                       race: str = "",
                       occupation: str = "",
                       location_id: str = "",
                       faction: str = "",
                       notes: str = "",
                       tags: Optional[List[str]] = None,
                       portrait_src_path: Optional[str] = None,
                       portrait_name_hint: Optional[str] = None,
                       registry: Optional[ActorRegistry] = None
                       ) -> QuickCreateResult:
    """Create an NPC, link an Actor, and (optionally) import a
    portrait. Returns the bookkeeping ids in :class:`QuickCreateResult`.

    All parameters are optional except ``name``; missing values get
    safe defaults. ``registry=None`` falls back to the project-wide
    singleton.
    """
    rep = QuickCreateResult()
    name = (name or "").strip()
    if not name:
        rep.warnings.append("name required")
        return rep

    # 1. Create NPC entry
    npc_id = generate_id(world, prefix="npc")
    npc = NPC(
        id=npc_id, name=name,
        race=race or "",
        occupation=occupation or "",
        faction=faction or "",
        location_id=location_id or "",
        notes=notes or "",
        tags=list(tags) if tags else [],
    )
    world.npcs[npc_id] = npc

    # If a location was supplied, mirror onto Location.npc_ids so
    # town summary picks it up immediately.
    if location_id and location_id in world.locations:
        loc = world.locations[location_id]
        if npc_id not in (loc.npc_ids or []):
            loc.npc_ids.append(npc_id)

    rep.npc_id = npc_id

    # 2. Bind to actor registry
    if registry is None:
        try:
            from data.actors import get_registry
            registry = get_registry()
        except Exception:
            registry = None
    if registry is not None:
        actor = ensure_actor_for_npc(world, npc_id, registry)
        if actor is not None:
            rep.actor_id = actor.id

    # 3. Import portrait
    if portrait_src_path:
        try:
            from data.portrait_loader import import_portrait_file
            rel = import_portrait_file(
                portrait_src_path,
                name_hint=(portrait_name_hint or name),
            )
        except Exception as ex:
            rep.warnings.append(f"portrait import failed: {ex}")
            rel = ""
        if rel:
            npc.portrait_path = rel
            rep.portrait_path = rel
            # Push portrait onto the linked actor so battle tokens
            # (Phase 17a) can resolve it.
            if registry is not None and rep.actor_id:
                actor = registry.get(rep.actor_id)
                if actor is not None:
                    actor.portrait_path = rel
        else:
            rep.warnings.append("portrait import returned empty path")

    return rep
