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
    """Orange base + crawling yellow cracks.

    The cracks used to see-saw around the tile centre, which meant the
    middle column never moved and a big lava field looked frozen. They
    now travel as a wave so every column animates.
    """
    surf.fill(_alpha((180, 50, 0), 230))
    t = ticks * 0.004
    for i, cy in enumerate((h // 4, h // 2, 3 * h // 4)):
        pts = []
        for x in range(0, w + 1, 2):
            y = cy + 2.5 * math.sin(x * 0.25 + t + i * 1.7)
            pts.append((x, int(y)))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (255, 220, 90), False, pts, 2)


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
# Architecture & furniture
# --------------------------------------------------------------------- #
def _paint_stairs_up(surf, w, h, base):
    """Steps receding upward — light edge on each tread."""
    surf.fill(_alpha(_shade(base, 0.8), 220))
    steps = 4
    for i in range(steps):
        inset = int(i * (min(w, h) * 0.11))
        rect = pygame.Rect(inset, inset, w - inset * 2, h - inset * 2)
        if rect.width <= 2 or rect.height <= 2:
            break
        pygame.draw.rect(surf, _shade(base, 0.9 + i * 0.14), rect)
        pygame.draw.line(surf, _shade(base, 1.5),
                         (rect.left, rect.top), (rect.right, rect.top), 1)


def _paint_stairs_down(surf, w, h, base):
    """Same treads, but the centre goes dark — it reads as descending."""
    surf.fill(_alpha(_shade(base, 1.1), 220))
    steps = 4
    for i in range(steps):
        inset = int(i * (min(w, h) * 0.11))
        rect = pygame.Rect(inset, inset, w - inset * 2, h - inset * 2)
        if rect.width <= 2 or rect.height <= 2:
            break
        pygame.draw.rect(surf, _shade(base, 1.0 - i * 0.2), rect)
        pygame.draw.line(surf, _shade(base, 0.5),
                         (rect.left, rect.bottom - 1),
                         (rect.right, rect.bottom - 1), 1)


def _paint_ladder(surf, w, h, base):
    """Two rails and rungs."""
    surf.fill(_alpha((30, 24, 16), 90))
    rail = _shade((150, 110, 60), 1.0)
    lx, rx = int(w * 0.3), int(w * 0.7)
    pygame.draw.line(surf, rail, (lx, 0), (lx, h), max(2, w // 12))
    pygame.draw.line(surf, rail, (rx, 0), (rx, h), max(2, w // 12))
    for i in range(4):
        y = int(h * (0.15 + i * 0.23))
        pygame.draw.line(surf, _shade(rail, 1.3), (lx, y), (rx, y),
                         max(1, w // 16))


def _paint_bridge(surf, w, h, base):
    """Rope bridge: planks across, rails along the edges."""
    surf.fill(_alpha((18, 18, 24), 140))
    plank = (150, 115, 70)
    for i in range(5):
        y = int(h * (0.12 + i * 0.19))
        pygame.draw.rect(surf, _shade(plank, 0.9 + 0.1 * (i % 2)),
                         pygame.Rect(2, y, w - 4, max(2, h // 9)))
    pygame.draw.line(surf, (110, 90, 60), (1, 0), (1, h), 2)
    pygame.draw.line(surf, (110, 90, 60), (w - 2, 0), (w - 2, h), 2)


def _paint_cover_half(surf, w, h, base):
    """Waist-high barricade — half-height slab with a shadow line."""
    surf.fill(_alpha(base, 60))
    top = int(h * 0.45)
    slab = pygame.Rect(1, top, w - 2, h - top - 1)
    pygame.draw.rect(surf, _shade(base, 1.05), slab, border_radius=2)
    pygame.draw.line(surf, _shade(base, 1.5),
                     (slab.left, slab.top), (slab.right, slab.top), 2)
    pygame.draw.rect(surf, _shade(base, 0.6), slab, 1, border_radius=2)


def _paint_cover_3q(surf, w, h, base):
    """Three-quarter cover — taller slab plus a firing notch."""
    surf.fill(_alpha(base, 60))
    top = int(h * 0.2)
    slab = pygame.Rect(1, top, w - 2, h - top - 1)
    pygame.draw.rect(surf, _shade(base, 1.05), slab, border_radius=2)
    pygame.draw.line(surf, _shade(base, 1.5),
                     (slab.left, slab.top), (slab.right, slab.top), 2)
    notch = pygame.Rect(int(w * 0.4), top, max(2, w // 6),
                        max(2, int(h * 0.2)))
    pygame.draw.rect(surf, _shade(base, 0.45), notch)
    pygame.draw.rect(surf, _shade(base, 0.6), slab, 1, border_radius=2)


def _paint_portcullis(surf, w, h, base):
    """Iron grid with spiked bottom."""
    surf.fill(_alpha((24, 24, 28), 200))
    iron = (130, 135, 145)
    for i in range(4):
        x = int(w * (0.15 + i * 0.23))
        pygame.draw.line(surf, iron, (x, 0), (x, h - 3), 2)
    for i in range(3):
        y = int(h * (0.2 + i * 0.3))
        pygame.draw.line(surf, _shade(iron, 0.8), (0, y), (w, y), 2)
    for i in range(4):
        x = int(w * (0.15 + i * 0.23))
        pygame.draw.polygon(surf, _shade(iron, 1.3),
                            [(x - 3, h - 4), (x, h - 1), (x + 3, h - 4)])


def _paint_altar(surf, w, h, base):
    """Stone block with a carved sigil and a lit candle either side."""
    surf.fill(_alpha(_shade(base, 0.55), 160))
    block = pygame.Rect(int(w * 0.12), int(h * 0.3),
                        int(w * 0.76), int(h * 0.55))
    pygame.draw.rect(surf, _shade(base, 1.05), block, border_radius=2)
    pygame.draw.rect(surf, _shade(base, 0.6), block, 1, border_radius=2)
    # top slab
    pygame.draw.rect(surf, _shade(base, 1.35),
                     pygame.Rect(int(w * 0.06), int(h * 0.24),
                                 int(w * 0.88), max(3, int(h * 0.12))),
                     border_radius=2)
    # sigil
    pygame.draw.circle(surf, (220, 200, 120),
                       (w // 2, int(h * 0.58)), max(2, min(w, h) // 9), 1)
    for sx in (int(w * 0.16), int(w * 0.84)):
        pygame.draw.line(surf, (240, 235, 200), (sx, int(h * 0.24)),
                         (sx, int(h * 0.1)), 2)
        pygame.draw.circle(surf, (255, 210, 110), (sx, int(h * 0.08)),
                           max(1, w // 18))


def _paint_statue(surf, w, h, base):
    """Plinth plus a hooded silhouette."""
    surf.fill(_alpha(_shade(base, 0.5), 130))
    plinth = pygame.Rect(int(w * 0.18), int(h * 0.78),
                         int(w * 0.64), int(h * 0.2))
    pygame.draw.rect(surf, _shade(base, 0.85), plinth)
    pygame.draw.line(surf, _shade(base, 1.4),
                     (plinth.left, plinth.top), (plinth.right, plinth.top), 1)
    body = [(w * 0.5, h * 0.14), (w * 0.72, h * 0.78),
            (w * 0.28, h * 0.78)]
    pygame.draw.polygon(surf, _shade(base, 1.15), body)
    pygame.draw.circle(surf, _shade(base, 1.35),
                       (w // 2, int(h * 0.2)), max(2, min(w, h) // 9))


def _paint_throne(surf, w, h, base):
    """High-backed seat with a gilded crest."""
    surf.fill(_alpha(_shade(base, 0.45), 150))
    back = pygame.Rect(int(w * 0.22), int(h * 0.1),
                       int(w * 0.56), int(h * 0.6))
    pygame.draw.rect(surf, _shade(base, 1.1), back, border_radius=3)
    seat = pygame.Rect(int(w * 0.14), int(h * 0.6),
                       int(w * 0.72), int(h * 0.28))
    pygame.draw.rect(surf, _shade(base, 0.9), seat, border_radius=2)
    pygame.draw.line(surf, (225, 195, 100),
                     (back.left + 2, back.top + 2),
                     (back.right - 2, back.top + 2), 2)
    pygame.draw.circle(surf, (235, 205, 110),
                       (w // 2, back.top + 6), max(2, w // 14))


def _paint_bookshelf(surf, w, h, base):
    """Shelves of coloured spines."""
    surf.fill(_alpha(_shade(base, 0.7), 220))
    spine_cols = [(150, 60, 50), (60, 90, 140), (140, 130, 60),
                  (70, 120, 70), (120, 70, 130)]
    shelves = 3
    sh = max(4, h // shelves)
    for s in range(shelves):
        y = s * sh
        pygame.draw.line(surf, _shade(base, 1.4), (0, y + sh - 1),
                         (w, y + sh - 1), 1)
        x = 2
        i = s
        while x < w - 2:
            bw = max(2, w // 8)
            pygame.draw.rect(surf, spine_cols[i % len(spine_cols)],
                             pygame.Rect(x, y + 2, bw - 1, sh - 4))
            x += bw
            i += 1


def _paint_brazier(surf, w, h, base):
    """Bowl on a tripod with embers."""
    surf.fill(_alpha((26, 20, 14), 90))
    cx = w // 2
    pygame.draw.line(surf, (90, 80, 70), (cx, int(h * 0.55)),
                     (cx - w // 5, h - 2), 2)
    pygame.draw.line(surf, (90, 80, 70), (cx, int(h * 0.55)),
                     (cx + w // 5, h - 2), 2)
    bowl = pygame.Rect(int(w * 0.22), int(h * 0.4),
                       int(w * 0.56), max(3, int(h * 0.2)))
    pygame.draw.ellipse(surf, (120, 100, 80), bowl)
    pygame.draw.ellipse(surf, (255, 170, 60),
                        pygame.Rect(bowl.left + 2, bowl.top - 2,
                                    bowl.width - 4, max(3, bowl.height)))
    pygame.draw.circle(surf, (255, 230, 140),
                       (cx, int(h * 0.34)), max(2, w // 10))


def _paint_cage(surf, w, h, base):
    """Bars on all four sides."""
    surf.fill(_alpha((30, 30, 34), 120))
    iron = (140, 140, 150)
    for i in range(4):
        x = int(w * (0.12 + i * 0.25))
        pygame.draw.line(surf, iron, (x, 2), (x, h - 2), 2)
    pygame.draw.rect(surf, _shade(iron, 0.8),
                     pygame.Rect(0, 0, w, h), 2)
    pygame.draw.line(surf, iron, (0, h // 2), (w, h // 2), 1)


def _paint_pit(surf, w, h, base):
    """Open hole — dark ellipse with a lip."""
    surf.fill(_alpha(_shade(base, 0.9), 150))
    lip = pygame.Rect(2, 2, w - 4, h - 4)
    pygame.draw.ellipse(surf, (40, 34, 28), lip)
    pygame.draw.ellipse(surf, (12, 10, 14),
                        pygame.Rect(5, 5, w - 10, h - 10))
    pygame.draw.arc(surf, _shade(base, 1.4), lip, 3.6, 5.8, 2)


# --------------------------------------------------------------------- #
# Natural features
# --------------------------------------------------------------------- #
def _paint_stalactite(surf, w, h, base):
    """Cones hanging from the top of the tile."""
    surf.fill(_alpha(_shade(base, 0.75), 130))
    for i, fx in enumerate((0.25, 0.55, 0.8)):
        cx = int(w * fx)
        depth = int(h * (0.75 - i * 0.18))
        pygame.draw.polygon(surf, _shade(base, 1.1 + 0.1 * i),
                            [(cx - max(2, w // 10), 0),
                             (cx + max(2, w // 10), 0), (cx, depth)])
    pygame.draw.line(surf, _shade(base, 1.5), (0, 1), (w, 1), 2)


def _paint_mushroom_giant(surf, w, h, base):
    """Thick stalk and a wide glowing cap."""
    surf.fill(_alpha((22, 30, 26), 110))
    cx = w // 2
    stalk_w = max(3, w // 6)
    pygame.draw.rect(surf, (215, 205, 180),
                     pygame.Rect(cx - stalk_w // 2, int(h * 0.42),
                                 stalk_w, int(h * 0.55)))
    cap = pygame.Rect(int(w * 0.08), int(h * 0.16),
                      int(w * 0.84), int(h * 0.42))
    pygame.draw.ellipse(surf, _shade(base, 1.0), cap)
    pygame.draw.ellipse(surf, _shade(base, 1.45),
                        pygame.Rect(cap.left + 3, cap.top + 2,
                                    cap.width - 6, max(3, cap.height // 2)))
    for fx in (0.3, 0.5, 0.72):
        pygame.draw.circle(surf, (200, 255, 220),
                           (int(w * fx), int(h * 0.3)), max(1, w // 20))


def _paint_mushroom_patch(surf, w, h, base):
    """A scatter of small caps."""
    surf.fill(_alpha((24, 32, 26), 90))
    for fx, fy, r in ((0.25, 0.7, 0.11), (0.5, 0.55, 0.14),
                      (0.75, 0.72, 0.1), (0.38, 0.82, 0.08)):
        cx, cy = int(w * fx), int(h * fy)
        rr = max(2, int(min(w, h) * r))
        pygame.draw.line(surf, (210, 200, 175), (cx, cy),
                         (cx, cy + rr + 2), 1)
        pygame.draw.circle(surf, _shade(base, 1.1), (cx, cy), rr)
        pygame.draw.circle(surf, _shade(base, 1.5), (cx, cy - 1), rr // 2)


def _paint_web(surf, w, h, base):
    """Radial strands plus two connecting rings."""
    surf.fill(_alpha((230, 230, 240), 45))
    cx, cy = w // 2, h // 2
    strand = (235, 235, 245)
    for i in range(8):
        ang = i * math.pi / 4
        pygame.draw.line(surf, strand, (cx, cy),
                         (cx + math.cos(ang) * w, cy + math.sin(ang) * h), 1)
    for f in (0.3, 0.6):
        r = int(min(w, h) * f)
        if r > 1:
            pygame.draw.circle(surf, strand, (cx, cy), r, 1)


def _paint_moss(surf, w, h, base):
    """Soft clumps of green."""
    surf.fill(_alpha(base, 130))
    for fx, fy in ((0.2, 0.3), (0.55, 0.2), (0.75, 0.55),
                   (0.35, 0.7), (0.65, 0.85)):
        pygame.draw.circle(surf, _shade(base, 1.25),
                           (int(w * fx), int(h * fy)),
                           max(2, min(w, h) // 7))
    for fx, fy in ((0.4, 0.45), (0.8, 0.3)):
        pygame.draw.circle(surf, _shade(base, 0.75),
                           (int(w * fx), int(h * fy)),
                           max(1, min(w, h) // 10))


def _paint_crystal(surf, w, h, base):
    """Cluster of faceted shards."""
    surf.fill(_alpha(_shade(base, 0.4), 110))
    for fx, fy, fs in ((0.3, 0.9, 0.7), (0.55, 0.95, 1.0),
                       (0.75, 0.9, 0.6)):
        bx, by = int(w * fx), int(h * fy)
        hh = int(h * 0.55 * fs)
        half = max(2, int(w * 0.11 * fs))
        pts = [(bx, by), (bx - half, by - hh // 2), (bx, by - hh),
               (bx + half, by - hh // 2)]
        pygame.draw.polygon(surf, _shade(base, 1.1), pts)
        pygame.draw.line(surf, _shade(base, 1.7), (bx, by - hh),
                         (bx, by), 1)
        pygame.draw.polygon(surf, _shade(base, 0.7), pts, 1)


def _paint_sand(surf, w, h, base):
    """Dune ripples."""
    surf.fill(_alpha(base, 210))
    light = _shade(base, 1.18)
    dark = _shade(base, 0.85)
    for i in range(4):
        y = int(h * (0.15 + i * 0.24))
        pts = [(x, y + int(2 * math.sin(x * 0.35 + i)))
               for x in range(0, w + 1, 2)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, light, False, pts, 1)
            pygame.draw.lines(surf, dark, False,
                              [(x, y + 1) for x, y in pts], 1)


def _paint_coral(surf, w, h, base):
    """Branching fans."""
    surf.fill(_alpha((30, 70, 90), 120))
    for fx in (0.28, 0.55, 0.78):
        bx = int(w * fx)
        pygame.draw.line(surf, _shade(base, 1.1), (bx, h - 1),
                         (bx, int(h * 0.45)), 2)
        for d in (-1, 1):
            pygame.draw.line(surf, _shade(base, 1.35),
                             (bx, int(h * 0.6)),
                             (bx + d * w // 7, int(h * 0.35)), 2)
            pygame.draw.circle(surf, _shade(base, 1.5),
                               (bx + d * w // 7, int(h * 0.35)),
                               max(1, w // 18))


def _paint_shipwreck(surf, w, h, base):
    """Broken hull ribs."""
    surf.fill(_alpha((36, 46, 58), 150))
    hull = [(1, int(h * 0.85)), (int(w * 0.2), int(h * 0.35)),
            (int(w * 0.85), int(h * 0.3)), (w - 2, int(h * 0.9))]
    pygame.draw.polygon(surf, _shade((110, 80, 50), 1.0), hull)
    pygame.draw.polygon(surf, _shade((70, 50, 32), 1.0), hull, 2)
    for i in range(3):
        x = int(w * (0.3 + i * 0.2))
        pygame.draw.line(surf, (85, 62, 40), (x, int(h * 0.32)),
                         (x, int(h * 0.85)), 2)


def _paint_mast(surf, w, h, base):
    """Upright spar with a furled sail."""
    surf.fill(_alpha((36, 46, 58), 110))
    cx = w // 2
    pygame.draw.line(surf, (120, 90, 55), (cx, 1), (cx, h - 1),
                     max(2, w // 8))
    pygame.draw.line(surf, (100, 75, 45), (int(w * 0.2), int(h * 0.3)),
                     (int(w * 0.8), int(h * 0.3)), 2)
    pygame.draw.polygon(surf, (215, 210, 195),
                        [(cx, int(h * 0.32)), (int(w * 0.78), int(h * 0.62)),
                         (int(w * 0.22), int(h * 0.62))])


# --------------------------------------------------------------------- #
# Graves & ritual
# --------------------------------------------------------------------- #
def _paint_tombstone(surf, w, h, base):
    """Rounded headstone on a mound."""
    surf.fill(_alpha(_shade((60, 70, 55), 1.0), 120))
    stone = pygame.Rect(int(w * 0.26), int(h * 0.28),
                        int(w * 0.48), int(h * 0.6))
    pygame.draw.rect(surf, _shade(base, 1.05), stone,
                     border_top_left_radius=max(2, w // 4),
                     border_top_right_radius=max(2, w // 4))
    pygame.draw.rect(surf, _shade(base, 0.6), stone, 1,
                     border_top_left_radius=max(2, w // 4),
                     border_top_right_radius=max(2, w // 4))
    pygame.draw.line(surf, _shade(base, 0.55),
                     (w // 2, int(h * 0.42)), (w // 2, int(h * 0.66)), 1)
    pygame.draw.line(surf, _shade(base, 0.55),
                     (int(w * 0.38), int(h * 0.5)),
                     (int(w * 0.62), int(h * 0.5)), 1)


def _paint_sarcophagus(surf, w, h, base):
    """Stone coffin lid with a carved figure."""
    surf.fill(_alpha(_shade(base, 0.5), 150))
    lid = pygame.Rect(int(w * 0.14), int(h * 0.16),
                      int(w * 0.72), int(h * 0.7))
    pygame.draw.rect(surf, _shade(base, 1.05), lid, border_radius=3)
    pygame.draw.rect(surf, _shade(base, 0.62), lid, 1, border_radius=3)
    pygame.draw.circle(surf, _shade(base, 1.35),
                       (w // 2, int(h * 0.32)), max(2, min(w, h) // 10))
    pygame.draw.line(surf, _shade(base, 1.3), (w // 2, int(h * 0.42)),
                     (w // 2, int(h * 0.76)), 2)
    pygame.draw.line(surf, _shade(base, 1.3),
                     (int(w * 0.34), int(h * 0.52)),
                     (int(w * 0.66), int(h * 0.52)), 2)


def _paint_grave_open(surf, w, h, base):
    """Dug-out rectangle with spoil heaps."""
    surf.fill(_alpha(_shade((58, 66, 52), 1.0), 140))
    hole = pygame.Rect(int(w * 0.2), int(h * 0.22),
                       int(w * 0.6), int(h * 0.62))
    pygame.draw.rect(surf, (48, 38, 28), hole)
    pygame.draw.rect(surf, (18, 14, 12),
                     pygame.Rect(hole.left + 2, hole.top + 2,
                                 hole.width - 4, hole.height - 4))
    for fx in (0.1, 0.9):
        pygame.draw.circle(surf, (74, 58, 40),
                           (int(w * fx), int(h * 0.5)),
                           max(2, min(w, h) // 8))


def _paint_magic_circle(surf, w, h, base):
    """Concentric runic rings."""
    surf.fill(_alpha(base, 70))
    cx, cy = w // 2, h // 2
    glow = _shade(base, 1.6)
    for f in (0.46, 0.32, 0.16):
        r = int(min(w, h) * f)
        if r > 1:
            pygame.draw.circle(surf, glow, (cx, cy), r, 1)
    for i in range(6):
        ang = i * math.pi / 3
        r1 = int(min(w, h) * 0.18)
        r2 = int(min(w, h) * 0.44)
        pygame.draw.line(surf, glow,
                         (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                         (cx + math.cos(ang) * r2, cy + math.sin(ang) * r2), 1)


def _paint_teleport_pad(surf, w, h, base):
    """Bright ring with an inward chevron."""
    surf.fill(_alpha(base, 90))
    cx, cy = w // 2, h // 2
    glow = _shade(base, 1.7)
    r = int(min(w, h) * 0.4)
    if r > 1:
        pygame.draw.circle(surf, glow, (cx, cy), r, 2)
        pygame.draw.circle(surf, glow, (cx, cy), max(1, r // 2), 1)
    pygame.draw.polygon(surf, glow,
                        [(cx, cy - r // 2), (cx - r // 3, cy + r // 3),
                         (cx + r // 3, cy + r // 3)], 1)


def _paint_leyline(surf, w, h, base):
    """A bright current running through the tile."""
    surf.fill(_alpha(base, 60))
    glow = _shade(base, 1.7)
    pts = [(x, int(h * 0.5 + math.sin(x * 0.4) * h * 0.22))
           for x in range(0, w + 1, 2)]
    if len(pts) >= 2:
        pygame.draw.lines(surf, _shade(base, 1.2), False, pts, 3)
        pygame.draw.lines(surf, glow, False, pts, 1)


def _paint_antimagic(surf, w, h, base):
    """Dead grey hatching — magic simply stops here."""
    surf.fill(_alpha((70, 70, 78), 150))
    line = (120, 120, 130)
    step = max(4, w // 5)
    for i in range(-h, w + h, step):
        pygame.draw.line(surf, line, (i, 0), (i + h, h), 1)
        pygame.draw.line(surf, line, (i + h, 0), (i, h), 1)


# --------------------------------------------------------------------- #
# Spell effects & clouds (animated where it helps readability)
# --------------------------------------------------------------------- #
def _paint_cloud(surf, w, h, base, ticks, alpha=150, blobs=5):
    """Shared drifting-cloud body used by fog / gas / storm tiles."""
    surf.fill(_alpha(base, alpha // 3))
    t = ticks / 500.0
    for i in range(blobs):
        fx = 0.2 + 0.15 * i
        cx = int(w * fx + math.sin(t + i) * w * 0.08)
        cy = int(h * (0.3 + 0.12 * (i % 3)) + math.cos(t + i) * h * 0.06)
        r = max(3, int(min(w, h) * (0.26 - 0.02 * (i % 3))))
        pygame.draw.circle(surf, _alpha(_shade(base, 1.15), alpha),
                           (cx, cy), r)


def _paint_fog(surf, w, h, base, ticks):
    _paint_cloud(surf, w, h, (205, 208, 214), ticks, alpha=170)


def _paint_fog_light(surf, w, h, base, ticks):
    _paint_cloud(surf, w, h, (210, 214, 220), ticks, alpha=95, blobs=4)


def _paint_darkness(surf, w, h, base):
    """Not a cloud — a hole in the light."""
    surf.fill(_alpha((6, 5, 10), 235))
    for i in range(3):
        r = int(min(w, h) * (0.45 - i * 0.1))
        if r > 1:
            pygame.draw.circle(surf, (14 + i * 6, 12 + i * 5, 24 + i * 8),
                               (w // 2, h // 2), r, 1)


def _paint_dim_light(surf, w, h, base):
    """Half-lit: a soft gradient wash."""
    for y in range(h):
        a = int(120 * (y / max(1, h - 1)))
        pygame.draw.line(surf, (30, 30, 44, a), (0, y), (w, y))


def _paint_stinking_cloud(surf, w, h, base, ticks):
    _paint_cloud(surf, w, h, (120, 150, 70), ticks, alpha=175)


def _paint_cloudkill(surf, w, h, base, ticks):
    _paint_cloud(surf, w, h, (100, 170, 90), ticks, alpha=195)
    pygame.draw.circle(surf, (60, 120, 50), (w // 2, h // 2),
                       max(2, min(w, h) // 6), 1)


def _paint_poison(surf, w, h, base, ticks):
    """Bubbling green pool."""
    surf.fill(_alpha((70, 130, 60), 210))
    for i in range(4):
        cx = int(w * (0.2 + 0.2 * i))
        cy = int(h * 0.6 + math.sin(ticks * 0.008 + i) * h * 0.2)
        pygame.draw.circle(surf, (150, 220, 120), (cx, cy),
                           max(1, w // 14))


def _paint_acid(surf, w, h, base, ticks):
    """Yellow-green with etching pits."""
    surf.fill(_alpha((160, 190, 40), 215))
    for i in range(5):
        cx = int(w * (0.15 + 0.18 * i))
        cy = int(h * (0.3 + 0.14 * (i % 3)) +
                 math.sin(ticks * 0.01 + i) * 2)
        pygame.draw.circle(surf, (90, 110, 20), (cx, cy),
                           max(1, w // 16))
    pygame.draw.line(surf, (220, 250, 120), (0, int(h * 0.75)),
                     (w, int(h * 0.7)), 1)


def _paint_sleet_storm(surf, w, h, base, ticks):
    """Slanted sleet over a pale wash."""
    surf.fill(_alpha((170, 195, 215), 140))
    off = int(ticks * 0.08) % max(4, w // 3)
    for i in range(-h, w + h, max(4, w // 4)):
        x = i + off
        pygame.draw.line(surf, (235, 245, 255), (x, 0),
                         (x - h // 2, h), 1)


def _paint_wall_fire(surf, w, h, base, ticks):
    """A curtain of flame, not a campfire."""
    surf.fill(_alpha((60, 12, 0), 170))
    cols = max(3, w // 6)
    for i in range(cols):
        cx = int((i + 0.5) * w / cols)
        top = int(h * 0.12 + h * 0.14 * abs(math.sin(ticks * 0.004 + i)))
        pygame.draw.polygon(surf, (255, 130, 30),
                            [(cx, top), (cx - w // (cols * 2) - 1, h),
                             (cx + w // (cols * 2) + 1, h)])
        pygame.draw.polygon(surf, (255, 225, 120),
                            [(cx, int(top + h * 0.35)),
                             (cx - max(1, w // (cols * 3)), h),
                             (cx + max(1, w // (cols * 3)), h)])


def _paint_wall_wind(surf, w, h, base, ticks):
    """Vertical shear lines."""
    surf.fill(_alpha((190, 205, 220), 70))
    off = int(ticks * 0.06) % max(3, h)
    for i in range(4):
        x = int(w * (0.15 + i * 0.23))
        for seg in range(0, h, max(4, h // 4)):
            y = (seg + off) % h
            pygame.draw.line(surf, (240, 248, 255), (x, y),
                             (x, min(h, y + max(2, h // 8))), 2)


def _paint_wall_thorns(surf, w, h, base):
    """Interlocking barbed stems."""
    surf.fill(_alpha((40, 60, 34), 190))
    stem = (70, 105, 55)
    barb = (185, 205, 160)
    for i in range(4):
        x = int(w * (0.12 + i * 0.25))
        pygame.draw.line(surf, stem, (x, h), (x + w // 10, 0), 2)
        for j in range(3):
            y = int(h * (0.25 + j * 0.28))
            bx = x + int((h - y) / max(1, h) * w // 10)
            pygame.draw.line(surf, barb, (bx, y),
                             (bx + (4 if j % 2 else -4), y - 3), 1)


def _paint_spike_growth(surf, w, h, base):
    """Low ground spikes, distinct from a spiked pit."""
    surf.fill(_alpha((80, 90, 60), 175))
    n = max(4, w // 6)
    for i in range(n):
        cx = int((i + 0.5) * w / n)
        top = int(h * (0.35 + 0.1 * (i % 3)))
        pygame.draw.polygon(surf, (170, 175, 150),
                            [(cx - 2, h - 1), (cx, top), (cx + 2, h - 1)])


def _paint_entangle(surf, w, h, base, ticks):
    """Grasping vines."""
    surf.fill(_alpha((50, 85, 45), 170))
    vine = (95, 150, 75)
    for i in range(3):
        pts = [(x, int(h * (0.25 + 0.25 * i) +
                       math.sin(x * 0.3 + i + ticks * 0.004) * h * 0.12))
               for x in range(0, w + 1, 2)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, vine, False, pts, 2)


def _paint_moonbeam(surf, w, h, base, ticks):
    """Cold column of light."""
    surf.fill(_alpha((150, 175, 225), 60))
    cx = w // 2
    pulse = 0.85 + 0.15 * math.sin(ticks * 0.006)
    half = max(2, int(w * 0.3 * pulse))
    pygame.draw.polygon(surf, (200, 220, 255, 110),
                        [(cx - half // 2, 0), (cx + half // 2, 0),
                         (cx + half, h), (cx - half, h)])
    pygame.draw.line(surf, (240, 248, 255), (cx, 0), (cx, h), 1)


def _paint_silence(surf, w, h, base):
    """Muted dome with a struck-through bell."""
    surf.fill(_alpha((120, 120, 140), 95))
    cx, cy = w // 2, h // 2
    r = int(min(w, h) * 0.34)
    if r > 1:
        pygame.draw.circle(surf, (180, 180, 200), (cx, cy), r, 1)
    pygame.draw.arc(surf, (200, 200, 215),
                    pygame.Rect(cx - r // 2, cy - r // 2, r, r),
                    3.14, 6.28, 2)
    pygame.draw.line(surf, (235, 120, 120), (cx - r, cy - r),
                     (cx + r, cy + r), 2)


def _paint_spirit_guardians(surf, w, h, base, ticks):
    """Circling spectral figures."""
    surf.fill(_alpha(base, 70))
    cx, cy = w // 2, h // 2
    t = ticks * 0.004
    for i in range(3):
        ang = t + i * (2 * math.pi / 3)
        r = min(w, h) * 0.3
        px = int(cx + math.cos(ang) * r)
        py = int(cy + math.sin(ang) * r)
        pygame.draw.circle(surf, _alpha(_shade(base, 1.6), 190),
                           (px, py), max(2, min(w, h) // 9))
        pygame.draw.line(surf, _alpha(_shade(base, 1.3), 140),
                         (px, py), (px, py + max(3, h // 6)), 2)


def _paint_fog_cloud(surf, w, h, base, ticks):
    _paint_cloud(surf, w, h, (200, 205, 212), ticks, alpha=180)



def _paint_black_tentacles(surf, w, h, base, ticks):
    """Writhing tentacles bursting out of the ground."""
    surf.fill(_alpha((26, 16, 34), 205))
    t = ticks * 0.004
    for i in range(5):
        bx = int(w * (0.15 + i * 0.18))
        by = h - 1
        pts = []
        for k in range(7):
            f = k / 6.0
            sway = math.sin(t + i * 1.4 + f * 3.0) * w * 0.10 * f
            pts.append((bx + sway, by - h * 0.85 * f))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (58, 34, 76), False, pts,
                              max(2, w // 12))
            pygame.draw.lines(surf, (96, 60, 122), False, pts,
                              max(1, w // 22))
            tipx, tipy = pts[-1]
            pygame.draw.circle(surf, (120, 80, 150),
                               (int(tipx), int(tipy)), max(1, w // 18))


def _paint_wall_force(surf, w, h, base, ticks):
    """Barely-there pane of force: a faint sheen and a bright edge."""
    surf.fill(_alpha(base, 45))
    shimmer = int(40 + 30 * math.sin(ticks * 0.005))
    for i in range(0, w + h, max(5, w // 3)):
        pygame.draw.line(surf, (*_shade(base, 1.5), shimmer),
                         (i, 0), (i - h, h), 1)
    pygame.draw.rect(surf, (*_shade(base, 1.6), 190),
                     pygame.Rect(0, 0, w, h), 2)


def _paint_forcecage(surf, w, h, base, ticks):
    """Bars of force — a cage you can see through but not leave."""
    surf.fill(_alpha(base, 40))
    glow = int(150 + 60 * math.sin(ticks * 0.006))
    bars = 4
    for i in range(bars):
        x = int(w * (i + 0.5) / bars)
        pygame.draw.line(surf, (*_shade(base, 1.5), glow), (x, 0), (x, h), 2)
    for i in range(3):
        y = int(h * (i + 0.5) / 3)
        pygame.draw.line(surf, (*_shade(base, 1.2), glow // 2),
                         (0, y), (w, y), 1)
    pygame.draw.rect(surf, (*_shade(base, 1.7), 210),
                     pygame.Rect(0, 0, w, h), 2)


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
    # Architecture & furniture
    "stairs_up":     _paint_stairs_up,
    "stairs_down":   _paint_stairs_down,
    "ladder":        _paint_ladder,
    "bridge":        _paint_bridge,
    "cover":         _paint_cover_half,
    "cover_3q":      _paint_cover_3q,
    "portcullis":    _paint_portcullis,
    "altar":         _paint_altar,
    "statue":        _paint_statue,
    "throne":        _paint_throne,
    "bookshelf":     _paint_bookshelf,
    "brazier":       _paint_brazier,
    "cage":          _paint_cage,
    "pit":           _paint_pit,
    # Natural features
    "stalactite":     _paint_stalactite,
    "mushroom_giant": _paint_mushroom_giant,
    "mushroom_patch": _paint_mushroom_patch,
    "web":            _paint_web,
    "moss":           _paint_moss,
    "crystal":        _paint_crystal,
    "sand":           _paint_sand,
    "coral":          _paint_coral,
    "shipwreck":      _paint_shipwreck,
    "mast":           _paint_mast,
    # Graves & ritual
    "tombstone":     _paint_tombstone,
    "sarcophagus":   _paint_sarcophagus,
    "grave_open":    _paint_grave_open,
    "magic_circle":  _paint_magic_circle,
    "teleport_pad":  _paint_teleport_pad,
    "leyline":       _paint_leyline,
    "antimagic":     _paint_antimagic,
    # Static zone markers — these read better as steady art than as
    # animation, so they live in the plain painter table.
    "darkness":      _paint_darkness,
    "dim_light":     _paint_dim_light,
    "wall_thorns":   _paint_wall_thorns,
    "spike_growth":  _paint_spike_growth,
    "silence":       _paint_silence,
}

_PAINTERS_TICKS = {
    "water":      _paint_water,
    "deep_water": _paint_water,
    "lava":       _paint_lava,
    "lava_chasm": _paint_lava,
    "fire":       _paint_fire,
    # Clouds, gases and light levels
    "fog":               _paint_fog,
    "fog_cloud":         _paint_fog_cloud,
    "fog_light":         _paint_fog_light,
    "stinking_cloud":    _paint_stinking_cloud,
    "cloudkill":         _paint_cloudkill,
    "poison":            _paint_poison,
    "acid":              _paint_acid,
    "sleet_storm":       _paint_sleet_storm,
    # Spell walls and zones
    "wall_fire":         _paint_wall_fire,
    "wall_wind":         _paint_wall_wind,
    "entangle":          _paint_entangle,
    "moonbeam":          _paint_moonbeam,
    "spirit_guardians":  _paint_spirit_guardians,
    "black_tentacles":   _paint_black_tentacles,
    "wall_force":        _paint_wall_force,
    "forcecage":         _paint_forcecage,
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
