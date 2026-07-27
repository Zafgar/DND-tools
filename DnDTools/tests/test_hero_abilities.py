"""Sankarien kyvyt: löytyvätkö, voiko niitä painaa, ja tapahtuuko mitään.

Lähtötilanne oli tämä: 47 sankarin lehdillä on 149 eri kykyä. Niistä
kaksi teki jotain kun niitä klikkasi. Loput kirjasivat lokiriviin
nimensä. Ja 70 kyvyistä — Reckless Attack, Uncanny Dodge, Cunning
Action, Shield Master mukaan lukien — ei ollut edes klikattavissa:
klikkausalue rekisteröitiin vain kyvyille joilla on rajattu määrä
käyttöjä, ja kytkimillä sellaista ei ole.

Iso osa kyvyistä ei kuulukaan olla nappi. Sneak Attack ja Danger Sense
lasketaan heittojen yhteydessä automaattisesti, ja nappi niille
valehtelisi. Ne pitää tunnistaa passiivisiksi eikä jättää kuolleeksi
riviksi.
"""
import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.heroes import hero_list
from data.library import library
from data.models import Feature
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.feature_actions import (classify, activate, describe,
                                    PASSIVE, TOGGLE, USE)
from states.battle_state import BattleState

try:
    from data.novus_party import novus_party
except Exception:                                    # pragma: no cover
    novus_party = []

ALL_HEROES = list(hero_list) + list(novus_party)


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(match):
    return next(h for h in ALL_HEROES if match in h.name)


def _in_battle(stats):
    p = Entity(copy.deepcopy(stats), 3.0, 3.0, is_player=True)
    foe = Entity(library.get_monster("Ogre"), 9.0, 3.0, is_player=False)
    b = BattleSystem(lambda m: None, [p, foe])
    b.start_combat()
    return p, b


def _feat(entity, name):
    return next(f for f in entity.stats.features if f.name == name)


# ===================================================================== #
# 1. WHAT KIND OF ABILITY IS IT
# ===================================================================== #
class TestClassification(unittest.TestCase):

    def test_a_passive_is_recognised_as_passive(self):
        for mech in ("sneak_attack", "danger_sense", "evasion",
                     "great_weapon_master", "extra_attack"):
            f = Feature(f"Test {mech}", "does its thing", mechanic=mech)
            self.assertEqual(classify(f), PASSIVE, mech)

    def test_rage_and_reckless_are_toggles(self):
        for mech in ("rage", "reckless_attack"):
            f = Feature("T", "", mechanic=mech)
            self.assertEqual(classify(f), TOGGLE, mech)

    def test_a_limited_use_ability_is_a_use(self):
        f = Feature("Second Wind", "Bonus action: heal 1d10+10 HP.",
                    mechanic="second_wind", uses_per_day=1)
        self.assertEqual(classify(f), USE)

    def test_a_declared_ability_without_a_counter_is_still_a_use(self):
        f = Feature("Cunning Action", "Bonus action: Dash, Disengage, "
                                      "or Hide", mechanic="cunning_action")
        self.assertEqual(classify(f), USE)

    def test_every_ability_classifies_without_raising(self):
        for h in ALL_HEROES:
            for f in h.features or ():
                self.assertIn(classify(f), (PASSIVE, TOGGLE, USE),
                              f"{h.name}/{f.name}")

    def test_the_description_says_what_will_happen(self):
        p, b = _in_battle(_hero("Grukk"))
        for f in p.stats.features:
            text = describe(f, p)
            self.assertTrue(text.strip(), f.name)
            if classify(f) == PASSIVE:
                self.assertIn("Passiivinen", text)


