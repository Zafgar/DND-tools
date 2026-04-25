"""Procedural battle-tile decoration — code-drawn art that turns the
plain coloured rectangles into something readable at a glance.

Pure drawing logic (no fonts, no labels, no game state) so it can be
unit-tested with a small surface and asserted to render *something*
without crashing. The renderer in battle_renderer calls
``decorate_tile(surface, terrain_type, rw, rh, base_color, ticks)``
after the base fill but before its label/border pass.
"""
from __future__ import annotations

import math

# pygame is imported lazily inside the painters so this module can be
# imported (and its dispatch tables inspected) in a headless test
# environment without pygame installed.
try:
    import pygame  # type: ignore
except ImportError:
    pygame = None  # noqa


# --------------------------------------------------------------------- #
# Colour helpers
# --------------------------------------------------------------------- #
def _shade(color, factor: float):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def _alpha(color, a: int):
    return (color[0], color[1], color[2], max(0, min(255, int(a))))


# --------------------------------------------------------------------- #
# Per-type painters
# --------------------------------------------------------------------- #
def _paint_wall(surf, w, h, base):
    """Brick courses with mortar lines."""
    brick_w = max(8, w // 4)
    brick_h = max(6, h // 4)
    light = _shade(base, 1.15)
    dark = _shade(base, 0.65)
    surf.fill(_alpha(base, 230))
    row = 0
    y = 0
    while y < h:
        offset = (brick_w // 2) if row % 2 else 0
        x = -offset
        while x < w:
            rect = pygame.Rect(x + 1, y + 1, brick_w - 2, brick_h - 2)
            pygame.draw.rect(surf, light, rect, border_radius=2)
            pygame.draw.rect(surf, dark, rect, 1, border_radius=2)
            x += brick_w
        y += brick_h
        row += 1


def _paint_tree(surf, w, h, base):
    """Trunk + layered canopy circles."""
    surf.fill(_alpha((20, 30, 12), 80))
    cx, cy = w // 2, h // 2
    trunk_w = max(2, w // 8)
    trunk = pygame.Rect(cx - trunk_w // 2, int(h * 0.55), trunk_w,
                          int(h * 0.4))
    pygame.draw.rect(surf, (90, 60, 30), trunk)
    # Three canopy layers, dark → bright
    for i, factor in enumerate((0.7, 0.95, 1.2)):
        r = int(min(w, h) * (0.45 - i * 0.08))
        col = _shade(base, factor)
        pygame.draw.circle(surf, col, (cx, cy - i * 3), r)


def _paint_rock(surf, w, h, base):
    """Hexagonal-ish rock with highlights."""
    surf.fill(_alpha(base, 120))
    cx, cy = w // 2, h // 2
    r_outer = min(w, h) // 2 - 2
    pts = []
    for i in range(6):
        ang = -math.pi / 2 + i * math.pi / 3
        rr = r_outer * (0.85 + 0.15 * (i % 2))
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pygame.draw.polygon(surf, base, pts)
    pygame.draw.polygon(surf, _shade(base, 0.7), pts, 2)
    # Highlight streak
    pygame.draw.line(surf, _shade(base, 1.4),
                      (cx - r_outer // 2, cy - r_outer // 3),
                      (cx + r_outer // 3, cy - r_outer // 4), 2)


def _paint_water(surf, w, h, base, ticks):
    """Wavy bands."""
    surf.fill(_alpha(base, 200))
    light = _shade(base, 1.4)
    t = (ticks / 600.0)
    for i in range(3):
        y = int(h * (0.2 + 0.3 * i) + 3 * math.sin(t + i))
        pygame.draw.line(surf, light, (0, y), (w, y), 1)


def _paint_lava(surf, w, h, base, ticks):
    """Orange base + flickering yellow cracks."""
    surf.fill(_alpha((180, 50, 0), 230))
    cracks_y = [h // 4, h // 2, 3 * h // 4]
    for cy in cracks_y:
        wob = int(2 * math.sin(ticks * 0.01 + cy))
        pygame.draw.line(surf, (255, 220, 90),
                          (0, cy + wob), (w, cy - wob), 2)


def _paint_fire(surf, w, h, base, ticks):
    """Animated flame triangle."""
    surf.fill(_alpha((30, 5, 0), 120))
    cx = w // 2
    flicker = int(2 * math.sin(ticks * 0.012))
    flame = [
        (cx, h // 4 - flicker),
        (cx - w // 3, int(h * 0.85)),
        (cx + w // 3, int(h * 0.85)),
    ]
    pygame.draw.polygon(surf, (255, 140, 40), flame)
    inner = [
        (cx, h // 2 - flicker // 2),
        (cx - w // 5, int(h * 0.78)),
        (cx + w // 5, int(h * 0.78)),
    ]
    pygame.draw.polygon(surf, (255, 230, 100), inner)


def _paint_door(surf, w, h, base):
    """Wooden door — vertical planks + handle."""
    surf.fill(_alpha(base, 220))
    plank_w = max(4, w // 4)
    light = _shade(base, 1.2)
    for x in range(0, w, plank_w):
        pygame.draw.rect(surf, light,
                          pygame.Rect(x + 1, 1, plank_w - 2, h - 2),
                          1, border_radius=2)
    # Handle
    pygame.draw.circle(surf, (200, 200, 60),
                        (int(w * 0.75), h // 2), max(2, w // 12))


def _paint_pillar(surf, w, h, base):
    """Stone column."""
    surf.fill(_alpha((30, 30, 35), 120))
    cx = w // 2
    body = pygame.Rect(int(w * 0.25), int(h * 0.1),
                        int(w * 0.5), int(h * 0.8))
    pygame.draw.rect(surf, base, body, border_radius=4)
    pygame.draw.rect(surf, _shade(base, 0.6), body, 2, border_radius=4)
    # Cap + base
    cap = pygame.Rect(int(w * 0.2), int(h * 0.05),
                       int(w * 0.6), int(h * 0.1))
    pygame.draw.rect(surf, _shade(base, 1.2), cap)
    base_r = pygame.Rect(int(w * 0.2), int(h * 0.85),
                          int(w * 0.6), int(h * 0.1))
    pygame.draw.rect(surf, _shade(base, 1.2), base_r)


def _paint_table(surf, w, h, base):
    """Wood plank table top."""
    surf.fill(_alpha(base, 200))
    light = _shade(base, 1.15)
    pygame.draw.rect(surf, base,
                      pygame.Rect(2, h // 4, w - 4, h // 2),
                      border_radius=2)
    for i in range(1, 3):
        y = h // 4 + i * (h // 6)
        pygame.draw.line(surf, light, (3, y), (w - 3, y), 1)


def _paint_crate(surf, w, h, base):
    """Wood crate with X-bracing."""
    surf.fill(_alpha(base, 230))
    pygame.draw.rect(surf, _shade(base, 0.7),
                      pygame.Rect(1, 1, w - 2, h - 2), 2)
    pygame.draw.line(surf, _shade(base, 0.7),
                      (1, 1), (w - 1, h - 1), 1)
    pygame.draw.line(surf, _shade(base, 0.7),
                      (w - 1, 1), (1, h - 1), 1)


def _paint_barrel(surf, w, h, base):
    """Round barrel: ellipse + horizontal bands."""
    surf.fill(_alpha((20, 20, 20), 0))   # transparent
    body = pygame.Rect(2, 4, w - 4, h - 8)
    pygame.draw.ellipse(surf, base, body)
    pygame.draw.ellipse(surf, _shade(base, 0.7), body, 2)
    for i in range(1, 3):
        y = 4 + i * (h - 8) // 3
        pygame.draw.line(surf, _shade(base, 0.6), (3, y), (w - 3, y), 1)


def _paint_chasm(surf, w, h, base):
    """Dark gradient + jagged edges."""
    for y in range(h):
        t = y / max(1, h - 1)
        col = (int(20 * (1 - t) + 5 * t),
                int(20 * (1 - t) + 5 * t),
                int(30 * (1 - t) + 10 * t))
        pygame.draw.line(surf, col, (0, y), (w, y))
    # Jagged top + bottom edges
    edge = (60, 50, 40)
    pts_top = [(x, 1 + (3 if x % 6 < 3 else 0)) for x in range(0, w + 1, 3)]
    pts_bot = [(x, h - 2 - (3 if x % 6 < 3 else 0)) for x in range(0, w + 1, 3)]
    if len(pts_top) >= 2:
        pygame.draw.lines(surf, edge, False, pts_top, 1)
    if len(pts_bot) >= 2:
        pygame.draw.lines(surf, edge, False, pts_bot, 1)


def _paint_spikes(surf, w, h, base):
    """Pit lined with metal spikes."""
    surf.fill(_alpha((40, 35, 30), 220))
    spike_count = max(3, w // 8)
    for i in range(spike_count):
        cx = (i + 0.5) * w / spike_count
        pts = [(cx - 3, h - 1), (cx, h * 0.25), (cx + 3, h - 1)]
        pygame.draw.polygon(surf, (180, 180, 200), pts)


def _paint_difficult(surf, w, h, base):
    """Brush / mud strokes."""
    surf.fill(_alpha(base, 180))
    light = _shade(base, 1.3)
    for i in range(5):
        x = (i + 1) * w // 6
        pygame.draw.line(surf, light, (x - 4, h // 4),
                          (x + 4, 3 * h // 4), 1)


def _paint_platform(surf, w, h, base):
    """Raised platform — pseudo-3D top."""
    surf.fill(_alpha(base, 220))
    light = _shade(base, 1.3)
    dark = _shade(base, 0.6)
    pygame.draw.polygon(surf, light, [(0, 0), (w, 0), (w - 4, 4), (4, 4)])
    pygame.draw.polygon(surf, dark, [(0, 0), (4, 4), (4, h - 1), (0, h - 1)])
    pygame.draw.polygon(surf, dark, [(w, 0), (w - 4, 4), (w - 4, h - 1),
                                       (w, h - 1)])


def _paint_ice(surf, w, h, base):
    """Pale blue with crystalline cracks."""
    surf.fill(_alpha(base, 220))
    pygame.draw.line(surf, (240, 250, 255),
                      (w // 4, h // 4), (3 * w // 4, 3 * h // 4), 1)
    pygame.draw.line(surf, (240, 250, 255),
                      (3 * w // 4, h // 4), (w // 4, 3 * h // 4), 1)


# --------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------- #
_PAINTERS = {
    "wall":          _paint_wall,
    "tree":          _paint_tree,
    "rock":          _paint_rock,
    "house":         _paint_wall,
    "pillar":        _paint_pillar,
    "table":         _paint_table,
    "crate":         _paint_crate,
    "barrel":        _paint_barrel,
    "door":          _paint_door,
    "door_locked":   _paint_door,
    "spikes":        _paint_spikes,
    "ice":           _paint_ice,
    "mud":           _paint_difficult,
    "rubble":        _paint_difficult,
    "difficult":     _paint_difficult,
    "platform_5":    _paint_platform,
    "platform_10":   _paint_platform,
    "platform_15":   _paint_platform,
    "platform_20":   _paint_platform,
    "roof":          _paint_platform,
}

_PAINTERS_TICKS = {
    "water":      _paint_water,
    "deep_water": _paint_water,
    "lava":       _paint_lava,
    "lava_chasm": _paint_lava,
    "fire":       _paint_fire,
}

_PAINTERS_NO_BASE = {
    "chasm":     _paint_chasm,
    "chasm_10":  _paint_chasm,
    "chasm_15":  _paint_chasm,
    "chasm_20":  _paint_chasm,
}


def has_painter(terrain_type: str) -> bool:
    """True when there's a procedural painter for this terrain type.
    Cheap dictionary lookup, no rendering — safe to call without pygame."""
    return (terrain_type in _PAINTERS
            or terrain_type in _PAINTERS_TICKS
            or terrain_type in _PAINTERS_NO_BASE)


def decorate_tile(surface, terrain_type: str, rw: int, rh: int,
                    base_color, ticks: int = 0) -> bool:
    """Paint procedural decoration for ``terrain_type`` onto ``surface``.

    Returns True if a decorator was applied; the caller may skip its
    own flat fill in that case. Falls back to a flat-coloured fill
    when the terrain type has no painter."""
    if pygame is None:
        return False
    if terrain_type in _PAINTERS_NO_BASE:
        _PAINTERS_NO_BASE[terrain_type](surface, rw, rh, base_color)
        return True
    if terrain_type in _PAINTERS_TICKS:
        _PAINTERS_TICKS[terrain_type](surface, rw, rh, base_color, ticks)
        return True
    if terrain_type in _PAINTERS:
        _PAINTERS[terrain_type](surface, rw, rh, base_color)
        return True
    return False
