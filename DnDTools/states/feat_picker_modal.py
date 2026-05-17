"""Phase 32 — feat picker modal.

Lets the DM add/remove PHB feats on a campaign NPC from the
campaign-manager NPC sheet (not only at hero creation).

Persists into ``NPC.custom_stats["features"]`` — the same dict used by
:func:`data.world._serialize_npc`. When the NPC has no custom stat
block yet, the modal seeds an empty one so adding a feat is enough to
establish the NPC's combat features.

UI:

  * Header: NPC name + count of feats applied.
  * Two columns:
    - Left: scrollable list of every PHB feat with [+] to add.
    - Right: currently-applied feats with [×] to remove and a
      short one-line summary of the combat effect.
  * Footer: "Save" persists the changes, "Cancel" reverts.

When a feat is added/removed the modal also applies the matching
runtime effect:

  * Tough: ``custom_stats["hit_points"] += 2 * level`` (or subtract
    on remove).
  * Resilient: adds proficiency to the named save.
  * Heavy Armor Master / others: pure :class:`Feature` rows — the
    engine already consults them via ``has_feature``.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.feats import ALL_FEATS, FEATS_BY_NAME, get_feat
from data.models import Feature


_ABBR_TO_FULL = {
    "STR": "Strength", "DEX": "Dexterity", "CON": "Constitution",
    "INT": "Intelligence", "WIS": "Wisdom", "CHA": "Charisma",
}


class FeatPickerModal:
    WIDTH = 880
    HEIGHT = 560
    ROW_H = 26

    def __init__(self, npc, *,
                  on_close: Optional[Callable[[], None]] = None,
                  on_saved: Optional[Callable[[], None]] = None):
        self.npc = npc
        self.on_close = on_close
        self.on_saved = on_saved
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        # Working copy of features (revertable on Cancel).
        original_features = list(self._read_features())
        self._working: List[Feature] = deepcopy(original_features)
        self._original_features: List[Feature] = original_features
        self.scroll_avail = 0
        self.scroll_applied = 0
        self._status = ""

        # Hit rects rebuilt every draw
        self._add_rects: List[Tuple[pygame.Rect, str]] = []
        self._remove_rects: List[Tuple[pygame.Rect, str]] = []

        self.btn_save = Button(0, 0, 120, 34, "Tallenna",
                                  self._save,
                                  color=COLORS.get("success",
                                                     (90, 200, 120)))
        self.btn_cancel = Button(0, 0, 120, 34, "Peruuta",
                                    self._cancel,
                                    color=COLORS.get("panel",
                                                       (60, 60, 80)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self._working = deepcopy(self._read_features())
        self._original_features = list(self._read_features())
        self.scroll_avail = 0
        self.scroll_applied = 0
        self._status = ""

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    def _read_features(self) -> List[Feature]:
        """Pull the NPC's current Feature list out of custom_stats."""
        if not self.npc:
            return []
        cs = self.npc.custom_stats or {}
        rows = cs.get("features", []) or []
        out: List[Feature] = []
        for r in rows:
            if isinstance(r, dict):
                out.append(Feature(
                    name=r.get("name", ""),
                    description=r.get("description", ""),
                    feature_type=r.get("feature_type", "feat"),
                    mechanic=r.get("mechanic", ""),
                    mechanic_value=r.get("mechanic_value", ""),
                    uses_per_day=r.get("uses_per_day", -1),
                ))
            elif isinstance(r, Feature):
                out.append(r)
        return out

    def _write_features(self) -> None:
        if not self.npc:
            return
        cs = self.npc.custom_stats or {}
        cs["features"] = [
            {"name": f.name, "description": f.description,
              "feature_type": f.feature_type, "mechanic": f.mechanic,
              "mechanic_value": f.mechanic_value,
              "uses_per_day": f.uses_per_day}
            for f in self._working
        ]
        self.npc.custom_stats = cs

    def _has_feat(self, feat_name: str) -> bool:
        return any(f.name == feat_name for f in self._working)

    def _add_feat(self, feat_name: str) -> None:
        if self._has_feat(feat_name):
            return
        feat = FEATS_BY_NAME.get(feat_name)
        if not feat:
            return
        self._working.append(Feature(
            name=feat.name,
            description=feat.combat_effect or feat.description[:100],
            feature_type="feat",
            mechanic=feat.mechanic,
            mechanic_value=feat.mechanic_value,
        ))
        # Resilient asks for a save type; default to CON if blank
        if feat.mechanic == "resilient" and not feat.mechanic_value:
            self._working[-1].mechanic_value = "CON"
        self._status = f"Lisätty {feat.name}."

    def _remove_feat(self, feat_name: str) -> None:
        self._working = [f for f in self._working if f.name != feat_name]
        self._status = f"Poistettu {feat_name}."

    # ------------------------------------------------------------------ #
    def _save(self) -> None:
        self._write_features()
        # Apply one-shot bonuses if the feat list changed
        self._apply_one_shot_bonuses()
        self._status = "Tallennettu."
        if self.on_saved:
            self.on_saved()
        self.close()

    def _cancel(self) -> None:
        self._working = list(self._original_features)
        self.close()

    def _apply_one_shot_bonuses(self) -> None:
        """Apply Tough HP and Resilient save proficiency immediately
        (rather than waiting for the next combat to re-derive stats).
        """
        cs = self.npc.custom_stats or {}
        level = max(1, int(cs.get("character_level", 1) or 1))
        # Tough: +2 HP per level, on add; -2 per level on remove.
        was_tough = any(f.name == "Tough"
                          for f in self._original_features)
        is_tough = any(f.name == "Tough" for f in self._working)
        if was_tough != is_tough:
            delta = (2 * level) if is_tough else (-2 * level)
            hp = int(cs.get("hit_points", 0) or 0)
            cs["hit_points"] = max(1, hp + delta)
        # Resilient: add ability save to saving_throws dict if missing.
        # mechanic_value carries the ability abbreviation.
        for f in self._working:
            if f.mechanic == "resilient" and f.mechanic_value:
                full = _ABBR_TO_FULL.get(f.mechanic_value.upper())
                if not full:
                    continue
                saves = cs.setdefault("saving_throws", {})
                if full not in saves:
                    # Approximate: PB at level (2 + (level-1)//4) +
                    # the ability mod.
                    pb = 2 + max(0, level - 1) // 4
                    abilities = cs.get("abilities", {})
                    score = int(abilities.get(
                        full.lower(),
                        abilities.get(f.mechanic_value.lower(), 10)
                    ) or 10)
                    mod = (score - 10) // 2
                    saves[full] = mod + pb
        self.npc.custom_stats = cs

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel()
            return True
        if event.type == pygame.MOUSEWHEEL:
            mp = pygame.mouse.get_pos()
            # Scroll the column under the mouse
            mid = self.x + self.WIDTH // 2
            if mp[0] < mid:
                self.scroll_avail = max(
                    0, self.scroll_avail - event.y * 30)
            else:
                self.scroll_applied = max(
                    0, self.scroll_applied - event.y * 30)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_save, self.btn_cancel):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            for rect, name in self._add_rects:
                if rect.collidepoint(event.pos):
                    self._add_feat(name)
                    return True
            for rect, name in self._remove_rects:
                if rect.collidepoint(event.pos):
                    self._remove_feat(name)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def draw(self, screen) -> None:
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                          rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                          rect, 2, border_radius=10)

        npc_name = getattr(self.npc, "name", "(no NPC)")
        screen.blit(fonts.body_bold.render(
            f"Featit — {npc_name}", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, self.y + 16))
        screen.blit(fonts.small.render(
            f"{len(self._working)} featia valittuna · "
            f"{len(ALL_FEATS)} saatavilla", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 20, self.y + 44))

        col_top = self.y + 78
        col_h = self.HEIGHT - 78 - 56
        left = pygame.Rect(self.x + 16, col_top,
                            (self.WIDTH - 48) // 2, col_h)
        right = pygame.Rect(left.right + 16, col_top,
                             (self.WIDTH - 48) // 2, col_h)
        self._draw_available(screen, left, mp)
        self._draw_applied(screen, right, mp)

        # Footer
        if self._status:
            screen.blit(fonts.small.render(
                self._status, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 20, self.HEIGHT + self.y - 56))
        self.btn_save.rect.x = self.x + 20
        self.btn_save.rect.y = self.y + self.HEIGHT - 44
        self.btn_save.draw(screen, mp)
        self.btn_cancel.rect.x = self.x + self.WIDTH - 140
        self.btn_cancel.rect.y = self.y + self.HEIGHT - 44
        self.btn_cancel.draw(screen, mp)

    # ------------------------------------------------------------------ #
    def _draw_available(self, screen, area, mp):
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        screen.blit(fonts.small_bold.render(
            "Saatavilla", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (area.x + 8, area.y + 6))
        body = pygame.Rect(area.x + 4, area.y + 28,
                            area.width - 8, area.height - 36)
        prev = screen.get_clip()
        screen.set_clip(body)
        self._add_rects = []
        y = body.y - self.scroll_avail
        for feat in sorted(ALL_FEATS, key=lambda f: f.name):
            if self._has_feat(feat.name):
                continue
            row = pygame.Rect(body.x + 4, y, body.width - 8, self.ROW_H)
            is_hov = row.collidepoint(mp)
            pygame.draw.rect(screen,
                              COLORS.get("hover", (60, 60, 80))
                              if is_hov
                              else COLORS.get("panel_dark", (32, 32, 42)),
                              row, border_radius=4)
            # "+" button
            add_btn = pygame.Rect(row.right - 28, row.y + 3, 22, 20)
            pygame.draw.rect(screen,
                              COLORS.get("success", (90, 200, 120)),
                              add_btn, border_radius=3)
            screen.blit(fonts.small_bold.render(
                "+", True, (20, 20, 20)),
                (add_btn.x + 7, add_btn.y + 1))
            self._add_rects.append((add_btn, feat.name))
            screen.blit(fonts.small.render(
                feat.name, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 8, row.y + 4))
            y += self.ROW_H + 2
        screen.set_clip(prev)

    def _draw_applied(self, screen, area, mp):
        pygame.draw.rect(screen, COLORS.get("panel", (40, 40, 56)),
                          area, border_radius=6)
        screen.blit(fonts.small_bold.render(
            "Valitut", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (area.x + 8, area.y + 6))
        body = pygame.Rect(area.x + 4, area.y + 28,
                            area.width - 8, area.height - 36)
        prev = screen.get_clip()
        screen.set_clip(body)
        self._remove_rects = []
        y = body.y - self.scroll_applied
        if not self._working:
            screen.blit(fonts.small.render(
                "(ei valittuja featejä — klikkaa + vasemmalta)",
                True,
                COLORS.get("text_dim", (170, 170, 180))),
                (body.x + 8, body.y + 8))
        for f in self._working:
            row = pygame.Rect(body.x + 4, y, body.width - 8,
                                self.ROW_H + 12)
            pygame.draw.rect(screen,
                              COLORS.get("panel_dark", (32, 32, 42)),
                              row, border_radius=4)
            # "×" button
            del_btn = pygame.Rect(row.right - 28, row.y + 3, 22, 20)
            pygame.draw.rect(screen,
                              COLORS.get("danger", (220, 100, 90)),
                              del_btn, border_radius=3)
            screen.blit(fonts.small_bold.render(
                "×", True, (20, 20, 20)),
                (del_btn.x + 7, del_btn.y + 1))
            self._remove_rects.append((del_btn, f.name))
            screen.blit(fonts.small_bold.render(
                f.name, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (row.x + 8, row.y + 4))
            feat = FEATS_BY_NAME.get(f.name)
            if feat:
                screen.blit(fonts.tiny.render(
                    (feat.combat_effect or feat.description)[:60],
                    True,
                    COLORS.get("text_dim", (170, 170, 180))),
                    (row.x + 8, row.y + 20))
            y += self.ROW_H + 14
        screen.set_clip(prev)
