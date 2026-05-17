"""Phase 32 / 33 — boss legendary timing, LR advisor, monk features.

Audits:

  * Boss legendary actions are spread across PC turns: with 3 LA and
    3 PCs, the boss exhausts all of them before its own next turn.
  * Legendary Resistance "advisor" returns a recommendation + a
    human-readable reason — DM can override knowingly.
  * Encounter-killer spells (Polymorph, Banishment, Hold Monster,
    Power Word Stun, etc.) trigger LR regardless of remaining count.
  * Damage-only saves only burn LR when the hit is genuinely lethal.
  * Conserve-LR path: minor effects don't drain the pool.
  * Step of the Wind: spends ki + bonus action.
  * Deflect Missiles: reaction reduces ranged-weapon damage.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import (
    CreatureStats, AbilityScores, Action, Feature,
)
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI
from engine.rules import (
    can_use_legendary_resistance, lr_decision_with_reason,
    lr_advisor_summary, _should_use_legendary_resistance,
    make_saving_throw,
)


def _boss(*, hp=200, lr=3, la=3, name="Boss"):
    stats = CreatureStats(
        name=name, size="Huge", hit_points=hp, armor_class=18,
        speed=40, abilities=AbilityScores(strength=23, dexterity=12,
                                              constitution=23,
                                              intelligence=18,
                                              wisdom=15, charisma=20),
        actions=[Action(name="Bite", attack_bonus=10,
                          damage_dice="2d10", damage_bonus=6,
                          damage_type="piercing", range=10),
                  Action(name="Wing", attack_bonus=10,
                          damage_dice="2d8", damage_bonus=4,
                          damage_type="bludgeoning",
                          range=15, aoe_radius=15,
                          aoe_shape="sphere",
                          action_type="legendary")],
        legendary_action_count=la,
        legendary_resistance_count=lr,
        proficiency_bonus=4,
    )
    e = Entity(stats, 5, 5, is_player=False)
    # Wire a 1-cost legendary action so the AI has something to pick
    e.stats.features.append(Feature(
        name="Wing", feature_type="legendary",
        legendary_cost=1, damage_dice="2d8",
        damage_type="bludgeoning",
    ))
    return e


def _pc(name="PC", x=6, y=5, hp=30, ac=15):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=hp, armor_class=ac,
        speed=30, abilities=AbilityScores(strength=14, dexterity=14,
                                              constitution=12,
                                              intelligence=10,
                                              wisdom=12, charisma=10),
        actions=[Action(name="Sword", attack_bonus=5,
                          damage_dice="1d8", damage_bonus=3,
                          damage_type="slashing", range=5)],
        proficiency_bonus=3,
    )
    return Entity(stats, x, y, is_player=True)


# --------------------------------------------------------------------- #
# Boss-side LA timing
# --------------------------------------------------------------------- #
class TestLegendaryActionTiming(unittest.TestCase):
    def test_all_three_legendary_actions_get_used_between_pc_turns(self):
        boss = _boss(la=3)
        pc1, pc2, pc3 = _pc("A", 6, 5), _pc("B", 6, 6), _pc("C", 6, 7)
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[boss, pc1, pc2, pc3])
        b.combat_started = True
        ai = TacticalAI()
        # Simulate the queue draining between PC turns.
        for _ in range(3):
            step = ai.calculate_legendary_action(boss, b)
            self.assertIsNotNone(step,
                                  "boss should pick a legendary action "
                                  "whenever budget allows")
        # Boss exhausted its pool
        self.assertEqual(boss.legendary_actions_left, 0)
        # Fourth pull yields nothing
        self.assertIsNone(ai.calculate_legendary_action(boss, b))

    def test_legendary_reset_on_boss_own_turn(self):
        boss = _boss(la=3)
        boss.legendary_actions_left = 0
        boss.reset_legendary_actions()
        self.assertEqual(boss.legendary_actions_left, 3)


# --------------------------------------------------------------------- #
# LR advisor — reasoning + recommendation
# --------------------------------------------------------------------- #
class TestLRAdvisor(unittest.TestCase):
    def test_paralyzed_forces_use_regardless_of_count(self):
        boss = _boss(lr=1)
        use, reason = lr_decision_with_reason(boss, "Paralyzed", "")
        self.assertTrue(use)
        self.assertIn("Paralyzed", reason)

    def test_polymorph_spell_is_encounter_killer(self):
        boss = _boss(lr=1)
        use, reason = lr_decision_with_reason(
            boss, "", "", spell_name="Polymorph")
        self.assertTrue(use)
        self.assertIn("encounter-killer", reason.lower())

    def test_banishment_is_encounter_killer(self):
        boss = _boss(lr=1)
        use, _ = lr_decision_with_reason(
            boss, "Banished", "", spell_name="Banishment")
        self.assertTrue(use)

    def test_hold_monster_is_encounter_killer(self):
        boss = _boss(lr=1)
        use, _ = lr_decision_with_reason(
            boss, "", "", spell_name="Hold Monster")
        self.assertTrue(use)

    def test_minor_dmg_save_does_not_burn_lr_at_full_hp(self):
        boss = _boss(hp=200, lr=3)
        use, reason = lr_decision_with_reason(
            boss, "", "1d4")
        self.assertFalse(use)
        self.assertIn("minor", reason.lower())

    def test_lethal_damage_burns_lr(self):
        boss = _boss(hp=20, lr=3)
        use, reason = lr_decision_with_reason(
            boss, "", "10d10")
        self.assertTrue(use)
        self.assertIn("lethal", reason.lower())

    def test_moderate_condition_burns_when_lr_plenty(self):
        boss = _boss(lr=3)
        use, reason = lr_decision_with_reason(boss, "Restrained", "")
        self.assertTrue(use)

    def test_moderate_condition_conserves_when_only_one_lr_left(self):
        boss = _boss(lr=3)
        boss.legendary_resistances_left = 1
        # Generic moderate condition not in the "always burn last"
        # safety net (Frightened, Charmed, Prone, Deafened, Poisoned,
        # Grappled, Slowed).
        use, _ = lr_decision_with_reason(boss, "Frightened", "")
        self.assertFalse(use)

    def test_advisor_summary_format(self):
        boss = _boss(lr=3)
        s = lr_advisor_summary(boss, "Hold Monster", "", "")
        self.assertIn("LR Advisor", s)
        self.assertIn("USE", s)
        self.assertIn(boss.name, s)
        # Counter format "(3/3 left)"
        self.assertIn("3/3", s.replace(" ", ""))

    def test_advisor_summary_for_save_recommendation(self):
        boss = _boss(hp=200, lr=3)
        s = lr_advisor_summary(boss, "Magic Missile", "", "3d4")
        self.assertIn("SAVE", s)

    def test_save_path_uses_advisor_and_logs_reason(self):
        # Verify the end-to-end save path injects the reason into the
        # log message when LR fires.
        boss = _boss(lr=3)
        # Boss is bad at WIS saves (cha 20 wis 15) — force failure
        # by giving an absurd DC.
        success, total, msg = make_saving_throw(
            boss, "Wisdom", dc=30,
            applies_condition="Paralyzed",
            spell_name="Hold Monster",
        )
        self.assertTrue(success, "LR should auto-pass the save")
        # The reason gets embedded in the message
        self.assertIn("encounter-killer", msg.lower())


# --------------------------------------------------------------------- #
# Phase 33 — monk Step of Wind + Deflect Missiles
# --------------------------------------------------------------------- #
class TestMonkFeatures(unittest.TestCase):
    def _monk(self, *, level=5, ki=3, features=None):
        feats = list(features or [])
        stats = CreatureStats(
            name="Monk", size="Medium", hit_points=38,
            armor_class=15, speed=40,
            abilities=AbilityScores(strength=14, dexterity=18,
                                      constitution=14,
                                      intelligence=10,
                                      wisdom=16, charisma=10),
            actions=[Action(name="Unarmed", attack_bonus=7,
                              damage_dice="1d6", damage_bonus=4,
                              damage_type="bludgeoning", range=5)],
            features=feats,
            ki_points=ki,
            character_level=level,
            character_class="Monk",
            proficiency_bonus=3,
        )
        e = Entity(stats, 5, 5, is_player=True)
        e.ki_points_left = ki
        return e

    def test_step_of_wind_requires_feat_and_ki(self):
        from engine.feat_effects import step_of_wind_available
        bare = self._monk(ki=3)
        self.assertFalse(step_of_wind_available(bare))
        monk_no_ki = self._monk(ki=0, features=[
            Feature(name="Ki", mechanic="ki", feature_type="class"),
            Feature(name="Step of the Wind",
                      mechanic="step_of_wind",
                      feature_type="class"),
        ])
        self.assertFalse(step_of_wind_available(monk_no_ki))
        monk = self._monk(ki=3, features=[
            Feature(name="Ki", mechanic="ki", feature_type="class"),
            Feature(name="Step of the Wind",
                      mechanic="step_of_wind",
                      feature_type="class"),
        ])
        self.assertTrue(step_of_wind_available(monk))

    def test_step_of_wind_consumes_ki_and_bonus_action(self):
        from engine.feat_effects import use_step_of_wind
        monk = self._monk(ki=2, features=[
            Feature(name="Ki", mechanic="ki", feature_type="class"),
            Feature(name="Step of the Wind",
                      mechanic="step_of_wind",
                      feature_type="class"),
        ])
        self.assertTrue(use_step_of_wind(monk))
        self.assertEqual(monk.ki_points_left, 1)
        self.assertTrue(monk.bonus_action_used)
        # Second call this turn: bonus action gone
        self.assertFalse(use_step_of_wind(monk))

    def test_deflect_missiles_reduces_ranged_damage(self):
        monk = self._monk(level=5, features=[
            Feature(name="Deflect Missiles",
                      mechanic="deflect_missiles",
                      mechanic_value="5",
                      feature_type="class"),
        ])
        # Take 25 piercing from arrow. Reduction = 1d10 + 4 (DEX 18)
        # + 5 (monk lvl) = at least 10, at most 19. Capped at 25.
        import random as _r
        _r.seed(7)
        monk.hp = 38
        dealt, _ = monk.take_damage(25, "piercing",
                                        is_ranged_weapon=True)
        self.assertLess(dealt, 25,
                          "Deflect Missiles should reduce ranged damage")
        self.assertTrue(monk.reaction_used,
                         "reaction should be consumed by Deflect")

    def test_deflect_missiles_does_not_fire_on_melee(self):
        monk = self._monk(level=5, features=[
            Feature(name="Deflect Missiles",
                      mechanic="deflect_missiles",
                      mechanic_value="5", feature_type="class"),
        ])
        dealt, _ = monk.take_damage(10, "slashing",
                                        is_ranged_weapon=False)
        self.assertEqual(dealt, 10)
        self.assertFalse(monk.reaction_used)

    def test_deflect_missiles_only_once_per_round(self):
        monk = self._monk(level=5, features=[
            Feature(name="Deflect Missiles",
                      mechanic="deflect_missiles",
                      mechanic_value="5", feature_type="class"),
        ])
        monk.take_damage(10, "piercing", is_ranged_weapon=True)
        self.assertTrue(monk.reaction_used)
        # Second arrow same round: full damage
        before = monk.hp
        monk.take_damage(10, "piercing", is_ranged_weapon=True)
        self.assertEqual(before - monk.hp, 10)


# --------------------------------------------------------------------- #
# Phase 32 — feat picker modal data layer
# --------------------------------------------------------------------- #
try:
    import pygame  # noqa: F401
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestFeatPickerModal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def _npc(self, *, features=None, hit_points=10, level=5):
        from data.world import NPC
        n = NPC(id="n1", name="Test NPC")
        n.custom_stats = {
            "features": features or [],
            "hit_points": hit_points,
            "character_level": level,
            "abilities": {
                "strength": 14, "dexterity": 14,
                "constitution": 16, "intelligence": 10,
                "wisdom": 12, "charisma": 10,
            },
            "saving_throws": {},
        }
        return n

    def test_add_then_save_writes_to_custom_stats(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc()
        m = FeatPickerModal(npc)
        m.open()
        m._add_feat("Mobile")
        m._save()
        feature_names = [f["name"] for f in npc.custom_stats["features"]]
        self.assertIn("Mobile", feature_names)

    def test_remove_then_save_drops_feat(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc(features=[{
            "name": "Mobile", "description": "",
            "feature_type": "feat", "mechanic": "mobile",
            "mechanic_value": "", "uses_per_day": -1,
        }])
        m = FeatPickerModal(npc)
        m.open()
        m._remove_feat("Mobile")
        m._save()
        self.assertEqual(npc.custom_stats["features"], [])

    def test_cancel_reverts_working_set(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc()
        m = FeatPickerModal(npc)
        m.open()
        m._add_feat("Alert")
        m._cancel()
        # NPC custom_stats unchanged after cancel
        self.assertEqual(npc.custom_stats["features"], [])

    def test_tough_adds_hp_on_save(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc(hit_points=40, level=5)
        m = FeatPickerModal(npc)
        m.open()
        m._add_feat("Tough")
        m._save()
        # +2 HP per level, level 5 → +10
        self.assertEqual(npc.custom_stats["hit_points"], 50)

    def test_tough_removed_subtracts_hp(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc(hit_points=50, level=5, features=[{
            "name": "Tough", "mechanic": "tough", "mechanic_value": "",
            "description": "", "feature_type": "feat",
            "uses_per_day": -1,
        }])
        m = FeatPickerModal(npc)
        m.open()
        m._remove_feat("Tough")
        m._save()
        self.assertEqual(npc.custom_stats["hit_points"], 40)

    def test_resilient_adds_save_proficiency_on_save(self):
        from states.feat_picker_modal import FeatPickerModal
        npc = self._npc()
        m = FeatPickerModal(npc)
        m.open()
        m._add_feat("Resilient")
        # Default mechanic_value gets seeded to "CON"
        m._save()
        # PB at level 5 = 3, CON 16 → mod 3 → Constitution save 6
        saves = npc.custom_stats.get("saving_throws", {})
        self.assertIn("Constitution", saves)


if __name__ == "__main__":
    unittest.main()
