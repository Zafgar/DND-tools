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
