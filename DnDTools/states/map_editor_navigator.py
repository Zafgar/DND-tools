"""
Kingdoms navigator panel for MapEditorState.

Drop-in replacement for the detail panel when the DM clicks "Kuningaskunnat".
Renders a collapsible tree:

    [Tarmaas]           (click header to expand/collapse)
      Frand  (pääkaupunki)       → Avaa kartta
        Hallitsijat (3)           ▸
        Uskonnolliset (1)
        Sepät (2)
        ...
      [+ Lisää kaupunki]

plus a search bar at the top that replaces the tree with name/occupation/
faction hits across the whole World.

The panel is *stateless* between frames aside from the expand-set; all data
comes from `state.campaign` + `state.world` and is always read fresh so the
DM sees new NPCs/cities immediately.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pygame

from settings import COLORS
from ui.components import fonts
from data.kingdoms import (
    NPC_ROLE_CATEGORIES, KingdomEntry, CityEntry,
    ensure_kingdoms_on_campaign, group_npcs_by_role, search_world_npcs,
    sync_kingdoms_to_campaign,
)


ROW_H = 22
HEADER_H = 28
INDENT = 14


class KingdomsNavigator:
    """Owned by MapEditorState; rendered in place of the detail panel."""

    def __init__(self, state):
        self.state = state
        self._expanded_kingdoms: set = set()
        self._expanded_cities: set = set()   # (kingdom_key, city_key)
        self._expanded_roles: set = set()    # (kingdom_key, city_key, role_key)
        self.search: str = ""
        self.search_active: bool = False
        self._hit_rects: List[Tuple[pygame.Rect, str, tuple]] = []
        self._scroll: int = 0
        self._content_h: int = 0

    # ------------------------------------------------------------------
    # Lifecycle — called from map_editor_tools.route_events
    # ------------------------------------------------------------------
    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Return True if the event was consumed."""
        rect = self.state.detail_panel_rect

        # Search-box focus state
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if not rect.collidepoint(ev.pos):
                self.search_active = False
                return False
            # Inside panel: consume all clicks
            self._handle_click(ev.pos)
            return True

        if ev.type == pygame.MOUSEWHEEL and rect.collidepoint(pygame.mouse.get_pos()):
            self._scroll = max(
                0, min(self._scroll - ev.y * 30,
                       max(0, self._content_h - rect.height + 40))
            )
            return True

        if ev.type == pygame.KEYDOWN and self.search_active:
            if ev.key == pygame.K_BACKSPACE:
                self.search = self.search[:-1]
            elif ev.key == pygame.K_RETURN:
                self.search_active = False
            elif ev.key == pygame.K_ESCAPE:
                self.search = ""
                self.search_active = False
            elif ev.unicode and ev.unicode.isprintable():
                self.search += ev.unicode
            return True

        return False

    # ------------------------------------------------------------------
    # Click dispatch
    # ------------------------------------------------------------------
    def _handle_click(self, pos) -> None:
        # Search box?
        rect = self.state.detail_panel_rect
        sb = pygame.Rect(rect.x + 10, rect.y + 8, rect.width - 20, 28)
        if sb.collidepoint(pos):
            self.search_active = True
            return
        self.search_active = False

        # Iterate drawn row targets
        for r, action, payload in self._hit_rects:
            if r.collidepoint(pos):
                self._invoke(action, payload)
                return

    def _invoke(self, action: str, payload: tuple) -> None:
        st = self.state
        if action == "toggle_kingdom":
            (kkey,) = payload
            if kkey in self._expanded_kingdoms:
                self._expanded_kingdoms.discard(kkey)
            else:
                self._expanded_kingdoms.add(kkey)
        elif action == "toggle_city":
            key = payload
            if key in self._expanded_cities:
                self._expanded_cities.discard(key)
            else:
                self._expanded_cities.add(key)
        elif action == "toggle_role":
            key = payload
            if key in self._expanded_roles:
                self._expanded_roles.discard(key)
            else:
                self._expanded_roles.add(key)
        elif action == "open_city_map":
            (map_id,) = payload
            st._switch_to_map_by_id(map_id, push_history=True)
        elif action == "bind_city_here":
            # Record that the currently-open map is the city's drill-down map.
            (kkey, ckey) = payload
            self._bind_city_to_current_map(kkey, ckey)
        elif action == "focus_npc":
            (npc_id,) = payload
            cb = st.callbacks.get("open_npc")
            if cb:
                cb(npc_id)
            else:
                st._set_status(f"NPC: {npc_id}")
        elif action == "focus_location":
            (loc_id,) = payload
            cb = st.callbacks.get("open_location")
            if cb:
                cb(loc_id)

    def _bind_city_to_current_map(self, kingdom_key: str, city_key: str) -> None:
        st = self.state
        if st.campaign is None:
            return
        kingdoms = ensure_kingdoms_on_campaign(st.campaign)
        for k in kingdoms:
            if k.key != kingdom_key:
                continue
            for c in k.cities:
                if c.key == city_key:
                    c.map_id = st.world_map.id
                    sync_kingdoms_to_campaign(st.campaign)
                    st._set_status(
                        f"Kaupunki '{c.name}' linkitetty karttaan "
                        f"'{st.world_map.name}'"
                    )
                    return

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        rect = self.state.detail_panel_rect
        pygame.draw.rect(screen, COLORS["panel_dark"], rect)
        pygame.draw.line(screen, COLORS["border"],
                         (rect.x, rect.y), (rect.x, rect.bottom))

        self._hit_rects = []
        self._draw_search_box(screen)

        body_top = rect.y + 44
        body_rect = pygame.Rect(rect.x, body_top,
                                rect.width, rect.bottom - body_top)
        screen.set_clip(body_rect)

        y = body_top - self._scroll
        if self.search.strip():
            y = self._draw_search_results(screen, y)
        else:
            y = self._draw_tree(screen, y)
        self._content_h = (y + self._scroll) - body_top

        screen.set_clip(None)

        # Hint footer
        hint = fonts.tiny.render(
            "Klikkaa kaupunkia avataksesi sen kartan.",
            True, COLORS["text_dim"])
        screen.blit(hint, (rect.x + 10, rect.bottom - 20))

    # ------------------------------------------------------------------
    def _draw_search_box(self, screen) -> None:
        rect = self.state.detail_panel_rect
        sb = pygame.Rect(rect.x + 10, rect.y + 8, rect.width - 20, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], sb, border_radius=4)
        border = COLORS["input_focus"] if self.search_active else COLORS["input_border"]
        pygame.draw.rect(screen, border, sb, 1, border_radius=4)
        placeholder = self.search or ("Etsi NPC…" if not self.search_active else "")
        col = COLORS["text_bright"] if self.search else COLORS["text_dim"]
        t = fonts.small.render(placeholder, True, col)
        screen.blit(t, (sb.x + 8, sb.y + 6))

    # ------------------------------------------------------------------
    def _draw_tree(self, screen, y) -> int:
        rect = self.state.detail_panel_rect
        st = self.state
        x = rect.x + 12
        w = rect.width - 24

        if st.campaign is None:
            s = fonts.small.render("Ei aktiivista kampanjaa.",
                                   True, COLORS["text_dim"])
            screen.blit(s, (x, y))
            return y + 20

        kingdoms = ensure_kingdoms_on_campaign(st.campaign)
        for k in kingdoms:
            y = self._draw_kingdom(screen, k, x, y, w)
        return y

    def _draw_kingdom(self, screen, k: KingdomEntry, x, y, w) -> int:
        expanded = k.key in self._expanded_kingdoms
        header = pygame.Rect(x, y, w, HEADER_H)
        bg = COLORS["accent_dim"] if expanded else COLORS["panel"]
        pygame.draw.rect(screen, bg, header, border_radius=4)
        caret = "▾" if expanded else "▸"
        t = fonts.small_bold.render(
            f"{caret}  {k.name}   ({len(k.cities)} kaupunkia)",
            True, COLORS["text_bright"])
        screen.blit(t, (header.x + 6, header.y + 6))
        self._hit_rects.append((header, "toggle_kingdom", (k.key,)))
        y += HEADER_H + 2

        if expanded:
            for c in k.cities:
                y = self._draw_city(screen, k, c, x + INDENT, y, w - INDENT)
            # "+ Add city" row could go here, via a callback in future revs.
        return y + 4

    def _draw_city(self, screen, k: KingdomEntry, c: CityEntry,
                   x, y, w) -> int:
        city_key = (k.key, c.key)
        expanded = city_key in self._expanded_cities
        row = pygame.Rect(x, y, w, ROW_H)
        pygame.draw.rect(screen, COLORS["panel"], row, border_radius=3)
        caret = "▾" if expanded else "▸"
        star  = " ★" if c.is_capital else ""
        t = fonts.small.render(f"{caret}  {c.name}{star}",
                               True, COLORS["text_main"])
        screen.blit(t, (row.x + 6, row.y + 3))
        self._hit_rects.append((row, "toggle_city", city_key))

        # Right-side buttons: "Avaa" / "Linkitä tähän"
        btn_w = 74
        gap = 4
        btn_y = y + 1
        if c.map_id:
            open_r = pygame.Rect(row.right - btn_w - 6, btn_y, btn_w, ROW_H - 2)
            pygame.draw.rect(screen, COLORS["success"], open_r, border_radius=3)
            tt = fonts.tiny.render("Avaa kartta", True, COLORS["text_bright"])
            screen.blit(tt, tt.get_rect(center=open_r.center))
            self._hit_rects.append((open_r, "open_city_map", (c.map_id,)))
        else:
            bind_r = pygame.Rect(row.right - btn_w - 6, btn_y, btn_w, ROW_H - 2)
            pygame.draw.rect(screen, COLORS["panel_light"], bind_r, border_radius=3)
            pygame.draw.rect(screen, COLORS["border"], bind_r, 1, border_radius=3)
            tt = fonts.tiny.render("Linkitä tähän", True, COLORS["text_bright"])
            screen.blit(tt, tt.get_rect(center=bind_r.center))
            self._hit_rects.append((bind_r, "bind_city_here", (k.key, c.key)))

        y += ROW_H + 2

        if expanded:
            y = self._draw_city_roles(screen, k, c, x + INDENT, y,
                                      w - INDENT)
        return y

    def _draw_city_roles(self, screen, k: KingdomEntry, c: CityEntry,
                         x, y, w) -> int:
        st = self.state
        if st.world is None or not c.location_id:
            s = fonts.tiny.render(
                "Linkitä kaupunki Worldin paikkaan nähdäksesi NPC:t.",
                True, COLORS["text_dim"])
            screen.blit(s, (x, y))
            return y + 16

        groups = group_npcs_by_role(st.world, c.location_id)
        for cat in NPC_ROLE_CATEGORIES:
            key  = cat["key"]
            label = cat["label"]
            npcs = groups.get(key, [])
            role_key = (k.key, c.key, key)
            expanded = role_key in self._expanded_roles
            row = pygame.Rect(x, y, w, ROW_H - 2)
            bg = COLORS["panel"] if not expanded else COLORS["panel_light"]
            pygame.draw.rect(screen, bg, row, border_radius=2)
            caret = "▾" if expanded else "▸"
            t = fonts.tiny.render(f"{caret} {label}  ({len(npcs)})",
                                  True, COLORS["text_main"])
            screen.blit(t, (row.x + 6, row.y + 3))
            self._hit_rects.append((row, "toggle_role", role_key))
            y += ROW_H
            if expanded:
                for npc in npcs:
                    y = self._draw_npc_row(screen, npc, x + INDENT, y,
                                           w - INDENT)
        return y

    def _draw_npc_row(self, screen, npc, x, y, w) -> int:
        row = pygame.Rect(x, y, w, ROW_H - 4)
        pygame.draw.rect(screen, (26, 30, 38), row, border_radius=2)
        name = npc.name
        sub  = npc.occupation or npc.title or ""
        disp = f"• {name}" + (f" — {sub}" if sub else "")
        disp = disp[:42]
        t = fonts.tiny.render(disp, True, COLORS["text_main"])
        screen.blit(t, (row.x + 6, row.y + 2))
        npc_id = getattr(npc, "id", "") or name
        self._hit_rects.append((row, "focus_npc", (npc_id,)))
        return y + ROW_H - 2

    # ------------------------------------------------------------------
    def _draw_search_results(self, screen, y) -> int:
        rect = self.state.detail_panel_rect
        st = self.state
        x = rect.x + 12
        w = rect.width - 24
        if st.world is None:
            return y
        results = search_world_npcs(st.world, self.search, limit=80)
        hdr = fonts.small_bold.render(
            f"Haku: {self.search}  ({len(results)})",
            True, COLORS["text_dim"])
        screen.blit(hdr, (x, y))
        y += 20
        for npc in results:
            row = pygame.Rect(x, y, w, ROW_H)
            pygame.draw.rect(screen, COLORS["panel"], row, border_radius=3)
            disp = f"{npc.name} — {npc.occupation or npc.title or '-'}"
            disp = disp[:44]
            t = fonts.small.render(disp, True, COLORS["text_main"])
            screen.blit(t, (row.x + 6, row.y + 3))
            npc_id = getattr(npc, "id", "") or npc.name
            self._hit_rects.append((row, "focus_npc", (npc_id,)))
            y += ROW_H + 2
        return y
