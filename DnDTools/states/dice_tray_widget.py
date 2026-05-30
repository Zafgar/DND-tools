"""Phase 45 — always-available dice tray widget.

A compact, collapsible panel the DM can pop from any view (campaign
manager, map, battle) to roll dice without leaving the current
screen.  Quick-buttons for the standard polyhedrals + advantage /
disadvantage, a free-text expression field ("3d6+2", "8d6"), a
re-roll button, and a scrolling history with full breakdowns.

Backed by the pure-logic :class:`data.dice_tray.DiceTray`.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.dice_tray import DiceTray


class DiceTrayWidget:
    WIDTH = 280
    HEADER_H = 34
    HISTORY_ROW_H = 30

    def __init__(self):
        self.tray = DiceTray()
        self.is_open = False
        self.expr = ""
        self.field_active = False
        self.label = ""           # optional roll label
        self._preset_rects: List[Tuple[pygame.Rect, str]] = []
        # Anchored bottom-right by default.
        self.x = SCREEN_WIDTH - self.WIDTH - 12
        self.y = 60

        self.btn_close = Button(0, 0, 24, 24, "×",
                                  self.close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))
        self.btn_roll = Button(0, 0, 70, 26, "Heitä",
                                 self._roll_expr,
                                 color=COLORS.get("success",
                                                    (90, 200, 120)))
        self.btn_reroll = Button(0, 0, 70, 26, "Uudemmin",
                                    self._reroll,
                                    color=COLORS.get("accent",
                                                       (110, 130, 220)))
        self.btn_clear = Button(0, 0, 60, 26, "Tyhjää",
                                   self._clear,
                                   color=COLORS.get("panel_dark",
                                                      (40, 40, 56)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def toggle(self):
        self.is_open = not self.is_open

    # ------------------------------------------------------------------ #
    def _roll_expr(self):
        if self.expr.strip():
            self.tray.roll(self.expr, label=self.label)

    def _reroll(self):
        self.tray.reroll_last()

    def _clear(self):
        self.tray.clear()

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.expr = self.expr[:-1]
                    return True
                if event.key == pygame.K_RETURN:
                    self._roll_expr()
                    return True
                if event.unicode and event.unicode.isprintable():
                    if len(self.expr) < 24:
                        self.expr += event.unicode
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rect = self._rect()
            if not rect.collidepoint(event.pos):
                return False  # let clicks outside fall through
            for btn in (self.btn_close, self.btn_roll,
                          self.btn_reroll, self.btn_clear):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            # Expression field?
            field = self._field_rect()
            self.field_active = field.collidepoint(event.pos)
            # Preset buttons?
            for r, value in self._preset_rects:
                if r.collidepoint(event.pos):
                    self.tray.roll_preset(value)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def _rect(self) -> pygame.Rect:
        # Height grows with history (capped).
        hist_rows = min(len(self.tray.history), 8)
        h = self.HEADER_H + 30 + 80 + hist_rows * self.HISTORY_ROW_H + 16
        return pygame.Rect(self.x, self.y, self.WIDTH, h)

    def _field_rect(self) -> pygame.Rect:
        r = self._rect()
        return pygame.Rect(r.x + 10, r.y + self.HEADER_H + 4,
                            r.width - 95, 26)

    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        rect = self._rect()
        pygame.draw.rect(screen, COLORS.get("bg_dark", (22, 22, 30)),
                          rect, border_radius=8)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                          rect, 2, border_radius=8)
        # Header
        screen.blit(fonts.small_bold.render(
            "Noppalaatikko", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (rect.x + 10, rect.y + 8))
        self.btn_close.rect.x = rect.right - 30
        self.btn_close.rect.y = rect.y + 6
        self.btn_close.draw(screen, mp)

        # Expression field + Roll
        field = self._field_rect()
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                          field, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.field_active
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, field, 1, border_radius=4)
        cursor = ("|" if self.field_active
                            and pygame.time.get_ticks() // 400 % 2 == 0
                    else "")
        disp = (self.expr + cursor) if (self.expr or self.field_active) \
            else "esim. 3d6+2"
        screen.blit(fonts.small.render(
            disp, True,
            COLORS.get("text_bright", (240, 240, 250))
            if self.expr else COLORS.get("text_dim", (140, 140, 150))),
            (field.x + 6, field.y + 4))
        self.btn_roll.rect.x = field.right + 6
        self.btn_roll.rect.y = field.y
        self.btn_roll.draw(screen, mp)

        # Preset buttons grid
        self._preset_rects = []
        px = rect.x + 10
        py = field.bottom + 8
        for name, value in DiceTray.QUICK_PRESETS:
            w = 48
            pr = pygame.Rect(px, py, w, 24)
            is_hov = pr.collidepoint(mp)
            col = (COLORS.get("legendary", (170, 110, 220))
                    if value.endswith("advantage")
                    else COLORS.get("danger", (200, 90, 90))
                    if value.endswith("disadvantage")
                    else COLORS.get("hover", (60, 60, 80))
                    if is_hov else COLORS.get("panel_dark",
                                                (40, 40, 56)))
            pygame.draw.rect(screen, col, pr, border_radius=4)
            screen.blit(fonts.tiny.render(
                name, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (pr.x + 6, pr.y + 5))
            self._preset_rects.append((pr, value))
            px += w + 4
            if px + w > rect.right - 8:
                px = rect.x + 10
                py += 28

        # Re-roll + clear
        py += 32
        self.btn_reroll.rect.x = rect.x + 10
        self.btn_reroll.rect.y = py
        self.btn_reroll.draw(screen, mp)
        self.btn_clear.rect.x = rect.x + 86
        self.btn_clear.rect.y = py
        self.btn_clear.draw(screen, mp)

        # History
        hy = py + 34
        if self.tray.history:
            latest = self.tray.history[0]
            # Big total for the most recent roll
            screen.blit(fonts.header.render(
                str(latest.total), True,
                COLORS.get("success", (120, 220, 140))),
                (rect.x + 10, hy - 4))
            screen.blit(fonts.tiny.render(
                latest.breakdown()[:40], True,
                COLORS.get("text_dim", (180, 180, 195))),
                (rect.x + 70, hy + 2))
            hy += 30
            for roll in self.tray.history[1:8]:
                lbl = f"{roll.label}: " if roll.label else ""
                screen.blit(fonts.tiny.render(
                    f"{lbl}{roll.breakdown()}"[:46], True,
                    COLORS.get("text_main", (210, 210, 225))),
                    (rect.x + 10, hy))
                hy += self.HISTORY_ROW_H - 12
