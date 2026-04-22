"""Vehicle helpers — ships, airships, caravans, wagons.

A *vehicle* is a MapObject whose ``object_type`` is one of
:data:`data.map_engine.VEHICLE_TYPES` (``caravan``, ``ship``,
``airship``, ``wagon``). Vehicles carry a list of Actor ids in
``passenger_actor_ids``; this module wraps add/remove/transfer
operations with validation and surfaces a hover-friendly description.

Kept separate from map_engine so the core map data model stays small.
"""
from __future__ import annotations

from typing import List, Optional

from data.map_engine import MapObject, VEHICLE_TYPES


def is_vehicle(obj: MapObject) -> bool:
    return obj.object_type in VEHICLE_TYPES


def list_passengers(obj: MapObject, registry=None) -> List:
    """Return the Actor objects riding ``obj``.

    If ``registry`` is None, the module-level default registry is
    looked up on first call. Unknown ids (deleted actors) are
    silently skipped — callers should not get ``None`` in the list.
    """
    if not is_vehicle(obj):
        return []
    if registry is None:
        from data.actors import get_registry
        registry = get_registry()
    actors = []
    for aid in obj.passenger_actor_ids:
        a = registry.get(aid)
        if a is not None:
            actors.append(a)
    return actors


def add_passenger(obj: MapObject, actor_id: str,
                    registry=None) -> bool:
    """Board ``actor_id`` onto vehicle ``obj``. Returns True if the
    passenger was added (idempotent — a repeat add is a noop and
    returns True). Returns False when the object isn't a vehicle or
    when the actor id is unknown."""
    if not is_vehicle(obj) or not actor_id:
        return False
    if registry is None:
        from data.actors import get_registry
        registry = get_registry()
    if registry.get(actor_id) is None:
        return False
    if actor_id not in obj.passenger_actor_ids:
        obj.passenger_actor_ids.append(actor_id)
    return True


def remove_passenger(obj: MapObject, actor_id: str) -> bool:
    """Disembark ``actor_id`` from ``obj``. Returns True iff the id
    was on the manifest."""
    if not is_vehicle(obj):
        return False
    if actor_id in obj.passenger_actor_ids:
        obj.passenger_actor_ids.remove(actor_id)
        return True
    return False


def transfer_passenger(src: MapObject, dst: MapObject,
                         actor_id: str, registry=None) -> bool:
    """Move ``actor_id`` from one vehicle to another (e.g. hopping from
    a wagon onto an airship). Returns True only if both vehicles are
    valid AND the passenger was present on ``src``."""
    if not is_vehicle(src) or not is_vehicle(dst):
        return False
    if actor_id not in src.passenger_actor_ids:
        return False
    if registry is None:
        from data.actors import get_registry
        registry = get_registry()
    if registry.get(actor_id) is None:
        return False
    remove_passenger(src, actor_id)
    add_passenger(dst, actor_id, registry=registry)
    return True


def clear_passengers(obj: MapObject) -> int:
    """Disembark everyone. Returns how many were aboard."""
    if not is_vehicle(obj):
        return 0
    n = len(obj.passenger_actor_ids)
    obj.passenger_actor_ids.clear()
    return n


def describe_vehicle(obj: MapObject, registry=None) -> str:
    """Short one-line summary suitable for a hover tooltip.

    Example: "Stormchaser — 3 aboard: Alara, Bran, Mari"
    """
    if not is_vehicle(obj):
        return obj.label or obj.id
    label = obj.label or _VEHICLE_LABEL.get(obj.object_type, "Vehicle")
    riders = list_passengers(obj, registry=registry)
    if not riders:
        return f"{label} — empty"
    names = ", ".join(r.name for r in riders[:5])
    if len(riders) > 5:
        names += f" +{len(riders) - 5}"
    return f"{label} — {len(riders)} aboard: {names}"


_VEHICLE_LABEL = {
    "caravan": "Caravan",
    "ship":    "Ship",
    "airship": "Airship",
    "wagon":   "Wagon",
}


def scrub_actor_from_all(world_map, actor_id: str) -> int:
    """Remove ``actor_id`` from every vehicle manifest on the map —
    call this after deleting an Actor so no dangling rider ids remain.
    Returns how many vehicles had the id removed."""
    scrubbed = 0
    for layer in world_map.layers:
        for obj in layer.objects:
            if is_vehicle(obj) and actor_id in obj.passenger_actor_ids:
                obj.passenger_actor_ids.remove(actor_id)
                scrubbed += 1
    return scrubbed
