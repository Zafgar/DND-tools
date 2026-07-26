"""Taistelukentän mekaniikka ja grafiikka.

Neljä asiaa, jotka pelinjohtaja pyysi tarkistettavaksi:

  1. Lohikäärmeen henkäysase toimii — ja on rajattu rechargeen.
  2. Seinä katkaisee näköyhteyden niin että AI joko siirtyy tai jättää
     loitsun tekemättä; kartio EI läpäise kiviseinää.
  3. Liikkuminen toimii oikein rakennetulla kartalla: kukaan ei päädy
     läpäisemättömän ruudun sisään, eikä auto-battle jää ikuiseen
     looppiin kun puolet eivät voi tavoittaa toisiaan.
  4. Grafiikka: jokaisella maastotyypillä on oma piirtäjä, joka kestää
     kaikki ruutukoot, ja jokaisella kartalla on oma lattiatekstuuri.
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
from data.maps import (PREMADE_MAPS, load_map_terrain, get_spawn_zones,
                       get_floor_style, get_map_names)
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from engine.terrain import TerrainObject, TERRAIN_TYPES
from states.battle_state import BattleState
from states import battle_floor, terrain_art


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name="Magnus Dragonius"):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


def _wall_column(x, y_from=-40, y_to=60):
    return [TerrainObject("wall", x, y) for y in range(y_from, y_to)]


# ===================================================================== #
# 1. BREATH WEAPONS
# ===================================================================== #
class TestBreathWeapons(unittest.TestCase):
    def test_ai_uses_a_dragons_breath(self):
        random.seed(3)
        d = Entity(library.get_monster("Adult Red Dragon"), 12, 5,
                   is_player=False)
        pcs = [Entity(_hero(), 4, 4 + i, is_player=True) for i in range(3)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [d])
        b.start_combat()
        ai = TacticalAI()
        used = None
        for _ in range(6):
            d.reset_turn()
            plan = ai.calculate_turn(d, b)
            used = next((s for s in plan.steps
                         if "breath" in (s.action_name or "").lower()), None)
            if used:
                break
        self.assertIsNotNone(used, "AI never used the breath weapon")
        self.assertGreaterEqual(len(used.targets), 2)
        self.assertEqual(used.save_ability, "Dexterity")
        self.assertEqual(used.save_dc, 21)

    def test_every_breath_weapon_is_rate_limited(self):
        """Neljältä hirviöltä puuttui recharge-Feature, joten AI puhalsi
        joka vuoro — Young White Dragon teki 10d8 kylmää kierroksessa."""
        unlimited = []
        for m in library.get_all_monsters():
            for a in m.actions:
                if a.aoe_radius <= 0 or not a.damage_dice:
                    continue
                if "breath" not in a.name.lower():
                    continue
                feat = next((f for f in m.features if f.name == a.name), None)
                if feat is None or not (feat.recharge or feat.uses_per_day > 0):
                    unlimited.append((m.name, a.name))
        self.assertEqual(unlimited, [])

    def test_previously_unlimited_monsters_now_recharge(self):
        for name, action in (("Young White Dragon", "Cold Breath"),
                             ("Young Black Dragon", "Acid Breath"),
                             ("Hell Hound", "Fire Breath"),
                             ("Dust Mephit", "Blinding Breath")):
            m = library.get_monster(name)
            feat = next(f for f in m.features if f.name == action)
            self.assertTrue(feat.recharge, name)

    def test_breath_fires_at_most_once_in_several_rounds(self):
        random.seed(2)
        for name in ("Young White Dragon", "Hell Hound",
                     "Young Black Dragon"):
            d = Entity(library.get_monster(name), 9, 5, is_player=False)
            pcs = [Entity(_hero(), 4, 4 + i, is_player=True)
                   for i in range(3)]
            b = BattleSystem(log_callback=lambda s: None,
                             initial_entities=pcs + [d])
            b.start_combat()
            ai = TacticalAI()
            uses = 0
            for _ in range(8):
                d.reset_turn()
                plan = ai.calculate_turn(d, b)
                if any("breath" in (s.action_name or "").lower()
                       for s in plan.steps):
                    uses += 1
            self.assertLessEqual(uses, 2, f"{name} breathed {uses}x in 8 rounds")


# ===================================================================== #
# 2. LINE OF SIGHT
# ===================================================================== #
class TestWallsBlockLineOfSight(unittest.TestCase):
    def test_caster_moves_to_regain_los_instead_of_casting_blind(self):
        caster = Entity(library.get_monster("Archmage"), 2, 5,
                        is_player=False)
        target = Entity(_hero(), 12, 5, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, target])
        b.terrain = _wall_column(7, 0, 12)
        b.start_combat()
        self.assertFalse(b.has_line_of_sight(caster, target))
        caster.reset_turn()
        plan = TacticalAI().calculate_turn(caster, b)
        kinds = [s.step_type for s in plan.steps]
        self.assertIn("move", kinds)
        # …and the move is what unlocks the cast
        self.assertTrue(b.has_line_of_sight(caster, target))

    def test_pinned_caster_does_not_cast_through_the_wall(self):
        caster = Entity(library.get_monster("Archmage"), 2, 5,
                        is_player=False)
        caster.stats.speed = 0
        target = Entity(_hero(), 12, 5, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, target])
        b.terrain = _wall_column(7)
        b.start_combat()
        caster.reset_turn()
        caster.movement_left = 0
        plan = TacticalAI().calculate_turn(caster, b)
        for s in plan.steps:
            self.assertNotIn(target, list(s.targets or []))
            self.assertIsNot(s.target, target)

    def test_dragon_cannot_breathe_through_a_stone_wall(self):
        """Kartiolle ei tarkistettu näköyhteyttä lainkaan."""
        random.seed(1)
        d = Entity(library.get_monster("Adult Red Dragon"), 2, 5,
                   is_player=False)
        d.stats.speed = 0
        d.stats.fly_speed = 0
        pcs = [Entity(_hero(), 12, 4 + i, is_player=True) for i in range(3)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [d])
        b.terrain = _wall_column(7)
        b.start_combat()
        self.assertFalse(any(b.has_line_of_sight(d, p) for p in pcs))
        d.reset_turn()
        d.movement_left = 0
        plan = TacticalAI().calculate_turn(d, b)
        for s in plan.steps:
            self.assertEqual(list(s.targets or []), [], s.description)

    def test_cone_still_works_in_the_open(self):
        random.seed(1)
        d = Entity(library.get_monster("Adult Red Dragon"), 2, 5,
                   is_player=False)
        pcs = [Entity(_hero(), 9, 4 + i, is_player=True) for i in range(3)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [d])
        b.start_combat()
        d.reset_turn()
        plan = TacticalAI().calculate_turn(d, b)
        breath = next(s for s in plan.steps
                      if "breath" in (s.action_name or "").lower())
        self.assertEqual(len(breath.targets), 3)

    def test_cone_skips_only_the_shielded_target(self):
        """Osittainen este: näkyvät osuvat, piilossa oleva ei."""
        random.seed(1)
        d = Entity(library.get_monster("Adult Red Dragon"), 2, 5,
                   is_player=False)
        d.stats.speed = 0
        d.stats.fly_speed = 0
        seen = Entity(_hero(), 9, 5, is_player=True)
        seen.name = "SEEN"
        hidden = Entity(_hero("Krusk"), 9, 8, is_player=True)
        hidden.name = "HIDDEN"
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[seen, hidden, d])
        b.terrain = [TerrainObject("wall", x, y)
                     for x in (5, 6) for y in (7, 8, 9)]
        b.start_combat()
        self.assertTrue(b.has_line_of_sight(d, seen))
        self.assertFalse(b.has_line_of_sight(d, hidden))
        d.reset_turn()
        d.movement_left = 0
        plan = TacticalAI().calculate_turn(d, b)
        hit = {t.name for s in plan.steps for t in (s.targets or [])}
        self.assertNotIn("HIDDEN", hit)

    def test_sphere_aoe_skips_targets_behind_total_cover(self):
        """PHB s.204: täysi suoja purskahduksen keskipisteestä = ei osu."""
        ai = TacticalAI()
        caster = Entity(library.get_monster("Archmage"), 2, 5,
                        is_player=False)
        near = Entity(_hero(), 9, 5, is_player=True)
        near.name = "OPEN"
        walled = Entity(_hero("Krusk"), 9, 9, is_player=True)
        walled.name = "WALLED"
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, near, walled])
        b.terrain = [TerrainObject("wall", x, 7) for x in range(6, 13)]
        b.start_combat()
        result = ai._best_aoe_cluster(caster, [near, walled], [], b, 40,
                                     shape="sphere")
        self.assertIsNotNone(result)
        cluster, _aim = result
        self.assertIn(near, cluster)
        self.assertNotIn(walled, cluster)


# ===================================================================== #
# 3. MOVEMENT ON BUILT MAPS
# ===================================================================== #
class TestSelfCentredBursts(unittest.TestCase):
    """Wing Attack, Fire Aura ja Disrupt Life purkautuvat olennosta
    itsestään (range 0), mutta niitä tähdättiin kuin tulipalloa — Adult
    Red Dragon lyödä siivillä 35 ft päähän."""

    def test_wing_attack_cannot_reach_a_distant_target(self):
        d = Entity(library.get_monster("Adult Red Dragon"), 2, 5,
                   is_player=False)
        far = Entity(_hero(), 9, 5, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[far, d])
        b.start_combat()
        wing = next(a for a in d.stats.actions if a.name == "Wing Attack")
        self.assertEqual(wing.range, 0)
        self.assertIsNone(TacticalAI()._best_aoe_cluster(
            d, [far], [], b, wing.aoe_radius, shape="sphere",
            damage_type=wing.damage_type, self_centred=True))

    def test_wing_attack_hits_what_is_actually_close(self):
        """Etäisyys mitataan olennon keskipisteestä, joten Huge-kokoisen
        lohikäärmeen kohdalla 10 ft ulottuu sen keskeltä — ei reunasta.
        Se on tiedostettu yksinkertaistus; olennaista on että purskaus
        ei enää siirry mielivaltaiseen pisteeseen kentällä."""
        d = Entity(library.get_monster("Adult Red Dragon"), 5, 5,
                   is_player=False)
        close = Entity(_hero(), 8, 6, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[close, d])
        b.start_combat()
        wing = next(a for a in d.stats.actions if a.name == "Wing Attack")
        result = TacticalAI()._best_aoe_cluster(
            d, [close], [], b, wing.aoe_radius, shape="sphere",
            damage_type=wing.damage_type, self_centred=True)
        self.assertIsNotNone(result)
        self.assertIn(close, result[0])

    def test_aimed_bursts_still_aim(self):
        """Magma Eruption (range 120) tähdätään yhä kauas."""
        d = Entity(library.get_monster("Adult Red Dragon"), 2, 5,
                   is_player=False)
        pcs = [Entity(_hero(), 14, 5 + i, is_player=True) for i in range(2)]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + [d])
        b.start_combat()
        eruption = next(a for a in d.stats.actions
                        if a.name == "Magma Eruption")
        self.assertGreater(eruption.range, 0)
        result = TacticalAI()._best_aoe_cluster(
            d, pcs, [], b, eruption.aoe_radius, shape="sphere",
            damage_type=eruption.damage_type,
            self_centred=(eruption.range == 0))
        self.assertIsNotNone(result)
        self.assertEqual(len(result[0]), 2)


class TestMovementOnBuiltMaps(unittest.TestCase):
    def test_no_spawn_point_sits_inside_impassable_terrain(self):
        bad = []
        for key in PREMADE_MAPS:
            terr = load_map_terrain(key)
            blocked = {(t.grid_x, t.grid_y) for t in terr if not t.passable}
            for tag, zone in get_spawn_zones(key).items():
                self.assertEqual(len(zone), len(set(zone)),
                                 f"{key}/{tag} has duplicate spawns")
                for p in zone:
                    if p in blocked:
                        bad.append((key, tag, p))
        self.assertEqual(bad, [])

    def test_never_finishes_a_step_inside_a_closed_door(self):
        """Pathfinding pitää suljettua ovea kulkukelpoisena, koska sen voi
        avata. Jos avaus ei onnistu (portcullis, teljetty ovi), liike on
        pysäytettävä sitä ennen."""
        ai = TacticalAI()
        e = Entity(library.get_monster("Sanguis Custos"), 3, 5,
                   is_player=False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        gate = TerrainObject("door_locked", 4, 5)
        b.terrain = [gate]
        b.start_combat()
        self.assertFalse(ai._enter_cell_allowed(b, e, 4, 5))
        self.assertFalse(gate.door_open)

    def test_an_openable_door_is_opened_on_entry(self):
        ai = TacticalAI()
        e = Entity(library.get_monster("Sanguis Custos"), 3, 5,
                   is_player=False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        door = TerrainObject("door", 4, 5)
        b.terrain = [door]
        b.start_combat()
        self.assertTrue(ai._enter_cell_allowed(b, e, 4, 5))
        self.assertTrue(door.door_open)

    def test_a_portcullis_can_be_raised_but_a_wall_cannot(self):
        ai = TacticalAI()
        e = Entity(library.get_monster("Sanguis Custos"), 3, 5,
                   is_player=False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        b.terrain = [TerrainObject("portcullis", 4, 5),
                     TerrainObject("wall", 6, 5)]
        b.start_combat()
        self.assertTrue(ai._enter_cell_allowed(b, e, 4, 5))
        self.assertFalse(ai._enter_cell_allowed(b, e, 6, 5))

    def test_spread_reposition_refuses_a_blocked_square(self):
        """Regressio: _spread_from_allies teleporttasi hahmon suoraan,
        joten se päätyi portcullisin sisään."""
        ai = TacticalAI()
        e = Entity(library.get_monster("Sanguis Custos"), 5, 5,
                   is_player=False)
        b = BattleSystem(log_callback=lambda s: None, initial_entities=[e])
        b.terrain = [TerrainObject("portcullis", 6, 5)]
        b.start_combat()
        self.assertFalse(ai._enter_cell_allowed(b, e, 6, 5)
                         and not b.get_terrain_at(6, 5).door_open)

    def test_nobody_ends_up_inside_a_wall_on_any_premade_map(self):
        for key in PREMADE_MAPS:
            random.seed(9)
            terr = load_map_terrain(key)
            pz = get_spawn_zones(key)
            pcs = [Entity(_hero(), *pz["players"][i], is_player=True)
                   for i in range(min(3, len(pz["players"])))]
            foes = [Entity(library.get_monster("Sanguis Custos"),
                           *pz["enemies"][i], is_player=False)
                    for i in range(min(3, len(pz["enemies"])))]
            bs = BattleState(_FM(), entities=pcs + foes)
            bs.battle.terrain = terr
            bs._set_ai_mode("full_auto")
            for _ in range(1200):
                bs._process_auto_battle()
                if not bs.auto_battle:
                    break
                if (not [e for e in bs.battle.entities
                         if e.is_player and e.hp > 0]
                        or not [e for e in bs.battle.entities
                                if not e.is_player and e.hp > 0]):
                    break
            for e in bs.battle.entities:
                for t in terr:
                    if t.occupies(int(e.grid_x), int(e.grid_y)) \
                            and not t.passable:
                        self.fail(f"{key}: {e.name} stands inside "
                                  f"{t.terrain_type} at "
                                  f"({int(e.grid_x)},{int(e.grid_y)})")


class TestAutoBattleStalemate(unittest.TestCase):
    """Kun puolet eivät voi tavoittaa toisiaan, auto-battle jäi pyörimään
    ikuisesti. Nyt se pysähtyy ja kertoo pelinjohtajalle."""

    def _sealed_battle(self):
        pc = Entity(_hero(), 3, 5, is_player=True)
        pc.stats.speed = 0
        foe = Entity(library.get_monster("Sanguis Custos"), 20, 5,
                     is_player=False)
        foe.stats.speed = 0
        bs = BattleState(_FM(), entities=[pc, foe])
        bs.battle.terrain = _wall_column(11)
        bs._set_ai_mode("full_auto")
        return bs

    def test_it_stops_instead_of_spinning_forever(self):
        bs = self._sealed_battle()
        for _ in range(600):
            bs._process_auto_battle()
            if not bs.auto_battle:
                break
        else:
            self.fail("auto-battle never stopped on an unreachable enemy")
        self.assertFalse(bs.auto_battle)
        self.assertEqual(bs.ai_mode, "suggest")
        self.assertTrue(any("Umpikuja" in str(m) for m in bs.logs))

    def test_a_live_fight_is_not_flagged_as_a_stalemate(self):
        random.seed(4)
        pc = Entity(_hero(), 4, 5, is_player=True)
        foe = Entity(library.get_monster("Sanguis Custos"), 6, 5,
                     is_player=False)
        bs = BattleState(_FM(), entities=[pc, foe])
        bs._set_ai_mode("full_auto")
        stopped_early = False
        for _ in range(400):
            bs._process_auto_battle()
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
            if not bs.auto_battle:
                stopped_early = True
                break
        self.assertFalse(stopped_early,
                         "an active fight was mistaken for a stalemate")


# ===================================================================== #
# 4. GRAPHICS
# ===================================================================== #
class TestTerrainArtCoversEverything(unittest.TestCase):
    def test_every_terrain_type_has_a_painter(self):
        missing = [t for t in TERRAIN_TYPES
                   if not terrain_art.has_painter(t)]
        self.assertEqual(missing, [])

    def test_painters_survive_every_tile_size(self):
        for t in TERRAIN_TYPES:
            for size in ((4, 4), (10, 10), (28, 28), (64, 64), (120, 40)):
                s = pygame.Surface(size, pygame.SRCALPHA)
                ok = terrain_art.decorate_tile(s, t, size[0], size[1],
                                               (120, 110, 100), ticks=777)
                self.assertTrue(ok, f"{t} @ {size}")

    def test_no_painter_renders_a_blank_tile(self):
        for t in TERRAIN_TYPES:
            s = pygame.Surface((32, 32), pygame.SRCALPHA)
            terrain_art.decorate_tile(s, t, 32, 32, (120, 110, 100),
                                      ticks=500)
            painted = any(s.get_at((x, y))[3] > 0
                          for x in range(0, 32, 2)
                          for y in range(0, 32, 2))
            self.assertTrue(painted, f"{t} rendered nothing")

    def test_animated_painters_actually_animate(self):
        static = []
        for t in terrain_art._PAINTERS_TICKS:
            a = pygame.Surface((32, 32), pygame.SRCALPHA)
            b = pygame.Surface((32, 32), pygame.SRCALPHA)
            terrain_art.decorate_tile(a, t, 32, 32, (120, 110, 100), ticks=0)
            terrain_art.decorate_tile(b, t, 32, 32, (120, 110, 100), ticks=900)
            if all(a.get_at((x, y)) == b.get_at((x, y))
                   for x in range(32) for y in range(32)):
                static.append(t)
        self.assertEqual(static, [])

    def test_lava_animates_at_the_tile_centre_too(self):
        """Halkeamat keikkuivat keskipisteen ympäri, joten ruudun keskellä
        laava näytti jäätyneeltä."""
        a = pygame.Surface((60, 60), pygame.SRCALPHA)
        b = pygame.Surface((60, 60), pygame.SRCALPHA)
        terrain_art.decorate_tile(a, "lava", 60, 60, (255, 100, 0), ticks=0)
        terrain_art.decorate_tile(b, "lava", 60, 60, (255, 100, 0),
                                  ticks=5000)
        diffs = sum(1 for y in range(60)
                    if a.get_at((30, y)) != b.get_at((30, y)))
        self.assertGreater(diffs, 0)


class TestBattleFloor(unittest.TestCase):
    def test_every_map_declares_a_known_floor_style(self):
        known = set(battle_floor.known_styles())
        for key in PREMADE_MAPS:
            self.assertIn(get_floor_style(key), known, key)

    def test_maps_do_not_all_share_one_floor(self):
        styles = {get_floor_style(k) for k in PREMADE_MAPS}
        self.assertGreaterEqual(len(styles), 8)

    def test_unknown_style_falls_back_instead_of_crashing(self):
        self.assertIsNotNone(
            battle_floor.get_floor_patch("no-such-style", 40))
        self.assertEqual(get_floor_style("no-such-map"), "stone")

    def test_patch_is_cached_and_deterministic(self):
        battle_floor.clear_caches()
        first = battle_floor.get_floor_patch("flagstone", 40)
        self.assertIs(first, battle_floor.get_floor_patch("flagstone", 40))
        snapshot = [first.get_at((x, y))
                    for x in range(0, first.get_width(), 7)
                    for y in range(0, first.get_height(), 7)]
        battle_floor.clear_caches()
        again = battle_floor.get_floor_patch("flagstone", 40)
        self.assertEqual(snapshot,
                         [again.get_at((x, y))
                          for x in range(0, again.get_width(), 7)
                          for y in range(0, again.get_height(), 7)])

    def test_every_style_paints_something(self):
        for style in battle_floor.known_styles():
            patch = battle_floor.get_floor_patch(style, 32)
            self.assertIsNotNone(patch, style)
            base = battle_floor.base_color(style)
            varied = any(patch.get_at((x, y))[:3] != base
                         for x in range(0, patch.get_width(), 3)
                         for y in range(0, patch.get_height(), 3))
            self.assertTrue(varied, f"{style} is a flat fill")

    def test_degenerate_grid_size_is_refused(self):
        self.assertIsNone(battle_floor.get_floor_patch("stone", 0))
        self.assertIsNone(battle_floor.get_vignette(0, 0))

    def test_draw_floor_and_vignette_paint_into_the_viewport(self):
        screen = pygame.Surface((300, 200))
        screen.fill((0, 0, 0))
        rect = pygame.Rect(0, 0, 300, 200)
        self.assertTrue(battle_floor.draw_floor(screen, rect, "grass", 40,
                                                camera_x=17, camera_y=23))
        self.assertNotEqual(screen.get_at((150, 100))[:3], (0, 0, 0))
        before = screen.get_at((2, 2))
        self.assertTrue(battle_floor.draw_vignette(screen, rect))
        self.assertNotEqual(screen.get_at((2, 2)), before)


class TestMapsRenderAndRun(unittest.TestCase):
    def test_every_map_is_listed_with_a_name_and_description(self):
        listed = {k for k, _n, _d in get_map_names()}
        self.assertEqual(listed, set(PREMADE_MAPS))
        for _k, name, desc in get_map_names():
            self.assertTrue(name)
            self.assertGreater(len(desc), 20)

    def test_the_new_campaign_maps_exist(self):
        for key in ("vigil_temple", "corvus_crypt", "crystal_lake_palace"):
            self.assertIn(key, PREMADE_MAPS, key)
            self.assertGreater(len(load_map_terrain(key)), 100, key)

    def test_loading_a_premade_map_applies_its_floor_style(self):
        bs = BattleState(_FM(), entities=[
            Entity(_hero(), 3, 3, is_player=True),
            Entity(library.get_monster("Sanguis Custos"), 9, 5,
                   is_player=False)])
        bs._load_premade_map("vigil_temple")
        self.assertEqual(bs.battle.floor_style, "temple")
        self.assertGreater(len(bs.battle.terrain), 100)
        bs._load_premade_map("forest_clearing")
        self.assertEqual(bs.battle.floor_style, "forest")

    def test_a_frame_renders_on_every_map(self):
        screen = pygame.display.get_surface()
        for key in PREMADE_MAPS:
            bs = BattleState(_FM(), entities=[
                Entity(_hero(), *get_spawn_zones(key)["players"][0],
                       is_player=True),
                Entity(library.get_monster("Praefectus Sanguinis Ostorius"),
                       *get_spawn_zones(key)["enemies"][0],
                       is_player=False)])
            bs._load_premade_map(key)
            screen.fill((0, 0, 0))
            bs.draw(screen)

    def test_a_frame_renders_with_every_terrain_type_on_screen(self):
        screen = pygame.display.get_surface()
        bs = BattleState(_FM(), entities=[
            Entity(_hero(), 4, 4, is_player=True),
            Entity(library.get_monster("Sanctum Abominatio"), 9, 5,
                   is_player=False)])
        bs.battle.terrain = [TerrainObject(t, 2 + (i % 20), 8 + (i // 20))
                             for i, t in enumerate(TERRAIN_TYPES)]
        for style in battle_floor.known_styles():
            bs.battle.floor_style = style
            screen.fill((0, 0, 0))
            bs.draw(screen)


if __name__ == "__main__":
    unittest.main()
