"""Multi-select picker helpers — wrap a SearchableDropdown so the
DM can attach / detach multiple ids to a list field (quest.npc_ids,
quest.location_ids, MapObject.linked_npc_ids, etc.).

Usage:

    picker = MultiNPCPicker(world, lambda npc_id: toggle(npc_id, list))
    picker.open(anchor_rect)

The picker opens once per click; the caller decides whether to
re-open after a pick (for chain selection).
"""
from __future__ import annotations

from typing import Callable, List, Optional

from data.world import World
from data.npc_actor_sync import search_npcs, search_locations
from states.searchable_dropdown import (
    SearchableDropdown, DropdownEntry,
)


def toggle_in_list(item_id: str, the_list: list) -> bool:
    """If ``item_id`` is in the list, remove it. Otherwise append.
    Returns True when added, False when removed."""
    if not item_id:
        return False
    if item_id in the_list:
        the_list.remove(item_id)
        return False
    the_list.append(item_id)
    return True


# --------------------------------------------------------------------- #
# Multi NPC picker
# --------------------------------------------------------------------- #
class MultiNPCPicker:
    def __init__(self, world: World,
                  on_pick: Callable[[Optional[str]], None],
                  *, max_results: int = 50):
        self.world = world
        self.on_pick = on_pick

        def _query_fn(q: str) -> List[DropdownEntry]:
            entries = []
            for npc in search_npcs(self.world, q, limit=max_results):
                sub = " · ".join(b for b in
                                  (npc.occupation, npc.faction)
                                  if b)
                entries.append(DropdownEntry(id=npc.id,
                                                label=npc.name,
                                                sub=sub))
            return entries

        self._dropdown = SearchableDropdown(
            query_fn=_query_fn,
            on_select=self._handle_pick,
            placeholder="Hae NPC...",
        )

    @property
    def is_open(self) -> bool:
        return self._dropdown.is_open

    def open(self, anchor_rect):
        self._dropdown.open(anchor_rect=anchor_rect)

    def close(self, *, commit: bool = False):
        self._dropdown.close(commit=commit)

    def handle_event(self, event) -> bool:
        return self._dropdown.handle_event(event)

    def draw(self, screen):
        self._dropdown.draw(screen)

    def _handle_pick(self, npc_id: Optional[str]):
        self.on_pick(npc_id)


# --------------------------------------------------------------------- #
# Multi Location picker
# --------------------------------------------------------------------- #
class MultiLocationPicker:
    def __init__(self, world: World,
                  on_pick: Callable[[Optional[str]], None],
                  *, location_type: Optional[str] = None,
                  max_results: int = 50):
        self.world = world
        self.on_pick = on_pick
        self.location_type = location_type

        def _query_fn(q: str) -> List[DropdownEntry]:
            entries = []
            for loc in search_locations(self.world, q,
                                            location_type=self.location_type,
                                            limit=max_results):
                entries.append(DropdownEntry(
                    id=loc.id, label=loc.name,
                    sub=loc.location_type or "",
                ))
            return entries

        self._dropdown = SearchableDropdown(
            query_fn=_query_fn,
            on_select=self._handle_pick,
            placeholder="Hae lokaatio...",
        )

    @property
    def is_open(self) -> bool:
        return self._dropdown.is_open

    def open(self, anchor_rect):
        self._dropdown.open(anchor_rect=anchor_rect)

    def close(self, *, commit: bool = False):
        self._dropdown.close(commit=commit)

    def handle_event(self, event) -> bool:
        return self._dropdown.handle_event(event)

    def draw(self, screen):
        self._dropdown.draw(screen)

    def _handle_pick(self, loc_id: Optional[str]):
        self.on_pick(loc_id)