# ===================================================================== #
# 2. USING THEM ACTUALLY DOES SOMETHING
# ===================================================================== #
class TestActivation(unittest.TestCase):

    def test_second_wind_heals(self):
        p, b = _in_battle(_hero("Veteran Fighter"))
        p.hp = 10
        ok, msg = activate(p, _feat(p, "Second Wind"), b)
        self.assertTrue(ok, msg)
        self.assertGreater(p.hp, 10, msg)

    def test_action_surge_gives_the_action_back(self):
        p, b = _in_battle(_hero("Veteran Fighter"))
        p.action_used = True
        ok, msg = activate(p, _feat(p, "Action Surge"), b)
        self.assertTrue(ok, msg)
        self.assertFalse(p.action_used)

    def test_rage_toggles_and_returns_the_use(self):
        p, b = _in_battle(_hero("Grukk"))
        f = _feat(p, "Rage")
        before = p.rages_left
        activate(p, f, b)
        self.assertTrue(p.rage_active)
        self.assertEqual(p.rages_left, before - 1)
        activate(p, f, b)
        self.assertFalse(p.rage_active)

    def test_reckless_attack_toggles(self):
        p, b = _in_battle(_hero("Grukk"))
        f = _feat(p, "Reckless Attack")
        activate(p, f, b)
        self.assertTrue(p.reckless_attack_active)
        activate(p, f, b)
        self.assertFalse(p.reckless_attack_active)

    def test_a_passive_is_refused_with_an_explanation(self):
        p, b = _in_battle(_hero("Grukk"))
        passives = [f for f in p.stats.features if classify(f) == PASSIVE]
        self.assertTrue(passives, "tällä sankarilla ei ole passiiveja")
        ok, msg = activate(p, passives[0], b)
        self.assertFalse(ok)
        self.assertIn("passiivinen", msg.lower())

    def test_a_spent_ability_refuses_when_it_runs_out(self):
        p, b = _in_battle(_hero("Veteran Fighter"))
        f = _feat(p, "Second Wind")
        p.hp = 5
        self.assertTrue(activate(p, f, b)[0])
        ok, msg = activate(p, f, b)
        self.assertFalse(ok)
        self.assertIn("käyttöjä", msg.lower())

    def test_a_reaction_ability_spends_the_reaction(self):
        p, b = _in_battle(_hero("Shadow Rogue"))
        f = next((x for x in p.stats.features
                  if x.name == "Uncanny Dodge"), None)
        if f is None:
            self.skipTest("this rogue has no Uncanny Dodge")
        ok, msg = activate(p, f, b)
        self.assertTrue(ok, msg)
        self.assertTrue(p.reaction_used)
        self.assertFalse(activate(p, f, b)[0])

    def test_a_temp_hp_ability_grants_temp_hp(self):
        blitz = next((h for h in ALL_HEROES if "Blitz" in h.name), None)
        if blitz is None:
            self.skipTest("Blitz Walker not in the roster")
        p, b = _in_battle(blitz)
        f = next((x for x in p.stats.features
                  if "Tireless" in x.name), None)
        if f is None:
            self.skipTest("no Tireless on this sheet")
        ok, msg = activate(p, f, b)
        self.assertTrue(ok, msg)
        self.assertGreater(p.temp_hp, 0, msg)

    def test_nothing_a_hero_owns_raises_when_used(self):
        for h in ALL_HEROES:
            p, b = _in_battle(h)
            for f in list(p.stats.features or ()):
                try:
                    activate(p, f, b)
                except Exception as ex:          # pragma: no cover
                    self.fail(f"{h.name}/{f.name}: {ex!r}")

    def test_most_usable_abilities_change_something(self):
        """Ei enää kahta 149:stä."""
        works = total = 0
        seen = set()
        for h in ALL_HEROES:
            p, b = _in_battle(h)
            for f in list(p.stats.features or ()):
                if f.name in seen or classify(f) == PASSIVE:
                    continue
                seen.add(f.name)
                total += 1
                p.hp = max(1, p.max_hp // 2)
                p.temp_hp = 0
                p.action_used = True
                p.reaction_used = False
                before = (p.hp, p.temp_hp, p.action_used, p.reaction_used,
                          p.bonus_action_used, p.rage_active,
                          p.reckless_attack_active, frozenset(p.conditions),
                          p.is_flying, p.ki_points_left,
                          p.bardic_inspiration_left,
                          p.channel_divinity_left,
                          tuple(sorted(p.feature_uses.items())))
                activate(p, f, b)
                after = (p.hp, p.temp_hp, p.action_used, p.reaction_used,
                         p.bonus_action_used, p.rage_active,
                         p.reckless_attack_active, frozenset(p.conditions),
                         p.is_flying, p.ki_points_left,
                         p.bardic_inspiration_left, p.channel_divinity_left,
                         tuple(sorted(p.feature_uses.items())))
                if before != after:
                    works += 1
        self.assertGreater(total, 40, "liian vähän käytettäviä kykyjä")
        self.assertGreaterEqual(
            works, int(total * 0.75),
            f"vain {works}/{total} käytettävää kykyä muuttaa mitään")


# ===================================================================== #
# 3. THE DM CAN REACH THEM
# ===================================================================== #
class TestTheyAreClickable(unittest.TestCase):

    def _panel_zones(self, stats):
        p = Entity(copy.deepcopy(stats), 3.0, 3.0, is_player=True)
        foe = Entity(library.get_monster("Ogre"), 9.0, 3.0, is_player=False)
        bs = BattleState(_FM(), entities=[p, foe])
        bs._do_start_combat()
        bs.selected_entity = p
        bs.draw(pygame.display.get_surface())
        hit = set()
        for _rect, cb in bs.ui_click_zones:
            for d in (getattr(cb, "__defaults__", None) or ()):
                if hasattr(d, "feature_type") and hasattr(d, "name"):
                    hit.add(d.name)
        return p, hit

    def test_every_usable_ability_has_a_clickable_row(self):
        missing = []
        for h in ALL_HEROES:
            p, hit = self._panel_zones(h)
            for f in p.stats.features or ():
                if classify(f) == PASSIVE:
                    continue
                if f.name not in hit:
                    missing.append(f"{h.name}: {f.name}")
        self.assertEqual(missing, [],
                         "näitä kykyjä ei voi klikata paneelista")

    def test_reckless_attack_is_clickable(self):
        # The specific one that was reported: a toggle with no daily
        # limit, so the old rule never gave it a click zone.
        p, hit = self._panel_zones(_hero("Grukk"))
        self.assertIn("Reckless Attack", hit)

    def test_clicking_it_through_the_panel_works(self):
        p = Entity(copy.deepcopy(_hero("Grukk")), 3.0, 3.0, is_player=True)
        foe = Entity(library.get_monster("Ogre"), 9.0, 3.0, is_player=False)
        bs = BattleState(_FM(), entities=[p, foe])
        bs._do_start_combat()
        bs.selected_entity = p
        bs.draw(pygame.display.get_surface())
        fired = None
        for _rect, cb in bs.ui_click_zones:
            for d in (getattr(cb, "__defaults__", None) or ()):
                if getattr(d, "name", "") == "Reckless Attack":
                    fired = cb
        self.assertIsNotNone(fired, "ei klikkausaluetta")
        fired()
        self.assertTrue(p.reckless_attack_active)

    def test_a_passive_row_is_not_a_dead_button(self):
        # Passives deliberately have no click zone; the row must still
        # say so rather than looking like something that failed.
        p, hit = self._panel_zones(_hero("Grukk"))
        passives = [f.name for f in p.stats.features
                    if classify(f) == PASSIVE]
        for name in passives:
            self.assertNotIn(name, hit, f"{name} pitäisi olla passiivinen")
        self.assertTrue(passives)


if __name__ == "__main__":
    unittest.main()
