"""Phase 39 — NPC search modal.

Full-screen DM-facing finder for the NPC roster.  Type to filter by
free text; chips on the right narrow further by location / faction /
organisation.  Each hit shows name + occupation + faction +
location, with "Open" jumping to the detail card and "Goto" jumping
the campaign manager to the NPC sheet.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.npc_directory import search_npcs


class NpcSearchModal:
    WIDTH = 900
    HEIGHT = 640
    ROW_H = 44

    def __init__(self, world, campaign, *,
                  on_close: Optional[Callable[[], None]] = None,
                  on_select: Optional[Callable[[object], None]] = None,
                  on_open_detail: Optional[Callable[[object], None]] = None):
        self.world = world
        self.campaign = campaign
        self.on_close = on_close
        self.on_select = on_select
        self.on_open_detail = on_open_detail
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        # Filter state
        self.query = ""
        self.field_active = True
        self.filter_location_id = ""
        self.filter_faction = ""
        self.filter_org_key = ""
        self.scroll = 0

        # Hit rects for click-handling
        self._row_rects: List[Tuple[pygame.Rect, object,
                                       pygame.Rect, pygame.Rect]] = []
        self._loc_chip_rects: List[Tuple[pygame.Rect, str]] = []
        self._fac_chip_rects: List[Tuple[pygame.Rect, str]] = []
        self._org_chip_rects: List[Tuple[pygame.Rect, str]] = []

        self.btn_close = Button(0, 0, 90, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))
        self.btn_clear = Button(0, 0, 90, 24, "Tyhjennä",
                                   self._clear_filters,
                                   color=COLORS.get("panel_dark",
                                                      (40, 40, 56)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.scroll = 0
        self.field_active = True

    def _close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _clear_filters(self):
        self.query = ""
        self.filter_location_id = ""
        self.filter_faction = ""
        self.filter_org_key = ""
        self.scroll = 0

    # ------------------------------------------------------------------ #
    def _hits(self) -> List:
        if not self.world:
            return []
        return search_npcs(
            self.world, self.query,
            location_id=self.filter_location_id,
            faction=self.filter_faction,
            organisation_key=self.filter_org_key,
            campaign=self.campaign,
        )

    def _unique_factions(self) -> List[str]:
        s = set()
        for n in self.world.npcs.values():
            if n.faction:
                s.add(n.faction)
        return sorted(s)

    def _location_choices(self) -> List[Tuple[str, str]]:
        # (location_id, display_name)
        out = []
        for lid, loc in (self.world.locations or {}).items():
            out.append((lid, loc.name))
        return sorted(out, key=lambda t: t[1].lower())

    def _organisation_choices(self) -> List[Tuple[str, str]]:
        if self.campaign is None:
            return []
        try:
            from data import organizations as orgs
            return [(o.key, o.name)
                     for o in orgs.ensure_organisations_on_campaign(
                         self.campaign)]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close()
                return True
            if self.field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.query = self.query[:-1]
                    return True
                if event.unicode and event.unicode.isprintable():
                    if len(self.query) < 60:
                        self.query += event.unicode
                    return True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_clear):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            # Click in query field?
            qf = pygame.Rect(self.x + 20, self.y + 50,
                              self.WIDTH - 40, 32)
            self.field_active = qf.collidepoint(event.pos)
            # Filter chips
            for rect, fid in self._loc_chip_rects:
                if rect.collidepoint(event.pos):
                    self.filter_location_id = (
                        "" if self.filter_location_id == fid else fid)
                    return True
            for rect, fac in self._fac_chip_rects:
                if rect.collidepoint(event.pos):
                    self.filter_faction = (
                        "" if self.filter_faction == fac else fac)
                    return True
            for rect, key in self._org_chip_rects:
                if rect.collidepoint(event.pos):
                    self.filter_org_key = (
                        "" if self.filter_org_key == key else key)
                    return True
            # Result rows
            for row, npc, open_btn, goto_btn in self._row_rects:
                if open_btn.collidepoint(event.pos):
                    if self.on_open_detail:
                        self.on_open_detail(npc)
                    return True
                if goto_btn.collidepoint(event.pos):
                    if self.on_select:
                        self.on_select(npc)
                    self._close()
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
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (22, 22, 30)),
                          rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (130, 130, 160)),
                          rect, 2, border_radius=10)

        # Header
        screen.blit(fonts.body_bold.render(
            f"NPC-hakemisto ({len(self.world.npcs)} hahmoa)",
            True, COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, self.y + 14))
        self.btn_close.rect.x = rect.right - 110
        self.btn_close.rect.y = self.y + 12
        self.btn_close.draw(screen, mp)

        # Query field
        qf = pygame.Rect(self.x + 20, self.y + 50,
                          self.WIDTH - 40, 32)
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                          qf, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.field_active
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, qf, 1, border_radius=4)
        cursor = ("|" if self.field_active
                            and pygame.time.get_ticks() // 400 % 2 == 0
                    else "")
        prompt = self.query + cursor
        if not self.query and not self.field_active:
            prompt = "(hae nimellä, ammatilla, faktiolla, taustalla…)"
        screen.blit(fonts.body.render(
            prompt, True,
            COLORS.get("text_bright", (240, 240, 250))
            if self.query else COLORS.get("text_dim",
                                              (140, 140, 150))),
            (qf.x + 8, qf.y + 4))
        # Clear button
        self.btn_clear.rect.x = qf.right - 95
        self.btn_clear.rect.y = qf.y + 4
        self.btn_clear.draw(screen, mp)

        # Filter chip rows
        chip_y = self.y + 94
        self._loc_chip_rects = []
        self._fac_chip_rects = []
        self._org_chip_rects = []

        x = self.x + 20
        screen.blit(fonts.tiny.render(
            "Faktio:", True,
            COLORS.get("text_dim", (180, 180, 195))),
            (x, chip_y + 4))
        x += 60
        for fac in self._unique_factions()[:6]:
            label = fac[:18]
            w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(x, chip_y, w, 22)
            active = (self.filter_faction == fac)
            pygame.draw.rect(screen,
                              COLORS.get("accent", (110, 130, 220))
                              if active
                              else COLORS.get("panel_dark",
                                                (40, 40, 56)),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(label, True,
                                              (20, 20, 30) if active
                                              else COLORS.get(
                                                  "text_main",
                                                  (220, 220, 235))),
                          (chip.x + 7, chip.y + 4))
            self._fac_chip_rects.append((chip, fac))
            x += w + 4

        chip_y += 28
        x = self.x + 20
        screen.blit(fonts.tiny.render(
            "Org:", True,
            COLORS.get("text_dim", (180, 180, 195))),
            (x, chip_y + 4))
        x += 60
        for key, name in self._organisation_choices()[:5]:
            label = name[:20]
            w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(x, chip_y, w, 22)
            active = (self.filter_org_key == key)
            pygame.draw.rect(screen,
                              COLORS.get("legendary",
                                          (170, 110, 220))
                              if active
                              else COLORS.get("panel_dark",
                                                (40, 40, 56)),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(label, True,
                                              (20, 20, 30) if active
                                              else COLORS.get(
                                                  "text_main",
                                                  (220, 220, 235))),
                          (chip.x + 7, chip.y + 4))
            self._org_chip_rects.append((chip, key))
            x += w + 4

        # Results
        list_top = self.y + 156
        list_h = self.HEIGHT - (list_top - self.y) - 16
        list_rect = pygame.Rect(self.x + 4, list_top,
                                  self.WIDTH - 8, list_h)
        prev_clip = screen.get_clip()
        screen.set_clip(list_rect)
        self._row_rects = []
        y = list_top - self.scroll
        hits = self._hits()
        for hit in hits:
            n = hit.npc
            row = pygame.Rect(self.x + 16, y,
                                self.WIDTH - 32, self.ROW_H)
            pygame.draw.rect(screen,
                              COLORS.get("panel_dark", (32, 32, 42)),
                              row, border_radius=4)
            screen.blit(fonts.body_bold.render(
                n.name, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 12, row.y + 4))
            sub_bits = []
            if n.race:
                sub_bits.append(n.race)
            if n.occupation:
                sub_bits.append(n.occupation)
            if n.faction:
                sub_bits.append(n.faction)
            if n.location_id and self.world.locations.get(n.location_id):
                sub_bits.append(
                    f"@ {self.world.locations[n.location_id].name}")
            if hit.matched_fields and self.query:
                sub_bits.append(
                    f"matches: {', '.join(hit.matched_fields[:3])}")
            screen.blit(fonts.tiny.render(
                "  ·  ".join(sub_bits), True,
                COLORS.get("text_dim", (180, 180, 195))),
                (row.x + 12, row.y + 24))
            # Action buttons
            open_btn = pygame.Rect(row.right - 200, row.y + 8,
                                      90, 26)
            goto_btn = pygame.Rect(row.right - 100, row.y + 8,
                                      88, 26)
            pygame.draw.rect(screen,
                              COLORS.get("accent", (110, 130, 220)),
                              open_btn, border_radius=4)
            pygame.draw.rect(screen,
                              COLORS.get("success", (90, 200, 120)),
                              goto_btn, border_radius=4)
            screen.blit(fonts.small.render(
                "Avaa", True, (20, 20, 30)),
                (open_btn.x + 26, open_btn.y + 5))
            screen.blit(fonts.small.render(
                "Hyppää", True, (20, 20, 30)),
                (goto_btn.x + 16, goto_btn.y + 5))
            self._row_rects.append((row, n, open_btn, goto_btn))
            y += self.ROW_H + 4
        if not hits:
            screen.blit(fonts.small.render(
                "(Ei osumia.)", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (list_rect.x + 16, list_top + 16))
        screen.set_clip(prev_clip)
