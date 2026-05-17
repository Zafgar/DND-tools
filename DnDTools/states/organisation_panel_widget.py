"""Organisation panel — full-screen widget listing the campaign's
organisations (guilds, churches, brotherhoods, criminal cells).

Left column = organisation list.  Right column = the selected
organisation's detail: motto, kind, alignment, headquarters, ranks +
members grouped under each rank.  Clicking a member with an NPC id
fires ``on_npc_click(npc_id)`` so the campaign manager can navigate to
their sheet.

Pure-pygame; reads :mod:`data.organizations` only.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import organizations as orgs


class OrganisationPanelWidget:
    """Phase 23c organisation list + drill-down."""
    ORG_ROW_H = 50
    MEMBER_ROW_H = 28

    def __init__(self, campaign,
                  on_close: Optional[Callable[[], None]] = None,
                  on_npc_click: Optional[Callable[[str], None]] = None):
        self.campaign = campaign
        self.on_close = on_close
        self.on_npc_click = on_npc_click
        self.is_open = False
        self.selected_key: str = ""
        self.scroll = 0

        self.btn_close = Button(0, 0, 80, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel_dark",
                                                     (40, 40, 60)))
        self._org_rects: List[Tuple[pygame.Rect, orgs.Organisation]] = []
        self._member_rects: List[Tuple[pygame.Rect,
                                          orgs.OrganisationMember]] = []

    # ------------------------------------------------------------------ #
    def open(self) -> None:
        self.is_open = True
        all_orgs = orgs.ensure_organisations_on_campaign(self.campaign)
        if all_orgs and not self.selected_key:
            self.selected_key = all_orgs[0].key
        self.scroll = 0

    def _close(self) -> None:
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _selected_org(self) -> Optional[orgs.Organisation]:
        return orgs.find_organisation(self.campaign, self.selected_key)

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.rect.collidepoint(event.pos):
                self.btn_close.handle_event(event)
                return True
            for rect, o in self._org_rects:
                if rect.collidepoint(event.pos):
                    if self.selected_key != o.key:
                        self.selected_key = o.key
                        self.scroll = 0
                    return True
            for rect, m in self._member_rects:
                if rect.collidepoint(event.pos):
                    if m.npc_id and self.on_npc_click:
                        self.on_npc_click(m.npc_id)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def draw(self, screen) -> None:
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        scrim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        scrim.set_alpha(180)
        scrim.fill((0, 0, 0))
        screen.blit(scrim, (0, 0))

        bg = COLORS.get("panel_dark", (28, 28, 38))
        rect = pygame.Rect(60, 60, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 120)
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS.get("border", (70, 70, 90)),
                          rect, 2, border_radius=8)

        screen.blit(
            fonts.body_bold.render("Organisaatiot", True,
                                      COLORS.get("text_bright",
                                                   (240, 240, 250))),
            (rect.x + 20, rect.y + 14),
        )
        self.btn_close.rect.x = rect.right - 100
        self.btn_close.rect.y = rect.y + 14
        self.btn_close.draw(screen, mp)

        left = pygame.Rect(rect.x + 16, rect.y + 56, 340,
                            rect.height - 80)
        right = pygame.Rect(left.right + 16, rect.y + 56,
                             rect.right - left.right - 32,
                             rect.height - 80)
        self._draw_org_list(screen, left, mp)
        self._draw_org_detail(screen, right, mp)

    # ----- left list ---------------------------------------------------
    def _draw_org_list(self, screen, area, mp) -> None:
        self._org_rects = []
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        y = area.y + 8
        for o in orgs.ensure_organisations_on_campaign(self.campaign):
            row = pygame.Rect(area.x + 6, y, area.width - 12,
                               self.ORG_ROW_H)
            is_sel = (o.key == self.selected_key)
            is_hov = row.collidepoint(mp)
            bg = (COLORS.get("accent", (110, 130, 220))
                   if is_sel
                   else COLORS.get("hover", (60, 60, 80))
                   if is_hov
                   else COLORS.get("panel_dark", (32, 32, 42)))
            pygame.draw.rect(screen, bg, row, border_radius=4)
            sw = pygame.Rect(row.x + 6, row.y + 6, 14, row.height - 12)
            pygame.draw.rect(screen, o.color or (160, 160, 160), sw,
                              border_radius=2)
            tag = o.name + (" 🜸" if o.secret else "")
            screen.blit(
                fonts.body_bold.render(tag, True,
                                          COLORS.get("text_bright",
                                                       (240, 240, 250))),
                (row.x + 28, row.y + 4),
            )
            sub = f"{o.kind}  ·  {len([m for m in o.members if m.active])} jäs."
            screen.blit(
                fonts.tiny.render(sub, True,
                                    COLORS.get("text_dim",
                                                 (180, 180, 190))),
                (row.x + 28, row.y + 24),
            )
            self._org_rects.append((row, o))
            y += self.ORG_ROW_H + 4
        if not self._org_rects:
            screen.blit(fonts.small.render(
                "(Ei organisaatioita.)", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (area.x + 12, area.y + 12))

    # ----- right detail ------------------------------------------------
    def _draw_org_detail(self, screen, area, mp) -> None:
        self._member_rects = []
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        o = self._selected_org()
        if o is None:
            screen.blit(fonts.body.render(
                "Valitse organisaatio vasemmalta.", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (area.x + 16, area.y + 16))
            return

        # Title strip
        screen.blit(
            fonts.body_bold.render(o.name, True,
                                      COLORS.get("text_bright",
                                                   (240, 240, 250))),
            (area.x + 16, area.y + 10),
        )
        if o.motto:
            screen.blit(
                fonts.tiny.render(f"“{o.motto}”", True,
                                    COLORS.get("text_dim",
                                                 (180, 180, 190))),
                (area.x + 16, area.y + 34),
            )
        sub = f"{o.kind}"
        if o.alignment:
            sub += f"  ·  {o.alignment}"
        if o.headquarters_kingdom:
            sub += f"  ·  HQ: {o.headquarters_kingdom}"
        if o.secret:
            sub += "  ·  salainen"
        screen.blit(
            fonts.tiny.render(sub, True,
                                COLORS.get("text_dim", (170, 170, 180))),
            (area.x + 16, area.y + 52),
        )

        # Members grouped by rank
        body_top = area.y + 80
        body_rect = pygame.Rect(area.x + 8, body_top,
                                  area.width - 16,
                                  area.bottom - body_top - 8)
        prev_clip = screen.get_clip()
        screen.set_clip(body_rect)
        y = body_top - self.scroll
        ranks_sorted = sorted(o.ranks, key=lambda r: r.tier)
        for r in ranks_sorted:
            members = o.members_at_rank(r.key)
            if not members:
                continue
            # Rank header
            screen.blit(
                fonts.small_bold.render(
                    f"{r.name}  ({len(members)})", True,
                    COLORS.get("text_bright", (240, 240, 250))),
                (body_rect.x + 6, y),
            )
            y += 22
            for m in members:
                row = pygame.Rect(body_rect.x + 14, y,
                                    body_rect.width - 20,
                                    self.MEMBER_ROW_H)
                is_hov = row.collidepoint(mp)
                clickable = bool(m.npc_id)
                bg = (COLORS.get("hover", (60, 60, 80))
                       if is_hov and clickable
                       else COLORS.get("panel_dark", (32, 32, 42)))
                pygame.draw.rect(screen, bg, row, border_radius=4)
                name = m.npc_name or m.npc_id or "(unnamed)"
                screen.blit(fonts.small_bold.render(
                    name, True,
                    COLORS.get("text_bright", (240, 240, 250))),
                    (row.x + 8, row.y + 3))
                bits = []
                if m.role_keys:
                    role_names = []
                    for rk in m.role_keys:
                        role = o.role(rk)
                        role_names.append(role.name if role else rk)
                    bits.append(", ".join(role_names))
                where = m.city_key or m.kingdom_key
                if where:
                    bits.append(where)
                if clickable:
                    bits.append("→ avaa NPC")
                screen.blit(fonts.tiny.render(
                    "  ·  ".join(bits), True,
                    COLORS.get("text_dim", (180, 180, 190))),
                    (row.x + 8, row.y + 16))
                self._member_rects.append((row, m))
                y += self.MEMBER_ROW_H + 4
            y += 6
        # Unranked members (rank_key missing)
        unranked = [m for m in o.members
                     if m.active and not m.rank_key]
        if unranked:
            screen.blit(fonts.small_bold.render(
                "Asemattomat", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (body_rect.x + 6, y))
            y += 22
            for m in unranked:
                row = pygame.Rect(body_rect.x + 14, y,
                                    body_rect.width - 20,
                                    self.MEMBER_ROW_H)
                pygame.draw.rect(screen,
                                  COLORS.get("panel_dark", (32, 32, 42)),
                                  row, border_radius=4)
                screen.blit(fonts.small_bold.render(
                    m.npc_name or m.npc_id, True,
                    COLORS.get("text_bright", (240, 240, 250))),
                    (row.x + 8, row.y + 3))
                self._member_rects.append((row, m))
                y += self.MEMBER_ROW_H + 4

        # Phase 27d — operations timeline
        if o.operations:
            y += 10
            screen.blit(fonts.small_bold.render(
                f"Operaatiot ({len(o.operations)})", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (body_rect.x + 6, y))
            y += 22
            kind_col = {
                "recruit":      (110, 180, 240),
                "sabotage":     (220, 130, 90),
                "extort":       (210, 180, 90),
                "conversion":   (190, 130, 220),
                "raid":         (220, 80, 70),
                "intelligence": (90, 180, 200),
                "ritual":       (220, 80, 220),
                "diplomacy":    (90, 200, 120),
                "other":        (160, 160, 170),
            }
            status_col = {
                "planned":   COLORS.get("text_dim", (170, 170, 180)),
                "active":    COLORS.get("accent", (110, 130, 220)),
                "completed": COLORS.get("success", (90, 200, 120)),
                "aborted":   COLORS.get("danger", (220, 100, 90)),
            }
            for op in o.operations:
                row = pygame.Rect(body_rect.x + 14, y,
                                    body_rect.width - 20, 44)
                pygame.draw.rect(screen,
                                  COLORS.get("panel_dark", (32, 32, 42)),
                                  row, border_radius=4)
                # Kind pip (left edge)
                pip = pygame.Rect(row.x, row.y, 4, row.height)
                pygame.draw.rect(screen,
                                  kind_col.get(op.kind,
                                                 (160, 160, 170)),
                                  pip)
                # Severity dots
                for i in range(5):
                    cx = row.right - 12 - i * 10
                    dot_col = ((220, 90, 70)
                                  if i < op.severity
                                  else (60, 60, 80))
                    pygame.draw.circle(screen, dot_col, (cx, row.y + 12),
                                        4)
                screen.blit(fonts.small_bold.render(
                    op.name or op.kind, True,
                    COLORS.get("text_bright", (240, 240, 250))),
                    (row.x + 12, row.y + 4))
                bits = [op.kind]
                if op.target_city_key:
                    bits.append(f"@ {op.target_city_key}")
                elif op.target_kingdom_key:
                    bits.append(f"@ {op.target_kingdom_key}")
                if op.timestamp:
                    bits.append(op.timestamp)
                screen.blit(fonts.tiny.render(
                    "  ·  ".join(bits), True,
                    COLORS.get("text_dim", (180, 180, 190))),
                    (row.x + 12, row.y + 22))
                # Status chip
                sw = fonts.tiny.size(op.status)[0] + 12
                schip = pygame.Rect(row.right - sw - 60,
                                      row.y + 22, sw, 16)
                pygame.draw.rect(screen,
                                  status_col.get(op.status,
                                                   (140, 140, 150)),
                                  schip, border_radius=8)
                screen.blit(fonts.tiny.render(
                    op.status, True, (20, 20, 30)),
                    (schip.x + 6, schip.y + 1))
                y += 48

        screen.set_clip(prev_clip)
