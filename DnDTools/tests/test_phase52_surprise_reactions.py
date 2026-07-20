"""Phase 52 — a surprised creature can't take reactions until the end of
its first turn (PHB p.189): no opportunity attacks, no Shield/Counterspell.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.reaction_advisor import _has_reaction_available


def _mk(name, x, y, is_player):
    s = CreatureStats(name=name, hit_points=40, armor_class=13, speed=30,
                      abilities=AbilityScores(strength=14, dexterity=14),
                      actions=[Action("Sword", "Melee", 5, "1d8", 3,
                                      "slashing")])
    return Entity(s, x, y, is_player=is_player)


class TestSurpriseGatesReactions(unittest.TestCase):
    def test_surprised_has_no_reaction(self):
        e = _mk("Guard", 0, 0, False)
        e.is_surprised = True
        self.assertFalse(_has_reaction_available(e))

    def test_unsurprised_has_reaction(self):
        e = _mk("Guard", 0, 0, False)
        e.is_surprised = False
        self.assertTrue(_has_reaction_available(e))

    def test_surprised_watcher_makes_no_oa(self):
        watcher = _mk("Guard", 5, 5, False)
        mover = _mk("Rogue", 6, 5, True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[watcher, mover])
        watcher.is_surprised = True
        mover.grid_x = 9.0  # leaves the guard's reach
        self.assertEqual(b.check_opportunity_attacks(mover, 6.0, 5.0), [])

    def test_awake_watcher_makes_oa(self):
        watcher = _mk("Guard", 5, 5, False)
        mover = _mk("Rogue", 6, 5, True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[watcher, mover])
        mover.grid_x = 9.0
        oas = b.check_opportunity_attacks(mover, 6.0, 5.0)
        self.assertIn(watcher, oas)

    def test_incapacitated_watcher_makes_no_oa(self):
        watcher = _mk("Guard", 5, 5, False)
        mover = _mk("Rogue", 6, 5, True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[watcher, mover])
        watcher.add_condition("Stunned")
        mover.grid_x = 9.0
        self.assertEqual(b.check_opportunity_attacks(mover, 6.0, 5.0), [])


if __name__ == "__main__":
    unittest.main()
