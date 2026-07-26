"""Token furniture — the ring, base, shadow and status readouts that make
a creature marker look like a miniature instead of a coloured circle.

The token *interior* stays where it was: a portrait, a procedural
character from ``states/character_art.py``, or initials. This module owns
everything **around** it, because that is where the readable information
lives:

  * a bevelled metal base ring with a lit top edge and a dark underside,
    so the token sits on the map rather than floating on it
  * an **HP arc** burned into the ring — green → amber → red, filling
    counter-clockwise as the creature drops. The DM reads remaining HP
    from across the table without parsing the bar
  * an elevation-aware **drop shadow**: a flying creature's shadow slides
    away and softens, which is the only cue that actually communicates
    "this thing is 30 ft up"
  * a **turn pulse** on the active creature and a distinct selection ring
  * **threat notches** on the rim for elite and boss creatures, so a CR 13
    priest never gets mistaken for one of the CR 4 choir

Everything is a pygame primitive — no assets. Every function tolerates a
tiny radius so the zoomed-out map does not crash.
"""
from __future__ import annotations

import math

try:
    import pygame  # type: ignore
except ImportError:                                   # pragma: no cover
    pygame = None  # noqa


# HP thresholds → arc colour. Deliberately only three bands: at the table
# "fine / hurt / nearly dead" is the decision, not the exact percentage.
HP_COLORS = (
    (0.60, (90, 210, 110)),
    (0.30, (235, 190, 70)),
    (0.00, (225, 75, 70)),
)

# CR → how many notches on the rim. A boss should be visibly a boss.
THREAT_TIERS = (
    (17.0, 4, (255, 120, 120)),   # legendary / mythic
    (11.0, 3, (255, 180, 90)),    # boss
    (5.0, 2, (230, 220, 120)),    # elite
    (2.0, 1, (180, 200, 220)),    # notable
)


def _shade(color, factor: float):
    return tuple(max(0, min(255, int(c * factor))) for c in color[:3])


def hp_color(fraction: float):
    """Arc colour for a remaining-HP fraction."""
    f = max(0.0, min(1.0, float(fraction)))
    for threshold, colour in HP_COLORS:
        if f > threshold:
            return colour
    return HP_COLORS[-1][1]


def threat_tier(challenge_rating: float):
    """(notches, colour) for a CR, or (0, None) for ordinary creatures."""
    try:
        cr = float(challenge_rating or 0)
    except (TypeError, ValueError):
        return 0, None
    for threshold, notches, colour in THREAT_TIERS:
        if cr >= threshold:
            return notches, colour
    return 0, None


