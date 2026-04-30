"""Phase 12c — searchable dropdown widget logic tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from states.searchable_dropdown import SearchableDropdown, DropdownEntry


def _fixed_query(rows):
    """Returns a query_fn that filters ``rows`` (list of
    DropdownEntry) by case-insensitive substring on label."""
    def fn(q: str):
        if not q:
            return list(rows)
        ql = q.lower()
        return [r for r in rows if ql in r.label.lower()]
    return fn


def _entries(*pairs):
    return [DropdownEntry(id=i, label=l) for i, l in pairs]


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.picked = []
        self.rows = _entries(("a", "Alara"), ("b", "Bran"),
                              ("c", "Mira"))
        self.dd = SearchableDropdown(
            query_fn=_fixed_query(self.rows),
            on_select=lambda x: self.picked.append(x),
        )

    def test_starts_closed(self):
        self.assertFalse(self.dd.is_open)

    def test_open_populates_results(self):
        self.dd.open(anchor_rect=(0, 0, 200, 30))
        self.assertTrue(self.dd.is_open)
        self.assertEqual(len(self.dd._results), 3)

    def test_open_with_initial_query_filters(self):
        self.dd.open(anchor_rect=(0, 0, 200, 30),
                       initial_query="al")
        self.assertEqual(len(self.dd._results), 1)
        self.assertEqual(self.dd._results[0].id, "a")

    def test_open_with_selected_id_highlights(self):
        self.dd.open(anchor_rect=(0, 0, 200, 30),
                       selected_id="b")
        self.assertEqual(self.dd.highlight_idx, 1)


class TestQueryAndResults(unittest.TestCase):
    def setUp(self):
        self.picked = []
        self.rows = _entries(("a", "Alara"), ("b", "Bran"),
                              ("m", "Mira"), ("z", "Zen"))
        self.dd = SearchableDropdown(
            query_fn=_fixed_query(self.rows),
            on_select=lambda x: self.picked.append(x),
        )
        self.dd.open(anchor_rect=(0, 0, 200, 30))

    def test_set_query_filters_results(self):
        self.dd.set_query("ar")
        labels = [r.label for r in self.dd._results]
        self.assertEqual(labels, ["Alara"])

    def test_append_to_query_then_backspace(self):
        self.dd.append_to_query("m")
        self.assertEqual(len(self.dd._results), 1)
        self.dd.append_to_query("\b")
        self.assertEqual(len(self.dd._results), 4)

    def test_set_query_resets_highlight(self):
        self.dd.set_query("z")
        self.assertEqual(self.dd.highlight_idx, 0)


class TestKeyboard(unittest.TestCase):
    def setUp(self):
        self.picked = []
        rows = _entries(("a", "Alara"), ("b", "Bran"), ("c", "Mira"))
        self.dd = SearchableDropdown(
            query_fn=_fixed_query(rows),
            on_select=lambda x: self.picked.append(x),
        )
        self.dd.open(anchor_rect=(0, 0, 200, 30))
        self.dd.highlight_idx = 0

    def test_move_highlight(self):
        self.dd.move_highlight(+1)
        self.assertEqual(self.dd.highlight_idx, 1)
        self.dd.move_highlight(+5)
        self.assertEqual(self.dd.highlight_idx, 2)
        self.dd.move_highlight(-10)
        self.assertEqual(self.dd.highlight_idx, 0)

    def test_commit_highlighted(self):
        self.dd.move_highlight(+1)
        self.assertTrue(self.dd.commit_highlighted())
        self.assertFalse(self.dd.is_open)
        self.assertEqual(self.picked, ["b"])

    def test_close_without_commit(self):
        self.dd.close()
        self.assertEqual(self.picked, [None])

    def test_commit_index_out_of_range(self):
        self.assertFalse(self.dd.commit_index(99))


class TestScroll(unittest.TestCase):
    def setUp(self):
        rows = _entries(*[(f"i{i}", f"Item {i}") for i in range(20)])
        self.dd = SearchableDropdown(
            query_fn=_fixed_query(rows),
            on_select=lambda x: None,
            max_visible_rows=5,
        )
        self.dd.open(anchor_rect=(0, 0, 200, 30))

    def test_highlight_below_visible_scrolls(self):
        for _ in range(8):
            self.dd.move_highlight(+1)
        # highlight is at 8, visible window starts at 4 (8-5+1)
        self.assertGreater(self.dd.scroll, 0)
        self.assertGreaterEqual(self.dd.highlight_idx,
                                self.dd.scroll)

    def test_highlight_above_visible_scrolls_up(self):
        # First fast-forward
        for _ in range(10):
            self.dd.move_highlight(+1)
        # Then scroll back up
        for _ in range(8):
            self.dd.move_highlight(-1)
        self.assertGreaterEqual(self.dd.highlight_idx,
                                self.dd.scroll)


class TestEmptyResults(unittest.TestCase):
    def test_no_results_no_crash(self):
        dd = SearchableDropdown(
            query_fn=lambda q: [],
            on_select=lambda x: None,
        )
        dd.open(anchor_rect=(0, 0, 200, 30))
        dd.move_highlight(+1)
        self.assertEqual(dd.highlight_idx, -1)
        self.assertFalse(dd.commit_highlighted())


class TestQueryFnCrash(unittest.TestCase):
    def test_query_fn_exception_is_swallowed(self):
        def boom(q):
            raise RuntimeError("nope")
        dd = SearchableDropdown(
            query_fn=boom,
            on_select=lambda x: None,
        )
        dd.open(anchor_rect=(0, 0, 200, 30))
        self.assertEqual(dd._results, [])


if __name__ == "__main__":
    unittest.main()
