"""NPC link picker — a thin controller that binds
``SearchableDropdown`` to the campaign world's NPC list (Phase 11e
search). Used by the map-object edit modal and the campaign manager
to replace the legacy "type the NPC id by hand" field.

Usage:

    picker = NPCLinkPicker(world, on_pick=lambda npc_id: ...)
    picker.open(anchor_rect=(x, y, w, h), exclude_ids={"npc_3"})
    # Forward events: picker.handle_event(event)
    # And drawing: picker.draw(screen)
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Set

from data.world import World
from data.npc_actor_sync import search_npcs
from states.searchable_dropdown import SearchableDropdown, DropdownEntry


class NPCLinkPicker:
    def __init__(self, world: World,
                  on_pick: Callable[[Optional[str]], None],
                  *, max_results: int = 50):
        self.world = world
        self.on_pick = on_pick
        self.exclude_ids: Set[str] = set()

        def _query_fn(q: str) -> List[DropdownEntry]:
            results = search_npcs(self.world, q, limit=max_results)
            entries = []
            for npc in results:
                if npc.id in self.exclude_ids:
                    continue
                sub_bits = [b for b in (npc.occupation, npc.faction)
                             if b]
                entries.append(DropdownEntry(
                    id=npc.id, label=npc.name,
                    sub=" · ".join(sub_bits),
                ))
            return entries

        self._dropdown = SearchableDropdown(
            query_fn=_query_fn,
            on_select=self._handle_pick,
            placeholder="Hae NPC...",
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @property
    def is_open(self) -> bool:
        return self._dropdown.is_open

    def open(self, anchor_rect, *,
              exclude_ids: Optional[Iterable[str]] = None,
              initial_query: str = "",
              selected_id: Optional[str] = None):
        self.exclude_ids = set(exclude_ids or ())
        self._dropdown.open(anchor_rect=anchor_rect,
                              initial_query=initial_query,
                              selected_id=selected_id)

    def close(self, *, commit: bool = False):
        self._dropdown.close(commit=commit)

    # ------------------------------------------------------------------ #
    # Events / draw forwarding
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        return self._dropdown.handle_event(event)

    def draw(self, screen):
        self._dropdown.draw(screen)

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #
    def _handle_pick(self, npc_id: Optional[str]):
        # Forward exactly what the dropdown supplies — None when the
        # picker dismissed without committing.
        self.on_pick(npc_id)


# --------------------------------------------------------------------- #
# Convenience: append-to-list callback for the legacy linked_npc_ids
# CSV field. UI code can call:
#
#     picker = NPCLinkPicker(
#         world,
#         on_pick=link_npc_to_object_callback(obj),
#     )
# --------------------------------------------------------------------- #
def link_npc_to_object_callback(obj) -> Callable[[Optional[str]], None]:
    """Return an ``on_pick`` callback that appends the picked NPC id
    to ``obj.linked_npc_ids`` (no duplicates). Called with None on
    cancel — the callback no-ops."""
    def _cb(npc_id: Optional[str]):
        if not npc_id:
            return
        if npc_id not in obj.linked_npc_ids:
            obj.linked_npc_ids.append(npc_id)
    return _cb
