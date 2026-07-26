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
# ConeBlast — a dragon's breath, a Burning Hands, a Verimessu sweep.
# --------------------------------------------------------------------- #
class ConeBlast:
    """Filled cone sweeping out from the origin toward a target.

    A breath weapon used to render as a single travelling bolt, which
    told the table nothing about who was inside the 60 ft cone. This
    paints the actual affected wedge, brightest at the mouth, and fades
    it out over the effect's lifetime.
    """
    __slots__ = ("gx0", "gy0", "gx1", "gy1", "length_cells", "half_angle",
                 "life", "max_life", "color")

    def __init__(self, gx0, gy0, gx1, gy1, *,
                 length_cells: float = 6.0,
                 half_angle_deg: float = 30.0,
                 damage_type: str = "fire",
                 color: tuple = None,
                 duration: int = 22):
        self.gx0 = float(gx0); self.gy0 = float(gy0)
        self.gx1 = float(gx1); self.gy1 = float(gy1)
        self.length_cells = max(1.0, float(length_cells))
        self.half_angle = math.radians(max(5.0, float(half_angle_deg)))
        self.color = color if color is not None else _color_for(damage_type)
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
        ox = x0 + grid_size // 2
        oy = y0 + grid_size // 2
        aim = math.atan2((y1 + grid_size // 2) - oy,
                         (x1 + grid_size // 2) - ox)
        # The cone reaches full length in the first third of the effect,
        # then holds and fades — reads as a burst, not a slow wipe.
        grow = min(1.0, t * 3.0)
        reach = self.length_cells * grid_size * grow
        pad = int(reach) + grid_size
        size = pad * 2 + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        fade = max(0.0, 1.0 - max(0.0, (t - 0.35)) / 0.65)
        # Layered wedges: wide dim outer, narrow bright core.
        for layer, (span, a_mul, r_mul) in enumerate((
                (1.0, 0.30, 1.00),
                (0.66, 0.55, 0.92),
                (0.33, 0.85, 0.80))):
            half = self.half_angle * span
            rr = reach * r_mul
            if rr < 2:
                continue
            pts = [(cx, cy)]
            steps = 12
            for i in range(steps + 1):
                a = aim - half + (2 * half) * (i / steps)
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            alpha = int(230 * a_mul * fade)
            if alpha <= 0:
                continue
            pygame.draw.polygon(surf, (*self.color, alpha), pts)
        # Leading edge highlight
        edge_alpha = int(200 * fade)
        if edge_alpha > 0 and reach > 3:
            pts = []
            for i in range(13):
                a = aim - self.half_angle + (2 * self.half_angle) * (i / 12)
                pts.append((cx + reach * math.cos(a), cy + reach * math.sin(a)))
            if len(pts) >= 2:
                pygame.draw.lines(surf, (255, 255, 255, edge_alpha), False,
                                  pts, 2)
        screen.blit(surf, (ox - cx, oy - cy))


# --------------------------------------------------------------------- #
# Explosion — Fireball, Meteor Swarm, Sielujen purkaus.
# --------------------------------------------------------------------- #
class Explosion:
    """Expanding fireball with a shockwave ring and flying embers."""
    __slots__ = ("gx", "gy", "radius_cells", "life", "max_life", "color",
                 "_embers")

    def __init__(self, gx, gy, *,
                 radius_cells: float = 4.0,
                 damage_type: str = "fire",
                 color: tuple = None,
                 duration: int = 26):
        self.gx = float(gx); self.gy = float(gy)
        self.radius_cells = max(0.5, float(radius_cells))
        self.color = color if color is not None else _color_for(damage_type)
        self.life = int(duration)
        self.max_life = int(duration)
        # Deterministic ember directions — no random, so the effect is
        # identical every replay and testable.
        self._embers = tuple(
            (i * 2.399963, 0.55 + 0.45 * ((i * 7) % 5) / 4.0)
            for i in range(14))

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        cx0 = sx + grid_size // 2
        cy0 = sy + grid_size // 2
        max_r = int(self.radius_cells * grid_size)
        size = max_r * 2 + grid_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2

        # Fireball body: snaps out fast, then fades.
        body_r = int(max_r * min(1.0, t * 2.6))
        fade = max(0.0, 1.0 - max(0.0, (t - 0.3)) / 0.7)
        if body_r > 1 and fade > 0:
            pygame.draw.circle(surf, (*self.color, int(70 * fade)),
                               (cx, cy), body_r)
            pygame.draw.circle(surf, (*self.color, int(150 * fade)),
                               (cx, cy), int(body_r * 0.7))
            hot = tuple(min(255, c + 70) for c in self.color)
            pygame.draw.circle(surf, (*hot, int(210 * fade)),
                               (cx, cy), int(body_r * 0.35))
        # Shockwave ring outruns the body.
        ring_r = int(max_r * min(1.15, 0.2 + t * 1.3))
        ring_a = int(220 * max(0.0, 1.0 - t))
        if ring_r > 2 and ring_a > 0:
            pygame.draw.circle(surf, (255, 255, 255, ring_a), (cx, cy),
                               ring_r, max(1, int(4 * (1 - t)) + 1))
        # Embers thrown outward.
        for ang, speed in self._embers:
            er = max_r * speed * t * 1.15
            ex = int(cx + er * math.cos(ang))
            ey = int(cy + er * math.sin(ang))
            ea = int(230 * max(0.0, 1.0 - t))
            if ea <= 0:
                continue
            pygame.draw.circle(surf, (*self.color, ea), (ex, ey),
                               max(1, int(3 * (1 - t)) + 1))
        screen.blit(surf, (cx0 - cx, cy0 - cy))


# --------------------------------------------------------------------- #
# LightningArc — a jagged branching bolt.
# --------------------------------------------------------------------- #
class LightningArc:
    """Zig-zag bolt with side branches, flashing then fading."""
    __slots__ = ("gx0", "gy0", "gx1", "gy1", "life", "max_life", "color",
                 "_seed")

    def __init__(self, gx0, gy0, gx1, gy1, *,
                 damage_type: str = "lightning",
                 color: tuple = None,
                 duration: int = 14,
                 seed: int = 7):
        self.gx0 = float(gx0); self.gy0 = float(gy0)
        self.gx1 = float(gx1); self.gy1 = float(gy1)
        self.color = color if color is not None else _color_for(damage_type)
        self.life = int(duration)
        self.max_life = int(duration)
        self._seed = int(seed)

    def update(self):
        self.life -= 1

    def _jag(self, x0, y0, x1, y1, segments, amp):
        """Deterministic zig-zag polyline between two screen points."""
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        pts = []
        for i in range(segments + 1):
            f = i / segments
            # Triangle-ish pseudo-noise from the seed; zero at both ends.
            wob = math.sin(f * 9.0 + self._seed) * math.sin(f * math.pi)
            px = x0 + dx * f + nx * wob * amp
            py = y0 + dy * f + ny * wob * amp
            pts.append((px, py))
        return pts

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        x0, y0 = get_screen_pos(self.gx0, self.gy0)
        x1, y1 = get_screen_pos(self.gx1, self.gy1)
        ax = x0 + grid_size // 2; ay = y0 + grid_size // 2
        bx = x1 + grid_size // 2; by = y1 + grid_size // 2
        pad = grid_size
        left = min(ax, bx) - pad; top = min(ay, by) - pad
        w = abs(bx - ax) + pad * 2; h = abs(by - ay) + pad * 2
        if w <= 0 or h <= 0:
            return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        amp = grid_size * 0.35
        main = self._jag(ax - left, ay - top, bx - left, by - top, 10, amp)
        alpha = int(255 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        pygame.draw.lines(surf, (*self.color, alpha // 3), False, main, 7)
        pygame.draw.lines(surf, (*self.color, alpha), False, main, 3)
        pygame.draw.lines(surf, (255, 255, 255, alpha), False, main, 1)
        # Branches off the middle third
        for i in (3, 6):
            if i >= len(main) - 1:
                continue
            px, py = main[i]
            qx, qy = main[i + 1]
            bxr = px + (qx - px) * 2.2 + amp * (0.6 if i == 3 else -0.7)
            byr = py + (qy - py) * 2.2 - amp * 0.5
            pygame.draw.line(surf, (*self.color, alpha),
                             (int(px), int(py)), (int(bxr), int(byr)), 2)
        screen.blit(surf, (left, top))


# --------------------------------------------------------------------- #
# FrostShards — cold burst: crystalline spikes and a chill ring.
# --------------------------------------------------------------------- #
class FrostShards:
    __slots__ = ("gx", "gy", "life", "max_life", "color", "radius_cells")

    def __init__(self, gx, gy, *, radius_cells: float = 1.0,
                 damage_type: str = "cold", color: tuple = None,
                 duration: int = 22):
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
        max_r = int(self.radius_cells * grid_size)
        size = max_r * 2 + grid_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(230 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        grow = min(1.0, t * 2.2)
        for i in range(8):
            ang = i * math.tau / 8 + 0.2
            rr = max_r * grow * (0.7 + 0.3 * (i % 2))
            tipx = cx + rr * math.cos(ang)
            tipy = cy + rr * math.sin(ang)
            halfw = max(2, int(grid_size * 0.09))
            px = -math.sin(ang) * halfw
            py = math.cos(ang) * halfw
            pygame.draw.polygon(surf, (*self.color, alpha),
                                [(cx + px, cy + py), (tipx, tipy),
                                 (cx - px, cy - py)])
        pygame.draw.circle(surf, (230, 250, 255, alpha // 2), (cx, cy),
                           int(max_r * grow), 2)
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


# --------------------------------------------------------------------- #
# DrainMotes — life/necrotic siphon: motes stream target → caster.
# --------------------------------------------------------------------- #
class DrainMotes:
    """Motes flowing from the victim back into the drainer.

    Direction is the whole point: this is how the table sees that the
    vampire just healed itself off somebody.
    """
    __slots__ = ("gx0", "gy0", "gx1", "gy1", "life", "max_life", "color")

    def __init__(self, gx_from, gy_from, gx_to, gy_to, *,
                 damage_type: str = "necrotic",
                 color: tuple = None, duration: int = 26):
        self.gx0 = float(gx_from); self.gy0 = float(gy_from)
        self.gx1 = float(gx_to); self.gy1 = float(gy_to)
        self.color = color if color is not None else _color_for(damage_type)
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
        ax = x0 + grid_size // 2; ay = y0 + grid_size // 2
        bx = x1 + grid_size // 2; by = y1 + grid_size // 2
        pad = grid_size
        left = min(ax, bx) - pad; top = min(ay, by) - pad
        w = abs(bx - ax) + pad * 2; h = abs(by - ay) + pad * 2
        if w <= 0 or h <= 0:
            return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        motes = 6
        for i in range(motes):
            f = (t * 1.4 + i / motes) % 1.0
            swirl = math.sin(f * math.tau + i) * grid_size * 0.22
            px = ax + dx * f + nx * swirl - left
            py = ay + dy * f + ny * swirl - top
            a = int(235 * (1.0 - abs(f - 0.5) * 0.8) * max(0.0, 1.0 - t))
            if a <= 0:
                continue
            pygame.draw.circle(surf, (*self.color, a), (int(px), int(py)),
                               max(2, int(grid_size * 0.07)))
        screen.blit(surf, (left, top))


# --------------------------------------------------------------------- #
# RadiantPillar — a column of holy light dropping onto the target.
# --------------------------------------------------------------------- #
class RadiantPillar:
    __slots__ = ("gx", "gy", "life", "max_life", "color")

    def __init__(self, gx, gy, *, damage_type: str = "radiant",
                 color: tuple = None, duration: int = 24):
        self.gx = float(gx); self.gy = float(gy)
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
        height = grid_size * 4
        size_w = grid_size * 2
        surf = pygame.Surface((size_w, height + grid_size), pygame.SRCALPHA)
        bx = size_w // 2
        by = height
        alpha = int(200 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        drop = min(1.0, t * 2.5)
        top_y = int(height * (1.0 - drop))
        for half, a_mul in ((grid_size * 0.45, 0.28),
                            (grid_size * 0.28, 0.55),
                            (grid_size * 0.12, 1.0)):
            pygame.draw.polygon(
                surf, (*self.color, int(alpha * a_mul)),
                [(bx - half * 0.5, top_y), (bx + half * 0.5, top_y),
                 (bx + half, by), (bx - half, by)])
        # Ground glow
        pygame.draw.ellipse(surf, (*self.color, int(alpha * 0.6)),
                            pygame.Rect(bx - grid_size * 0.5, by - 6,
                                        grid_size, 14))
        screen.blit(surf, (cx - bx, cy - by))


# --------------------------------------------------------------------- #
# PsychicRipple — concentric distortion rings, no bright core.
# --------------------------------------------------------------------- #
class PsychicRipple:
    __slots__ = ("gx", "gy", "life", "max_life", "color", "radius_cells")

    def __init__(self, gx, gy, *, radius_cells: float = 1.5,
                 damage_type: str = "psychic", color: tuple = None,
                 duration: int = 26):
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
        max_r = int(self.radius_cells * grid_size)
        size = max_r * 2 + grid_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for i in range(3):
            f = (t * 1.3 - i * 0.22)
            if f <= 0 or f > 1:
                continue
            r = int(max_r * f)
            a = int(220 * (1.0 - f))
            if r > 1 and a > 0:
                pygame.draw.circle(surf, (*self.color, a), (cx, cy), r, 2)
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


# --------------------------------------------------------------------- #
# PoisonBubbles / AcidSplash — sickly rising blobs.
# --------------------------------------------------------------------- #
class PoisonBubbles:
    __slots__ = ("gx", "gy", "life", "max_life", "color", "radius_cells")

    def __init__(self, gx, gy, *, radius_cells: float = 1.0,
                 damage_type: str = "poison", color: tuple = None,
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
        max_r = int(self.radius_cells * grid_size)
        size = max_r * 2 + grid_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(200 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        pygame.draw.circle(surf, (*self.color, alpha // 4), (cx, cy),
                           int(max_r * min(1.0, t * 2.0)))
        for i in range(9):
            ang = i * 2.399963
            f = (t * 1.5 + i / 9.0) % 1.0
            rr = max_r * 0.8 * f
            bx = int(cx + rr * math.cos(ang))
            by = int(cy + rr * math.sin(ang) - max_r * 0.35 * f)
            pygame.draw.circle(surf, (*self.color, alpha), (bx, by),
                               max(2, int(grid_size * 0.09 * (1 - f * 0.5))))
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


# --------------------------------------------------------------------- #
# ThunderRing — a pure shockwave, no colour fill.
# --------------------------------------------------------------------- #
class ThunderRing:
    __slots__ = ("gx", "gy", "life", "max_life", "color", "radius_cells")

    def __init__(self, gx, gy, *, radius_cells: float = 2.0,
                 damage_type: str = "thunder", color: tuple = None,
                 duration: int = 18):
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
        max_r = int(self.radius_cells * grid_size)
        size = max_r * 2 + grid_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for i, delay in enumerate((0.0, 0.18, 0.36)):
            f = t - delay
            if f <= 0 or f > 1:
                continue
            r = int(max_r * f)
            a = int(200 * (1.0 - f))
            if r > 1 and a > 0:
                pygame.draw.circle(surf, (*self.color, a), (cx, cy), r,
                                   max(1, 4 - i))
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


# --------------------------------------------------------------------- #
# CritStar / MissSpark — outcome feedback at a glance.
# --------------------------------------------------------------------- #
class CritStar:
    """Bright starburst so a critical hit is unmistakable."""
    __slots__ = ("gx", "gy", "life", "max_life", "color")

    def __init__(self, gx, gy, *, damage_type: str = "slashing",
                 color: tuple = None, duration: int = 22):
        self.gx = float(gx); self.gy = float(gy)
        self.color = color if color is not None else (255, 240, 150)
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        size = grid_size * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(255 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        reach = grid_size * (0.5 + 1.0 * min(1.0, t * 2.0))
        for i in range(8):
            ang = i * math.tau / 8
            spike = reach * (1.0 if i % 2 == 0 else 0.55)
            pygame.draw.line(surf, (*self.color, alpha), (cx, cy),
                             (int(cx + spike * math.cos(ang)),
                              int(cy + spike * math.sin(ang))),
                             max(2, int(4 * (1 - t)) + 1))
        pygame.draw.circle(surf, (255, 255, 255, alpha), (cx, cy),
                           max(2, int(grid_size * 0.16 * (1 - t))))
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


class MissSpark:
    """Glancing deflection — small grey sparks skidding off the target."""
    __slots__ = ("gx", "gy", "angle_deg", "life", "max_life")

    def __init__(self, gx, gy, angle_deg: float = 0.0, *, duration: int = 14):
        self.gx = float(gx); self.gy = float(gy)
        self.angle_deg = float(angle_deg)
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        size = grid_size * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(220 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        base = math.radians(self.angle_deg)
        for i in range(4):
            ang = base + (i - 1.5) * 0.28
            rr = grid_size * 0.55 * t
            ex = int(cx + rr * math.cos(ang))
            ey = int(cy + rr * math.sin(ang))
            pygame.draw.line(surf, (225, 225, 235, alpha), (cx, cy),
                             (ex, ey), 2)
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


# --------------------------------------------------------------------- #
# TeleportPuff / SummonRune / ConditionMark — non-damage feedback.
# --------------------------------------------------------------------- #
class TeleportPuff:
    """Two puffs: one where the creature left, one where it arrived."""
    __slots__ = ("gx", "gy", "life", "max_life", "color", "inward")

    def __init__(self, gx, gy, *, inward: bool = False,
                 color: tuple = (170, 150, 240), duration: int = 20):
        self.gx = float(gx); self.gy = float(gy)
        self.inward = bool(inward)
        self.color = color
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        f = (1.0 - t) if self.inward else t
        sx, sy = get_screen_pos(self.gx, self.gy)
        size = grid_size * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(220 * max(0.0, 1.0 - t))
        if alpha <= 0:
            return
        for i in range(7):
            ang = i * math.tau / 7 + t * 3.0
            rr = grid_size * 0.55 * f
            px = int(cx + rr * math.cos(ang))
            py = int(cy + rr * math.sin(ang))
            pygame.draw.circle(surf, (*self.color, alpha), (px, py),
                               max(2, int(grid_size * 0.1 * (1 - f))))
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


class SummonRune:
    """Rotating summoning circle under a newly arrived creature."""
    __slots__ = ("gx", "gy", "life", "max_life", "color", "cells")

    def __init__(self, gx, gy, *, cells: float = 1.0,
                 color: tuple = (150, 220, 255), duration: int = 34):
        self.gx = float(gx); self.gy = float(gy)
        self.cells = max(0.6, float(cells))
        self.color = color
        self.life = int(duration)
        self.max_life = int(duration)

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos, grid_size):
        if pygame is None or self.life <= 0:
            return
        t = 1.0 - max(0, self.life) / self.max_life
        sx, sy = get_screen_pos(self.gx, self.gy)
        r = int(self.cells * grid_size * 0.55)
        size = r * 2 + 8
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        alpha = int(230 * (1.0 - abs(t - 0.4) * 1.4))
        alpha = max(0, min(255, alpha))
        if alpha <= 0 or r < 2:
            return
        spin = t * 2.4
        pygame.draw.circle(surf, (*self.color, alpha), (cx, cy), r, 2)
        pygame.draw.circle(surf, (*self.color, alpha), (cx, cy),
                           int(r * 0.62), 1)
        for i in range(6):
            ang = spin + i * math.tau / 6
            x1 = cx + int(r * 0.62 * math.cos(ang))
            y1 = cy + int(r * 0.62 * math.sin(ang))
            x2 = cx + int(r * math.cos(ang))
            y2 = cy + int(r * math.sin(ang))
            pygame.draw.line(surf, (*self.color, alpha), (x1, y1), (x2, y2), 2)
        screen.blit(surf, (sx + grid_size // 2 - cx,
                           sy + grid_size // 2 - cy))


class ConditionMark:
    """Short badge that rises off a token when a condition lands, so the
    table sees WHAT changed and not just that a number appeared."""
    __slots__ = ("gx", "gy", "label", "color", "life", "max_life")

    def __init__(self, gx, gy, label: str, color: tuple = (255, 220, 120),
                 *, duration: int = 46):
        self.gx = float(gx); self.gy = float(gy)
        self.label = str(label)[:4].upper()
        self.color = color
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
        cy = sy + grid_size // 2 - int(grid_size * (0.35 + 0.5 * t))
        alpha = int(255 * max(0.0, 1.0 - max(0.0, t - 0.6) / 0.4))
        if alpha <= 0:
            return
        try:
            from ui.components import fonts
            txt = fonts.small_bold.render(self.label, True, self.color)
        except Exception:
            return
        pad = 4
        box = pygame.Surface((txt.get_width() + pad * 2,
                              txt.get_height() + pad), pygame.SRCALPHA)
        pygame.draw.rect(box, (10, 10, 16, min(210, alpha)),
                         box.get_rect(), border_radius=3)
        pygame.draw.rect(box, (*self.color, alpha), box.get_rect(), 1,
                         border_radius=3)
        txt.set_alpha(alpha)
        box.blit(txt, (pad, pad // 2))
        screen.blit(box, (cx - box.get_width() // 2, cy))


# --------------------------------------------------------------------- #
# Convenience factories — keep the call-sites short.
# --------------------------------------------------------------------- #
# Damage type → burst class for area / touch effects. Keeping this in one
# table means a new spell picks up the right look for free.
_BURST_BY_TYPE = {
    "fire": Explosion,
    "cold": FrostShards,
    "lightning": Explosion,
    "thunder": ThunderRing,
    "force": Explosion,
    "necrotic": PoisonBubbles,
    "poison": PoisonBubbles,
    "acid": PoisonBubbles,
    "radiant": RadiantPillar,
    "psychic": PsychicRipple,
}

# Damage types whose single-target hit reads better as a jagged arc than a
# straight beam.
_ARC_TYPES = ("lightning",)

# Types that visibly steal something from the victim.
_DRAIN_TYPES = ("necrotic",)


def _num(value, default=0.0) -> float:
    """Coerce a possibly-missing / non-numeric field to a float.

    Action and SpellInfo always carry these fields, but the VFX layer is
    called from the middle of combat resolution and must never be the
    thing that crashes a turn because a stub or hand-built action was
    missing an attribute.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _burst_at(gx, gy, damage_type, radius_cells):
    """Build the best burst effect for a damage type at a point."""
    cls = _BURST_BY_TYPE.get(damage_type)
    if cls is RadiantPillar:
        return RadiantPillar(gx, gy, damage_type=damage_type)
    if cls is None:
        return SpellAura(gx, gy, radius_cells=radius_cells,
                         damage_type=damage_type or "force")
    return cls(gx, gy, radius_cells=radius_cells,
               damage_type=damage_type or "force")


def make_cone_vfx(attacker, target, *, length_ft: float,
                  damage_type: str = "fire"):
    """Breath weapon / cone spell. A 60 ft cone used to render as a single
    travelling bolt, which told the table nothing about who was caught."""
    if attacker is None or target is None:
        return None
    return ConeBlast(attacker.grid_x, attacker.grid_y,
                     target.grid_x, target.grid_y,
                     length_cells=max(1.0, length_ft / 5.0),
                     damage_type=damage_type or "fire")


def make_attack_vfx(attacker, target, action, *, damage_type: str = ""):
    """Pick the appropriate VFX for an attack given the action's shape,
    range and damage type. ``attacker`` and ``target`` need ``grid_x``,
    ``grid_y``."""
    rng = _num(getattr(action, "range", 5), 5) if action else 5
    damage_type = damage_type or getattr(action, "damage_type", "slashing")
    if not isinstance(damage_type, str):
        damage_type = "slashing"
    radius_ft = _num(getattr(action, "aoe_radius", 0))
    raw_shape = getattr(action, "aoe_shape", "")
    shape = raw_shape.lower() if isinstance(raw_shape, str) else ""

    # Area actions first — a breath weapon is not a projectile.
    if radius_ft > 0:
        if shape in ("cone", "line"):
            vfx = make_cone_vfx(attacker, target, length_ft=radius_ft,
                                damage_type=damage_type)
            if vfx is not None:
                return vfx
        centre = target if target is not None else attacker
        if centre is not None:
            # A self-centred burst (range 0) erupts from the creature.
            if rng == 0 and attacker is not None:
                centre = attacker
            return _burst_at(centre.grid_x, centre.grid_y, damage_type,
                             max(1.0, radius_ft / 5.0))

    if rng <= 5:
        # Melee: a drain bite should look like a drain, not a sword swipe.
        if damage_type in _DRAIN_TYPES and attacker is not None:
            return DrainMotes(target.grid_x, target.grid_y,
                              attacker.grid_x, attacker.grid_y,
                              damage_type=damage_type)
        angle = 0.0
        if attacker is not None:
            angle = math.degrees(math.atan2(
                attacker.grid_y - target.grid_y,
                attacker.grid_x - target.grid_x))
        return SlashTrail(target.grid_x, target.grid_y, angle,
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
    """For a spell hit: pick the effect from the spell's shape and damage
    type — cone, burst, arc, drain or beam."""
    radius = _num(getattr(spell, "aoe_radius", 0))
    raw_shape = getattr(spell, "aoe_shape", "")
    shape = raw_shape.lower() if isinstance(raw_shape, str) else ""
    damage_type = getattr(spell, "damage_type", "force") or "force"
    if not isinstance(damage_type, str):
        damage_type = "force"

    if radius > 0 and shape in ("cone", "line") and caster is not None \
            and target is not None:
        return make_cone_vfx(caster, target, length_ft=radius,
                             damage_type=damage_type)
    if radius > 0 and target is not None:
        return _burst_at(target.grid_x, target.grid_y, damage_type,
                         max(1.0, radius / 5.0))
    if radius > 0 and caster is not None:
        # Self-centred AoE
        return _burst_at(caster.grid_x, caster.grid_y, damage_type,
                         max(1.0, radius / 5.0))
    if target is not None and caster is not None:
        if damage_type in _ARC_TYPES:
            return LightningArc(caster.grid_x, caster.grid_y,
                                target.grid_x, target.grid_y,
                                damage_type=damage_type)
        if damage_type in _DRAIN_TYPES:
            return DrainMotes(target.grid_x, target.grid_y,
                              caster.grid_x, caster.grid_y,
                              damage_type=damage_type)
        if damage_type == "radiant":
            return RadiantPillar(target.grid_x, target.grid_y,
                                 damage_type=damage_type)
        return Beam(caster.grid_x, caster.grid_y,
                     target.grid_x, target.grid_y,
                     damage_type=damage_type)
    return None


def make_outcome_vfx(attacker, target, outcome: str, *,
                     damage_type: str = "slashing"):
    """Crit / miss feedback so the result is readable without the log."""
    if target is None:
        return None
    if outcome == "crit":
        return CritStar(target.grid_x, target.grid_y,
                        damage_type=damage_type)
    if outcome == "miss":
        angle = 0.0
        if attacker is not None:
            angle = math.degrees(math.atan2(
                target.grid_y - attacker.grid_y,
                target.grid_x - attacker.grid_x))
        return MissSpark(target.grid_x, target.grid_y, angle)
    return None


def make_condition_vfx(target, condition: str):
    """Badge that rises off a token when a condition actually lands."""
    if target is None or not condition:
        return None
    try:
        from states.battle_constants import CONDITION_BADGES
        label, colour = CONDITION_BADGES.get(
            condition, (condition[:4].upper(), (255, 220, 120)))
    except Exception:
        label, colour = condition[:4].upper(), (255, 220, 120)
    return ConditionMark(target.grid_x, target.grid_y, label, colour)
