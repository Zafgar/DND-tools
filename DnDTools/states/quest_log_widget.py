"""Quest log widget — full-screen quest browser for the DM.

Left column = filterable quest list with status chips.  Right column
= the selected quest's full sheet: description, objectives with check
boxes, linked NPCs / shops / monsters / locations as coloured chips,
chronological log entries with gold movement totals, reward summary.

Clicking an NPC / shop / location chip fires the matching callback so
the campaign manager can jump to that entity's sheet.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import quest_log as ql


# Status → colour and Finnish label for the chip row.
_STATUS = {
    "active":      ((110, 180, 240), "Aktiivinen"),
    "completed":   ((90, 200, 120), "Valmis"),
    "failed":      ((220, 100, 90), "Epäonnistui"),
    "on_hold":     ((210, 180, 90), "Odottaa"),
    "not_started": ((140, 140, 150), "Ei aloitettu"),
}

# Quest priority → tint.
_PRI = {
    "low":     (100, 130, 130),
    "normal":  (140, 140, 150),
    "high":    (220, 180, 80),
    "urgent":  (220, 100, 90),
}

# Log entry kind → colour.
_LOG_KIND = {
    "note":        (140, 140, 150),
    "transaction": (110, 180, 240),
    "kill":        (220, 100, 90),
    "deliver":     (90, 200, 120),
    "complete":    (160, 220, 120),
}


def _gp(amount: float) -> str:
    if abs(amount) >= 1000:
        return f"{amount / 1000:+.1f}k gp"
    return f"{amount:+.0f} gp"


class QuestLogWidget:
    LIST_ROW_H = 56

    def __init__(self, campaign, world,
                  on_close: Optional[Callable[[], None]] = None,
                  on_npc_click: Optional[Callable[[str], None]] = None,
                  on_shop_click: Optional[Callable[[str], None]] = None,
                  on_location_click: Optional[Callable[[str], None]] = None):
        self.campaign = campaign
        self.world = world
        self.on_close = on_close
        self.on_npc_click = on_npc_click
        self.on_shop_click = on_shop_click
        self.on_location_click = on_location_click
        self.is_open = False
        self.selected_quest_id: str = ""
        self.status_filter: str = "all"   # all | active | completed | failed | on_hold
        self.scroll_list = 0
        self.scroll_detail = 0

        self.btn_close = Button(0, 0, 80, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel_dark",
                                                     (40, 40, 60)))
        self.btn_filter_all = Button(0, 0, 90, 24, "Kaikki",
                                        lambda: self._set_filter("all"),
                                        color=COLORS.get("panel",
                                                           (60, 60, 80)))
        self.btn_filter_active = Button(0, 0, 100, 24, "Aktiiviset",
                                            lambda: self._set_filter("active"),
                                            color=COLORS.get("accent",
                                                               (110, 180, 240)))
        self.btn_filter_done = Button(0, 0, 90, 24, "Valmiit",
                                          lambda: self._set_filter("completed"),
                                          color=COLORS.get("success",
                                                             (90, 200, 120)))
        self.btn_complete = Button(0, 0, 150, 28, "Merkitse valmiiksi",
                                       self._mark_complete,
                                       color=COLORS.get("success",
                                                          (90, 200, 120)))
        self.btn_fail = Button(0, 0, 130, 28, "Epäonnistui",
                                  self._mark_failed,
                                  color=COLORS.get("danger",
                                                     (220, 100, 90)))
        # Per-frame hit-tested rects
        self._list_rects: List[Tuple[pygame.Rect, str]] = []
        self._chip_rects: List[Tuple[pygame.Rect, str, str]] = []

    # ------------------------------------------------------------------ #
    def open(self) -> None:
        self.is_open = True
        if (not self.selected_quest_id) and self.world is not None:
            for q in self.world.quests.values():
                self.selected_quest_id = q.id
                break

    def _close(self) -> None:
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _set_filter(self, status: str) -> None:
        self.status_filter = status
        self.scroll_list = 0

    def _selected_quest(self):
        if not self.world or not self.selected_quest_id:
            return None
        return self.world.quests.get(self.selected_quest_id)

    def _filtered_quests(self) -> List:
        if not self.world:
            return []
        items = list(self.world.quests.values())
        if self.status_filter != "all":
            items = [q for q in items if q.status == self.status_filter]
        # Sort: active first, then by priority, then by name
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        items.sort(key=lambda q: (
            0 if q.status == "active" else 1,
            priority_order.get(q.priority, 2),
            q.name.lower(),
        ))
        return items

    def _mark_complete(self) -> None:
        q = self._selected_quest()
        if q is None:
            return
        ql.complete_quest(q, campaign=self.campaign)

    def _mark_failed(self) -> None:
        q = self._selected_quest()
        if q is None:
            return
        q.status = "failed"
        ql.log_event(q, kind="note", description="Tehtävä epäonnistui.",
                       campaign=self.campaign)

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return True
        if event.type == pygame.MOUSEWHEEL:
            # Default: scroll detail. Holding shift scrolls the list.
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                self.scroll_list = max(
                    0, self.scroll_list - event.y * 30)
            else:
                self.scroll_detail = max(
                    0, self.scroll_detail - event.y * 30)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_filter_all,
                          self.btn_filter_active, self.btn_filter_done,
                          self.btn_complete, self.btn_fail):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            for rect, qid in self._list_rects:
                if rect.collidepoint(event.pos):
                    if self.selected_quest_id != qid:
                        self.selected_quest_id = qid
                        self.scroll_detail = 0
                    return True
            for rect, kind, oid in self._chip_rects:
                if rect.collidepoint(event.pos):
                    if kind == "npc" and self.on_npc_click:
                        self.on_npc_click(oid)
                    elif kind == "shop" and self.on_shop_click:
                        self.on_shop_click(oid)
                    elif kind == "location" and self.on_location_click:
                        self.on_location_click(oid)
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

        rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80)
        pygame.draw.rect(screen, COLORS.get("panel_dark", (28, 28, 38)),
                          rect, border_radius=8)
        pygame.draw.rect(screen, COLORS.get("border", (70, 70, 90)),
                          rect, 2, border_radius=8)

        screen.blit(fonts.body_bold.render(
            "Tehtäväpäiväkirja", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (rect.x + 20, rect.y + 14))

        # Filter chips
        self.btn_filter_all.rect.x = rect.x + 200
        self.btn_filter_all.rect.y = rect.y + 18
        self.btn_filter_active.rect.x = rect.x + 295
        self.btn_filter_active.rect.y = rect.y + 18
        self.btn_filter_done.rect.x = rect.x + 400
        self.btn_filter_done.rect.y = rect.y + 18
        for btn, key in ((self.btn_filter_all, "all"),
                            (self.btn_filter_active, "active"),
                            (self.btn_filter_done, "completed")):
            tint = (COLORS.get("accent", (110, 130, 220))
                     if self.status_filter == key
                     else COLORS.get("panel", (60, 60, 80)))
            btn.color = tint
            btn.draw(screen, mp)

        self.btn_close.rect.x = rect.right - 100
        self.btn_close.rect.y = rect.y + 14
        self.btn_close.draw(screen, mp)

        # Two columns
        left = pygame.Rect(rect.x + 16, rect.y + 56, 340,
                            rect.height - 80)
        right = pygame.Rect(left.right + 16, rect.y + 56,
                             rect.right - left.right - 32,
                             rect.height - 80)
        self._draw_list(screen, left, mp)
        self._draw_detail(screen, right, mp)

    # ----- list --------------------------------------------------------
    def _draw_list(self, screen, area, mp) -> None:
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        self._list_rects = []
        prev_clip = screen.get_clip()
        screen.set_clip(area)
        y = area.y + 8 - self.scroll_list
        for q in self._filtered_quests():
            row = pygame.Rect(area.x + 6, y, area.width - 12,
                               self.LIST_ROW_H)
            is_sel = (q.id == self.selected_quest_id)
            is_hov = row.collidepoint(mp)
            bg = (COLORS.get("accent", (110, 130, 220))
                   if is_sel
                   else COLORS.get("hover", (60, 60, 80))
                   if is_hov
                   else COLORS.get("panel_dark", (32, 32, 42)))
            pygame.draw.rect(screen, bg, row, border_radius=4)
            sw = pygame.Rect(row.x + 6, row.y + 6, 4, row.height - 12)
            pygame.draw.rect(screen, _PRI.get(q.priority,
                                                  (140, 140, 150)),
                              sw)
            screen.blit(fonts.body_bold.render(
                q.name, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 16, row.y + 4))
            stat_col, stat_lab = _STATUS.get(q.status,
                                                  ((140, 140, 150),
                                                   q.status))
            chip_w = fonts.tiny.size(stat_lab)[0] + 12
            chip = pygame.Rect(row.right - chip_w - 6,
                                 row.y + 6, chip_w, 16)
            pygame.draw.rect(screen, stat_col, chip, border_radius=8)
            screen.blit(fonts.tiny.render(
                stat_lab, True, (20, 20, 30)),
                (chip.x + 6, chip.y + 1))
            prog = ql.objective_progress(q)
            sub = f"{q.quest_type}"
            if prog:
                sub += f"  ·  obj {prog}"
            screen.blit(fonts.tiny.render(
                sub, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (row.x + 16, row.y + 22))
            screen.blit(fonts.tiny.render(
                ql.reward_summary(q), True,
                COLORS.get("text_dim", (180, 180, 190))),
                (row.x + 16, row.y + 36))
            self._list_rects.append((row, q.id))
            y += self.LIST_ROW_H + 4
        screen.set_clip(prev_clip)

    # ----- detail ------------------------------------------------------
    def _draw_detail(self, screen, area, mp) -> None:
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        q = self._selected_quest()
        if q is None:
            screen.blit(fonts.body.render(
                "Valitse tehtävä vasemmalta.", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (area.x + 16, area.y + 16))
            return

        self._chip_rects = []
        prev_clip = screen.get_clip()
        screen.set_clip(area)
        y = area.y + 12 - self.scroll_detail

        # Title + status
        screen.blit(fonts.body_bold.render(
            q.name, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (area.x + 16, y))
        y += 24
        stat_col, stat_lab = _STATUS.get(q.status,
                                              ((140, 140, 150), q.status))
        chip = pygame.Rect(area.x + 16, y, 110, 20)
        pygame.draw.rect(screen, stat_col, chip, border_radius=10)
        screen.blit(fonts.tiny.render(stat_lab, True, (20, 20, 30)),
                      (chip.x + 8, chip.y + 3))
        # Reward summary + action toolbar
        screen.blit(fonts.small.render(
            f"Palkkio: {ql.reward_summary(q)}", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (area.x + 140, y + 1))
        y += 30

        # Description
        if q.description:
            y = self._draw_wrapped_text(
                screen, q.description, area.x + 16, y,
                area.width - 32)
            y += 6

        # Linked entities (NPC chips, shop chips, monster chips, location chips)
        y = self._draw_link_row(screen, area, y, "Antoi:",
                                  [("npc", q.giver_npc_id)] if q.giver_npc_id else [],
                                  mp)
        if q.turn_in_npc_id and q.turn_in_npc_id != q.giver_npc_id:
            y = self._draw_link_row(screen, area, y, "Palauta:",
                                      [("npc", q.turn_in_npc_id)], mp)
        if q.npc_ids:
            y = self._draw_link_row(screen, area, y, "Liittyy NPC:",
                                      [("npc", nid) for nid in q.npc_ids], mp)
        if q.shop_ids:
            y = self._draw_link_row(screen, area, y, "Kaupat:",
                                      [("shop", sid) for sid in q.shop_ids], mp)
        if q.location_ids or q.map_pin_location_id:
            locs = list(q.location_ids or [])
            if q.map_pin_location_id and q.map_pin_location_id not in locs:
                locs.insert(0, q.map_pin_location_id)
            y = self._draw_link_row(screen, area, y, "Paikat:",
                                      [("location", lid) for lid in locs], mp)
        if q.monster_names:
            y = self._draw_link_row(screen, area, y, "Hirviöt:",
                                      [("monster", nm) for nm in q.monster_names],
                                      mp)

        # Objectives
        if q.objectives:
            y += 6
            screen.blit(fonts.small_bold.render(
                f"Tavoitteet ({ql.objective_progress(q)})", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (area.x + 16, y))
            y += 20
            for o in q.objectives:
                mark = "☑" if o.completed else "☐"
                screen.blit(fonts.small.render(
                    f"{mark}  {o.description}", True,
                    COLORS.get("text_main", (220, 220, 230))),
                    (area.x + 24, y))
                y += 20

        # Log
        if q.log:
            y += 6
            mv = ql.gold_movements(q)
            screen.blit(fonts.small_bold.render(
                f"Loki ({len(q.log)})  "
                f"·  saatu {_gp(mv['received'])}, "
                f"maksettu {_gp(-mv['paid'])}, "
                f"netto {_gp(mv['net'])}",
                True,
                COLORS.get("text_bright", (240, 240, 250))),
                (area.x + 16, y))
            y += 22
            for e in q.log[-30:]:
                col = _LOG_KIND.get(e.kind, (140, 140, 150))
                pip = pygame.Rect(area.x + 16, y + 6, 6, 6)
                pygame.draw.rect(screen, col, pip, border_radius=3)
                screen.blit(fonts.tiny.render(
                    e.timestamp, True,
                    COLORS.get("text_dim", (170, 170, 180))),
                    (area.x + 28, y))
                screen.blit(fonts.small.render(
                    e.description, True,
                    COLORS.get("text_main", (220, 220, 230))),
                    (area.x + 90, y))
                y += 18

        # Action toolbar
        if y < area.bottom - 60:
            self.btn_complete.rect.x = area.x + 16
            self.btn_complete.rect.y = area.bottom - 40
            self.btn_complete.draw(screen, mp)
            self.btn_fail.rect.x = area.x + 176
            self.btn_fail.rect.y = area.bottom - 40
            self.btn_fail.draw(screen, mp)
        screen.set_clip(prev_clip)

    # ----- chip helpers -----------------------------------------------
    def _draw_link_row(self, screen, area, y, label, chips, mp):
        if not chips:
            return y
        screen.blit(fonts.small_bold.render(
            label, True,
            COLORS.get("text_dim", (180, 180, 190))),
            (area.x + 16, y))
        x = area.x + 100
        for kind, oid in chips:
            text = self._chip_label(kind, oid)
            cw = fonts.tiny.size(text)[0] + 14
            chip = pygame.Rect(x, y, cw, 18)
            col = self._chip_color(kind)
            pygame.draw.rect(screen, col, chip, border_radius=9)
            if chip.collidepoint(mp):
                pygame.draw.rect(screen, (255, 255, 255), chip, 1,
                                  border_radius=9)
            screen.blit(fonts.tiny.render(text, True, (20, 20, 30)),
                          (chip.x + 7, chip.y + 2))
            self._chip_rects.append((chip, kind, oid))
            x += cw + 6
            if x > area.right - 30:
                x = area.x + 100
                y += 22
        return y + 24

    def _chip_color(self, kind):
        if kind == "npc":
            return COLORS.get("player", (110, 180, 240))
        if kind == "shop":
            return COLORS.get("legendary", (170, 110, 220))
        if kind == "location":
            return COLORS.get("accent", (140, 200, 150))
        if kind == "monster":
            return COLORS.get("danger", (220, 100, 90))
        return (140, 140, 150)

    def _chip_label(self, kind, oid) -> str:
        if not self.world:
            return oid
        if kind == "npc":
            n = self.world.npcs.get(oid)
            return n.name if n is not None else oid
        if kind == "shop":
            s = self.world.shops.get(oid)
            return s.name if s is not None else oid
        if kind == "location":
            l = self.world.locations.get(oid)
            return l.name if l is not None else oid
        return oid

    def _draw_wrapped_text(self, screen, text, x, y, w):
        font = fonts.small
        line_h = font.get_height() + 2
        words = text.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if font.size(test)[0] <= w:
                line = test
            else:
                screen.blit(font.render(line, True,
                                          COLORS.get("text_main",
                                                       (220, 220, 230))),
                              (x, y))
                y += line_h
                line = word
        if line:
            screen.blit(font.render(line, True,
                                      COLORS.get("text_main",
                                                   (220, 220, 230))),
                          (x, y))
            y += line_h
        return y
