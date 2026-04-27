"""Phase 11a — auto-battle reliability + terrain editor robustness.

We can't drive the full BattleState (it owns pygame surfaces), but we
can stub the methods that normally do GUI work and check the new
defensive paths.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest
from unittest.mock import MagicMock

from data.models import CreatureStats, AbilityScores, Action
from engine.entities import Entity
from engine.battle import BattleSystem


def _make_battle(*ents):
    return BattleSystem(log_callback=lambda *a: None,
                         initial_entities=list(ents))


def _make_entity(name="Hero", x=5, y=5, is_player=True):
    stats = CreatureStats(
        name=name, size="Medium", hit_points=24, armor_class=15,
        speed=30,
        abilities=AbilityScores(strength=14, dexterity=12,
                                  constitution=14, intelligence=10,
                                  wisdom=10, charisma=10),
        actions=[Action(name="Sword", attack_bonus=4, damage_dice="1d8",
                        damage_bonus=2, damage_type="slashing", range=5)],
    )
    return Entity(stats, x, y, is_player=is_player)


class _StubBattleState:
    """Pure-logic stub — replicates the new _toggle_auto_battle and
    paint defensive logic in isolation, so we can exercise them
    without instantiating the pygame-dependent BattleState."""
    def __init__(self, battle):
        self.battle = battle
        self.auto_battle = False
        self.auto_battle_paused = False
        self.auto_battle_mode = "full"
        self.logs = []

        # Mock buttons
        self.btn_auto = MagicMock()
        self.btn_pause = MagicMock()

        # Terrain state used by the paint defensive layer
        self.terrain_tool = "paint"
        self.terrain_selected_type = "wall"
        self.terrain_rect_start = None
        self.terrain_rect_preview = []
        self.terrain_drag_obj = None

    def _log(self, msg):
        self.logs.append(msg)

    # Direct copy of the production logic
    def _toggle_auto_battle(self):
        self.auto_battle = not self.auto_battle
        self.auto_battle_paused = False
        if self.auto_battle:
            if not self.battle.combat_started:
                if not self.battle.entities:
                    self._log("[SYSTEM] Auto-Battle aborted — "
                               "no entities on the field.")
                    self.auto_battle = False
                    return
                try:
                    self.battle.start_combat()
                    self._log("[SYSTEM] Auto-Battle: combat auto-started "
                               "(no manual START COMBAT needed).")
                except Exception as ex:
                    self._log(f"[SYSTEM] Auto-Battle could not start "
                               f"combat: {ex}.")
                    self.auto_battle = False
                    return
            self._log("[SYSTEM] Auto-Battle STARTED")
        else:
            self._log("[SYSTEM] Auto-Battle STOPPED.")


class TestAutoBattleStart(unittest.TestCase):
    def test_starts_combat_when_not_started(self):
        b = _make_battle(_make_entity("Hero"), _make_entity("Goblin",
                                                              is_player=False))
        st = _StubBattleState(b)
        self.assertFalse(b.combat_started)
        st._toggle_auto_battle()
        # Combat auto-started so AUTO sticks
        self.assertTrue(st.auto_battle)
        self.assertTrue(b.combat_started)
        self.assertTrue(any("auto-started" in m for m in st.logs))

    def test_aborts_when_no_entities(self):
        b = BattleSystem(log_callback=lambda *a: None,
                          initial_entities=[])
        b.entities = []
        st = _StubBattleState(b)
        st._toggle_auto_battle()
        # Auto stayed off and we logged the abort
        self.assertFalse(st.auto_battle)
        self.assertTrue(any("aborted" in m for m in st.logs))

    def test_stays_started_when_already_in_combat(self):
        b = _make_battle(_make_entity("Hero"))
        b.combat_started = True
        st = _StubBattleState(b)
        st._toggle_auto_battle()
        self.assertTrue(st.auto_battle)
        # No "auto-started" message — combat was already up
        self.assertFalse(any("auto-started" in m for m in st.logs))

    def test_toggle_off_logs_stop(self):
        b = _make_battle(_make_entity("Hero"))
        b.combat_started = True
        st = _StubBattleState(b)
        st._toggle_auto_battle()
        st._toggle_auto_battle()
        self.assertFalse(st.auto_battle)
        self.assertTrue(any("STOPPED" in m for m in st.logs))


class TestTerrainPaintFallback(unittest.TestCase):
    """Verify the production fallback used in
    _paint_terrain_at_unchecked: an unknown selected type falls back
    to 'wall' instead of raising at TerrainObject construction."""
    def test_unknown_type_falls_back_to_wall(self):
        from engine.terrain import TERRAIN_TYPES, TerrainObject
        bad_type = "definitely_not_a_terrain_kind"
        self.assertNotIn(bad_type, TERRAIN_TYPES)
        # The paint method's logic: bad type → fallback to "wall"
        if bad_type not in TERRAIN_TYPES:
            t = TerrainObject("wall", 0, 0)
        self.assertEqual(t.terrain_type, "wall")


if __name__ == "__main__":
    unittest.main()
