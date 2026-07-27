"""Aurelian kruunu — the grand city map, and the city assets it needs.

The pelinjohtaja asked for one enormous human city with room for a
dragon to walk down the street, built properly rather than sketched.
The single design rule that everything else follows from is that a
Huge creature covers 3x3 squares and a Gargantuan one 4x4, so a street
that looks generous on paper can still be impassable to the boss.

These tests measure the built map instead of trusting the layout
comments: they walk a dragon's footprint through every district, count
the open squares across each avenue, and check that every spawn point
can actually hold the creature that starts on it. Each of the following
was a real defect this file caught while the map was being built:

  * the market stalls were spaced four apart, leaving two-square aisles
    that fenced the whole square off from anything Huge,
  * three wells and a forge down the middle of a five-wide artisan lane
    pinched it below three squares and sealed that quarter too,
  * the castle's wall walk ringed the courtyard, so entering by the
    gate meant climbing a 20 ft battlement and falling off it,
  * a single lamppost stood in front of the five-wide castle gate,
    which is enough to stop a 3x3 creature lining up on it,
  * and a Huge creature could not open a multi-square gate at all: the
    engine opened the one leaf under its anchor square and the
    footprint check then failed on the four still shut.
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
from data.heroes import hero_list
from data.maps import PREMADE_MAPS, load_map_terrain, get_spawn_zones
from data import maps_city
from data.maps_city import CITY_W, CITY_H, AVENUE_NS, AVENUE_EW
from engine.battle import BattleSystem
from engine.entities import Entity
from engine.ai import TacticalAI
from engine.terrain import TERRAIN_TYPES, TerrainObject
from states import terrain_art
from states.battle_state import BattleState

KEY = "grand_city"

CITY_ASSETS = ["cobblestone", "well", "fountain", "market_stall", "cart",
               "haystack", "fence", "hedge", "lamppost", "signpost",
               "gate", "battlement", "tower", "forge", "crops",
               "barricade", "dock"]


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


def _battle(*entities):
    b = BattleSystem(log_callback=lambda s: None,
                     initial_entities=list(entities))
    b.terrain = load_map_terrain(KEY)
    return b


def _reachable_with(entity_name, start, battle=None):
    """Every square ``entity_name`` can stand on, walking from ``start``."""
    probe = _mon(entity_name, *start)
    b = battle or _battle(probe)
    if probe not in b.entities:
        b.entities.append(probe)
    seen = {start}
    stack = [start]
    while stack:
        cx, cy = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cx + dx, cy + dy)
            if nxt in seen:
                continue
            if not (0 <= nxt[0] < CITY_W and 0 <= nxt[1] < CITY_H):
                continue
            if not b.is_passable(nxt[0], nxt[1], exclude=probe):
                continue
            seen.add(nxt)
            stack.append(nxt)
    return seen


# ===================================================================== #
# 1. THE MAP EXISTS AND IS ACTUALLY BIG
# ===================================================================== #
class TestTheCityIsBig(unittest.TestCase):

    def test_it_is_registered_as_a_premade_map(self):
        self.assertIn(KEY, PREMADE_MAPS)
        self.assertTrue(PREMADE_MAPS[KEY]["name"])
        self.assertTrue(PREMADE_MAPS[KEY]["description"])

    def test_it_dwarfs_every_other_map(self):
        terr = load_map_terrain(KEY)
        others = [len(v["terrain"]) for k, v in PREMADE_MAPS.items()
                  if k != KEY]
        self.assertGreater(len(terr), 3 * max(others))

    def test_it_covers_the_declared_extent(self):
        terr = load_map_terrain(KEY)
        xs = [t.grid_x for t in terr]
        ys = [t.grid_y for t in terr]
        self.assertEqual((min(xs), max(xs)), (0, CITY_W - 1))
        self.assertEqual((min(ys), max(ys)), (0, CITY_H - 1))

    def test_no_square_holds_two_tiles(self):
        """The builder merges overlapping features; a doubled square
        would mean get_terrain_at returns whichever came first."""
        terr = load_map_terrain(KEY)
        seen = set()
        for t in terr:
            key = (t.grid_x, t.grid_y)
            self.assertNotIn(key, seen, f"two tiles on {key}")
            seen.add(key)

    def test_it_is_walled_all_the_way_round(self):
        terr = {(t.grid_x, t.grid_y): t for t in load_map_terrain(KEY)}
        for x in range(CITY_W):
            for y in (0, CITY_H - 1):
                self.assertIn((x, y), terr, f"gap in the wall at ({x},{y})")
        for y in range(CITY_H):
            for x in (0, CITY_W - 1):
                self.assertIn((x, y), terr, f"gap in the wall at ({x},{y})")

    def test_every_district_is_present(self):
        kinds = {t.terrain_type for t in load_map_terrain(KEY)}
        for expected in ("tower", "battlement", "gate", "throne", "altar",
                         "market_stall", "fountain", "well", "forge",
                         "dock", "water", "bridge", "house", "cobblestone"):
            self.assertIn(expected, kinds, f"no {expected} in the city")


# ===================================================================== #
# 2. A DRAGON CAN WALK DOWN THE STREET
# ===================================================================== #
class TestDragonSizedStreets(unittest.TestCase):

    def _open(self, grid, x, y):
        t = grid.get((x, y))
        return t is None or t.passable

    def test_both_grand_avenues_are_at_least_four_squares_wide(self):
        """Four squares is 20 ft — the width of a Gargantuan creature."""
        grid = {(t.grid_x, t.grid_y): t for t in load_map_terrain(KEY)}

        def run_h(y, x0, x1):
            best = run = 0
            for x in range(x0, x1 + 1):
                run = run + 1 if self._open(grid, x, y) else 0
                best = max(best, run)
            return best

        def run_v(x, y0, y1):
            best = run = 0
            for y in range(y0, y1 + 1):
                run = run + 1 if self._open(grid, x, y) else 0
                best = max(best, run)
            return best

        for y in range(2, CITY_H - 2):
            w = run_h(y, AVENUE_NS[0] - 2, AVENUE_NS[1] + 2)
            self.assertGreaterEqual(
                w, 4, f"north-south avenue is only {w} wide at y={y}")
        for x in range(2, CITY_W - 2):
            w = run_v(x, AVENUE_EW[0] - 2, AVENUE_EW[1] + 2)
            self.assertGreaterEqual(
                w, 4, f"east-west avenue is only {w} wide at x={x}")

    def test_a_huge_creature_reaches_every_district(self):
        reach = _reachable_with("Adult Red Dragon", (28, 40))
        landmarks = {
            "avenue crossing": (28, 20),
            "temple forecourt": (40, 14),
            "market square": (42, 31),
            "artisan lane": (12, 32),
            "canal wharf": (51, 30),
        }
        for name, (lx, ly) in landmarks.items():
            near = any((lx + dx, ly + dy) in reach
                       for dx in range(-2, 3) for dy in range(-2, 3))
            self.assertTrue(near, f"a dragon cannot reach the {name}")

    def test_a_gargantuan_creature_can_cross_the_city(self):
        """Kraken is Gargantuan — 4x4. If it can walk the avenues,
        nothing larger exists in the library to worry about."""
        reach = _reachable_with("Kraken", (27, 39))
        self.assertGreater(len(reach), 200)
        # The far end of both avenues
        self.assertTrue(any((x, 20) in reach for x in range(3, 8)),
                        "cannot reach the west end of the avenue")
        self.assertTrue(any((x, 20) in reach for x in range(52, 57)),
                        "cannot reach the east end of the avenue")
        self.assertTrue(any((28, y) in reach for y in range(2, 6)),
                        "cannot reach the north end of the avenue")

    def test_the_castle_is_shut_until_somebody_opens_the_gate(self):
        reach = _reachable_with("Adult Red Dragon", (28, 40))
        self.assertNotIn((12, 12), reach,
                         "the castle gate is standing open")

    def test_a_huge_creature_can_open_and_pass_the_five_wide_gate(self):
        """The bug this covers: only the leaf under the anchor square
        opened, so the footprint check failed on the other four."""
        ai = TacticalAI()
        dragon = _mon("Adult Red Dragon", 12, 18)
        b = _battle(dragon)
        b.start_combat()
        gate_row = [b.get_terrain_at(x, 16) for x in range(10, 15)]
        self.assertTrue(all(g.is_door for g in gate_row))
        self.assertFalse(any(g.door_open for g in gate_row))

        self.assertTrue(ai._enter_cell_allowed(b, dragon, 12, 16))
        opened = [g.door_open for g in gate_row]
        self.assertEqual(sum(opened), dragon.size_in_squares,
                         "should open exactly the leaves under its body")
        # ...and now the courtyard is reachable. Counted rather than
        # spot-checked: a single hand-picked square keeps landing on
        # the well or the cart parked against the wall.
        reach = _reachable_with("Adult Red Dragon", (12, 14), battle=b)
        yard = [p for p in reach if 3 <= p[0] <= 21 and 3 <= p[1] <= 15]
        self.assertGreater(len(yard), 25,
                           "the castle courtyard is still walled off "
                           "from anything Huge")
        self.assertTrue(any(p[1] <= 12 for p in yard),
                        "cannot get up alongside the keep")

    def test_the_pathfinder_finds_real_routes_across_the_city(self):
        ai = TacticalAI()
        for start, end in (((28, 40), (28, 4)),
                           ((28, 40), (44, 30)),
                           ((5, 20), (52, 20))):
            with self.subTest(route=(start, end)):
                dragon = _mon("Adult Red Dragon", *start)
                b = _battle(dragon)
                b.start_combat()
                path = ai._find_path(start, end, b, dragon,
                                     return_partial=False)
                self.assertTrue(path, f"no route {start} -> {end}")

    def test_the_astar_budget_scales_with_the_map(self):
        """600 nodes was sized for a 20x15 room and cannot cross this."""
        ai = TacticalAI()
        small = BattleSystem(log_callback=lambda s: None)
        small.terrain = load_map_terrain("tavern_brawl")
        big = _battle()
        self.assertGreater(ai._path_budget(big), 5 * ai._path_budget(small))
        self.assertGreaterEqual(ai._path_budget(small), 600)


# ===================================================================== #
# 3. SPAWN POINTS
# ===================================================================== #
class TestSpawnPoints(unittest.TestCase):

    def test_every_spawn_holds_a_huge_creature(self):
        pz = get_spawn_zones(KEY)
        self.assertGreaterEqual(len(pz["players"]), 4)
        self.assertGreaterEqual(len(pz["enemies"]), 4)
        for side in ("players", "enemies"):
            for (sx, sy) in pz[side]:
                for name in ("Commoner", "Ogre", "Adult Red Dragon"):
                    with self.subTest(side=side, at=(sx, sy), mon=name):
                        e = _mon(name, sx, sy)
                        b = _battle(e)
                        self.assertTrue(
                            b.is_passable(sx, sy, exclude=e),
                            f"{name} does not fit on {side} spawn "
                            f"({sx},{sy})")

    def test_the_two_sides_start_apart(self):
        pz = get_spawn_zones(KEY)
        for p in pz["players"]:
            for e in pz["enemies"]:
                d = ((p[0] - e[0]) ** 2 + (p[1] - e[1]) ** 2) ** 0.5
                self.assertGreater(d, 8, f"{p} and {e} start on top "
                                         f"of each other")

    def test_a_full_party_and_warband_deploy_without_overlapping(self):
        pz = get_spawn_zones(KEY)
        ents = [_mon("Ogre", *pz["players"][i], player=True)
                for i in range(4)]
        ents += [_mon("Adult Red Dragon", *pz["enemies"][0]),
                 _mon("Knight", *pz["enemies"][1]),
                 _mon("Gladiator", *pz["enemies"][2])]
        b = _battle(*ents)
        b.start_combat()
        for i, a in enumerate(b.entities):
            sa = a.size_in_squares
            fa = {(int(a.grid_x) + dx, int(a.grid_y) + dy)
                  for dx in range(sa) for dy in range(sa)}
            for c in b.entities[i + 1:]:
                sc = c.size_in_squares
                fc = {(int(c.grid_x) + dx, int(c.grid_y) + dy)
                      for dx in range(sc) for dy in range(sc)}
                self.assertFalse(fa & fc, f"{a.name} overlaps {c.name}")
            for (cx, cy) in fa:
                t = b.get_terrain_at(cx, cy)
                self.assertTrue(t is None or t.passable,
                                f"{a.name} deployed inside {t.terrain_type}")


# ===================================================================== #
# 4. A REAL FIGHT IN THE STREETS
# ===================================================================== #
class TestBattleInTheCity(unittest.TestCase):

    def test_a_dragon_fight_runs_to_a_finish_without_illegal_positions(self):
        random.seed(8)
        pz = get_spawn_zones(KEY)
        party = [Entity(_hero(n), *pz["players"][i], is_player=True)
                 for i, n in enumerate(
                     ["Magnus Dragonius", "Beatrice", "Carlo"])]
        foes = [_mon("Adult Red Dragon", *pz["enemies"][0]),
                _mon("Knight", *pz["enemies"][1]),
                _mon("Gladiator", *pz["enemies"][2])]
        bs = BattleState(_FM(), entities=party + foes)
        bs.battle.terrain = load_map_terrain(KEY)
        bs._set_ai_mode("full_auto")

        for step in range(900):
            bs._process_auto_battle()
            live = [e for e in bs.battle.entities
                    if e.hp > 0 and not e.is_lair]
            for i, a in enumerate(live):
                sa = a.size_in_squares
                fa = {(int(a.grid_x) + dx, int(a.grid_y) + dy)
                      for dx in range(sa) for dy in range(sa)}
                for c in live[i + 1:]:
                    sc = c.size_in_squares
                    fc = {(int(c.grid_x) + dx, int(c.grid_y) + dy)
                          for dx in range(sc) for dy in range(sc)}
                    self.assertFalse(
                        fa & fc,
                        f"step {step}: {a.name} overlaps {c.name}")
                for (cx, cy) in fa:
                    t = bs.battle.get_terrain_at(cx, cy)
                    if t is None or t.passable:
                        continue
                    if a.is_flying and bs.battle.flyer_clears(a, t):
                        continue
                    self.fail(f"step {step}: {a.name} stands in "
                              f"{t.terrain_type} at ({cx},{cy})")
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        else:
            self.fail("the fight never ended")

    def test_the_map_renders(self):
        screen = pygame.display.get_surface()
        pz = get_spawn_zones(KEY)
        bs = BattleState(_FM(), entities=[
            Entity(_hero(), *pz["players"][0], is_player=True),
            _mon("Adult Red Dragon", *pz["enemies"][0])])
        bs.battle.terrain = load_map_terrain(KEY)
        screen.fill((0, 0, 0))
        bs.draw(screen)          # must not raise on 2000+ tiles

    def test_offscreen_tiles_are_culled(self):
        """Without culling every one of ~2000 tiles allocates a surface
        and runs a procedural painter on every single frame."""
        import inspect
        from states import battle_renderer
        src = inspect.getsource(battle_renderer.BattleRendererMixin
                                ._draw_terrain)
        self.assertIn("colliderect", src)
        self.assertIn("continue", src)


# ===================================================================== #
# 5. THE NEW CITY ASSETS
# ===================================================================== #
class TestCityAssets(unittest.TestCase):

    def test_each_one_is_a_real_terrain_type(self):
        for k in CITY_ASSETS:
            self.assertIn(k, TERRAIN_TYPES, k)
            self.assertTrue(TERRAIN_TYPES[k].get("label"), k)
            self.assertTrue(TERRAIN_TYPES[k].get("description"), k)

    def test_each_one_has_a_painter_that_survives_every_tile_size(self):
        for k in CITY_ASSETS:
            self.assertTrue(terrain_art.has_painter(k), f"{k} has no art")
            for size in (10, 16, 24, 40, 60, 96):
                with self.subTest(asset=k, size=size):
                    s = pygame.Surface((size, size), pygame.SRCALPHA)
                    terrain_art.decorate_tile(s, k, size, size,
                                              TERRAIN_TYPES[k]["color"])

    def test_every_terrain_type_in_the_game_now_has_art(self):
        missing = [k for k in TERRAIN_TYPES
                   if not terrain_art.has_painter(k)]
        self.assertEqual(missing, [])

    def test_each_one_actually_draws_something(self):
        for k in CITY_ASSETS:
            with self.subTest(asset=k):
                s = pygame.Surface((48, 48), pygame.SRCALPHA)
                s.fill((0, 0, 0, 0))
                terrain_art.decorate_tile(s, k, 48, 48,
                                          TERRAIN_TYPES[k]["color"])
                painted = sum(1 for y in range(0, 48, 3)
                              for x in range(0, 48, 3)
                              if s.get_at((x, y))[3] > 0)
                self.assertGreater(painted, 20, f"{k} drew almost nothing")

    def test_the_house_no_longer_shares_the_brick_wall_art(self):
        """A block of houses painted with the wall texture read as one
        flat slab of masonry instead of a row of roofs."""
        a = pygame.Surface((48, 48), pygame.SRCALPHA)
        b = pygame.Surface((48, 48), pygame.SRCALPHA)
        terrain_art.decorate_tile(a, "house", 48, 48,
                                  TERRAIN_TYPES["house"]["color"])
        terrain_art.decorate_tile(b, "wall", 48, 48,
                                  TERRAIN_TYPES["house"]["color"])
        self.assertNotEqual(pygame.image.tostring(a, "RGBA"),
                            pygame.image.tostring(b, "RGBA"))

    def test_the_gate_behaves_like_a_door(self):
        g = TerrainObject("gate", 5, 5)
        self.assertTrue(g.is_door)
        self.assertFalse(g.passable)
        self.assertFalse(g.is_locked)
        g.door_open = True
        self.assertTrue(g.passable)

    def test_the_battlement_is_a_walkway_twenty_feet_up(self):
        b = TerrainObject("battlement", 5, 5)
        self.assertTrue(b.passable)
        self.assertEqual(b.elevation, 20)
        self.assertEqual(b.cover_bonus, 5)

    def test_a_tower_stops_even_a_high_flyer(self):
        tower = TerrainObject("tower", 5, 5)
        dragon = _mon("Adult Red Dragon", 1, 1)
        dragon.is_flying = True
        dragon.elevation = 30
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[dragon])
        b.terrain = [tower]
        self.assertFalse(b.flyer_clears(dragon, tower))
        dragon.elevation = 45
        self.assertTrue(b.flyer_clears(dragon, tower))

    def test_the_soft_obstacles_can_be_pushed_through_slowly(self):
        for k in ("haystack", "hedge", "fence", "crops"):
            with self.subTest(asset=k):
                t = TerrainObject(k, 5, 5)
                self.assertTrue(t.passable, f"{k} should be passable")
                self.assertTrue(t.is_difficult, f"{k} should be difficult")

    def test_a_hedge_hides_you_but_does_not_stop_you(self):
        h = TerrainObject("hedge", 5, 5)
        self.assertTrue(h.passable)
        self.assertTrue(h.blocks_los)


# ===================================================================== #
# 6. THE BUILDER
# ===================================================================== #
class TestTheBuilder(unittest.TestCase):

    def test_building_it_twice_gives_the_same_city(self):
        a = maps_city.build_grand_city()
        b = maps_city.build_grand_city()
        self.assertEqual(a["terrain"], b["terrain"])

    def test_doors_are_never_paved_or_walled_over(self):
        """Merge priority: a door or gate beats whatever lands on it."""
        merged = maps_city._merge([
            maps_city._t("door", 3, 3),
            maps_city._t("wall", 3, 3),
            maps_city._t("gate", 4, 4),
            maps_city._t("cobblestone", 4, 4),
        ])
        by_pos = {(t["grid_x"], t["grid_y"]): t["terrain_type"]
                  for t in merged}
        self.assertEqual(by_pos[(3, 3)], "door")
        self.assertEqual(by_pos[(4, 4)], "gate")

    def test_the_helpers_produce_what_they_claim(self):
        self.assertEqual(len(maps_city._fill("wall", 0, 0, 2, 1)), 6)
        self.assertEqual(len(maps_city._outline("wall", 0, 0, 3, 3)), 12)
        self.assertEqual(len(maps_city._row("wall", 0, 4, 7)), 5)
        self.assertEqual(len(maps_city._col("wall", 7, 0, 4)), 5)

    def test_a_house_gets_exactly_one_door(self):
        for side in ("n", "s", "e", "w"):
            tiles = maps_city._building(2, 2, 6, 5, side)
            doors = [t for t in tiles if t["terrain_type"] == "door"]
            self.assertEqual(len(doors), 1, side)


if __name__ == "__main__":
    unittest.main()
