"""Procedural character tokens — code-drawn humanoids with idle /
walk / attack / hurt animation states.

No spritesheets, no asset files: every body part is a circle / oval /
rounded rect drawn with pygame primitives, then offset / rotated by a
small per-state phase function so the figure breathes (idle), bobs
(walk), or thrusts a weapon (attack).

API:
    draw_character(surf, w, h, *, kind="warrior",
                    color=(...), state="idle", phase=0.0)

``phase`` is a 0..1 float that callers advance every frame
(``(time_ms / 600) % 1.0`` for a 600ms cycle is typical).

States:
    "idle"   — gentle vertical breathing
    "walk"   — leg/arm swing, 2-frame
    "attack" — one-shot windup -> swing
    "hurt"   — shake + red flash overlay

Kinds (different head/torso/weapon shapes):
    "warrior"   — broad shoulders, sword
    "ranger"    — slim, bow
    "mage"      — pointy hat, staff
    "rogue"     — hooded, daggers
    "cleric"    — round body, mace
    "druid"     — leafy hat, staff
    "monster"   — generic angular grunt
    "beast"     — quadruped silhouette (for wild shape / familiars)
"""
from __future__ import annotations

import math

try:
    import pygame  # type: ignore
except ImportError:
    pygame = None


# --------------------------------------------------------------------- #
# Colour helpers
# --------------------------------------------------------------------- #
def _shade(c, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in c[:3])


# --------------------------------------------------------------------- #
# State phase generators
# --------------------------------------------------------------------- #
def _state_offsets(state: str, phase: float) -> dict:
    """Return per-part offsets / rotations driven by ``phase`` (0..1).

    Returned keys:
        body_y      — bob in pixels
        arm_swing   — radians
        leg_swing   — radians (one-leg up, one-leg down)
        weapon_arc  — radians (extra arm rotation for attacks)
        shake_x     — small horizontal jitter (hurt state)
        red_flash   — 0..1 overlay alpha factor (hurt)
    """
    p = max(0.0, min(1.0, float(phase)))
    if state == "walk":
        return {
            "body_y":     int(2 * math.sin(p * math.tau * 2)),
            "arm_swing":  0.4 * math.sin(p * math.tau),
            "leg_swing":  0.5 * math.sin(p * math.tau),
            "weapon_arc": 0.0,
            "shake_x":    0,
            "red_flash":  0.0,
        }
    if state == "attack":
        # 0..0.4 windup, 0.4..0.7 strike, 0.7..1 recovery
        if p < 0.4:
            arc = -0.6 * (p / 0.4)              # raise weapon up-and-back
        elif p < 0.7:
            arc = -0.6 + 1.6 * ((p - 0.4) / 0.3)   # full swing forward
        else:
            arc = 1.0 - 1.0 * ((p - 0.7) / 0.3)    # ease back to neutral
        return {
            "body_y":     0,
            "arm_swing":  0.0,
            "leg_swing":  0.0,
            "weapon_arc": arc,
            "shake_x":    0,
            "red_flash":  0.0,
        }
    if state == "hurt":
        # Two horizontal jitter cycles + red flash that fades
        return {
            "body_y":     0,
            "arm_swing":  0.0,
            "leg_swing":  0.0,
            "weapon_arc": 0.0,
            "shake_x":    int(3 * math.sin(p * math.tau * 3)),
            "red_flash":  max(0.0, 1.0 - p) * 0.6,
        }
    # idle (default) — slow breathing
    return {
        "body_y":     int(1.5 * math.sin(p * math.tau)),
        "arm_swing":  0.0,
        "leg_swing":  0.0,
        "weapon_arc": 0.0,
        "shake_x":    0,
        "red_flash":  0.0,
    }


# --------------------------------------------------------------------- #
# Part painters
# --------------------------------------------------------------------- #
def _draw_body(surf, cx, cy, w, h, color):
    body_w = max(6, int(w * 0.35))
    body_h = max(8, int(h * 0.30))
    rect = pygame.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)
    pygame.draw.rect(surf, color, rect, border_radius=4)
    pygame.draw.rect(surf, _shade(color, 0.65), rect, 1, border_radius=4)


def _draw_head(surf, cx, cy, w, h, skin):
    r = max(3, int(min(w, h) * 0.13))
    pygame.draw.circle(surf, skin, (cx, cy), r)
    pygame.draw.circle(surf, _shade(skin, 0.6), (cx, cy), r, 1)
    return r


