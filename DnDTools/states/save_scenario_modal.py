"""Save-as-Scenario modal — captures the current battle (terrain,
monsters, ceiling, background, party spawn spots) as a reusable
Scenario and writes it under ``saves/user_scenarios/`` so it shows up
in the scenario picker next to the built-in catalog.
"""
import logging

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect
from data import scenarios


class SaveScenarioModal:
    WIDTH = 560
    HEIGHT = 360

    def __init__(self, battle, log_callback=None,
                  on_saved=None):
        self.battle = battle
        self.log = log_callback or (lambda *a: None)
        self.on_saved = on_saved
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.name_text = ""
        self.name_active = True
        self.selected_category = scenarios.CATEGORIES[0]
        self.status = ""

        self.cat_btns = []
        for i, cat in enumerate(scenarios.CATEGORIES):
            col = i % 4
            row = i // 4
            bx = self.x + 20 + col * 130
            by = self.y + 150 + row * 40
            self.cat_btns.append(Button(
                bx, by, 120, 32, cat.replace("_", " ").title(),
                lambda c=cat: self._select_category(c),
                color=COLORS["panel"],
            ))

        self.btn_save = Button(
            self.x + self.WIDTH - 230, self.y + self.HEIGHT - 55,
            110, 40, "Save", self._save, color=COLORS["success"],
        )
        self.btn_close = Button(
            self.x + self.WIDTH - 115, self.y + self.HEIGHT - 55,
            95, 40, "Cancel", self.close, color=COLORS["panel"],
        )
        self._refresh_tabs()

    def open(self):
        self.is_open = True
        self.status = ""
        self.name_active = True

    def close(self):
        self.is_open = False

    def _select_category(self, cat):
        self.selected_category = cat
        self._refresh_tabs()

    def _refresh_tabs(self):
        for btn, cat in zip(self.cat_btns, scenarios.CATEGORIES):
            btn.color = COLORS["accent"] if cat == self.selected_category \
                         else COLORS["panel"]

    def _save(self):
        name = self.name_text.strip()
        if not name:
            self.status = "Name required."
            return
        scen = scenarios.scenario_from_battle(
            self.battle, name=name,
            category=self.selected_category,
            description=f"Captured battle: {name}",
        )
        try:
            path = scenarios.save_user_scenario(scen)
        except OSError as ex:
            self.status = f"Save failed: {ex}"
            logging.warning(f"[SCENARIO] save failed: {ex}")
            return
        self.status = f"Saved → {path}"
        self.log(f"[SCENARIO] Captured '{name}' to {path}")
        if self.on_saved:
            self.on_saved(scen)

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.name_active:
                if event.key == pygame.K_BACKSPACE:
                    self.name_text = self.name_text[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    self._save()
                elif event.unicode and event.unicode.isprintable():
                    if len(self.name_text) < 50:
                        self.name_text += event.unicode
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click on name field focuses it
            field_rect = pygame.Rect(self.x + 20, self.y + 70,
                                      self.WIDTH - 40, 34)
            self.name_active = field_rect.collidepoint(event.pos)
        for b in self.cat_btns:
            b.handle_event(event)
        self.btn_save.handle_event(event)
        self.btn_close.handle_event(event)
        return True

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        draw_gradient_rect(screen, rect, COLORS["bg_dark"], COLORS["bg"],
                           border_radius=10)
        pygame.draw.rect(screen, COLORS["border_light"], rect, 2, border_radius=10)

        t = fonts.header.render("Save as Scenario", True, COLORS["accent"])
        screen.blit(t, (self.x + 20, self.y + 15))

        # Name field
        lbl = fonts.body_bold.render("Scenario name", True, COLORS["text"])
        screen.blit(lbl, (self.x + 20, self.y + 50))
        field_rect = pygame.Rect(self.x + 20, self.y + 70,
                                  self.WIDTH - 40, 34)
        pygame.draw.rect(screen, COLORS["bg_dark"], field_rect, border_radius=4)
        pygame.draw.rect(screen,
                         COLORS["accent"] if self.name_active else COLORS["border"],
                         field_rect, 1, border_radius=4)
        txt = self.name_text + ("|" if (self.name_active
                                          and pygame.time.get_ticks() // 400 % 2 == 0)
                                 else "")
        screen.blit(fonts.body.render(txt, True, COLORS["text"]),
                    (self.x + 28, self.y + 76))

        # Category picker
        cat_lbl = fonts.body_bold.render("Category", True, COLORS["text"])
        screen.blit(cat_lbl, (self.x + 20, self.y + 125))
        for b in self.cat_btns:
            b.draw(screen, mp)

        # Preview summary (entity / terrain / ceiling counts)
        ent_count = sum(1 for e in self.battle.entities
                        if not e.is_lair and not e.is_summon)
        summary = (f"Terrain: {len(self.battle.terrain)} tiles · "
                   f"Entities: {ent_count} · "
                   f"Ceiling: {self.battle.ceiling_ft or 'open sky'} · "
                   f"Weather: {self.battle.weather}")
        summ_surf = fonts.tiny.render(summary, True, COLORS["text_dim"])
        screen.blit(summ_surf, (self.x + 20, self.y + self.HEIGHT - 90))

        if self.status:
            col = COLORS["success"] if self.status.startswith("Saved") \
                   else COLORS["warning"]
            s = fonts.small.render(self.status, True, col)
            screen.blit(s, (self.x + 20, self.y + self.HEIGHT - 70))

        self.btn_save.draw(screen, mp)
        self.btn_close.draw(screen, mp)
