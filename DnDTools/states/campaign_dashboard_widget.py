"""Campaign dashboard panel — renders ``CampaignOverview`` as a
compact top-of-screen banner (or full-screen overlay when expanded).

Used by the campaign manager as a "what's the state?" reminder
that's always one click away.
"""
from __future__ import annotations

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.campaign_dashboard import build_overview, CampaignOverview


class CampaignDashboardWidget:
    BAR_H = 60        # collapsed banner height
    EXPANDED_H = 360  # full overlay height

    def __init__(self, campaign, world, *, on_close=None):
        self.campaign = campaign
        self.world = world
        self.on_close = on_close
        self.is_open = False
        self.expanded = False

        self.btn_close = Button(
            SCREEN_WIDTH - 80, 8, 60, 28, "Sulje",
            self.close, color=COLORS.get("panel", (60, 60, 80)),
        )
        self.btn_expand = Button(
            SCREEN_WIDTH - 220, 8, 130, 28, "Laajenna",
            self._toggle_expand,
            color=COLORS.get("accent", (180, 180, 240)),
        )

    def open(self):
        self.is_open = True
        self.expanded = False

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _toggle_expand(self):
        self.expanded = not self.expanded
        self.btn_expand.text = "Pienennä" if self.expanded else "Laajenna"

    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        rect = self._rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_expand):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            if rect.collidepoint(event.pos):
                return True
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False

    def _rect(self) -> pygame.Rect:
        h = self.EXPANDED_H if self.expanded else self.BAR_H
        return pygame.Rect(0, 0, SCREEN_WIDTH, h)

    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        rect = self._rect()

        overview: CampaignOverview = build_overview(
            self.campaign, self.world,
        )

        # Background
        pygame.draw.rect(screen, COLORS.get("panel_dark",
                                              (32, 32, 40)), rect)
        pygame.draw.line(screen, COLORS.get("border", (80, 80, 100)),
                         (0, rect.bottom), (rect.width, rect.bottom), 2)

        # Compact summary line
        bits = [
            f"Sessio {overview.session_number}",
            f"Aika: {overview.time_of_day or '—'}",
            f"Paikka: {overview.current_area or '—'}",
            f"Party {overview.party_active}/{overview.party_size} "
            f"· HP {overview.party_total_hp}/{overview.party_total_max_hp}",
            f"Kulta {overview.party_gold_shared:.0f}+"
            f"{overview.party_gold_per_pc:.0f} gp",
        ]
        x = 16
        for b in bits:
            surf = fonts.small.render(b, True,
                                          COLORS.get("text_bright",
                                                       (240, 240, 240)))
            screen.blit(surf, (x, 12))
            x += surf.get_width() + 28

        # Headlines (always visible — main source of "DM, look here")
        if overview.headlines:
            txt = " · ".join(overview.headlines)
            surf = fonts.tiny.render(txt, True,
                                          COLORS.get("warning",
                                                       (220, 180, 80)))
            screen.blit(surf, (16, 36))

        self.btn_expand.draw(screen, mp)
        self.btn_close.draw(screen, mp)

        if self.expanded:
            self._draw_expanded(screen, overview)

    def _draw_expanded(self, screen, o: CampaignOverview):
        y = self.BAR_H + 12
        col_w = 280
        # Column 1 — World counts
        x = 16
        screen.blit(fonts.body_bold.render("Maailma", True,
                                              COLORS.get("accent",
                                                           (180, 180, 240))),
                    (x, y))
        for label, val in (
            ("NPC:t (yht. / elossa)",
             f"{o.npc_total} / {o.npc_alive}"),
            ("Lokaatiot",
             f"{o.location_total} (asutuksia {o.location_settlements})"),
            ("Kaupat",     f"{o.shop_total}"),
            ("Palvelut",   f"{o.service_total}"),
            ("Quests (active / done)",
             f"{o.quest_active} / {o.quest_completed}"),
        ):
            screen.blit(fonts.small.render(
                f"{label}: {val}", True,
                COLORS.get("text_bright", (240, 240, 240))),
                (x, y + 24))
            y += 22

        # Column 2 — Party / encounters
        y = self.BAR_H + 12
        x = 16 + col_w
        screen.blit(fonts.body_bold.render("Joukko", True,
                                              COLORS.get("accent",
                                                           (180, 180, 240))),
                    (x, y))
        rows = [
            ("Hahmoja", f"{o.party_size}"),
            ("Aktiivisia", f"{o.party_active}"),
            ("HP", f"{o.party_total_hp} / {o.party_total_max_hp}"),
            ("Uupumus (yht.)", f"{o.party_total_exhaustion}"),
            ("Encounters (yht. / loppuun)",
             f"{o.encounters_total} / {o.encounters_completed}"),
        ]
        for label, val in rows:
            screen.blit(fonts.small.render(
                f"{label}: {val}", True,
                COLORS.get("text_bright", (240, 240, 240))),
                (x, y + 24))
            y += 22

        # Column 3 — Current area summary
        y = self.BAR_H + 12
        x = 16 + col_w * 2
        screen.blit(fonts.body_bold.render("Nykyinen alue", True,
                                              COLORS.get("accent",
                                                           (180, 180, 240))),
                    (x, y))
        if o.current_area_summary:
            sa = o.current_area_summary
            for label, val in (
                ("Paikka", sa.location.name),
                ("NPC:t",   str(len(sa.npcs))),
                ("Kaupat",  str(len(sa.shops))),
                ("Palvelut", str(len(sa.services))),
                ("Lapsisijaintit",
                 str(len(sa.child_locations))),
                ("Quests",  str(sa.quest_count)),
            ):
                screen.blit(fonts.small.render(
                    f"{label}: {val}", True,
                    COLORS.get("text_bright", (240, 240, 240))),
                    (x, y + 24))
                y += 22
        else:
            screen.blit(fonts.small.render(
                "(ei valittua aluetta)", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (x, y + 24))
