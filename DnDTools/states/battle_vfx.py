"""Combat VFX — short, code-drawn animated effects shown alongside the
existing FloatingText / ImpactFlash.

Every effect class follows the same protocol:
    update()  — advance one frame; sets life=0 when finished.
    draw(screen, get_screen_pos, grid_size) — render at the current
        frame using the supplied (gx, gy) → (px, py) helper.

All effects are pure pygame draw primitives — no sprites, no asset
files. ``self.life > 0`` means alive, ``<= 0`` means schedule for
removal (battle_state filters them each frame).
"""
from __future__ import annotations

import math

try:
    import pygame  # type: ignore
except ImportError:
    pygame = None

from states.battle_constants import DAMAGE_TYPE_COLORS


def _color_for(damage_type: str) -> tuple:
    return DAMAGE_TYPE_COLORS.get(damage_type, (220, 220, 220))


# --------------------------------------------------------------------- #
# Projectile — an arrow / bolt / spell mote arcing from caster to target
# --------------------------------------------------------------------- #
class Projectile:
    """Linear or arcing projectile from (gx0, gy0) to (gx1, gy1).

    ``style`` tweaks the shape:
        "arrow"   — slim shaft with a head, modest arc.
        "bolt"    — fat magic bolt with glow.
        "stone"   — round rock, gravity arc.
        "mote"    — small fizzling magical sphere, no arc.
    """
    __slots__ = ("gx0", "gy0", "gx1", "gy1", "life", "max_life",
                  "style", "color")

    def __init__(self, gx0, gy0, gx1, gy1, *,
                  style: str = "arrow",
                  damage_type: str = "piercing",
                  color: tuple = None,
                  duration: int = 18):
        self.gx0 = float(gx0)
        self.gy0 = float(gy0)
        self.gx1 = float(gx1)
        self.gy1 = float(gy1)
        self.style = style
        self.color = color if color is not None else _color_for(damage_type)
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def _t(self) -> float:
        if self.max_life <= 0:
            return 1.0
        return 1.0 - max(0, self.life) / self.max_life

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = self._t()
        # Base linear interpolation between start and end (cell centres)
        x0, y0 = get_screen_pos(self.gx0, self.gy0)
        x1, y1 = get_screen_pos(self.gx1, self.gy1)
        cx0 = x0 + grid_size // 2
        cy0 = y0 + grid_size // 2
        cx1 = x1 + grid_size // 2
        cy1 = y1 + grid_size // 2
        cx = cx0 + (cx1 - cx0) * t
        cy = cy0 + (cy1 - cy0) * t
        # Optional arc (pulls the path upward at midflight)
        arc_h = {"arrow": 0.12, "bolt": 0.05, "stone": 0.25,
                  "mote": 0.0}.get(self.style, 0.0)
        if arc_h > 0:
            cy -= arc_h * grid_size * 4 * t * (1 - t)
        cx, cy = int(cx), int(cy)
        # Draw style
        if self.style == "arrow":
            self._draw_arrow(screen, cx, cy, cx1, cy1)
        elif self.style == "bolt":
            self._draw_bolt(screen, cx, cy)
        elif self.style == "stone":
            self._draw_stone(screen, cx, cy)
        else:  # mote / fallback
            self._draw_mote(screen, cx, cy)

    def _draw_arrow(self, screen, cx, cy, cx1, cy1):
        # Direction towards the target so the head points the right way
        dx, dy = cx1 - cx, cy1 - cy
        d = math.hypot(dx, dy) or 1
        ux, uy = dx / d, dy / d
        tail_x = int(cx - ux * 14)
        tail_y = int(cy - uy * 14)
        head_x = int(cx + ux * 4)
        head_y = int(cy + uy * 4)
        pygame.draw.line(screen, (200, 180, 110),
                          (tail_x, tail_y), (head_x, head_y), 2)
        # Head
        pygame.draw.circle(screen, self.color, (head_x, head_y), 3)

    def _draw_bolt(self, screen, cx, cy):
        # Glow halo + bright core
        for r, a in ((10, 60), (7, 120), (4, 200)):
            surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, a), (r + 1, r + 1), r)
            screen.blit(surf, (cx - r - 1, cy - r - 1))

    def _draw_stone(self, screen, cx, cy):
        pygame.draw.circle(screen, (90, 80, 70), (cx, cy), 5)
        pygame.draw.circle(screen, (140, 130, 110), (cx, cy), 5, 1)

    def _draw_mote(self, screen, cx, cy):
        flick = 4 + (self.life % 3)
        surf = pygame.Surface((flick * 4, flick * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, 200),
                            (flick * 2, flick * 2), flick)
        screen.blit(surf, (cx - flick * 2, cy - flick * 2))


