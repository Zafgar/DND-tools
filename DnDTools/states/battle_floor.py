"""Procedural battle-floor textures and viewport lighting.

The battle grid used to be a single flat ``bg_dark`` fill, so every map —
tavern, forest, volcano, temple — sat on identical dark grey. This module
paints a **tiling floor texture** under the grid lines instead, chosen per
map via ``battle.floor_style``, plus a soft vignette that makes the
viewport read as a lit space rather than a spreadsheet.

Everything is generated once per (style, tile size) and cached, so the
per-frame cost is a handful of blits.

Design constraints:
  * Deterministic — the pattern comes from a hash of the cell coordinates,
    never from ``random``, so the floor does not shimmer between frames
    and tests can assert on it.
  * Dark enough that tokens, terrain tiles and grid lines stay the
    brightest things on screen. A pretty floor that hides the creatures
    would be a downgrade.
  * Never raises. A missing style falls back to plain stone.
"""
from __future__ import annotations

import math

try:
    import pygame  # type: ignore
except ImportError:                                   # pragma: no cover
    pygame = None  # noqa


# Base tone per style, kept deliberately desaturated and dark.
FLOOR_STYLES = {
    "stone":   (48, 48, 54),
    "flagstone": (52, 50, 48),
    "dungeon": (40, 39, 44),
    "cave":    (38, 35, 34),
    "grass":   (34, 50, 34),
    "forest":  (30, 44, 30),
    "sand":    (66, 58, 42),
    "desert":  (72, 62, 44),
    "wood":    (54, 40, 28),
    "marble":  (58, 58, 66),
    "temple":  (56, 52, 46),
    "snow":    (62, 68, 78),
    "ash":     (44, 40, 40),
    "volcanic": (46, 34, 32),
    "water":   (26, 40, 56),
    "underdark": (34, 32, 44),
    "arena":   (68, 58, 44),
    "ship":    (50, 38, 30),
    "graveyard": (36, 42, 36),
}

DEFAULT_STYLE = "stone"

# One tile of texture covers this many grid cells, so the pattern does
# not repeat on every single square.
_PATCH_CELLS = 4


def _shade(color, factor: float):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def _cell_hash(cx: int, cy: int) -> int:
    """Cheap deterministic 2D hash — same cell always gets same value."""
    n = (cx * 73856093) ^ (cy * 19349663)
    n = (n ^ (n >> 13)) & 0x7FFFFFFF
    return n


def base_color(style: str):
    return FLOOR_STYLES.get(style, FLOOR_STYLES[DEFAULT_STYLE])


def known_styles():
    return sorted(FLOOR_STYLES)


# --------------------------------------------------------------------- #
# Per-style patch painters. Each fills a patch of _PATCH_CELLS² cells.
# --------------------------------------------------------------------- #
def _patch_flagstone(surf, gsz, base, cells):
    """Irregular flagstones with mortar gaps."""
    surf.fill(base)
    for cy in range(cells):
        for cx in range(cells):
            hv = _cell_hash(cx, cy)
            inset = 1 + (hv % 2)
            rect = pygame.Rect(cx * gsz + inset, cy * gsz + inset,
                               gsz - inset * 2, gsz - inset * 2)
            tone = 0.88 + ((hv >> 3) % 5) * 0.06
            pygame.draw.rect(surf, _shade(base, tone), rect, border_radius=2)
            pygame.draw.line(surf, _shade(base, 1.18),
                             (rect.left, rect.top), (rect.right, rect.top), 1)


