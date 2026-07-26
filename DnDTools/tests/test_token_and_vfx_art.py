"""Token-taide ja taistelun VFX.

Kaksi asiaa: olentojen tokenit näyttävät nappuloilta eikä väripalloilta,
ja kentällä tapahtuvat asiat näkyvät — kartio kartiona, tulipallo
räjähdyksenä, elinvoiman imu virtana kohteesta imijään.
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
from data.spells import get_spell
from data.maps import load_map_terrain
from engine.entities import Entity
from states.battle_state import BattleState
from states import token_art
import states.battle_vfx as V


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name="Magnus Dragonius"):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


class _P:
    """Minimal stand-in with just the grid position the VFX need."""
    def __init__(self, x, y):
        self.grid_x = float(x)
        self.grid_y = float(y)


def _gp(gx, gy):
    return (int(gx * 40), int(gy * 40))


def _blank(surf):
    w, h = surf.get_size()
    return not any(surf.get_at((x, y))[3] > 0
                   for x in range(0, w, 3) for y in range(0, h, 3))


# ===================================================================== #
# TOKEN ART
# ===================================================================== #
class TestTokenArtHelpers(unittest.TestCase):
    def _surf(self, size=200):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        return s

    def test_hp_colour_bands(self):
        self.assertEqual(token_art.hp_color(1.0), (90, 210, 110))
        self.assertEqual(token_art.hp_color(0.5), (235, 190, 70))
        self.assertEqual(token_art.hp_color(0.1), (225, 75, 70))
        self.assertEqual(token_art.hp_color(0.0), (225, 75, 70))

    def test_hp_colour_clamps_out_of_range(self):
        self.assertEqual(token_art.hp_color(5.0), token_art.hp_color(1.0))
        self.assertEqual(token_art.hp_color(-3.0), token_art.hp_color(0.0))

    def test_threat_tiers_separate_boss_from_mook(self):
        self.assertEqual(token_art.threat_tier(0.5)[0], 0)    # rabble
        self.assertEqual(token_art.threat_tier(4.0)[0], 1)    # notable
        self.assertEqual(token_art.threat_tier(8.0)[0], 2)    # elite
        self.assertEqual(token_art.threat_tier(13.0)[0], 3)   # boss
        self.assertEqual(token_art.threat_tier(20.0)[0], 4)   # legendary
        # a CR 13 priest must not look like one of the CR 4 choir
        self.assertGreater(token_art.threat_tier(13.0)[0],
                           token_art.threat_tier(4.0)[0])

    def test_the_vigil_roster_is_visually_ranked(self):
        """Ostorius (CR 13) ja Sanctum Abominatio (CR 16) saavat enemmän
        merkkejä kuin kuoro (CR 4)."""
        cr = {n: library.get_monster(n).challenge_rating
              for n in ("Verikuoron akolyytti", "Sanguis Custos",
                        "Praefectus Sanguinis Ostorius",
                        "Sanctum Abominatio")}
        notches = {n: token_art.threat_tier(c)[0] for n, c in cr.items()}
        self.assertLess(notches["Verikuoron akolyytti"],
                        notches["Praefectus Sanguinis Ostorius"])
        self.assertLessEqual(notches["Sanguis Custos"],
                             notches["Sanctum Abominatio"])

    def test_threat_tier_survives_junk_input(self):
        self.assertEqual(token_art.threat_tier(None), (0, None))
        self.assertEqual(token_art.threat_tier("boss"), (0, None))

    def test_base_ring_paints(self):
        s = self._surf()
        token_art.draw_base_ring(s, 100, 100, 30, (200, 160, 60))
        self.assertFalse(_blank(s))

    def test_hp_arc_returns_the_fraction_and_paints(self):
        s = self._surf()
        frac = token_art.draw_hp_arc(s, 100, 100, 30, 25, 100)
        self.assertAlmostEqual(frac, 0.25, places=3)
        self.assertFalse(_blank(s))

    def test_hp_arc_at_full_and_zero(self):
        s = self._surf()
        self.assertEqual(token_art.draw_hp_arc(s, 100, 100, 30, 100, 100), 1.0)
        s2 = self._surf()
        self.assertEqual(token_art.draw_hp_arc(s2, 100, 100, 30, 0, 100), 0.0)
        # an empty track is still drawn so the ring reads as "at zero"
        self.assertFalse(_blank(s2))

    def test_hp_arc_skips_creatures_with_no_hp_pool(self):
        s = self._surf()
        self.assertEqual(token_art.draw_hp_arc(s, 100, 100, 30, 0, 0), 0.0)
        self.assertTrue(_blank(s))

    def test_flying_shadow_is_offset_from_a_grounded_one(self):
        ground = self._surf()
        air = self._surf()
        token_art.draw_shadow(ground, 100, 100, 30, elevation_ft=0)
        token_art.draw_shadow(air, 100, 100, 30, elevation_ft=40,
                              is_flying=True)
        self.assertFalse(_blank(ground))
        self.assertFalse(_blank(air))
        diff = sum(1 for x in range(0, 200, 2) for y in range(0, 200, 2)
                   if ground.get_at((x, y)) != air.get_at((x, y)))
        self.assertGreater(diff, 0, "altitude did not change the shadow")

    def test_threat_notches_paint_only_for_real_threats(self):
        mook = self._surf()
        boss = self._surf()
        self.assertEqual(token_art.draw_threat_notches(mook, 100, 100, 30, 0.25), 0)
        self.assertTrue(_blank(mook))
        self.assertEqual(token_art.draw_threat_notches(boss, 100, 100, 30, 16.0), 3)
        self.assertFalse(_blank(boss))

    def test_turn_pulse_breathes(self):
        a = self._surf()
        b = self._surf()
        token_art.draw_turn_pulse(a, 100, 100, 30, 0)
        token_art.draw_turn_pulse(b, 100, 100, 30, 500)
        self.assertFalse(_blank(a))
        diff = sum(1 for x in range(0, 200, 2) for y in range(0, 200, 2)
                   if a.get_at((x, y)) != b.get_at((x, y)))
        self.assertGreater(diff, 0, "turn pulse is static")

    def test_selection_ring_differs_from_turn_pulse(self):
        pulse = self._surf()
        select = self._surf()
        token_art.draw_turn_pulse(pulse, 100, 100, 30, 0)
        token_art.draw_selection_ring(select, 100, 100, 30)
        self.assertFalse(_blank(select))
        diff = sum(1 for x in range(0, 200, 2) for y in range(0, 200, 2)
                   if pulse.get_at((x, y)) != select.get_at((x, y)))
        self.assertGreater(diff, 20,
                           "selection and active turn look the same")

    def test_condition_ring_picks_the_most_disabling_condition(self):
        s = self._surf()
        chosen = token_art.draw_condition_ring(
            s, 100, 100, 30, ["Poisoned", "Stunned", "Prone"])
        self.assertEqual(chosen, "Stunned")
        self.assertFalse(_blank(s))

    def test_condition_ring_is_silent_with_no_conditions(self):
        s = self._surf()
        self.assertIsNone(token_art.draw_condition_ring(s, 100, 100, 30, []))
        self.assertTrue(_blank(s))

    def test_condition_ring_ignores_unknown_conditions(self):
        s = self._surf()
        self.assertIsNone(
            token_art.draw_condition_ring(s, 100, 100, 30, ["Bewildered"]))

    def test_every_helper_survives_a_tiny_radius(self):
        s = self._surf(40)
        for r in (0, 1, 2, 3, 6):
            token_art.draw_shadow(s, 20, 20, r)
            token_art.draw_base_ring(s, 20, 20, r, (200, 100, 50))
            token_art.draw_hp_arc(s, 20, 20, r, 5, 10)
            token_art.draw_threat_notches(s, 20, 20, r, 20.0)
            token_art.draw_turn_pulse(s, 20, 20, r, 100)
            token_art.draw_selection_ring(s, 20, 20, r)
            token_art.draw_condition_ring(s, 20, 20, r, ["Stunned"])
            token_art.draw_prone_base(s, 20, 20, r, (200, 100, 50))


class TestTokensRenderInBattle(unittest.TestCase):
    def test_a_frame_renders_with_every_token_state(self):
        heroes = ["Magnus Dragonius", "Balthazar", "Venris Galanodel"]
        pcs = [Entity(_hero(n), 4, 4 + i, is_player=True)
               for i, n in enumerate(heroes)]
        foes = [Entity(library.get_monster(n), 10, 4 + i * 2, is_player=False)
                for i, n in enumerate(["Praefectus Sanguinis Ostorius",
                                       "Verikuoron akolyytti",
                                       "Adult Red Dragon"])]
        foes[1].add_condition("Stunned")
        foes[2].elevation = 30
        foes[2].is_flying = True
        pcs[1].add_condition("Prone")
        pcs[2].hp = max(1, pcs[2].max_hp // 5)
        bs = BattleState(_FM(), entities=pcs + foes)
        bs.battle.terrain = load_map_terrain("vigil_temple")
        screen = pygame.display.get_surface()
        screen.fill((0, 0, 0))
        bs.draw(screen)

    def test_dead_and_dying_tokens_still_render(self):
        pc = Entity(_hero(), 4, 4, is_player=True)
        pc.hp = 0
        foe = Entity(library.get_monster("Verikuoron akolyytti"), 6, 4,
                     is_player=False)
        foe.hp = -5
        bs = BattleState(_FM(), entities=[pc, foe])
        screen = pygame.display.get_surface()
        screen.fill((0, 0, 0))
        bs.draw(screen)


# ===================================================================== #
# VFX
# ===================================================================== #
ALL_VFX = (
    lambda: V.ConeBlast(2, 2, 8, 5, length_cells=12, damage_type="fire"),
    lambda: V.Explosion(5, 5, radius_cells=4, damage_type="fire"),
    lambda: V.LightningArc(2, 2, 9, 6),
    lambda: V.FrostShards(5, 5, radius_cells=2),
    lambda: V.DrainMotes(8, 5, 2, 2),
    lambda: V.RadiantPillar(5, 5),
    lambda: V.PsychicRipple(5, 5, radius_cells=2),
    lambda: V.PoisonBubbles(5, 5, radius_cells=2),
    lambda: V.ThunderRing(5, 5, radius_cells=3),
    lambda: V.CritStar(5, 5),
    lambda: V.MissSpark(5, 5, 45),
    lambda: V.TeleportPuff(5, 5, inward=True),
    lambda: V.SummonRune(5, 5, cells=2),
    lambda: V.ConditionMark(5, 5, "STN", (255, 255, 100)),
    lambda: V.Projectile(2, 2, 8, 5, style="arrow"),
    lambda: V.Beam(2, 2, 8, 5),
    lambda: V.SpellAura(5, 5, radius_cells=3),
    lambda: V.SlashTrail(5, 5, 30),
    lambda: V.HealAura(5, 5),
)


class TestVfxProtocol(unittest.TestCase):
    def test_every_effect_expires(self):
        for make in ALL_VFX:
            fx = make()
            frames = 0
            while fx.life > 0 and frames < 300:
                fx.update()
                frames += 1
            self.assertLess(frames, 300, type(fx).__name__)

    def test_every_effect_renders_every_frame_without_crashing(self):
        screen = pygame.Surface((800, 600), pygame.SRCALPHA)
        for make in ALL_VFX:
            fx = make()
            while fx.life > 0:
                fx.draw(screen, _gp, 40)
                fx.update()

    def test_every_effect_paints_something_mid_life(self):
        for make in ALL_VFX:
            fx = make()
            painted = False
            while fx.life > 0:
                screen = pygame.Surface((800, 600), pygame.SRCALPHA)
                screen.fill((0, 0, 0, 0))
                fx.draw(screen, _gp, 40)
                if not _blank(screen):
                    painted = True
                    break
                fx.update()
            self.assertTrue(painted, f"{type(fx).__name__} never painted")

    def test_effects_animate_over_their_lifetime(self):
        for make in ALL_VFX:
            fx = make()
            frames = []
            for _ in range(3):
                s = pygame.Surface((400, 300), pygame.SRCALPHA)
                s.fill((0, 0, 0, 0))
                fx.draw(s, _gp, 40)
                frames.append(s)
                for _ in range(max(1, fx.max_life // 4)):
                    fx.update()
            differing = any(
                frames[0].get_at((x, y)) != frames[1].get_at((x, y))
                for x in range(0, 400, 4) for y in range(0, 300, 4))
            self.assertTrue(differing, f"{type(fx).__name__} is static")

    def test_effects_survive_a_tiny_grid_size(self):
        screen = pygame.Surface((200, 200), pygame.SRCALPHA)
        for make in ALL_VFX:
            fx = make()
            while fx.life > 0:
                fx.draw(screen, lambda gx, gy: (int(gx * 6), int(gy * 6)), 6)
                fx.update()


class TestVfxSelection(unittest.TestCase):
    """Oikea efekti oikeaan asiaan — tämä on koko pyynnön ydin."""

    def setUp(self):
        self.a = _P(2, 2)
        self.b = _P(8, 5)

    def _action(self, name, monster="Adult Red Dragon"):
        return next(x for x in library.get_monster(monster).actions
                    if x.name == name)

    def test_breath_weapon_renders_as_a_cone_not_a_bolt(self):
        breath = self._action("Fire Breath")
        vfx = V.make_attack_vfx(self.a, self.b, breath, damage_type="fire")
        self.assertIsInstance(vfx, V.ConeBlast)

    def test_melee_weapon_renders_as_a_slash(self):
        bite = self._action("Bite")
        vfx = V.make_attack_vfx(self.a, self.b, bite, damage_type="piercing")
        self.assertIsInstance(vfx, V.SlashTrail)

    def test_slash_points_back_toward_the_attacker(self):
        bite = self._action("Bite")
        vfx = V.make_attack_vfx(self.a, self.b, bite, damage_type="piercing")
        self.assertNotEqual(vfx.angle_deg, 0.0)

    def test_a_drain_bite_flows_from_victim_to_drainer(self):
        drain = next(a for a in library.get_monster(
            "Praefectus Sanguinis Ostorius").actions
            if a.name == "Elinvoiman purenta")
        vfx = V.make_attack_vfx(self.a, self.b, drain,
                                damage_type="necrotic")
        self.assertIsInstance(vfx, V.DrainMotes)
        # motes start at the victim and end at the attacker
        self.assertEqual((vfx.gx0, vfx.gy0), (self.b.grid_x, self.b.grid_y))
        self.assertEqual((vfx.gx1, vfx.gy1), (self.a.grid_x, self.a.grid_y))

    def test_self_centred_burst_erupts_from_the_creature(self):
        wing = self._action("Wing Attack")
        self.assertEqual(wing.range, 0)
        vfx = V.make_attack_vfx(self.a, self.b, wing,
                                damage_type="bludgeoning")
        self.assertEqual((vfx.gx, vfx.gy), (self.a.grid_x, self.a.grid_y))

    def test_ranged_weapon_is_still_a_projectile(self):
        bow = next(a for a in library.get_monster("Custos Nocturnus").actions
                   if a.name == "Pyhä varsijousi")
        vfx = V.make_attack_vfx(self.a, self.b, bow, damage_type="piercing")
        self.assertIsInstance(vfx, V.Projectile)

    def test_spell_effects_match_their_damage_type(self):
        expected = {
            "Fireball": V.Explosion,
            "Cone of Cold": V.ConeBlast,
            "Chain Lightning": V.LightningArc,
            "Thunderwave": V.ThunderRing,
            "Cloudkill": V.PoisonBubbles,
            "Guiding Bolt": V.RadiantPillar,
            "Vampiric Touch": V.DrainMotes,
            "Sunburst": V.RadiantPillar,
        }
        for name, cls in expected.items():
            vfx = V.make_spell_vfx(self.a, self.b, get_spell(name))
            self.assertIsInstance(vfx, cls, name)

    def test_a_plain_single_target_spell_is_a_beam(self):
        vfx = V.make_spell_vfx(self.a, self.b, get_spell("Magic Missile"))
        self.assertIsInstance(vfx, V.Beam)

    def test_every_library_spell_produces_a_usable_effect(self):
        import data.spells as spells_mod
        screen = pygame.Surface((900, 700), pygame.SRCALPHA)
        for name, sp in spells_mod._spells.items():
            vfx = V.make_spell_vfx(self.a, self.b, sp)
            if vfx is None:
                continue
            while vfx.life > 0:
                vfx.draw(screen, _gp, 40)
                vfx.update()

    def test_every_monster_action_produces_a_usable_effect(self):
        screen = pygame.Surface((1200, 900), pygame.SRCALPHA)
        checked = 0
        for m in library.get_all_monsters():
            for act in m.actions:
                if act.is_multiattack:
                    continue
                vfx = V.make_attack_vfx(self.a, self.b, act,
                                        damage_type=act.damage_type)
                if vfx is None:
                    continue
                checked += 1
                while vfx.life > 0:
                    vfx.draw(screen, _gp, 40)
                    vfx.update()
        self.assertGreater(checked, 200)

    def test_outcome_effects(self):
        self.assertIsInstance(V.make_outcome_vfx(self.a, self.b, "crit"),
                              V.CritStar)
        self.assertIsInstance(V.make_outcome_vfx(self.a, self.b, "miss"),
                              V.MissSpark)
        self.assertIsNone(V.make_outcome_vfx(self.a, self.b, "hit"))
        self.assertIsNone(V.make_outcome_vfx(self.a, None, "crit"))

    def test_condition_effect_uses_the_badge_label(self):
        vfx = V.make_condition_vfx(self.b, "Stunned")
        self.assertIsInstance(vfx, V.ConditionMark)
        self.assertEqual(vfx.label, "STN")
        self.assertIsNone(V.make_condition_vfx(self.b, ""))
        self.assertIsNone(V.make_condition_vfx(None, "Stunned"))

    def test_unknown_condition_still_gets_a_mark(self):
        vfx = V.make_condition_vfx(self.b, "Bewildered")
        self.assertIsInstance(vfx, V.ConditionMark)
        self.assertEqual(vfx.label, "BEWI")


class TestVfxWiredIntoCombat(unittest.TestCase):
    """Efektit eivät ole olemassa jos niitä ei koskaan luoda oikeassa
    taistelussa."""

    def _run(self, foe_names, seed, steps=2500):
        random.seed(seed)
        heroes = ["Magnus Dragonius", "Balthazar", "Venris Galanodel",
                  "Padak Onslaught", "Marduk"]
        pcs = [Entity(_hero(n), 3 + (i % 3), 3 + i, is_player=True)
               for i, n in enumerate(heroes)]
        foes = [Entity(library.get_monster(n), 12, 3 + i * 2,
                       is_player=False)
                for i, n in enumerate(foe_names)]
        bs = BattleState(_FM(), entities=pcs + foes)
        bs._set_ai_mode("full_auto")
        screen = pygame.display.get_surface()
        seen = set()
        for i in range(steps):
            bs._process_auto_battle()
            seen.update(type(fx).__name__ for fx in bs.impact_flashes)
            if i % 25 == 0:
                screen.fill((0, 0, 0))
                bs.draw(screen)
            if not bs.auto_battle:
                break
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        return seen

    def test_a_dragon_fight_produces_a_cone(self):
        seen = self._run(["Adult Red Dragon",
                          "Praefectus Sanguinis Ostorius"], 5)
        self.assertIn("ConeBlast", seen)

    def test_condition_marks_and_misses_appear(self):
        seen = self._run(["Magister Sanguinis Vhaltor", "Sanguis Custos",
                          "Custos Nocturnus"], 11)
        self.assertIn("ConditionMark", seen)
        self.assertIn("MissSpark", seen)

    def test_summons_get_a_summoning_circle(self):
        seen = self._run(["Cazna Icharyd"], 23)
        self.assertIn("SummonRune", seen)

    def test_teleport_step_carries_both_ends(self):
        """Misty Step relocates the token during planning; the step has to
        remember where it came from or the puffs cannot be drawn."""
        from engine.ai import TacticalAI
        from engine.battle import BattleSystem
        caster = Entity(library.get_monster("Sanguis Custos"), 10, 10,
                        is_player=False)
        threat = Entity(_hero(), 11, 10, is_player=True)
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=[caster, threat])
        b.start_combat()
        caster.reset_turn()
        spell = next(s for s in caster.stats.spells_known
                     if s.name == "Misty Step")
        step = TacticalAI()._try_teleport_escape(caster, threat, b, spell)
        self.assertIsNotNone(step)
        self.assertEqual((step.old_x, step.old_y), (10.0, 10.0))
        self.assertNotEqual((step.new_x, step.new_y),
                            (step.old_x, step.old_y))

    def test_spawn_helpers_are_safe_with_nothing_to_show(self):
        bs = BattleState(_FM(), entities=[
            Entity(_hero(), 3, 3, is_player=True),
            Entity(library.get_monster("Verikuoron akolyytti"), 6, 3,
                   is_player=False)])
        before = len(bs.impact_flashes)
        bs._spawn_outcome_vfx(None, None, "crit")
        bs._spawn_condition_vfx(None, "Stunned")
        bs._spawn_condition_vfx(bs.battle.entities[0], "")
        bs._spawn_summon_vfx(None)
        bs._spawn_teleport_vfx(None, None)
        self.assertEqual(len(bs.impact_flashes), before)


if __name__ == "__main__":
    unittest.main()
