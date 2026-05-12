"""Kingdom navigator — full-screen widget that shows the campaign's
five kingdoms, their cities, demographics, treasuries and relations.

Left column = kingdom list.  Right column = selected kingdom's detail
(population, crown gold, motto, primary export, relation chip row) +
its city list with a per-city wealth breakdown.  Click a city to open
the demographics / relations / income-source detail sheet.

Pure-pygame; uses :mod:`data.kingdoms`, :mod:`data.wealth`,
:mod:`data.demographics` and :mod:`data.organizations` for read-only
queries — no schema mutations.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import kingdoms as kg
from data import wealth as wlth
from data import organizations as orgs


# Attitude → tint for relation chips.
_REL_COLOR = {
    "ally":     (90, 200, 120),
    "trade":    (100, 180, 220),
    "neutral":  (140, 140, 150),
    "wary":     (210, 180, 90),
    "hostile":  (220, 100, 90),
    "at_war":   (240, 60, 60),
    "self":     (80, 80, 90),
}


def _gp(amount: float) -> str:
    """Format a gold amount: 1234 → '1,234 gp', 1.2M → '1.2M gp'."""
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M gp"
    if amount >= 10_000:
        return f"{amount / 1000:.1f}k gp"
    return f"{amount:.0f} gp"


def _pop(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1000:.1f}k"
    return f"{n:,}".replace(",", " ")


class KingdomNavigatorWidget:
    """Phase 23b kingdom + city navigator."""
    KINGDOM_ROW_H = 48
    CITY_ROW_H = 40

    def __init__(self, campaign, world,
                  on_close: Optional[Callable[[], None]] = None,
                  on_npc_click: Optional[Callable[[str], None]] = None):
        self.campaign = campaign
        self.world = world
        self.on_close = on_close
        self.on_npc_click = on_npc_click
        self.is_open = False
        self.selected_kingdom_key: str = ""
        self.selected_city_key: str = ""
        self.scroll_cities = 0

        self.btn_close = Button(0, 0, 80, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel_dark",
                                                     (40, 40, 60)))
        self._city_rects: List[Tuple[pygame.Rect, kg.CityEntry]] = []
        self._kingdom_rects: List[Tuple[pygame.Rect, kg.KingdomEntry]] = []

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self) -> None:
        self.is_open = True
        ks = kg.ensure_kingdoms_on_campaign(self.campaign)
        if ks and not self.selected_kingdom_key:
            self.selected_kingdom_key = ks[0].key
        self.scroll_cities = 0

    def _close(self) -> None:
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _kingdom(self) -> Optional[kg.KingdomEntry]:
        return kg.find_kingdom(self.campaign, self.selected_kingdom_key)

    def _city(self) -> Optional[kg.CityEntry]:
        return kg.find_city(self.campaign, self.selected_kingdom_key,
                              self.selected_city_key)

    # ------------------------------------------------------------------ #
    # Event handling
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.selected_city_key:
                self.selected_city_key = ""
            else:
                self._close()
            return True

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_cities = max(
                0, self.scroll_cities - event.y * 30)
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.rect.collidepoint(event.pos):
                self.btn_close.handle_event(event)
                return True
            for rect, k in self._kingdom_rects:
                if rect.collidepoint(event.pos):
                    if self.selected_kingdom_key != k.key:
                        self.selected_kingdom_key = k.key
                        self.selected_city_key = ""
                        self.scroll_cities = 0
                    return True
            for rect, c in self._city_rects:
                if rect.collidepoint(event.pos):
                    self.selected_city_key = (
                        "" if self.selected_city_key == c.key else c.key)
                    return True
            # Click anywhere inside the panel without hitting anything
            # → still consume so it doesn't bleed through to the host.
            return True

        return False

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def draw(self, screen) -> None:
        if not self.is_open:
            return
        # Backdrop
        scrim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        scrim.set_alpha(180)
        scrim.fill((0, 0, 0))
        screen.blit(scrim, (0, 0))

        mp = pygame.mouse.get_pos()
        bg = COLORS.get("panel_dark", (28, 28, 38))
        rect = pygame.Rect(60, 60, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 120)
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS.get("border", (70, 70, 90)),
                          rect, 2, border_radius=8)

        # Header
        screen.blit(
            fonts.body_bold.render("Valtakunnat", True,
                                      COLORS.get("text_bright",
                                                   (240, 240, 250))),
            (rect.x + 20, rect.y + 14),
        )
        # World totals strip
        tot_pop = kg.world_population(self.campaign)
        tot_gp = (wlth.world_total_wealth_gp(self.world, self.campaign)
                    if self.world is not None
                    else kg.world_treasury_total_gp(self.campaign))
        screen.blit(
            fonts.small.render(
                f"Maailman väestö: {_pop(tot_pop)}  ·  "
                f"Yhteenlaskettu varallisuus: {_gp(tot_gp)}",
                True, COLORS.get("text_dim", (170, 170, 180))),
            (rect.x + 20, rect.y + 46),
        )

        # Close button
        self.btn_close.rect.x = rect.right - 100
        self.btn_close.rect.y = rect.y + 14
        self.btn_close.draw(screen, mp)

        # Two-column layout
        left = pygame.Rect(rect.x + 16, rect.y + 80,
                            320, rect.height - 100)
        right = pygame.Rect(left.right + 16, rect.y + 80,
                             rect.right - left.right - 32,
                             rect.height - 100)

        self._draw_kingdom_list(screen, left, mp)
        self._draw_kingdom_detail(screen, right, mp)

    # ----- kingdom list ------------------------------------------------
    def _draw_kingdom_list(self, screen, area, mp) -> None:
        self._kingdom_rects = []
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        y = area.y + 8
        for k in kg.ensure_kingdoms_on_campaign(self.campaign):
            row = pygame.Rect(area.x + 6, y, area.width - 12,
                               self.KINGDOM_ROW_H)
            is_sel = (k.key == self.selected_kingdom_key)
            is_hov = row.collidepoint(mp)
            bg = (COLORS.get("accent", (110, 130, 220))
                   if is_sel
                   else COLORS.get("hover", (60, 60, 80))
                   if is_hov
                   else COLORS.get("panel_dark", (32, 32, 42)))
            pygame.draw.rect(screen, bg, row, border_radius=4)
            # Flag swatch
            sw = pygame.Rect(row.x + 6, row.y + 6, 14, row.height - 12)
            pygame.draw.rect(screen, k.flag_color or (180, 180, 180), sw,
                              border_radius=2)
            screen.blit(
                fonts.body_bold.render(
                    k.name, True,
                    COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 28, row.y + 4),
            )
            sub = f"{_pop(kg.kingdom_population(k))}  ·  " \
                  f"{_gp(kg.kingdom_treasury_total_gp(k))}"
            screen.blit(
                fonts.tiny.render(sub, True,
                                    COLORS.get("text_dim",
                                                 (180, 180, 190))),
                (row.x + 28, row.y + 24),
            )
            self._kingdom_rects.append((row, k))
            y += self.KINGDOM_ROW_H + 4

    # ----- kingdom detail ---------------------------------------------
    def _draw_kingdom_detail(self, screen, area, mp) -> None:
        self._city_rects = []
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        k = self._kingdom()
        if k is None:
            screen.blit(fonts.body.render(
                "Valitse valtakunta vasemmalta.", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (area.x + 16, area.y + 16))
            return

        # Title row
        screen.blit(
            fonts.body_bold.render(k.name, True,
                                      COLORS.get("text_bright",
                                                   (240, 240, 250))),
            (area.x + 16, area.y + 10),
        )
        if k.motto:
            screen.blit(
                fonts.tiny.render(f"“{k.motto}”", True,
                                    COLORS.get("text_dim",
                                                 (180, 180, 190))),
                (area.x + 16, area.y + 36),
            )

        # Stat row
        stats = [
            ("Väestö", _pop(kg.kingdom_population(k))),
            ("Kruunun kassa", _gp(k.treasury_gp)),
            ("Yhteensä", _gp(wlth.kingdom_total_wealth_gp(self.world, k))
                          if self.world is not None
                          else _gp(kg.kingdom_treasury_total_gp(k))),
            ("Päävienti", k.primary_export or "—"),
            ("Biomi", k.biome or "—"),
            ("Hallitseva usko", k.capital_religion or "—"),
        ]
        sx = area.x + 16
        sy = area.y + 58
        for label, val in stats:
            chip_w = max(120, fonts.small_bold.size(val)[0] + 24)
            chip = pygame.Rect(sx, sy, chip_w, 36)
            pygame.draw.rect(screen, COLORS.get("panel_dark", (32, 32, 42)),
                              chip, border_radius=4)
            screen.blit(fonts.tiny.render(label, True,
                                              COLORS.get("text_dim",
                                                           (170, 170, 180))),
                          (chip.x + 8, chip.y + 4))
            screen.blit(fonts.small_bold.render(val, True,
                                                    COLORS.get("text_bright",
                                                                 (240, 240, 250))),
                          (chip.x + 8, chip.y + 16))
            sx += chip_w + 6
            if sx > area.right - 130:
                sx = area.x + 16
                sy += 42

        # Relations strip
        rels_y = sy + 50
        screen.blit(
            fonts.small_bold.render(
                "Suhteet:", True,
                COLORS.get("text_bright", (240, 240, 250))),
            (area.x + 16, rels_y - 22),
        )
        rx = area.x + 16
        for other in kg.ensure_kingdoms_on_campaign(self.campaign):
            if other.key == k.key:
                continue
            attitude = k.relations.get(other.key, "neutral")
            label = f"{other.name}: {attitude}"
            chip_w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(rx, rels_y, chip_w, 22)
            pygame.draw.rect(screen, _REL_COLOR.get(attitude,
                                                       (140, 140, 150)),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(label, True, (20, 20, 30)),
                          (chip.x + 7, chip.y + 4))
            rx += chip_w + 6

        # City list header
        cities_y = rels_y + 38
        screen.blit(
            fonts.small_bold.render(
                f"Kaupungit ({len(k.cities)})", True,
                COLORS.get("text_bright", (240, 240, 250))),
            (area.x + 16, cities_y),
        )

        # City rows (scrollable)
        list_top = cities_y + 22
        list_rect = pygame.Rect(area.x + 8, list_top,
                                  area.width - 16,
                                  area.bottom - list_top - 8)
        prev_clip = screen.get_clip()
        screen.set_clip(list_rect)
        y = list_top - self.scroll_cities
        for c in k.cities:
            row = pygame.Rect(list_rect.x + 4, y,
                                list_rect.width - 8, self.CITY_ROW_H)
            is_sel = (c.key == self.selected_city_key)
            is_hov = row.collidepoint(mp)
            bg = (COLORS.get("accent", (110, 130, 220))
                   if is_sel
                   else COLORS.get("hover", (60, 60, 80))
                   if is_hov
                   else COLORS.get("panel_dark", (32, 32, 42)))
            pygame.draw.rect(screen, bg, row, border_radius=4)
            star = "★ " if c.is_capital else ""
            screen.blit(fonts.body_bold.render(
                f"{star}{c.name}", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 10, row.y + 4))
            br = wlth.city_wealth_breakdown(self.world, c) \
                if self.world is not None \
                else {"total": float(c.treasury_gp or 0.0),
                       "crown": float(c.treasury_gp or 0.0),
                       "npcs": 0, "shops": 0, "banks": 0}
            sub = (f"{_pop(kg.city_population(c))} as.  ·  "
                    f"{_gp(br['total'])}  "
                    f"(kassa {_gp(br['crown'])}, "
                    f"asukkaat {_gp(br['npcs'])}, "
                    f"kaupat {_gp(br['shops'])}, "
                    f"pankki {_gp(br['banks'])})")
            screen.blit(fonts.tiny.render(
                sub, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (row.x + 10, row.y + 22))
            self._city_rects.append((row, c))
            y += self.CITY_ROW_H + 4

            # Expanded detail under selected city
            if is_sel:
                detail_h = 130
                drow = pygame.Rect(row.x + 16, y,
                                     row.width - 32, detail_h)
                pygame.draw.rect(screen, COLORS.get("panel",
                                                       (50, 50, 70)),
                                  drow, border_radius=4)
                self._draw_city_detail(screen, drow, c, k)
                y += detail_h + 6
        if not k.cities:
            screen.blit(fonts.small.render(
                "(Ei kaupunkeja vielä — lisää navigaattorin kautta.)",
                True, COLORS.get("text_dim", (160, 160, 170))),
                (list_rect.x + 8, list_top + 8))
        screen.set_clip(prev_clip)

    def _draw_city_detail(self, screen, drow, c, k) -> None:
        # Demographics chips
        demo = c.demographics or {}
        if not demo and c.biome:
            from data.demographics import suggest_demographics
            demo = suggest_demographics(c.biome,
                                         total_population=c.population).by_race
        if demo:
            screen.blit(fonts.small_bold.render(
                "Rotujakauma:", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (drow.x + 8, drow.y + 6))
            sx = drow.x + 110
            for race, pct in list(demo.items())[:8]:
                txt = f"{race} {pct:.0f}%"
                chip_w = fonts.tiny.size(txt)[0] + 12
                chip = pygame.Rect(sx, drow.y + 8, chip_w, 18)
                pygame.draw.rect(screen,
                                  COLORS.get("panel_dark",
                                              (32, 32, 42)),
                                  chip, border_radius=9)
                screen.blit(fonts.tiny.render(
                    txt, True,
                    COLORS.get("text_bright", (240, 240, 250))),
                    (chip.x + 6, chip.y + 2))
                sx += chip_w + 4
                if sx > drow.right - 20:
                    break

        # Industry / income / religion
        screen.blit(fonts.tiny.render(
            f"Pääelinkeino: {c.primary_industry or '—'}",
            True, COLORS.get("text_dim", (180, 180, 190))),
            (drow.x + 8, drow.y + 36))
        if c.income_sources:
            screen.blit(fonts.tiny.render(
                f"Tulonlähteet: {', '.join(c.income_sources)}",
                True, COLORS.get("text_dim", (180, 180, 190))),
                (drow.x + 8, drow.y + 52))
        if c.religion:
            screen.blit(fonts.tiny.render(
                f"Hallitseva usko: {c.religion}",
                True, COLORS.get("text_dim", (180, 180, 190))),
                (drow.x + 8, drow.y + 68))

        # Organisations operating in this city
        op_list = orgs.organisations_in_city(self.campaign, c.key)
        if op_list:
            screen.blit(fonts.small_bold.render(
                "Organisaatiot:", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (drow.x + 8, drow.y + 88))
            sx = drow.x + 110
            for o in op_list[:6]:
                txt = o.name
                chip_w = fonts.tiny.size(txt)[0] + 12
                chip = pygame.Rect(sx, drow.y + 90, chip_w, 18)
                pygame.draw.rect(screen,
                                  (o.color or (160, 160, 160)),
                                  chip, border_radius=9)
                screen.blit(fonts.tiny.render(
                    txt, True, (20, 20, 30)),
                    (chip.x + 6, chip.y + 2))
                sx += chip_w + 4

        # Inter-city relations (compact line)
        if c.relations:
            rels = ", ".join(
                f"{ck}: {att}" for ck, att in list(c.relations.items())[:6])
            screen.blit(fonts.tiny.render(
                f"Suhteet: {rels}", True,
                COLORS.get("text_dim", (180, 180, 190))),
                (drow.x + 8, drow.y + 110))
