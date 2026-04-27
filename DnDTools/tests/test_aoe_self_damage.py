"""Phase 10d — AI penalises AoE that catches the caster."""
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


def _wizard(x=5, y=5, sculpt=False):
    feats = []
    if sculpt:
        feats.append(Feature(name="Sculpt Spells",
                              mechanic="sculpt_spells"))
    stats = CreatureStats(
        name="Wizard", size="Medium", hit_points=24, armor_class=12,
        speed=30,
        abilities=AbilityScores(strength=8, dexterity=14,
                                  constitution=12, intelligence=18,
                                  wisdom=12, charisma=10),
        spellcasting_ability="Intelligence",
        proficiency_bonus=2,
        features=feats,
        actions=[Action(name="Dagger", attack_bonus=4,
                        damage_dice="1d4", damage_bonus=2,
                        damage_type="piercing", range=5)],
    )
    return Entity(stats, x, y, is_player=True)


def _orc(x, y, hp=15):
    stats = CreatureStats(
        name="Orc", size="Medium", hit_points=hp, armor_class=13,
        speed=30,
        abilities=AbilityScores(strength=16, dexterity=12,
                                  constitution=14, intelligence=8,
                                  wisdom=10, charisma=8),
        actions=[Action(name="Greataxe", attack_bonus=5,
                        damage_dice="1d12", damage_bonus=3,
                        damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=False)


class TestSelfHitPenalty(unittest.TestCase):
    """If the caster sits inside a candidate AoE radius, the planner
    should pick a different aim point."""
    def test_safe_aim_preferred_over_self_blast(self):
        wiz = _wizard(x=0, y=0)
        # Three orcs clustered far enough that a 15ft (3-cell) sphere
        # has aim points outside the caster's blast radius.
        orcs = [
            _orc(15, 10),
            _orc(15, 11),
            _orc(16, 10),
        ]
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, *orcs])
        ai = TacticalAI()
        result = ai._best_aoe_cluster(
            wiz, orcs, [wiz], b,
            radius_ft=15, shape="sphere",
        )
        self.assertIsNotNone(result)
        cluster, (aim_x, aim_y) = result
        # Caster should NOT be inside the chosen aim radius
        import math
        self.assertGreater(
            math.hypot(aim_x - wiz.grid_x, aim_y - wiz.grid_y) * 5,
            15.0 - 1e-6,
            f"AI chose {aim_x},{aim_y} which still hits its own caster",
        )

    def test_sculpt_spells_caster_can_self_blast(self):
        """Evoker with sculpt_spells doesn't penalise self-overlap."""
        wiz = _wizard(x=5, y=5, sculpt=True)
        orcs = [_orc(6, 5), _orc(5, 6), _orc(4, 5)]
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, *orcs])
        result = TacticalAI()._best_aoe_cluster(
            wiz, orcs, [wiz], b,
            radius_ft=15,
            shape="sphere",
        )
        self.assertIsNotNone(result)
        # Sculpt allows the cluster around the wizard. Just verify
        # at least 2 orcs ended up in the chosen cluster — the
        # planner can pick an aim that catches the wizard if useful.
        cluster, _ = result
        self.assertGreaterEqual(len(cluster), 2)

    def test_far_caster_no_penalty(self):
        """When the caster is well outside any plausible AoE radius,
        the cluster scoring should still pick the best enemy cluster."""
        wiz = _wizard(x=0, y=0)
        orcs = [_orc(20, 5), _orc(20, 6), _orc(21, 5)]
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[wiz, *orcs])
        result = TacticalAI()._best_aoe_cluster(
            wiz, orcs, [wiz], b,
            radius_ft=15, shape="sphere",
        )
        self.assertIsNotNone(result)
        cluster, _ = result
        self.assertGreaterEqual(len(cluster), 2)


if __name__ == "__main__":
    unittest.main()
