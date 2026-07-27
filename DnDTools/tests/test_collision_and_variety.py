"""Olennot eivät mene päällekkäin eivätkä seinien läpi — ja uusi grafiikka.

Pelinjohtaja pyysi kahta asiaa: tärkeämpänä sen, ettei kaksi olentoa
koskaan seiso samassa ruudussa eikä kukaan livahda seinän läpi kun tila
on liian pieni, ja lisäksi lisää grafiikkaa: eri värisiä lohikäärmeitä
ja useampia erilaisia hirviöitä.

Törmäystestit ajavat oikeita taisteluita jokaisella valmiilla kartalla
ja tarkistavat JOKAISEN askeleen jälkeen, että kentän tilanne on laillinen.
Juuri niin nämä bugit löytyivät: pelkkä koodin lukeminen ei paljastanut,
että lentävä lohikäärme sivuutti kaikki tarkistukset, että kaadetun
hahmon päälle sai kävellä ja että hän nousi kuolinheiton kakkosluvulla
suoraan toisen sisään.
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

from data.library import library
from data.maps import PREMADE_MAPS, load_map_terrain, get_spawn_zones
from engine.battle import BattleSystem
from engine.entities import Entity
from engine.ai import TacticalAI
from engine.terrain import TerrainObject
from states import creature_art as ca
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _mon(name, x, y, player=False):
    return Entity(copy.deepcopy(library.get_monster(name)),
                  float(x), float(y), is_player=player)


def _battle(*entities, terrain=None):
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=list(entities))
    if terrain:
        b.terrain = list(terrain)
    return b


def _footprint(e):
    s = e.size_in_squares
    return {(int(e.grid_x) + dx, int(e.grid_y) + dy)
            for dx in range(s) for dy in range(s)}


def _violations(battle):
    """Every illegal thing on the field right now, as readable strings."""
    bad = []
    live = [e for e in battle.entities
            if e.hp > 0 and not getattr(e, "is_lair", False)]
    for i, a in enumerate(live):
        fa = _footprint(a)
        for b in live[i + 1:]:
            shared = fa & _footprint(b)
            if shared:
                bad.append(f"{a.name} and {b.name} share {sorted(shared)}")
        for (cx, cy) in fa:
            t = battle.get_terrain_at(cx, cy)
            if t is None or t.passable:
                continue
            if a.is_flying and battle.flyer_clears(a, t):
                continue
            bad.append(f"{a.name} stands in {t.terrain_type} at ({cx},{cy})")
    return bad


# ===================================================================== #
# 1. FOOTPRINTS
# ===================================================================== #
class TestFootprintPassability(unittest.TestCase):
    """``is_occupied`` only ever looked at one square, so a Huge creature
    could park with three quarters of itself inside somebody else."""

    def test_a_huge_creature_blocks_all_four_of_its_squares(self):
        dragon = _mon("Adult Red Dragon", 5, 5)
        b = _battle(dragon)
        for dx in range(3):
            for dy in range(3):
                self.assertTrue(b.is_occupied(5 + dx, 5 + dy),
                                f"({5+dx},{5+dy}) should be covered")

    def test_a_large_creature_cannot_settle_half_on_a_medium_one(self):
        goblin = _mon("Goblin", 6, 5)
        ogre = _mon("Ogre", 5, 5)
        b = _battle(goblin, ogre)
        # The ogre covers (5,5)-(6,6); (5,5) itself is free of the goblin
        # but its footprint is not.
        self.assertFalse(b.is_occupied(5, 5, exclude=ogre))
        self.assertFalse(b.is_passable(5, 5, exclude=ogre))

    def test_footprint_occupied_ignores_the_mover_itself(self):
        ogre = _mon("Ogre", 5, 5)
        b = _battle(ogre)
        self.assertFalse(b.footprint_occupied(ogre, 5, 5))

    def test_a_large_creature_cannot_squeeze_through_a_one_wide_gap(self):
        """Kapea aukko: keskikokoinen mahtuu, iso ei."""
        walls = [TerrainObject("wall", 6, y) for y in range(0, 5)]
        walls += [TerrainObject("wall", 6, y) for y in range(6, 12)]
        ogre = _mon("Ogre", 4, 5)
        goblin = _mon("Goblin", 4, 8)
        b = _battle(ogre, goblin, terrain=walls)
        self.assertTrue(b.is_passable(6, 5, exclude=goblin))
        self.assertFalse(b.is_passable(6, 5, exclude=ogre))


# ===================================================================== #
# 2. FLIGHT IS NOT PHASING
# ===================================================================== #
class TestFlyingObstacles(unittest.TestCase):
    """Lentäminen ohitti KAIKKI esteet, myös toiset olennot. Nyt lentävä
    ylittää esteen vain jos se on oikeasti sen yläpuolella."""

    def _flyer(self, x=5, y=5, elevation=0):
        d = _mon("Adult Red Dragon", x, y)
        d.is_flying = True
        d.elevation = elevation
        return d

    def test_a_flyer_below_a_wall_top_is_stopped_by_it(self):
        d = self._flyer(elevation=0)
        b = _battle(d, terrain=[TerrainObject("wall", 9, 9)])
        self.assertFalse(b.is_passable(9, 9, exclude=d))

    def test_a_flyer_above_a_wall_top_passes_over_it(self):
        d = self._flyer(elevation=20)
        b = _battle(d, terrain=[TerrainObject("wall", 9, 9)])
        self.assertTrue(b.is_passable(9, 9, exclude=d))

    def test_nothing_flies_through_a_portcullis(self):
        """Portcullis ei ilmoita korkeutta, joten se yltää kattoon."""
        d = self._flyer(elevation=60)
        b = _battle(d, terrain=[TerrainObject("portcullis", 9, 9)])
        self.assertFalse(b.is_passable(9, 9, exclude=d))

    def test_nothing_flies_out_of_a_forcecage(self):
        d = self._flyer(elevation=60)
        b = _battle(d, terrain=[TerrainObject("forcecage", 9, 9)])
        self.assertFalse(b.is_passable(9, 9, exclude=d))

    def test_a_flyer_always_crosses_a_chasm(self):
        d = self._flyer(elevation=0)
        b = _battle(d, terrain=[TerrainObject("chasm", 9, 9)])
        self.assertTrue(b.is_passable(9, 9, exclude=d))

    def test_a_flyer_never_shares_a_square_with_another_creature(self):
        """Tämä oli se bugi: lohikäärme laskeutui rautagolemin päälle."""
        golem = _mon("Iron Golem", 9, 9)
        d = self._flyer(elevation=40)
        b = _battle(d, golem)
        self.assertFalse(b.is_passable(9, 9, exclude=d))

    def test_enter_cell_allowed_no_longer_waves_flyers_through(self):
        ai = TacticalAI()
        golem = _mon("Iron Golem", 9, 9)
        d = self._flyer(elevation=40)
        b = _battle(d, golem)
        b.start_combat()
        self.assertFalse(ai._enter_cell_allowed(b, d, 9, 9))

    def test_a_flyer_does_not_open_doors_by_flying_at_them(self):
        ai = TacticalAI()
        door = TerrainObject("door", 9, 9)
        d = self._flyer(elevation=40)
        b = _battle(d, terrain=[door])
        b.start_combat()
        ai._enter_cell_allowed(b, d, 9, 9)
        self.assertFalse(door.door_open)


# ===================================================================== #
# 3. PLACEMENT REPAIR
# ===================================================================== #
class TestPlacementRepair(unittest.TestCase):

    def test_start_of_combat_untangles_overlapping_spawns(self):
        a = _mon("Ogre", 5, 5)
        c = _mon("Goblin", 5, 5)
        d = _mon("Goblin", 6, 6)
        b = _battle(a, c, d)
        b.start_combat()
        self.assertEqual(_violations(b), [])

    def test_the_biggest_creature_keeps_its_ground_at_setup(self):
        """resolve_overlaps käsittelee isoimman ensin, koska sille löytyy
        vähiten laillisia ruutuja."""
        dragon = _mon("Adult Red Dragon", 5, 5)
        goblin = _mon("Goblin", 6, 6)
        b = _battle(dragon, goblin)
        b.start_combat()
        self.assertEqual(_violations(b), [])

    def test_separate_overlapping_moves_the_smaller_creature(self):
        """Kääpiö kaivautuu esiin lohikäärmeen alta, ei toisin päin."""
        dragon = _mon("Adult Red Dragon", 5, 5)
        goblin = _mon("Goblin", 6, 6)
        b = _battle(dragon)
        b.entities.append(goblin)      # sneak it in past start_combat
        moved = b.separate_overlapping()
        self.assertEqual(moved, 1)
        self.assertEqual((int(dragon.grid_x), int(dragon.grid_y)), (5, 5))
        self.assertEqual(_violations(b), [])

    def test_a_revived_creature_does_not_stand_up_inside_its_killer(self):
        """Kaadetun päältä sai kävellä; kun hän heitti kuolinheitosta 20,
        hän nousi suoraan päällä seisovan sisään."""
        dragon = _mon("Adult Red Dragon", 5, 5)
        victim = _mon("Goblin", 20, 20, player=True)
        b = _battle(dragon, victim)
        b.start_combat()
        victim.hp = 0
        victim.grid_x, victim.grid_y = 6.0, 6.0   # dragon walked over it
        victim.hp = 1                              # nat 20 on the save
        b.separate_overlapping()
        self.assertEqual(_violations(b), [])

    def test_a_creature_sealed_in_a_forcecage_is_left_where_it_is(self):
        """separate_overlapping ei saa teleportata ketään ulos häkistä."""
        goblin = _mon("Goblin", 5, 5)
        b = _battle(goblin, terrain=[TerrainObject("forcecage", 5, 5)])
        b.separate_overlapping()
        self.assertEqual((int(goblin.grid_x), int(goblin.grid_y)), (5, 5))

    def test_find_free_cell_returns_the_square_itself_when_it_is_free(self):
        goblin = _mon("Goblin", 5, 5)
        b = _battle(goblin)
        self.assertEqual(b.find_free_cell(goblin, 5, 5), (5, 5))

    def test_a_summon_never_lands_on_top_of_anybody(self):
        """Kutsuttu olento ilmestyi ennen suoraan pyydettyyn ruutuun,
        vaikka siinä seisoi joku."""
        caster = _mon("Archmage", 9, 9, player=True)
        blocker = _mon("Ogre", 5, 5)
        b = _battle(caster, blocker)
        b.start_combat()
        summon = b.spawn_summon(caster, "Spiritual Weapon", 5, 5,
                                hp=20, ac=12, damage_dice="1d8")
        self.assertIsNotNone(summon)
        self.assertEqual(_violations(b), [])


# ===================================================================== #
# 4. LIVE BATTLES ON EVERY PREMADE MAP
# ===================================================================== #
FOES = ["Adult Red Dragon", "Iron Golem", "Troll", "Giant Spider"]
ALLIES = ["Gelatinous Cube", "Treant", "Ogre", "Dire Wolf"]


class TestNoOverlapDuringRealBattles(unittest.TestCase):
    """Sekakokoinen porukka jokaisella valmiilla kartalla. Tarkistus
    tehdään joka askeleen jälkeen, ei vasta lopussa — päällekkäisyys
    korjaantui usein itsestään seuraavalla vuorolla ja jäi huomaamatta."""

    def _build(self, map_key, seed):
        random.seed(seed)
        pz = get_spawn_zones(map_key)
        ents = []
        for i, nm in enumerate(ALLIES[:len(pz["players"])]):
            ents.append(_mon(nm, *pz["players"][i], player=True))
        for i, nm in enumerate(FOES[:len(pz["enemies"])]):
            ents.append(_mon(nm, *pz["enemies"][i]))
        bs = BattleState(_FM(), entities=ents)
        bs.battle.terrain = load_map_terrain(map_key)
        bs._set_ai_mode("full_auto")
        return bs

    def _run(self, map_key, seed, max_steps=400):
        bs = self._build(map_key, seed)
        self.assertEqual(_violations(bs.battle), [],
                         f"{map_key}: illegal setup")
        for step in range(max_steps):
            bs._process_auto_battle()
            bad = _violations(bs.battle)
            self.assertEqual(bad, [],
                             f"{map_key} seed {seed} step {step}: {bad}")
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break

    def test_every_premade_map_stays_legal(self):
        for key in PREMADE_MAPS:
            with self.subTest(map=key):
                self._run(key, 7)


# ===================================================================== #
# 5. NEW SILHOUETTES
# ===================================================================== #
NEW_KINDS = ["goblinoid", "armored", "caster", "bird", "bat", "aquatic",
             "hydra", "centaur", "lycanthrope", "crustacean", "dinosaur"]


def _paint(kind, size=64, phase=0.25, color=(190, 100, 90)):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    ca.draw_creature(s, size, size, kind=kind, color=color, phase=phase)
    return s


def _signature(surf, cells=6):
    """Coarse ink-coverage grid — a shape's fingerprint."""
    w, h = surf.get_size()
    sig = []
    for gy in range(cells):
        for gx in range(cells):
            ink = 0
            for y in range(gy * h // cells, (gy + 1) * h // cells, 2):
                for x in range(gx * w // cells, (gx + 1) * w // cells, 2):
                    if surf.get_at((x, y))[3] > 40:
                        ink += 1
            sig.append(1 if ink > 2 else 0)
    return sig


class TestNewSilhouettes(unittest.TestCase):

    def test_every_new_kind_has_a_painter(self):
        for k in NEW_KINDS:
            self.assertTrue(ca.has_painter(k), k)

    def test_the_library_grew_by_eleven_shapes(self):
        self.assertEqual(len(ca.kinds()), 31)

    def test_each_new_kind_draws_at_every_token_size(self):
        for k in NEW_KINDS:
            for size in (16, 24, 32, 48, 64, 96, 128):
                with self.subTest(kind=k, size=size):
                    s = _paint(k, size)
                    self.assertTrue(any(s.get_at((x, y))[3] > 0
                                        for y in range(0, size, 3)
                                        for x in range(0, size, 3)),
                                    f"{k} drew nothing at {size}px")

    def test_each_new_kind_animates(self):
        """0.0 ja 0.5 eivät kelpaa: sin(0) ja sin(pi) ovat molemmat 0,
        joten moni piirtäjä on niissä täsmälleen samassa asennossa."""
        for k in NEW_KINDS:
            with self.subTest(kind=k):
                a = hash(pygame.image.tostring(_paint(k, 64, 0.10), "RGBA"))
                b = hash(pygame.image.tostring(_paint(k, 64, 0.35), "RGBA"))
                self.assertNotEqual(a, b, f"{k} is frozen")

    def test_no_new_shape_collapses_into_a_generic_one(self):
        """Uusi siluetti on turha jos se näyttää samalta kuin se
        yleishahmo, jota se korvaa."""
        generic = {g: _signature(_paint(g, 96))
                   for g in ("humanoid", "quadruped")}
        for k in NEW_KINDS:
            sig = _signature(_paint(k, 96))
            for name, other in generic.items():
                diff = sum(1 for x, y in zip(sig, other) if x != y)
                with self.subTest(kind=k, generic=name):
                    self.assertGreaterEqual(
                        diff, 4, f"{k} looks like a plain {name}")

    def test_a_bad_kind_still_draws_something(self):
        s = _paint("no-such-creature", 48)
        self.assertTrue(any(s.get_at((x, y))[3] > 0
                            for y in range(0, 48, 3)
                            for x in range(0, 48, 3)))


# ===================================================================== #
# 6. CLASSIFICATION
# ===================================================================== #
class TestClassification(unittest.TestCase):

    EXPECTED = {
        "Giant Eagle": "bird", "Roc": "bird", "Harpy": "bird",
        "Giant Bat": "bat",
        "Hunter Shark": "aquatic", "Sahuagin": "aquatic",
        "Merrow": "aquatic",
        "Giant Crab": "crustacean", "Chuul": "crustacean",
        "Centaur": "centaur",
        "Tyrannosaurus Rex": "dinosaur", "Velociraptor": "dinosaur",
        "Wererat": "lycanthrope", "Weretiger": "lycanthrope",
        "Werewolf": "lycanthrope",
        "Goblin": "goblinoid", "Kobold": "goblinoid",
        "Bugbear": "goblinoid", "Hobgoblin Captain": "goblinoid",
        "Xvart": "goblinoid",
        "Knight": "armored", "Gladiator": "armored", "Guard": "armored",
        "Priest": "caster", "Necromancer": "caster", "Archmage": "caster",
        "Cultist": "caster",
        "Hydra": "hydra",
    }

    def test_each_new_monster_gets_its_own_shape(self):
        for name, kind in self.EXPECTED.items():
            with self.subTest(monster=name):
                self.assertEqual(
                    ca.kind_for_stats(library.get_monster(name)), kind)

    def test_bugbear_is_not_mistaken_for_a_bear(self):
        """'bear' on 'bugbear':n sisällä — sääntöjärjestys ratkaisee."""
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Bugbear")), "goblinoid")
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Brown Bear")),
            "quadruped")

    def test_short_names_do_not_match_inside_longer_ones(self):
        """'roc' on 'Crocodile':n sisällä, 'owl' on 'Owlbear':n, 'hai'
        on 'Chain Devil':n. Nämä hoidetaan tarkalla nimellä."""
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Owlbear")), "quadruped")
        self.assertEqual(
            ca.kind_for_stats(library.get_monster("Chain Devil")), "devil")

    def test_the_vigil_vampire_priests_read_as_vampires(self):
        for name in ("Sanguis Custos", "Custos Nocturnus",
                     "Magister Sanguinis Vhaltor", "Medicus Sanguinis"):
            with self.subTest(monster=name):
                self.assertEqual(
                    ca.kind_for_stats(library.get_monster(name)), "vampire")

    def test_every_monster_in_the_library_classifies(self):
        for m in library.get_all_monsters():
            self.assertTrue(ca.has_painter(ca.kind_for_stats(m)), m.name)


# ===================================================================== #
# 7. SPECIES COLOUR
# ===================================================================== #
class TestSpeciesColour(unittest.TestCase):
    """Kaikki lohikäärmeet olivat samaa ruskeaa. Nyt punainen on punainen
    ja valkoinen on valkoinen."""

    def test_every_chromatic_and_metallic_dragon_has_its_own_colour(self):
        seen = {}
        for hue in ("Red", "Blue", "Green", "Black", "White", "Brass",
                    "Bronze", "Copper", "Silver"):
            stats = library.get_monster(f"Adult {hue} Dragon")
            col = ca.species_color(stats)
            self.assertNotIn(col, seen,
                             f"{hue} shares a colour with {seen.get(col)}")
            seen[col] = hue

    def test_age_does_not_change_the_colour(self):
        for hue in ("Red", "White", "Green"):
            adult = ca.species_color(library.get_monster(f"Adult {hue} Dragon"))
            old = ca.species_color(
                library.get_monster(f"Ancient {hue} Dragon"))
            self.assertEqual(adult, old, hue)

    def test_the_longest_match_wins(self):
        class _S:
            name = "Ancient Shadow Dragon"
        self.assertEqual(ca.species_color(_S()),
                         ca._SPECIES_COLORS["shadow dragon"])

    def test_an_unknown_creature_keeps_the_fallback(self):
        class _S:
            name = "Nameless Horror of Cunae"
        self.assertEqual(ca.species_color(_S(), (1, 2, 3)), (1, 2, 3))

    def test_a_blank_name_keeps_the_fallback(self):
        class _S:
            name = ""
        self.assertEqual(ca.species_color(_S(), (9, 8, 7)), (9, 8, 7))

    def test_the_golems_are_told_apart_by_their_material(self):
        iron = ca.species_color(library.get_monster("Iron Golem"))
        stone = ca.species_color(library.get_monster("Stone Golem"))
        clay = ca.species_color(library.get_monster("Clay Golem"))
        self.assertEqual(len({iron, stone, clay}), 3)

    def test_a_species_colour_is_a_plain_rgb_triple(self):
        for m in library.get_all_monsters():
            col = ca.species_color(m)
            self.assertEqual(len(col), 3, m.name)
            for channel in col:
                self.assertTrue(0 <= channel <= 255, m.name)


# ===================================================================== #
# 8. THE NEW STAT BLOCKS
# ===================================================================== #
class TestBestiaryExtra(unittest.TestCase):

    NEW = ["Giant Eagle", "Roc", "Harpy", "Giant Bat", "Hunter Shark",
           "Sahuagin", "Merrow", "Giant Crab", "Chuul", "Centaur",
           "Tyrannosaurus Rex", "Velociraptor", "Wererat", "Weretiger",
           "Hobgoblin Captain", "Xvart", "Knight", "Gladiator", "Priest",
           "Necromancer"]

    def test_all_of_them_load(self):
        for name in self.NEW:
            with self.subTest(monster=name):
                self.assertIsNotNone(library.get_monster(name))

    def test_each_one_can_actually_fight(self):
        for name in self.NEW:
            with self.subTest(monster=name):
                m = library.get_monster(name)
                self.assertGreater(m.hit_points, 0)
                self.assertGreater(m.armor_class, 0)
                self.assertTrue(m.actions, f"{name} has no actions")

    def test_multiattack_names_point_at_real_actions(self):
        for name in self.NEW:
            m = library.get_monster(name)
            have = {a.name for a in m.actions}
            for a in m.actions:
                if not a.is_multiattack:
                    continue
                for target in a.multiattack_targets:
                    self.assertIn(target, have,
                                  f"{name}: Multiattack names '{target}' "
                                  f"but no such action exists")

    def test_the_casters_have_slots_and_a_save_dc(self):
        for name in ("Priest", "Necromancer"):
            m = library.get_monster(name)
            self.assertTrue(m.spell_slots, name)
            self.assertGreater(m.spell_save_dc, 0, name)
            self.assertTrue(m.spells_known, name)

    def test_they_survive_a_round_of_combat(self):
        random.seed(3)
        for name in self.NEW:
            with self.subTest(monster=name):
                foe = _mon(name, 5, 5)
                hero = _mon("Knight", 7, 5, player=True)
                b = _battle(foe, hero)
                b.start_combat()
                for _ in range(6):
                    b.compute_ai_turn(b.get_current_entity())
                    b.next_turn()


if __name__ == "__main__":
    unittest.main()
