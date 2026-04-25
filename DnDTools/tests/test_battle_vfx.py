"""Phase 8a — combat VFX class tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from unittest.mock import MagicMock

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from states.battle_vfx import (
    Projectile, Beam, SpellAura, SlashTrail, HealAura,
    make_attack_vfx, make_spell_vfx,
)


def _ent(x, y):
    e = MagicMock()
    e.grid_x = x; e.grid_y = y
    return e


def _action(rng=5, damage_type="slashing"):
    a = MagicMock()
    a.range = rng
    a.damage_type = damage_type
    return a


def _spell(damage_type="fire", aoe_radius=0):
    s = MagicMock()
    s.damage_type = damage_type
    s.aoe_radius = aoe_radius
    return s


class TestLifecycle(unittest.TestCase):
    def test_projectile_advances(self):
        p = Projectile(0, 0, 5, 5, duration=10)
        self.assertEqual(p.life, 10)
        for _ in range(10):
            p.update()
        self.assertLessEqual(p.life, 0)

    def test_beam_advances(self):
        b = Beam(0, 0, 5, 5, duration=8)
        for _ in range(8):
            b.update()
        self.assertLessEqual(b.life, 0)

    def test_aura_advances(self):
        a = SpellAura(5, 5, duration=15)
        for _ in range(15):
            a.update()
        self.assertLessEqual(a.life, 0)

    def test_slash_advances(self):
        s = SlashTrail(5, 5, duration=6)
        for _ in range(6):
            s.update()
        self.assertLessEqual(s.life, 0)

    def test_heal_aura_advances(self):
        h = HealAura(3, 3, duration=20)
        for _ in range(20):
            h.update()
        self.assertLessEqual(h.life, 0)


class TestAttackFactory(unittest.TestCase):
    def test_melee_makes_slash(self):
        att = _ent(5, 5); tgt = _ent(6, 5)
        vfx = make_attack_vfx(att, tgt, _action(rng=5, damage_type="slashing"))
        self.assertIsInstance(vfx, SlashTrail)

    def test_ranged_piercing_makes_arrow(self):
        att = _ent(5, 5); tgt = _ent(15, 5)
        vfx = make_attack_vfx(att, tgt, _action(rng=80, damage_type="piercing"))
        self.assertIsInstance(vfx, Projectile)
        self.assertEqual(vfx.style, "arrow")

    def test_ranged_bludgeoning_makes_stone(self):
        att = _ent(5, 5); tgt = _ent(15, 5)
        vfx = make_attack_vfx(att, tgt, _action(rng=60, damage_type="bludgeoning"))
        self.assertIsInstance(vfx, Projectile)
        self.assertEqual(vfx.style, "stone")

    def test_ranged_fire_makes_bolt(self):
        att = _ent(5, 5); tgt = _ent(15, 5)
        vfx = make_attack_vfx(att, tgt, _action(rng=60, damage_type="fire"))
        self.assertIsInstance(vfx, Projectile)
        self.assertEqual(vfx.style, "bolt")


class TestSpellFactory(unittest.TestCase):
    def test_aoe_spell_makes_aura(self):
        caster = _ent(0, 0); tgt = _ent(5, 5)
        vfx = make_spell_vfx(caster, tgt, _spell("fire", aoe_radius=20))
        self.assertIsInstance(vfx, SpellAura)
        self.assertGreaterEqual(vfx.radius_cells, 1.0)

    def test_single_target_makes_beam(self):
        caster = _ent(0, 0); tgt = _ent(10, 0)
        vfx = make_spell_vfx(caster, tgt, _spell("fire"))
        self.assertIsInstance(vfx, Beam)

    def test_self_aoe_uses_caster_position(self):
        caster = _ent(7, 7)
        vfx = make_spell_vfx(caster, None, _spell("fire", aoe_radius=15))
        self.assertIsInstance(vfx, SpellAura)
        self.assertEqual(vfx.gx, 7)
        self.assertEqual(vfx.gy, 7)

    def test_no_target_no_caster_returns_none(self):
        self.assertIsNone(make_spell_vfx(None, None, _spell("fire")))


class TestDamageColors(unittest.TestCase):
    def test_explicit_color_overrides_damage_type(self):
        p = Projectile(0, 0, 5, 5, color=(1, 2, 3))
        self.assertEqual(p.color, (1, 2, 3))

    def test_fallback_color_for_unknown_damage(self):
        p = Projectile(0, 0, 5, 5, damage_type="weird_unknown")
        # Should not crash, gets default tuple
        self.assertEqual(len(p.color), 3)


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestRendering(unittest.TestCase):
    """Integration: actually invoke draw() on each effect to make sure
    nothing crashes. Skipped when pygame isn't installed."""

    def setUp(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        self.surface = pygame.Surface((400, 400), pygame.SRCALPHA)
        self.gsz = 60
        self.pos = lambda gx, gy: (int(gx * self.gsz), int(gy * self.gsz))

    def test_arrow_renders(self):
        Projectile(0, 0, 4, 4, style="arrow").draw(
            self.surface, self.pos, self.gsz
        )

    def test_bolt_renders(self):
        Projectile(0, 0, 4, 4, style="bolt").draw(
            self.surface, self.pos, self.gsz
        )

    def test_stone_renders(self):
        Projectile(0, 0, 4, 4, style="stone").draw(
            self.surface, self.pos, self.gsz
        )

    def test_mote_renders(self):
        Projectile(0, 0, 4, 4, style="mote").draw(
            self.surface, self.pos, self.gsz
        )

    def test_beam_renders(self):
        Beam(0, 0, 5, 5).draw(self.surface, self.pos, self.gsz)

    def test_aura_renders(self):
        SpellAura(2, 2, radius_cells=2.0).draw(
            self.surface, self.pos, self.gsz
        )

    def test_slash_renders(self):
        SlashTrail(3, 3).draw(self.surface, self.pos, self.gsz)

    def test_heal_renders(self):
        HealAura(3, 3).draw(self.surface, self.pos, self.gsz)


if __name__ == "__main__":
    unittest.main()
