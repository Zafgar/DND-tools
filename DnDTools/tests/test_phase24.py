"""Phase 24 — living-world editor modals:

  24a: DemographicsEditorModal persistence + biome suggest.
  24b: RelationsMatrixModal cycles attitudes symmetrically.
  24c: quick_create_npc honours wealth_tier.
  24d: NPC sheet shows organisations the NPC belongs to (data layer).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data import kingdoms as kg
from data import organizations as orgs
from data import demographics as demo
from data.wealth import npc_coins
from data.npc_quick_create import quick_create_npc
from data.world import World

try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:  # pragma: no cover
    HAS_PYGAME = False


class _FakeCampaign:
    def __init__(self):
        self.kingdoms_data = None
        self.organisations_data = None


# --------------------------------------------------------------------- #
# 24d — quick_create_npc with wealth_tier
# --------------------------------------------------------------------- #
class TestQuickCreateWealth(unittest.TestCase):
    def test_no_tier_no_coins(self):
        w = World()
        rep = quick_create_npc(w, name="Pauper")
        npc = w.npcs[rep.npc_id]
        # No wealth dict was set
        self.assertFalse(getattr(npc, "wealth", None))

    def test_wealth_tier_modest(self):
        w = World()
        rep = quick_create_npc(w, name="Crafter", wealth_tier="modest")
        npc = w.npcs[rep.npc_id]
        self.assertTrue(getattr(npc, "wealth", None))
        self.assertAlmostEqual(npc_coins(npc).total_gp(), 25.0)

    def test_wealth_tier_aristocratic(self):
        w = World()
        rep = quick_create_npc(w, name="Duke",
                                 wealth_tier="aristocratic")
        npc = w.npcs[rep.npc_id]
        self.assertAlmostEqual(npc_coins(npc).total_gp(), 2500.0)


# --------------------------------------------------------------------- #
# 24c — organisations_for_npc returns the linkage the NPC sheet uses
# --------------------------------------------------------------------- #
class TestNpcOrganisationLinkage(unittest.TestCase):
    def test_member_found_by_npc_id(self):
        camp = _FakeCampaign()
        b = orgs.ensure_organisations_on_campaign(camp)[0]
        b.members[0].npc_id = "npc_x"
        hits = orgs.organisations_for_npc(camp, "npc_x")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].key, "brotherhood_of_glorious_sun")

    def test_member_found_by_name_when_no_id(self):
        camp = _FakeCampaign()
        b = orgs.ensure_organisations_on_campaign(camp)[0]
        b.members[1].npc_name = "Mavrek"
        hits = orgs.organisations_for_npc_name(camp, "Mavrek")
        self.assertGreaterEqual(len(hits), 1)


# --------------------------------------------------------------------- #
# 24a/b — modal data-layer behaviour (no pygame surface needed)
# --------------------------------------------------------------------- #
@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestDemographicsEditorModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def _build_city(self, **kw):
        city = kg.CityEntry(key="testcity", name="Testcity", **kw)
        return city

    def test_save_persists_population_biome_demographics(self):
        from states.demographics_editor_modal import DemographicsEditorModal
        city = self._build_city(biome="forest", population=0)
        m = DemographicsEditorModal(city)
        m.open()
        m.population_str = "1200"
        m._bump("Elf", 10)  # bump or create Elf entry
        m._save()
        self.assertEqual(city.population, 1200)
        self.assertEqual(city.biome, "forest")
        self.assertTrue(city.demographics)
        # Zero rows are dropped on save
        for v in city.demographics.values():
            self.assertGreater(v, 0)

    def test_biome_suggest_replaces_table(self):
        from states.demographics_editor_modal import DemographicsEditorModal
        city = self._build_city(biome="underdark")
        m = DemographicsEditorModal(city)
        m.open()
        m.by_race = {"Human": 100}
        m._apply_biome_suggestion()
        # Should now look like an Underdark mix, not 100% human
        self.assertNotEqual(m.by_race, {"Human": 100})
        # Major Underdark races present
        self.assertTrue(any(r in m.by_race
                              for r in ("Drow", "Duergar",
                                          "Svirfneblin")))

    def test_cycle_biome_advances(self):
        from states.demographics_editor_modal import DemographicsEditorModal
        city = self._build_city(biome="human_heartland")
        m = DemographicsEditorModal(city)
        m.open()
        before = m.biome
        m._cycle_biome()
        self.assertNotEqual(m.biome, before)


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestRelationsMatrixModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_cycle_kingdom_is_symmetric(self):
        from states.relations_matrix_modal import RelationsMatrixModal
        camp = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(camp)
        m = RelationsMatrixModal(camp, scope="kingdom")
        m.open()
        # Cycle tarmaas → smardu and check it took on both ends
        before = kg.get_kingdom_relation(camp, "tarmaas", "smardu")
        m._cycle("tarmaas", "smardu")
        after = kg.get_kingdom_relation(camp, "tarmaas", "smardu")
        self.assertNotEqual(after, before)
        # Symmetric
        self.assertEqual(
            kg.get_kingdom_relation(camp, "smardu", "tarmaas"),
            after)

    def test_self_relation_not_cycled(self):
        from states.relations_matrix_modal import RelationsMatrixModal
        camp = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(camp)
        m = RelationsMatrixModal(camp, scope="kingdom")
        m.open()
        m._cycle("tarmaas", "tarmaas")
        self.assertEqual(
            kg.get_kingdom_relation(camp, "tarmaas", "tarmaas"),
            "self")

    def test_city_scope_works(self):
        from states.relations_matrix_modal import RelationsMatrixModal
        camp = _FakeCampaign()
        kg.ensure_kingdoms_on_campaign(camp)
        # Add a second city so the matrix has something to do
        kg.add_city(camp, "tarmaas", "highmoor", "Highmoor")
        m = RelationsMatrixModal(camp, scope="city",
                                    parent_kingdom_key="tarmaas")
        m.open()
        m._cycle("frand", "highmoor")
        att = kg.get_city_relation(camp, "tarmaas",
                                      "frand", "highmoor")
        self.assertIn(att, kg.RELATION_LEVELS)
        # Symmetric
        self.assertEqual(
            kg.get_city_relation(camp, "tarmaas",
                                   "highmoor", "frand"),
            att)


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestQuickCreateModalWealthCycler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def test_cycle_passes_through_all_tiers_back_to_empty(self):
        from states.quick_create_npc_modal import QuickCreateNPCModal
        w = World()
        m = QuickCreateNPCModal(w)
        m.open()
        seen = [m.wealth_tier]
        for _ in range(len(m._WEALTH_TIERS)):
            m._cycle_wealth_tier()
            seen.append(m.wealth_tier)
        # Should have visited every tier and returned to start
        self.assertEqual(set(seen), set(m._WEALTH_TIERS))
        self.assertEqual(seen[0], seen[-1])


if __name__ == "__main__":
    unittest.main()
