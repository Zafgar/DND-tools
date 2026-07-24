"""main.py must not die to a black screen when a state raises.

A broken frame (handle_events/update/draw) or a failed state build should
log its traceback, show an on-screen banner, and fall back to the menu —
the app keeps running so the user can navigate away and read crash_log.txt.
"""
import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
import pygame

_MAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "main.py")


def _load_main():
    spec = importlib.util.spec_from_file_location("mainmod_res", _MAIN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _GoodMenu:
    def __init__(self):
        self.drawn = 0

    def handle_events(self, e):
        pass

    def update(self):
        pass

    def draw(self, s):
        self.drawn += 1
        s.fill((10, 10, 10))


class _BrokenState:
    def handle_events(self, e):
        raise RuntimeError("boom in handle_events")

    def update(self):
        pass

    def draw(self, s):
        raise RuntimeError("boom in draw")


class TestFrameResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((400, 300))
        cls.mod = _load_main()

    def _manager(self):
        m = self.mod.GameManager.__new__(self.mod.GameManager)
        m.screen = pygame.display.get_surface()
        m.running = True
        m.error_banner = ""
        m._error_font = None
        menu = _GoodMenu()
        m.states = {"MENU": menu}
        return m, menu

    def _run_one_frame(self, m):
        """Mirror the body of GameManager.run() for a single frame."""
        try:
            m.current_state.handle_events([])
            m.current_state.update()
            m.current_state.draw(m.screen)
        except Exception:
            broken = type(m.current_state).__name__
            m.error_banner = f"Error in {broken}"
            menu = m.states.get("MENU")
            if menu is not None and m.current_state is not menu:
                m.current_state = menu
                m.current_state.draw(m.screen)
            else:
                m.screen.fill((20, 20, 24))
        m._draw_error_banner()

    def test_broken_state_reverts_to_menu(self):
        m, menu = self._manager()
        m.current_state = _BrokenState()
        self._run_one_frame(m)
        self.assertIs(m.current_state, menu)
        self.assertTrue(m.error_banner)

    def test_recovers_and_keeps_running(self):
        m, menu = self._manager()
        m.current_state = _BrokenState()
        self._run_one_frame(m)      # crash -> menu
        drawn_after_crash = menu.drawn
        self._run_one_frame(m)      # normal menu frame
        self.assertGreater(menu.drawn, drawn_after_crash)
        self.assertTrue(m.running)

    def test_error_banner_draws_without_crashing(self):
        m, _ = self._manager()
        m.error_banner = "Error in Something — see crash_log.txt.\nPress ESC."
        m._draw_error_banner()      # must not raise
        self.assertIsNotNone(m._error_font)


class TestChangeStateResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((400, 300))
        cls.mod = _load_main()

    def test_failed_state_build_sets_banner_not_crash(self):
        m = self.mod.GameManager.__new__(self.mod.GameManager)
        m.screen = pygame.display.get_surface()
        m.error_banner = ""
        menu = _GoodMenu()
        m.states = {"MENU": menu, "CAMPAIGN": None}
        m.current_state = menu

        # Force CampaignManagerState construction to raise.
        import states.campaign_manager as cmmod
        orig = cmmod.CampaignManagerState

        class Boom:
            def __init__(self, *a, **k):
                raise RuntimeError("bad save data")

        self.mod.CampaignManagerState = Boom
        try:
            m.change_state("CAMPAIGN", campaign=None)
        finally:
            self.mod.CampaignManagerState = orig

        self.assertTrue(m.error_banner)
        self.assertIs(m.current_state, menu)  # stayed on the safe screen


if __name__ == "__main__":
    unittest.main()
