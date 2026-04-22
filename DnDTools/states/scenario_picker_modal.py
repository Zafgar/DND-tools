"""Scenario picker modal — lets the DM browse the scenario catalog by
category and load a chosen scenario into the encounter setup.

The modal is a self-contained mini-state: call ``open_scenario_picker``
from encounter_setup when the "Scenarios" button is clicked; the modal
handles its own events/draw while it's ``is_open``.
"""
import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect
from data import scenarios


CATEGORY_LABELS = {
    "bandit_lair": "Bandit Lair",
    "dungeon":     "Dungeon",
    "cave":        "Cave",
    "underwater":  "Underwater",
    "outdoor":     "Outdoor",
    "urban":       "Urban",
    "planar":      "Planar",
}


class ScenarioPickerModal:
    WIDTH = 900
    HEIGHT = 600

    def __init__(self, on_load):
        """``on_load(scenario)`` is called when the DM confirms a pick."""
        self.is_open = False
        self.on_load = on_load
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.selected_category = scenarios.CATEGORIES[0]
        self.selected_scenario = None
        self.scroll = 0

        # Category tabs on the left
        self.cat_btns = []
        for i, cat in enumerate(scenarios.CATEGORIES):
            self.cat_btns.append(Button(
                self.x + 15, self.y + 60 + i * 45,
                170, 38, CATEGORY_LABELS[cat],
                lambda c=cat: self._select_category(c),
                color=COLORS["panel"],
            ))

        # Action buttons
        self.btn_load = Button(
            self.x + self.WIDTH - 240, self.y + self.HEIGHT - 55,
            110, 40, "Load",
            self._confirm_load, color=COLORS["success"],
        )
        self.btn_close = Button(
            self.x + self.WIDTH - 125, self.y + self.HEIGHT - 55,
            110, 40, "Cancel",
            self.close, color=COLORS["panel"],
        )
        self._refresh_tabs()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.selected_scenario = None
        self.scroll = 0

    def close(self):
        self.is_open = False

    # ------------------------------------------------------------------ #
    # Selection helpers
    # ------------------------------------------------------------------ #
    def _select_category(self, cat):
        self.selected_category = cat
        self.selected_scenario = None
        self.scroll = 0
        self._refresh_tabs()

    def _refresh_tabs(self):
        for btn, cat in zip(self.cat_btns, scenarios.CATEGORIES):
            if cat == self.selected_category:
                btn.color = COLORS["accent"]
            else:
                btn.color = COLORS["panel"]

    def _visible_scenarios(self):
        return scenarios.list_by_category(self.selected_category)

    def _confirm_load(self):
        if self.selected_scenario is None:
            return
        self.on_load(self.selected_scenario)
        self.close()

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event):
        if not self.is_open:
            return False
        # Modal eats all events while open
        for b in self.cat_btns:
            b.handle_event(event)
        self.btn_load.handle_event(event)
        self.btn_close.handle_event(event)

        # Scenario list click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            list_x = self.x + 210
            list_y = self.y + 60
            list_w = 340
            row_h = 60
            if list_x <= mx <= list_x + list_w:
                for idx, s in enumerate(self._visible_scenarios()):
                    ry = list_y + idx * row_h + self.scroll
                    if ry <= my <= ry + row_h - 4 and list_y <= my <= list_y + self.HEIGHT - 120:
                        self.selected_scenario = s
                        break

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self.x + 210 <= mx <= self.x + 550:
                self.scroll = min(0, self.scroll + event.y * 25)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        return True

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()

        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        draw_gradient_rect(screen, rect,
                           COLORS["bg_dark"], COLORS["bg"], border_radius=10)
        pygame.draw.rect(screen, COLORS["border_light"], rect, 2, border_radius=10)

        # Title
        title = fonts.header.render("Valmiit skenaariot", True, COLORS["accent"])
        screen.blit(title, (self.x + 20, self.y + 15))

        # Category tabs
        for b in self.cat_btns:
            b.draw(screen, mp)

        # Scenario list
        self._draw_scenario_list(screen, mp)

        # Preview panel
        self._draw_preview(screen)

        # Buttons
        self.btn_load.enabled = self.selected_scenario is not None
        self.btn_load.draw(screen, mp)
        self.btn_close.draw(screen, mp)

    def _draw_scenario_list(self, screen, mp):
        list_x = self.x + 210
        list_y = self.y + 60
        list_w = 340
        list_h = self.HEIGHT - 130
        row_h = 60

        # List background + clip
        bg = pygame.Rect(list_x, list_y, list_w, list_h)
        pygame.draw.rect(screen, COLORS["bg_dark"], bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=6)
        prev_clip = screen.get_clip()
        screen.set_clip(bg)

        sc_list = self._visible_scenarios()
        if not sc_list:
            msg = fonts.body.render("(no scenarios)", True, COLORS["text_dim"])
            screen.blit(msg, (list_x + 10, list_y + 10))
        for idx, s in enumerate(sc_list):
            ry = list_y + idx * row_h + self.scroll
            row = pygame.Rect(list_x + 3, ry + 2, list_w - 6, row_h - 4)
            if s is self.selected_scenario:
                pygame.draw.rect(screen, COLORS["accent"], row, border_radius=4)
            elif row.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["panel"], row, border_radius=4)

            name_surf = fonts.small_bold.render(s.name, True, COLORS["text"])
            screen.blit(name_surf, (list_x + 10, ry + 6))

            lvl = f"Lv {s.recommended_level_min}-{s.recommended_level_max}  " \
                  f"· {len(s.monsters)} monsters"
            lvl_surf = fonts.tiny.render(lvl, True, COLORS["text_dim"])
            screen.blit(lvl_surf, (list_x + 10, ry + 26))

            if s.tags:
                tag_str = " ".join(f"#{t}" for t in s.tags[:3])
                tag_surf = fonts.tiny.render(tag_str, True, COLORS["text_dim"])
                screen.blit(tag_surf, (list_x + 10, ry + 42))

        screen.set_clip(prev_clip)

    def _draw_preview(self, screen):
        px = self.x + 565
        py = self.y + 60
        pw = self.WIDTH - 580
        ph = self.HEIGHT - 130

        bg = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(screen, COLORS["bg_dark"], bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=6)

        s = self.selected_scenario
        if s is None:
            msg = fonts.body.render("Valitse skenaario",
                                    True, COLORS["text_dim"])
            screen.blit(msg, (px + 15, py + 15))
            return

        y = py + 10
        title = fonts.body_bold.render(s.name, True, COLORS["accent"])
        screen.blit(title, (px + 12, y))
        y += 28

        meta = f"{CATEGORY_LABELS[s.category]} · Lv " \
               f"{s.recommended_level_min}-{s.recommended_level_max}"
        meta_surf = fonts.small.render(meta, True, COLORS["text_dim"])
        screen.blit(meta_surf, (px + 12, y))
        y += 22

        # Description (wrapped)
        y = self._blit_wrapped(screen, s.description, px + 12, y,
                                pw - 24, fonts.small, COLORS["text"])
        y += 10

        # Monsters
        mons_title = fonts.small_bold.render("Monsters:", True, COLORS["text"])
        screen.blit(mons_title, (px + 12, y))
        y += 20
        from collections import Counter
        mon_counts = Counter(m.name for m in s.monsters)
        for name, n in mon_counts.most_common():
            line = f"  {n}× {name}"
            screen.blit(fonts.tiny.render(line, True, COLORS["text_dim"]),
                        (px + 12, y))
            y += 16

        # Environment facts
        y += 6
        if s.ceiling_ft:
            screen.blit(fonts.tiny.render(f"Ceiling: {s.ceiling_ft} ft",
                                          True, COLORS["text_dim"]),
                        (px + 12, y))
            y += 14
        if s.weather and s.weather != "Clear":
            screen.blit(fonts.tiny.render(f"Weather: {s.weather}",
                                          True, COLORS["text_dim"]),
                        (px + 12, y))

    @staticmethod
    def _blit_wrapped(screen, text, x, y, max_w, font, color):
        words = text.split()
        line = ""
        for w in words:
            cand = (line + " " + w).strip()
            if font.size(cand)[0] > max_w:
                screen.blit(font.render(line, True, color), (x, y))
                y += font.get_height() + 2
                line = w
            else:
                line = cand
        if line:
            screen.blit(font.render(line, True, color), (x, y))
            y += font.get_height() + 2
        return y
