"""Lore Codex -selain — maailmanlore löydettävissä sekunneissa.

Kaksi palstaa: vasemmalla hakukenttä + kategoriapainikkeet + osumalista,
oikealla koko artikkeli luettavana leipätekstinä.  Artikkelin alaosassa
ovat ristiviittaukset (``see_also``) sekä NPC- ja paikkalinkit, joista
pelinjohtaja pääsee suoraan hahmon lehdelle tai paikan tietoihin.

Käyttö pöydässä:
  * kirjoita → haku suodattuu heti (nimet, hakusanat, leipäteksti)
  * klikkaa kategoriaa → vain sen artikkelit
  * klikkaa osumaa → artikkeli auki oikealle
  * ESC → sulkee (tai tyhjentää haun jos hakukenttä ei ole tyhjä)
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import lore_codex as codex


class LoreCodexModal:
    """Searchable browser over :mod:`data.lore_codex`."""

    WIDTH = min(1240, SCREEN_WIDTH - 60)
    HEIGHT = min(760, SCREEN_HEIGHT - 60)
    LIST_W = 380
    ROW_H = 52

    def __init__(self, world=None, campaign=None, *,
                 on_close: Optional[Callable[[], None]] = None,
                 on_open_npc: Optional[Callable[[str], None]] = None,
                 on_open_location: Optional[Callable[[str], None]] = None):
        self.world = world
        self.campaign = campaign
        self.on_close = on_close
        self.on_open_npc = on_open_npc
        self.on_open_location = on_open_location

        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.query = ""
        self.field_active = True
        self.filter_category = ""
        self.show_spoilers = True
        self.selected_key = ""
        self.list_scroll = 0
        self.body_scroll = 0

        # Per-frame hit rects
        self._row_rects: List[Tuple[pygame.Rect, str]] = []
        self._cat_rects: List[Tuple[pygame.Rect, str]] = []
        self._see_rects: List[Tuple[pygame.Rect, str]] = []
        self._npc_rects: List[Tuple[pygame.Rect, str]] = []
        self._loc_rects: List[Tuple[pygame.Rect, str]] = []
        self._query_rect: Optional[pygame.Rect] = None
        self._body_rect: Optional[pygame.Rect] = None
        self._body_height = 0

        self.btn_close = Button(0, 0, 90, 28, "Sulje", self._close,
                                color=COLORS.get("panel", (60, 60, 80)))
        self.btn_clear = Button(0, 0, 86, 24, "Tyhjennä", self._clear,
                                color=COLORS.get("panel_dark", (40, 40, 56)),
                                font=fonts.tiny)
        self.btn_spoiler = Button(0, 0, 160, 24, "Spoilerit: näkyvät",
                                  self._toggle_spoilers,
                                  color=COLORS.get("warning", (220, 180, 80)),
                                  font=fonts.tiny)

    # ------------------------------------------------------------------ #
    def open(self, entry_key: str = "", query: str = ""):
        """Open the codex.  ``entry_key`` jumps straight to an article
        (used by the "miksi tärkeä" links on NPC/location sheets)."""
        self.is_open = True
        self.list_scroll = 0
        self.body_scroll = 0
        self.field_active = not entry_key
        if query:
            self.query = query
        if entry_key and codex.get_entry(entry_key):
            self.selected_key = entry_key
            self.filter_category = ""
            self.query = ""
        elif not self.selected_key:
            hits = self._hits()
            self.selected_key = hits[0].key if hits else ""

    def _close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _clear(self):
        self.query = ""
        self.filter_category = ""
        self.list_scroll = 0

    def _toggle_spoilers(self):
        self.show_spoilers = not self.show_spoilers
        self.btn_spoiler.text = ("Spoilerit: näkyvät" if self.show_spoilers
                                 else "Spoilerit: piilossa")
        if not self.show_spoilers:
            entry = self.entry()
            if entry is not None and entry.spoiler:
                self.selected_key = ""

    # ------------------------------------------------------------------ #
    def _hits(self) -> List:
        out = codex.search(self.query, category=self.filter_category)
        if not self.show_spoilers:
            out = [e for e in out if not e.spoiler]
        return out

    def entry(self):
        """Currently selected article (or the first hit)."""
        e = codex.get_entry(self.selected_key) if self.selected_key else None
        if e is not None and (self.show_spoilers or not e.spoiler):
            return e
        hits = self._hits()
        return hits[0] if hits else None

    def select(self, key: str):
        if codex.get_entry(key) is None:
            return False
        self.selected_key = key
        self.body_scroll = 0
        return True

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.query or self.filter_category:
                    self._clear()
                else:
                    self._close()
                return True
            if event.key == pygame.K_DOWN or event.key == pygame.K_UP:
                hits = self._hits()
                if hits:
                    keys = [e.key for e in hits]
                    try:
                        i = keys.index(self.selected_key)
                    except ValueError:
                        i = -1
                    step = 1 if event.key == pygame.K_DOWN else -1
                    self.select(keys[(i + step) % len(keys)])
                return True
            if self.field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.query = self.query[:-1]
                    self.list_scroll = 0
                    return True
                if event.unicode and event.unicode.isprintable():
                    if len(self.query) < 60:
                        self.query += event.unicode
                        self.list_scroll = 0
                    return True
            return True
        if event.type == pygame.MOUSEWHEEL:
            mp = pygame.mouse.get_pos()
            if self._body_rect and self._body_rect.collidepoint(mp):
                max_scroll = max(0, self._body_height
                                 - self._body_rect.height + 40)
                self.body_scroll = max(
                    0, min(max_scroll, self.body_scroll - event.y * 40))
            else:
                self.list_scroll = max(0, self.list_scroll - event.y * 40)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_clear, self.btn_spoiler):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            if self._query_rect:
                self.field_active = self._query_rect.collidepoint(event.pos)
            for rect, cat in self._cat_rects:
                if rect.collidepoint(event.pos):
                    self.filter_category = ("" if self.filter_category == cat
                                            else cat)
                    self.list_scroll = 0
                    return True
            for rect, key in self._row_rects:
                if rect.collidepoint(event.pos):
                    self.select(key)
                    return True
            for rect, key in self._see_rects:
                if rect.collidepoint(event.pos):
                    self.select(key)
                    return True
            for rect, npc_id in self._npc_rects:
                if rect.collidepoint(event.pos):
                    if self.on_open_npc:
                        self.on_open_npc(npc_id)
                    return True
            for rect, loc_id in self._loc_rects:
                if rect.collidepoint(event.pos):
                    if self.on_open_location:
                        self.on_open_location(loc_id)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def _wrap(self, text: str, max_width: int, font=None) -> List[str]:
        font = font or fonts.small
        lines: List[str] = []
        for para in (text or "").split("\n"):
            if not para.strip():
                lines.append("")
                continue
            cur = ""
            for w in para.split():
                test = (cur + " " + w).strip()
                if font.size(test)[0] <= max_width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
        return lines

    def _npc_name(self, npc_id: str) -> str:
        if self.world and getattr(self.world, "npcs", None):
            n = self.world.npcs.get(npc_id)
            if n is not None:
                return n.name
        return npc_id

    def _loc_name(self, loc_id: str) -> str:
        if self.world and getattr(self.world, "locations", None):
            l = self.world.locations.get(loc_id)
            if l is not None:
                return l.name
        return loc_id

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (22, 22, 30)),
                         rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light", (130, 130, 160)),
                         rect, 2, border_radius=10)

        self._row_rects = []
        self._cat_rects = []
        self._see_rects = []
        self._npc_rects = []
        self._loc_rects = []

        hits = self._hits()
        screen.blit(fonts.body_bold.render(
            f"Lore-Codex — {len(codex.all_entries())} artikkelia",
            True, COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, self.y + 14))
        self.btn_close.rect.topleft = (rect.right - 110, self.y + 12)
        self.btn_close.draw(screen, mp)
        self.btn_spoiler.rect.topleft = (rect.right - 280, self.y + 16)
        self.btn_spoiler.draw(screen, mp)

        self._draw_search(screen, mp)
        self._draw_list(screen, mp, hits)
        self._draw_article(screen, mp)

    # ------------------------------------------------------------------ #
    def _draw_search(self, screen, mp):
        qf = pygame.Rect(self.x + 20, self.y + 48, self.LIST_W - 4, 30)
        self._query_rect = qf
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                         qf, border_radius=4)
        pygame.draw.rect(screen,
                         COLORS.get("accent", (180, 180, 240))
                         if self.field_active
                         else COLORS.get("border", (80, 80, 100)),
                         qf, 1, border_radius=4)
        cursor = ("|" if self.field_active
                  and pygame.time.get_ticks() // 400 % 2 == 0 else "")
        if self.query:
            txt, col = self.query + cursor, COLORS.get("text_bright",
                                                       (240, 240, 250))
        else:
            txt = (cursor or "hae: garrutha, veru, clavise, kupu…")
            col = COLORS.get("text_muted", (140, 140, 150))
        screen.blit(fonts.small.render(txt, True, col), (qf.x + 8, qf.y + 6))
        self.btn_clear.rect.topleft = (qf.right - 92, qf.y + 3)
        self.btn_clear.draw(screen, mp)

        # Category chips (wrap into as many rows as needed)
        x, y = self.x + 20, self.y + 84
        row_right = self.x + 20 + self.LIST_W - 4
        for cat in [""] + codex.categories():
            label = cat.capitalize() if cat else "Kaikki"
            w = fonts.tiny.size(label)[0] + 16
            if x + w > row_right:
                x = self.x + 20
                y += 24
            chip = pygame.Rect(x, y, w, 21)
            active = (self.filter_category == cat)
            pygame.draw.rect(screen,
                             COLORS.get("accent", (110, 130, 220)) if active
                             else COLORS.get("panel_dark", (40, 40, 56)),
                             chip, border_radius=10)
            screen.blit(fonts.tiny.render(
                label, True, (20, 20, 30) if active
                else COLORS.get("text_main", (220, 220, 235))),
                (chip.x + 8, chip.y + 3))
            self._cat_rects.append((chip, cat))
            x += w + 4
        self._list_top = y + 30

    # ------------------------------------------------------------------ #
    def _draw_list(self, screen, mp, hits):
        top = getattr(self, "_list_top", self.y + 140)
        list_rect = pygame.Rect(self.x + 16, top, self.LIST_W,
                                self.y + self.HEIGHT - 20 - top)
        pygame.draw.rect(screen, COLORS.get("panel_dark", (30, 30, 40)),
                         list_rect, border_radius=6)
        prev = screen.get_clip()
        screen.set_clip(list_rect)
        y = top + 6 - self.list_scroll
        sel = self.entry()
        sel_key = sel.key if sel else ""
        for e in hits:
            row = pygame.Rect(list_rect.x + 6, y, list_rect.width - 12,
                              self.ROW_H)
            active = (e.key == sel_key)
            pygame.draw.rect(screen,
                             COLORS.get("accent", (110, 130, 220)) if active
                             else (COLORS.get("hover", (52, 52, 68))
                                   if row.collidepoint(mp)
                                   else COLORS.get("panel", (40, 40, 54))),
                             row, border_radius=4)
            title = e.title
            while (fonts.small_bold.size(title)[0] > row.width - 20
                   and len(title) > 4):
                title = title[:-2]
            screen.blit(fonts.small_bold.render(
                title, True, (20, 20, 30) if active
                else COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 8, row.y + 5))
            tag = e.category.upper() + ("  ·  SPOILER" if e.spoiler else "")
            screen.blit(fonts.tiny.render(
                tag, True, (40, 40, 50) if active
                else COLORS.get("text_muted", (150, 150, 165))),
                (row.x + 8, row.y + 26))
            self._row_rects.append((row, e.key))
            y += self.ROW_H + 4
        if not hits:
            screen.blit(fonts.small.render(
                "(Ei osumia.)", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (list_rect.x + 14, top + 14))
        screen.set_clip(prev)

    # ------------------------------------------------------------------ #
    def _draw_article(self, screen, mp):
        left = self.x + 16 + self.LIST_W + 14
        top = self.y + 48
        body_rect = pygame.Rect(left, top,
                                self.x + self.WIDTH - 20 - left,
                                self.y + self.HEIGHT - 20 - top)
        self._body_rect = body_rect
        pygame.draw.rect(screen, COLORS.get("panel_dark", (30, 30, 40)),
                         body_rect, border_radius=6)
        e = self.entry()
        if e is None:
            screen.blit(fonts.small.render(
                "Valitse artikkeli vasemmalta.", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (body_rect.x + 16, body_rect.y + 16))
            self._body_height = 0
            return

        prev = screen.get_clip()
        screen.set_clip(body_rect)
        wrap_w = body_rect.width - 40
        y = body_rect.y + 14 - self.body_scroll
        x = body_rect.x + 18

        screen.blit(fonts.body_bold.render(
            e.title, True, COLORS.get("text_bright", (240, 240, 250))),
            (x, y))
        y += 28
        meta = e.category.upper()
        if e.spoiler:
            meta += "   ·   SPOILER — älä näytä pelaajille"
        screen.blit(fonts.tiny.render(
            meta, True, COLORS.get("warning", (220, 180, 80)) if e.spoiler
            else COLORS.get("text_muted", (150, 150, 165))), (x, y))
        y += 22

        # Summary box — the "what the DM needs right now" line.
        sum_lines = self._wrap(e.summary, wrap_w - 20)
        box = pygame.Rect(x - 4, y, wrap_w + 8,
                          len(sum_lines) * 18 + 14)
        pygame.draw.rect(screen, COLORS.get("panel", (44, 44, 58)),
                         box, border_radius=5)
        pygame.draw.rect(screen, COLORS.get("accent", (110, 130, 220)),
                         box, 1, border_radius=5)
        sy = y + 7
        for line in sum_lines:
            screen.blit(fonts.small.render(
                line, True, COLORS.get("text_bright", (240, 240, 250))),
                (x + 6, sy))
            sy += 18
        y = box.bottom + 12

        for line in self._wrap(e.body, wrap_w):
            if line:
                screen.blit(fonts.small.render(
                    line, True, COLORS.get("text_main", (220, 220, 235))),
                    (x, y))
            y += 18

        y += 10
        y = self._draw_chip_row(screen, mp, x, y, wrap_w, "Liittyy:",
                                [(k, self._see_title(k)) for k in e.see_also],
                                self._see_rects,
                                COLORS.get("spell", (150, 120, 220)))
        y = self._draw_chip_row(screen, mp, x, y, wrap_w, "Hahmot:",
                                [(n, self._npc_name(n)) for n in e.npc_ids],
                                self._npc_rects,
                                COLORS.get("success", (90, 200, 120)))
        y = self._draw_chip_row(screen, mp, x, y, wrap_w, "Paikat:",
                                [(l, self._loc_name(l)) for l in e.location_ids],
                                self._loc_rects,
                                COLORS.get("warning", (220, 180, 80)))

        self._body_height = (y - (body_rect.y + 14 - self.body_scroll))
        screen.set_clip(prev)

    def _see_title(self, key: str) -> str:
        other = codex.get_entry(key)
        return other.title if other else key

    def _draw_chip_row(self, screen, mp, x, y, wrap_w, label, items,
                       sink, colour):
        if not items:
            return y
        screen.blit(fonts.small_bold.render(
            label, True, COLORS.get("text_dim", (180, 180, 195))), (x, y))
        y += 20
        cx = x
        for ident, name in items:
            w = fonts.tiny.size(name)[0] + 18
            if cx + w > x + wrap_w:
                cx = x
                y += 26
            chip = pygame.Rect(cx, y, w, 22)
            hot = chip.collidepoint(mp)
            pygame.draw.rect(screen, colour if hot
                             else COLORS.get("panel", (44, 44, 58)),
                             chip, border_radius=11)
            pygame.draw.rect(screen, colour, chip, 1, border_radius=11)
            screen.blit(fonts.tiny.render(
                name, True, (20, 20, 30) if hot
                else COLORS.get("text_main", (220, 220, 235))),
                (chip.x + 9, chip.y + 4))
            sink.append((chip, ident))
            cx += w + 5
        return y + 32
