"""Combat auditin löytämät viat — korjaukset ja niiden regressiotestit.

Työkalu löysi nämä ajamalla 70 oikeaa taistelua. Jokainen testi tässä
vastaa yhtä löydöstä, ja kuvaa mitä oikeasti tapahtui — ei sitä mitä
koodin pitäisi tehdä.

  * Kaatunut Spiritual Weapon jatkoi iskemistä −1 HP:llä, koska kutsu
    on pelaajan puolella ja täytti "kuoleva pelaaja saa silti vuoron"
    -ehdon. Kutsu on loitsuefekti: se tuhoutuu nollassa eikä heitä
    kuolinheittoja.
  * Suunnitelma tehdään kerralla ja vahvistetaan askel kerrallaan.
    Välissä ehtii tapahtua paljon — vapaaisku, maastovahinko — ja
    kaatunut olento jatkoi silti vuoroaan loppuun.
  * Luonnollinen 1 kuolinheitossa lisää kaksi epäonnistumista. Ilman
    kattoa hahmolla luki "1s/4f", pistemäärä jota ei ole olemassa.
  * Lähitaistelija joka oli juuri sulkenut etäisyyden ja iskenyt juoksi
    25 jalkaa pois hajaantuakseen — antaen ilmaisen vapaaiskun ja
    hukaten liikkeensä.
  * Spiritual Weapon "liikkui" mihin tahansa vapaaseen ruutuun kohteen
    vierellä etäisyydestä riippumatta (66 jalkaa 20 jalan nopeudella),
    ja iski silloinkin kun se ei yltänyt.
  * Neljä tilaa (Lethargic, Turned, Max HP Reduced, Cursed) asetettiin
    ilman merkintää tilataulukossa, joten pelinjohtaja ei nähnyt niitä.
"""
import sys
import os
import copy
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.conditions import CONDITIONS, CONDITION_EFFECTS
from data.heroes import hero_list
from data.library import library
from engine.ai import TacticalAI
from engine.ai.models import ActionStep
from engine.battle import BattleSystem
from engine.entities import Entity
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name="Magnus Dragonius"):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


def _mon(name, x, y, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)),
                  float(x), float(y), is_player=player)


def _battle(*ents):
    return BattleSystem(log_callback=lambda s: None,
                        initial_entities=list(ents))


