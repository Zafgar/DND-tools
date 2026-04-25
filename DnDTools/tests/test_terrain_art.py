"""Phase 7f — procedural terrain art tests.

These tests need a working pygame; they are skipped automatically when
pygame isn't importable in the test environment (e.g. headless CI
without the wheel installed). They run normally on developer machines
where pygame is available.
"""
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


class TestPainterCoverage(unittest.TestCase):
    """Pure-dict tests — no pygame needed; the dispatch tables are
    populated regardless of whether pygame can render."""

    CRITICAL = (
        "wall", "tree", "rock", "house", "pillar",
        "table", "crate", "barrel", "door", "door_locked",
        "spikes", "ice", "mud", "rubble", "difficult",
        "platform_5", "platform_10", "platform_15", "platform_20", "roof",
        "water", "deep_water", "lava", "lava_chasm", "fire",
        "chasm", "chasm_10", "chasm_15", "chasm_20",
    )

    def test_critical_types_have_painters(self):
        from states.terrain_art import has_painter
        missing = [t for t in self.CRITICAL if not has_painter(t)]
        self.assertEqual(missing, [],
                         f"No painter for: {missing}")

    def test_unknown_type_no_painter(self):
        from states.terrain_art import has_painter
        self.assertFalse(has_painter("plasma"))

    def test_decorate_returns_false_without_pygame(self):
        """When pygame isn't installed, decorate_tile must safely
        no-op and report False so the renderer can use its fallback."""
        from states.terrain_art import decorate_tile
        if PYGAME_AVAILABLE:
            self.skipTest("pygame is available, can't exercise the no-op path")
        self.assertFalse(decorate_tile(None, "wall", 60, 60, (0, 0, 0)))


def _setup_display():
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


def _is_blank(surface):
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if surface.get_at((x, y)) != (0, 0, 0, 0):
                return False
    return True


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestDecorateTile(unittest.TestCase):
    def setUp(self):
        _setup_display()

    def _surf(self, w=60, h=60):
        return pygame.Surface((w, h), pygame.SRCALPHA)

    def test_unknown_type_returns_false(self):
        from states.terrain_art import decorate_tile
        s = self._surf()
        ok = decorate_tile(s, "definitely_not_a_terrain_type",
                            60, 60, (100, 100, 100))
        self.assertFalse(ok)

    def test_known_static_type_paints(self):
        from states.terrain_art import decorate_tile
        s = self._surf()
        ok = decorate_tile(s, "wall", 60, 60, (80, 65, 45))
        self.assertTrue(ok)
        self.assertFalse(_is_blank(s))

    def test_known_animated_type_paints(self):
        from states.terrain_art import decorate_tile
        s = self._surf()
        ok = decorate_tile(s, "water", 60, 60, (30, 80, 160), ticks=1234)
        self.assertTrue(ok)
        self.assertFalse(_is_blank(s))

    def test_chasm_paints_dark_gradient(self):
        from states.terrain_art import decorate_tile
        s = self._surf()
        ok = decorate_tile(s, "chasm_20", 60, 60, (10, 10, 22))
        self.assertTrue(ok)
        self.assertFalse(_is_blank(s))

    def test_two_calls_with_different_ticks_animate(self):
        from states.terrain_art import decorate_tile
        s1 = self._surf(); s2 = self._surf()
        decorate_tile(s1, "lava", 60, 60, (255, 100, 0), ticks=0)
        decorate_tile(s2, "lava", 60, 60, (255, 100, 0), ticks=5_000)
        diffs = sum(1 for y in range(60)
                    if s1.get_at((30, y)) != s2.get_at((30, y)))
        self.assertGreater(diffs, 0)

    def test_handles_tiny_tile(self):
        from states.terrain_art import decorate_tile
        s = self._surf(8, 8)
        for kind in ("wall", "tree", "rock", "water", "lava", "fire",
                      "chasm", "spikes", "barrel"):
            decorate_tile(s, kind, 8, 8, (100, 100, 100))


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame not available")
class TestNoCrashAcrossAllTypes(unittest.TestCase):
    def setUp(self):
        _setup_display()

    def test_all_painters_run(self):
        from states.terrain_art import (
            decorate_tile, _PAINTERS, _PAINTERS_TICKS, _PAINTERS_NO_BASE,
        )
        for kind in list(_PAINTERS.keys()):
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            decorate_tile(s, kind, 60, 60, (100, 100, 100))
        for kind in list(_PAINTERS_TICKS.keys()):
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            decorate_tile(s, kind, 60, 60, (100, 100, 100), ticks=1000)
        for kind in list(_PAINTERS_NO_BASE.keys()):
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            decorate_tile(s, kind, 60, 60, (100, 100, 100))


if __name__ == "__main__":
    unittest.main()
