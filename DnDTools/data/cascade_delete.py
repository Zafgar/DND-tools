"""Cascade-delete helpers — when the DM removes an NPC, location,
or actor we scrub every dangling reference instead of leaving
zombie ids around to corrupt downstream queries.

Pure logic, no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from data.world import World, Location, NPC, Shop, Service


@dataclass
class CascadeReport:
    """Summary of what a cascade-delete touched."""
    target_kind: str = ""
    target_id: str = ""
    npcs_deleted: int = 0
    npcs_unlinked: int = 0
    shops_deleted: int = 0
    shops_unlinked: int = 0
    services_deleted: int = 0
    services_unlinked: int = 0
    locations_deleted: int = 0
    locations_orphaned: int = 0
    map_objects_unlinked: int = 0
    actors_removed: int = 0
    quests_unlinked: int = 0
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        bits = []
        if self.npcs_deleted:
            bits.append(f"{self.npcs_deleted} NPC poistettu")
        if self.npcs_unlinked:
            bits.append(f"{self.npcs_unlinked} NPC irrotettu")
        if self.shops_deleted:
            bits.append(f"{self.shops_deleted} kauppaa poistettu")
        if self.shops_unlinked:
            bits.append(f"{self.shops_unlinked} kauppaa irrotettu")
        if self.services_unlinked:
            bits.append(f"{self.services_unlinked} palvelua irrotettu")
        if self.locations_deleted:
            bits.append(f"{self.locations_deleted} lokaatiota poistettu")
        if self.map_objects_unlinked:
            bits.append(f"{self.map_objects_unlinked} tokenia siivottu")
        if self.actors_removed:
            bits.append(f"{self.actors_removed} aktoria")
        return " · ".join(bits) if bits else "ei muutoksia"


# --------------------------------------------------------------------- #
# NPC delete
# --------------------------------------------------------------------- #
def delete_npc(world: World, npc_id: str, *,
                 world_map=None, registry=None,
                 remove_actor: bool = False) -> CascadeReport:
    """Delete an NPC and scrub references.

    * ``shops`` whose owner_npc_id matches → owner cleared (shop kept).
    * ``services`` whose npc_id matches → cleared.
    * ``world.locations[*].npc_ids`` lists → entry removed.
    * ``Location.linked_npc_ids`` is not present, but ``MapObject.
      linked_npc_ids`` lists are scrubbed when ``world_map`` is given.
    * The optional ``registry`` is consulted for the linked Actor;
      ``remove_actor=True`` deletes it. Otherwise Actor stays.
    """
    rep = CascadeReport(target_kind="npc", target_id=npc_id)
    if npc_id not in world.npcs:
        return rep
    npc = world.npcs[npc_id]
    actor_id = getattr(npc, "actor_id", "")

    # Scrub shops + services
    for shop in world.shops.values():
        if shop.owner_npc_id == npc_id:
            shop.owner_npc_id = ""
            rep.shops_unlinked += 1
    for svc in world.services.values():
        if svc.npc_id == npc_id:
            svc.npc_id = ""
            rep.services_unlinked += 1

    # Scrub Location.npc_ids
    for loc in world.locations.values():
        if npc_id in (loc.npc_ids or []):
            loc.npc_ids = [x for x in loc.npc_ids if x != npc_id]

    # Scrub map tokens that link to this NPC
    if world_map is not None:
        for layer in world_map.layers:
            for obj in layer.objects:
                if npc_id in obj.linked_npc_ids:
                    obj.linked_npc_ids = [x for x in obj.linked_npc_ids
                                            if x != npc_id]
                    rep.map_objects_unlinked += 1

    # Scrub actor link
    if registry is not None and actor_id:
        if remove_actor and actor_id in registry:
            registry.remove(actor_id)
            rep.actors_removed += 1

    # Drop the NPC itself
    del world.npcs[npc_id]
    rep.npcs_deleted = 1
    return rep


# --------------------------------------------------------------------- #
# Location delete
# --------------------------------------------------------------------- #
def delete_location(world: World, location_id: str, *,
                       world_map=None,
                       cascade_npcs: bool = False) -> CascadeReport:
    """Delete a location.

    By default attached NPCs / shops / services have their
    location_id cleared (they survive, just unmoored). Pass
    ``cascade_npcs=True`` to delete the NPCs too.

    Map tokens linked to the location have their ``linked_location_id``
    cleared via the shared bridge so stale tokens don't re-create the
    location on next sync.

    Children locations are *promoted* to top-level (parent_id cleared)
    rather than deleted — losing whole regions because the DM
    deleted a parent feels like a bug.
    """
    rep = CascadeReport(target_kind="location",
                          target_id=location_id)
    if location_id not in world.locations:
        return rep

    # Clear children's parent_id
    for loc in world.locations.values():
        if loc.parent_id == location_id:
            loc.parent_id = ""
            rep.locations_orphaned += 1

    # NPCs at this location
    for npc_id, npc in list(world.npcs.items()):
        if npc.location_id == location_id:
            if cascade_npcs:
                sub = delete_npc(world, npc_id, world_map=world_map)
                rep.npcs_deleted += sub.npcs_deleted
            else:
                npc.location_id = ""
                rep.npcs_unlinked += 1

    # Shops + services at this location → location cleared
    for shop in world.shops.values():
        if shop.location_id == location_id:
            shop.location_id = ""
            rep.shops_unlinked += 1
    for svc in world.services.values():
        if svc.location_id == location_id:
            svc.location_id = ""
            rep.services_unlinked += 1

    # Map tokens linking back here
    if world_map is not None:
        try:
            from data.campaign_map_sync import unlink_location
            n = unlink_location(world_map, location_id)
            rep.map_objects_unlinked += n
        except Exception:
            pass

    # Quests pointing at this location
    for q in world.quests.values():
        if location_id in (q.location_ids or []):
            q.location_ids = [x for x in q.location_ids
                                if x != location_id]
            rep.quests_unlinked += 1

    del world.locations[location_id]
    rep.locations_deleted = 1
    return rep


# --------------------------------------------------------------------- #
# Shop delete (small)
# --------------------------------------------------------------------- #
def delete_shop(world: World, shop_id: str) -> CascadeReport:
    rep = CascadeReport(target_kind="shop", target_id=shop_id)
    if shop_id in world.shops:
        del world.shops[shop_id]
        rep.shops_deleted = 1
    return rep


def delete_service(world: World, service_id: str) -> CascadeReport:
    rep = CascadeReport(target_kind="service", target_id=service_id)
    if service_id in world.services:
        del world.services[service_id]
        rep.services_deleted = 1
    return rep


# --------------------------------------------------------------------- #
# Integrity audit
# --------------------------------------------------------------------- #
def find_orphan_references(world: World) -> dict:
    """Walk the world for ids that point at deleted entities. Useful
    for a "data integrity check" diagnostic."""
    orphans = {
        "shops_with_missing_owner": [],
        "shops_at_missing_location": [],
        "services_at_missing_location": [],
        "npcs_at_missing_location": [],
        "quests_with_missing_location": [],
    }
    for shop in world.shops.values():
        if shop.owner_npc_id and shop.owner_npc_id not in world.npcs:
            orphans["shops_with_missing_owner"].append(shop.id)
        if shop.location_id and shop.location_id not in world.locations:
            orphans["shops_at_missing_location"].append(shop.id)
    for svc in world.services.values():
        if svc.location_id and svc.location_id not in world.locations:
            orphans["services_at_missing_location"].append(svc.id)
    for npc in world.npcs.values():
        if npc.location_id and npc.location_id not in world.locations:
            orphans["npcs_at_missing_location"].append(npc.id)
    for q in world.quests.values():
        for loc_id in q.location_ids or []:
            if loc_id not in world.locations:
                orphans["quests_with_missing_location"].append(q.id)
                break
    return orphans
