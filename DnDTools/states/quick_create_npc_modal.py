"""Quick-create NPC modal — single text field for the NPC's name,
optional location auto-filled from the campaign manager's current
selection, plus a "Choose portrait..." button. Calls
:func:`data.npc_quick_create.quick_create_npc` on confirm.
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.npc_quick_create import quick_create_npc


class QuickCreateNPCModal:
    WIDTH = 480
    HEIGHT = 290

    # Phase 24d — wealth-tier cycler.
    _WEALTH_TIERS = ("", "squalid", "poor", "modest", "comfortable",
                       "wealthy", "aristocratic")
    _WEALTH_LABELS = {
        "":             "(ei kolikoita)",
        "squalid":      "Kerjäläinen (~0.5 gp)",
        "poor":         "Köyhä (~5 gp)",
        "modest":       "Vaatimaton (~25 gp)",
        "comfortable":  "Mukava (~100 gp)",
        "wealthy":      "Varakas (~500 gp)",
        "aristocratic": "Aatelinen (~2500 gp)",
    }

    def __init__(self, world, *,
                  default_location_id: str = "",
                  on_close: Optional[Callable[[], None]] = None,
                  on_created: Optional[Callable[[str], None]] = None):
        self.world = world
        self.default_location_id = default_location_id
        self.on_close = on_close
        self.on_created = on_created
        self.is_open = False
        self.name = ""
        self.field_active = True
        self.portrait_src = ""
        self.wealth_tier = ""
        self._status = ""
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.btn_pick_portrait = Button(
            self.x + 20, self.y + 130, 200, 30,
            "Valitse portretti...", self._pick_portrait,
            color=COLORS.get("warning", (220, 180, 80)),
        )
        self.btn_wealth = Button(
            self.x + 20, self.y + 175, 280, 30,
            self._wealth_label(), self._cycle_wealth_tier,
            color=COLORS.get("legendary", (170, 110, 220)),
        )
        self.btn_create = Button(
            self.x + 20, self.y + self.HEIGHT - 50,
            150, 36, "Luo NPC", self._create,
            color=COLORS.get("success", (90, 200, 120)),
        )
        self.btn_close = Button(
            self.x + self.WIDTH - 110, self.y + self.HEIGHT - 50,
            90, 36, "Sulje", self.close,
            color=COLORS.get("panel", (60, 60, 80)),
        )

    def _wealth_label(self) -> str:
        return f"Varallisuus: {self._WEALTH_LABELS[self.wealth_tier]}"

    def _cycle_wealth_tier(self):
        idx = self._WEALTH_TIERS.index(self.wealth_tier)
        self.wealth_tier = self._WEALTH_TIERS[
            (idx + 1) % len(self._WEALTH_TIERS)]
        self.btn_wealth.text = self._wealth_label()

    def open(self):
        self.is_open = True
        self.name = ""
        self.portrait_src = ""
        self.wealth_tier = ""
        self.btn_wealth.text = self._wealth_label()
        self._status = ""
        self.field_active = True

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _pick_portrait(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Valitse NPC-portretti",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.webp"),
                    ("All files", "*.*"),
                ],
            )
            root.destroy()
        except Exception as ex:
            self._status = f"Picker unavailable: {ex}"
            return
        if path:
            self.portrait_src = path
            self._status = f"Portretti: {os.path.basename(path)}"

    def _create(self):
        nm = self.name.strip()
        if not nm:
            self._status = "Anna nimi."
            return
        rep = quick_create_npc(
            self.world, name=nm,
            location_id=self.default_location_id or "",
            portrait_src_path=self.portrait_src or None,
            wealth_tier=self.wealth_tier or "",
        )
        if not rep.npc_id:
            self._status = "Luonti epäonnistui."
            return
        self._status = f"Luotu: {nm}"
        if self.on_created:
            self.on_created(rep.npc_id)
        self.close()

    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                    return True
                if event.key == pygame.K_RETURN:
                    self._create()
                    return True
                if event.unicode and event.unicode.isprintable():
                    if len(self.name) < 60:
                        self.name += event.unicode
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            field = pygame.Rect(self.x + 20, self.y + 70,
                                  self.WIDTH - 40, 32)
            self.field_active = field.collidepoint(event.pos)
            for btn in (self.btn_pick_portrait, self.btn_wealth,
                          self.btn_create, self.btn_close):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            return True
        return False

    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
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

        screen.blit(fonts.header.render("Pika-luo NPC", True,
                                            COLORS.get("accent",
                                                         (180, 180, 240))),
                    (self.x + 20, self.y + 14))
        screen.blit(fonts.small.render("Nimi:", True,
                                          COLORS.get("text",
                                                       (220, 220, 220))),
                    (self.x + 20, self.y + 50))
        field = pygame.Rect(self.x + 20, self.y + 70,
                              self.WIDTH - 40, 32)
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                         field, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.field_active
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, field, 1, border_radius=4)
        cursor = ("|" if self.field_active and
                          pygame.time.get_ticks() // 400 % 2 == 0
                  else "")
        screen.blit(fonts.body.render(self.name + cursor, True,
                                          COLORS.get("text_bright",
                                                       (240, 240, 240))),
                    (field.x + 8, field.y + 6))

        self.btn_pick_portrait.draw(screen, mp)
        self.btn_wealth.draw(screen, mp)

        if self._status:
            col = (COLORS.get("warning", (220, 180, 80))
                    if "epäonnistui" in self._status
                    or "Anna" in self._status
                    else COLORS.get("success", (90, 200, 120)))
            screen.blit(fonts.small.render(self._status, True, col),
                        (self.x + 20, self.y + 215))

        self.btn_create.draw(screen, mp)
        self.btn_close.draw(screen, mp)


# Late import to keep module-level free of tkinter cost
import os
