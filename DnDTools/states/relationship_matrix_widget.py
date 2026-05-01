"""Relationship matrix widget — for one NPC, one row per PC in the
campaign party showing the current attitude (with colour-coded
attitude pill) and a +/- pair of buttons to nudge the score, plus
a notes field.

Reads/writes the NPC's ``relationships`` list via Phase 14c
helpers (``set_attitude``, ``adjust_attitude``,
``get_relationship``).
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.town_economy import (
    ATTITUDES, attitude_score, attitude_from_score,
    get_relationship, set_attitude, adjust_attitude,
)


_ATTITUDE_COLOR = {
    "hostile":    (220, 80, 80),
    "unfriendly": (220, 140, 80),
    "neutral":    (180, 180, 180),
    "friendly":   (140, 200, 100),
    "allied":     (90, 200, 200),
}


class RelationshipMatrixWidget:
    WIDTH = 480
    ROW_H = 56

    def __init__(self, npc, campaign,
                  on_close: Optional[Callable[[], None]] = None):
        self.npc = npc
        self.campaign = campaign
        self.on_close = on_close
        self.is_open = False
        self.scroll = 0
        self.content_h = 0
        # Map of hero_name → (plus_btn, minus_btn). Lazy-built each draw.
        self._row_buttons = {}

        self.btn_close = Button(0, 0, 50, 24, "Sulje",
                                  self.close,
                                  color=COLORS.get("panel", (60, 60, 80)))

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

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _hero_names(self) -> List[str]:
        out = []
        for member in (getattr(self.campaign, "party", []) or []):
            hero = getattr(member, "hero_data", {}) or {}
            name = hero.get("name", "")
            if name:
                out.append(name)
        return out

    def _bump(self, hero_name: str, delta: int):
        adjust_attitude(self.npc, hero_name, delta)

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
            if self.btn_close.rect.collidepoint(event.pos):
                self.close()
                return True
            for hero_name, (plus, minus) in self._row_buttons.items():
                if plus.rect.collidepoint(event.pos):
                    self._bump(hero_name, +1)
                    return True
                if minus.rect.collidepoint(event.pos):
                    self._bump(hero_name, -1)
                    return True
            return True
        if event.type == pygame.MOUSEWHEEL and rect.collidepoint(
                pygame.mouse.get_pos()):
            max_s = max(0, self.content_h - rect.height + 80)
            self.scroll = max(0, min(self.scroll - event.y * 30, max_s))
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

        title = f"{self.npc.name} · suhteet"
        screen.blit(fonts.body_bold.render(title, True,
                                              COLORS.get("text_bright",
                                                           (240, 240, 240))),
                    (rect.x + 12, rect.y + 8))

        self.btn_close.rect.x = rect.right - 60
        self.btn_close.rect.y = rect.y + 6
        self.btn_close.draw(screen, mp)

        body_top = rect.y + 50
        body_h = rect.bottom - body_top - 8
        body_rect = pygame.Rect(rect.x + 4, body_top,
                                  rect.width - 8, body_h)
        prev_clip = screen.get_clip()
        screen.set_clip(body_rect)
        self._row_buttons = {}
        y = body_top - self.scroll
        names = self._hero_names()
        if not names:
            screen.blit(fonts.small.render(
                "Kampanjan partyssa ei ole hahmoja.", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (rect.x + 12, body_top + 8))
        for hero_name in names:
            row = pygame.Rect(rect.x + 8, y,
                                rect.width - 16, self.ROW_H)
            pygame.draw.rect(screen,
                              COLORS.get("panel", (40, 40, 50)),
                              row, border_radius=4)
            screen.blit(
                fonts.small_bold.render(
                    hero_name, True,
                    COLORS.get("text_bright", (240, 240, 240))),
                (row.x + 8, row.y + 4),
            )
            rel = get_relationship(self.npc, hero_name)
            attitude = rel.attitude if rel else "neutral"
            pill = pygame.Rect(row.x + 8, row.y + 26, 110, 18)
            pygame.draw.rect(screen,
                              _ATTITUDE_COLOR.get(attitude,
                                                    (180, 180, 180)),
                              pill, border_radius=8)
            screen.blit(
                fonts.tiny.render(attitude.upper(), True,
                                    (20, 20, 20)),
                (pill.x + 8, pill.y + 2),
            )
            # +/- buttons
            minus_btn = Button(
                row.right - 110, row.y + 8, 36, 32, "-",
                lambda h=hero_name: self._bump(h, -1),
                color=COLORS.get("danger", (220, 80, 80)),
            )
            plus_btn = Button(
                row.right - 60, row.y + 8, 36, 32, "+",
                lambda h=hero_name: self._bump(h, +1),
                color=COLORS.get("success", (90, 200, 120)),
            )
            minus_btn.draw(screen, mp)
            plus_btn.draw(screen, mp)
            self._row_buttons[hero_name] = (plus_btn, minus_btn)
            # Notes preview
            if rel and rel.notes:
                note_str = rel.notes[:60]
                screen.blit(
                    fonts.tiny.render(
                        note_str, True,
                        COLORS.get("text_dim", (160, 160, 160))),
                    (pill.right + 12, pill.y + 1),
                )
            y += self.ROW_H + 4
        self.content_h = (y + self.scroll) - body_top
        screen.set_clip(prev_clip)
