"""Searchable dropdown widget — a tiny, generic UI control built on
top of the Phase 11e search helpers.

The control is detached from any specific data source: callers
provide a ``query_fn(query: str) -> List[(id, label, sub_label)]``
that yields rows for the current query, and an ``on_select(id)``
callback fired when the user picks one. Used by the campaign
manager's "Link this NPC to ..." field, the location picker, etc.

The widget can be placed anywhere on screen (caller passes an anchor
rect). Filtering, scrolling, and keyboard navigation are pure
logic — the pygame dependency is confined to ``draw`` and event
parsing. Lifecycle / state is testable headlessly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

try:
    import pygame  # type: ignore
except ImportError:
    pygame = None


@dataclass
class DropdownEntry:
    """One picker row.

    ``id`` is opaque (the caller's reference key). ``label`` is the
    bold first line. ``sub`` is the optional dim second line."""
    id: str
    label: str
    sub: str = ""


class SearchableDropdown:
    """Generic searchable picker. Construction is cheap; draw + event
    handling fire only when ``is_open``."""

    ROW_H = 36

    def __init__(self,
                  query_fn: Callable[[str], List[DropdownEntry]],
                  on_select: Callable[[Optional[str]], None],
                  *, placeholder: str = "Hae...",
                  max_visible_rows: int = 8):
        self.query_fn = query_fn
        self.on_select = on_select
        self.placeholder = placeholder
        self.max_visible_rows = max_visible_rows

        # State
        self.is_open = False
        self.query = ""
        self._results: List[DropdownEntry] = []
        self.highlight_idx = -1   # which result is keyboard-highlighted
        self.scroll = 0
        self.anchor_rect = None   # set on open()
        self.selected_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self, anchor_rect, *, initial_query: str = "",
              selected_id: Optional[str] = None):
        """Show the dropdown anchored to ``anchor_rect`` (a 4-tuple
        or pygame.Rect). Refreshes the result list immediately."""
        self.is_open = True
        self.anchor_rect = anchor_rect
        self.query = initial_query
        self.selected_id = selected_id
        self.scroll = 0
        self._refresh_results()
        # Keyboard cursor sits on the previously-selected row when
        # possible.
        self.highlight_idx = self._index_of(selected_id) if selected_id else -1

    def close(self, *, commit: bool = False):
        """Close the dropdown. If ``commit`` is True and a row is
        highlighted, fire ``on_select`` with that id. Otherwise call
        on_select(None) so the caller knows the picker dismissed."""
        self.is_open = False
        if commit and 0 <= self.highlight_idx < len(self._results):
            self.on_select(self._results[self.highlight_idx].id)
        else:
            self.on_select(None)

    # ------------------------------------------------------------------ #
    # State helpers
    # ------------------------------------------------------------------ #
    def _refresh_results(self):
        try:
            self._results = list(self.query_fn(self.query)) or []
        except Exception:
            self._results = []
        # Clamp highlight if the result list shrank
        if self.highlight_idx >= len(self._results):
            self.highlight_idx = len(self._results) - 1

    def _index_of(self, entry_id: Optional[str]) -> int:
        if not entry_id:
            return -1
        for i, e in enumerate(self._results):
            if e.id == entry_id:
                return i
        return -1

    def set_query(self, q: str):
        """Replace the query string and refresh results."""
        self.query = q
        self._refresh_results()
        self.scroll = 0
        if self._results:
            self.highlight_idx = 0
        else:
            self.highlight_idx = -1

    def append_to_query(self, ch: str):
        if ch == "\b":
            self.query = self.query[:-1]
        else:
            self.query += ch
        self._refresh_results()
        self.scroll = 0
        if self._results:
            self.highlight_idx = 0

    def move_highlight(self, delta: int):
        if not self._results:
            return
        self.highlight_idx = max(
            0, min(len(self._results) - 1, self.highlight_idx + delta)
        )
        # Scroll into view
        if self.highlight_idx < self.scroll:
            self.scroll = self.highlight_idx
        elif self.highlight_idx >= self.scroll + self.max_visible_rows:
            self.scroll = self.highlight_idx - self.max_visible_rows + 1

    def commit_highlighted(self):
        if 0 <= self.highlight_idx < len(self._results):
            self.on_select(self._results[self.highlight_idx].id)
            self.is_open = False
            return True
        return False

    def commit_index(self, idx: int) -> bool:
        if 0 <= idx < len(self._results):
            self.on_select(self._results[idx].id)
            self.is_open = False
            return True
        return False

    # ------------------------------------------------------------------ #
    # Pygame events / draw
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open or pygame is None:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.commit_highlighted()
                return True
            if event.key == pygame.K_DOWN:
                self.move_highlight(+1)
                return True
            if event.key == pygame.K_UP:
                self.move_highlight(-1)
                return True
            if event.key == pygame.K_BACKSPACE:
                self.append_to_query("\b")
                return True
            if event.unicode and event.unicode.isprintable():
                self.append_to_query(event.unicode)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click on a row → commit
            for i, rect in enumerate(self._row_rects()):
                if rect.collidepoint(event.pos):
                    self.commit_index(self.scroll + i)
                    return True
            # Outside → dismiss
            self.close()
            return True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(
                0, min(self.scroll - event.y,
                        max(0, len(self._results) - self.max_visible_rows)),
            )
            return True
        return False

    def _row_rects(self) -> List["pygame.Rect"]:
        if pygame is None or self.anchor_rect is None:
            return []
        ar = pygame.Rect(*self.anchor_rect) if not hasattr(
            self.anchor_rect, "x") else self.anchor_rect
        rows = []
        body_top = ar.bottom + 2
        for i in range(min(self.max_visible_rows,
                             max(0, len(self._results) - self.scroll))):
            rows.append(pygame.Rect(ar.x, body_top + i * self.ROW_H,
                                      ar.width, self.ROW_H))
        return rows

    def draw(self, screen):
        if not self.is_open or pygame is None or self.anchor_rect is None:
            return
        from settings import COLORS
        from ui.components import fonts
        ar = pygame.Rect(*self.anchor_rect) if not hasattr(
            self.anchor_rect, "x") else self.anchor_rect

        # Search field on top of the anchor
        pygame.draw.rect(screen, COLORS.get("bg_dark", (20, 20, 26)),
                         ar, border_radius=4)
        pygame.draw.rect(screen, COLORS.get("accent", (180, 180, 240)),
                         ar, 1, border_radius=4)
        text = self.query or self.placeholder
        col = (COLORS.get("text", (220, 220, 220)) if self.query
                else COLORS.get("text_dim", (140, 140, 140)))
        screen.blit(fonts.small.render(text, True, col),
                    (ar.x + 8, ar.y + 6))

        # Result rows
        for i, rect in enumerate(self._row_rects()):
            entry = self._results[self.scroll + i]
            is_hi = (self.scroll + i) == self.highlight_idx
            bg = (COLORS.get("accent", (180, 180, 240)) if is_hi
                   else COLORS.get("panel", (40, 40, 50)))
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            screen.blit(
                fonts.small_bold.render(
                    entry.label, True,
                    COLORS.get("text_bright", (240, 240, 240)),
                ),
                (rect.x + 8, rect.y + 4),
            )
            if entry.sub:
                screen.blit(
                    fonts.tiny.render(entry.sub, True,
                                        COLORS.get("text_dim",
                                                     (160, 160, 160))),
                    (rect.x + 8, rect.y + 18),
                )

        # No-results badge
        if not self._results:
            note = pygame.Rect(ar.x, ar.bottom + 2,
                                 ar.width, self.ROW_H)
            pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 50)),
                             note, border_radius=4)
            screen.blit(
                fonts.small.render("(ei tuloksia)", True,
                                      COLORS.get("text_dim",
                                                   (140, 140, 140))),
                (note.x + 8, note.y + 8),
            )
