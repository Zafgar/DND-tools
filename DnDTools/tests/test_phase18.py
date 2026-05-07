"""Phase 18 — relationship sync + loot + dashboard tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from data.world import World, NPC, NPCRelationship, Quest, Location
from data.campaign import (
    Campaign, PartyMember, HeroRelationship, CampaignEncounter,
)
from data.relationship_sync import (
    set_hero_relationship, sync_attitude_both_ways,
    rebuild_dual_relationships, hero_attitude_to_npc,
    list_npc_attitudes_for_hero,
)
from data.loot import (
    LootBundle, AwardReport,
    award_loot, award_bundle, hand_item_to_pc,
    loot_from_defeated_entities,
)
from data.campaign_dashboard import build_overview, CampaignOverview


def _campaign_with_party(*pcs):
    c = Campaign()
    c.party = list(pcs)
    return c


def _pc(name, level=3, hp=24, char_class="Ranger"):
    return PartyMember(hero_data={
        "name": name,
        "character_class": char_class,
        "character_level": level,
        "hit_points": hp,
    })


# --------------------------------------------------------------------- #
# 18a — Dual relationship sync
# --------------------------------------------------------------------- #
class TestSyncBothWays(unittest.TestCase):
    def test_creates_both_sides(self):
        w = World()
        w.npcs["mira"] = NPC(id="mira", name="Mira")
        c = _campaign_with_party(_pc("Alara"))
        info = sync_attitude_both_ways(c, w,
                                          npc_id="mira",
                                          hero_name="Alara",
                                          attitude="friendly")
        self.assertTrue(info["npc_updated"])
        self.assertTrue(info["hero_updated"])
        # NPC side
        self.assertEqual(w.npcs["mira"].relationships[0].attitude,
                          "friendly")
        # Hero side
        self.assertEqual(c.party[0].relationships[0].target_id, "mira")
        self.assertEqual(c.party[0].relationships[0].attitude, "friendly")

    def test_unknown_npc_flag(self):
        c = _campaign_with_party(_pc("Alara"))
        w = World()
        info = sync_attitude_both_ways(c, w, npc_id="ghost",
                                          hero_name="Alara",
                                          attitude="hostile")
        self.assertTrue(info["missing_npc"])

    def test_unknown_hero_partial_update(self):
        w = World()
        w.npcs["mira"] = NPC(id="mira", name="Mira")
        c = _campaign_with_party()
        info = sync_attitude_both_ways(c, w, npc_id="mira",
                                          hero_name="Ghost",
                                          attitude="hostile")
        self.assertTrue(info["npc_updated"])
        self.assertFalse(info["hero_updated"])
        self.assertTrue(info["missing_party_member"])

    def test_repeat_sync_updates_in_place(self):
        w = World()
        w.npcs["mira"] = NPC(id="mira", name="Mira")
        c = _campaign_with_party(_pc("Alara"))
        sync_attitude_both_ways(c, w, npc_id="mira",
                                  hero_name="Alara",
                                  attitude="friendly")
        sync_attitude_both_ways(c, w, npc_id="mira",
                                  hero_name="Alara",
                                  attitude="hostile")
        self.assertEqual(len(w.npcs["mira"].relationships), 1)
        self.assertEqual(len(c.party[0].relationships), 1)
        self.assertEqual(w.npcs["mira"].relationships[0].attitude,
                          "hostile")


class TestRebuildDualRelationships(unittest.TestCase):
    def test_npc_to_hero_mirror(self):
        w = World()
        npc = NPC(id="m", name="Mira")
        npc.relationships = [NPCRelationship(hero_name="Alara",
                                                attitude="allied")]
        w.npcs["m"] = npc
        c = _campaign_with_party(_pc("Alara"))
        rep = rebuild_dual_relationships(c, w)
        self.assertEqual(rep["npc_to_hero_synced"], 1)
        self.assertEqual(c.party[0].relationships[0].attitude,
                          "allied")

    def test_hero_to_npc_mirror(self):
        w = World()
        w.npcs["m"] = NPC(id="m", name="Mira")
        c = _campaign_with_party(_pc("Alara"))
        c.party[0].relationships = [HeroRelationship(
            target_name="Mira", target_id="m",
            target_type="npc", attitude="hostile",
        )]
        rep = rebuild_dual_relationships(c, w)
        self.assertEqual(rep["hero_to_npc_synced"], 1)
        self.assertEqual(w.npcs["m"].relationships[0].attitude,
                          "hostile")


class TestHeroReadHelpers(unittest.TestCase):
    def test_hero_attitude_neutral_default(self):
        c = _campaign_with_party(_pc("Alara"))
        member = c.party[0]
        self.assertEqual(hero_attitude_to_npc(member, npc_id="x"),
                          "neutral")

    def test_list_npc_attitudes_for_hero(self):
        w = World()
        for nid in ("m", "b"):
            n = NPC(id=nid, name=nid.title())
            n.relationships = [NPCRelationship(hero_name="Alara",
                                                 attitude="friendly")]
            w.npcs[nid] = n
        rows = list_npc_attitudes_for_hero(w, "Alara")
        self.assertEqual(len(rows), 2)


# --------------------------------------------------------------------- #
# 18b — Loot helpers
# --------------------------------------------------------------------- #
class TestLootAward(unittest.TestCase):
    def test_shared_default(self):
        c = Campaign(party_gold=10.0)
        rep = award_loot(c, gold=50.0, items=["potion", "rope"])
        self.assertEqual(c.party_gold, 60.0)
        self.assertEqual(c.party_inventory, ["potion", "rope"])
        self.assertEqual(rep.gold_credited, 50.0)
        self.assertEqual(rep.items_added, 2)

    def test_split_evenly(self):
        c = _campaign_with_party(_pc("A"), _pc("B"))
        rep = award_loot(c, gold=100.0, distribution="split")
        self.assertEqual(c.party[0].gold, 50.0)
        self.assertEqual(c.party[1].gold, 50.0)
        self.assertEqual(rep.distribution, "split")

    def test_split_falls_back_when_no_active(self):
        c = Campaign()
        rep = award_loot(c, gold=20.0, distribution="split")
        self.assertEqual(c.party_gold, 20.0)

    def test_first_pc(self):
        c = _campaign_with_party(_pc("A"), _pc("B"))
        award_loot(c, gold=15.0, distribution="first")
        self.assertEqual(c.party[0].gold, 15.0)
        self.assertEqual(c.party[1].gold, 0.0)

    def test_zero_gold_no_op(self):
        c = Campaign()
        rep = award_loot(c, gold=0)
        self.assertEqual(rep.gold_credited, 0)

    def test_award_bundle(self):
        c = Campaign()
        bundle = LootBundle(gold=12.5, items=["scroll"])
        award_bundle(c, bundle)
        self.assertEqual(c.party_gold, 12.5)
        self.assertEqual(c.party_inventory, ["scroll"])


class TestHandItemToPc(unittest.TestCase):
    def test_transfer(self):
        c = _campaign_with_party(_pc("Alara"))
        c.party_inventory = ["potion"]
        ok = hand_item_to_pc(c, "Alara", "potion")
        self.assertTrue(ok)
        self.assertEqual(c.party_inventory, [])
        self.assertEqual(c.party[0].custom_items, ["potion"])

    def test_unknown_item(self):
        c = _campaign_with_party(_pc("Alara"))
        self.assertFalse(hand_item_to_pc(c, "Alara", "ghost"))

    def test_unknown_pc(self):
        c = _campaign_with_party(_pc("Alara"))
        c.party_inventory = ["x"]
        self.assertFalse(hand_item_to_pc(c, "Bran", "x"))


class TestLootFromEntities(unittest.TestCase):
    def test_collects_dead_enemy_items(self):
        class _Stats:
            items = ["sword", "10gp pouch"]
            loot_gold = 8.0
        class _E:
            def __init__(self, name, hp, is_player=False,
                          is_summon=False, is_lair=False):
                self.name = name; self.hp = hp
                self.is_player = is_player
                self.is_summon = is_summon
                self.is_lair = is_lair
                self.stats = _Stats()
        ents = [
            _E("Bandit", 0),
            _E("Goblin", 0),
            _E("Hero", 0, is_player=True),  # excluded
            _E("LairAction", 0, is_lair=True),  # excluded
            _E("Alive", 5),  # still alive
        ]
        bundle = loot_from_defeated_entities(ents)
        self.assertEqual(bundle.gold, 16.0)  # 2 dead enemies × 8gp
        self.assertEqual(len(bundle.items), 4)
        self.assertEqual(set(bundle.source_names), {"Bandit", "Goblin"})

    def test_empty(self):
        b = loot_from_defeated_entities([])
        self.assertTrue(b.is_empty())


# --------------------------------------------------------------------- #
# 18d — Campaign dashboard
# --------------------------------------------------------------------- #
class TestCampaignOverview(unittest.TestCase):
    def test_basic_party_stats(self):
        c = Campaign(party_gold=125.0,
                       party_inventory=["a", "b"])
        c.party = [
            _pc("Alara", level=3, hp=24),
            _pc("Bran",  level=3, hp=30),
        ]
        c.party[0].current_hp = 12
        c.party[1].current_hp = -1     # uses max
        c.party[0].gold = 50
        o = build_overview(c)
        self.assertEqual(o.party_size, 2)
        self.assertEqual(o.party_active, 2)
        self.assertEqual(o.party_total_max_hp, 54)
        self.assertEqual(o.party_total_hp, 12 + 30)
        self.assertEqual(o.party_gold_shared, 125.0)
        self.assertEqual(o.party_gold_per_pc, 50.0)
        self.assertEqual(o.party_inventory_size, 2)

    def test_with_world_counts(self):
        c = Campaign()
        w = World()
        w.locations["a"] = Location(id="a", name="A",
                                       location_type="town")
        w.locations["b"] = Location(id="b", name="B",
                                       location_type="wilderness")
        w.npcs["n1"] = NPC(id="n1", name="X")
        w.quests["q1"] = Quest(id="q1", name="Goblin", status="active")
        w.quests["q2"] = Quest(id="q2", name="Done", status="completed")
        o = build_overview(c, w)
        self.assertEqual(o.npc_total, 1)
        self.assertEqual(o.location_total, 2)
        self.assertEqual(o.location_settlements, 1)
        self.assertEqual(o.quest_active, 1)
        self.assertEqual(o.quest_completed, 1)

    def test_headlines_critical_hp(self):
        c = Campaign()
        c.party = [_pc("X", hp=20)]
        c.party[0].current_hp = 4   # 20% of max → critical
        o = build_overview(c)
        joined = " ".join(o.headlines)
        self.assertIn("critical", joined.lower())

    def test_current_area_summary(self):
        c = Campaign(current_area="Arenhold")
        w = World()
        w.locations["a"] = Location(id="a", name="Arenhold",
                                       location_type="town")
        w.npcs["n1"] = NPC(id="n1", name="Jolan", location_id="a")
        o = build_overview(c, w)
        self.assertIsNotNone(o.current_area_summary)
        self.assertEqual(o.current_area_summary.location.name,
                          "Arenhold")
        self.assertEqual(len(o.current_area_summary.npcs), 1)

    def test_encounters_count(self):
        c = Campaign()
        c.encounters = [
            CampaignEncounter(name="A", completed=True),
            CampaignEncounter(name="B", completed=False),
        ]
        o = build_overview(c)
        self.assertEqual(o.encounters_total, 2)
        self.assertEqual(o.encounters_completed, 1)


if __name__ == "__main__":
    unittest.main()
