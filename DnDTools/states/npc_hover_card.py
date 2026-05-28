"""Phase 41 — NPC hover mini-card.

A lightweight, reusable tooltip that any view (world map, town view,
NPC list, battle roster, organisation panel) can pop up when the DM
hovers an NPC reference.  Shows a portrait thumbnail + the compact
field set from :func:`data.npc_graph.mini_card_content`.

Efficiency notes:
  * The content dict is recomputed only when the *target NPC changes*
    (``show`` caches by npc id), not every frame.
  * The scaled portrait surface is cached per portrait path so we
    don't re-load / re-scale the image each frame.
  * Drawing clamps the card inside the screen so it never spills off
    an edge near the mouse.

Usage:
    card = NpcHoverCard()
    # each frame while hovering:
    card.show(world, npc, campaign)         # cheap if same npc
    card.draw(screen, mouse_pos)
    # when not hovering:
    card.hide()
"""
from __future__ import annotations

from typing import Dict, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import fonts
from data.npc_graph import mini_card_content


_THUMB = 56


class NpcHoverCard:
    WIDTH = 280

    def __init__(self):
        self._npc_id = ""
        self._content: Optional[Dict] = None
        self._visible = False
        # portrait_path -> scaled Surface (or None if load failed)
        self._portrait_cache: Dict[str, Optional[pygame.Surface]] = {}

    # ------------------------------------------------------------------ #
    def show(self, world, npc, campaign=None) -> None:
        """Set the card's target NPC. Recomputes content only when the
        target actually changes (so calling it every hover-frame is
        cheap)."""
        if npc is None:
            self.hide()
            return
        if npc.id != self._npc_id or self._content is None:
            self._npc_id = npc.id
            self._content = mini_card_content(world, npc, campaign)
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    @property
    def is_visible(self) -> bool:
        return self._visible

    # ------------------------------------------------------------------ #
    def _portrait_surface(self, path: str) -> Optional[pygame.Surface]:
        if not path:
            return None
        if path in self._portrait_cache:
            return self._portrait_cache[path]
        surf = None
        try:
            raw = pygame.image.load(path)
            surf = pygame.transform.smoothscale(raw, (_THUMB, _THUMB))
        except Exception:
            surf = None
        self._portrait_cache[path] = surf
        return surf

    def _estimate_height(self) -> int:
        c = self._content or {}
        h = 12 + _THUMB + 8
        for key in ("occupation", "faction", "location",
                      "organisation"):
            if c.get(key):
                h += 16
        h += 18 * min(len(c.get("links", [])), 3)
        if c.get("link_count", 0) > 3:
            h += 16
        return h + 10

    # ------------------------------------------------------------------ #
    def draw(self, screen, mouse_pos) -> None:
        if not self._visible or not self._content:
            return
        c = self._content
        mx, my = mouse_pos
        w = self.WIDTH
        h = self._estimate_height()
        # Clamp inside the screen, offset from cursor.
        x = mx + 18
        y = my + 12
        if x + w > SCREEN_WIDTH:
            x = mx - w - 18
        if y + h > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - h - 8
        x = max(4, x)
        y = max(4, y)

        rect = pygame.Rect(x, y, w, h)
        # Drop shadow + panel
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 120))
        screen.blit(shadow, (x + 3, y + 3))
        pygame.draw.rect(screen, COLORS.get("bg_dark", (24, 24, 32)),
                          rect, border_radius=8)
        border = (COLORS.get("danger", (220, 100, 90))
                   if not c.get("alive", True)
                   else COLORS.get("border_light", (130, 130, 160)))
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)

        # Portrait
        port = self._portrait_surface(c.get("portrait_path", ""))
        px, py = x + 10, y + 10
        if port is not None:
            screen.blit(port, (px, py))
        else:
            box = pygame.Rect(px, py, _THUMB, _THUMB)
            pygame.draw.rect(screen, COLORS.get("panel_dark",
                                                  (40, 40, 56)),
                              box, border_radius=6)
            initials = "".join(
                wd[0].upper()
                for wd in (c.get("name") or "?").split()[:2])
            screen.blit(fonts.body_bold.render(
                initials, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (px + _THUMB // 2 - 10, py + _THUMB // 2 - 10))

        # Name + title
        tx = px + _THUMB + 10
        name = c.get("name", "")
        if not c.get("alive", True):
            name += "  †"
        screen.blit(fonts.body_bold.render(
            name[:24], True,
            COLORS.get("text_bright", (240, 240, 250))),
            (tx, y + 10))
        ty = y + 30
        if c.get("title"):
            screen.blit(fonts.tiny.render(
                c["title"][:30], True,
                COLORS.get("legendary", (200, 170, 90))),
                (tx, ty))
            ty += 14
        if c.get("identity"):
            screen.blit(fonts.tiny.render(
                c["identity"][:30], True,
                COLORS.get("text_dim", (180, 180, 195))),
                (tx, ty))
            ty += 14

        # Body lines under portrait
        by = y + 10 + _THUMB + 6
        line_x = x + 12

        def _line(label, val, colour):
            nonlocal by
            if not val:
                return
            screen.blit(fonts.small.render(
                f"{label}: {val}"[:42], True, colour),
                (line_x, by))
            by += 16
        _line("Ammatti", c.get("occupation"),
                COLORS.get("text_main", (220, 220, 235)))
        _line("Faktio", c.get("faction"),
                COLORS.get("text_main", (220, 220, 235)))
        _line("Sijainti", c.get("location"),
                COLORS.get("text_dim", (180, 180, 195)))
        if c.get("organisation"):
            org_str = c["organisation"]
            if c.get("org_rank"):
                org_str += f" ({c['org_rank']})"
            _line("Org", org_str,
                    COLORS.get("legendary", (200, 170, 90)))

        # Top links
        for link in c.get("links", [])[:3]:
            screen.blit(fonts.tiny.render(
                f"  • {link}"[:46], True,
                COLORS.get("accent", (140, 200, 240))),
                (line_x, by))
            by += 15
        if c.get("link_count", 0) > 3:
            screen.blit(fonts.tiny.render(
                f"  • +{c['link_count'] - 3} more links…", True,
                COLORS.get("text_dim", (160, 160, 175))),
                (line_x, by))
