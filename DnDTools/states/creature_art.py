"""Procedural creature silhouettes — one recognisable shape per monster.

Every monster in the library used to render as the same horned humanoid,
so at the table a beholder, an ooze and an ancient dragon were the same
red circle with "AB" written on it. This module gives each archetype its
own **silhouette**, drawn from pygame primitives, and animates it just
enough that the map feels alive: wings beat, tentacles sway, an ooze
wobbles, a skeleton's ribs rise.

Design rules, in priority order:

  1. **Readable at token size.** The shapes have to work at 24 px, not
     just at 120. That means bold outlines, few parts, and silhouette
     over detail — you should recognise a dragon from its wings and neck,
     not from its scales.
  2. **Distinct from its neighbours.** The point is telling creatures
     apart at a glance, so shapes are chosen to differ in outline: round
     (beholder), wide (dragon), tall (giant), low (ooze), many-legged
     (spider), coiled (serpent).
  3. **Team colour survives.** Each silhouette is tinted with the colour
     the token renderer passes in, so friend/foe stays legible.
  4. **Deterministic.** Animation comes from the ``phase`` argument only,
     never from ``random``, so a frame is reproducible and testable.

``kind_for_stats`` classifies any ``CreatureStats`` into one of these
silhouettes using the creature type plus name keywords, so a new monster
gets a sensible shape without anyone editing a table.
"""
from __future__ import annotations

import math

try:
    import pygame  # type: ignore
except ImportError:                                   # pragma: no cover
    pygame = None  # noqa


def _shade(c, factor: float):
    return tuple(max(0, min(255, int(v * factor))) for v in c[:3])


def _bob(phase: float, amount: float = 1.0) -> float:
    """Gentle idle rise-and-fall, one cycle per phase."""
    return math.sin(phase * math.tau) * amount


