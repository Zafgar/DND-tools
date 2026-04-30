"""Post-import linkage helpers.

After ``data.text_import.import_text`` has populated a Campaign's
World, the same NPCs/locations are not automatically connected to the
shared ActorRegistry or to any existing map tokens. This module
applies that second-pass linkage in one call:

  * Every imported NPC gets an Actor in the registry (Phase 11e).
  * Every imported settlement Location gets a MapObject on the
    primary WorldMap if one isn't already there (Phase 10a bridge).
  * Map tokens whose label exactly matches an existing actor's name
    are auto-linked through ``MapObject.actor_id``.

Pure logic; no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from data.world import World
from data.actors import ActorRegistry
from data.map_engine import WorldMap, SETTLEMENT_TYPES
from data.campaign_map_sync import sync_location_to_map
from data.npc_actor_sync import (
    ensure_actor_for_npc, sync_npc_changes_to_actor,
)


@dataclass
class LinkReport:
    actors_created: int = 0
    actors_synced: int = 0
    locations_placed: int = 0
    tokens_linked_to_actor: int = 0
    skipped: List[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        if self.actors_created or self.actors_synced:
            parts.append(f"{self.actors_created}+ "
                          f"{self.actors_synced}~ actors")
        if self.locations_placed:
            parts.append(f"{self.locations_placed}+ tokens")
        if self.tokens_linked_to_actor:
            parts.append(f"{self.tokens_linked_to_actor} actor links")
        return ", ".join(parts) if parts else "no links"


def link_all(world: World, world_map: Optional[WorldMap] = None,
                registry: Optional[ActorRegistry] = None,
                *, place_settlements: bool = True) -> LinkReport:
    """Run the full linkage pass on the supplied campaign data.

    Returns a :class:`LinkReport`. None world_map / registry skips
    the corresponding sync step (so this can run early when the
    campaign exists but no interactive map has been picked yet).
    """
    report = LinkReport()
    if registry is not None:
        for npc_id, npc in list(world.npcs.items()):
            had_actor = bool(npc.actor_id) and npc.actor_id in registry
            actor = ensure_actor_for_npc(world, npc_id, registry)
            if actor is None:
                continue
            if had_actor:
                sync_npc_changes_to_actor(npc, registry)
                report.actors_synced += 1
            else:
                report.actors_created += 1

    if world_map is not None and place_settlements:
        # Default-place settlements that don't have a token yet.
        # Position is staggered so they don't pile up at (50, 50).
        for i, loc in enumerate(_settlement_locations(world)):
            existing = _find_token_for_location(world_map, loc.id)
            if existing is not None:
                continue
            x = 30.0 + (i % 6) * 8.0
            y = 30.0 + (i // 6) * 8.0
            sync_location_to_map(world, world_map, loc.id,
                                    default_x=x, default_y=y)
            report.locations_placed += 1

    if world_map is not None and registry is not None:
        # Match map tokens by label to actors with the same name.
        # Skips already-linked tokens.
        actor_by_name = {a.name.lower(): a
                          for a in registry.list_all()}
        for layer in world_map.layers:
            for obj in layer.objects:
                if obj.actor_id and obj.actor_id in registry:
                    continue  # already linked
                key = (obj.label or "").strip().lower()
                if not key:
                    continue
                actor = actor_by_name.get(key)
                if actor is None:
                    continue
                obj.actor_id = actor.id
                report.tokens_linked_to_actor += 1
    return report


# --------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------- #
def _settlement_locations(world: World):
    keys = {"capital", "city", "town", "village", "fort",
            "kingdom", "country", "stronghold", "outpost", "hamlet"}
    for loc in world.locations.values():
        if (loc.location_type or "").lower() in keys:
            yield loc


def _find_token_for_location(world_map: WorldMap, location_id: str):
    if not location_id:
        return None
    for layer in world_map.layers:
        for obj in layer.objects:
            if obj.linked_location_id == location_id:
                return obj
    return None
