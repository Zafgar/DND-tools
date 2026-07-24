"""main.py must import and expose a working server hook even when Flask
is not installed — the DM tool should launch on a bare pygame machine.

Regression for the Windows startup crash:
    ModuleNotFoundError: No module named 'flask'
"""
import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest


_MAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "main.py")


def _load_main(flask_present):
    """Import main.py with Flask either available or blocked."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if not flask_present and (name == "flask" or name.startswith("flask.")):
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = fake_import
    try:
        spec = importlib.util.spec_from_file_location("mainmod_test", _MAIN_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        builtins.__import__ = real_import


class TestOptionalFlask(unittest.TestCase):
    def test_imports_without_flask(self):
        mod = _load_main(flask_present=False)
        self.assertFalse(mod.FLASK_AVAILABLE)
        # run_server must exist and be a safe no-op (callable, no raise)
        self.assertTrue(callable(mod.run_server))
        mod.run_server()  # must not raise

    def test_update_queue_present_without_flask(self):
        mod = _load_main(flask_present=False)
        # The queue the game loop drains must exist regardless of Flask.
        self.assertTrue(hasattr(mod, "_update_queue"))
        mod._update_queue.put({"x": 1})
        self.assertEqual(mod._update_queue.get_nowait(), {"x": 1})

    def test_game_manager_class_available_without_flask(self):
        mod = _load_main(flask_present=False)
        self.assertTrue(hasattr(mod, "GameManager"))

    @unittest.skipUnless(
        importlib.util.find_spec("flask") is not None,
        "flask not installed in this environment")
    def test_flask_path_sets_flag(self):
        mod = _load_main(flask_present=True)
        self.assertTrue(mod.FLASK_AVAILABLE)
        self.assertTrue(hasattr(mod, "app"))


if __name__ == "__main__":
    unittest.main()
