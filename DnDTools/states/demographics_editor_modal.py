"""Demographics editor — modal for editing one city's race breakdown.

Opened from the kingdom navigator's city card.  UI:

* Total-population field (numeric, editable).
* Biome cycler — click to step through known biomes.
* Race table — each row shows ``Race  [—]  pct%  [+]`` with the
  percentage editable by clicking +/- or typing.
* Toolbar: "Ehdota biomin mukaan" overwrites the breakdown with the
  biome's default distribution.  "Lisää rotu" cycles a new race onto
  the list.  "Tallenna" persists into ``CityEntry.demographics`` /
  ``population`` / ``biome``.

The widget never touches anything other than the supplied
:class:`CityEntry`.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import demographics as demo
from data.kingdoms import CityEntry


class DemographicsEditorModal:
    WIDTH = 560
    HEIGHT = 520
    ROW_H = 26

    def __init__(self, city: CityEntry, *,
                  on_close: Optional[Callable[[], None]] = None):
        self.city = city
        self.on_close = on_close
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        # Snapshot working state — we commit only on "Tallenna".
        self.population_str = str(city.population or 0)
        self.population_field_active = False
        self.biome = city.biome or "human_heartland"
        self.by_race: dict = dict(city.demographics or {})
        if not self.by_race:
            # Seed from biome so the table is never empty
            seeded = demo.suggest_demographics(
                self.biome, total_population=0).by_race
            self.by_race = dict(seeded)
        # Race-to-add cycler index
        self._add_index = 0
        self._status = ""
        # Hit-tested per draw
        self._row_actions: List[Tuple[pygame.Rect, str, str]] = []

        self.btn_close = Button(0, 0, 80, 30, "Sulje",
                                  self.close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))
        self.btn_save = Button(0, 0, 130, 30, "Tallenna",
                                 self._save,
                                 color=COLORS.get("success",
                                                    (90, 200, 120)))
        self.btn_suggest = Button(0, 0, 220, 30,
                                     "Ehdota biomin mukaan",
                                     self._apply_biome_suggestion,
                                     color=COLORS.get("accent",
                                                        (110, 130, 220)))
        self.btn_add_race = Button(0, 0, 160, 30, "Lisää rotu",
                                      self._add_race,
                                      color=COLORS.get("legendary",
                                                         (170, 110, 220)))
        self.btn_biome = Button(0, 0, 220, 30,
                                   self._biome_label(),
                                   self._cycle_biome,
                                   color=COLORS.get("warning",
                                                      (220, 180, 80)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    def _biome_label(self) -> str:
        return f"Biomi: {self.biome}"

    def _cycle_biome(self):
        keys = list(demo.known_biomes())
        if self.biome not in keys:
            keys.insert(0, self.biome)
        i = keys.index(self.biome)
        self.biome = keys[(i + 1) % len(keys)]
        self.btn_biome.text = self._biome_label()

    def _apply_biome_suggestion(self):
        try:
            pop = int(self.population_str or 0)
        except ValueError:
            pop = 0
        d = demo.suggest_demographics(self.biome, total_population=pop)
        self.by_race = dict(d.by_race)
        self._status = f"Asetettu {self.biome}-jakauma."

    def _add_race(self):
        all_races = list(demo.COMMON_RACES)
        missing = [r for r in all_races if r not in self.by_race]
        if not missing:
            self._status = "Kaikki rodut jo listalla."
            return
        race = missing[self._add_index % len(missing)]
        self._add_index += 1
        # Steal 5% from the largest existing entry so the total stays
        # close to 100%.
        if self.by_race:
            top = max(self.by_race, key=lambda k: self.by_race[k])
            self.by_race[top] = max(0, self.by_race[top] - 5)
        self.by_race[race] = self.by_race.get(race, 0) + 5
        self._status = f"Lisätty {race}."

    def _bump(self, race: str, delta: int):
        cur = int(self.by_race.get(race, 0))
        nxt = max(0, min(100, cur + delta))
        self.by_race[race] = nxt

    def _delete_race(self, race: str):
        self.by_race.pop(race, None)
        self._status = f"Poistettu {race}."

    def _save(self):
        try:
            pop = int(self.population_str or 0)
        except ValueError:
            pop = 0
            self._status = "Väkiluku ei kelpaa — asetettu 0."
        self.city.population = max(0, pop)
        self.city.biome = self.biome
        # Drop zero rows
        self.city.demographics = {
            r: int(v) for r, v in self.by_race.items() if int(v) > 0
        }
        self._status = "Tallennettu."

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.population_field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.population_str = self.population_str[:-1]
                    return True
                if event.key == pygame.K_RETURN:
                    self.population_field_active = False
                    return True
                if event.unicode and event.unicode.isdigit():
                    if len(self.population_str) < 10:
                        self.population_str += event.unicode
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_save,
                          self.btn_suggest, self.btn_add_race,
                          self.btn_biome):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            pop_field = pygame.Rect(self.x + 200, self.y + 56,
                                      180, 26)
            self.population_field_active = pop_field.collidepoint(event.pos)
            for rect, kind, race in self._row_actions:
                if rect.collidepoint(event.pos):
                    if kind == "minus":
                        self._bump(race, -5)
                    elif kind == "plus":
                        self._bump(race, +5)
                    elif kind == "del":
                        self._delete_race(race)
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
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                         rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                         rect, 2, border_radius=10)

        # Title
        screen.blit(fonts.body_bold.render(
            f"Demografia — {self.city.name}", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 18, self.y + 16))

        # Population row
        screen.blit(fonts.small.render(
            "Väkiluku:", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 18, self.y + 60))
        pop_field = pygame.Rect(self.x + 200, self.y + 56, 180, 26)
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                          pop_field, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.population_field_active
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, pop_field, 1, border_radius=4)
        cursor = ("|" if self.population_field_active
                            and pygame.time.get_ticks() // 400 % 2 == 0
                    else "")
        screen.blit(fonts.body.render(
            self.population_str + cursor, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (pop_field.x + 8, pop_field.y + 4))

        # Toolbar (biome cycler + suggest + add)
        self.btn_biome.rect.x = self.x + 18
        self.btn_biome.rect.y = self.y + 96
        self.btn_biome.text = self._biome_label()
        self.btn_biome.draw(screen, mp)

        self.btn_suggest.rect.x = self.x + 248
        self.btn_suggest.rect.y = self.y + 96
        self.btn_suggest.draw(screen, mp)

        self.btn_add_race.rect.x = self.x + 18
        self.btn_add_race.rect.y = self.y + 132
        self.btn_add_race.draw(screen, mp)

        # Race table
        table_top = self.y + 178
        self._row_actions = []
        # Header
        screen.blit(fonts.small_bold.render(
            "Rotu", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 24, table_top - 22))
        screen.blit(fonts.small_bold.render(
            "%-osuus", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 230, table_top - 22))
        screen.blit(fonts.small_bold.render(
            "Väki", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 350, table_top - 22))
        try:
            total_pop = int(self.population_str or 0)
        except ValueError:
            total_pop = 0
        total_pct = sum(int(v) for v in self.by_race.values())
        y = table_top
        for race, pct in sorted(self.by_race.items(),
                                  key=lambda kv: -int(kv[1])):
            row = pygame.Rect(self.x + 18, y, self.WIDTH - 36, self.ROW_H)
            pygame.draw.rect(screen,
                              COLORS.get("panel_dark", (40, 40, 56)),
                              row, border_radius=4)
            screen.blit(fonts.small.render(
                race, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 8, row.y + 4))
            # +/- buttons
            minus = pygame.Rect(row.x + 200, row.y + 3, 22, 20)
            plus = pygame.Rect(row.x + 282, row.y + 3, 22, 20)
            pygame.draw.rect(screen,
                              COLORS.get("warning", (220, 180, 80)),
                              minus, border_radius=3)
            pygame.draw.rect(screen,
                              COLORS.get("success", (90, 200, 120)),
                              plus, border_radius=3)
            screen.blit(fonts.small_bold.render(
                "−", True, (30, 30, 30)),
                (minus.x + 8, minus.y + 1))
            screen.blit(fonts.small_bold.render(
                "+", True, (30, 30, 30)),
                (plus.x + 7, plus.y + 1))
            screen.blit(fonts.small_bold.render(
                f"{int(pct)}%", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 230, row.y + 4))
            if total_pop > 0:
                people = int(round(total_pop * pct / 100.0))
                screen.blit(fonts.small.render(
                    f"{people:,}".replace(",", " "), True,
                    COLORS.get("text_dim", (180, 180, 190))),
                    (row.x + 350, row.y + 4))
            # Delete (×)
            delx = pygame.Rect(row.right - 28, row.y + 3, 22, 20)
            pygame.draw.rect(screen,
                              COLORS.get("danger", (220, 100, 90)),
                              delx, border_radius=3)
            screen.blit(fonts.small_bold.render(
                "×", True, (30, 30, 30)),
                (delx.x + 7, delx.y + 1))
            self._row_actions.append((minus, "minus", race))
            self._row_actions.append((plus, "plus", race))
            self._row_actions.append((delx, "del", race))
            y += self.ROW_H + 4
            if y > self.y + self.HEIGHT - 90:
                break  # don't overflow

        # Footer totals
        screen.blit(fonts.small.render(
            f"Yhteensä: {total_pct}%", True,
            (COLORS.get("warning", (220, 180, 80))
              if abs(total_pct - 100) > 2
              else COLORS.get("success", (90, 200, 120)))),
            (self.x + 18, self.y + self.HEIGHT - 80))

        if self._status:
            screen.blit(fonts.small.render(
                self._status, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 18, self.y + self.HEIGHT - 58))

        # Save / close
        self.btn_save.rect.x = self.x + 18
        self.btn_save.rect.y = self.y + self.HEIGHT - 40
        self.btn_save.draw(screen, mp)
        self.btn_close.rect.x = self.x + self.WIDTH - 100
        self.btn_close.rect.y = self.y + self.HEIGHT - 40
        self.btn_close.draw(screen, mp)
