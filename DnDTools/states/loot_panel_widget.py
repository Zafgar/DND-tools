"""Battle-end loot panel — auto-detects defeated enemies and lets
the DM credit gold + items to the campaign in a few clicks.

Open at the end of an encounter (e.g. from the battle report screen
or directly when the encounter resolves). The panel reads the
battle's entities, builds a :class:`LootBundle`, and offers three
distribution buttons (Yhteinen kassa / Jaa tasan / Yhdelle PC:lle).
Items always go to the shared inventory.
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.loot import (
    LootBundle, AwardReport,
    award_bundle, loot_from_defeated_entities,
)


class LootPanelWidget:
    WIDTH = 560
    HEIGHT = 420

    def __init__(self, campaign, *, entities=None, on_close=None):
        """``entities`` is a list of post-combat Entity objects so we
        can auto-build the loot bundle. Caller can also construct a
        bundle manually and assign it via ``self.bundle = ...`` after
        instantiation."""
        self.campaign = campaign
        self.on_close = on_close
        self.is_open = False
        self.entities = entities or []
        self.bundle: LootBundle = loot_from_defeated_entities(
            self.entities)
        self.bonus_gold_input = ""
        self.bonus_field_active = False
        self._status = ""
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.btn_close = Button(
            self.x + self.WIDTH - 110, self.y + self.HEIGHT - 50,
            90, 36, "Sulje", self.close,
            color=COLORS.get("panel", (60, 60, 80)),
        )
        self.btn_shared = Button(
            self.x + 20, self.y + self.HEIGHT - 50,
            150, 36, "Yhteiseen kassaan",
            lambda: self._award("shared"),
            color=COLORS.get("success", (90, 200, 120)),
        )
        self.btn_split = Button(
            self.x + 180, self.y + self.HEIGHT - 50,
            120, 36, "Jaa tasan",
            lambda: self._award("split"),
            color=COLORS.get("accent", (180, 180, 240)),
        )
        self.btn_first = Button(
            self.x + 310, self.y + self.HEIGHT - 50,
            150, 36, "Yhdelle PC:lle",
            lambda: self._award("first"),
            color=COLORS.get("legendary", (220, 200, 80)),
        )

    def open(self):
        self.is_open = True
        self._status = ""

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _bonus_gold(self) -> float:
        try:
            return float(self.bonus_gold_input or 0)
        except ValueError:
            return 0.0

    def _award(self, distribution: str):
        bundle = LootBundle(
            gold=self.bundle.gold + self._bonus_gold(),
            items=list(self.bundle.items),
            source_names=list(self.bundle.source_names),
        )
        if bundle.is_empty():
            self._status = "Ei jaettavaa loottia."
            return
        rep = award_bundle(self.campaign, bundle,
                              distribution=distribution)
        self._status = "Jaettu: " + rep.summary()
        # Clear the bundle so a second click doesn't double-credit
        self.bundle = LootBundle()
        self.bonus_gold_input = ""

    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.bonus_field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.bonus_gold_input = self.bonus_gold_input[:-1]
                    return True
                if event.key == pygame.K_RETURN:
                    self.bonus_field_active = False
                    return True
                ch = event.unicode
                if ch and (ch.isdigit() or ch == "."):
                    if len(self.bonus_gold_input) < 8:
                        self.bonus_gold_input += ch
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            field_rect = self._bonus_field_rect()
            if field_rect.collidepoint(event.pos):
                self.bonus_field_active = True
                return True
            self.bonus_field_active = False
            for btn in (self.btn_close, self.btn_shared,
                          self.btn_split, self.btn_first):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
        return False

    def _bonus_field_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + 220, self.y + 240, 120, 28)

    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                         rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                         rect, 2, border_radius=10)

        screen.blit(fonts.header.render("Lootti", True,
                                            COLORS.get("accent",
                                                         (180, 180, 240))),
                    (self.x + 20, self.y + 14))

        # Source list
        y = self.y + 60
        if self.bundle.source_names:
            sources = "Lähde: " + ", ".join(self.bundle.source_names)
            screen.blit(fonts.small.render(sources, True,
                                              COLORS.get("text_dim",
                                                           (160, 160, 160))),
                        (self.x + 20, y))
            y += 22
        else:
            screen.blit(fonts.small.render(
                "Ei automaattisesti tunnistettua loottia. "
                "Lisää bonus käsin alla.",
                True,
                COLORS.get("text_dim", (160, 160, 160))),
                (self.x + 20, y))
            y += 22

        # Gold + items summary
        gold_total = self.bundle.gold + self._bonus_gold()
        screen.blit(fonts.body_bold.render(
            f"Kulta: {gold_total:.0f} gp", True,
            COLORS.get("legendary", (220, 200, 80))),
            (self.x + 20, y))
        y += 28
        screen.blit(fonts.small.render(
            f"Esineitä: {len(self.bundle.items)}", True,
            COLORS.get("text_bright", (240, 240, 240))),
            (self.x + 20, y))
        y += 22
        for item in self.bundle.items[:6]:
            screen.blit(fonts.tiny.render(
                f"  · {item}", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (self.x + 20, y))
            y += 14
        if len(self.bundle.items) > 6:
            screen.blit(fonts.tiny.render(
                f"  · +{len(self.bundle.items) - 6} lisää", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (self.x + 20, y))
            y += 14
        y += 10

        # Bonus gold field
        screen.blit(fonts.small.render("Bonus-kulta (gp):", True,
                                          COLORS.get("text",
                                                       (220, 220, 220))),
                    (self.x + 20, self.y + 246))
        field_rect = self._bonus_field_rect()
        pygame.draw.rect(screen, COLORS.get("bg_dark", (20, 20, 26)),
                         field_rect, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.bonus_field_active
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, field_rect, 1, border_radius=4)
        cursor = ("|" if self.bonus_field_active
                          and pygame.time.get_ticks() // 400 % 2 == 0
                  else "")
        screen.blit(fonts.small.render(
            self.bonus_gold_input + cursor, True,
            COLORS.get("text_bright", (240, 240, 240))),
            (field_rect.x + 8, field_rect.y + 4))

        # Status
        if self._status:
            col = (COLORS.get("warning", (220, 180, 80))
                    if self._status.startswith("Ei ")
                    else COLORS.get("success", (90, 200, 120)))
            screen.blit(fonts.small.render(self._status, True, col),
                        (self.x + 20, self.y + 290))

        self.btn_shared.draw(screen, mp)
        self.btn_split.draw(screen, mp)
        self.btn_first.draw(screen, mp)
        self.btn_close.draw(screen, mp)