def _patch_grass(surf, gsz, base, cells):
    """Tufts and patchy tone variation."""
    surf.fill(base)
    span = cells * gsz
    for cy in range(cells):
        for cx in range(cells):
            hv = _cell_hash(cx, cy)
            tone = 0.9 + ((hv >> 2) % 4) * 0.07
            pygame.draw.rect(surf, _shade(base, tone),
                             pygame.Rect(cx * gsz, cy * gsz, gsz, gsz))
    blade = _shade(base, 1.5)
    step = max(4, gsz // 3)
    for y in range(0, span, step):
        for x in range(0, span, step):
            hv = _cell_hash(x, y)
            if hv % 3:
                continue
            px, py = x + hv % step, y + (hv >> 4) % step
            pygame.draw.line(surf, blade, (px, py), (px, py - 3), 1)


def _patch_cave(surf, gsz, base, cells):
    """Mottled rock with darker pockets."""
    surf.fill(base)
    span = cells * gsz
    step = max(5, gsz // 2)
    for y in range(0, span, step):
        for x in range(0, span, step):
            hv = _cell_hash(x, y)
            r = max(2, step // 2 + (hv % 3))
            tone = 0.78 + (hv % 6) * 0.08
            pygame.draw.circle(surf, _shade(base, tone), (x, y), r)


def _patch_sand(surf, gsz, base, cells):
    """Wind ripples."""
    surf.fill(base)
    span = cells * gsz
    light = _shade(base, 1.14)
    dark = _shade(base, 0.9)
    for y in range(0, span, max(4, gsz // 3)):
        pts = [(x, y + int(2.0 * math.sin(x * 0.13 + y * 0.05)))
               for x in range(0, span + 1, 3)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, light, False, pts, 1)
            pygame.draw.lines(surf, dark, False,
                              [(x, yy + 1) for x, yy in pts], 1)


def _patch_wood(surf, gsz, base, cells):
    """Long planks with grain."""
    surf.fill(base)
    span = cells * gsz
    plank_h = max(6, gsz // 2)
    row = 0
    for y in range(0, span, plank_h):
        tone = 0.9 + (row % 3) * 0.08
        pygame.draw.rect(surf, _shade(base, tone),
                         pygame.Rect(0, y, span, plank_h - 1))
        pygame.draw.line(surf, _shade(base, 0.7), (0, y + plank_h - 1),
                         (span, y + plank_h - 1), 1)
        for x in range(0, span, max(8, gsz)):
            hv = _cell_hash(x, y)
            if hv % 2:
                pygame.draw.line(surf, _shade(base, 1.18),
                                 (x, y + plank_h // 2),
                                 (x + max(6, gsz // 2), y + plank_h // 2), 1)
        row += 1


def _patch_marble(surf, gsz, base, cells):
    """Big pale slabs with veining."""
    surf.fill(base)
    span = cells * gsz
    slab = gsz * 2
    for cy in range(0, span, slab):
        for cx in range(0, span, slab):
            hv = _cell_hash(cx, cy)
            tone = 0.94 + (hv % 3) * 0.06
            pygame.draw.rect(surf, _shade(base, tone),
                             pygame.Rect(cx + 1, cy + 1, slab - 2, slab - 2))
            vein = _shade(base, 1.35)
            pygame.draw.line(surf, vein, (cx + 2, cy + slab // 3),
                             (cx + slab - 2, cy + slab // 2), 1)
    for cy in range(0, span + 1, slab):
        pygame.draw.line(surf, _shade(base, 0.72), (0, cy), (span, cy), 1)
    for cx in range(0, span + 1, slab):
        pygame.draw.line(surf, _shade(base, 0.72), (cx, 0), (cx, span), 1)


def _patch_snow(surf, gsz, base, cells):
    """Drifts with sparkle."""
    surf.fill(base)
    span = cells * gsz
    for y in range(0, span, max(5, gsz // 2)):
        pts = [(x, y + int(3.0 * math.sin(x * 0.08)))
               for x in range(0, span + 1, 4)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, _shade(base, 1.2), False, pts, 2)
    for y in range(0, span, max(7, gsz)):
        for x in range(0, span, max(7, gsz)):
            if _cell_hash(x, y) % 4 == 0:
                surf.set_at((min(span - 1, x), min(span - 1, y)),
                            _shade(base, 1.6))


def _patch_ash(surf, gsz, base, cells):
    """Cracked scorched ground with faint embers."""
    surf.fill(base)
    span = cells * gsz
    for y in range(0, span, max(6, gsz)):
        for x in range(0, span, max(6, gsz)):
            hv = _cell_hash(x, y)
            if hv % 3:
                continue
            pygame.draw.line(surf, _shade(base, 0.66), (x, y),
                             (x + 4 + hv % 5, y + 3 + (hv >> 3) % 5), 1)
            if hv % 11 == 0:
                pygame.draw.circle(surf, (120, 55, 30), (x, y), 1)


def _patch_underdark(surf, gsz, base, cells):
    """Cave rock with faint faerzress glimmer."""
    _patch_cave(surf, gsz, base, cells)
    span = cells * gsz
    for y in range(0, span, max(8, gsz)):
        for x in range(0, span, max(8, gsz)):
            hv = _cell_hash(x + 7, y + 13)
            if hv % 5 == 0:
                pygame.draw.circle(surf, (70, 60, 130), (x, y),
                                   max(1, gsz // 8))


def _patch_water(surf, gsz, base, cells):
    """Open water — long slow swells."""
    surf.fill(base)
    span = cells * gsz
    for y in range(0, span, max(4, gsz // 3)):
        pts = [(x, y + int(2.5 * math.sin(x * 0.1 + y * 0.06)))
               for x in range(0, span + 1, 3)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, _shade(base, 1.25), False, pts, 1)


def _patch_graveyard(surf, gsz, base, cells):
    """Turf with sunken patches — the graves that are already filled."""
    _patch_grass(surf, gsz, base, cells)
    for cy in range(cells):
        for cx in range(cells):
            if _cell_hash(cx + 3, cy + 5) % 6:
                continue
            rect = pygame.Rect(cx * gsz + 2, cy * gsz + 3,
                               gsz - 4, gsz - 6)
            pygame.draw.rect(surf, _shade(base, 0.72), rect, border_radius=2)
            pygame.draw.rect(surf, _shade(base, 0.55), rect, 1,
                             border_radius=2)


_PATCH_PAINTERS = {
    "stone":     _patch_flagstone,
    "flagstone": _patch_flagstone,
    "dungeon":   _patch_flagstone,
    "temple":    _patch_marble,
    "marble":    _patch_marble,
    "arena":     _patch_sand,
    "sand":      _patch_sand,
    "desert":    _patch_sand,
    "grass":     _patch_grass,
    "forest":    _patch_grass,
    "graveyard": _patch_graveyard,
    "cave":      _patch_cave,
    "underdark": _patch_underdark,
    "wood":      _patch_wood,
    "ship":      _patch_wood,
    "snow":      _patch_snow,
    "ash":       _patch_ash,
    "volcanic":  _patch_ash,
    "water":     _patch_water,
}


# --------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------- #
_patch_cache: dict = {}


def get_floor_patch(style: str, grid_size: int):
    """A tiling floor surface covering ``_PATCH_CELLS``² cells.

    Returns None when pygame is unavailable or the grid size is degenerate.
    Cached per (style, grid_size).
    """
    if pygame is None:
        return None
    gsz = int(grid_size)
    if gsz <= 0:
        return None
    style = style if style in _PATCH_PAINTERS else DEFAULT_STYLE
    key = (style, gsz)
    cached = _patch_cache.get(key)
    if cached is not None:
        return cached
    span = gsz * _PATCH_CELLS
    surf = pygame.Surface((span, span))
    try:
        _PATCH_PAINTERS[style](surf, gsz, base_color(style), _PATCH_CELLS)
    except Exception:
        surf.fill(base_color(style))
    _patch_cache[key] = surf
    return surf


def draw_floor(screen, rect, style: str, grid_size: int,
               camera_x: float = 0.0, camera_y: float = 0.0) -> bool:
    """Tile the procedural floor across ``rect``, aligned to the camera.

    Returns True when something was painted.
    """
    patch = get_floor_patch(style, grid_size)
    if patch is None:
        return False
    span = patch.get_width()
    # Align the pattern to world space so it scrolls with the camera
    # instead of sliding under it.
    ox = -int(camera_x) % span
    oy = -int(camera_y) % span
    prev_clip = screen.get_clip()
    screen.set_clip(rect)
    y = rect.top + oy - span
    while y < rect.bottom:
        x = rect.left + ox - span
        while x < rect.right:
            screen.blit(patch, (x, y))
            x += span
        y += span
    screen.set_clip(prev_clip)
    return True


_vignette_cache: dict = {}


def get_vignette(width: int, height: int, strength: int = 110):
    """Cached edge-darkening overlay sized to the viewport."""
    if pygame is None:
        return None
    width, height = int(width), int(height)
    if width <= 0 or height <= 0:
        return None
    key = (width, height, int(strength))
    cached = _vignette_cache.get(key)
    if cached is not None:
        return cached
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    # Four edge gradients are far cheaper than a per-pixel radial falloff
    # and read the same at this strength.
    band = max(8, min(width, height) // 5)
    for i in range(band):
        a = int(strength * (1.0 - i / band) ** 2)
        if a <= 0:
            continue
        col = (0, 0, 0, a)
        pygame.draw.line(surf, col, (0, i), (width, i))
        pygame.draw.line(surf, col, (0, height - 1 - i), (width, height - 1 - i))
        pygame.draw.line(surf, col, (i, 0), (i, height))
        pygame.draw.line(surf, col, (width - 1 - i, 0), (width - 1 - i, height))
    _vignette_cache[key] = surf
    return surf


def draw_vignette(screen, rect, strength: int = 110) -> bool:
    """Darken the viewport edges so the map reads as a lit space."""
    surf = get_vignette(rect.width, rect.height, strength)
    if surf is None:
        return False
    screen.blit(surf, rect.topleft)
    return True


def clear_caches():
    """Test helper — drop the generated surfaces."""
    _patch_cache.clear()
    _vignette_cache.clear()
