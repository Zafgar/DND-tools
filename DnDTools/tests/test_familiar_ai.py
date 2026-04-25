"""Phase 9a — AI familiar control tests."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import CreatureStats, AbilityScores, Action
from data.familiars import summon_familiar
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai.tactical_ai import TacticalAI


def _wizard(x=5, y=5, hp=24):
    stats = CreatureStats(
        name="Wizard", size="Medium", hit_points=hp, armor_class=12,
        speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=12, intelligence=18,
                                  wisdom=12, charisma=10),
        spellcasting_ability="Intelligence",
        proficiency_bonus=2,
        actions=[Action(name="Dagger", attack_bonus=4, damage_dice="1d4",
                        damage_bonus=2, damage_type="piercing", range=5)],
    )
    return Entity(stats, x, y, is_player=True)


def _fighter(x=6, y=5, hp=30):
    stats = CreatureStats(
        name="Fighter", size="Medium", hit_points=hp, armor_class=18,
        speed=30,
        abilities=AbilityScores(strength=16, dexterity=12,
                                  constitution=14, intelligence=10,
                                  wisdom=10, charisma=10),
        actions=[Action(name="Longsword", attack_bonus=5, damage_dice="1d8",
                        damage_bonus=3, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=True)


def _goblin(x=7, y=5, hp=10):
    stats = CreatureStats(
        name="Goblin", size="Small", hit_points=hp, armor_class=15,
        speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=10, intelligence=10,
                                  wisdom=8, charisma=8),
        actions=[Action(name="Scimitar", attack_bonus=4,
                        damage_dice="1d6", damage_bonus=2,
                        damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=False)


def _battle(*entities):
    b = BattleSystem(log_callback=lambda *a: None,
                      initial_entities=list(entities))
    return b


class TestFamiliarHelpAction(unittest.TestCase):
    def test_help_when_ally_engages_same_enemy(self):
        """Goblin is between fighter and the familiar — perfect Help spot."""
        wizard = _wizard(x=2, y=5)
        fighter = _fighter(x=6, y=5)
        goblin = _goblin(x=7, y=5)
        b = _battle(wizard, fighter, goblin)
        owl = summon_familiar(b, wizard, kind="owl", x=8, y=5)

        plan = TacticalAI()._handle_familiar_turn(owl, b, _new_plan(owl))
        self.assertFalse(plan.skipped)
        # First step should be Help
        first = plan.steps[0]
        self.assertEqual(first.action_name, "Help")
        self.assertIs(first.target, goblin)
        self.assertIn("Help", first.description)
        self.assertIn("advantage", first.description.lower())

    def test_help_picks_an_engaged_enemy(self):
        """Two enemies adjacent to familiar; Help fires on the one
        an ally is also engaging."""
        wizard = _wizard(x=2, y=5)
        fighter = _fighter(x=6, y=5)
        engaged = _goblin(x=7, y=5)
        loose = _goblin(x=8, y=4)
        b = _battle(wizard, fighter, engaged, loose)
        owl = summon_familiar(b, wizard, kind="owl", x=8, y=5)

        plan = TacticalAI()._handle_familiar_turn(owl, b, _new_plan(owl))
        first = plan.steps[0]
        self.assertEqual(first.action_name, "Help")
        self.assertIs(first.target, engaged)


class TestFamiliarRetreat(unittest.TestCase):
    def test_no_help_target_dodges_near_owner(self):
        wizard = _wizard(x=2, y=5)
        b = _battle(wizard)
        owl = summon_familiar(b, wizard, kind="owl", x=10, y=5)

        plan = TacticalAI()._handle_familiar_turn(owl, b, _new_plan(owl))
        # At least Dodge declared; possibly a move-to-owner step too
        action_names = [s.action_name for s in plan.steps]
        self.assertIn("Dodge", action_names)

    def test_already_adjacent_owner_only_dodges(self):
        wizard = _wizard(x=5, y=5)
        b = _battle(wizard)
        # Familiar lands adjacent on default east cell (6, 5)
        owl = summon_familiar(b, wizard, kind="owl")

        plan = TacticalAI()._handle_familiar_turn(owl, b, _new_plan(owl))
        # No move step needed when already adjacent
        moves = [s for s in plan.steps if s.step_type == "move"]
        self.assertEqual(len(moves), 0)
        self.assertEqual(plan.steps[-1].action_name, "Dodge")

    def test_dodging_condition_in_step(self):
        wizard = _wizard(x=5, y=5)
        b = _battle(wizard)
        owl = summon_familiar(b, wizard, kind="owl")
        plan = TacticalAI()._handle_familiar_turn(owl, b, _new_plan(owl))
        dodge_step = next(s for s in plan.steps if s.action_name == "Dodge")
        self.assertEqual(dodge_step.applies_condition, "Dodging")


class TestFamiliarOwnerDefeated(unittest.TestCase):
    def test_no_owner_skips_turn(self):
        wizard = _wizard()
        b = _battle(wizard)
        owl = summon_familiar(b, wizard, kind="owl")
        wizard.hp = 0
        plan = TacticalAI()._handle_summon_turn(owl, b, _new_plan(owl))
        self.assertTrue(plan.skipped)
        self.assertIn("Owner defeated", plan.skip_reason)


class TestFamiliarRouting(unittest.TestCase):
    """Ensure the dispatch in _handle_summon_turn forwards Find Familiar
    summons to the new familiar handler instead of the attack code."""
    def test_familiar_takes_familiar_branch(self):
        wizard = _wizard(x=2, y=5)
        b = _battle(wizard)
        owl = summon_familiar(b, wizard, kind="owl")
        plan = TacticalAI()._handle_summon_turn(owl, b, _new_plan(owl))
        # No attack should be planned for a 1-HP familiar
        attacks = [s for s in plan.steps if s.step_type == "attack"]
        self.assertEqual(attacks, [])

    def test_spiritual_weapon_keeps_attack_branch(self):
        wizard = _wizard(x=2, y=5)
        goblin = _goblin(x=4, y=5)
        b = _battle(wizard, goblin)
        sw = b.spawn_summon(
            owner=wizard, name="Spiritual Weapon",
            x=3, y=5, damage_dice="1d8", damage_type="force",
            duration=10, spell_name="Spiritual Weapon",
        )
        plan = TacticalAI()._handle_summon_turn(sw, b, _new_plan(sw))
        # SW should still try to attack
        steps = [s.step_type for s in plan.steps]
        # Either bonus_attack or attack — both valid
        self.assertTrue(any(t in ("attack", "bonus_attack") for t in steps),
                         f"Expected attack step in {steps}")


# --------------------------------------------------------------------- #
def _new_plan(entity):
    from engine.ai.models import TurnPlan
    return TurnPlan(entity=entity)


if __name__ == "__main__":
    unittest.main()
