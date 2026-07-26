"""Olentografiikka: jokaisella olennolla oma tunnistettava hahmo.

Aiemmin kaikki 226 hirviötä piirtyivät samana sarvipäisenä humanoidina,
joten beholder, hyytelökuutio ja muinainen lohikäärme olivat pöydässä
sama punainen pallo. Nyt jokaisella arkkityypillä on oma siluettinsa,
joka myös liikkuu vähän.

Testataan kolme asiaa:
  * luokittelu kattaa jokaisen kirjaston olennon,
  * jokainen siluetti piirtyy joka ruutukoossa kaatumatta ja animoituu,
  * siluetit eroavat toisistaan — muuten koko pointti katoaa.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.library import library
from data.heroes import hero_list
from engine.entities import Entity
from states import creature_art as ca
from states.character_art import kind_for_entity, draw_character
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


ALL_MONSTERS = library.get_all_monsters()


def _surf(size=64):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    return s


def _painted(surf, step=2):
    w, h = surf.get_size()
    return sum(1 for x in range(0, w, step) for y in range(0, h, step)
               if surf.get_at((x, y))[3] > 0)


def _signature(kind, size=64, phase=0.25):
    """Coarse occupancy grid — a shape fingerprint after the circular
    token mask, i.e. what the DM actually sees."""
    s = _surf(size)
    ca.draw_creature(s, size, size, kind=kind, color=(200, 90, 90),
                     state="idle", phase=phase)
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255),
                       (size // 2, size // 2), size // 2)
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    cells = 8
    step = size // cells
    sig = []
    for gy in range(cells):
        for gx in range(cells):
            hit = 0
            for x in range(gx * step, (gx + 1) * step, 2):
                for y in range(gy * step, (gy + 1) * step, 2):
                    if s.get_at((x, y))[3] > 40:
                        hit += 1
            sig.append(1 if hit >= 2 else 0)
    return tuple(sig)


class TestClassification(unittest.TestCase):
    def test_every_monster_in_the_library_classifies(self):
        for m in ALL_MONSTERS:
            kind = ca.kind_for_stats(m)
            self.assertTrue(ca.has_painter(kind), f"{m.name} -> {kind}")

    def test_every_silhouette_is_actually_used(self):
        used = {ca.kind_for_stats(m) for m in ALL_MONSTERS}
        unused = sorted(set(ca.kinds()) - used)
        self.assertEqual(unused, [], f"dead silhouettes: {unused}")

    def test_the_obvious_ones_land_where_a_dm_would_expect(self):
        cases = {
            "Ancient Red Dragon": "dragon",
            "Young White Dragon": "dragon",
            "Dracolich": "dragon",
            "Beholder": "beholder",
            "Death Tyrant": "beholder",
            "Gelatinous Cube": "ooze",
            "Skeleton": "skeleton",
            "Vampire": "vampire",
            "Lordi Dimerius Blackfeet": "vampire",
            "Iron Golem": "construct",
            "Whitestone Colossus": "construct",
            "Treant": "plant",
            "Swarm of Rats": "swarm",
            "Sprite": "fey",
            "Green Hag": "fey",
            "Mind Flayer": "tentacled",
            "Kraken": "tentacled",
            "Aboleth": "tentacled",
            "Solar": "celestial",
            "Unicorn": "celestial",
            "Giant Spider": "spider",
            "Balor": "devil",
            "Pit Fiend": "devil",
            "Storm Giant": "giant",
            "Troll": "giant",
            "Dire Wolf": "quadruped",
            "Fire Snake": "serpent",
            "Ghost": "ghost",
            "Zombie": "shambler",
        }
        for name, expected in cases.items():
            self.assertEqual(ca.kind_for_stats(library.get_monster(name)),
                             expected, name)

    def test_a_bone_devil_is_a_devil_not_a_skeleton(self):
        """Nimikeyword-järjestys ratkaisee: tarkempi luenta voittaa."""
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Bone Devil")), "devil")

    def test_a_vampire_spellcaster_is_still_a_vampire(self):
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Vampire Spellcaster")),
            "vampire")

    def test_an_unknown_creature_type_falls_back(self):
        from data.models import CreatureStats
        odd = CreatureStats(name="Whatsit", creature_type="Nonsense")
        self.assertEqual(ca.kind_for_stats(odd), ca.DEFAULT_KIND)

    def test_classification_survives_junk(self):
        class _Bare:
            pass
        self.assertTrue(ca.has_painter(ca.kind_for_stats(_Bare())))


class TestDrawing(unittest.TestCase):
    SIZES = (16, 24, 40, 64, 120)

    def test_every_silhouette_draws_at_every_size(self):
        for kind in ca.kinds():
            for size in self.SIZES:
                s = _surf(size)
                self.assertTrue(
                    ca.draw_creature(s, size, size, kind=kind,
                                     color=(190, 100, 90), phase=0.3),
                    f"{kind} @ {size}")

    def test_every_silhouette_paints_something_at_token_size(self):
        for kind in ca.kinds():
            for size in (24, 40, 64):
                s = _surf(size)
                ca.draw_creature(s, size, size, kind=kind,
                                 color=(190, 100, 90), phase=0.3)
                self.assertGreater(_painted(s), 8, f"{kind} @ {size}")

    def test_every_silhouette_animates(self):
        static = []
        for kind in ca.kinds():
            frames = []
            for p in (0.0, 0.25, 0.5, 0.75):
                s = _surf(64)
                ca.draw_creature(s, 64, 64, kind=kind,
                                 color=(190, 100, 90), phase=p)
                frames.append(s)
            moved = any(
                frames[0].get_at((x, y)) != frames[i].get_at((x, y))
                for i in (1, 2, 3)
                for x in range(0, 64, 2) for y in range(0, 64, 2))
            if not moved:
                static.append(kind)
        self.assertEqual(static, [], f"these never move: {static}")

    def test_the_states_change_the_pose(self):
        for kind in ca.kinds():
            base = _surf(64)
            ca.draw_creature(base, 64, 64, kind=kind, color=(190, 100, 90),
                             state="idle", phase=0.3)
            hurt = _surf(64)
            ca.draw_creature(hurt, 64, 64, kind=kind, color=(190, 100, 90),
                             state="hurt", phase=0.3)
            differs = any(base.get_at((x, y)) != hurt.get_at((x, y))
                          for x in range(0, 64, 3) for y in range(0, 64, 3))
            self.assertTrue(differs, f"{kind}: hurt looks like idle")

    def test_team_colour_reaches_the_silhouette(self):
        """Ystävä/vihollinen pitää erottua värillä."""
        for kind in ca.kinds():
            red = _surf(64)
            blue = _surf(64)
            ca.draw_creature(red, 64, 64, kind=kind, color=(220, 60, 60),
                             phase=0.3)
            ca.draw_creature(blue, 64, 64, kind=kind, color=(60, 80, 220),
                             phase=0.3)
            differs = sum(
                1 for x in range(0, 64, 2) for y in range(0, 64, 2)
                if red.get_at((x, y)) != blue.get_at((x, y)))
            self.assertGreater(differs, 5, f"{kind} ignores its colour")

    def test_degenerate_sizes_are_refused_not_crashed(self):
        self.assertFalse(ca.draw_creature(_surf(8), 0, 0, kind="dragon"))
        self.assertFalse(ca.draw_creature(None, 40, 40, kind="dragon"))

    def test_an_unknown_kind_still_draws(self):
        s = _surf(48)
        self.assertTrue(ca.draw_creature(s, 48, 48, kind="banana"))
        self.assertGreater(_painted(s), 8)

    def test_no_silhouette_can_crash_the_map(self):
        """draw_creature nielaisee virheen ja piirtää varapallon."""
        broken = dict(ca.PAINTERS)
        try:
            ca.PAINTERS["dragon"] = lambda *a, **k: 1 / 0
            s = _surf(48)
            self.assertTrue(ca.draw_creature(s, 48, 48, kind="dragon"))
            self.assertGreater(_painted(s), 8)
        finally:
            ca.PAINTERS.clear()
            ca.PAINTERS.update(broken)


class TestSilhouettesAreDistinct(unittest.TestCase):
    def test_no_two_silhouettes_share_a_shape(self):
        """Jos kaksi siluettia ovat identtisiä maskin jälkeen, pöytä ei
        erota niitä toisistaan."""
        sigs = {}
        for kind in ca.kinds():
            sig = _signature(kind)
            twin = sigs.get(sig)
            self.assertIsNone(twin, f"{kind} looks identical to {twin}")
            sigs[sig] = kind

    def test_the_headline_shapes_differ_a_lot(self):
        """Beholderin, lohikäärmeen ja limaisen pitää erottua selvästi."""
        pairs = (("dragon", "beholder"), ("beholder", "ooze"),
                 ("dragon", "ooze"), ("humanoid", "dragon"),
                 ("swarm", "giant"), ("serpent", "construct"))
        for a, b in pairs:
            sa, sb = _signature(a), _signature(b)
            diff = sum(1 for x, y in zip(sa, sb) if x != y)
            self.assertGreaterEqual(diff, 8,
                                    f"{a} and {b} differ in only {diff} cells")

    def test_every_pair_differs_by_a_few_cells_at_least(self):
        kinds = ca.kinds()
        for i, a in enumerate(kinds):
            sa = _signature(a)
            for b in kinds[i + 1:]:
                diff = sum(1 for x, y in zip(sa, _signature(b)) if x != y)
                self.assertGreaterEqual(diff, 6, f"{a} vs {b}: {diff}")


class TestWiredIntoTheTokens(unittest.TestCase):
    def test_kind_for_entity_gives_monsters_their_silhouette(self):
        for name in ("Ancient Red Dragon", "Beholder", "Gelatinous Cube",
                     "Kraken", "Iron Golem"):
            e = Entity(library.get_monster(name), 0, 0, is_player=False)
            self.assertTrue(ca.has_painter(kind_for_entity(e)), name)

    def test_players_keep_their_class_art(self):
        heroes = {h.name: h for h in hero_list}
        e = Entity(heroes["Magnus Dragonius"], 0, 0, is_player=True)
        self.assertIn(kind_for_entity(e),
                      ("warrior", "ranger", "mage", "rogue", "cleric",
                       "druid"))

    def test_wild_shape_and_summons_stay_beasts(self):
        heroes = {h.name: h for h in hero_list}
        e = Entity(heroes["Magnus Dragonius"], 0, 0, is_player=True)
        e.is_wild_shaped = True
        self.assertEqual(kind_for_entity(e), "beast")

    def test_draw_character_delegates_for_creature_kinds(self):
        s = _surf(48)
        self.assertTrue(draw_character(s, 48, 48, kind="beholder",
                                       color=(200, 90, 90), phase=0.3))
        self.assertGreater(_painted(s), 8)

    def test_every_monster_renders_through_the_token_path(self):
        for m in ALL_MONSTERS:
            e = Entity(m, 0, 0, is_player=False)
            kind = kind_for_entity(e)
            s = _surf(44)
            self.assertTrue(
                draw_character(s, 44, 44, kind=kind, color=(190, 100, 90),
                               state="idle", phase=0.4), m.name)
            self.assertGreater(_painted(s), 6, m.name)

    def test_a_battle_frame_renders_with_a_zoo_on_the_map(self):
        zoo = ["Ancient Red Dragon", "Beholder", "Gelatinous Cube",
               "Skeleton", "Iron Golem", "Treant", "Kraken", "Solar",
               "Giant Spider", "Balor", "Storm Giant", "Swarm of Rats",
               "Sprite", "Fire Snake", "Ghost", "Zombie",
               "Lordi Dimerius Blackfeet", "Dire Wolf"]
        import copy
        heroes = {h.name: h for h in hero_list}
        pcs = [Entity(copy.deepcopy(heroes["Magnus Dragonius"]), 2, 2 + i,
                      is_player=True) for i in range(2)]
        foes = [Entity(library.get_monster(n), 5 + (i % 6) * 2,
                       4 + (i // 6) * 3, is_player=False)
                for i, n in enumerate(zoo)]
        bs = BattleState(_FM(), entities=pcs + foes)
        screen = pygame.display.get_surface()
        # Several frames so the animation phases actually advance.
        for _ in range(3):
            screen.fill((0, 0, 0))
            bs.draw(screen)


if __name__ == "__main__":
    unittest.main()