# ===================================================================== #
# Silhouettes
# ===================================================================== #
def _dragon(surf, w, h, c, phase, state):
    """Bold V of wings, compact body, wedge head on a curved neck.

    Two earlier passes failed for opposite reasons: the first spread the
    wings past the round token mask so the tips were sheared off, the
    second drew them darker than the map and they vanished into it. The
    membranes are now LIGHTER than the body with a bright leading edge,
    which is what makes the shape read at 24 px.
    """
    cx, cy = w // 2, int(h * 0.60)
    flap = math.sin(phase * math.tau) * (1.0 if state != "idle" else 0.6)
    body_c = _shade(c, 0.85)
    membrane = _shade(c, 1.25)
    edge = _shade(c, 1.7)
    dark = _shade(c, 0.45)
    for side in (-1, 1):
        shoulder = (cx + side * int(w * 0.05), cy - int(h * 0.14))
        tip = (int(cx + side * w * 0.36),
               int(cy - h * (0.32 + 0.05 * flap)))
        low = (int(cx + side * w * 0.26),
               int(cy - h * (0.02 - 0.03 * flap)))
        pygame.draw.polygon(surf, membrane, [shoulder, tip, low])
        pygame.draw.polygon(surf, dark, [shoulder, tip, low],
                            max(1, w // 34))
        # Bright leading edge — the single strongest silhouette cue
        pygame.draw.line(surf, edge, shoulder, tip, max(2, w // 20))
        # One membrane rib
        mid = ((tip[0] + low[0]) // 2, (tip[1] + low[1]) // 2)
        pygame.draw.line(surf, dark, shoulder, mid, max(1, w // 34))
    # Tail
    pygame.draw.lines(surf, body_c, False, [
        (cx, cy + int(h * 0.06)),
        (cx - int(w * 0.17), cy + int(h * 0.17)),
        (cx - int(w * 0.29), cy + int(h * 0.06))], max(2, w // 17))
    # Body + hind legs
    pygame.draw.ellipse(surf, body_c, pygame.Rect(
        cx - int(w * 0.13), cy - int(h * 0.09),
        int(w * 0.26), int(h * 0.23)))
    for side in (-1, 1):
        pygame.draw.line(surf, dark,
                         (cx + side * int(w * 0.06), cy + int(h * 0.10)),
                         (cx + side * int(w * 0.11), cy + int(h * 0.25)),
                         max(2, w // 20))
    # Neck + wedge head
    pygame.draw.lines(surf, body_c, False, [
        (cx, cy - int(h * 0.05)),
        (cx + int(w * 0.11), cy - int(h * 0.19)),
        (cx + int(w * 0.19), cy - int(h * 0.25))], max(3, w // 12))
    hx, hy = cx + int(w * 0.19), cy - int(h * 0.25)
    hr = max(3, int(min(w, h) * 0.08))
    pygame.draw.polygon(surf, edge, [
        (hx - hr, hy - hr), (int(hx + w * 0.13), hy),
        (hx - hr, hy + hr)])
    pygame.draw.line(surf, dark, (hx - hr, hy - hr),
                     (int(hx - w * 0.09), int(hy - h * 0.09)),
                     max(1, w // 26))
    pygame.draw.circle(surf, (40, 25, 20), (hx, hy), max(1, hr // 3))
    return True


def _beholder(surf, w, h, c, phase, state):
    """Floating sphere, one huge eye, waving stalks."""
    cx = w // 2
    cy = int(h * 0.5 + _bob(phase, h * 0.03))
    r = max(4, int(min(w, h) * 0.27))
    stalks = 6
    for i in range(stalks):
        a = -math.pi / 2 + (i - (stalks - 1) / 2.0) * 0.42
        wob = math.sin(phase * math.tau + i) * 0.22
        reach = r * 2.1
        ex = cx + math.cos(a + wob) * reach
        ey = cy + math.sin(a + wob) * reach
        mx = cx + math.cos(a + wob * 0.4) * reach * 0.55
        my = cy + math.sin(a + wob * 0.4) * reach * 0.55
        pygame.draw.lines(surf, _shade(c, 0.7), False,
                          [(cx, cy), (int(mx), int(my)), (int(ex), int(ey))],
                          max(1, w // 26))
        pygame.draw.circle(surf, _shade(c, 1.3), (int(ex), int(ey)),
                           max(1, w // 22))
    pygame.draw.circle(surf, c, (cx, cy), r)
    pygame.draw.circle(surf, _shade(c, 0.55), (cx, cy), r, max(1, w // 30))
    # The eye — the single most recognisable part
    er = max(2, int(r * 0.55))
    pygame.draw.circle(surf, (240, 240, 250), (cx, cy), er)
    pygame.draw.circle(surf, (20, 20, 30), (cx, cy), max(1, int(er * 0.5)))
    return True


def _ooze(surf, w, h, c, phase, state):
    """Low wobbling blob — nothing else on the map is this shape."""
    squash = 1.0 + 0.12 * math.sin(phase * math.tau)
    bw = int(w * 0.72 * squash)
    bh = int(h * 0.40 / squash)
    rect = pygame.Rect(w // 2 - bw // 2, int(h * 0.85) - bh, bw, bh)
    pygame.draw.ellipse(surf, c, rect)
    pygame.draw.ellipse(surf, _shade(c, 1.4), rect, max(1, w // 28))
    # Two bubbles drifting inside
    for i in (0, 1):
        f = (phase + i * 0.5) % 1.0
        bx = rect.centerx + int((i * 2 - 1) * rect.width * 0.18)
        by = rect.bottom - int(rect.height * (0.2 + 0.6 * f))
        pygame.draw.circle(surf, _shade(c, 1.55), (bx, by),
                           max(1, int(w * 0.05 * (1 - f * 0.5))))
    return True


def _skeleton(surf, w, h, c, phase, state):
    """Skull and ribcage — bone-pale whatever the team colour."""
    bone = (226, 222, 205)
    cx = w // 2
    cy = int(h * 0.52 + _bob(phase, h * 0.012))
    # Ribs
    for i in range(3):
        y = cy - int(h * 0.06) + int(i * h * 0.075)
        rw = int(w * (0.24 - i * 0.03))
        pygame.draw.arc(surf, bone,
                        pygame.Rect(cx - rw, y - int(h * 0.05),
                                    rw * 2, int(h * 0.11)),
                        3.34, 6.08, max(1, w // 30))
    # Spine + legs + arms
    pygame.draw.line(surf, bone, (cx, cy - int(h * 0.12)),
                     (cx, cy + int(h * 0.14)), max(1, w // 26))
    sway = math.sin(phase * math.tau) * w * 0.04
    for side in (-1, 1):
        pygame.draw.line(surf, bone, (cx, cy + int(h * 0.14)),
                         (int(cx + side * w * 0.10), int(h * 0.90)),
                         max(1, w // 28))
        pygame.draw.line(surf, bone, (cx, cy - int(h * 0.08)),
                         (int(cx + side * w * 0.20 + sway),
                          cy + int(h * 0.04)), max(1, w // 30))
    # Skull
    r = max(3, int(min(w, h) * 0.12))
    hy = cy - int(h * 0.22)
    pygame.draw.circle(surf, bone, (cx, hy), r)
    for dx in (-1, 1):
        pygame.draw.circle(surf, (25, 20, 20),
                           (cx + dx * max(1, r // 2), hy - r // 6),
                           max(1, r // 3))
    pygame.draw.line(surf, (25, 20, 20), (cx - r // 2, hy + r // 2),
                     (cx + r // 2, hy + r // 2), 1)
    # A hint of the team colour so friend/foe still reads
    pygame.draw.circle(surf, c, (cx, cy + int(h * 0.02)),
                       max(1, int(w * 0.05)))
    return True


def _shambler(surf, w, h, c, phase, state):
    """Hunched, head lolling, both arms out front — zombies and ghouls.

    The first version was too blobby to tell from a plain humanoid, so
    the outline is now deliberately lopsided: one shoulder dropped, the
    head off-centre, and the arms reaching well past the body.
    """
    cx = w // 2
    cy = int(h * 0.56)
    lurch = math.sin(phase * math.tau) * w * 0.055
    dark, light = _shade(c, 0.55), _shade(c, 1.2)
    # Dragging legs, out of step with each other
    for side, off in ((-1, 0.0), (1, 0.45)):
        f = math.sin((phase + off) * math.tau)
        pygame.draw.line(surf, dark, (cx, cy + int(h * 0.13)),
                         (int(cx + side * w * 0.11 + f * w * 0.04),
                          int(h * 0.93)), max(3, w // 15))
    # Hunched torso, tipped forward
    torso = [(int(cx - w * 0.13 + lurch * 0.3), cy - int(h * 0.10)),
             (int(cx + w * 0.15 + lurch * 0.5), cy - int(h * 0.16)),
             (int(cx + w * 0.13), cy + int(h * 0.15)),
             (int(cx - w * 0.11), cy + int(h * 0.15))]
    pygame.draw.polygon(surf, c, torso)
    pygame.draw.polygon(surf, dark, torso, max(1, w // 30))
    # Both arms reaching forward, one lower than the other
    for side, drop in ((-1, 0.10), (1, 0.02)):
        pygame.draw.lines(surf, dark, False, [
            (cx, cy - int(h * 0.06)),
            (int(cx + w * 0.16), cy + int(h * (drop - 0.02))),
            (int(cx + w * 0.30 + lurch * 0.4),
             cy + int(h * (drop + 0.04)))], max(2, w // 19))
    # Head lolling to one side
    hx = int(cx + w * 0.10 + lurch * 0.5)
    hy = cy - int(h * 0.24)
    r = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, light, (hx, hy), r)
    pygame.draw.line(surf, (35, 25, 25), (hx - r // 2, hy + r // 3),
                     (hx + r // 2, hy + r // 3), max(1, w // 34))
    for dx in (-1, 1):
        pygame.draw.circle(surf, (40, 30, 30),
                           (hx + dx * max(1, r // 2), hy - r // 4),
                           max(1, r // 4))
    return True


def _vampire(surf, w, h, c, phase, state):
    """Humanoid with a high collared cape."""
    cx = w // 2
    cy = int(h * 0.55 + _bob(phase, h * 0.012))
    cape_spread = 0.30 + 0.05 * math.sin(phase * math.tau)
    pygame.draw.polygon(surf, _shade(c, 0.45), [
        (cx, cy - int(h * 0.20)),
        (int(cx - w * cape_spread), int(h * 0.92)),
        (int(cx + w * cape_spread), int(h * 0.92)),
    ])
    body = pygame.Rect(cx - int(w * 0.11), cy - int(h * 0.14),
                       int(w * 0.22), int(h * 0.30))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 18))
    # Collar wings
    for side in (-1, 1):
        pygame.draw.polygon(surf, _shade(c, 0.8), [
            (cx, cy - int(h * 0.20)),
            (int(cx + side * w * 0.18), cy - int(h * 0.30)),
            (int(cx + side * w * 0.07), cy - int(h * 0.13)),
        ])
    hy = cy - int(h * 0.25)
    r = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, (232, 226, 224), (cx, hy), r)
    for dx in (-1, 1):
        pygame.draw.circle(surf, (200, 40, 40),
                           (cx + dx * max(1, r // 2), hy), max(1, r // 4))
    return True


def _ghost(surf, w, h, c, phase, state):
    """No legs, see-through, and a ragged tattered hem.

    A plain translucent blob read almost identically to a humanoid in a
    coarse silhouette test, so the hem is now scalloped into three
    drifting tails — the outline is what tells the table this thing has
    no feet on the ground.
    """
    cx = w // 2
    cy = int(h * 0.40 + _bob(phase, h * 0.05))
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    hood_r = max(3, int(min(w, h) * 0.16))
    # Shroud: narrow shoulders widening into a torn hem
    left = cx - int(w * 0.19)
    right = cx + int(w * 0.19)
    hem_y = int(h * 0.86)
    body = [(cx - hood_r, cy),
            (cx + hood_r, cy),
            (right, hem_y - int(h * 0.10)),
            (left, hem_y - int(h * 0.10))]
    pygame.draw.polygon(layer, (*c, 120), body)
    # Three tails of shroud, each drifting on its own beat
    span = right - left
    for i in range(3):
        f = math.sin((phase + i * 0.33) * math.tau)
        x0 = left + int(span * i / 3.0)
        x1 = left + int(span * (i + 1) / 3.0)
        tip = int(hem_y + f * h * 0.06)
        pygame.draw.polygon(layer, (*c, 100), [
            (x0, hem_y - int(h * 0.12)),
            (x1, hem_y - int(h * 0.12)),
            ((x0 + x1) // 2, tip)])
    # Hood and two bright eyes
    pygame.draw.circle(layer, (*_shade(c, 1.15), 165), (cx, cy), hood_r)
    pygame.draw.circle(layer, (*_shade(c, 0.6), 150), (cx, cy), hood_r,
                       max(1, w // 34))
    for dx in (-1, 1):
        pygame.draw.circle(layer, (250, 250, 255, 235),
                           (cx + dx * max(1, int(w * 0.055)),
                            cy - int(h * 0.01)),
                           max(1, int(w * 0.035)))
    surf.blit(layer, (0, 0))
    return True


def _giant(surf, w, h, c, phase, state):
    """Tall, broad, small head, big club — reads as sheer mass."""
    cx = w // 2
    cy = int(h * 0.52 + _bob(phase, h * 0.015))
    dark = _shade(c, 0.65)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.03
        pygame.draw.line(surf, dark, (cx, cy + int(h * 0.16)),
                         (int(cx + side * w * 0.14 + f), int(h * 0.95)),
                         max(3, w // 11))
    body = pygame.Rect(cx - int(w * 0.22), cy - int(h * 0.18),
                       int(w * 0.44), int(h * 0.36))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 12))
    pygame.draw.rect(surf, dark, body, max(1, w // 30),
                     border_radius=max(2, w // 12))
    # Club over the shoulder
    swing = math.sin(phase * math.tau) * 0.25
    hx = cx + int(w * 0.26)
    pygame.draw.line(surf, (140, 100, 60), (hx, cy),
                     (int(hx + w * 0.12 * math.cos(swing)),
                      int(cy - h * 0.30)), max(3, w // 14))
    pygame.draw.circle(surf, (120, 85, 50),
                       (int(hx + w * 0.12 * math.cos(swing)),
                        int(cy - h * 0.30)), max(2, int(w * 0.08)))
    hy = cy - int(h * 0.26)
    pygame.draw.circle(surf, _shade(c, 1.2), (cx, hy),
                       max(3, int(min(w, h) * 0.10)))
    return True


def _devil(surf, w, h, c, phase, state):
    """Horns, bat wings, barbed tail."""
    cx = w // 2
    cy = int(h * 0.55)
    flap = math.sin(phase * math.tau) * 0.22
    dark = _shade(c, 0.5)
    for side in (-1, 1):
        pygame.draw.polygon(surf, dark, [
            (cx, cy - int(h * 0.10)),
            (int(cx + side * w * 0.42), int(cy - h * (0.20 + flap * 0.4))),
            (int(cx + side * w * 0.22), cy + int(h * 0.10)),
        ])
    # Barbed tail
    pygame.draw.lines(surf, dark, False, [
        (cx, cy + int(h * 0.14)),
        (cx - int(w * 0.12), cy + int(h * 0.26)),
        (cx - int(w * 0.02), int(h * 0.90))], max(1, w // 26))
    body = pygame.Rect(cx - int(w * 0.14), cy - int(h * 0.14),
                       int(w * 0.28), int(h * 0.30))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 16))
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.025
        pygame.draw.line(surf, _shade(c, 0.7), (cx, cy + int(h * 0.14)),
                         (int(cx + side * w * 0.11 + f), int(h * 0.93)),
                         max(2, w // 18))
    hy = cy - int(h * 0.24)
    r = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, _shade(c, 1.2), (cx, hy), r)
    for side in (-1, 1):
        pygame.draw.line(surf, (245, 230, 210),
                         (cx + side * r // 2, hy - r // 2),
                         (int(cx + side * w * 0.14), int(hy - h * 0.14)),
                         max(1, w // 28))
    for dx in (-1, 1):
        pygame.draw.circle(surf, (255, 190, 60),
                           (cx + dx * max(1, r // 3), hy), max(1, r // 4))
    return True


def _celestial(surf, w, h, c, phase, state):
    """Feathered wings and a halo."""
    cx = w // 2
    cy = int(h * 0.55 + _bob(phase, h * 0.02))
    glow = (255, 245, 200)
    lift = math.sin(phase * math.tau) * 0.18
    for side in (-1, 1):
        for k in range(3):
            pygame.draw.line(
                surf, _shade(glow, 0.9 - k * 0.12),
                (cx, cy - int(h * 0.10)),
                (int(cx + side * w * (0.26 + k * 0.09)),
                 int(cy - h * (0.24 - k * 0.06 + lift * 0.3))),
                max(2, w // 22))
    body = pygame.Rect(cx - int(w * 0.11), cy - int(h * 0.13),
                       int(w * 0.22), int(h * 0.30))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 18))
    hy = cy - int(h * 0.24)
    r = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, (245, 232, 210), (cx, hy), r)
    halo = pygame.Rect(cx - r - 2, hy - r - int(h * 0.10),
                       (r + 2) * 2, max(3, int(h * 0.07)))
    pygame.draw.ellipse(surf, glow, halo, max(1, w // 34))
    return True


def _elemental(surf, w, h, c, phase, state):
    """A rising vortex with a bright core — no limbs, no head.

    Overlapping circles read as mush, so the shape is now a spiral of
    tapering arcs: obviously a swirl of stuff rather than a creature.
    """
    cx = w // 2
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    # Solid funnel underneath, so the shape still has mass at 24 px where
    # thin arcs alone almost disappear.
    wob = math.sin(phase * math.tau) * w * 0.03
    pygame.draw.polygon(layer, (*_shade(c, 0.75), 200), [
        (int(cx - w * 0.30), int(h * 0.88)),
        (int(cx + w * 0.30), int(h * 0.88)),
        (int(cx + w * 0.11 + wob), int(h * 0.30)),
        (int(cx - w * 0.11 + wob), int(h * 0.30)),
    ])
    turns = 3
    for i in range(turns):
        f = (phase + i / turns) % 1.0
        # Wider low, narrower high — a funnel
        rise = 1.0 - f
        ry = int(h * (0.80 - 0.52 * f))
        rx = int(w * (0.34 * rise + 0.06))
        band = pygame.Rect(cx - rx, ry - int(h * 0.07), rx * 2,
                           max(3, int(h * 0.14)))
        alpha = int(210 * (0.35 + 0.65 * rise))
        pygame.draw.arc(layer, (*_shade(c, 1.0 + 0.15 * i), alpha), band,
                        0.2 + f * 6.0, 3.4 + f * 6.0, max(2, w // 14))
    # Core
    core_y = int(h * 0.60)
    pygame.draw.circle(layer, (*_shade(c, 1.75), 245), (cx, core_y),
                       max(2, int(min(w, h) * 0.10)))
    pygame.draw.circle(layer, (255, 250, 225, 220), (cx, core_y),
                       max(1, int(min(w, h) * 0.045)))
    # Sparks flung off the top
    for i in range(3):
        f = (phase * 1.4 + i / 3.0) % 1.0
        sx = int(cx + math.sin((f + i) * math.tau) * w * 0.20)
        sy = int(h * (0.55 - 0.40 * f))
        pygame.draw.circle(layer, (*_shade(c, 1.6), int(220 * (1 - f))),
                           (sx, sy), max(1, int(w * 0.035 * (1 - f * 0.5))))
    surf.blit(layer, (0, 0))
    return True


def _construct(surf, w, h, c, phase, state):
    """Blocky plates and a glowing core — obviously not alive."""
    cx = w // 2
    cy = int(h * 0.52)
    hum = 0.5 + 0.5 * math.sin(phase * math.tau)
    dark, light = _shade(c, 0.55), _shade(c, 1.3)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.02
        pygame.draw.rect(surf, dark, pygame.Rect(
            int(cx + side * w * 0.16 - w * 0.05 + f), cy + int(h * 0.14),
            max(2, int(w * 0.10)), int(h * 0.30)))
    torso = pygame.Rect(cx - int(w * 0.20), cy - int(h * 0.16),
                        int(w * 0.40), int(h * 0.32))
    pygame.draw.rect(surf, c, torso)
    pygame.draw.rect(surf, dark, torso, max(1, w // 24))
    pygame.draw.line(surf, light, (torso.left, torso.top),
                     (torso.right, torso.top), max(1, w // 28))
    for side in (-1, 1):
        pygame.draw.rect(surf, _shade(c, 0.8), pygame.Rect(
            int(cx + side * w * 0.24 - w * 0.04), cy - int(h * 0.10),
            max(2, int(w * 0.08)), int(h * 0.24)))
    # Core
    pygame.draw.circle(surf, (120 + int(120 * hum), 220, 255),
                       (cx, cy), max(2, int(w * 0.06)))
    head = pygame.Rect(cx - int(w * 0.10), cy - int(h * 0.30),
                       int(w * 0.20), int(h * 0.14))
    pygame.draw.rect(surf, light, head)
    pygame.draw.line(surf, (30, 40, 50),
                     (head.left + 2, head.centery),
                     (head.right - 2, head.centery), max(1, w // 30))
    return True


def _spider(surf, w, h, c, phase, state):
    """Eight legs and a fat abdomen."""
    cx, cy = w // 2, int(h * 0.55)
    dark = _shade(c, 0.6)
    for side in (-1, 1):
        for k in range(4):
            step = math.sin((phase + k * 0.22 + (0 if side < 0 else 0.5))
                            * math.tau) * h * 0.05
            kneex = cx + side * w * (0.16 + k * 0.05)
            kneey = cy - h * 0.10 + k * h * 0.03
            footx = cx + side * w * (0.30 + k * 0.06)
            footy = cy + h * (0.16 + k * 0.04) + step
            pygame.draw.lines(surf, dark, False, [
                (cx, cy), (int(kneex), int(kneey)),
                (int(footx), int(footy))], max(1, w // 30))
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.16), cy - int(h * 0.04),
        int(w * 0.32), int(h * 0.26)))
    pygame.draw.circle(surf, _shade(c, 1.25), (cx, cy - int(h * 0.08)),
                       max(2, int(min(w, h) * 0.09)))
    for dx in (-1, 1):
        pygame.draw.circle(surf, (250, 240, 120),
                           (cx + dx * max(1, int(w * 0.04)),
                            cy - int(h * 0.10)), max(1, int(w * 0.02)))
    return True


def _serpent(surf, w, h, c, phase, state):
    """A coiled body with the head reared up.

    A single sine wave sometimes landed on a phase that looked like a
    plain chevron, so the body is now a full double coil and the head is
    lifted clear of it — that is what makes it read as a snake.
    """
    slither = phase * math.tau
    pts = []
    for i in range(19):
        f = i / 18.0
        x = w * 0.18 + f * w * 0.56
        y = h * 0.72 + math.sin(f * math.pi * 3.0 + slither) * h * 0.14
        pts.append((int(x), int(y)))
    pygame.draw.lines(surf, _shade(c, 0.55), False, pts, max(4, w // 8))
    pygame.draw.lines(surf, c, False, pts, max(2, w // 13))
    # Belly scale ticks
    for i in range(2, 18, 3):
        x, y = pts[i]
        pygame.draw.line(surf, _shade(c, 1.35), (x, y - 1), (x, y + 1),
                         max(1, w // 34))
    # Neck rears up off the last coil
    tailx, taily = pts[-1]
    neck = [(tailx, taily),
            (int(tailx + w * 0.06), int(taily - h * 0.14)),
            (int(tailx + w * 0.02), int(taily - h * 0.26))]
    pygame.draw.lines(surf, c, False, neck, max(3, w // 12))
    hx, hy = neck[-1]
    hr = max(3, int(min(w, h) * 0.085))
    pygame.draw.circle(surf, _shade(c, 1.35), (hx, hy), hr)
    # Forked tongue + eye
    flick = 1.0 if (phase % 0.5) < 0.25 else 0.4
    pygame.draw.line(surf, (235, 70, 70), (hx + hr // 2, hy),
                     (int(hx + w * 0.11 * flick), hy), max(1, w // 32))
    pygame.draw.circle(surf, (250, 230, 120), (hx, hy - hr // 3),
                       max(1, hr // 3))
    return True


def _tentacled(surf, w, h, c, phase, state):
    """Mind flayer / aboleth / kraken — head plus writhing tentacles."""
    cx = w // 2
    cy = int(h * 0.46 + _bob(phase, h * 0.02))
    head_r = max(3, int(min(w, h) * 0.16))
    for i in range(5):
        f = (i - 2) * 0.30
        wob = math.sin(phase * math.tau + i * 1.1) * 0.35
        pts = [(cx + int(f * w * 0.10), cy + head_r)]
        for k in range(1, 4):
            t = k / 3.0
            pts.append((
                int(cx + f * w * 0.16 + math.sin(wob + t * 2.4) * w * 0.10),
                int(cy + head_r + t * h * 0.36)))
        pygame.draw.lines(surf, _shade(c, 0.65), False, pts,
                          max(1, w // 26))
    pygame.draw.circle(surf, c, (cx, cy), head_r)
    pygame.draw.circle(surf, _shade(c, 0.5), (cx, cy), head_r,
                       max(1, w // 30))
    for dx in (-1, 1):
        pygame.draw.circle(surf, (200, 240, 200),
                           (cx + dx * max(1, head_r // 2),
                            cy - head_r // 4), max(1, head_r // 4))
    return True


def _plant(surf, w, h, c, phase, state):
    """Trunk and swaying canopy — treants, shambling mounds."""
    cx = w // 2
    sway = math.sin(phase * math.tau) * w * 0.03
    trunk_w = max(3, int(w * 0.14))
    pygame.draw.polygon(surf, (110, 78, 48), [
        (cx - trunk_w, int(h * 0.95)),
        (cx + trunk_w, int(h * 0.95)),
        (int(cx + trunk_w * 0.6 + sway), int(h * 0.45)),
        (int(cx - trunk_w * 0.6 + sway), int(h * 0.45)),
    ])
    for i, (fx, fy, fr) in enumerate(((0.0, 0.34, 0.22),
                                      (-0.18, 0.44, 0.16),
                                      (0.18, 0.44, 0.16))):
        wob = math.sin(phase * math.tau + i) * w * 0.02
        pygame.draw.circle(surf, _shade(c, 0.9 + i * 0.12),
                           (int(cx + fx * w + sway + wob), int(h * fy)),
                           max(2, int(min(w, h) * fr)))
    # Branch arms
    for side in (-1, 1):
        pygame.draw.line(surf, (95, 68, 42),
                         (int(cx + sway * 0.5), int(h * 0.60)),
                         (int(cx + side * w * 0.26 + sway),
                          int(h * 0.48)), max(1, w // 26))
    return True


def _swarm(surf, w, h, c, phase, state):
    """A cloud of small bodies, obviously many things not one."""
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(16):
        a = i * 2.399963 + phase * math.tau
        rr = min(w, h) * (0.12 + 0.20 * ((i * 7) % 5) / 4.0)
        x = int(w / 2 + math.cos(a) * rr)
        y = int(h * 0.55 + math.sin(a * 1.3) * rr * 0.8)
        pygame.draw.circle(layer, (*c, 225), (x, y), max(1, int(w * 0.045)))
    surf.blit(layer, (0, 0))
    return True


def _fey(surf, w, h, c, phase, state):
    """Small body, fast insect wings, sparkle."""
    cx = w // 2
    cy = int(h * 0.55 + _bob(phase, h * 0.03))
    beat = abs(math.sin(phase * math.tau * 3))
    for side in (-1, 1):
        wing = pygame.Rect(0, 0, max(2, int(w * 0.20 * (0.5 + beat))),
                           max(2, int(h * 0.26)))
        wing.center = (int(cx + side * w * 0.16), cy - int(h * 0.08))
        pygame.draw.ellipse(surf, (225, 240, 255), wing)
        pygame.draw.ellipse(surf, _shade(c, 1.3), wing, 1)
    body = pygame.Rect(cx - int(w * 0.06), cy - int(h * 0.08),
                       int(w * 0.12), int(h * 0.22))
    pygame.draw.ellipse(surf, c, body)
    pygame.draw.circle(surf, _shade(c, 1.35), (cx, cy - int(h * 0.14)),
                       max(2, int(min(w, h) * 0.07)))
    sx = int(cx + math.cos(phase * math.tau) * w * 0.22)
    sy = int(cy + math.sin(phase * math.tau) * h * 0.18)
    pygame.draw.circle(surf, (255, 255, 200), (sx, sy),
                       max(1, int(w * 0.03)))
    return True


def _quadruped(surf, w, h, c, phase, state):
    """Four-legged beast — wolves, bears, big cats, mounts.

    Legs are deliberately chunky: at 24 px a hairline leg disappears and
    the whole thing reads as a floating lozenge.
    """
    cx, cy = w // 2, int(h * 0.50)
    dark, light = _shade(c, 0.55), _shade(c, 1.25)
    leg_w = max(3, int(w * 0.075))
    for i, fx in enumerate((-0.19, -0.07, 0.09, 0.20)):
        step = math.sin((phase + i * 0.25) * math.tau) * h * 0.055
        top = cy + int(h * 0.08)
        pygame.draw.line(surf, dark,
                         (int(cx + fx * w), top),
                         (int(cx + fx * w), int(cy + h * 0.34 + step)),
                         leg_w)
    # Barrel body
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.26), cy - int(h * 0.10),
        int(w * 0.48), int(h * 0.22)))
    # Tail, flicking
    pygame.draw.line(surf, dark, (cx - int(w * 0.25), cy - int(h * 0.02)),
                     (int(cx - w * 0.36),
                      int(cy - h * (0.14 + 0.05 * math.sin(phase * math.tau)))),
                     max(2, w // 20))
    # Head: skull, muzzle and a pricked ear
    hx, hy = cx + int(w * 0.26), cy - int(h * 0.12)
    hr = max(3, int(min(w, h) * 0.105))
    pygame.draw.circle(surf, light, (hx, hy), hr)
    pygame.draw.polygon(surf, light, [
        (hx + hr // 2, hy - hr // 3),
        (int(hx + w * 0.15), hy + hr // 3),
        (hx + hr // 2, hy + hr)])
    pygame.draw.polygon(surf, dark, [
        (hx - int(w * 0.05), hy - hr + 1),
        (hx + int(w * 0.01), hy - hr + 1),
        (hx - int(w * 0.02), int(hy - h * 0.15))])
    pygame.draw.circle(surf, (255, 220, 120), (int(hx + w * 0.03), hy),
                       max(1, hr // 4))
    return True


def _humanoid(surf, w, h, c, phase, state):
    """Plain two-legged fighter — orcs, bandits, guards, cultists."""
    cx = w // 2
    cy = int(h * 0.54 + _bob(phase, h * 0.012))
    dark = _shade(c, 0.7)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.035
        pygame.draw.line(surf, dark, (cx, cy + int(h * 0.14)),
                         (int(cx + side * w * 0.10 + f), int(h * 0.93)),
                         max(2, w // 16))
    body = pygame.Rect(cx - int(w * 0.13), cy - int(h * 0.14),
                       int(w * 0.26), int(h * 0.30))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 18))
    pygame.draw.rect(surf, dark, body, max(1, w // 30),
                     border_radius=max(2, w // 18))
    # Weapon arm
    swing = math.sin(phase * math.tau) * 0.3
    gx = int(cx + w * 0.20)
    gy = int(cy - h * 0.02)
    pygame.draw.line(surf, dark, (body.right, cy - int(h * 0.04)),
                     (gx, gy), max(2, w // 22))
    pygame.draw.line(surf, (215, 215, 225), (gx, gy),
                     (int(gx + w * 0.12 * math.cos(swing - 1.1)),
                      int(gy + h * 0.30 * math.sin(swing - 1.1))),
                     max(2, w // 22))
    hy = cy - int(h * 0.24)
    pygame.draw.circle(surf, (232, 198, 160), (cx, hy),
                       max(3, int(min(w, h) * 0.10)))
    return True


def _goblinoid(surf, w, h, c, phase, state):
    """Squat body, oversized head, jug ears — goblins, kobolds, gnomes.

    Two cues carry it, because "small person" on its own is not enough
    to tell from ``_humanoid`` at 24 px. First the proportions invert:
    a big head over a small body instead of the other way round.
    Second the ears stick out further than the shoulders do, which puts
    ink in the upper corners of the token where a humanoid has none.
    """
    cx = w // 2
    cy = int(h * 0.66 + _bob(phase, h * 0.012))
    dark, light = _shade(c, 0.65), _shade(c, 1.2)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.03
        pygame.draw.line(surf, dark, (cx, cy + int(h * 0.06)),
                         (int(cx + side * w * 0.08 + f), int(h * 0.88)),
                         max(2, w // 16))
    body = pygame.Rect(cx - int(w * 0.09), cy - int(h * 0.04),
                       int(w * 0.18), int(h * 0.16))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 22))
    # Big head with a pointed jaw
    hy = cy - int(h * 0.18)
    hr = max(4, int(min(w, h) * 0.16))
    pygame.draw.circle(surf, light, (cx, hy), hr)
    pygame.draw.polygon(surf, light, [
        (cx - hr // 2, hy + hr // 2), (cx + hr // 2, hy + hr // 2),
        (cx, hy + hr + hr // 2)])
    # Jug ears — wider than the shoulders, and twitching
    twitch = math.sin(phase * math.tau * 2) * hr * 0.18
    for side in (-1, 1):
        pygame.draw.polygon(surf, light, [
            (cx + side * (hr - 1), hy - hr // 2),
            (int(cx + side * hr * 2.8), int(hy - hr * 1.1 + twitch)),
            (int(cx + side * hr * 2.2), int(hy + hr * 0.5 + twitch)),
            (cx + side * (hr - 1), hy + hr // 3)])
        pygame.draw.polygon(surf, dark, [
            (cx + side * (hr - 1), hy - hr // 2),
            (int(cx + side * hr * 2.8), int(hy - hr * 1.1 + twitch)),
            (int(cx + side * hr * 2.2), int(hy + hr * 0.5 + twitch)),
            (cx + side * (hr - 1), hy + hr // 3)], max(1, w // 40))
    for side in (-1, 1):
        pygame.draw.circle(surf, (255, 230, 120),
                           (cx + side * hr // 2, hy), max(1, hr // 5))
    # Crude blade held low across the body
    pygame.draw.line(surf, (205, 205, 215),
                     (int(cx - w * 0.06), int(cy + h * 0.12)),
                     (int(cx + w * 0.20), int(cy + h * 0.02)),
                     max(2, w // 28))
    return True


def _armored(surf, w, h, c, phase, state):
    """Helmed soldier behind a shield — guards, knights, gladiators.

    The shield is the silhouette: a plain humanoid is a stick, this is a
    stick with a slab bolted to one side, and the slab is what you see
    first in a line of enemy tokens.
    """
    cx = w // 2
    cy = int(h * 0.54 + _bob(phase, h * 0.010))
    dark, steel = _shade(c, 0.6), (198, 202, 214)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.03
        pygame.draw.line(surf, dark, (cx, cy + int(h * 0.14)),
                         (int(cx + side * w * 0.10 + f), int(h * 0.93)),
                         max(2, w // 16))
    body = pygame.Rect(cx - int(w * 0.13), cy - int(h * 0.14),
                       int(w * 0.26), int(h * 0.30))
    pygame.draw.rect(surf, c, body, border_radius=max(2, w // 22))
    # Pauldrons
    for side in (-1, 1):
        pygame.draw.circle(surf, steel,
                           (cx + side * int(w * 0.14), cy - int(h * 0.11)),
                           max(2, int(w * 0.06)))
    # Spear held upright
    thrust = math.sin(phase * math.tau) * h * 0.03
    sx = int(cx + w * 0.21)
    pygame.draw.line(surf, (140, 100, 60), (sx, int(cy - h * 0.34 + thrust)),
                     (sx, int(cy + h * 0.26 + thrust)), max(2, w // 26))
    pygame.draw.polygon(surf, steel, [
        (sx, int(cy - h * 0.42 + thrust)),
        (sx - max(2, int(w * 0.04)), int(cy - h * 0.32 + thrust)),
        (sx + max(2, int(w * 0.04)), int(cy - h * 0.32 + thrust))])
    # Kite shield on the off hand
    shield = pygame.Rect(0, 0, int(w * 0.24), int(h * 0.34))
    shield.center = (cx - int(w * 0.19), cy)
    pygame.draw.ellipse(surf, steel, shield)
    pygame.draw.ellipse(surf, _shade(c, 1.3), shield.inflate(
        -max(2, w // 12), -max(2, h // 9)))
    pygame.draw.ellipse(surf, dark, shield, max(1, w // 30))
    # Helm with a visor slit
    hy = cy - int(h * 0.25)
    hr = max(3, int(min(w, h) * 0.11))
    pygame.draw.circle(surf, steel, (cx, hy), hr)
    pygame.draw.rect(surf, (30, 30, 40), pygame.Rect(
        cx - hr, hy - max(1, hr // 4), hr * 2, max(1, hr // 2)))
    return True


def _caster(surf, w, h, c, phase, state):
    """Hooded robe with sleeves, no legs, a staff with a lit head.

    Cultists, mages and priests all used to be the generic fighter. The
    robe reads as "no legs" even at 24 px, which is exactly the thing
    you want to notice before the fireball lands. It needs the flared
    sleeves though — a bare cone with a ball on top read as a traffic
    marker rather than a person.
    """
    cx = w // 2
    cy = int(h * 0.54 + _bob(phase, h * 0.02))
    dark, light = _shade(c, 0.6), _shade(c, 1.3)
    hem = int(h * 0.90)
    robe = [(cx - int(w * 0.10), cy - int(h * 0.12)),
            (cx + int(w * 0.10), cy - int(h * 0.12)),
            (cx + int(w * 0.24), hem),
            (cx - int(w * 0.24), hem)]
    pygame.draw.polygon(surf, c, robe)
    pygame.draw.polygon(surf, dark, robe, max(1, w // 30))
    # Sleeves: the shoulders are what make it read as a figure
    for side in (-1, 1):
        pygame.draw.polygon(surf, light, [
            (cx + side * int(w * 0.08), cy - int(h * 0.13)),
            (cx + side * int(w * 0.24), cy + int(h * 0.02)),
            (cx + side * int(w * 0.17), cy + int(h * 0.12)),
            (cx + side * int(w * 0.06), cy - int(h * 0.02))])
    # A pale strip down the front, so the robe is not a flat slab
    pygame.draw.polygon(surf, light, [
        (cx - int(w * 0.03), cy - int(h * 0.10)),
        (cx + int(w * 0.03), cy - int(h * 0.10)),
        (cx + int(w * 0.06), hem), (cx - int(w * 0.06), hem)])
    # Hood: a peaked cowl with darkness inside
    hy = cy - int(h * 0.24)
    hr = max(4, int(min(w, h) * 0.145))
    pygame.draw.polygon(surf, c, [
        (cx - hr, hy + hr // 2), (cx, hy - int(hr * 1.7)),
        (cx + hr, hy + hr // 2)])
    pygame.draw.circle(surf, c, (cx, hy), hr)
    pygame.draw.circle(surf, (20, 18, 28), (cx, hy + hr // 6),
                       max(2, int(hr * 0.72)))
    for side in (-1, 1):
        pygame.draw.circle(surf, (255, 205, 110),
                           (cx + side * max(1, hr // 3), hy + hr // 6),
                           max(1, hr // 5))
    # Staff with a pulsing head
    sx = int(cx + w * 0.26)
    pygame.draw.line(surf, (150, 110, 70), (sx, int(cy - h * 0.24)),
                     (sx, hem), max(2, w // 26))
    glow = 0.6 + 0.4 * abs(math.sin(phase * math.tau))
    pygame.draw.circle(surf, _shade((160, 210, 255), glow),
                       (sx, int(cy - h * 0.27)),
                       max(2, int(w * 0.06 * glow)))
    return True


def _bird(surf, w, h, c, phase, state):
    """Swept wings, fanned tail, hooked beak — seen from above.

    Deliberately the mirror image of ``_dragon``: that one is a V seen
    from the side, this is a raptor seen from overhead. The wings sweep
    BACK from the shoulder rather than sticking straight out — drawn as
    a flat bar the whole thing read as a scarecrow on a post.
    """
    cx, cy = w // 2, int(h * 0.50 + _bob(phase, h * 0.02))
    beat = math.sin(phase * math.tau)
    light, dark = _shade(c, 1.3), _shade(c, 0.55)
    # Fanned tail, drawn first so the wings overlap it
    pygame.draw.polygon(surf, dark, [
        (cx - int(w * 0.08), cy + int(h * 0.10)),
        (cx + int(w * 0.08), cy + int(h * 0.10)),
        (cx + int(w * 0.17), int(h * 0.88)),
        (cx - int(w * 0.17), int(h * 0.88))])
    for k in (-1, 0, 1):
        pygame.draw.line(surf, _shade(c, 0.8),
                         (cx + k * int(w * 0.04), cy + int(h * 0.12)),
                         (cx + k * int(w * 0.11), int(h * 0.86)),
                         max(1, w // 40))
    for side in (-1, 1):
        lift = int(h * 0.09 * beat)
        shoulder_f = (cx + side * int(w * 0.07), cy - int(h * 0.14))
        shoulder_b = (cx + side * int(w * 0.07), cy + int(h * 0.06))
        tip = (cx + side * int(w * 0.44), cy - int(h * 0.02) - lift)
        # Swept-back planform: leading edge forward, trailing edge in
        pygame.draw.polygon(surf, light, [
            shoulder_f,
            (cx + side * int(w * 0.26), cy - int(h * 0.16) - lift),
            tip,
            (cx + side * int(w * 0.24), cy + int(h * 0.10) - lift // 2),
            shoulder_b])
        pygame.draw.lines(surf, dark, False, [
            shoulder_f, (cx + side * int(w * 0.26),
                         cy - int(h * 0.16) - lift), tip],
            max(1, w // 32))
        # Primary feather splits at the tip
        for k in (0.86, 0.72):
            pygame.draw.line(surf, dark, tip,
                             (cx + side * int(w * 0.44 * k),
                              cy + int(h * 0.08) - lift // 2),
                             max(1, w // 44))
    # Body and head
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.09), cy - int(h * 0.20),
        int(w * 0.18), int(h * 0.34)))
    hy = cy - int(h * 0.24)
    hr = max(2, int(min(w, h) * 0.085))
    pygame.draw.circle(surf, light, (cx, hy), hr)
    pygame.draw.polygon(surf, (250, 200, 80), [
        (cx - max(1, int(w * 0.035)), hy - int(h * 0.04)),
        (cx + max(1, int(w * 0.035)), hy - int(h * 0.04)),
        (cx, int(hy - h * 0.14))])
    for side in (-1, 1):
        pygame.draw.circle(surf, (40, 30, 25),
                           (cx + side * max(1, hr // 2), hy),
                           max(1, hr // 4))
    return True


def _bat(surf, w, h, c, phase, state):
    """Tiny body slung under huge scalloped wings, beating fast.

    The scallops and the droop are the point. A bat, a bird and a fey
    are all "small thing with wings" in outline, so this one is drawn
    as a wide W: elbows arched above the shoulders, tips hanging BELOW
    them, and a tail membrane closing the gap between the feet. That
    fills the bottom corners of the token, which is where the other two
    are empty.
    """
    cx, cy = w // 2, int(h * 0.48 + _bob(phase * 2, h * 0.035))
    beat = math.sin(phase * math.tau * 3)
    light, dark = _shade(c, 1.2), _shade(c, 0.45)
    span = w * (0.44 + 0.04 * beat)
    for side in (-1, 1):
        shoulder = (cx + side * int(w * 0.05), cy - int(h * 0.08))
        elbow = (int(cx + side * span * 0.52),
                 int(cy - h * (0.26 + 0.06 * beat)))
        tip = (int(cx + side * span), int(cy + h * (0.06 - 0.06 * beat)))
        pts = [shoulder, elbow, tip]
        # Trailing edge, scalloped back to the body
        for k in (0.70, 0.40):
            pts.append((int(cx + side * span * (k + 0.08)),
                        int(cy + h * 0.10)))
            pts.append((int(cx + side * span * k),
                        int(cy + h * 0.28)))
        pts.append((cx + side * int(w * 0.06), cy + int(h * 0.14)))
        pygame.draw.polygon(surf, light, pts)
        pygame.draw.polygon(surf, dark, pts, max(1, w // 36))
        # Finger struts fanning out from the elbow
        for k in (0.70, 0.40):
            pygame.draw.line(surf, dark, elbow,
                             (int(cx + side * span * k),
                              int(cy + h * 0.28)), max(1, w // 40))
        pygame.draw.line(surf, dark, shoulder, elbow, max(1, w // 34))
    # Tail membrane and feet
    pygame.draw.polygon(surf, light, [
        (cx - int(w * 0.11), cy + int(h * 0.14)),
        (cx + int(w * 0.11), cy + int(h * 0.14)),
        (cx, int(cy + h * 0.40))])
    for side in (-1, 1):
        pygame.draw.line(surf, dark, (cx + side * int(w * 0.05),
                                      cy + int(h * 0.14)),
                         (cx + side * int(w * 0.10), int(cy + h * 0.36)),
                         max(1, w // 34))
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.07), cy - int(h * 0.10),
        int(w * 0.14), int(h * 0.26)))
    hy = cy - int(h * 0.15)
    hr = max(2, int(min(w, h) * 0.08))
    pygame.draw.circle(surf, dark, (cx, hy), hr)
    for side in (-1, 1):
        pygame.draw.polygon(surf, dark, [
            (cx + side * hr // 2, hy - hr // 2),
            (int(cx + side * hr * 1.2), int(hy - h * 0.13)),
            (cx + side * hr, hy - hr // 3)])
    for side in (-1, 1):
        pygame.draw.circle(surf, (255, 190, 90),
                           (cx + side * max(1, hr // 3), hy),
                           max(1, hr // 4))
    return True


def _aquatic(surf, w, h, c, phase, state):
    """Streamlined body, dorsal fin, crescent tail — sharks and sahuagin.

    The tail sweeps side to side rather than bobbing, which is the cue
    that this thing swims instead of walking.
    """
    cx, cy = w // 2, int(h * 0.52)
    sweep = math.sin(phase * math.tau) * h * 0.10
    light, dark = _shade(c, 1.2), _shade(c, 0.5)
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.30), cy - int(h * 0.13),
        int(w * 0.56), int(h * 0.27)))
    pygame.draw.polygon(surf, dark, [
        (cx - int(w * 0.26), cy),
        (int(cx - w * 0.44), int(cy - h * 0.18 + sweep)),
        (int(cx - w * 0.44), int(cy + h * 0.18 + sweep))])
    pygame.draw.polygon(surf, light, [
        (cx - int(w * 0.06), cy - int(h * 0.11)),
        (cx + int(w * 0.08), cy - int(h * 0.11)),
        (cx - int(w * 0.02), int(cy - h * 0.34))])
    for side in (-1, 1):
        pygame.draw.polygon(surf, dark, [
            (cx + int(w * 0.02), cy + int(h * 0.06)),
            (cx + int(w * 0.16), int(cy + h * (0.06 + side * 0.02))),
            (cx + int(w * 0.04), cy + int(h * 0.24))])
    hx = cx + int(w * 0.26)
    pygame.draw.polygon(surf, light, [
        (hx - int(w * 0.04), cy - int(h * 0.11)),
        (int(cx + w * 0.36), cy - int(h * 0.02)),
        (hx - int(w * 0.04), cy + int(h * 0.11))])
    pygame.draw.circle(surf, (25, 25, 35), (hx, cy - int(h * 0.04)),
                       max(1, int(w * 0.025)))
    # Gill slits
    for k in range(3):
        gx = cx + int(w * (0.10 + 0.05 * k))
        pygame.draw.line(surf, dark, (gx, cy - int(h * 0.06)),
                         (gx, cy + int(h * 0.04)), max(1, w // 40))
    return True


def _hydra(surf, w, h, c, phase, state):
    """One heavy bulk, five S-curved necks, five snapping heads.

    Straight necks made this read as a table with lollipops on it. They
    are drawn as arcs now, fanning outward from a deep body, and each
    head is a wedge rather than a dot so you can see which way it faces.
    """
    cx, cy = w // 2, int(h * 0.70)
    light, dark = _shade(c, 1.2), _shade(c, 0.5)
    # Deep body first, so the necks emerge from behind it
    body = pygame.Rect(cx - int(w * 0.30), cy - int(h * 0.16),
                       int(w * 0.60), int(h * 0.32))
    for i in range(5):
        lean = (i - 2) * 0.22
        wave = math.sin((phase + i * 0.2) * math.tau) * 0.07
        pts = []
        for step in range(5):
            f = step / 4.0
            # S-curve: leans out at the shoulder, straightens at the head
            bend = math.sin(f * math.pi) * (0.10 + wave) * (1 if i % 2 else -1)
            pts.append((int(cx + (lean * f * 1.5 + bend) * w * 0.62),
                        int(cy - h * (0.06 + 0.44 * f))))
        pygame.draw.lines(surf, c, False, pts,
                          max(3, w // 18))
        pygame.draw.lines(surf, light, False, pts, max(1, w // 40))
        tip = pts[-1]
        hr = max(3, int(min(w, h) * 0.065))
        face = 1 if lean >= 0 else -1
        pygame.draw.circle(surf, light, tip, hr)
        pygame.draw.polygon(surf, light, [
            (tip[0], tip[1] - hr), (int(tip[0] + face * hr * 2.0), tip[1]),
            (tip[0], tip[1] + hr)])
        pygame.draw.circle(surf, (60, 30, 25),
                           (int(tip[0] + face * hr // 2), tip[1] - hr // 3),
                           max(1, hr // 3))
    pygame.draw.ellipse(surf, c, body)
    pygame.draw.arc(surf, light, body.inflate(-w // 9, -h // 9),
                    0.3, 2.8, max(2, w // 26))
    for side in (-1, 1):
        pygame.draw.line(surf, dark,
                         (cx + side * int(w * 0.16), cy + int(h * 0.10)),
                         (cx + side * int(w * 0.22), int(h * 0.96)),
                         max(3, w // 15))
    # Thick tail sweeping out behind
    pygame.draw.lines(surf, dark, False, [
        (cx - int(w * 0.28), cy + int(h * 0.04)),
        (int(cx - w * 0.42), int(cy + h * 0.14)),
        (int(cx - w * 0.46), int(cy - h * 0.02))], max(2, w // 22))
    return True


def _centaur(surf, w, h, c, phase, state):
    """Deep horse barrel with a humanoid torso rising from the withers.

    The barrel has to be genuinely deep. Drawn flat it looked like a
    plank on four sticks, and the whole silhouette depends on reading
    "horse" before you read "person on top of it".
    """
    cx, cy = w // 2, int(h * 0.54)
    dark, light = _shade(c, 0.6), _shade(c, 1.3)
    leg_w = max(3, int(w * 0.07))
    # Legs a touch darker than the barrel but not black — at _shade 0.6
    # they disappeared into a dark map entirely.
    leg_c = _shade(c, 0.78)
    for i, fx in enumerate((-0.26, -0.17, 0.02, 0.11)):
        step = math.sin((phase + i * 0.25) * math.tau) * h * 0.05
        knee = int(cy + h * 0.20)
        pygame.draw.lines(surf, leg_c, False, [
            (int(cx + fx * w), cy + int(h * 0.06)),
            (int(cx + fx * w + (w * 0.02 if i > 1 else -w * 0.02)), knee),
            (int(cx + fx * w), int(cy + h * 0.38 + step))], leg_w)
    # Barrel — long and shallow. Drawn round it read as a beetle; a
    # horse's body is much wider than it is deep.
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.34), cy - int(h * 0.10),
        int(w * 0.52), int(h * 0.21)))
    pygame.draw.arc(surf, light, pygame.Rect(
        cx - int(w * 0.30), cy - int(h * 0.09),
        int(w * 0.44), int(h * 0.16)), 0.3, 2.8, max(2, w // 34))
    # Haunch over the back legs
    pygame.draw.circle(surf, c, (cx - int(w * 0.22), cy),
                       max(3, int(min(w, h) * 0.105)))
    # Tail, hanging from the rump
    pygame.draw.lines(surf, light, False, [
        (cx - int(w * 0.32), cy - int(h * 0.03)),
        (int(cx - w * 0.40), cy + int(h * 0.06)),
        (int(cx - w * 0.40),
         int(cy + h * (0.24 + 0.04 * math.sin(phase * math.tau))))],
        max(3, w // 20))
    # Human half, standing clear of the withers. It has to be narrow,
    # tall and a different shade or horse and rider merge into one
    # shapeless brown lump — which is exactly what the first pass did.
    waist_x = cx + int(w * 0.13)
    torso = pygame.Rect(0, 0, int(w * 0.15), int(h * 0.26))
    torso.midbottom = (waist_x, cy - int(h * 0.08))
    pygame.draw.line(surf, light, (waist_x, cy - int(h * 0.06)),
                     (waist_x, torso.bottom), max(3, w // 18))
    pygame.draw.rect(surf, light, torso, border_radius=max(2, w // 22))
    pygame.draw.rect(surf, dark, torso, max(1, w // 36),
                     border_radius=max(2, w // 22))
    # Shoulders, so the torso is not a bare post
    pygame.draw.line(surf, light,
                     (torso.left - int(w * 0.04), torso.top + int(h * 0.03)),
                     (torso.right + int(w * 0.04), torso.top + int(h * 0.03)),
                     max(2, w // 26))
    pygame.draw.circle(surf, (235, 200, 165),
                       (torso.centerx, torso.top - int(h * 0.05)),
                       max(3, int(min(w, h) * 0.085)))
    # Drawn bow, held out front and pale enough to see
    pull = math.sin(phase * math.tau) * w * 0.02
    bx = int(cx + w * 0.34)
    top = (bx, int(cy - h * 0.46))
    bot = (bx, int(cy - h * 0.10))
    pygame.draw.lines(surf, (208, 168, 108), False, [
        top, (int(bx + w * 0.08), int(cy - h * 0.28)), bot],
        max(2, w // 26))
    pygame.draw.line(surf, (245, 242, 235), top,
                     (int(bx - w * 0.06 - pull), int(cy - h * 0.28)),
                     max(1, w // 40))
    pygame.draw.line(surf, (245, 242, 235),
                     (int(bx - w * 0.06 - pull), int(cy - h * 0.28)), bot,
                     max(1, w // 40))
    return True


def _lycanthrope(surf, w, h, c, phase, state):
    """Hunched beast-headed biped — werewolves and their cousins.

    Halfway between ``_humanoid`` and ``_quadruped`` on purpose: upright
    legs, a forward-leaning spine and a muzzle, so it reads as "man that
    is also a wolf" rather than as either one.
    """
    cx = w // 2
    cy = int(h * 0.52 + _bob(phase, h * 0.02))
    dark, light = _shade(c, 0.6), _shade(c, 1.2)
    for side, off in ((-1, 0.0), (1, 0.5)):
        f = math.sin((phase + off) * math.tau) * w * 0.04
        knee = (int(cx + side * w * 0.13), cy + int(h * 0.20))
        pygame.draw.lines(surf, dark, False, [
            (cx, cy + int(h * 0.10)), knee,
            (int(cx + side * w * 0.07 + f), int(h * 0.93))],
            max(2, w // 16))
    # Hunched torso, leaning forward
    pygame.draw.polygon(surf, c, [
        (cx - int(w * 0.14), cy + int(h * 0.12)),
        (cx - int(w * 0.06), cy - int(h * 0.18)),
        (cx + int(w * 0.14), cy - int(h * 0.14)),
        (cx + int(w * 0.12), cy + int(h * 0.12))])
    # Long arms with claws
    for side in (-1, 1):
        sw = math.sin((phase + (0.5 if side > 0 else 0.0)) * math.tau)
        hand = (int(cx + side * w * 0.24), int(cy + h * (0.16 + 0.04 * sw)))
        pygame.draw.line(surf, dark, (cx + side * int(w * 0.10),
                                      cy - int(h * 0.10)), hand,
                         max(2, w // 20))
        for k in (-1, 0, 1):
            pygame.draw.line(surf, (240, 240, 230), hand,
                             (hand[0] + side * int(w * 0.06),
                              hand[1] + int(h * 0.05) + k * max(1, h // 24)),
                             max(1, w // 36))
    # Wolf head with muzzle and ears
    hx, hy = cx + int(w * 0.10), cy - int(h * 0.27)
    hr = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, light, (hx, hy), hr)
    pygame.draw.polygon(surf, light, [
        (hx + hr // 2, hy - hr // 3),
        (int(hx + w * 0.16), hy + hr // 3),
        (hx + hr // 2, hy + hr)])
    for side in (-1, 1):
        pygame.draw.polygon(surf, dark, [
            (hx + side * hr // 2, hy - hr + 1),
            (hx + side * hr, hy - hr + 1),
            (int(hx + side * hr * 0.8), int(hy - h * 0.14))])
    pygame.draw.circle(surf, (255, 215, 90), (int(hx + w * 0.03), hy),
                       max(1, hr // 4))
    return True


def _crustacean(surf, w, h, c, phase, state):
    """Low shell, two big pincers, spindly legs — crabs, chuuls, chitin."""
    cx, cy = w // 2, int(h * 0.58)
    dark, light = _shade(c, 0.55), _shade(c, 1.25)
    for side in (-1, 1):
        for k in range(3):
            step = math.sin((phase + k * 0.3) * math.tau) * h * 0.03
            pygame.draw.lines(surf, dark, False, [
                (cx + side * int(w * 0.16), cy + int(h * 0.02)),
                (int(cx + side * w * (0.28 + 0.04 * k)),
                 int(cy + h * 0.10 + step)),
                (int(cx + side * w * (0.26 + 0.05 * k)),
                 int(cy + h * 0.30))], max(1, w // 28))
    shell = pygame.Rect(cx - int(w * 0.24), cy - int(h * 0.16),
                        int(w * 0.48), int(h * 0.28))
    pygame.draw.ellipse(surf, c, shell)
    pygame.draw.arc(surf, light, shell.inflate(-w // 8, -h // 10),
                    0.4, 2.7, max(2, w // 26))
    # Pincers, opening and closing
    gape = 0.25 + 0.25 * abs(math.sin(phase * math.tau))
    for side in (-1, 1):
        px = int(cx + side * w * 0.32)
        py = int(cy - h * 0.20)
        pygame.draw.line(surf, dark, (cx + side * int(w * 0.19),
                                      cy - int(h * 0.06)), (px, py),
                         max(2, w // 24))
        for sign in (-1, 1):
            pygame.draw.line(surf, light, (px, py),
                             (int(px + side * w * 0.13 * math.cos(gape * sign)),
                              int(py - h * 0.16 * math.sin(gape * sign + 0.6))),
                             max(2, w // 28))
    for side in (-1, 1):
        ex = cx + side * int(w * 0.07)
        pygame.draw.line(surf, dark, (ex, cy - int(h * 0.14)),
                         (ex, int(cy - h * 0.26)), max(1, w // 34))
        pygame.draw.circle(surf, (250, 240, 200), (ex, int(cy - h * 0.27)),
                           max(1, int(w * 0.028)))
    return True


def _dinosaur(surf, w, h, c, phase, state):
    """Heavy bipedal saurian — deep chest, counterweight tail, big jaws.

    Level-backed rather than upright, which is what keeps it from
    reading as a wingless dragon: no neck arch, and the tail is as long
    as the body.
    """
    cx, cy = w // 2, int(h * 0.50)
    dark, light = _shade(c, 0.55), _shade(c, 1.25)
    stride = math.sin(phase * math.tau)
    # Tail: as long as the body and as thick at the root, tapering.
    # Drawn thin it read as an ostrich's neck pointing the wrong way.
    for fx, fy, tw in ((-0.06, 0.04, 0.13), (-0.20, 0.02, 0.095),
                       (-0.32, 0.00, 0.06), (-0.42, -0.01, 0.032)):
        pygame.draw.line(
            surf, light,
            (int(cx + fx * w), int(cy + fy * h)),
            (int(cx + (fx - 0.13) * w),
             int(cy + (fy - 0.015 - 0.02 * stride) * h)),
            max(2, int(h * tw)))
    # Chest — long, not round. A circle read as a beach ball with a
    # head glued on; a real theropod is a horizontal wedge.
    pygame.draw.ellipse(surf, c, pygame.Rect(
        cx - int(w * 0.20), cy - int(h * 0.14),
        int(w * 0.40), int(h * 0.26)))
    # Two heavy legs with a backward-bending ankle
    for ph, depth in ((0.5, 0.85), (0.0, 1.0)):
        step = math.sin((phase + ph) * math.tau) * w * 0.05
        col = _shade(c, 0.75) if depth == 1.0 else dark
        pygame.draw.lines(surf, col, False, [
            (cx + int(w * 0.02), cy + int(h * 0.10)),
            (int(cx + w * 0.13 + step * 0.4), cy + int(h * 0.24)),
            (int(cx + w * 0.03 + step * 0.8), cy + int(h * 0.34)),
            (int(cx + w * 0.12 + step), int(h * 0.93))],
            max(3, int(w * 0.075 * depth)))
    # Stubby arms tucked under the chest
    pygame.draw.line(surf, dark, (cx + int(w * 0.13), cy - int(h * 0.01)),
                     (cx + int(w * 0.21), cy + int(h * 0.08)),
                     max(2, w // 24))
    # Head: massive boxy jaws on a short level neck
    hx, hy = cx + int(w * 0.28), cy - int(h * 0.20)
    pygame.draw.line(surf, c, (cx + int(w * 0.14), cy - int(h * 0.12)),
                     (hx, hy), max(4, w // 12))
    jaw = abs(math.sin(phase * math.tau)) * h * (0.02 if state == "idle"
                                                 else 0.06)
    pygame.draw.polygon(surf, light, [
        (hx - int(w * 0.08), hy - int(h * 0.09)),
        (int(cx + w * 0.46), hy - int(h * 0.03)),
        (int(cx + w * 0.44), int(hy + h * 0.02)),
        (hx - int(w * 0.07), int(hy + h * 0.03))])
    pygame.draw.polygon(surf, dark, [
        (hx - int(w * 0.06), int(hy + h * 0.04 + jaw)),
        (int(cx + w * 0.43), int(hy + h * 0.04 + jaw)),
        (hx - int(w * 0.05), int(hy + h * 0.10 + jaw))])
    # Teeth along the upper jaw
    for k in range(3):
        tx = int(cx + w * (0.30 + 0.05 * k))
        pygame.draw.line(surf, (250, 246, 232), (tx, int(hy + h * 0.02)),
                         (tx, int(hy + h * 0.05)), max(1, w // 44))
    pygame.draw.circle(surf, (255, 200, 70),
                       (hx - int(w * 0.01), hy - int(h * 0.04)),
                       max(1, int(w * 0.03)))
    return True


PAINTERS = {
    "dragon":     _dragon,
    "beholder":   _beholder,
    "ooze":       _ooze,
    "skeleton":   _skeleton,
    "shambler":   _shambler,
    "vampire":    _vampire,
    "ghost":      _ghost,
    "giant":      _giant,
    "devil":      _devil,
    "celestial":  _celestial,
    "elemental":  _elemental,
    "construct":  _construct,
    "spider":     _spider,
    "serpent":    _serpent,
    "tentacled":  _tentacled,
    "plant":      _plant,
    "swarm":      _swarm,
    "fey":        _fey,
    "quadruped":  _quadruped,
    "humanoid":   _humanoid,
    "goblinoid":  _goblinoid,
    "armored":    _armored,
    "caster":     _caster,
    "bird":       _bird,
    "bat":        _bat,
    "aquatic":    _aquatic,
    "hydra":      _hydra,
    "centaur":    _centaur,
    "lycanthrope": _lycanthrope,
    "crustacean": _crustacean,
    "dinosaur":   _dinosaur,
}

DEFAULT_KIND = "humanoid"


def kinds() -> list:
    return sorted(PAINTERS)


def has_painter(kind: str) -> bool:
    return kind in PAINTERS


# ===================================================================== #
# Classification
# ===================================================================== #
# Name keywords win over the creature type, because "Bone Devil" is a
# devil and "Vampire Spellcaster" is a vampire regardless of how the
# stat block files it.
_NAME_RULES = (
    ("beholder",  ("beholder", "death tyrant", "spectator", "gazer")),
    ("dragon",    ("dragon", "dracolich", "wyvern", "drake", "wyrm",
                   "lohikäärme")),
    ("ooze",      ("ooze", "slime", "jelly", "gelatinous", "pudding",
                   "mold", "alghoul")),
    ("skeleton",  ("skeleton", "bone ", "luuranko", "lich", "demilich",
                   "warhorse skeleton")),
    # The Vigil priests Dimerius turned carry Latin titles rather than
    # the word "vampire", and were reading as generic shamblers.
    ("vampire",   ("vampire", "vampyyri", "dimerius", "nosferatu",
                   "sanguis", "sanguin", "verikuoro", "nocturnus")),
    ("ghost",     ("ghost", "spectre", "specter", "shadow", "wraith",
                   "banshee", "poltergeist", "will-o", "aave", "varjo")),
    ("shambler",  ("zombie", "ghoul", "mummy", "wight", "revenant",
                   "abominatio", "flesh golem", "shambling")),
    ("spider",    ("spider", "hämähäkki", "scorpion", "insect", "beetle",
                   "ankheg", "drider")),
    ("serpent",   ("snake", "serpent", "naga", "couatl", "worm",
                   "käärme", "viper", "constrictor", "fire snake")),
    ("tentacled", ("mind flayer", "aboleth", "kraken", "cloaker",
                   "otyugh", "roper", "intellect devourer", "lonkero",
                   "tentacle")),
    ("swarm",     ("swarm", "parvi")),
    ("hydra",     ("hydra",)),
    ("lycanthrope", ("werewolf", "wererat", "weretiger", "werebear",
                     "wereboar", "lycanthrope", "ihmissusi", "jackalwere")),
    ("centaur",   ("centaur", "kentauri", "wemic", "sphinx")),
    ("dinosaur",  ("tyrannosaurus", "allosaurus", "raptor", "deinonychus",
                   "ankylosaurus", "plesiosaurus", "pteranodon",
                   "dinosaur", "hadrosaurus", "quetzalcoatlus")),
    ("crustacean", ("crab", "chuul", "lobster", "rapu", "tortoise",
                    "turtle", "chitine", "thri-kreen")),
    ("aquatic",   ("shark", "sahuagin", "merfolk", "merrow", "koalinth",
                   "sea horse", "quipper", "reef shark", "marid",
                   "kalmari", "squid", "octopus")),
    ("bat",       ("giant bat", "dire bat", "stirge", "lepakko")),
    # Substrings are matched anywhere in the name, so these are chosen
    # to be ones that cannot appear inside an unrelated monster: bare
    # "roc" is inside "Crocodile", "owl" inside "Owlbear", "hai" inside
    # "Chain Devil". Exact names go in _EXACT_NAMES below instead.
    ("bird",      ("eagle", "giant owl", "hawk", "vulture",
                   "harpy", "aarakocra", "cockatrice", "peryton",
                   "kenku", "griffon", "hippogriff",
                   "lintu", "kotka", "pteranodon")),
    ("construct", ("golem", "automat", "colossus", "titaani", "armor",
                   "helmed", "guardian", "clockwork", "kellopeli",
                   "a.e.g.i.s", "modron", "scarecrow")),
    ("elemental", ("elemental", "mephit", "salamander", "gargoyle",
                   "efreeti", "phoenix", "galeb", "azer", "invisible stalker")),
    ("celestial", ("deva", "planetar", "solar", "empyrean", "angel",
                   "unicorn", "pegasus")),
    ("devil",     ("devil", "demon", "fiend", "balor", "marilith",
                   "nalfeshnee", "rakshasa", "succubus", "incubus",
                   "imp", "quasit", "hezrou", "glabrezu", "vrock",
                   "demogorgon", "orcus", "erinyes", "barbed",
                   "hell hound", "cambion", "night hag")),
    ("giant",     ("giant", "ogre", "ettin", "troll", "oni", "cyclops",
                   "jätti")),
    ("plant",     ("treant", "tree", "shambling mound", "blight",
                   "twig", "vine", "myconid", "mushroom")),
    ("fey",       ("sprite", "pixie", "dryad", "satyr", "hag",
                   "blink dog", "quickling", "faerie")),
    # Humanoid sub-shapes. These sit before "quadruped" because
    # "bugbear" would otherwise be caught by "bear", and after every
    # monster rule above because a "Goblin Boss Vampire" is a vampire.
    ("goblinoid", ("goblin", "kobold", "bugbear", "gnome", "halfling",
                   "xvart", "grimlock", "jermlaine", "boggle", "hiisi",
                   "menninkäinen", "kääpiö", "gremlin")),
    ("armored",   ("knight", "guard", "veteran", "gladiator", "soldier",
                   "myrmidon", "legionnaire", "sentinel", "champion",
                   "warlord", "ritari", "vartija", "sotilas", "hoplite",
                   "man-at-arms", "praetorian")),
    ("caster",    ("mage", "wizard", "sorcerer", "warlock", "priest",
                   "acolyte", "cultist", "necromancer", "apprentice",
                   "evoker", "illusionist", "conjurer", "abjurer",
                   "enchanter", "transmuter", "diviner", "druid",
                   "shaman", "velho", "pappi", "noita", "loitsija",
                   "spellcaster", "arcanist")),
    ("quadruped", ("wolf", "bear", "tiger", "lion", "boar", "horse",
                   "mastiff", "panther", "ape", "rhino", "elk",
                   "hyena", "jackal", "rat", "hound", "worg",
                   "bulette", "owlbear", "displacer", "griffon",
                   "hippogriff", "susi", "karhu", "lisko", "lizard",
                   "basilisk", "chimera", "manticore", "minotaur",
                   "gnoll", "cat", "crocodile", "shark", "mammoth",
                   "triceratops", "tyrannosaurus", "raptor")),
)

# Creature type → silhouette when the name gives nothing away.
_TYPE_RULES = {
    "Dragon":      "dragon",
    "Ooze":        "ooze",
    "Undead":      "shambler",
    "Fiend":       "devil",
    "Celestial":   "celestial",
    "Elemental":   "elemental",
    "Construct":   "construct",
    "Giant":       "giant",
    "Plant":       "plant",
    "Fey":         "fey",
    "Aberration":  "tentacled",
    "Beast":       "quadruped",
    "Monstrosity": "quadruped",
    "Humanoid":    "humanoid",
    "Swarm of Tiny Beasts": "swarm",
}


# Whole-name matches, for creatures whose name is too short to search
# for safely: "roc" hides inside "Crocodile", "owl" inside "Owlbear",
# "bat" inside any homebrew "Battle Priest".
_EXACT_NAMES = {
    "roc": "bird",
    "giant eagle": "bird",
    "raven": "bird",
    "owl": "bird",
    "bat": "bat",
    "crab": "crustacean",
    "giant crab": "crustacean",
}


def kind_for_stats(stats) -> str:
    """Which silhouette suits this creature?

    Exact names first, then name keywords (a "Bone Devil" is a devil,
    not a skeleton — the rules are ordered so the more specific reading
    wins), then the creature type, then a plain humanoid.
    """
    name = (getattr(stats, "name", "") or "").lower().strip()
    ctype = getattr(stats, "creature_type", "") or ""
    if name in _EXACT_NAMES:
        return _EXACT_NAMES[name]
    # Devil beats skeleton for "Bone Devil"; check the devil rule first
    # for any name that mentions one.
    if "devil" in name or "demon" in name:
        return "devil"
    for kind, words in _NAME_RULES:
        if any(word in name for word in words):
            return kind
    if "swarm" in ctype.lower():
        return "swarm"
    return _TYPE_RULES.get(ctype, DEFAULT_KIND)


# ===================================================================== #
# Species colour
# ===================================================================== #
# A red dragon and a white dragon are the same monster mechanically and
# completely different at the table. Tokens used to take one colour per
# creature TYPE, so every dragon in the library was the same shade of
# scaly brown. This table gives the ones whose colour is part of their
# name — and a handful of others everybody pictures a certain way — the
# right hue. The token's outer ring still carries friend/foe, so this
# only repaints the silhouette inside it.
_SPECIES_COLORS = {
    # Chromatic dragons
    "red dragon":     (196,  58,  40),
    "blue dragon":    ( 58, 118, 205),
    "green dragon":   ( 74, 150,  70),
    "black dragon":   ( 74,  68,  84),
    "white dragon":   (206, 224, 238),
    # Metallic dragons
    "brass dragon":   (198, 158,  70),
    "bronze dragon":  (166, 118,  62),
    "copper dragon":  (188, 106,  62),
    "gold dragon":    (231, 190,  74),
    "silver dragon":  (196, 206, 218),
    # Gem and exotic dragons
    "amethyst dragon": (162, 108, 206),
    "crystal dragon": (208, 226, 236),
    "emerald dragon": ( 58, 174, 124),
    "sapphire dragon": ( 74, 106, 208),
    "topaz dragon":   (216, 176,  96),
    "shadow dragon":  ( 62,  58,  76),
    "deep dragon":    (108,  76, 148),
    "faerie dragon":  (226, 128, 200),
    "dracolich":      (146, 154, 128),
    "dragon turtle":  ( 66, 128, 118),
    "wyvern":         (128, 104,  84),
    # Elementals and golems, whose material is the whole point
    "fire elemental": (232, 122,  46),
    "water elemental": ( 70, 142, 196),
    "air elemental":  (196, 214, 228),
    "earth elemental": (132, 112,  86),
    "ice elemental":  (172, 214, 232),
    "magma":          (222,  98,  46),
    "iron golem":     (128, 134, 146),
    "stone golem":    (140, 136, 126),
    "clay golem":     (176, 128,  92),
    "flesh golem":    (142, 168, 130),
    # Common creatures with a colour everybody already pictures
    "troll":          (104, 148,  86),
    "ogre":           (168, 132,  92),
    "orc":            (108, 142,  92),
    "goblin":         (126, 156,  82),
    "hobgoblin":      (176,  86,  62),
    "kobold":         (188, 116,  70),
    "zombie":         (126, 142, 108),
    "skeleton":       (214, 208, 186),
    "ghost":          (176, 208, 216),
    "vampire":        (150,  54,  66),
    "beholder":       (168, 120, 170),
    "mind flayer":    (140, 106, 168),
    "gelatinous cube": (150, 206, 178),
    "treant":         (110, 128,  74),
    "wolf":           (128, 126, 132),
    "bear":           (126,  92,  62),
    "spider":         ( 92,  80, 104),
    "hydra":          ( 88, 146, 108),
    "shark":          (118, 136, 150),
    "sahuagin":       ( 84, 142, 132),
    "merrow":         ( 72, 122, 128),
    "harpy":          (168, 148, 106),
    "roc":            (142, 118,  96),
    "eagle":          (156, 122,  84),
    "crab":           (188, 108,  82),
    "chuul":          (156, 132,  84),
    "centaur":        (152, 116,  78),
    "tyrannosaurus":  (128, 126,  92),
    "velociraptor":   (156, 136,  86),
    "wererat":        (126, 116, 108),
    "weretiger":      (206, 152,  70),
    "knight":         (146, 152, 168),
    "gladiator":      (178, 140,  92),
    "priest":         (222, 214, 190),
    "necromancer":    ( 96,  88, 122),
    "xvart":          ( 84, 116, 178),
}

# Longest key first, so "shadow dragon" beats "dragon" and "adult red
# dragon" still finds "red dragon".
_SPECIES_ORDER = sorted(_SPECIES_COLORS, key=len, reverse=True)


def species_color(stats, fallback=(180, 90, 90)):
    """Signature colour for this creature, or ``fallback``.

    Matches on the longest name fragment, so "Ancient White Dragon" is
    white and "Adult Red Dragon" is red without either needing its own
    entry.
    """
    name = (getattr(stats, "name", "") or "").lower()
    if not name:
        return tuple(fallback[:3])
    for key in _SPECIES_ORDER:
        if key in name:
            return _SPECIES_COLORS[key]
    return tuple(fallback[:3])


def draw_creature(surf, w: int, h: int, *, kind: str = DEFAULT_KIND,
                  color=(180, 90, 90), state: str = "idle",
                  phase: float = 0.0) -> bool:
    """Paint a creature silhouette. Returns True when something was drawn.

    ``phase`` (0..1) drives every animation; ``state`` nudges intensity
    ("attack" and "walk" move more than "idle"). Never raises — a bad
    kind falls back to the plain humanoid.
    """
    if pygame is None or surf is None or w <= 0 or h <= 0:
        return False
    painter = PAINTERS.get(kind, PAINTERS[DEFAULT_KIND])
    p = float(phase) % 1.0
    if state == "attack":
        p = min(1.0, p * 1.6)
    try:
        painter(surf, int(w), int(h), tuple(color[:3]), p, state)
    except Exception:
        # A silhouette must never take the battle map down with it.
        pygame.draw.circle(surf, tuple(color[:3]), (w // 2, h // 2),
                           max(2, min(w, h) // 3))
    if state == "hurt":
        flash = pygame.Surface((w, h), pygame.SRCALPHA)
        flash.fill((255, 60, 60, 90))
        surf.blit(flash, (0, 0))
    return True
