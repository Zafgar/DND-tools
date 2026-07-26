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
    ("vampire",   ("vampire", "vampyyri", "dimerius", "nosferatu")),
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


def kind_for_stats(stats) -> str:
    """Which silhouette suits this creature?

    Name keywords first (a "Bone Devil" is a devil, not a skeleton — the
    rules are ordered so the more specific reading wins), then the
    creature type, then a plain humanoid.
    """
    name = (getattr(stats, "name", "") or "").lower()
    ctype = getattr(stats, "creature_type", "") or ""
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