# --------------------------------------------------------------------- #
# Beam — a straight ray from caster to target (ray spells, scorching
# ray, eldritch blast, fire breath, etc.)
# --------------------------------------------------------------------- #
class Beam:
    __slots__ = ("gx0", "gy0", "gx1", "gy1", "life", "max_life",
                  "color", "thickness")

    def __init__(self, gx0, gy0, gx1, gy1, *,
                  damage_type: str = "fire",
                  color: tuple = None,
                  thickness: int = 5,
                  duration: int = 12):
        self.gx0 = float(gx0); self.gy0 = float(gy0)
        self.gx1 = float(gx1); self.gy1 = float(gy1)
        self.color = color if color is not None else _color_for(damage_type)
        self.thickness = max(1, int(thickness))
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        x0, y0 = get_screen_pos(self.gx0, self.gy0)
        x1, y1 = get_screen_pos(self.gx1, self.gy1)
        cx0 = x0 + grid_size // 2; cy0 = y0 + grid_size // 2
        cx1 = x1 + grid_size // 2; cy1 = y1 + grid_size // 2
        # Outer glow
        glow_w = self.thickness + int(6 * (1 - t))
        # Approximate by drawing two layered thick lines
        outer_alpha = int(80 * (1 - t))
        outer_col = (*self.color, outer_alpha)
        # pygame.draw.line doesn't accept alpha colors; use a SRCALPHA surface
        w = abs(cx1 - cx0) + glow_w * 2 + 4
        h = abs(cy1 - cy0) + glow_w * 2 + 4
        if w <= 0 or h <= 0:
            return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        ox = min(cx0, cx1) - glow_w - 2
        oy = min(cy0, cy1) - glow_w - 2
        pygame.draw.line(surf, outer_col,
                          (cx0 - ox, cy0 - oy),
                          (cx1 - ox, cy1 - oy), glow_w)
        pygame.draw.line(surf, (*self.color, 230),
                          (cx0 - ox, cy0 - oy),
                          (cx1 - ox, cy1 - oy), self.thickness)
        screen.blit(surf, (ox, oy))