# ===================================================================== #
# 1. A DESTROYED SUMMON IS GONE
# ===================================================================== #
class TestDestroyedSummons(unittest.TestCase):

    def _weapon(self, b, owner):
        return b.spawn_summon(owner, "Spiritual Weapon", 6, 5,
                              hp=20, ac=12, damage_dice="1d8")

    def test_a_summon_at_zero_hp_is_removed(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        b = _battle(pc)
        w = self._weapon(b, pc)
        self.assertIn(w, b.entities)
        w.hp = 0
        b.remove_expired_summons()
        self.assertNotIn(w, b.entities, "the wreck stayed on the field")

    def test_an_expired_summon_is_still_removed(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        b = _battle(pc)
        w = self._weapon(b, pc)
        w.summon_rounds_left = 0
        b.remove_expired_summons()
        self.assertNotIn(w, b.entities)

    def test_a_living_summon_is_left_alone(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        b = _battle(pc)
        w = self._weapon(b, pc)
        b.remove_expired_summons()
        self.assertIn(w, b.entities)

    def test_a_downed_summon_does_not_get_a_turn_to_roll_death_saves(self):
        """Se oli tarkka mekanismi: kutsu on is_player=True, joten se
        täytti 'kuoleva pelaaja saa vuoron' -ehdon."""
        pc = Entity(_hero(), 5, 5, is_player=True)
        foe = _mon("Ogre", 12, 5)
        b = _battle(pc, foe)
        w = self._weapon(b, pc)
        b.start_combat()
        w.hp = -1
        for _ in range(len(b.entities) * 3):
            b.next_turn()
            self.assertIsNot(b.get_current_entity(), w,
                             "a destroyed summon took a turn")

    def test_a_downed_player_still_gets_their_death_saves(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        foe = _mon("Ogre", 12, 5)
        b = _battle(pc, foe)
        b.start_combat()
        pc.hp = 0
        seen = set()
        for _ in range(8):
            b.next_turn()
            seen.add(b.get_current_entity())
        self.assertIn(pc, seen, "a dying player lost their death saves")


# ===================================================================== #
# 2. A TURN STOPS WHEN ITS ACTOR GOES DOWN
# ===================================================================== #
class TestPlanAbortsOnDeath(unittest.TestCase):

    def test_the_rest_of_the_turn_is_cancelled(self):
        foe = _mon("Ogre", 6, 5)
        pc = Entity(_hero(), 5, 5, is_player=True)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.start_combat()
        from engine.ai.models import TurnPlan
        atk = ActionStep(step_type="attack", attacker=foe, target=pc,
                         action_name="Greatclub", damage=3)
        bs.pending_plan = TurnPlan(entity=foe, steps=[atk, atk])
        bs.pending_step_idx = 0
        foe.hp = 0                       # dropped by a reaction
        bs._confirm_step()
        self.assertIsNone(bs.pending_plan,
                          "a dead creature finished its turn")

    def test_a_living_actor_finishes_normally(self):
        foe = _mon("Ogre", 6, 5)
        pc = Entity(_hero(), 5, 5, is_player=True)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.start_combat()
        from engine.ai.models import TurnPlan
        atk = ActionStep(step_type="attack", attacker=foe, target=pc,
                         action_name="Greatclub", damage=3)
        bs.pending_plan = TurnPlan(entity=foe, steps=[atk, atk])
        bs.pending_step_idx = 0
        bs._confirm_step()
        self.assertIsNotNone(bs.pending_plan)
        self.assertEqual(bs.pending_step_idx, 1)

    def test_a_dying_player_may_still_finish_their_own_turn(self):
        """Pelaaja 0 HP:llä heittää kuolinheittonsa; hänen vuoronsa ei
        katkea samalla tavalla kuin hirviön."""
        pc = Entity(_hero(), 5, 5, is_player=True)
        foe = _mon("Ogre", 12, 5)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.start_combat()
        from engine.ai.models import TurnPlan
        wait = ActionStep(step_type="wait", attacker=pc,
                          description="death save")
        bs.pending_plan = TurnPlan(entity=pc, steps=[wait, wait])
        bs.pending_step_idx = 0
        pc.hp = 0
        bs._confirm_step()
        self.assertIsNotNone(bs.pending_plan)

    def test_the_state_records_which_step_actually_ran(self):
        foe = _mon("Ogre", 6, 5)
        pc = Entity(_hero(), 5, 5, is_player=True)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.start_combat()
        from engine.ai.models import TurnPlan
        atk = ActionStep(step_type="attack", attacker=foe, target=pc,
                         action_name="Greatclub", damage=3)
        bs.pending_plan = TurnPlan(entity=foe, steps=[atk])
        bs.pending_step_idx = 0
        self.assertIsNone(bs.last_executed_step)
        bs._confirm_step()
        self.assertIs(bs.last_executed_step, atk)

    def test_a_cancelled_step_is_not_recorded_as_executed(self):
        foe = _mon("Ogre", 6, 5)
        pc = Entity(_hero(), 5, 5, is_player=True)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.start_combat()
        from engine.ai.models import TurnPlan
        atk = ActionStep(step_type="attack", attacker=foe, target=pc,
                         action_name="Greatclub", damage=3)
        bs.pending_plan = TurnPlan(entity=foe, steps=[atk])
        bs.pending_step_idx = 0
        foe.hp = 0
        bs._confirm_step()
        self.assertIsNone(bs.last_executed_step)


# ===================================================================== #
# 3. DEATH SAVES STOP AT THREE
# ===================================================================== #
class TestDeathSaveTrack(unittest.TestCase):

    def test_a_natural_one_cannot_push_the_count_past_three(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        pc.hp = 0
        pc.death_save_failures = 2
        random.seed(0)
        for _ in range(60):
            pc.death_save_failures = 2
            pc.death_save_successes = 0
            pc.is_stable = False
            pc.roll_death_save()
            self.assertLessEqual(pc.death_save_failures, 3,
                                 "the failure track ran past death")
            self.assertLessEqual(pc.death_save_successes, 3)

    def test_three_failures_still_means_dead(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        pc.hp = 0
        pc.death_save_failures = 2
        random.seed(3)
        for _ in range(40):
            if pc.death_save_failures >= 3:
                break
            pc.roll_death_save()
        self.assertEqual(pc.death_save_failures, 3)
        self.assertEqual(pc.roll_death_save(), "",
                         "kept rolling after death")

    def test_a_normal_run_still_stabilises_at_three_successes(self):
        pc = Entity(_hero(), 5, 5, is_player=True)
        pc.hp = 0
        random.seed(11)
        for _ in range(60):
            if pc.is_stable or pc.death_save_failures >= 3 or pc.hp > 0:
                break
            pc.roll_death_save()
        self.assertTrue(pc.is_stable or pc.death_save_failures == 3
                        or pc.hp > 0)


# ===================================================================== #
# 4. A MELEE FIGHTER DOES NOT WALK OUT OF THE FIGHT
# ===================================================================== #
class TestNoKitingOutOfMelee(unittest.TestCase):

    def test_a_creature_in_contact_does_not_reposition_away(self):
        ai = TacticalAI()
        gob = _mon("Goblin", 6, 5)
        pcs = [Entity(_hero(), 5, 5, is_player=True),
               Entity(_hero("Beatrice"), 6, 6, is_player=True),
               Entity(_hero("Carlo"), 5, 6, is_player=True)]
        b = _battle(gob, *pcs)
        b.start_combat()
        gob.movement_left = 30
        where = (gob.grid_x, gob.grid_y)
        step = ai._try_post_attack_reposition(gob, pcs, [], b)
        self.assertIsNone(step, "walked out of melee for no reason")
        self.assertEqual((gob.grid_x, gob.grid_y), where)

    def test_disengaging_creatures_may_still_pull_back(self):
        ai = TacticalAI()
        gob = _mon("Goblin", 6, 5)
        pcs = [Entity(_hero(), 5, 5, is_player=True)]
        b = _battle(gob, *pcs)
        b.start_combat()
        gob.movement_left = 30
        gob.is_disengaging = True
        ai._try_post_attack_reposition(gob, pcs, [], b)   # must not raise

    def test_a_creature_out_of_contact_is_unaffected(self):
        ai = TacticalAI()
        gob = _mon("Goblin", 2, 2)
        pcs = [Entity(_hero(), 18, 18, is_player=True)]
        b = _battle(gob, *pcs)
        b.start_combat()
        gob.movement_left = 30
        ai._try_post_attack_reposition(gob, pcs, [], b)   # must not raise


# ===================================================================== #
# 5. A SPIRITUAL WEAPON OBEYS ITS OWN SPEED AND REACH
# ===================================================================== #
class TestSummonMovementAndReach(unittest.TestCase):

    def _scene(self, target_x):
        pc = Entity(_hero("War Cleric"), 3, 5, is_player=True)
        foe = _mon("Ogre", target_x, 5)
        b = _battle(pc, foe)
        b.start_combat()
        w = b.spawn_summon(pc, "Spiritual Weapon", 4, 5,
                           hp=20, ac=12, damage_dice="1d8")
        return b, pc, foe, w

    def test_it_never_covers_more_than_its_speed(self):
        ai = TacticalAI()
        b, pc, foe, w = self._scene(20)
        step = ai._move_summon_to_target(w, foe, b)
        if step is not None:
            self.assertLessEqual(step.movement_ft, w.get_speed() + 0.01,
                                 f"floated {step.movement_ft} ft on a "
                                 f"{w.get_speed()} ft speed")

    def test_it_still_closes_when_the_target_is_near(self):
        ai = TacticalAI()
        b, pc, foe, w = self._scene(7)
        step = ai._move_summon_to_target(w, foe, b)
        self.assertIsNotNone(step)
        self.assertLessEqual(b.get_distance(w, foe) * 5, 5.01,
                             "did not reach a target within its speed")

    def test_it_drifts_toward_a_target_it_cannot_reach(self):
        ai = TacticalAI()
        b, pc, foe, w = self._scene(24)
        before = b.get_distance(w, foe)
        ai._move_summon_to_target(w, foe, b)
        self.assertLess(b.get_distance(w, foe), before,
                        "stood still instead of closing what it could")

    def test_it_does_not_swing_at_something_out_of_reach(self):
        ai = TacticalAI()
        from engine.ai.models import TurnPlan
        b, pc, foe, w = self._scene(24)
        plan = ai._handle_summon_turn(w, b, TurnPlan(entity=w))
        for s in plan.steps:
            if s.step_type in ("attack", "bonus_attack") and s.target:
                self.assertLessEqual(
                    b.get_distance(w, s.target) * 5, 5.01,
                    "attacked from beyond its reach")

    def test_the_bonus_action_command_also_respects_reach(self):
        ai = TacticalAI()
        b, pc, foe, w = self._scene(30)
        steps = ai._decide_bonus_action(pc, [foe], [], b)
        for s in steps or []:
            if s.step_type == "bonus_attack" and s.target and s.action:
                self.assertLessEqual(
                    b.get_distance(s.attacker, s.target) * 5,
                    max(s.action.range, s.action.reach, 5) + 0.01)


# ===================================================================== #
# 6. AN ATTACK REMEMBERS WHERE IT WAS MADE FROM
# ===================================================================== #
class TestAttackRecordsItsOrigin(unittest.TestCase):

    def test_the_step_stamps_the_attackers_position(self):
        ai = TacticalAI()
        gob = _mon("Goblin", 6, 5)
        pc = Entity(_hero(), 7, 5, is_player=True)
        b = _battle(gob, pc)
        b.start_combat()
        weapon = next(a for a in gob.stats.actions
                      if not a.is_multiattack and a.damage_dice)
        step = ai._execute_attack(gob, weapon, pc, b)
        self.assertEqual((step.old_x, step.old_y), (gob.grid_x, gob.grid_y))

    def test_the_stamp_survives_the_attacker_moving_afterwards(self):
        ai = TacticalAI()
        gob = _mon("Goblin", 6, 5)
        pc = Entity(_hero(), 7, 5, is_player=True)
        b = _battle(gob, pc)
        b.start_combat()
        weapon = next(a for a in gob.stats.actions
                      if not a.is_multiattack and a.damage_dice)
        step = ai._execute_attack(gob, weapon, pc, b)
        gob.grid_x, gob.grid_y = 18.0, 18.0
        self.assertEqual((step.old_x, step.old_y), (6.0, 5.0))


# ===================================================================== #
# 7. THE CONDITION TABLE IS COMPLETE
# ===================================================================== #
class TestConditionTable(unittest.TestCase):

    NEWLY_LISTED = ["Lethargic", "Turned", "Max HP Reduced", "Cursed"]

    def test_the_four_missing_conditions_are_documented(self):
        for cond in self.NEWLY_LISTED:
            with self.subTest(condition=cond):
                self.assertIn(cond, CONDITIONS)
                self.assertGreater(len(CONDITIONS[cond]), 40,
                                   "the description has to tell the DM "
                                   "what the condition does")

    def test_every_condition_any_stat_block_applies_is_in_the_table(self):
        applied = set()
        for src in (hero_list, library.get_all_monsters()):
            for stats in src:
                for a in stats.actions:
                    if a.applies_condition:
                        applied.add(a.applies_condition)
                for f in stats.features:
                    if getattr(f, "applies_condition", ""):
                        applied.add(f.applies_condition)
        missing = sorted(applied - set(CONDITIONS))
        self.assertEqual(missing, [],
                         f"stat blocks apply conditions the table has "
                         f"never heard of: {missing}")

    def test_every_condition_any_spell_applies_is_in_the_table(self):
        import data.spells as spell_lib
        applied = {s.applies_condition for s in spell_lib._spells.values()
                   if getattr(s, "applies_condition", "")}
        missing = sorted(applied - set(CONDITIONS))
        self.assertEqual(missing, [], f"spells apply unknown conditions: "
                                      f"{missing}")

    def test_turn_undead_now_does_something(self):
        self.assertIn("Turned", CONDITION_EFFECTS)
        self.assertTrue(CONDITION_EFFECTS["Turned"].get("no_reactions"))

    def test_a_creature_can_carry_the_new_conditions(self):
        gob = _mon("Goblin", 5, 5)
        for cond in self.NEWLY_LISTED:
            gob.add_condition(cond)
            self.assertTrue(gob.has_condition(cond))
            gob.remove_condition(cond)


# ===================================================================== #
# 8. SHIFTED POSITIONAL ARGUMENTS IN STAT BLOCKS
# ===================================================================== #
class TestShiftedActionArguments(unittest.TestCase):
    """``Action("Bite", "Melee", 3, "2d8+3", "piercing")`` reads
    naturally and is wrong: the fifth positional is damage_bonus, so
    the damage TYPE landed there and damage_type kept its default. The
    deeper audit found it as a crash inside the win-probability meter,
    where ``21 + "piercing"`` raised TypeError."""

    def test_a_damage_type_in_the_bonus_slot_is_moved_where_it_belongs(self):
        from data.models import Action
        a = Action("Bite", "Melee", 3, "2d8+3", "piercing")
        self.assertEqual(a.damage_type, "piercing")
        self.assertEqual(a.damage_bonus, 0)

    def test_a_real_damage_type_is_not_overwritten(self):
        from data.models import Action
        a = Action("Bite", "Melee", 3, "2d8", "piercing", "fire")
        self.assertEqual(a.damage_type, "fire")

    def test_a_numeric_string_bonus_still_becomes_a_number(self):
        from data.models import Action
        a = Action("Club", "Melee", 3, "1d6", "2")
        self.assertEqual(a.damage_bonus, 2)

    def test_an_action_type_in_the_attack_bonus_slot_is_moved(self):
        from data.models import Action
        a = Action("Parry", "Reaction", "reaction")
        self.assertEqual(a.action_type, "reaction")
        self.assertEqual(a.attack_bonus, 0)

    def test_nonsense_never_survives_as_a_number(self):
        from data.models import Action
        a = Action("Odd", "x", "not a number", "1d4", "also not")
        self.assertEqual(a.attack_bonus, 0)
        self.assertEqual(a.damage_bonus, 0)

    def test_no_stat_block_in_the_game_has_a_non_numeric_number(self):
        bad = []
        for src in (hero_list, library.get_all_monsters()):
            for stats in src:
                actions = (list(stats.actions)
                           + list(getattr(stats, "bonus_actions", []) or [])
                           + list(getattr(stats, "reactions", []) or []))
                for a in actions:
                    for f in ("attack_bonus", "damage_bonus", "range",
                              "reach", "condition_dc", "aoe_radius",
                              "long_range", "multiattack_count"):
                        v = getattr(a, f, 0)
                        if not isinstance(v, (int, float)):
                            bad.append(f"{stats.name}/{a.name}.{f}={v!r}")
        self.assertEqual(bad, [], f"{len(bad)} fields hold text where a "
                                  f"number belongs")

    def test_the_ghoul_bites_for_piercing_again(self):
        ghoul = library.get_monster("Ghoul")
        bite = next(a for a in ghoul.actions if a.name == "Bite")
        self.assertEqual(bite.damage_type, "piercing")

    def test_the_win_probability_meter_survives_every_monster(self):
        """Se kaatui juuri tähän: 21 + 'piercing'."""
        from engine.win_probability import WinProbabilityCalculator
        pcs = [Entity(_hero(), 3, 3, is_player=True)]
        for name in ("Ghoul", "Ghast", "Vampire", "Shadow", "Beholder",
                     "Adult Red Dragon", "Mind Flayer", "Noble"):
            with self.subTest(monster=name):
                foe = _mon(name, 9, 3)
                b = _battle(*(pcs + [foe]))
                b.start_combat()
                WinProbabilityCalculator().calculate(b)   # must not raise


# ===================================================================== #
# 9. THE DEEP RUN'S FINDINGS
#
# 510 battles and 34,000 steps turned up three more.
# ===================================================================== #
class TestOpportunityAttackRewind(unittest.TestCase):
    """Kun liike provosoi vapaaiskun, moottori kelaa liikkujan takaisin
    lähtöruutuun jotta reaktio ratkeaa ennen siirtoa. Lähtöruutu voi
    olla jo varattu — ja Huge-lohikäärme keloutui papin päälle."""

    def _scene(self):
        dragon = _mon("Adult Brass Dragon", 5, 6)
        cleric = Entity(_hero("War Cleric"), 4, 6, is_player=True)
        bs = BattleState(_FM(), entities=[cleric, dragon])
        bs.battle.start_combat()
        return bs, dragon, cleric

    def test_it_does_not_rewind_onto_another_creature(self):
        from engine.ai.models import TurnPlan
        bs, dragon, cleric = self._scene()
        move = ActionStep(step_type="move", attacker=dragon,
                          old_x=4.0, old_y=6.0,          # now the cleric's
                          new_x=dragon.grid_x, new_y=dragon.grid_y,
                          movement_ft=5.0)
        bs.pending_plan = TurnPlan(entity=dragon, steps=[move])
        bs.pending_step_idx = 0
        bs._confirm_step()
        sd = dragon.size_in_squares
        fd = {(int(dragon.grid_x) + dx, int(dragon.grid_y) + dy)
              for dx in range(sd) for dy in range(sd)}
        self.assertNotIn((int(cleric.grid_x), int(cleric.grid_y)), fd,
                         "the dragon was rewound on top of the cleric")

    def test_it_still_rewinds_when_the_origin_is_free(self):
        from engine.ai.models import TurnPlan
        dragon = _mon("Adult Brass Dragon", 8, 6)
        pc = Entity(_hero(), 20, 20, is_player=True)
        bs = BattleState(_FM(), entities=[pc, dragon])
        bs.battle.start_combat()
        move = ActionStep(step_type="move", attacker=dragon,
                          old_x=5.0, old_y=6.0,
                          new_x=8.0, new_y=6.0, movement_ft=15.0)
        bs.pending_plan = TurnPlan(entity=dragon, steps=[move])
        bs.pending_step_idx = 0
        bs._confirm_step()
        # No opportunity attacks here, so the move simply stands.
        self.assertEqual((dragon.grid_x, dragon.grid_y), (8.0, 6.0))


class TestLegendaryMoveDoesNotLeak(unittest.TestCase):
    """_move_toward kävelyttää olennon suunnitellessaan. Legendaarisen
    liikkeen *pisteytys* siirsi olennon, vaikka vaihtoehtoa ei valittu
    — ja se hyökkäsi sitten ruudusta jonka oli jo jättänyt."""

    def _polsen(self):
        p = _mon("Polsen", 20, 6)
        pcs = [Entity(_hero(), 3, 5, is_player=True),
               Entity(_hero("Beatrice"), 3, 7, is_player=True)]
        b = _battle(p, *pcs)
        b.start_combat()
        p.legendary_actions_left = 3
        return b, p, pcs

    def test_scoring_a_reposition_does_not_move_the_creature(self):
        from engine.ai import TacticalAI
        from engine.special_actions import resolve_special_actions
        ai = TacticalAI()
        b, p, pcs = self._polsen()
        move_ability = next(
            (sa for sa in resolve_special_actions(p.stats, "legendary")
             if sa.intent == "move"), None)
        if move_ability is None:
            self.skipTest("Polsen has no repositioning legendary action")
        where = (p.grid_x, p.grid_y)
        ai._legendary_fallback(p, move_ability, pcs, b)
        self.assertEqual((p.grid_x, p.grid_y), where,
                         "pricing an option walked the creature")

    def test_the_chosen_reposition_does_move_it(self):
        random.seed(2)
        b, p, pcs = self._polsen()
        where = (p.grid_x, p.grid_y)
        for _ in range(3):
            step = b.ai.calculate_legendary_action(p, b)
            if step is not None and step.movement_ft:
                self.assertNotEqual((p.grid_x, p.grid_y), where,
                                    "the winning move was never applied")
                self.assertEqual((p.grid_x, p.grid_y),
                                 (step.new_x, step.new_y))
                return

    def test_a_legendary_attack_is_never_made_from_out_of_reach(self):
        random.seed(5)
        b, p, pcs = self._polsen()
        for _ in range(6):
            step = b.ai.calculate_legendary_action(p, b)
            if step is None:
                break
            if step.action is not None and step.target is not None:
                reach = max(step.action.range, step.action.reach)
                if reach and not step.action.aoe_radius:
                    ax = step.old_x if (step.old_x or step.old_y) else p.grid_x
                    ay = step.old_y if (step.old_x or step.old_y) else p.grid_y
                    d = ((ax - step.target.grid_x) ** 2
                         + (ay - step.target.grid_y) ** 2) ** 0.5 * 5
                    self.assertLessEqual(
                        d, reach + 10,
                        f"{step.action_name} ({reach} ft) swung at "
                        f"{d:.0f} ft")
            p.legendary_actions_left = 3


class TestAuditorFalsePositives(unittest.TestCase):
    """Meluava auditoija on hyödytön. Nämä kaksi olivat sen omia."""

    def test_falling_into_a_chasm_is_a_legal_place_to_be(self):
        from engine.combat_audit import AuditReport, _Watcher, ERROR
        from engine.terrain import TerrainObject
        pc = Entity(_hero(), 7, 4, is_player=True)
        b = _battle(pc)
        chasm = TerrainObject("chasm", 7, 4)
        b.terrain = [chasm]
        pc.elevation = chasm.elevation          # it fell in
        pc.add_condition("Prone")
        rep = AuditReport()
        _Watcher(rep).check_state(b, "x")
        self.assertEqual([f for f in rep.findings.values()
                          if f.severity == ERROR], [],
                         "a creature at the bottom of a pit it fell into "
                         "was reported as standing inside solid rock")

    def test_hovering_inside_a_wall_is_still_reported(self):
        from engine.combat_audit import AuditReport, _Watcher, ERROR
        from engine.terrain import TerrainObject
        pc = Entity(_hero(), 7, 4, is_player=True)
        b = _battle(pc)
        b.terrain = [TerrainObject("wall", 7, 4)]
        rep = AuditReport()
        _Watcher(rep).check_state(b, "x")
        self.assertTrue([f for f in rep.findings.values()
                         if f.severity == ERROR],
                        "standing inside a wall must still be an error")

    def test_a_rogue_may_dash_twice(self):
        """Cunning Action on TOINEN Dash samalla vuorolla: 25 jalkaa
        kävelyä plus kaksi 25 jalan Dashia on laillista."""
        from engine.combat_audit import AuditReport, _Watcher, ERROR
        rogue = Entity(_hero("Shadow Rogue"), 3, 3, is_player=True)
        self.assertTrue(rogue.has_feature("cunning_action"))
        b = _battle(rogue)
        rep = AuditReport()
        step = ActionStep(step_type="move", attacker=rogue,
                          movement_ft=rogue.get_speed() * 3)
        _Watcher(rep).check_step(b, step, "x")
        moved = [f for f in rep.findings.values()
                 if "speed" in f.title and f.severity == ERROR]
        self.assertEqual(moved, [], "a double Dash was called a cheat")

    def test_a_creature_without_cunning_action_still_cannot(self):
        from engine.combat_audit import AuditReport, _Watcher, ERROR
        ogre = _mon("Ogre", 3, 3)
        b = _battle(ogre)
        rep = AuditReport()
        step = ActionStep(step_type="move", attacker=ogre,
                          movement_ft=ogre.get_speed() * 3)
        _Watcher(rep).check_step(b, step, "x")
        self.assertTrue([f for f in rep.findings.values()
                         if "speed" in f.title and f.severity == ERROR])


# ===================================================================== #
# 10. AND THE AUDIT ITSELF AGREES
# ===================================================================== #
class TestTheAuditIsCleaner(unittest.TestCase):

    def test_a_slice_of_the_real_matrix_finds_no_rule_errors(self):
        """Ei mikrotesti vaan oikea ajo: nämä samat skenaariot tuottivat
        neljä virhelajia ennen korjauksia."""
        from engine.combat_audit import (AuditRunner, build_scenarios,
                                         ERROR)
        sc = [s for s in build_scenarios("quick")
              if s.suite in ("classes", "spells")][:14]
        rep = AuditRunner("quick", scenarios=sc).run_all()
        errors = [f for f in rep.findings.values() if f.severity == ERROR]
        self.assertEqual(
            [f"{f.category}/{f.title} x{f.count}" for f in errors], [],
            "the audit still finds rule violations in its own suites")


if __name__ == "__main__":
    unittest.main()
