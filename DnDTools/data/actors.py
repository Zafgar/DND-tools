"""Actor registry — a single source of truth for *who* a token is,
independent of *where* it appears.

The problem this solves: a hero or NPC can appear simultaneously on the
world map (tiny pin), in a town view (medium portrait), and in a
tactical battle (full 5-ft grid square). Without a shared identity each
view stores its own ``name``/``color`` and they drift out of sync.

An ``Actor`` is that shared identity. MapObjects and battle Entities
both carry an optional ``actor_id`` pointing at one, so any view can
resolve ``registry.get(actor_id)`` to show the same portrait, colour,
notes, and stats.

Persistence: ``saves/actors.json`` is read on startup (created on first
save) so actors survive across sessions.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import uuid


ACTOR_KINDS = ("hero", "npc", "monster", "vehicle", "unknown")

# Per-view default pixel sizes — views can still override but these
# give sensible defaults that keep world-map tokens from overwhelming
# the map.
DEFAULT_WORLD_PX = 16
DEFAULT_TOWN_PX = 32


def _new_id() -> str:
    return f"actor_{uuid.uuid4().hex[:10]}"


@dataclass
class Actor:
    id: str = ""
    name: str = ""
    kind: str = "npc"             # hero / npc / monster / vehicle / unknown
    portrait_path: str = ""
    color: Tuple[int, int, int] = (200, 200, 200)
    # Optional link to a CreatureStats entry in data.library (monsters)
    # or in data.heroes (players). Empty means no combat stats.
    stats_name: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    world_px: int = DEFAULT_WORLD_PX
    town_px: int = DEFAULT_TOWN_PX
    # Vehicle-specific: crew/passenger actor ids
    passenger_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id()
        if self.kind not in ACTOR_KINDS:
            self.kind = "unknown"
        # Colour might be saved as a list — coerce back to tuple
        if isinstance(self.color, list):
            self.color = tuple(self.color)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["color"] = list(self.color)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Actor":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            kind=d.get("kind", "npc"),
            portrait_path=d.get("portrait_path", ""),
            color=tuple(d.get("color", (200, 200, 200))),
            stats_name=d.get("stats_name", ""),
            notes=d.get("notes", ""),
            tags=list(d.get("tags", [])),
            world_px=int(d.get("world_px", DEFAULT_WORLD_PX)),
            town_px=int(d.get("town_px", DEFAULT_TOWN_PX)),
            passenger_ids=list(d.get("passenger_ids", [])),
        )


class ActorRegistry:
    def __init__(self):
        self._actors: Dict[str, Actor] = {}

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def add(self, actor: Actor) -> Actor:
        self._actors[actor.id] = actor
        return actor

    def create(self, name: str, kind: str = "npc", **kwargs) -> Actor:
        a = Actor(name=name, kind=kind, **kwargs)
        return self.add(a)

    def remove(self, actor_id: str) -> bool:
        if actor_id not in self._actors:
            return False
        # Scrub any passenger references so vehicles don't hold dangling ids
        for a in self._actors.values():
            if actor_id in a.passenger_ids:
                a.passenger_ids.remove(actor_id)
        del self._actors[actor_id]
        return True

    def get(self, actor_id: str) -> Optional[Actor]:
        return self._actors.get(actor_id)

    def get_by_name(self, name: str) -> Optional[Actor]:
        key = name.strip().lower()
        for a in self._actors.values():
            if a.name.lower() == key:
                return a
        return None

    def list_all(self) -> List[Actor]:
        return sorted(self._actors.values(), key=lambda a: a.name.lower())

    def list_by_kind(self, kind: str) -> List[Actor]:
        return [a for a in self.list_all() if a.kind == kind]

    def __len__(self) -> int:
        return len(self._actors)

    def __contains__(self, actor_id: str) -> bool:
        return actor_id in self._actors

    # ------------------------------------------------------------------ #
    # Vehicle / passenger convenience
    # ------------------------------------------------------------------ #
    def add_passenger(self, vehicle_id: str, passenger_id: str) -> bool:
        vehicle = self.get(vehicle_id)
        if vehicle is None or vehicle.kind != "vehicle":
            return False
        if passenger_id not in self._actors:
            return False
        if passenger_id not in vehicle.passenger_ids:
            vehicle.passenger_ids.append(passenger_id)
        return True

    def remove_passenger(self, vehicle_id: str, passenger_id: str) -> bool:
        vehicle = self.get(vehicle_id)
        if vehicle is None or vehicle.kind != "vehicle":
            return False
        if passenger_id in vehicle.passenger_ids:
            vehicle.passenger_ids.remove(passenger_id)
            return True
        return False

    # ------------------------------------------------------------------ #
    # Resolve from the embedding objects
    # ------------------------------------------------------------------ #
    def resolve(self, obj) -> Optional[Actor]:
        """Look up the actor referenced by ``obj`` — either a MapObject
        or battle Entity. Returns None when the object has no actor_id
        set or the id is unknown."""
        aid = getattr(obj, "actor_id", "") or ""
        return self.get(aid) if aid else None

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {"actors": [a.to_dict() for a in self._actors.values()]}

    def load_dict(self, data: dict):
        self._actors.clear()
        for d in data.get("actors", []):
            a = Actor.from_dict(d)
            if a.id:
                self._actors[a.id] = a

    def save(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> bool:
        if not os.path.isfile(path):
            return False
        try:
            with open(path, encoding="utf-8") as f:
                self.load_dict(json.load(f))
            return True
        except (json.JSONDecodeError, OSError):
            return False


# --------------------------------------------------------------------- #
# Module-level singleton (lazy)
# --------------------------------------------------------------------- #
_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "saves", "actors.json"
)

_registry: Optional[ActorRegistry] = None


def get_registry() -> ActorRegistry:
    """Return the process-wide ActorRegistry, loading from disk on first
    access. The registry persists across sessions at saves/actors.json."""
    global _registry
    if _registry is None:
        _registry = ActorRegistry()
        _registry.load(_DEFAULT_PATH)
    return _registry


def save_registry():
    """Persist the default registry to disk."""
    if _registry is not None:
        _registry.save(_DEFAULT_PATH)


def reset_registry_for_tests():
    """Drop the in-memory singleton; next get_registry() will re-init."""
    global _registry
    _registry = None