# --------------------------------------------------------------------- #
# SpellAura — pulsing AoE glow at the centre of an area effect
# --------------------------------------------------------------------- #
class SpellAura:
    __slots__ = ("gx", "gy", "radius_cells", "life", "max_life",
                  "color")

    def __init__(self, gx, gy, *,
                  radius_cells: float = 2.0,
                  damage_type: str = "fire",
                  color: tuple = None,
                  duration: int = 30):
        self.gx = float(gx); self.gy = float(gy)
        self.radius_cells = max(0.5, float(radius_cells))
        self.color = color if color is not None else _color_for(damage_type)
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        cx = sx + grid_size // 2
        cy = sy + grid_size // 2
        max_r = int(self.radius_cells * grid_size)
        r = int(max_r * (0.4 + 0.8 * t))
        alpha = int(160 * (1 - t))
        surf = pygame.Surface((max_r * 2 + 4, max_r * 2 + 4), pygame.SRCALPHA)
        # Gradient rings
        for i in range(3):
            rr = max(1, int(r * (1.0 - i * 0.25)))
            aa = max(0, alpha // (i + 1))
            pygame.draw.circle(surf, (*self.color, aa),
                                (max_r + 2, max_r + 2), rr)
        screen.blit(surf, (cx - max_r - 2, cy - max_r - 2))


# --------------------------------------------------------------------- #
# SlashTrail — a quick crescent for melee swings
# --------------------------------------------------------------------- #
class SlashTrail:
    __slots__ = ("gx", "gy", "angle_deg", "life", "max_life",
                  "color", "length_cells")

    def __init__(self, gx, gy, angle_deg=0, *,
                  damage_type: str = "slashing",
                  color: tuple = None,
                  length_cells: float = 1.0,
                  duration: int = 10):
        self.gx = float(gx); self.gy = float(gy)
        self.angle_deg = float(angle_deg)
        self.color = color if color is not None else _color_for(damage_type)
        self.length_cells = max(0.3, float(length_cells))
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        cx = sx + grid_size // 2
        cy = sy + grid_size // 2
        # Sweep arc
        radius = int(self.length_cells * grid_size * 0.5)
        a0 = math.radians(self.angle_deg - 50 + 100 * t)
        alpha = int(220 * (1 - t))
        # Approximate the crescent by a series of small dots
        for k in range(7):
            ka = a0 + (k - 3) * 0.07
            kx = int(cx + radius * math.cos(ka))
            ky = int(cy + radius * math.sin(ka))
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (3, 3),
                                3 - abs(k - 3) // 2)
            screen.blit(surf, (kx - 3, ky - 3))


# --------------------------------------------------------------------- #
# HealAura — a rising green sparkle column over a healed target
# --------------------------------------------------------------------- #
class HealAura:
    __slots__ = ("gx", "gy", "life", "max_life")

    def __init__(self, gx, gy, *, duration: int = 30):
        self.gx = float(gx); self.gy = float(gy)
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        cx = sx + grid_size // 2
        cy = sy + grid_size // 2
        # Floating sparks
        sparks = 5
        col = (160, 255, 180)
        alpha = int(255 * (1 - t))
        surf = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
        for i in range(sparks):
            ang = (i / sparks) * math.tau + t * 4
            rr = grid_size * 0.25 * (0.5 + 0.5 * t)
            sx2 = int(grid_size // 2 + rr * math.cos(ang))
            sy2 = int(grid_size // 2 - grid_size * 0.4 * t
                      + rr * math.sin(ang) * 0.4)
            pygame.draw.circle(surf, (*col, alpha), (sx2, sy2),
                                2 + (i % 2))
        screen.blit(surf, (cx - grid_size // 2, cy - grid_size // 2))


# --------------------------------------------------------------------- #
# Convenience factories — keep the call-sites short.
# --------------------------------------------------------------------- #
def make_attack_vfx(attacker, target, action, *, damage_type: str = ""):
    """Pick the appropriate VFX for an attack given the action's range
    and damage type. ``attacker`` and ``target`` need ``grid_x``,
    ``grid_y``."""
    rng = getattr(action, "range", 5) if action else 5
    damage_type = damage_type or getattr(action, "damage_type", "slashing")
    if rng <= 5:
        return SlashTrail(target.grid_x, target.grid_y,
                           damage_type=damage_type)
    # Choose projectile style: arrows for piercing, stones for
    # bludgeoning, magical motes otherwise.
    style = "arrow"
    if damage_type == "bludgeoning":
        style = "stone"
    elif damage_type in ("fire", "cold", "force", "necrotic", "radiant",
                          "lightning", "thunder", "psychic", "acid", "poison"):
        style = "bolt"
    return Projectile(attacker.grid_x, attacker.grid_y,
                       target.grid_x, target.grid_y,
                       style=style, damage_type=damage_type)


def make_spell_vfx(caster, target, spell):
    """For a spell hit: pick beam / aura / projectile based on the
    spell's shape (single target ray vs AoE)."""
    radius = getattr(spell, "aoe_radius", 0) or 0
    damage_type = getattr(spell, "damage_type", "force") or "force"
    if radius > 0 and target is not None:
        return SpellAura(target.grid_x, target.grid_y,
                          radius_cells=max(1.0, radius / 5.0),
                          damage_type=damage_type)
    if radius > 0 and caster is not None:
        # Self-centred AoE
        return SpellAura(caster.grid_x, caster.grid_y,
                          radius_cells=max(1.0, radius / 5.0),
                          damage_type=damage_type)
    if target is not None and caster is not None:
        return Beam(caster.grid_x, caster.grid_y,
                     target.grid_x, target.grid_y,
                     damage_type=damage_type)
    return None
