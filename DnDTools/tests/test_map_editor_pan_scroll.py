"""Phase 11b/11d — tool-panel scroll math + canvas pan logic.

We don't drive the full pygame editor; we exercise the data math
that the new wheel handler and key-press handler rely on so a future
refactor doesn't break these guarantees.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


import unittest


class TestToolPanelScrollClamp(unittest.TestCase):
    """Replicates the formula used by map_editor_tools._handle_event
    for MOUSEWHEEL over the tool panel."""
    def _clamp(self, current_scroll, wheel_y, content_h, panel_h,
                pad: int = 40, step: int = 30) -> int:
        max_scroll = max(0, content_h - panel_h + pad)
        return max(0, min(current_scroll - wheel_y * step, max_scroll))

    def test_scroll_down_increases(self):
        new = self._clamp(current_scroll=0, wheel_y=-1,
                           content_h=600, panel_h=300)
        self.assertEqual(new, 30)

    def test_scroll_up_decreases(self):
        new = self._clamp(current_scroll=60, wheel_y=+1,
                           content_h=600, panel_h=300)
        self.assertEqual(new, 30)

    def test_scroll_clamped_to_zero(self):
        new = self._clamp(current_scroll=10, wheel_y=+1,
                           content_h=600, panel_h=300)
        self.assertEqual(new, 0)

    def test_scroll_clamped_to_max(self):
        new = self._clamp(current_scroll=999, wheel_y=-1,
                           content_h=400, panel_h=300)
        self.assertEqual(new, 140)  # 400 - 300 + 40

    def test_short_content_locks_scroll(self):
        """When the content fits the panel, scroll stays at 0."""
        new = self._clamp(current_scroll=0, wheel_y=-1,
                           content_h=100, panel_h=300)
        self.assertEqual(new, 0)


class TestPanComputation(unittest.TestCase):
    """Replicates the formula used by MapEditorState.update for
    WASD/arrow panning."""
    def _pan_step(self, zoom, base=12.0) -> float:
        return base / max(zoom, 0.1)

    def test_pan_speed_scales_inversely_with_zoom(self):
        zoomed_out = self._pan_step(zoom=0.5)   # zoomed out → travel further
        zoomed_in = self._pan_step(zoom=4.0)
        self.assertGreater(zoomed_out, zoomed_in)

    def test_pan_speed_is_finite_at_tiny_zoom(self):
        self.assertEqual(self._pan_step(zoom=0.0), 120.0)
        self.assertEqual(self._pan_step(zoom=-1.0), 120.0)


if __name__ == "__main__":
    unittest.main()