# --------------------------------------------------------------------- #
# Shadow
# --------------------------------------------------------------------- #
def draw_shadow(screen, cx, cy, radius, *, elevation_ft: int = 0,
                is_flying: bool = False):
    """Soft ellipse under the token, offset and blurred by altitude.

    A grounded creature gets a tight shadow directly beneath it. The
    higher it is, the further the shadow slides down-right and the
    weaker it gets — that offset is what sells "airborne".
    """
    if pygame is None or radius <= 0:
        return
    height = max(0, int(elevation_ft))
    if is_flying and height <= 0:
        height = 10
    lift = min(1.0, height / 40.0)
    offset = int(radius * 0.25 * lift) + 2
    spread = 1.0 + 0.5 * lift
    alpha_top = int(70 * (1.0 - 0.6 * lift))
    size = int(radius * 2 * spread) + offset * 2 + 12
    if size <= 0:
        return
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    for i, a_mul in ((0, 1.0), (2, 0.6), (4, 0.35)):
        rx = int(radius * spread) + i
        ry = int(radius * spread * 0.55) + i
        if rx <= 0 or ry <= 0:
            continue
        a = int(alpha_top * a_mul)
        if a <= 0:
            continue
        pygame.draw.ellipse(surf, (0, 0, 0, a),
                            pygame.Rect(mid - rx, mid - ry, rx * 2, ry * 2))
    screen.blit(surf, (cx - mid + offset, cy - mid + offset + radius // 3))


# --------------------------------------------------------------------- #
# Base ring
# --------------------------------------------------------------------- #
def draw_base_ring(screen, cx, cy, radius, team_color, *, thickness: int = 4):
    """Bevelled metal rim: lit along the top, dark along the bottom."""
    if pygame is None or radius <= 2:
        return
    size = radius * 2 + 8
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    rect = pygame.Rect(mid - radius, mid - radius, radius * 2, radius * 2)
    w = max(2, int(thickness))
    # Body of the rim
    pygame.draw.circle(surf, team_color, (mid, mid), radius, w)
    # Lit upper arc and shaded lower arc give it thickness
    pygame.draw.arc(surf, _shade(team_color, 1.55), rect,
                    math.radians(200), math.radians(340), max(1, w - 1))
    pygame.draw.arc(surf, _shade(team_color, 0.45), rect,
                    math.radians(20), math.radians(160), max(1, w - 1))
    # Thin dark keyline outside so the token separates from the floor
    pygame.draw.circle(surf, (12, 12, 16, 170), (mid, mid), radius + 1, 1)
    screen.blit(surf, (cx - mid, cy - mid))


def draw_hp_arc(screen, cx, cy, radius, hp, max_hp, *, width: int = 3):
    """Ring segment showing remaining HP, starting at the top.

    Returns the fraction drawn so callers can reuse it. Draws nothing for
    a creature with no HP pool (objects, lair actions).
    """
    if pygame is None or radius <= 3 or not max_hp or max_hp <= 0:
        return 0.0
    frac = max(0.0, min(1.0, float(hp) / float(max_hp)))
    size = radius * 2 + 8
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    r = radius + 3
    rect = pygame.Rect(mid - r, mid - r, r * 2, r * 2)
    w = max(2, int(width))
    # Empty track first
    pygame.draw.arc(surf, (30, 30, 38, 190), rect, 0, math.tau, w)
    if frac > 0.005:
        # Start at 12 o'clock and sweep clockwise as HP is spent, i.e. the
        # arc SHRINKS toward the top — matching how a health ring reads.
        start = math.radians(90) - math.tau * frac
        pygame.draw.arc(surf, (*hp_color(frac), 240), rect,
                        start, math.radians(90), w)
    screen.blit(surf, (cx - mid, cy - mid))
    return frac


def draw_threat_notches(screen, cx, cy, radius, challenge_rating):
    """Small rim ticks marking elite / boss / legendary creatures."""
    if pygame is None or radius <= 5:
        return 0
    notches, colour = threat_tier(challenge_rating)
    if not notches or colour is None:
        return 0
    size = radius * 2 + 14
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    # Fan the ticks across the bottom of the rim, away from the HP arc's
    # start point at the top.
    spread = math.radians(16)
    base = math.radians(90)
    for i in range(notches):
        ang = base + (i - (notches - 1) / 2.0) * spread
        inner = radius + 2
        outer = radius + 7
        x1 = mid + inner * math.cos(ang)
        y1 = mid + inner * math.sin(ang)
        x2 = mid + outer * math.cos(ang)
        y2 = mid + outer * math.sin(ang)
        pygame.draw.line(surf, (10, 10, 14, 200), (x1, y1), (x2, y2), 4)
        pygame.draw.line(surf, (*colour, 245), (x1, y1), (x2, y2), 2)
    screen.blit(surf, (cx - mid, cy - mid))
    return notches


def draw_turn_pulse(screen, cx, cy, radius, ticks, color=(255, 245, 200)):
    """Breathing halo around the creature whose turn it is."""
    if pygame is None or radius <= 2:
        return
    phase = (math.sin(ticks * 0.006) + 1.0) * 0.5      # 0..1
    reach = int(radius + 4 + 5 * phase)
    size = reach * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    pygame.draw.circle(surf, (*color, int(40 + 55 * (1 - phase))),
                       (mid, mid), reach, 3)
    pygame.draw.circle(surf, (*color, int(120 + 80 * (1 - phase))),
                       (mid, mid), radius + 3, 2)
    screen.blit(surf, (cx - mid, cy - mid))


def draw_selection_ring(screen, cx, cy, radius, color=(255, 200, 90)):
    """Dashed ring for the DM's current selection — visually distinct from
    the turn pulse so the two never get confused."""
    if pygame is None or radius <= 2:
        return
    r = radius + 7
    size = r * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    rect = pygame.Rect(mid - r, mid - r, r * 2, r * 2)
    for i in range(8):
        a0 = i * math.tau / 8
        pygame.draw.arc(surf, (*color, 235), rect, a0, a0 + 0.36, 2)
    screen.blit(surf, (cx - mid, cy - mid))


def draw_condition_ring(screen, cx, cy, radius, conditions):
    """Tint the outermost rim by the most significant active condition.

    One glance tells the DM that a token is Stunned rather than merely
    Poisoned, without reading the badge stack.
    """
    if pygame is None or radius <= 3 or not conditions:
        return None
    try:
        from states.battle_constants import CONDITION_BADGES
    except Exception:
        return None
    # Priority: things that stop a turn outright come first.
    priority = ("Unconscious", "Paralyzed", "Stunned", "Petrified",
                "Incapacitated", "Restrained", "Grappled", "Frightened",
                "Charmed", "Prone", "Blinded", "Poisoned", "Invisible")
    active = {str(c) for c in conditions}
    chosen = next((c for c in priority if c in active), None)
    if chosen is None:
        return None
    colour = CONDITION_BADGES.get(chosen, (None, (200, 200, 210)))[1]
    r = radius + 5
    size = r * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid = size // 2
    pygame.draw.circle(surf, (*colour, 200), (mid, mid), r, 2)
    screen.blit(surf, (cx - mid, cy - mid))
    return chosen


def draw_prone_base(screen, cx, cy, radius, team_color):
    """Flattened ellipse base for a prone creature."""
    if pygame is None or radius <= 2:
        return
    rect = pygame.Rect(cx - radius, cy - radius // 2, radius * 2, radius)
    pygame.draw.ellipse(screen, _shade(team_color, 0.5), rect)
    pygame.draw.ellipse(screen, team_color, rect, 3)
    pygame.draw.arc(screen, _shade(team_color, 1.5), rect,
                    math.radians(200), math.radians(340), 2)
