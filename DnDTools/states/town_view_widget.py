"""Town view widget — tabbed UI rendering ``TownSummary`` from
``data/town_economy.py``.

Tabs: Map / NPCs / Shops / Services / Quests. Each tab paints the
corresponding list against the current location. Click an entry →
fires ``on_pick(kind, id)`` so the campaign manager can open the
detail panel for that item.

Lifecycle is the same shape as
:class:`states.location_palette_widget.LocationPaletteWidget` so the
campaign manager can host both interchangeably.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.town_economy import town_summary, TownSummary


_TABS = ("map", "npcs", "shops", "services", "quests")
_TAB_LABEL = {
    "map":      "Kartta",
    "npcs":     "NPC:t",
    "shops":    "Kaupat",
    "services": "Palvelut",
    "quests":   "Tehtävät",
}


class TownViewWidget:
    WIDTH = 460
    ROW_H = 36

    def __init__(self, world, location_id: str,
                  on_pick: Optional[Callable[[str, str], None]] = None,
                  on_close: Optional[Callable[[], None]] = None):
        self.world = world
        self.location_id = location_id
        self.on_pick = on_pick or (lambda kind, _id: None)
        self.on_close = on_close
        self.is_open = False
        self.active_tab = "npcs"
        self.scroll = 0
        self.content_h = 0
        self._row_rects: List[Tuple[pygame.Rect, str, str]] = []
        self._btn_close: Optional[Button] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.scroll = 0

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def set_location(self, location_id: str):
        self.location_id = location_id
        self.scroll = 0

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _rect(self) -> pygame.Rect:
        from states.map_editor import TOP_BAR_H, BOTTOM_BAR_H
        sw = SCREEN_WIDTH
        sh = SCREEN_HEIGHT
        return pygame.Rect(
            sw - self.WIDTH, TOP_BAR_H,
            self.WIDTH, sh - TOP_BAR_H - BOTTOM_BAR_H,
        )

    def _summary(self) -> Optional[TownSummary]:
        return town_summary(self.world, self.location_id)

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        rect = self._rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not rect.collidepoint(event.pos):
                return False
            if (self._btn_close is not None
                    and self._btn_close.rect.collidepoint(event.pos)):
                self.close()
                return True
            # Tab strip
            tab_w = (rect.width - 12) // len(_TABS)
            for i, key in enumerate(_TABS):
                tab_rect = pygame.Rect(rect.x + 6 + i * tab_w,
                                          rect.y + 36, tab_w - 4, 28)
                if tab_rect.collidepoint(event.pos):
                    self.active_tab = key
                    self.scroll = 0
                    return True
            # Body row click
            for r, kind, oid in self._row_rects:
                if r.collidepoint(event.pos):
                    self.on_pick(kind, oid)
                    return True
            return True
        if event.type == pygame.MOUSEWHEEL and rect.collidepoint(
                pygame.mouse.get_pos()):
            max_scroll = max(0, self.content_h - rect.height + 100)
            self.scroll = max(0, min(self.scroll - event.y * 30,
                                          max_scroll))
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        rect = self._rect()
        pygame.draw.rect(screen, COLORS.get("panel_dark",
                                              (32, 32, 40)), rect)
        pygame.draw.line(screen, COLORS.get("border", (80, 80, 100)),
                         (rect.x, rect.y), (rect.x, rect.bottom), 1)

        summary = self._summary()
        title = (summary.location.name if summary else "(ei sijaintia)")
        screen.blit(fonts.body_bold.render(title, True,
                                              COLORS.get("text_bright",
                                                           (240, 240, 240))),
                    (rect.x + 12, rect.y + 8))

        if self._btn_close is None:
            self._btn_close = Button(
                rect.right - 60, rect.y + 6, 50, 24, "Sulje",
                self.close, color=COLORS.get("panel", (60, 60, 80)),
            )
        else:
            self._btn_close.rect.x = rect.right - 60
            self._btn_close.rect.y = rect.y + 6
        self._btn_close.draw(screen, mp)

        # Tab strip
        tab_w = (rect.width - 12) // len(_TABS)
        for i, key in enumerate(_TABS):
            tab_rect = pygame.Rect(rect.x + 6 + i * tab_w,
                                      rect.y + 36, tab_w - 4, 28)
            is_active = (key == self.active_tab)
            is_hover = tab_rect.collidepoint(mp)
            bg = (COLORS.get("accent", (180, 180, 240)) if is_active
                   else COLORS.get("hover", (60, 60, 80)) if is_hover
                   else COLORS.get("panel", (40, 40, 50)))
            pygame.draw.rect(screen, bg, tab_rect, border_radius=4)
            screen.blit(fonts.small.render(_TAB_LABEL[key], True,
                                              COLORS.get("text_bright",
                                                           (240, 240, 240))),
                        (tab_rect.x + 8, tab_rect.y + 6))

        # Body
        body_top = rect.y + 76
        body_h = rect.bottom - body_top - 8
        body_rect = pygame.Rect(rect.x + 4, body_top,
                                  rect.width - 8, body_h)
        prev_clip = screen.get_clip()
        screen.set_clip(body_rect)
        self._row_rects = []
        if summary is None:
            screen.blit(fonts.small.render(
                "Avoinna olevaa sijaintia ei ole valittu.", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (rect.x + 12, body_top + 8))
        else:
            self._draw_tab_body(screen, mp, body_top, summary)
        screen.set_clip(prev_clip)

    # ------------------------------------------------------------------ #
    def _draw_tab_body(self, screen, mp, body_top, summary: TownSummary):
        rect = self._rect()
        y = body_top - self.scroll
        if self.active_tab == "map":
            text = (f"Lapsisijaintien määrä: "
                    f"{len(summary.child_locations)}")
            screen.blit(fonts.small.render(text, True,
                                              COLORS.get("text_dim",
                                                           (160, 160, 160))),
                        (rect.x + 12, y + 4))
            y += 26
            for child in summary.child_locations:
                row = self._row(screen, rect, y, mp,
                                 title=child.name,
                                 sub=f"({child.location_type})")
                self._row_rects.append((row, "location", child.id))
                y += self.ROW_H + 4
        elif self.active_tab == "npcs":
            for npc in summary.npcs:
                sub_bits = [b for b in (npc.occupation, npc.faction) if b]
                row = self._row(screen, rect, y, mp,
                                 title=npc.name,
                                 sub=" · ".join(sub_bits))
                self._row_rects.append((row, "npc", npc.id))
                y += self.ROW_H + 4
        elif self.active_tab == "shops":
            for shop in summary.shops:
                sub = (f"{shop.shop_type} · {len(shop.inventory)} esinettä "
                        f"· {shop.gold:.0f} gp")
                row = self._row(screen, rect, y, mp,
                                 title=shop.name, sub=sub)
                self._row_rects.append((row, "shop", shop.id))
                y += self.ROW_H + 4
        elif self.active_tab == "services":
            for svc in summary.services:
                row = self._row(screen, rect, y, mp,
                                 title=svc.name,
                                 sub=f"{svc.service_type} · "
                                      f"{svc.price_gp:.0f} gp")
                self._row_rects.append((row, "service", svc.id))
                y += self.ROW_H + 4
        elif self.active_tab == "quests":
            screen.blit(fonts.small.render(
                f"Tehtäviä tähän paikkaan linkitetty: "
                f"{summary.quest_count}", True,
                COLORS.get("text_bright", (240, 240, 240))),
                (rect.x + 12, y))
            y += 26
        self.content_h = (y + self.scroll) - body_top

    def _row(self, screen, rect: pygame.Rect, y: int, mp,
              *, title: str, sub: str = "") -> pygame.Rect:
        row = pygame.Rect(rect.x + 8, y, rect.width - 16, self.ROW_H)
        is_hover = row.collidepoint(mp)
        bg = (COLORS.get("hover", (60, 60, 80)) if is_hover
               else COLORS.get("panel", (40, 40, 50)))
        pygame.draw.rect(screen, bg, row, border_radius=4)
        screen.blit(
            fonts.small_bold.render(
                title, True,
                COLORS.get("text_bright", (240, 240, 240))),
            (row.x + 8, row.y + 4),
        )
        if sub:
            screen.blit(
                fonts.tiny.render(sub, True,
                                    COLORS.get("text_dim",
                                                 (160, 160, 160))),
                (row.x + 8, row.y + 20),
            )
        return row
