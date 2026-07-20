"""Phase 50 — spellcasting/rules fixes from the RAW audit.

  * Dice parser handles multi-term expressions ("2d8+4d6") and upcast
    strings ("8d6+1d6") — previously everything after the first die was
    dropped.
  * half_on_save=False spells (Sacred Flame etc.) deal 0 on a successful
    save, not half.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from engine.dice import roll_dice, roll_dice_critical, average_damage


class TestMultiTermDice(unittest.TestCase):
    def test_average_multi_term(self):
        self.assertAlmostEqual(average_damage("2d8+4d6"), 9 + 14)      # 23
        self.assertAlmostEqual(average_damage("20d6+20d6"), 140)
        self.assertAlmostEqual(average_damage("1d8+2d6"), 4.5 + 7)     # 11.5
        self.assertAlmostEqual(average_damage("2d6+3"), 7 + 3)         # 10

    def test_roll_range_multi_term(self):
        for _ in range(500):
            v = roll_dice("2d8+4d6")
            self.assertGreaterEqual(v, 6)    # 2 + 4
            self.assertLessEqual(v, 40)      # 16 + 24

    def test_flat_and_negative(self):
        self.assertEqual(average_damage("10"), 10)
        vals = [roll_dice("1d6-1") for _ in range(500)]
        self.assertGreaterEqual(min(vals), 0)   # clamped
        self.assertLessEqual(max(vals), 5)

    def test_crit_doubles_all_dice_not_flat(self):
        # 1d8+5 crit -> 2d8+5 : range 7..21, flat added once
        vals = [roll_dice_critical("1d8+5") for _ in range(500)]
        self.assertGreaterEqual(min(vals), 7)
        self.assertLessEqual(max(vals), 21)
        # multi-term crit doubles every die: 2d8+4d6 -> 4d8+8d6
        vals2 = [roll_dice_critical("2d8+4d6") for _ in range(500)]
        self.assertLessEqual(max(vals2), 32 + 48)


class TestHalfOnSaveNegate(unittest.TestCase):
    def _setup(self):
        import pygame
        pygame.init()
        pygame.display.set_mode((320, 240))
        from states.battle_state import BattleState
        from engine.ai import ActionStep
        from data.models import CreatureStats, AbilityScores, SpellInfo
        from engine.entities import Entity

        class FM:
            def __init__(s):
                s.screen = pygame.display.get_surface()
                s.running = True

            def change_state(s, *a, **k):
                pass

        def mk(name, is_player):
            st = CreatureStats(name=name, hit_points=40, armor_class=13,
                               speed=30, abilities=AbilityScores())
            return Entity(st, 0, 0, is_player=is_player)

        caster = mk("Cleric", False)
        target = mk("Hero", True)
        bs = BattleState(FM(), entities=[caster, target])
        return bs, caster, target, ActionStep, SpellInfo

    def test_negate_spell_deals_zero_on_save(self):
        bs, caster, target, ActionStep, SpellInfo = self._setup()
        step = ActionStep("spell")
        step.attacker = caster
        step.target = target
        step.damage = 12
        step.damage_type = "radiant"
        step.save_ability = "Dexterity"
        step.spell = SpellInfo("Sacred Flame", level=0, half_on_save=False)
        hp0 = target.hp
        bs._resolve_target_outcome(step, target, "save")
        self.assertEqual(target.hp, hp0, "half_on_save=False must deal 0 on save")

    def test_half_on_save_true_still_halves(self):
        bs, caster, target, ActionStep, SpellInfo = self._setup()
        step = ActionStep("spell")
        step.attacker = caster
        step.target = target
        step.damage = 12
        step.damage_type = "fire"
        step.save_ability = "Dexterity"
        step.spell = SpellInfo("Fireball", level=3, half_on_save=True)
        hp0 = target.hp
        bs._resolve_target_outcome(step, target, "save")
        self.assertEqual(target.hp, hp0 - 6, "half_on_save=True deals half")


if __name__ == "__main__":
    unittest.main()
