"""Bulk-edit modal — pops up after rectangle-selecting a group of
MapObjects so the DM can retype / tag / hide / delete them in one
gesture.

Pure pygame UI on top of ``data/map_bulk_ops.py``. Fields:

  * Object type — text or quick presets to retype every selected
    object (uses Phase 12b's bulk_set_object_type).
  * Add tags / Remove tags — comma-separated.
  * "DM only" / "Visible" toggles.
  * "Delete" button (with confirm) for the whole selection.

ESC / "Sulje" closes without applying. "Käytä" (Apply) batches
the changes.
"""
from __future__ import annotations

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect
from data.map_bulk_ops import (
    bulk_set_object_type, bulk_add_tags, bulk_remove_tags,
    bulk_set_visibility, bulk_delete, selection_summary,
)


class BulkEditModal:
    WIDTH = 480
    HEIGHT = 420

    def __init__(self, state, on_close=None):
        """``state`` is the MapEditorState. Reads
        ``state.selected_object_ids`` and ``state.world_map``."""
        self.state = state
        self.on_close = on_close
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self._field_focus = None      # "type" / "add_tags" / "rm_tags"
        self.type_input = ""
        self.add_tags_input = ""
        self.rm_tags_input = ""
        self._confirm_delete = False
        self._status = ""

        self.btn_close = Button(
            self.x + self.WIDTH - 110, self.y + self.HEIGHT - 50,
            90, 36, "Sulje", self._cancel,
            color=COLORS.get("panel", (60, 60, 80)),
        )
        self.btn_apply = Button(
            self.x + 20, self.y + self.HEIGHT - 50,
            120, 36, "Käytä",
            self._apply, color=COLORS.get("success", (90, 200, 120)),
        )
        self.btn_delete = Button(
            self.x + 150, self.y + self.HEIGHT - 50,
            150, 36, "Poista valitut",
            self._delete_clicked, color=COLORS.get("danger",
                                                       (220, 80, 80)),
        )
        # Visibility quick-toggles
        self.btn_dm_only = Button(
            self.x + 20, self.y + 280,
            150, 32, "Vain DM",
            lambda: self._set_visibility(dm_only=True),
            color=COLORS.get("warning", (220, 180, 80)),
        )
        self.btn_show_all = Button(
            self.x + 180, self.y + 280,
            150, 32, "Kaikille näkyvä",
            lambda: self._set_visibility(dm_only=False, visible=True),
            color=COLORS.get("accent", (180, 180, 240)),
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self._field_focus = None
        self._confirm_delete = False
        self._status = ""
        self.type_input = ""
        self.add_tags_input = ""
        self.rm_tags_input = ""

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _cancel(self):
        self.close()

    # ------------------------------------------------------------------ #
    # Bulk action wrappers
    # ------------------------------------------------------------------ #
    def _apply(self):
        sel = self.state.selected_object_ids
        if not sel:
            self._status = "Ei valittuja objekteja"
            return
        wm = self.state.world_map
        bits = []
        if self.type_input.strip():
            n = bulk_set_object_type(wm, sel, self.type_input.strip())
            bits.append(f"tyyppi {n}")
        if self.add_tags_input.strip():
            tags = [t for t in
                    (s.strip() for s in self.add_tags_input.split(","))
                    if t]
            n = bulk_add_tags(wm, sel, tags)
            if n:
                bits.append(f"+tagit {n}")
        if self.rm_tags_input.strip():
            tags = [t for t in
                    (s.strip() for s in self.rm_tags_input.split(","))
                    if t]
            n = bulk_remove_tags(wm, sel, tags)
            if n:
                bits.append(f"-tagit {n}")
        self._status = ("Käytetty: " + ", ".join(bits) if bits
                         else "Ei muutoksia")

    def _set_visibility(self, *, dm_only=None, visible=None):
        sel = self.state.selected_object_ids
        if not sel:
            self._status = "Ei valittuja objekteja"
            return
        n = bulk_set_visibility(self.state.world_map, sel,
                                  dm_only=dm_only, visible=visible)
        flag = "vain DM" if dm_only else "näkyvä"
        self._status = f"Näkyvyys {flag}: {n}"

    def _delete_clicked(self):
        sel = self.state.selected_object_ids
        if not sel:
            self._status = "Ei valittuja objekteja"
            return
        if not self._confirm_delete:
            self._confirm_delete = True
            self._status = (f"Vahvista: poista {len(sel)} objektia? "
                              f"Klikkaa 'Poista' uudelleen")
            return
        n = bulk_delete(self.state.world_map, sel)
        self.state.selected_object_ids.clear()
        self._status = f"Poistettu {n} objektia"
        self._confirm_delete = False

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self._field_focus is not None:
                target = self._field_focus
                if event.key == pygame.K_BACKSPACE:
                    setattr(self, target, getattr(self, target)[:-1])
                    return True
                if event.key == pygame.K_RETURN:
                    self._field_focus = None
                    return True
                if event.unicode and event.unicode.isprintable():
                    cur = getattr(self, target)
                    if len(cur) < 80:
                        setattr(self, target, cur + event.unicode)
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Field focus rectangles
            for name, rect in self._field_rects().items():
                if rect.collidepoint(event.pos):
                    self._field_focus = name
                    return True
            self._field_focus = None
            self.btn_apply.handle_event(event)
            self.btn_delete.handle_event(event)
            self.btn_close.handle_event(event)
            self.btn_dm_only.handle_event(event)
            self.btn_show_all.handle_event(event)
            return True
        return False

    def _field_rects(self):
        return {
            "type_input":     pygame.Rect(self.x + 140, self.y + 90,
                                            self.WIDTH - 160, 30),
            "add_tags_input": pygame.Rect(self.x + 140, self.y + 140,
                                            self.WIDTH - 160, 30),
            "rm_tags_input":  pygame.Rect(self.x + 140, self.y + 190,
                                            self.WIDTH - 160, 30),
        }

    # ------------------------------------------------------------------ #
    # Draw
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
        draw_gradient_rect(screen, rect,
                            COLORS.get("bg_dark", (24, 24, 32)),
                            COLORS.get("bg", (32, 32, 40)),
                            border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light", (110, 110, 140)),
                         rect, 2, border_radius=10)

        title = fonts.header.render("Bulk-muokkaus",
                                       True, COLORS.get("accent",
                                                          (180, 180, 240)))
        screen.blit(title, (self.x + 20, self.y + 12))

        # Selection summary
        summary = selection_summary(self.state.world_map,
                                       self.state.selected_object_ids)
        if summary.count == 0:
            sub = "Ei valintoja — sulje ja valitse alue."
        else:
            type_str = ", ".join(f"{k}({v})"
                                  for k, v in summary.by_type.items())
            sub = f"{summary.count} objektia · {type_str}"
        screen.blit(fonts.small.render(sub, True,
                                          COLORS.get("text_dim",
                                                       (160, 160, 160))),
                    (self.x + 20, self.y + 50))

        # Field rows
        labels = (
            ("Vaihda tyyppi:", "type_input"),
            ("Lisää tagit:",   "add_tags_input"),
            ("Poista tagit:",  "rm_tags_input"),
        )
        rects = self._field_rects()
        for (lbl, name) in labels:
            rect_field = rects[name]
            screen.blit(
                fonts.small.render(
                    lbl, True,
                    COLORS.get("text", (220, 220, 220))),
                (self.x + 20, rect_field.y + 6),
            )
            pygame.draw.rect(screen,
                              COLORS.get("bg_dark", (20, 20, 26)),
                              rect_field, border_radius=4)
            edge = (COLORS.get("accent", (180, 180, 240))
                     if self._field_focus == name
                     else COLORS.get("border", (80, 80, 100)))
            pygame.draw.rect(screen, edge, rect_field, 1,
                              border_radius=4)
            cursor = ("|" if (self._field_focus == name
                                and pygame.time.get_ticks() // 400 % 2 == 0)
                       else "")
            txt = (getattr(self, name) + cursor) or ""
            screen.blit(
                fonts.small.render(txt, True,
                                      COLORS.get("text_bright",
                                                   (240, 240, 240))),
                (rect_field.x + 8, rect_field.y + 6),
            )

        # Visibility row
        screen.blit(
            fonts.small.render("Näkyvyys:", True,
                                  COLORS.get("text", (220, 220, 220))),
            (self.x + 20, self.y + 252),
        )
        self.btn_dm_only.draw(screen, mp)
        self.btn_show_all.draw(screen, mp)

        if self._status:
            screen.blit(
                fonts.small.render(self._status, True,
                                      COLORS.get("warning",
                                                   (220, 180, 80))),
                (self.x + 20, self.y + 330),
            )

        self.btn_apply.draw(screen, mp)
        self.btn_delete.draw(screen, mp)
        self.btn_close.draw(screen, mp)
