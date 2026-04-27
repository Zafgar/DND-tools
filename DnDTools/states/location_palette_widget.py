"""Pygame widget that renders the campaign-locations drag-onto-map
palette. Pure UI on top of ``data/location_palette.py``.

Toggle with ``palette_open = True`` from the editor's tool button. The
widget paints a sidebar over the right detail panel with:

  * A search field at the top.
  * A scrollable list of unplaced + placed settlements.
  * Click an entry → drops the linked MapObject at the centre of the
    canvas (or returns the entry so the caller can drag it onto the
    canvas at a chosen point).

The widget is intentionally small — most of the work is data
filtering, which the test-covered helpers in
``data/location_palette.py`` handle.
"""
from __future__ import annotations

import pygame

from settings import COLORS
from ui.components import Button, fonts
from data.location_palette import (
    PaletteEntry, palette_search, place_location_on_map,
)


class LocationPaletteWidget:
    WIDTH = 280
    ROW_H = 38

    def __init__(self, state, *, on_close=None):
        """``state`` is the MapEditorState. Reads ``state.world``,
        ``state.world_map`` to render."""
        self.state = state
        self.on_close = on_close
        self.is_open = False
        self.search = ""
        self.search_active = False
        self.scroll = 0
        self.content_h = 0
        self._row_rects = []   # [(rect, PaletteEntry), ...]
        self._hover_idx = -1

        # Lazy-built buttons
        self._btn_close = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.search_active = False
        self.scroll = 0

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _rect(self) -> pygame.Rect:
        # Anchor to the right side of the screen, just under the top bar.
        from states.map_editor import TOP_BAR_H, BOTTOM_BAR_H
        sw = self.state.screen_w
        sh = self.state.screen_h
        return pygame.Rect(
            sw - self.WIDTH, TOP_BAR_H,
            self.WIDTH, sh - TOP_BAR_H - BOTTOM_BAR_H,
        )

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, ev) -> bool:
        if not self.is_open:
            return False
        rect = self._rect()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if not rect.collidepoint(ev.pos):
                return False
            # Search field row
            field_rect = pygame.Rect(rect.x + 8, rect.y + 36,
                                       rect.width - 16, 30)
            if field_rect.collidepoint(ev.pos):
                self.search_active = True
                return True
            # Close button
            if (self._btn_close is not None
                    and self._btn_close.rect.collidepoint(ev.pos)):
                self.close()
                return True
            # Row click — drop the location at the canvas centre
            for r, entry in self._row_rects:
                if r.collidepoint(ev.pos):
                    self._drop_at_canvas_center(entry)
                    return True
            self.search_active = False
            return True

        if ev.type == pygame.MOUSEWHEEL and rect.collidepoint(
                pygame.mouse.get_pos()):
            max_scroll = max(0, self.content_h - rect.height + 80)
            self.scroll = max(0, min(self.scroll - ev.y * 30, max_scroll))
            return True

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.search_active:
                if ev.key == pygame.K_BACKSPACE:
                    self.search = self.search[:-1]
                    return True
                if ev.key == pygame.K_RETURN:
                    self.search_active = False
                    return True
                if ev.unicode and ev.unicode.isprintable():
                    self.search += ev.unicode
                    return True
        return False

    def _drop_at_canvas_center(self, entry: PaletteEntry):
        """Place the location at (50%, 50%) — caller can drag the
        token from there. Logs status via the editor's status bar."""
        if self.state.world is None or self.state.world_map is None:
            return
        place_location_on_map(self.state.world, self.state.world_map,
                                entry.location_id, 50.0, 50.0)
        self.state._set_status(
            f"Lisätty kartalle: {entry.name} (raahaa oikeaan paikkaan)"
        )

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        rect = self._rect()
        pygame.draw.rect(screen, COLORS.get("panel_dark",
                                              (32, 32, 40)), rect)
        pygame.draw.line(screen, COLORS.get("border", (80, 80, 100)),
                         (rect.x, rect.y), (rect.x, rect.bottom), 1)

        # Header
        title = fonts.body_bold.render("Sijainnit", True,
                                          COLORS.get("text_bright",
                                                       (240, 240, 240)))
        screen.blit(title, (rect.x + 12, rect.y + 8))

        # Close button (lazy)
        if self._btn_close is None:
            self._btn_close = Button(
                rect.right - 60, rect.y + 6, 50, 24, "Sulje",
                self.close, color=COLORS.get("panel", (60, 60, 80)),
            )
        else:
            self._btn_close.rect.x = rect.right - 60
            self._btn_close.rect.y = rect.y + 6
        self._btn_close.draw(screen, pygame.mouse.get_pos())

        # Search field
        field_rect = pygame.Rect(rect.x + 8, rect.y + 36,
                                   rect.width - 16, 30)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (20, 20, 26)),
                         field_rect, border_radius=4)
        pygame.draw.rect(screen,
                         COLORS.get("accent", (180, 180, 240))
                         if self.search_active
                         else COLORS.get("border", (80, 80, 100)),
                         field_rect, 1, border_radius=4)
        cursor = ("|" if self.search_active
                  and pygame.time.get_ticks() // 400 % 2 == 0 else "")
        text = self.search + cursor or ("Hae nimellä / tyypillä..."
                                          if not self.search_active
                                          else cursor)
        screen.blit(fonts.small.render(text, True,
                                          COLORS.get("text",
                                                       (220, 220, 220))),
                    (field_rect.x + 8, field_rect.y + 6))

        # Body — scrollable list
        body_top = rect.y + 76
        body_h = rect.bottom - body_top - 8
        body_rect = pygame.Rect(rect.x + 4, body_top,
                                  rect.width - 8, body_h)
        prev_clip = screen.get_clip()
        screen.set_clip(body_rect)

        rows = []
        if self.state.world is not None and self.state.world_map is not None:
            rows = palette_search(self.state.world, self.state.world_map,
                                    self.search)
        self._row_rects = []
        y = body_top - self.scroll
        mp = pygame.mouse.get_pos()
        for entry in rows:
            row_rect = pygame.Rect(rect.x + 8, y,
                                     rect.width - 16, self.ROW_H)
            self._row_rects.append((row_rect, entry))
            is_hover = row_rect.collidepoint(mp)
            bg_col = (COLORS.get("hover", (60, 60, 80))
                       if is_hover else COLORS.get("panel",
                                                     (40, 40, 50)))
            pygame.draw.rect(screen, bg_col, row_rect, border_radius=4)
            if entry.has_token:
                pygame.draw.rect(screen,
                                 COLORS.get("success", (90, 200, 120)),
                                 row_rect, 1, border_radius=4)
            screen.blit(
                fonts.small_bold.render(
                    entry.name, True,
                    COLORS.get("text_bright", (240, 240, 240)),
                ),
                (row_rect.x + 8, row_rect.y + 4),
            )
            kind = entry.location_type or "-"
            tag = f"{kind} · {'kartalla' if entry.has_token else 'ei kartalla'}"
            screen.blit(
                fonts.tiny.render(tag, True,
                                    COLORS.get("text_dim",
                                                 (160, 160, 160))),
                (row_rect.x + 8, row_rect.y + 20),
            )
            y += self.ROW_H + 4
        self.content_h = (y + self.scroll) - body_top
        screen.set_clip(prev_clip)

        # Footer count badge
        from data.location_palette import unplaced_count
        if self.state.world is not None and self.state.world_map is not None:
            n = unplaced_count(self.state.world, self.state.world_map)
            if n > 0:
                badge = fonts.tiny.render(f"Lisättävänä: {n}", True,
                                             COLORS.get("warning",
                                                          (220, 180, 80)))
                screen.blit(badge, (rect.x + 12, rect.bottom - 18))
