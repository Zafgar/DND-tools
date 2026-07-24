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


class TestAoEFriendlyFire(unittest.TestCase):
    """PHB: an area spell hits every creature in the area, friend or foe."""

    def _ai_and_battle(self):
        from data.models import CreatureStats, AbilityScores
        from engine.entities import Entity
        from engine.battle import BattleSystem
        from engine.ai import TacticalAI

        def mk(n, x, y, pl):
            s = CreatureStats(name=n, hit_points=40, armor_class=13,
                              speed=30, abilities=AbilityScores())
            return Entity(s, x, y, is_player=pl)
        return mk, BattleSystem, TacticalAI

    def test_ally_in_blast_is_included(self):
        mk, BattleSystem, TacticalAI = self._ai_and_battle()
        caster = mk("Mage", 0, 0, False)
        foe1 = mk("Hero1", 5, 5, True)
        foe2 = mk("Hero2", 6, 5, True)
        ally = mk("Ally", 5, 6, False)          # standing in the cluster
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, foe1, foe2, ally])
        cluster, _ = TacticalAI()._best_aoe_cluster(
            caster, [foe1, foe2], [ally], b, radius_ft=20, shape="sphere")
        names = {e.name for e in cluster}
        self.assertIn("Ally", names, "ally in the blast must take the hit")
        self.assertIn("Hero1", names)

    def test_distant_ally_not_included(self):
        mk, BattleSystem, TacticalAI = self._ai_and_battle()
        caster = mk("Mage", 0, 0, False)
        foe1 = mk("Hero1", 5, 5, True)
        foe2 = mk("Hero2", 6, 5, True)
        ally = mk("Ally", 0, 1, False)           # far from the blast center
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, foe1, foe2, ally])
        cluster, _ = TacticalAI()._best_aoe_cluster(
            caster, [foe1, foe2], [ally], b, radius_ft=20, shape="sphere")
        self.assertNotIn("Ally", {e.name for e in cluster})



if __name__ == "__main__":
    unittest.main()


class TestUpcastScaling(unittest.TestCase):
    """Leveled spells scale to the slot spent (needs the multi-term dice
    parser to combine base + scaling correctly)."""

    def _wizard(self):
        from data.models import CreatureStats, AbilityScores
        from engine.entities import Entity
        st = CreatureStats(name="Wiz",
                           abilities=AbilityScores(intelligence=18),
                           spellcasting_ability="Intelligence",
                           character_level=9)
        return Entity(st, 0, 0, is_player=True)

    def test_fireball_upcasts_extra_dice(self):
        from engine.ai.utils import _get_spell_damage_dice
        from engine.dice import average_damage
        from data.spells import get_spell
        e = self._wizard()
        fb = get_spell("Fireball")
        base = average_damage(_get_spell_damage_dice(fb, e, slot_used=3))
        up = average_damage(_get_spell_damage_dice(fb, e, slot_used=5))
        self.assertGreater(up, base + 6, "5th-level Fireball adds ~2d6")

    def test_magic_missile_scales_darts(self):
        from engine.ai.utils import _get_spell_damage_dice
        from engine.dice import average_damage
        from data.spells import get_spell
        e = self._wizard()
        mm = get_spell("Magic Missile")
        base = average_damage(_get_spell_damage_dice(mm, e, slot_used=1))
        up = average_damage(_get_spell_damage_dice(mm, e, slot_used=3))
        self.assertGreater(up, base, "upcast Magic Missile adds darts")



if __name__ == "__main__":
    unittest.main()
