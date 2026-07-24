"""Phase 49 — Finnish in-combat ability/condition/action explanations."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import Action, Feature
from data.conditions import CONDITIONS
from data.ability_help_fi import (
    explain_action, explain_condition, explain_feature,
    summarize_ai_plan_fi, CONDITION_HELP_FI, MECHANIC_HELP_FI,
    target_rationale_fi, difficulty_read_fi,
)
from data.models import CreatureStats, AbilityScores
from engine.entities import Entity
from engine.battle import BattleSystem


class TestConditionHelp(unittest.TestCase):
    def test_every_condition_has_finnish_help(self):
        for cond in CONDITIONS:
            self.assertTrue(explain_condition(cond),
                            f"{cond} lacks a Finnish explanation")

    def test_lethargic_covered(self):
        self.assertIn("Haste", CONDITION_HELP_FI["Lethargic"])


class TestActionExplain(unittest.TestCase):
    def test_attack_action(self):
        a = Action("Aether Siphon", "", 11, "4d8", 4, "force", range=120)
        txt = explain_action(a)
        self.assertIn("1d20+11", txt)
        self.assertIn("4d8+4", txt)
        self.assertIn("voima", txt)          # force -> Finnish
        self.assertIn("Kantama 120", txt)

    def test_multiattack(self):
        a = Action("Multiattack", "", 0, "", 0, "", is_multiattack=True,
                   multiattack_count=3,
                   multiattack_targets=["Sword", "Sword", "Sword"])
        txt = explain_action(a)
        self.assertIn("Multiattack", txt)
        self.assertIn("3 hyök", txt)

    def test_condition_rider_includes_dc_and_save_fi(self):
        a = Action("Venom Blade", "", 10, "5d6", 0, "slashing",
                   applies_condition="Poisoned", condition_save="Constitution",
                   condition_dc=17)
        txt = explain_action(a)
        self.assertIn("Poisoned", txt)
        self.assertIn("DC 17", txt)
        self.assertIn("Kesto (CON)", txt)

    def test_save_based_action(self):
        a = Action("Mind Blast", "", 0, "5d8", 0, "psychic", range=60,
                   aoe_radius=60, aoe_shape="cone",
                   condition_save="Intelligence", condition_dc=17)
        txt = explain_action(a)
        self.assertIn("Pelastus", txt)
        self.assertIn("Äly (INT)", txt)
        self.assertIn("kartio", txt)


class TestFeatureExplain(unittest.TestCase):
    def test_mechanic_lookup(self):
        f = Feature("Magic Resistance", "whatever", mechanic="magic_resistance")
        self.assertIn("Maagivastus", explain_feature(f))

    def test_keyword_lookup_when_no_mechanic(self):
        f = Feature("Legendary Resistance", "3/day", uses_per_day=3)
        txt = explain_feature(f)
        self.assertIn("Legendaarinen vastus", txt)
        self.assertIn("3/päivä", txt)

    def test_fallback_to_description(self):
        f = Feature("Aether Ward", "Starts with 45 temp HP")
        self.assertIn("45 temp", explain_feature(f))


class TestAiPlanSummary(unittest.TestCase):
    def test_skipped_plan(self):
        class P:
            skipped = True
            skip_reason = "toimintakyvytön"
            steps = []
        self.assertIn("ohittaisi", summarize_ai_plan_fi(P())[0])

    def test_none_plan(self):
        self.assertTrue(summarize_ai_plan_fi(None))

    def test_attack_and_move_steps(self):
        from engine.ai import ActionStep

        class Tgt:
            name = "Hero"

        class P:
            skipped = False
            skip_reason = ""
            steps = []
        mv = ActionStep("move")
        mv.movement_ft = 20
        atk = ActionStep("attack")
        atk.action_name = "Aether Siphon"
        atk.target = Tgt()
        P.steps = [mv, atk]
        lines = summarize_ai_plan_fi(P())
        self.assertTrue(any("Liiku" in l for l in lines))
        self.assertTrue(any("Hyökkää" in l and "Hero" in l for l in lines))


def _ent(name, hp, ac=15, is_player=True, x=0, y=0):
    s = CreatureStats(name=name, hit_points=hp, armor_class=ac, speed=30,
                      abilities=AbilityScores(strength=14, dexterity=14,
                                              constitution=14))
    return Entity(s, x, y, is_player=is_player)


class TestTacticalAdvice(unittest.TestCase):
    def test_low_hp_target_rationale(self):
        wounded = _ent("Wounded", 40, is_player=True)
        wounded.hp = 8  # 20 %
        healthy = _ent("Orc", 60, is_player=False, x=5, y=5)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[wounded, healthy])
        txt = target_rationale_fi(wounded, battle)
        self.assertIn("matala HP", txt)

    def test_rationale_never_empty(self):
        a = _ent("A", 30, is_player=True)
        b = _ent("B", 30, is_player=False, x=5, y=5)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[a, b])
        self.assertTrue(target_rationale_fi(b, battle))

    def test_difficulty_read_is_finnish(self):
        hero = _ent("Hero", 100, is_player=True)
        goblin = _ent("Goblin", 7, is_player=False, x=5, y=5)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[hero, goblin])
        txt = difficulty_read_fi(battle)
        self.assertIn("Voitto-%", txt)

    def test_difficulty_read_no_target_safe(self):
        # No enemies -> calculator returns a result; must not raise.
        hero = _ent("Hero", 100, is_player=True)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=[hero])
        # Should not raise
        difficulty_read_fi(battle)


if __name__ == "__main__":
    unittest.main()
