"""Quick-create Quest modal — single-form quest builder.

Fields:
  * Name (text)
  * Quest type cycler (main / side / personal / faction / bounty)
  * Priority cycler (low / normal / high / urgent)
  * Giver NPC dropdown — cycler through ``world.npcs`` values
  * Map-pin location cycler (locations with map positions)
  * Monster keyword (text)
  * Reward XP (numeric)
  * Reward gold (numeric)

The active text field is highlighted; arrow keys cycle non-text fields.
Confirm builds a :class:`data.world.Quest`, drops it into
``world.quests`` and fires ``on_created(quest_id)``.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.world import (
    World, Quest, generate_id,
    QUEST_TYPES, QUEST_PRIORITIES,
)


class QuickCreateQuestModal:
    WIDTH = 540
    HEIGHT = 470

    # Field keys in tab order
    _FIELDS = ("name", "monster", "xp", "gold")

    def __init__(self, world: World, *,
                  default_giver_npc_id: str = "",
                  default_location_id: str = "",
                  on_close: Optional[Callable[[], None]] = None,
                  on_created: Optional[Callable[[str], None]] = None):
        self.world = world
        self.on_close = on_close
        self.on_created = on_created
        self.is_open = False

        # State
        self.name = ""
        self.monster = ""
        self.xp_str = "0"
        self.gold_str = "0"
        self.active_field = "name"
        self.quest_type_idx = QUEST_TYPES.index("side")
        self.priority_idx = QUEST_PRIORITIES.index("normal")
        # Build cycler sources from the world
        self._npc_keys: List[str] = [""] + sorted(world.npcs.keys())
        if default_giver_npc_id in self._npc_keys:
            self.npc_idx = self._npc_keys.index(default_giver_npc_id)
        else:
            self.npc_idx = 0
        self._loc_keys: List[str] = [""] + sorted(world.locations.keys())
        if default_location_id in self._loc_keys:
            self.loc_idx = self._loc_keys.index(default_location_id)
        else:
            self.loc_idx = 0
        self._status = ""

        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        col = COLORS.get
        self.btn_type = Button(0, 0, 240, 24, self._type_label(),
                                  self._cycle_type,
                                  color=col("legendary", (170, 110, 220)))
        self.btn_pri = Button(0, 0, 240, 24, self._pri_label(),
                                 self._cycle_pri,
                                 color=col("warning", (220, 180, 80)))
        self.btn_npc = Button(0, 0, 280, 24, self._npc_label(),
                                 self._cycle_npc,
                                 color=col("player", (110, 180, 240)))
        self.btn_loc = Button(0, 0, 280, 24, self._loc_label(),
                                 self._cycle_loc,
                                 color=col("accent", (110, 130, 220)))
        self.btn_create = Button(0, 0, 160, 32, "Luo tehtävä",
                                    self._create,
                                    color=col("success", (90, 200, 120)))
        self.btn_close = Button(0, 0, 100, 32, "Peruuta",
                                   self._cancel,
                                   color=col("panel", (60, 60, 80)))

    # ------------------------------------------------------------------ #
    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _cancel(self) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    def _type_label(self) -> str:
        return f"Tyyppi: {QUEST_TYPES[self.quest_type_idx]}"

    def _pri_label(self) -> str:
        return f"Prioriteetti: {QUEST_PRIORITIES[self.priority_idx]}"

    def _npc_label(self) -> str:
        key = self._npc_keys[self.npc_idx]
        if not key:
            return "Antaja: (ei kukaan)"
        npc = self.world.npcs.get(key)
        return f"Antaja: {npc.name if npc else key}"

    def _loc_label(self) -> str:
        key = self._loc_keys[self.loc_idx]
        if not key:
            return "Kartta: (ei pinniä)"
        loc = self.world.locations.get(key)
        return f"Kartta: {loc.name if loc else key}"

    def _cycle_type(self) -> None:
        self.quest_type_idx = (self.quest_type_idx + 1) % len(QUEST_TYPES)
        self.btn_type.text = self._type_label()

    def _cycle_pri(self) -> None:
        self.priority_idx = (self.priority_idx + 1) % len(QUEST_PRIORITIES)
        self.btn_pri.text = self._pri_label()

    def _cycle_npc(self) -> None:
        self.npc_idx = (self.npc_idx + 1) % len(self._npc_keys)
        self.btn_npc.text = self._npc_label()

    def _cycle_loc(self) -> None:
        self.loc_idx = (self.loc_idx + 1) % len(self._loc_keys)
        self.btn_loc.text = self._loc_label()

    # ------------------------------------------------------------------ #
    def _create(self) -> None:
        nm = (self.name or "").strip()
        if not nm:
            self._status = "Anna tehtävän nimi."
            return
        try:
            xp = int(self.xp_str or 0)
        except ValueError:
            xp = 0
        try:
            gold = float(self.gold_str or 0)
        except ValueError:
            gold = 0.0
        qid = generate_id(self.world, "quest")
        quest = Quest(
            id=qid, name=nm,
            quest_type=QUEST_TYPES[self.quest_type_idx],
            priority=QUEST_PRIORITIES[self.priority_idx],
            status="active",
            giver_npc_id=self._npc_keys[self.npc_idx],
            map_pin_location_id=self._loc_keys[self.loc_idx],
            reward_xp=xp, reward_gold=gold,
        )
        if self.monster.strip():
            quest.monster_names = [self.monster.strip()]
        if quest.giver_npc_id:
            quest.npc_ids.append(quest.giver_npc_id)
        if quest.map_pin_location_id:
            quest.location_ids.append(quest.map_pin_location_id)
        self.world.quests[qid] = quest
        if self.on_created:
            self.on_created(qid)
        self.close()

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if event.key == pygame.K_TAB:
                cur = self._FIELDS.index(self.active_field)
                self.active_field = self._FIELDS[
                    (cur + 1) % len(self._FIELDS)]
                return True
            # Edit the active text field
            target_attr = {
                "name": "name", "monster": "monster",
                "xp": "xp_str", "gold": "gold_str",
            }[self.active_field]
            cur = getattr(self, target_attr)
            if event.key == pygame.K_BACKSPACE:
                setattr(self, target_attr, cur[:-1])
                return True
            if event.key == pygame.K_RETURN:
                self._create()
                return True
            if event.unicode and event.unicode.isprintable():
                ok = True
                if self.active_field in ("xp", "gold"):
                    ok = (event.unicode.isdigit()
                           or (event.unicode == "." and
                                "." not in cur))
                if ok and len(cur) < 80:
                    setattr(self, target_attr, cur + event.unicode)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_type, self.btn_pri, self.btn_npc,
                          self.btn_loc, self.btn_create, self.btn_close):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            # Field clicks switch focus
            for key, rect in self._field_rects():
                if rect.collidepoint(event.pos):
                    self.active_field = key
                    return True
            return True
        return False

    def _field_rects(self):
        return [
            ("name", pygame.Rect(self.x + 20, self.y + 60,
                                  self.WIDTH - 40, 32)),
            ("monster", pygame.Rect(self.x + 20, self.y + 260,
                                       self.WIDTH - 40, 28)),
            ("xp", pygame.Rect(self.x + 20, self.y + 320,
                                  140, 28)),
            ("gold", pygame.Rect(self.x + 180, self.y + 320,
                                    140, 28)),
        ]

    # ------------------------------------------------------------------ #
    def draw(self, screen) -> None:
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                          rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (110, 110, 140)),
                          rect, 2, border_radius=10)
        screen.blit(fonts.body_bold.render(
            "Pika-luo tehtävä", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, self.y + 16))

        # Name field
        screen.blit(fonts.small.render(
            "Nimi:", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 20, self.y + 44))
        self._draw_text_field(screen, "name", self.name,
                                self.x + 20, self.y + 60,
                                self.WIDTH - 40, 32)

        # Type + Priority cycler row
        self.btn_type.rect.x = self.x + 20
        self.btn_type.rect.y = self.y + 100
        self.btn_type.text = self._type_label()
        self.btn_type.draw(screen, mp)
        self.btn_pri.rect.x = self.x + 270
        self.btn_pri.rect.y = self.y + 100
        self.btn_pri.text = self._pri_label()
        self.btn_pri.draw(screen, mp)

        # Giver NPC + map pin cycler row (stacked)
        self.btn_npc.rect.x = self.x + 20
        self.btn_npc.rect.y = self.y + 140
        self.btn_npc.text = self._npc_label()
        self.btn_npc.draw(screen, mp)
        self.btn_loc.rect.x = self.x + 20
        self.btn_loc.rect.y = self.y + 180
        self.btn_loc.text = self._loc_label()
        self.btn_loc.draw(screen, mp)

        # Monster + rewards
        screen.blit(fonts.small.render(
            "Hirviö (vapaa teksti):", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 20, self.y + 240))
        self._draw_text_field(screen, "monster", self.monster,
                                self.x + 20, self.y + 260,
                                self.WIDTH - 40, 28)
        screen.blit(fonts.small.render(
            "Palkkio XP:", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 20, self.y + 300))
        screen.blit(fonts.small.render(
            "Palkkio gp:", True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 180, self.y + 300))
        self._draw_text_field(screen, "xp", self.xp_str,
                                self.x + 20, self.y + 320, 140, 28)
        self._draw_text_field(screen, "gold", self.gold_str,
                                self.x + 180, self.y + 320, 140, 28)

        if self._status:
            screen.blit(fonts.small.render(
                self._status, True,
                COLORS.get("warning", (220, 180, 80))),
                (self.x + 20, self.y + 365))

        self.btn_create.rect.x = self.x + 20
        self.btn_create.rect.y = self.y + self.HEIGHT - 50
        self.btn_create.draw(screen, mp)
        self.btn_close.rect.x = self.x + self.WIDTH - 120
        self.btn_close.rect.y = self.y + self.HEIGHT - 50
        self.btn_close.draw(screen, mp)

    def _draw_text_field(self, screen, key, text, x, y, w, h):
        field = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, COLORS.get("bg", (32, 32, 40)),
                          field, border_radius=4)
        edge = (COLORS.get("accent", (180, 180, 240))
                 if self.active_field == key
                 else COLORS.get("border", (80, 80, 100)))
        pygame.draw.rect(screen, edge, field, 1, border_radius=4)
        cursor = ("|" if self.active_field == key
                            and pygame.time.get_ticks() // 400 % 2 == 0
                    else "")
        screen.blit(fonts.body.render(
            text + cursor, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (field.x + 8, field.y + 4))
