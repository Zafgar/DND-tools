"""Phase 9c — procedural character art tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from states.character_art import (
    draw_character, kind_for_entity, _state_offsets, _CLASS_TO_KIND,
)


class _StubStats:
    def __init__(self, character_class=""):
        self.character_class = character_class


class _StubEntity:
    def __init__(self, **kwargs):
        self.is_player = kwargs.get("is_player", False)
        self.is_summon = kwargs.get("is_summon", False)
        self.is_wild_shaped = kwargs.get("is_wild_shaped", False)
        self.stats = _StubStats(kwargs.get("character_class", ""))


class TestStateOffsets(unittest.TestCase):
    def test_idle_returns_dict(self):
        d = _state_offsets("idle", 0.0)
        self.assertIn("body_y", d)
        self.assertIn("arm_swing", d)

    def test_walk_arm_swing_changes_with_phase(self):
        a = _state_offsets("walk", 0.0)["arm_swing"]
        b = _state_offsets("walk", 0.5)["arm_swing"]
        self.assertNotEqual(a, b)

    def test_attack_weapon_arc_progresses(self):
        windup = _state_offsets("attack", 0.1)["weapon_arc"]
        strike = _state_offsets("attack", 0.55)["weapon_arc"]
        self.assertLess(windup, strike,
                         "Strike phase should swing weapon further "
                         "than the windup")

    def test_hurt_red_flash_decays(self):
        early = _state_offsets("hurt", 0.0)["red_flash"]
        late = _state_offsets("hurt", 0.99)["red_flash"]
        self.assertGreater(early, late)

    def test_unknown_state_falls_back_to_idle(self):
        d = _state_offsets("not_a_state", 0.5)
        # Falls through to idle keys
        for k in ("body_y", "arm_swing", "leg_swing", "weapon_arc",
                  "shake_x", "red_flash"):
            self.assertIn(k, d)


class TestKindForEntity(unittest.TestCase):
    def test_class_mapping(self):
        for cls, expected in _CLASS_TO_KIND.items():
            ent = _StubEntity(is_player=True, character_class=cls)
            self.assertEqual(kind_for_entity(ent), expected)

    def test_unknown_class_defaults_warrior(self):
        ent = _StubEntity(is_player=True, character_class="trickster")
        self.assertEqual(kind_for_entity(ent), "warrior")

    def test_monster_default(self):
        ent = _StubEntity(is_player=False)
        self.assertEqual(kind_for_entity(ent), "monster")

    def test_wild_shape_is_beast(self):
        ent = _StubEntity(is_player=True, is_wild_shaped=True,
                           character_class="druid")
        self.assertEqual(kind_for_entity(ent), "beast")

    def test_summon_is_beast(self):
        ent = _StubEntity(is_player=True, is_summon=True)
        self.assertEqual(kind_for_entity(ent), "beast")


class TestDrawWithoutPygame(unittest.TestCase):
    def test_returns_false_when_no_pygame(self):
        if PYGAME_AVAILABLE:
            self.skipTest("pygame is available; can't test no-op path")
        self.assertFalse(draw_character(None, 60, 60))


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestRendering(unittest.TestCase):
    def setUp(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        self.surf = pygame.Surface((60, 60), pygame.SRCALPHA)

    def _is_blank(self):
        for x in range(self.surf.get_width()):
            for y in range(self.surf.get_height()):
                if self.surf.get_at((x, y)) != (0, 0, 0, 0):
                    return False
        return True

    def test_warrior_idle_renders(self):
        ok = draw_character(self.surf, 60, 60, kind="warrior",
                             color=(200, 80, 80), state="idle")
        self.assertTrue(ok)
        self.assertFalse(self._is_blank())

    def test_all_kinds_render(self):
        for kind in ("warrior", "ranger", "mage", "rogue",
                      "cleric", "druid", "monster", "beast"):
            self.surf.fill((0, 0, 0, 0))
            ok = draw_character(self.surf, 60, 60, kind=kind,
                                 color=(80, 200, 120))
            self.assertTrue(ok)
            self.assertFalse(self._is_blank(),
                             f"{kind} produced empty render")

    def test_all_states_render(self):
        for state in ("idle", "walk", "attack", "hurt"):
            self.surf.fill((0, 0, 0, 0))
            ok = draw_character(self.surf, 60, 60,
                                 kind="warrior", color=(180, 80, 80),
                                 state=state, phase=0.5)
            self.assertTrue(ok)
            self.assertFalse(self._is_blank(),
                             f"{state} produced empty render")

    def test_walk_animates(self):
        s1 = pygame.Surface((60, 60), pygame.SRCALPHA)
        s2 = pygame.Surface((60, 60), pygame.SRCALPHA)
        draw_character(s1, 60, 60, kind="warrior",
                        color=(200, 80, 80), state="walk", phase=0.0)
        draw_character(s2, 60, 60, kind="warrior",
                        color=(200, 80, 80), state="walk", phase=0.5)
        # Some pixel along the leg row should differ between phases
        diffs = 0
        for y in range(40, 55):
            for x in range(20, 40):
                if s1.get_at((x, y)) != s2.get_at((x, y)):
                    diffs += 1
        self.assertGreater(diffs, 0, "Walk frames should differ")

    def test_handles_tiny_token(self):
        small = pygame.Surface((24, 24), pygame.SRCALPHA)
        ok = draw_character(small, 24, 24, kind="ranger",
                             color=(40, 200, 80), state="walk",
                             phase=0.3)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
