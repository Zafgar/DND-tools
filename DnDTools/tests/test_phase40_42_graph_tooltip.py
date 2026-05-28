"""Phase 40/41/42 — add-link form, hover mini-card, relationship graph.

  40: NpcDetailModal link-form logic (target/kind cyclers + commit
      via npc_directory). Pygame-skipped for draw; logic exercised
      directly.
  41: mini_card_content shape + NpcHoverCard show/hide caching.
  42: build_graph node/edge correctness, layout determinism, no
      cross-filter leakage, nearest_node hit-testing.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.world import World, NPC, Location
from data import npc_directory as nd
from data import npc_graph as ng


def _world():
    w = World()
    w.locations["loc"] = Location(id="loc", name="Frand",
                                    location_type="city")
    names = [("n0", "Cal", "Brotherhood"),
             ("n1", "Vela", "Brotherhood"),
             ("n2", "Jolan", "Crown"),
             ("n3", "Garek", ""),
             ("n4", "Arys", "House Tarn")]
    for nid, name, fac in names:
        w.npcs[nid] = NPC(id=nid, name=name, faction=fac,
                            occupation="Test", race="Human",
                            location_id="loc")
    nd.add_npc_link(w, "n0", "n1", "patron", "funds")
    nd.add_npc_link(w, "n0", "n2", "rival", "docks")
    nd.add_npc_link(w, "n3", "n4", "mentor", "smithing")
    return w


# --------------------------------------------------------------------- #
# Phase 41 — mini card content
# --------------------------------------------------------------------- #
class TestMiniCardContent(unittest.TestCase):
    def setUp(self):
        self.w = _world()

    def test_content_has_core_fields(self):
        c = ng.mini_card_content(self.w, self.w.npcs["n0"])
        self.assertEqual(c["name"], "Cal")
        self.assertEqual(c["faction"], "Brotherhood")
        self.assertEqual(c["location"], "Frand")
        self.assertTrue(c["alive"])

    def test_content_lists_top_links(self):
        c = ng.mini_card_content(self.w, self.w.npcs["n0"])
        self.assertEqual(c["link_count"], 2)
        # patron: Vela and rival: Jolan
        joined = " ".join(c["links"])
        self.assertIn("Vela", joined)
        self.assertIn("Jolan", joined)

    def test_content_caps_links_at_three(self):
        # Add several more links to n0
        for tgt in ("n3", "n4"):
            nd.add_npc_link(self.w, "n0", tgt, "ally")
        c = ng.mini_card_content(self.w, self.w.npcs["n0"])
        self.assertEqual(len(c["links"]), 3)
        self.assertGreaterEqual(c["link_count"], 4)


# --------------------------------------------------------------------- #
# Phase 42 — graph build + layout
# --------------------------------------------------------------------- #
class TestBuildGraph(unittest.TestCase):
    def setUp(self):
        self.w = _world()

    def test_all_nodes_present_with_isolated(self):
        g = ng.build_graph(self.w)
        self.assertEqual(len(g.nodes), 5)

    def test_edges_dedup_undirected(self):
        g = ng.build_graph(self.w)
        # 3 links → 3 undirected edges (each link auto-flips but the
        # pair collapses to one edge)
        self.assertEqual(len(g.edges), 3)

    def test_degree_counts(self):
        g = ng.build_graph(self.w)
        cal = g.node("n0")
        self.assertEqual(cal.degree, 2)  # patron + rival
        garek = g.node("n3")
        self.assertEqual(garek.degree, 1)

    def test_faction_filter(self):
        g = ng.build_graph(self.w, faction="Brotherhood")
        ids = {n.id for n in g.nodes}
        self.assertEqual(ids, {"n0", "n1"})
        # Only the patron edge survives (n0→n1); n0→n2 dropped (n2 out)
        self.assertEqual(len(g.edges), 1)

    def test_exclude_isolated(self):
        # Garek/Arys are linked; everyone else too. Add a lone NPC.
        self.w.npcs["lone"] = NPC(id="lone", name="Hermit")
        g_with = ng.build_graph(self.w, include_isolated=True)
        g_without = ng.build_graph(self.w, include_isolated=False)
        self.assertIn("lone", {n.id for n in g_with.nodes})
        self.assertNotIn("lone", {n.id for n in g_without.nodes})

    def test_nodes_sorted_by_degree_desc(self):
        g = ng.build_graph(self.w)
        # First node should be the highest-degree (Cal, degree 2)
        self.assertEqual(g.nodes[0].id, "n0")


class TestLayout(unittest.TestCase):
    def setUp(self):
        self.w = _world()

    def test_force_directed_is_deterministic(self):
        g1 = ng.build_graph(self.w)
        g2 = ng.build_graph(self.w)
        ng.force_directed_layout(g1, width=800, height=600, seed=1)
        ng.force_directed_layout(g2, width=800, height=600, seed=1)
        for a, b in zip(g1.nodes, g2.nodes):
            self.assertAlmostEqual(a.x, b.x, places=3)
            self.assertAlmostEqual(a.y, b.y, places=3)

    def test_layout_keeps_nodes_in_bounds(self):
        g = ng.build_graph(self.w)
        ng.force_directed_layout(g, width=800, height=600, seed=1)
        for n in g.nodes:
            self.assertGreaterEqual(n.x, 0)
            self.assertLessEqual(n.x, 800)
            self.assertGreaterEqual(n.y, 0)
            self.assertLessEqual(n.y, 600)

    def test_circular_layout_spreads_nodes(self):
        g = ng.build_graph(self.w)
        ng.circular_layout(g, cx=400, cy=300, radius=200)
        # No two nodes should share the exact same coordinate
        coords = {(round(n.x, 1), round(n.y, 1)) for n in g.nodes}
        self.assertEqual(len(coords), len(g.nodes))

    def test_nearest_node_hit_test(self):
        g = ng.build_graph(self.w)
        ng.circular_layout(g, cx=400, cy=300, radius=200)
        target = g.nodes[0]
        # Click right on it
        hit = ng.nearest_node(g, target.x, target.y, max_dist=10)
        self.assertIs(hit, target)
        # Click far away → None
        miss = ng.nearest_node(g, -999, -999, max_dist=10)
        self.assertIsNone(miss)

    def test_single_node_layout_centres(self):
        w = World()
        w.npcs["solo"] = NPC(id="solo", name="Solo")
        g = ng.build_graph(w)
        ng.force_directed_layout(g, width=800, height=600)
        self.assertEqual(g.nodes[0].x, 400)
        self.assertEqual(g.nodes[0].y, 300)

    def test_empty_graph_layout_noop(self):
        w = World()
        g = ng.build_graph(w)
        # Should not raise
        ng.force_directed_layout(g, width=800, height=600)
        self.assertEqual(g.nodes, [])


# --------------------------------------------------------------------- #
# Phase 40 — add-link form logic + Phase 41 hover card (pygame)
# --------------------------------------------------------------------- #
try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestDetailModalLinkForm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_commit_link_creates_relationship(self):
        from states.npc_detail_modal import NpcDetailModal
        w = _world()
        # Start on a fresh NPC with no links
        w.npcs["fresh"] = NPC(id="fresh", name="Fresh", active=True)
        m = NpcDetailModal(w, campaign=None, npc=w.npcs["fresh"])
        m.open()
        m._toggle_link_form()
        self.assertTrue(m._link_form_open)
        # Target idx 0 = first candidate alphabetically
        cands = m._link_candidates()
        first = cands[0]
        m._link_kind_idx = nd.LINK_KINDS.index("ally")
        m._link_notes = "Met at the docks"
        m._commit_link()
        links = nd.npc_links_of(w, "fresh")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["target_id"], first.id)
        self.assertEqual(links[0]["kind"], "ally")
        self.assertEqual(links[0]["notes"], "Met at the docks")
        # Form closes after commit
        self.assertFalse(m._link_form_open)

    def test_cycle_kind_wraps(self):
        from states.npc_detail_modal import NpcDetailModal
        w = _world()
        m = NpcDetailModal(w, campaign=None, npc=w.npcs["n0"])
        m.open()
        m._link_kind_idx = len(nd.LINK_KINDS) - 1
        m._cycle_link_kind(1)
        self.assertEqual(m._link_kind_idx, 0)

    def test_remove_link_button(self):
        from states.npc_detail_modal import NpcDetailModal
        w = _world()
        m = NpcDetailModal(w, campaign=None, npc=w.npcs["n0"])
        m.open()
        # n0 links to n1 (patron) and n2 (rival)
        self.assertEqual(len(nd.npc_links_of(w, "n0")), 2)
        m._remove_link("n1")
        self.assertEqual(len(nd.npc_links_of(w, "n0")), 1)


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestHoverCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_show_caches_by_npc_id(self):
        from states.npc_hover_card import NpcHoverCard
        w = _world()
        card = NpcHoverCard()
        card.show(w, w.npcs["n0"])
        first_content = card._content
        # Showing the same NPC again should not rebuild content
        card.show(w, w.npcs["n0"])
        self.assertIs(card._content, first_content)
        # Different NPC rebuilds
        card.show(w, w.npcs["n1"])
        self.assertIsNot(card._content, first_content)

    def test_hide_sets_invisible(self):
        from states.npc_hover_card import NpcHoverCard
        w = _world()
        card = NpcHoverCard()
        card.show(w, w.npcs["n0"])
        self.assertTrue(card.is_visible)
        card.hide()
        self.assertFalse(card.is_visible)

    def test_draw_when_hidden_is_noop(self):
        from states.npc_hover_card import NpcHoverCard
        import pygame
        card = NpcHoverCard()
        # Not visible — draw should simply return
        card.draw(pygame.display.get_surface(), (100, 100))


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestRelationshipGraphView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1600, 900))

    def test_open_builds_and_draws(self):
        from states.npc_relationship_graph import NpcRelationshipGraph
        import pygame
        w = _world()
        v = NpcRelationshipGraph(w, campaign=None)
        v.open()
        self.assertIsNotNone(v.graph)
        self.assertEqual(len(v.graph.nodes), 5)
        v.draw(pygame.display.get_surface())

    def test_filter_rebuilds_graph(self):
        from states.npc_relationship_graph import NpcRelationshipGraph
        w = _world()
        v = NpcRelationshipGraph(w, campaign=None)
        v.open()
        v.filter_faction = "Brotherhood"
        v._rebuild()
        self.assertEqual(len(v.graph.nodes), 2)


if __name__ == "__main__":
    unittest.main()
