"""
MapEditorState — pop-up modals for editing MapObjects.

Keep-it-simple editor: tab Enter to move between fields, click a field to
focus, Save to write back to the object. Not a full WYSIWYG dialog — just
fast keyboard-driven editing for label / hover / notes / links.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.map_engine import MapObject, MAP_OBJECT_TYPES


class _TextField:
    def __init__(self, label: str, value: str, multiline: bool = False,
                 allowed: str = ""):
        self.label = label
        self.value = str(value)
        self.multiline = multiline
        self.allowed = allowed   # if non-empty, restrict chars (e.g. "0123456789.")
        self.focused = False

    def key_event(self, ev: pygame.event.Event) -> None:
        if not self.focused:
            return
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        elif ev.key == pygame.K_RETURN:
            if self.multiline:
                self.value += "\n"
        elif ev.unicode and ev.unicode.isprintable():
            if self.allowed and ev.unicode not in self.allowed:
                return
            self.value += ev.unicode


class MapObjectEditModal:
    """Lightweight modal backing the right-click 'edit object' action.

    Fields:
        label, object_type, hover_info, notes,
        linked_location_id, linked_map_id, linked_npc_ids (comma-separated),
        linked_encounter_id, unit_count, unit_type, faction,
        treasure_gold, treasure_items (comma), trap_save, trap_damage,
        lockpick_dc, detect_dc,
        visible, dm_only, hidden.
    """
    W = 640
    H = 680

    def __init__(self, obj: MapObject, on_close: Callable[[], None]):
        self.obj = obj
        self.on_close = on_close
        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2
        self.rect = pygame.Rect(self.x, self.y, self.W, self.H)

        self.fields: List[Tuple[str, _TextField]] = [
            ("label",               _TextField("Nimi",          obj.label)),
            ("object_type",         _TextField("Tyyppi (avain)", obj.object_type)),
            ("hover_info",          _TextField("Hover-info",    obj.hover_info, multiline=True)),
            ("notes",               _TextField("DM-muistiinpanot", obj.notes, multiline=True)),
            ("linked_location_id",  _TextField("Linkki: Location id", obj.linked_location_id)),
            ("linked_map_id",       _TextField("Linkki: Map id", obj.linked_map_id)),
            ("linked_npc_ids",      _TextField("Linkki: NPC id:t (pilkuin)",
                                               ",".join(obj.linked_npc_ids))),
            ("linked_encounter_id", _TextField("Linkki: Encounter", obj.linked_encounter_id)),
            ("unit_count",          _TextField("Joukko: määrä", str(obj.unit_count),
                                               allowed="0123456789")),
            ("unit_type",           _TextField("Joukko: tyyppi", obj.unit_type)),
            ("faction",             _TextField("Fraktio", obj.faction)),
            ("treasure_gold",       _TextField("Aarre (gp)", str(obj.treasure_gold),
                                               allowed="0123456789.")),
            ("treasure_items",      _TextField("Aarre-esineet (pilkuin)",
                                               ",".join(obj.treasure_items))),
            ("trap_save",           _TextField("Ansa: save", obj.trap_save)),
            ("trap_damage",         _TextField("Ansa: vah", obj.trap_damage)),
            ("lockpick_dc",         _TextField("Tiirikka DC", str(obj.lockpick_dc),
                                               allowed="0123456789")),
            ("detect_dc",           _TextField("Havainto DC", str(obj.detect_dc),
                                               allowed="0123456789")),
            ("follow_path_id",      _TextField("Seuraa reittiä (path id)",
                                                obj.follow_path_id)),
            ("travel_speed_mult",   _TextField("Matkanopeuskerroin",
                                                str(obj.travel_speed_mult),
                                                allowed="0123456789.")),
            ("path_progress_miles", _TextField("Reittietappi (mailia)",
                                                str(obj.path_progress_miles),
                                                allowed="0123456789.")),
        ]
        self.flags = {
            "visible": obj.visible,
            "dm_only": obj.dm_only,
            "hidden":  obj.hidden,
        }
        self._field_rects: List[pygame.Rect] = []

        self.btn_save   = Button(self.x + self.W - 240, self.y + self.H - 50,
                                 110, 38, "Tallenna", self._save,
                                 color=COLORS["success"])
        self.btn_cancel = Button(self.x + self.W - 120, self.y + self.H - 50,
                                 100, 38, "Peruuta", self._cancel,
                                 color=COLORS["danger"])

    # ------------------------------------------------------------------
    def _save(self) -> None:
        o = self.obj
        for key, fld in self.fields:
            v = fld.value.strip() if not fld.multiline else fld.value
            if key == "linked_npc_ids":
                o.linked_npc_ids = [x.strip() for x in v.split(",") if x.strip()]
            elif key == "treasure_items":
                o.treasure_items = [x.strip() for x in v.split(",") if x.strip()]
            elif key in ("unit_count", "lockpick_dc", "detect_dc"):
                try:
                    setattr(o, key, int(v or 0))
                except ValueError:
                    pass
            elif key == "treasure_gold":
                try:
                    o.treasure_gold = float(v or 0)
                except ValueError:
                    pass
            elif key in ("travel_speed_mult", "path_progress_miles"):
                try:
                    setattr(o, key, float(v or 0))
                except ValueError:
                    pass
            elif key == "object_type":
                # Keep the existing icon/color/size if palette entry exists.
                if v and v != o.object_type:
                    o.object_type = v
                    proto = MAP_OBJECT_TYPES.get(v)
                    if proto:
                        o.icon  = proto["icon"]
                        o.color = proto["color"]
                        o.size  = proto["size"]
            else:
                setattr(o, key, v)

        o.visible = self.flags["visible"]
        o.dm_only = self.flags["dm_only"]
        o.hidden  = self.flags["hidden"]
        self.on_close()

    def _cancel(self) -> None:
        self.on_close()

    # ------------------------------------------------------------------
    def handle_event(self, ev: pygame.event.Event) -> None:
        # Keyboard
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._cancel()
            return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_TAB:
            self._focus_next()
            return

        # Mouse — focus field / toggle flag / buttons
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self._handle_mouse_down(ev.pos)

        # Delegate to focused field
        for _key, fld in self.fields:
            fld.key_event(ev)

        self.btn_save.handle_event(ev)
        self.btn_cancel.handle_event(ev)

    def _focus_next(self) -> None:
        idx = -1
        for i, (_, f) in enumerate(self.fields):
            if f.focused:
                idx = i
                f.focused = False
                break
        self.fields[(idx + 1) % len(self.fields)][1].focused = True

    def _handle_mouse_down(self, pos) -> None:
        for (_key, f), r in zip(self.fields, self._field_rects):
            f.focused = r.collidepoint(pos)
        # Flag chip row
        for name, r in self._flag_rects().items():
            if r.collidepoint(pos):
                self.flags[name] = not self.flags[name]

    # ------------------------------------------------------------------
    # Layout helpers used both by draw + hit-testing
    # ------------------------------------------------------------------
    def _flag_rects(self) -> dict:
        y = self.y + self.H - 90
        rects = {}
        x = self.x + 20
        for name in ("visible", "dm_only", "hidden"):
            r = pygame.Rect(x, y, 110, 28)
            rects[name] = r
            x += 120
        return rects

    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, COLORS["panel"], self.rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 2, border_radius=10)

        hdr = fonts.header.render("Muokkaa objektia", True, COLORS["text_bright"])
        screen.blit(hdr, (self.x + 16, self.y + 12))

        # Field rows — two-column layout for compactness
        self._field_rects = []
        start_y = self.y + 54
        col_w = (self.W - 40) // 2 - 8
        row_h = 46
        for i, (_key, fld) in enumerate(self.fields):
            col = i % 2
            row = i // 2
            fx = self.x + 20 + col * (col_w + 16)
            fy = start_y + row * row_h
            # Label
            lbl = fonts.tiny.render(fld.label, True, COLORS["text_dim"])
            screen.blit(lbl, (fx, fy))
            # Input box
            box = pygame.Rect(fx, fy + 14, col_w, 26)
            self._field_rects.append(box)
            pygame.draw.rect(
                screen,
                COLORS["input_bg"] if not fld.focused else (25, 30, 40),
                box, border_radius=4)
            pygame.draw.rect(
                screen,
                COLORS["input_focus"] if fld.focused else COLORS["input_border"],
                box, 1, border_radius=4)
            display = fld.value.replace("\n", " \\n ")
            if len(display) > 60:
                display = "…" + display[-59:]
            txt = fonts.small.render(display, True, COLORS["text_bright"])
            screen.blit(txt, (box.x + 6, box.y + 4))

        # Flag chips
        for name, r in self._flag_rects().items():
            active = self.flags[name]
            col = COLORS["accent_dim"] if active else COLORS["panel_dark"]
            pygame.draw.rect(screen, col, r, border_radius=14)
            pygame.draw.rect(screen, COLORS["border"], r, 1, border_radius=14)
            tx = fonts.small_bold.render(name, True, COLORS["text_bright"])
            screen.blit(tx, tx.get_rect(center=r.center))

        mp = pygame.mouse.get_pos()
        self.btn_save.draw(screen, mp)
        self.btn_cancel.draw(screen, mp)


class NPCDetailModal:
    """Read-only overview of an NPC — lore, combat sheet summary, inventory,
    relationships.  Opened from the navigator panel or a map token whose
    linked_npc_ids lists one or more NPCs.

    For N>1 linked NPCs the modal shows a quick picker list at the top; the
    DM can click one to switch focus.
    """
    W = 760
    H = 620

    def __init__(self, world, npc_ids, on_close):
        self.world = world
        self.npc_ids = [nid for nid in (npc_ids or []) if nid in world.npcs]
        if not self.npc_ids and world.npcs:
            # Tolerate name-style ids from kingdoms navigator
            for nid, npc in world.npcs.items():
                if npc.name in (npc_ids or []):
                    self.npc_ids.append(nid)
        self.on_close = on_close
        self.active_idx = 0
        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2
        self.rect = pygame.Rect(self.x, self.y, self.W, self.H)
        self.scroll = 0
        self._picker_rects = []
        self._section_rects = []
        self.active_tab = "lore"   # lore | combat | inventory | relations
        self.btn_close = Button(self.x + self.W - 110, self.y + self.H - 50,
                                 90, 38, "Sulje", self._close,
                                 color=COLORS["danger"])

    # ------------------------------------------------------------------
    @property
    def npc(self):
        if not self.npc_ids:
            return None
        nid = self.npc_ids[max(0, min(self.active_idx, len(self.npc_ids) - 1))]
        return self.world.npcs.get(nid)

    def _close(self):
        self.on_close()

    # ------------------------------------------------------------------
    def handle_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._close()
            return
        if ev.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.scroll = max(0, self.scroll - ev.y * 30)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self._picker_rects):
                if r.collidepoint(ev.pos):
                    self.active_idx = i
                    self.scroll = 0
                    return
            for name, r in self._section_rects:
                if r.collidepoint(ev.pos):
                    self.active_tab = name
                    self.scroll = 0
                    return
        self.btn_close.handle_event(ev)

    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, COLORS["panel"], self.rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 2, border_radius=12)

        npc = self.npc
        if npc is None:
            msg = fonts.header.render("NPC:tä ei löydy.", True, COLORS["text_bright"])
            screen.blit(msg, (self.x + 20, self.y + 20))
            self.btn_close.draw(screen, pygame.mouse.get_pos())
            return

        # Header — name + title/occupation
        hdr = fonts.large.render(npc.name, True, COLORS["text_bright"])
        screen.blit(hdr, (self.x + 20, self.y + 14))
        sub_parts = [p for p in (npc.title, npc.occupation, npc.race) if p]
        sub = fonts.small.render(" · ".join(sub_parts), True, COLORS["text_dim"])
        screen.blit(sub, (self.x + 20, self.y + 44))

        # Multi-NPC picker strip (if applicable)
        self._picker_rects = []
        if len(self.npc_ids) > 1:
            px = self.x + 20
            py = self.y + 68
            for i, nid in enumerate(self.npc_ids):
                n = self.world.npcs.get(nid)
                if not n:
                    continue
                label = n.name[:20]
                tw = fonts.tiny.size(label)[0] + 14
                r = pygame.Rect(px, py, tw, 22)
                active = (i == self.active_idx)
                pygame.draw.rect(screen, COLORS["accent_dim"] if active else COLORS["panel_dark"],
                                 r, border_radius=4)
                ts = fonts.tiny.render(label, True, COLORS["text_bright"])
                screen.blit(ts, (r.x + 7, r.y + 4))
                self._picker_rects.append(r)
                px += tw + 6
                if px > self.x + self.W - 40:
                    py += 24
                    px = self.x + 20

        # Tabs
        tab_y = self.y + 94 + (24 if len(self.npc_ids) > 1 else 0)
        tabs = [("lore", "Lore"), ("combat", "Taistelu"),
                ("inventory", "Varusteet"), ("relations", "Suhteet")]
        self._section_rects = []
        tx = self.x + 20
        for key, label in tabs:
            tw = fonts.small.size(label)[0] + 20
            r = pygame.Rect(tx, tab_y, tw, 26)
            active = (self.active_tab == key)
            pygame.draw.rect(screen, COLORS["accent"] if active else COLORS["panel_dark"],
                             r, border_radius=5)
            ts = fonts.small.render(label, True, COLORS["text_bright"])
            screen.blit(ts, ts.get_rect(center=r.center))
            self._section_rects.append((key, r))
            tx += tw + 6

        # Content body
        body_top = tab_y + 34
        body_rect = pygame.Rect(self.x + 12, body_top,
                                self.W - 24, self.H - (body_top - self.y) - 60)
        pygame.draw.rect(screen, COLORS["panel_dark"], body_rect, border_radius=6)
        screen.set_clip(body_rect)
        y = body_top + 10 - self.scroll
        x = body_rect.x + 12
        max_w = body_rect.width - 24

        if self.active_tab == "lore":
            y = self._draw_lore(screen, npc, x, y, max_w)
        elif self.active_tab == "combat":
            y = self._draw_combat(screen, npc, x, y, max_w)
        elif self.active_tab == "inventory":
            y = self._draw_inventory(screen, npc, x, y, max_w)
        elif self.active_tab == "relations":
            y = self._draw_relations(screen, npc, x, y, max_w)

        screen.set_clip(None)

        self.btn_close.draw(screen, pygame.mouse.get_pos())

    # ------------------------------------------------------------------
    def _kv(self, screen, label, value, x, y, max_w) -> int:
        if not value:
            return y
        l = fonts.small_bold.render(f"{label}:", True, COLORS["text_dim"])
        screen.blit(l, (x, y))
        y += 18
        return self._wrap(screen, str(value), x, y, max_w) + 6

    def _wrap(self, screen, text, x, y, max_w) -> int:
        font = fonts.small
        for para in text.split("\n"):
            line = ""
            for w in para.split():
                test = (line + " " + w).strip()
                if font.size(test)[0] > max_w and line:
                    screen.blit(font.render(line, True, COLORS["text_main"]), (x, y))
                    y += 18
                    line = w
                else:
                    line = test
            if line:
                screen.blit(font.render(line, True, COLORS["text_main"]), (x, y))
                y += 18
        return y

    # --- tab renderers ---
    def _draw_lore(self, screen, npc, x, y, max_w) -> int:
        y = self._kv(screen, "Fraktio", npc.faction, x, y, max_w)
        y = self._kv(screen, "Suuntautuminen", npc.alignment, x, y, max_w)
        y = self._kv(screen, "Asenne", npc.attitude, x, y, max_w)
        y = self._kv(screen, "Ikä / sukupuoli", f"{npc.age} {npc.gender}".strip(), x, y, max_w)
        y = self._kv(screen, "Ulkonäkö", npc.appearance, x, y, max_w)
        y = self._kv(screen, "Persoonallisuus", npc.personality, x, y, max_w)
        y = self._kv(screen, "Tausta", npc.backstory, x, y, max_w)
        y = self._kv(screen, "DM-muistiinpanot", npc.notes, x, y, max_w)
        if npc.tags:
            y = self._kv(screen, "Tagit", ", ".join(npc.tags), x, y, max_w)
        return y

    def _draw_combat(self, screen, npc, x, y, max_w) -> int:
        src = npc.stat_source or ""
        l = fonts.small_bold.render("Tilasto-lähde:", True, COLORS["text_dim"])
        screen.blit(l, (x, y)); y += 18
        val = src or "-"
        screen.blit(fonts.small.render(val, True, COLORS["text_main"]), (x, y))
        y += 24
        stats = None
        try:
            if src.startswith("monster:"):
                from data.library import library
                stats = library.get_monster(src.split(":", 1)[1])
        except Exception:
            stats = None
        if stats is not None:
            lines = [
                f"HP: {getattr(stats, 'hit_points', '-')}",
                f"AC: {getattr(stats, 'armor_class', '-')}",
                f"CR: {getattr(stats, 'challenge_rating', '-')}",
                f"Nopeus: {getattr(stats, 'speed', '-')}",
            ]
            for line in lines:
                screen.blit(fonts.small.render(line, True, COLORS["text_main"]), (x, y))
                y += 18
        elif npc.custom_stats:
            for k, v in npc.custom_stats.items():
                if isinstance(v, (str, int, float)) and v != "":
                    screen.blit(fonts.tiny.render(f"{k}: {v}", True, COLORS["text_main"]),
                                (x, y))
                    y += 14
        else:
            screen.blit(fonts.small.render("Ei tilastoja. Linkitä hirviö tai "
                                            "sankari Worldin kautta.",
                                            True, COLORS["text_dim"]), (x, y))
            y += 18
        return y

    def _draw_inventory(self, screen, npc, x, y, max_w) -> int:
        hdr = fonts.small_bold.render(f"Kulta: {npc.gold:.1f} gp",
                                       True, COLORS["text_bright"])
        screen.blit(hdr, (x, y)); y += 22
        if npc.inventory_items:
            screen.blit(fonts.small_bold.render("Henkilökohtaiset esineet:",
                                                 True, COLORS["text_dim"]), (x, y))
            y += 18
            for item in npc.inventory_items:
                screen.blit(fonts.small.render(f"• {item}", True,
                                                COLORS["text_main"]), (x, y))
                y += 16
            y += 6
        if npc.is_shopkeeper and npc.shop_items:
            screen.blit(fonts.small_bold.render(
                f"Kauppa: {npc.shop_name or npc.shop_type}",
                True, COLORS["text_dim"]), (x, y))
            y += 18
            for si in npc.shop_items:
                line = f"• {si.item_name}"
                screen.blit(fonts.small.render(line, True, COLORS["text_main"]),
                            (x, y))
                y += 16
        if not npc.inventory_items and not (npc.is_shopkeeper and npc.shop_items):
            screen.blit(fonts.small.render("Ei listattuja esineitä.", True,
                                            COLORS["text_dim"]), (x, y))
            y += 18
        return y

    def _draw_relations(self, screen, npc, x, y, max_w) -> int:
        if not npc.relationships:
            screen.blit(fonts.small.render("Ei merkittyjä suhteita PC:ihin.",
                                            True, COLORS["text_dim"]), (x, y))
            return y + 18
        for rel in npc.relationships:
            hdr = fonts.small_bold.render(
                f"{rel.hero_name or '-'}  ({rel.attitude})",
                True, COLORS["text_bright"])
            screen.blit(hdr, (x, y)); y += 18
            y = self._wrap(screen, rel.notes or "-", x, y, max_w)
            y += 8
        return y


# ======================================================================
class AdvanceTimeModal:
    """Small confirm dialog: pick a day count, advance world time.

    Triggers :func:`data.map_travel.advance_followers` on the state's
    ``world_map`` and nudges every party/caravan/army_token that has a
    ``follow_path_id`` forward by the configured number of travel days.
    """
    W = 400
    H = 230
    PRESETS = (1, 3, 7)

    def __init__(self, state, on_close):
        self.state = state
        self.on_close = on_close
        self.days = 1.0
        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2
        self.rect = pygame.Rect(self.x, self.y, self.W, self.H)

        self._preset_btns = []
        bx = self.x + 20
        for n in self.PRESETS:
            self._preset_btns.append(
                Button(bx, self.y + 80, 70, 36, f"{n} pv",
                        lambda n=n: self._set_days(n),
                        color=COLORS["panel_light"])
            )
            bx += 80

        self.btn_go = Button(self.x + 20, self.y + self.H - 50,
                              170, 38, "Edistä aikaa", self._go,
                              color=COLORS["accent"])
        self.btn_close = Button(self.x + self.W - 110, self.y + self.H - 50,
                                 90, 38, "Sulje", self._close,
                                 color=COLORS["danger"])

    def _set_days(self, n: float) -> None:
        self.days = float(n)

    def _close(self) -> None:
        self.on_close()

    def _go(self) -> None:
        from data.map_travel import advance_followers_events
        events = advance_followers_events(self.state.world_map, self.days)
        moved = len(events)
        arrivals = [e for e in events if e["arrived"]]
        crossings = []
        for e in events:
            for wp in e.get("waypoints_passed", []):
                crossings.append(f"{e['label']} → {wp['label']}")
        msg = f"Edistetty {self.days:.1f} pv — {moved} yksikköä liikkui."
        if crossings:
            msg += "  Kulki: " + "; ".join(crossings) + "."
        if arrivals:
            names = ", ".join(e["label"] for e in arrivals)
            msg += f"  SAAPUI: {names}."
        self.state._set_status(msg)

    def handle_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._close()
            return
        self.btn_go.handle_event(ev)
        self.btn_close.handle_event(ev)
        for b in self._preset_btns:
            b.handle_event(ev)

    def draw(self, screen) -> None:
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        screen.blit(ov, (0, 0))
        pygame.draw.rect(screen, COLORS["panel"], self.rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 2, border_radius=12)

        hdr = fonts.header.render("Edistä matkaa",
                                    True, COLORS["text_bright"])
        screen.blit(hdr, (self.x + 20, self.y + 16))

        info = fonts.small.render(
            f"Valitut päivät: {self.days:.1f} — siirtää reittiä seuraavat tokenit.",
            True, COLORS["text_dim"])
        screen.blit(info, (self.x + 20, self.y + 54))

        mp = pygame.mouse.get_pos()
        for b in self._preset_btns:
            b.draw(screen, mp)
        self.btn_go.draw(screen, mp)
        self.btn_close.draw(screen, mp)