def _draw_legs(surf, cx, cy, w, h, color, swing):
    leg_h = max(4, int(h * 0.20))
    leg_w = max(2, int(w * 0.10))
    sx = int(swing * 4)
    left = pygame.Rect(cx - leg_w - 1 + sx, cy, leg_w, leg_h)
    right = pygame.Rect(cx + 1 - sx, cy, leg_w, leg_h)
    pygame.draw.rect(surf, color, left, border_radius=2)
    pygame.draw.rect(surf, color, right, border_radius=2)


def _draw_arm(surf, cx, cy, w, h, color, swing, side=1):
    """side: -1 = left, 1 = right."""
    arm_h = max(4, int(h * 0.18))
    arm_w = max(2, int(w * 0.08))
    sx = int(swing * 4 * side)
    rect = pygame.Rect(cx + side * (w * 0.18) - arm_w // 2 + sx,
                        cy, arm_w, arm_h)
    pygame.draw.rect(surf, color, rect, border_radius=2)


def _draw_weapon(surf, cx, cy, w, h, kind, weapon_arc):
    """Weapon held in the right arm, rotated by weapon_arc radians."""
    if pygame is None:
        return
    # Anchor where the right hand is
    hand_x = cx + int(w * 0.22)
    hand_y = cy + int(h * 0.15)
    length = int(w * 0.55)
    angle = -math.pi / 4 + weapon_arc   # pointing up-and-forward
    end_x = hand_x + int(length * math.cos(angle))
    end_y = hand_y + int(length * math.sin(angle))
    if kind in ("warrior", "monster"):
        # Sword: silver blade + pommel
        pygame.draw.line(surf, (210, 215, 230),
                          (hand_x, hand_y), (end_x, end_y), 3)
        pygame.draw.circle(surf, (140, 110, 60), (hand_x, hand_y), 3)
    elif kind == "ranger":
        # Bow: arc
        bow_pts = []
        for i in range(7):
            f = i / 6
            bx = hand_x + int(length * 0.6 * math.cos(angle))
            by = hand_y + int(length * 0.6 * math.sin(angle))
            cur = math.pi / 2 + f * math.pi
            x = int(bx + 8 * math.cos(angle + math.pi / 2)
                    * math.sin(f * math.pi))
            y = int(by + 8 * math.sin(angle + math.pi / 2)
                    * math.sin(f * math.pi))
            bow_pts.append((x, y))
        if len(bow_pts) > 1:
            pygame.draw.lines(surf, (140, 90, 50), False, bow_pts, 2)
    elif kind in ("mage", "druid", "cleric"):
        # Staff / mace: thick brown line + glowing top
        pygame.draw.line(surf, (110, 75, 40),
                          (hand_x, hand_y), (end_x, end_y), 3)
        glow = (90, 200, 120) if kind == "druid" else \
                (120, 200, 240) if kind == "mage" else \
                (240, 220, 120)
        pygame.draw.circle(surf, glow, (end_x, end_y), 4)
    elif kind == "rogue":
        # Two daggers, smaller
        pygame.draw.line(surf, (200, 200, 220),
                          (hand_x, hand_y),
                          (end_x // 2 + hand_x // 2,
                           end_y // 2 + hand_y // 2), 2)


def _draw_kind_extras(surf, cx, head_cy, w, h, kind, head_r):
    """Hat / hood / horns drawn on top of the head."""
    if kind == "mage":
        # Pointy wizard hat
        tip = (cx, head_cy - head_r * 3)
        left = (cx - head_r, head_cy - head_r // 2)
        right = (cx + head_r, head_cy - head_r // 2)
        pygame.draw.polygon(surf, (60, 40, 100), [tip, left, right])
        pygame.draw.line(surf, (220, 180, 60),
                          (cx - head_r, head_cy - head_r // 2),
                          (cx + head_r, head_cy - head_r // 2), 2)
    elif kind == "druid":
        # Leafy circlet
        pygame.draw.arc(surf, (40, 130, 60),
                         pygame.Rect(cx - head_r - 1,
                                      head_cy - head_r - 2,
                                      head_r * 2 + 2, head_r),
                         0, math.pi, 2)
    elif kind == "rogue":
        # Hood — a darker arc above the head
        pygame.draw.arc(surf, (40, 40, 60),
                         pygame.Rect(cx - head_r - 2,
                                      head_cy - head_r - 3,
                                      head_r * 2 + 4, head_r * 2),
                         math.pi, math.pi * 2, 3)
    elif kind == "monster":
        # Two angular horns
        for s in (-1, 1):
            tip = (cx + s * head_r, head_cy - head_r * 2)
            base = (cx + s * head_r // 2, head_cy - head_r // 2)
            pygame.draw.line(surf, (60, 30, 30), base, tip, 2)


def _draw_quadruped(surf, cx, cy, w, h, color):
    """Beast / familiar silhouette — for wild-shape bears, owls etc."""
    # Body — wide oval
    body = pygame.Rect(cx - int(w * 0.30), cy - int(h * 0.05),
                        int(w * 0.60), int(h * 0.25))
    pygame.draw.ellipse(surf, color, body)
    pygame.draw.ellipse(surf, _shade(color, 0.65), body, 1)
    # Head — smaller circle attached on the right
    head_cx = cx + int(w * 0.25)
    head_cy = cy + int(h * 0.0)
    head_r = max(3, int(min(w, h) * 0.10))
    pygame.draw.circle(surf, color, (head_cx, head_cy), head_r)
    pygame.draw.circle(surf, _shade(color, 0.6), (head_cx, head_cy),
                        head_r, 1)
    # Legs — four short rectangles
    leg_h = max(3, int(h * 0.12))
    leg_w = max(2, int(w * 0.06))
    for i, dx in enumerate((-0.22, -0.05, 0.10, 0.22)):
        lx = cx + int(w * dx)
        pygame.draw.rect(surf, _shade(color, 0.7),
                          pygame.Rect(lx, cy + int(h * 0.18),
                                       leg_w, leg_h),
                          border_radius=2)


# --------------------------------------------------------------------- #
# Public draw
# --------------------------------------------------------------------- #
def draw_character(surf, w: int, h: int, *,
                    kind: str = "warrior",
                    color=(200, 80, 80),
                    state: str = "idle",
                    phase: float = 0.0) -> bool:
    """Draw a procedural character onto ``surf``. Returns True on
    success, False when pygame isn't available."""
    if pygame is None or surf is None:
        return False
    off = _state_offsets(state, phase)
    cx = w // 2 + off["shake_x"]
    cy = h // 2 + off["body_y"]

    if kind == "beast":
        _draw_quadruped(surf, cx, cy, w, h, color)
        return True

    # 1. Legs
    legs_y = cy + int(h * 0.18)
    _draw_legs(surf, cx, legs_y, w, h, _shade(color, 0.65),
                off["leg_swing"])
    # 2. Body / torso
    _draw_body(surf, cx, cy, w, h, color)
    # 3. Off-arm
    _draw_arm(surf, cx, cy + int(h * 0.05), w, h,
               _shade(color, 0.85), -off["arm_swing"], side=-1)
    # 4. Head
    head_cy = cy - int(h * 0.18)
    head_r = _draw_head(surf, cx, head_cy, w, h, (240, 200, 160))
    _draw_kind_extras(surf, cx, head_cy, w, h, kind, head_r)
    # 5. Weapon (drawn AFTER head so it appears in front)
    _draw_weapon(surf, cx, cy, w, h, kind, off["weapon_arc"])
    # 6. Main arm (holds the weapon)
    _draw_arm(surf, cx, cy + int(h * 0.05), w, h,
               _shade(color, 0.85),
               off["arm_swing"] + off["weapon_arc"] * 0.5, side=1)
    # 7. Hurt overlay (red flash)
    if off["red_flash"] > 0:
        red_alpha = int(120 * off["red_flash"])
        flash = pygame.Surface((w, h), pygame.SRCALPHA)
        flash.fill((255, 60, 60, red_alpha))
        surf.blit(flash, (0, 0))
    return True


# --------------------------------------------------------------------- #
# Class → kind mapping (used by token renderer)
# --------------------------------------------------------------------- #
_CLASS_TO_KIND = {
    "fighter":   "warrior",
    "barbarian": "warrior",
    "paladin":   "warrior",
    "ranger":    "ranger",
    "rogue":     "rogue",
    "wizard":    "mage",
    "sorcerer":  "mage",
    "warlock":   "mage",
    "bard":      "mage",
    "cleric":    "cleric",
    "druid":     "druid",
    "monk":      "warrior",
    "artificer": "mage",
}


def kind_for_entity(entity) -> str:
    """Pick a character kind from an Entity. Wild Shape / summons take
    the "beast" silhouette."""
    if getattr(entity, "is_wild_shaped", False):
        return "beast"
    if getattr(entity, "is_summon", False):
        return "beast"
    if getattr(entity, "is_player", False):
        cls = (entity.stats.character_class or "").lower()
        return _CLASS_TO_KIND.get(cls, "warrior")
    return "monster"
