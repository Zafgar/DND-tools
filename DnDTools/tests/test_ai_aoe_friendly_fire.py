"""AI ei enää tuhoa omaa ryhmäänsä AoE-loitsuilla, eikä juo montaa
juomaa yhdellä vuorolla.

Kaksi optimointikorjausta:
  * ``_try_aoe_spell`` laskee liittolaisiin (ja itseen) osuvan vahingon
    KUSTANNUKSEKSI (ei hyödyksi). AI heittää AoE:n vain jos vihollisiin
    kohdistuva EV selvästi ylittää oman ryhmän saaman vahingon.
  * Juoman juominen on toiminto (RAW 2014): vain yksi juoma / vuoro.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((320, 240))

from data.models import CreatureStats, AbilityScores, Item
from data.heroes import hero_list
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI


def _foe(name, x, y):
    s = CreatureStats(name=name, hit_points=40, armor_class=14, speed=30,
                      abilities=AbilityScores(strength=12, dexterity=12,
                                              constitution=12, intelligence=8,
                                              wisdom=10, charisma=8))
    return Entity(s, x, y, is_player=False)


def _ally(name, x, y):
    s = CreatureStats(name=name, hit_points=40, armor_class=14, speed=30,
                      abilities=AbilityScores(strength=12, dexterity=12,
                                              constitution=12, intelligence=8,
                                              wisdom=10, charisma=8))
    return Entity(s, x, y, is_player=True)


def _venris():
    return {h.name: h for h in hero_list}["Venris Galanodel"]


def _casts_aoe(enemy_pos, ally_pos):
    caster = Entity(_venris(), 0, 0, is_player=True)
    ents = [caster]
    enemies, allies = [], []
    for i, (x, y) in enumerate(enemy_pos):
        e = _foe(f"Foe{i}", x, y)
        ents.append(e)
        enemies.append(e)
    for i, (x, y) in enumerate(ally_pos):
        a = _ally(f"Ally{i}", x, y)
        ents.append(a)
        allies.append(a)
    battle = BattleSystem(log_callback=lambda s: None, initial_entities=ents)
    caster.reset_turn()
    ai = TacticalAI()
    return ai._try_aoe_spell(caster, enemies, allies, battle) is not None


class TestAoeFriendlyFire(unittest.TestCase):
    def test_two_enemies_no_ally_casts(self):
        self.assertTrue(_casts_aoe([(10, 10), (11, 10)], []))

    def test_two_enemies_two_allies_declines(self):
        # Net friendly fire ≈ enemy value → not worth it.
        self.assertFalse(_casts_aoe([(10, 10), (11, 10)],
                                    [(10, 11), (11, 11)]))

    def test_three_enemies_two_allies_declines(self):
        self.assertFalse(_casts_aoe([(10, 10), (11, 10), (10, 11)],
                                    [(11, 11), (11, 12)]))

    def test_four_enemies_one_ally_casts(self):
        # Clipping one ally to hit four enemies is optimal.
        self.assertTrue(_casts_aoe(
            [(10, 10), (11, 10), (10, 11), (11, 11)], [(10, 12)]))

    def test_ally_out_of_blast_casts(self):
        self.assertTrue(_casts_aoe([(10, 10), (11, 10)], [(2, 2)]))


class TestMonsterBreathFriendlyFire(unittest.TestCase):
    """A monster with a breath weapon must not gas its own allies."""

    def _dragon(self, x, y):
        from data.models import Action
        s = CreatureStats(
            name="Dragon", hit_points=100, armor_class=17, speed=30,
            abilities=AbilityScores(strength=18, dexterity=10,
                                    constitution=18, intelligence=10,
                                    wisdom=12, charisma=12),
            actions=[Action("Fire Breath", "30ft cone", 0, "12d6", 0, "fire",
                            aoe_radius=30, aoe_shape="cone",
                            condition_save="Dexterity", condition_dc=18)])
        return Entity(s, x, y, is_player=False)

    def _breathes(self, pc_pos, ally_mon_pos):
        dragon = self._dragon(0, 5)
        ents = [dragon]
        enemies, allies = [], []
        for i, (x, y) in enumerate(pc_pos):
            p = _ally(f"PC{i}", x, y)   # players are the dragon's enemies
            ents.append(p)
            enemies.append(p)
        for i, (x, y) in enumerate(ally_mon_pos):
            m = _foe(f"Minion{i}", x, y)  # same side as the dragon
            ents.append(m)
            allies.append(m)
        battle = BattleSystem(log_callback=lambda s: None,
                              initial_entities=ents)
        ai = TacticalAI()
        return ai._try_aoe_action(dragon, enemies, allies, battle) is not None

    def test_clean_cone_breathes(self):
        self.assertTrue(self._breathes([(5, 5), (6, 5)], []))

    def test_one_enemy_one_ally_declines(self):
        self.assertFalse(self._breathes([(5, 5)], [(5, 6)]))


class TestOnePotionPerTurn(unittest.TestCase):
    def _wounded_barbarian(self):
        krusk = Entity({h.name: h for h in hero_list}["Krusk"], 0, 0,
                       is_player=True)
        krusk.hp = 20  # badly hurt so healing is attractive
        # Give it two healing potions.
        krusk.items = [
            Item(name="Potion of Superior Healing", item_type="potion",
                 heals="8d4+8", uses=1),
            Item(name="Potion of Greater Healing", item_type="potion",
                 heals="4d4+4", uses=1),
        ]
        krusk.reset_turn()
        return krusk

    def test_heal_action_sets_potion_flag(self):
        ai = TacticalAI()
        krusk = self._wounded_barbarian()
        step = ai._try_heal_action(krusk)
        self.assertIsNotNone(step)
        self.assertTrue(krusk.potion_used_this_turn)

    def test_second_potion_blocked_same_turn(self):
        ai = TacticalAI()
        krusk = self._wounded_barbarian()
        first = ai._try_heal_action(krusk)
        self.assertIsNotNone(first)
        # Bonus-action potion must not fire after an action potion.
        second = ai._try_use_healing_potion_bonus(krusk)
        self.assertIsNone(second)
        # And a second action potion is likewise blocked.
        third = ai._try_heal_action(krusk)
        self.assertIsNone(third)

    def test_potion_flag_resets_next_turn(self):
        krusk = self._wounded_barbarian()
        krusk.potion_used_this_turn = True
        krusk.reset_turn()
        self.assertFalse(krusk.potion_used_this_turn)


class TestReactionLabelText(unittest.TestCase):
    """A reaction that spawns a label ("Shield!", "Parry!", "Dodge!"...)
    must not crash — _spawn_damage_text used to abs() the string."""

    class _FM:
        def __init__(self):
            self.screen = pygame.display.get_surface()
            self.running = True

        def change_state(self, *a, **k):
            pass

    def _battle_state(self):
        from states.battle_state import BattleState
        watcher = _foe("Guard", 5, 5)
        mover = _ally("Rogue", 6, 5)
        return BattleState(self._FM(), entities=[watcher, mover]), mover

    def test_string_label_does_not_crash(self):
        bs, target = self._battle_state()
        for label in ("Shield!", "Parry!", "Absorb!", "Dodge!",
                      "Wild Shape!", "Silvery!"):
            bs._spawn_damage_text(target, label, is_heal=True)  # must not raise
        self.assertTrue(bs.floating_texts)

    def test_numeric_amount_still_formats(self):
        bs, target = self._battle_state()
        before = len(bs.floating_texts)
        bs._spawn_damage_text(target, -12, damage_type="fire")
        bs._spawn_damage_text(target, 8, is_heal=True)
        self.assertEqual(len(bs.floating_texts), before + 2)


if __name__ == "__main__":
    unittest.main()
