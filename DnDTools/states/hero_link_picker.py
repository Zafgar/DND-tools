"""Hero / party-member link picker — pygame widget that lets the DM
pick a PC from the campaign party using the same searchable
dropdown as :mod:`states.npc_link_picker`.

Used by the relationship matrix (Phase 15e) and anywhere else the
DM needs to point at "this hero" instead of typing the name.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Set

from data.npc_actor_sync import search_party_members
from states.searchable_dropdown import (
    SearchableDropdown, DropdownEntry,
)


class HeroLinkPicker:
    def __init__(self, campaign,
                  on_pick: Callable[[Optional[str]], None],
                  *, max_results: int = 50):
        self.campaign = campaign
        self.on_pick = on_pick
        self.exclude_names: Set[str] = set()

        def _query_fn(q: str) -> List[DropdownEntry]:
            members = search_party_members(self.campaign, q,
                                              limit=max_results)
            entries = []
            for member in members:
                hero = getattr(member, "hero_data", {}) or {}
                name = hero.get("name", "")
                if not name or name in self.exclude_names:
                    continue
                # Sub-label: class + level if known
                cls = hero.get("character_class", "")
                lvl = hero.get("character_level", "")
                bits = []
                if cls:
                    bits.append(cls.title())
                if lvl:
                    bits.append(f"lv{lvl}")
                entries.append(DropdownEntry(
                    id=name, label=name,
                    sub=" · ".join(bits),
                ))
            return entries

        self._dropdown = SearchableDropdown(
            query_fn=_query_fn,
            on_select=self._handle_pick,
            placeholder="Hae hahmo...",
        )

    @property
    def is_open(self) -> bool:
        return self._dropdown.is_open

    def open(self, anchor_rect, *,
              exclude_names=None,
              initial_query: str = "",
              selected_name: Optional[str] = None):
        self.exclude_names = set(exclude_names or ())
        self._dropdown.open(anchor_rect=anchor_rect,
                              initial_query=initial_query,
                              selected_id=selected_name)

    def close(self, *, commit: bool = False):
        self._dropdown.close(commit=commit)

    def handle_event(self, event) -> bool:
        return self._dropdown.handle_event(event)

    def draw(self, screen):
        self._dropdown.draw(screen)

    def _handle_pick(self, hero_name: Optional[str]):
        self.on_pick(hero_name)
