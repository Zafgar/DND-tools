"""Relations matrix editor — pop-up modal for clicking attitudes between
kingdoms (or, in city mode, between cities of one kingdom) until they
read right.

UI: a square grid; row = "from", column = "to".  Diagonal cells show
"self".  Click any off-diagonal cell to cycle through the canonical
attitudes from :data:`data.kingdoms.RELATION_LEVELS`.  Edits are
symmetric: setting A→B also sets B→A.

The widget mutates :class:`KingdomEntry` / :class:`CityEntry` objects
in-place via :func:`data.kingdoms.set_kingdom_relation` /
:func:`data.kingdoms.set_city_relation`.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import kingdoms as kg


# Reuse the navigator's attitude colour palette so the chips read the same.
_REL_COLOR = {
    "ally":     (90, 200, 120),
    "trade":    (100, 180, 220),
    "neutral":  (140, 140, 150),
    "wary":     (210, 180, 90),
    "hostile":  (220, 100, 90),
    "at_war":   (240, 60, 60),
    "self":     (80, 80, 90),
}


class RelationsMatrixModal:
    """Phase 24b — edit kingdom↔kingdom or city↔city relations.

    ``scope`` is either ``"kingdom"`` (uses the full 5-kingdom matrix)
    or ``"city"`` (cities of ``parent_kingdom_key``).
    """
    MIN_CELL = 70
    HEADER_W = 140
    HEADER_H = 60
    PADDING = 20

    def __init__(self, campaign, *,
                  scope: str = "kingdom",
                  parent_kingdom_key: str = "",
                  on_close: Optional[Callable[[], None]] = None):
        if scope not in ("kingdom", "city"):
            raise ValueError("scope must be 'kingdom' or 'city'")
        self.campaign = campaign
        self.scope = scope
        self.parent_kingdom_key = parent_kingdom_key
        self.on_close = on_close
        self.is_open = False
        self._cells: List[Tuple[pygame.Rect, str, str]] = []
        self._status = ""
        self.btn_close = Button(0, 0, 90, 30, "Sulje",
                                  self.close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self._status = ""

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    def _entities(self) -> List:
        if self.scope == "kingdom":
            return list(kg.ensure_kingdoms_on_campaign(self.campaign))
        k = kg.find_kingdom(self.campaign, self.parent_kingdom_key)
        return list(k.cities) if k else []

    def _attitude(self, src_key: str, dst_key: str) -> str:
        if src_key == dst_key:
            return "self"
        if self.scope == "kingdom":
            return kg.get_kingdom_relation(self.campaign, src_key, dst_key)
        return kg.get_city_relation(self.campaign,
                                       self.parent_kingdom_key,
                                       src_key, dst_key)

    def _cycle(self, src_key: str, dst_key: str) -> None:
        if src_key == dst_key:
            return
        levels = list(kg.RELATION_LEVELS)
        cur = self._attitude(src_key, dst_key)
        if cur not in levels:
            cur = "neutral"
        nxt = levels[(levels.index(cur) + 1) % len(levels)]
        if self.scope == "kingdom":
            kg.set_kingdom_relation(self.campaign, src_key, dst_key, nxt)
        else:
            kg.set_city_relation(self.campaign,
                                   self.parent_kingdom_key,
                                   src_key, dst_key, nxt)
        self._status = f"{src_key} ↔ {dst_key}: {nxt}"

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.rect.collidepoint(event.pos):
                self.btn_close.handle_event(event)
                return True
            for rect, src, dst in self._cells:
                if rect.collidepoint(event.pos):
                    self._cycle(src, dst)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        entities = self._entities()
        n = len(entities)
        if n == 0:
            self._draw_empty(screen, mp)
            return

        # Size the modal to fit the grid
        cell = max(self.MIN_CELL, min(120, 700 // max(1, n)))
        w = self.HEADER_W + cell * n + self.PADDING * 2
        h = self.HEADER_H + cell * n + self.PADDING * 2 + 80
        x = (SCREEN_WIDTH - w) // 2
        y = (SCREEN_HEIGHT - h) // 2
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                         rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                         rect, 2, border_radius=10)
        title = ("Valtakuntien suhteet"
                  if self.scope == "kingdom"
                  else f"Kaupunkien suhteet ({self.parent_kingdom_key})")
        screen.blit(fonts.body_bold.render(
            title, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (x + self.PADDING, y + 14))

        grid_x = x + self.PADDING + self.HEADER_W
        grid_y = y + self.PADDING + self.HEADER_H

        # Column headers (destination)
        for j, dst in enumerate(entities):
            cx = grid_x + j * cell
            label = (dst.name[:9] if hasattr(dst, "name") else dst.key)
            screen.blit(fonts.small_bold.render(
                label, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (cx + 4, grid_y - 18))

        # Cells
        self._cells = []
        for i, src in enumerate(entities):
            cy = grid_y + i * cell
            # Row header
            screen.blit(fonts.small_bold.render(
                (src.name if hasattr(src, "name") else src.key),
                True,
                COLORS.get("text_bright", (240, 240, 250))),
                (x + self.PADDING, cy + cell // 2 - 7))
            for j, dst in enumerate(entities):
                cx = grid_x + j * cell
                cell_rect = pygame.Rect(cx, cy, cell - 4, cell - 4)
                att = self._attitude(src.key, dst.key)
                col = _REL_COLOR.get(att, (140, 140, 150))
                pygame.draw.rect(screen, col, cell_rect, border_radius=4)
                if cell_rect.collidepoint(mp):
                    pygame.draw.rect(screen,
                                      (255, 255, 255), cell_rect, 2,
                                      border_radius=4)
                txt = "—" if att == "self" else att
                screen.blit(fonts.tiny.render(
                    txt, True, (20, 20, 30)),
                    (cell_rect.x + 6, cell_rect.y + 6))
                if att != "self":
                    self._cells.append((cell_rect, src.key, dst.key))

        # Legend
        ly = grid_y + cell * n + 16
        screen.blit(fonts.tiny.render(
            "Klikkaa solua: ", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (x + self.PADDING, ly))
        lx = x + self.PADDING + 90
        for level in kg.RELATION_LEVELS:
            cw = fonts.tiny.size(level)[0] + 12
            chip = pygame.Rect(lx, ly - 2, cw, 18)
            pygame.draw.rect(screen, _REL_COLOR.get(level,
                                                       (140, 140, 150)),
                              chip, border_radius=9)
            screen.blit(fonts.tiny.render(level, True, (20, 20, 30)),
                          (chip.x + 6, chip.y + 2))
            lx += cw + 4

        if self._status:
            screen.blit(fonts.small.render(
                self._status, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (x + self.PADDING, rect.bottom - 70))

        self.btn_close.rect.x = rect.right - 110
        self.btn_close.rect.y = rect.bottom - 40
        self.btn_close.draw(screen, mp)

    def _draw_empty(self, screen, mp):
        w, h = 360, 160
        x = (SCREEN_WIDTH - w) // 2
        y = (SCREEN_HEIGHT - h) // 2
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                         rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                         rect, 2, border_radius=10)
        screen.blit(fonts.body.render(
            "Ei kohteita tällä laajuudella.", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (x + 20, y + 20))
        self.btn_close.rect.x = rect.right - 110
        self.btn_close.rect.y = rect.bottom - 40
        self.btn_close.draw(screen, mp)
