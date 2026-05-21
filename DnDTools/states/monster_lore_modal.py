"""Phase 37 — Monster Lore modal.

Full-screen DM-facing info card for a creature.  Shows everything that
helps run the encounter:

  * Identity strip: name, size, type, CR, XP, alignment.
  * Combat-relevant numbers: AC, HP, speed list, prof. bonus.
  * Damage profile: immunities / resistances / vulnerabilities,
    condition immunities.
  * Saves and skills.
  * Senses, languages, sources (MM page reference).
  * Lore paragraph (DM-facing flavour).
  * Tactics paragraph (how the AI / DM should play it).
  * Loot suggestions (treasure-hoard tier, signature items).
  * Habitat.
  * Action / reaction / legendary action lists, grouped.
  * Feature list, separating racial / class / legendary / lair.
  * Legendary Action and Resistance counters with live remaining.

Usable from the campaign-manager NPC sheet (when the NPC's stats came
from a monster catalog entry) and from the battle renderer (right-
click an entity → "Show lore").
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts


_COND_COLOR = {
    "immunity":      (90, 200, 120),
    "resistance":    (110, 180, 240),
    "vulnerability": (220, 130, 90),
}


def _format_speed(stats) -> str:
    parts = [f"walk {stats.speed} ft"]
    if stats.fly_speed:
        parts.append(f"fly {stats.fly_speed} ft")
    if stats.swim_speed:
        parts.append(f"swim {stats.swim_speed} ft")
    if stats.climb_speed:
        parts.append(f"climb {stats.climb_speed} ft")
    if stats.burrow_speed:
        parts.append(f"burrow {stats.burrow_speed} ft")
    return ", ".join(parts)


def _format_abilities(abilities) -> str:
    def m(score):
        mod = (score - 10) // 2
        sign = "+" if mod >= 0 else ""
        return f"{score} ({sign}{mod})"
    return (f"STR {m(abilities.strength)}   "
             f"DEX {m(abilities.dexterity)}   "
             f"CON {m(abilities.constitution)}   "
             f"INT {m(abilities.intelligence)}   "
             f"WIS {m(abilities.wisdom)}   "
             f"CHA {m(abilities.charisma)}")


def _wrap(text: str, font, max_width: int) -> list:
    """Break ``text`` into rendered lines fitting ``max_width``."""
    if not text:
        return []
    words = text.split()
    lines = []
    cur = ""
    for w in words:
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


class MonsterLoreModal:
    """Phase 37 — DM-facing creature info card."""
    WIDTH = 920
    HEIGHT = 640

    def __init__(self, stats, *,
                  entity=None,
                  on_close: Optional[Callable[[], None]] = None):
        self.stats = stats
        self.entity = entity   # Optional live Entity for live counters
        self.on_close = on_close
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2
        self.scroll = 0
        self._content_height = 0
        self.btn_close = Button(0, 0, 90, 32, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))

    # ------------------------------------------------------------------ #
    def open(self) -> None:
        self.is_open = True
        self.scroll = 0

    def _close(self) -> None:
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return True
        if event.type == pygame.MOUSEWHEEL:
            max_scroll = max(0, self._content_height
                              - (self.HEIGHT - 100))
            self.scroll = max(0, min(max_scroll,
                                        self.scroll - event.y * 30))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.rect.collidepoint(event.pos):
                self.btn_close.handle_event(event)
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
        pygame.draw.rect(screen, COLORS.get("bg_dark", (22, 22, 30)),
                          rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (130, 130, 160)),
                          rect, 2, border_radius=10)

        # Header strip (always visible — not scrolled)
        self._draw_header(screen, rect)

        # Scrollable content area
        content_top = self.y + 90
        content_rect = pygame.Rect(self.x + 4, content_top,
                                      self.WIDTH - 8,
                                      self.HEIGHT - 90 - 56)
        prev_clip = screen.get_clip()
        screen.set_clip(content_rect)
        y = content_top + 8 - self.scroll
        y = self._draw_combat_stats(screen, y)
        y = self._draw_damage_profile(screen, y)
        y = self._draw_legendary_panel(screen, y)
        y = self._draw_section(screen, y, "Lore",
                                  self.stats.lore or
                                  "(No lore recorded.)")
        y = self._draw_section(screen, y, "Tactics",
                                  self.stats.tactics or
                                  "(No tactics recorded.)")
        y = self._draw_section(screen, y, "Loot",
                                  self.stats.loot_table or
                                  "(No loot suggestions.)")
        y = self._draw_section(screen, y, "Habitat",
                                  self.stats.habitat or "(Unknown.)",
                                  short=True)
        y = self._draw_section(screen, y, "Source",
                                  self.stats.sources or "(Unknown.)",
                                  short=True)
        y = self._draw_actions(screen, y, "Actions",
                                  filter_type="action")
        y = self._draw_actions(screen, y, "Legendary Actions",
                                  filter_type="legendary")
        y = self._draw_actions(screen, y, "Lair Actions",
                                  filter_type="lair")
        y = self._draw_features(screen, y)
        self._content_height = (y - (content_top - self.scroll))
        screen.set_clip(prev_clip)

        # Footer with close button
        self.btn_close.rect.x = rect.right - 110
        self.btn_close.rect.y = rect.bottom - 44
        self.btn_close.draw(screen, mp)

    # ------------------------------------------------------------------ #
    def _draw_header(self, screen, rect):
        s = self.stats
        title = s.name
        screen.blit(fonts.body_bold.render(
            title, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, self.y + 14))
        cr_str = (f"CR {s.challenge_rating:g}"
                   if s.challenge_rating else "CR ?")
        sub_bits = [
            f"{s.size} {s.creature_type}",
            cr_str,
            f"{s.xp} XP" if s.xp else "",
            s.alignment or "",
        ]
        sub = "  ·  ".join(x for x in sub_bits if x)
        screen.blit(fonts.small.render(
            sub, True,
            COLORS.get("text_dim", (180, 180, 190))),
            (self.x + 20, self.y + 40))
        # AC / HP / Speed line
        ent = self.entity
        if ent is not None:
            ac_str = f"AC {ent.armor_class}"
            hp_str = f"HP {ent.hp}/{ent.max_hp}"
        else:
            ac_str = f"AC {s.armor_class}"
            hp_str = f"HP {s.hit_points}"
        line = f"{ac_str}   {hp_str}   {_format_speed(s)}"
        screen.blit(fonts.small.render(
            line, True,
            COLORS.get("text_main", (220, 220, 235))),
            (self.x + 20, self.y + 60))
        # Separator
        pygame.draw.line(
            screen, COLORS.get("border", (60, 60, 80)),
            (self.x + 16, self.y + 84),
            (self.x + self.WIDTH - 16, self.y + 84), 1)

    def _draw_combat_stats(self, screen, y):
        s = self.stats
        # Ability block
        screen.blit(fonts.small_bold.render(
            "Ability Scores", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        screen.blit(fonts.small.render(
            _format_abilities(s.abilities), True,
            COLORS.get("text_main", (220, 220, 235))),
            (self.x + 20, y))
        y += 24
        if s.saving_throws:
            saves = "Saves: " + ", ".join(
                f"{k} {'+' if v >= 0 else ''}{v}"
                for k, v in s.saving_throws.items()
            )
            screen.blit(fonts.small.render(
                saves, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 20, y))
            y += 20
        if s.skills:
            skills = "Skills: " + ", ".join(
                f"{k} {'+' if v >= 0 else ''}{v}"
                for k, v in s.skills.items()
            )
            screen.blit(fonts.small.render(
                skills, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 20, y))
            y += 20
        if s.senses:
            screen.blit(fonts.small.render(
                f"Senses: {s.senses}", True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 20, y))
            y += 20
        if s.languages:
            screen.blit(fonts.small.render(
                f"Languages: {s.languages}", True,
                COLORS.get("text_dim", (180, 180, 190))),
                (self.x + 20, y))
            y += 20
        return y + 4

    def _draw_damage_profile(self, screen, y):
        s = self.stats

        def _chip_row(label, items, colour):
            nonlocal y
            if not items:
                return
            x = self.x + 20
            screen.blit(fonts.small_bold.render(
                label, True,
                COLORS.get("text_dim", (180, 180, 190))),
                (x, y))
            x += 130
            for it in items:
                txt = str(it)
                w = fonts.tiny.size(txt)[0] + 14
                chip = pygame.Rect(x, y + 1, w, 20)
                pygame.draw.rect(screen, colour, chip, border_radius=10)
                screen.blit(fonts.tiny.render(
                    txt, True, (20, 20, 30)),
                    (chip.x + 7, chip.y + 3))
                x += w + 6
                if x > self.x + self.WIDTH - 30:
                    y += 22
                    x = self.x + 150
            y += 24
        _chip_row("Immunities:", s.damage_immunities,
                   _COND_COLOR["immunity"])
        _chip_row("Resistances:", s.damage_resistances,
                   _COND_COLOR["resistance"])
        _chip_row("Vulnerabilities:", s.damage_vulnerabilities,
                   _COND_COLOR["vulnerability"])
        _chip_row("Cond. Immun.:", s.condition_immunities,
                   (140, 140, 150))
        return y

    def _draw_legendary_panel(self, screen, y):
        s = self.stats
        if not s.legendary_action_count and not s.legendary_resistance_count:
            return y
        ent = self.entity
        la_left = (ent.legendary_actions_left if ent else
                    s.legendary_action_count)
        lr_left = (ent.legendary_resistances_left if ent else
                    s.legendary_resistance_count)
        bits = []
        if s.legendary_action_count:
            bits.append(f"Legendary Actions: "
                         f"{la_left}/{s.legendary_action_count}")
        if s.legendary_resistance_count:
            bits.append(f"Legendary Resist: "
                         f"{lr_left}/{s.legendary_resistance_count}")
        screen.blit(fonts.small_bold.render(
            "  ·  ".join(bits), True,
            COLORS.get("legendary", (200, 160, 90))),
            (self.x + 20, y))
        return y + 24

    def _draw_section(self, screen, y, label, text, short=False):
        screen.blit(fonts.small_bold.render(
            label, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        lines = _wrap(text, fonts.small, self.WIDTH - 40)
        for line in lines:
            screen.blit(fonts.small.render(
                line, True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 20, y))
            y += 18
            if short and y - (self.y + 90) > 30:
                break
        return y + 6

    def _draw_actions(self, screen, y, label, filter_type):
        s = self.stats
        items = [a for a in s.actions if a.action_type == filter_type]
        if filter_type == "action":
            items = [a for a in s.actions
                      if a.action_type not in (
                          "legendary", "lair")]
        if not items:
            return y
        screen.blit(fonts.small_bold.render(
            label, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        for a in items:
            head = a.name
            if a.is_multiattack:
                head = f"{head} (Multiattack)"
            screen.blit(fonts.small_bold.render(
                head, True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 30, y))
            y += 18
            desc_parts = []
            if a.description:
                desc_parts.append(a.description)
            if a.damage_dice:
                bonus = (f"+{a.damage_bonus}"
                           if a.damage_bonus > 0
                           else (str(a.damage_bonus) if
                                  a.damage_bonus < 0 else ""))
                desc_parts.append(
                    f"Damage: {a.damage_dice}{bonus} "
                    f"{a.damage_type}")
            if a.attack_bonus:
                desc_parts.append(f"Attack: +{a.attack_bonus}")
            if a.range and a.range != 5:
                desc_parts.append(f"Range: {a.range} ft")
            if a.aoe_radius and a.aoe_shape:
                desc_parts.append(
                    f"AoE: {a.aoe_radius} ft {a.aoe_shape}")
            if a.applies_condition:
                desc_parts.append(
                    f"Applies: {a.applies_condition} "
                    f"(DC {a.condition_dc} {a.condition_save})")
            sub = "  ·  ".join(desc_parts)
            for line in _wrap(sub, fonts.tiny, self.WIDTH - 70):
                screen.blit(fonts.tiny.render(
                    line, True,
                    COLORS.get("text_dim", (180, 180, 195))),
                    (self.x + 40, y))
                y += 15
            y += 4
        return y + 6

    def _draw_features(self, screen, y):
        s = self.stats
        if not s.features:
            return y
        screen.blit(fonts.small_bold.render(
            "Features", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        for f in s.features:
            tag = f.feature_type or "passive"
            head = f"{f.name}  ({tag})"
            if f.recharge:
                head += f"  · recharge {f.recharge}"
            if f.uses_per_day > 0:
                head += f"  · {f.uses_per_day}/day"
            screen.blit(fonts.small_bold.render(
                head, True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 30, y))
            y += 18
            for line in _wrap(f.description, fonts.tiny,
                                 self.WIDTH - 70):
                screen.blit(fonts.tiny.render(
                    line, True,
                    COLORS.get("text_dim", (180, 180, 195))),
                    (self.x + 40, y))
                y += 15
            y += 4
        return y
