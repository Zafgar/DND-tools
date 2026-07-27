"""Kampanjan kaksi tärkeintä hahmoa: Tarquvas Redfei ja Cazna Icharyd.

Kattaa:
  * pelinjohtajan antaman raakapohjan numerot sellaisenaan (CR, HP, AC,
    kykyarvot, regeneraatio, DC:t),
  * täydennykset joita hän erikseen pyysi — Tarquvaksen musta
    obsidiaaninen kahden käden miekka, vaalea täyshaarniska ja kehoon
    liitettyjen kristallien magia; Caznan miekkataito,
  * myyttiset toisen vaiheen kyvyt (Unstoppable Will, Foresight),
  * kytkennät maailmaan: NPC-lehdet, suhteet, Lore-Codex,
  * AI ajaa molemmat läpi kaatumatta, ja auto-battle päättyy,
  * regressio: Relentless Endurance kuluu — puoliörkki ei ole
    kuolematon eikä auto-battle jää ikuiseen looppiin.
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
from data.spells import has_spell, get_spell
from data.heroes import hero_list
from data.novus_somnium import build_novus_somnium
from data import lore_codex as codex
from states.campaign_manager import CampaignManagerState
from engine.entities import Entity
from engine.battle import BattleSystem
from engine.ai import TacticalAI
from states.battle_state import BattleState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


def _hero(name):
    return copy.deepcopy({h.name: h for h in hero_list}[name])


class TestTarquvas(unittest.TestCase):
    def setUp(self):
        self.t = library.get_monster("Keisari Tarquvas Redfei")

    def test_raw_numbers_from_the_dm(self):
        self.assertEqual(self.t.challenge_rating, 28.0)
        self.assertEqual(self.t.xp, 120000)
        self.assertEqual(self.t.hit_points, 750)
        self.assertEqual(self.t.armor_class, 25)
        self.assertEqual(self.t.proficiency_bonus, 8)
        a = self.t.abilities
        self.assertEqual(
            (a.strength, a.dexterity, a.constitution,
             a.intelligence, a.wisdom, a.charisma),
            (30, 18, 30, 16, 20, 24))

    def test_veru_regeneration_is_50_per_turn(self):
        regen = next(f for f in self.t.features
                     if f.mechanic == "regeneration")
        self.assertEqual(regen.mechanic_value, "50")

    def test_faerzress_tattoos_give_magic_resistance(self):
        feats = {f.name: f for f in self.t.features}
        self.assertIn("Faerzress-tatuoinnit", feats)
        self.assertEqual(feats["Faerzress-tatuoinnit"].mechanic,
                         "magic_resistance")
        # tason 5 ja alle loitsut eivät vaikuta lainkaan
        self.assertIn("tason 5", feats["Faerzress-tatuoinnit"].description)

    def test_unstoppable_will_mythic_trait(self):
        feats = {f.name: f for f in self.t.features}
        self.assertIn("Unstoppable Will (Mythic Trait)", feats)
        desc = feats["Unstoppable Will (Mythic Trait)"].description
        self.assertIn("400", desc)
        self.assertIn("Oknar", desc)

    def test_second_phase_is_wired_to_the_engine(self):
        phase = next(f for f in self.t.features
                     if f.phase_trigger_hp_pct > 0)
        self.assertEqual(phase.phase_trigger_hp_pct, 0.25)
        self.assertTrue(phase.phase_description)

    def test_titanic_strikes(self):
        names = {a.name for a in self.t.actions}
        self.assertIn("Multiattack", names)
        self.assertIn("Titaaninen isku", names)
        ma = next(a for a in self.t.actions if a.is_multiattack)
        self.assertEqual(ma.multiattack_count, 4)
        punch = next(a for a in self.t.actions
                     if a.name == "Titaaninen isku")
        self.assertEqual(punch.attack_bonus, 19)
        self.assertEqual(punch.damage_dice, "4d12")
        self.assertEqual(punch.applies_condition, "Prone")

    def test_black_obsidian_greatsword(self):
        """DM: 'valtavaa täysin mustaa obsidian väristä kahden käden
        miekkaa'."""
        sword = next(a for a in self.t.actions if a.name == "Aki'kor")
        self.assertEqual(sword.attack_bonus, 19)
        self.assertEqual(sword.damage_type, "slashing")
        self.assertEqual(sword.reach, 10)
        self.assertIn("two-handed", sword.properties)
        self.assertIn("heavy", sword.properties)
        item = next(i for i in self.t.items if "Aki'kor" in i.name)
        self.assertEqual(item.item_type, "weapon")
        self.assertEqual(item.slot, "main_hand")
        self.assertEqual(item.rarity, "artifact")
        self.assertIn("musta", item.description.lower())
        self.assertIn("obsidiaani", item.description.lower())

    def test_pale_full_plate(self):
        """DM: 'kaunis vaalea täys plate haarniska'."""
        armour = next(i for i in self.t.items if i.slot == "armor")
        self.assertEqual(armour.armor_category, "heavy")
        self.assertIn("valkoinen", armour.description.lower())
        self.assertFalse(armour.stealth_disadvantage)
        self.assertIn("täyshaarniska", self.t.armor_type.lower())

    def test_crystal_magic_bound_to_his_body(self):
        """DM: 'kykenevä käyttämään magiaa joka liittyi hänen kehoon
        liitettyihin kristalleihin'."""
        self.assertEqual(self.t.spellcasting_ability, "Charisma")
        self.assertEqual(self.t.spell_save_dc, 23)
        self.assertTrue(self.t.spells_known)
        feats = {f.name for f in self.t.features}
        self.assertIn("Kristallimagia (Innate Spellcasting)", feats)
        self.assertIn("Kristallimagia", {a.name for a in self.t.actions})
        # Force / lightning / reality-bending — ei kirjaloitsijan arsenaali
        known = {s.name for s in self.t.spells_known}
        for expected in ("Chain Lightning", "Disintegrate", "Wall of Force",
                         "Telekinesis"):
            self.assertIn(expected, known)

    def test_garruthan_rage_destroys_force_walls(self):
        rage = next(a for a in self.t.actions if a.name == "Garruthan raivo")
        self.assertEqual(rage.damage_dice, "15d10")
        self.assertEqual(rage.damage_type, "force")
        self.assertEqual(rage.aoe_shape, "cone")
        self.assertEqual(rage.aoe_radius, 90)
        self.assertEqual(rage.condition_dc, 26)
        self.assertIn("Wall of Force", rage.description)

    def test_three_of_five_veru_fragments(self):
        feats = {f.name: f for f in self.t.features}
        self.assertIn("Kolme viidestä Veru-palasesta", feats)
        self.assertIn("SIELUNSA",
                      feats["Kolme viidestä Veru-palasesta"].description)
        self.assertTrue(any("Veru" in i.name for i in self.t.items))

    def test_lore_details_are_present(self):
        for bit in ("25-vuotiaana", "lohikäärme", "suodattimen",
                    "Garrutha"):
            self.assertIn(bit, self.t.lore)
        self.assertTrue(self.t.tactics)
        self.assertTrue(self.t.loot_table)

    def test_immunities_match_the_unkillable_lore(self):
        for cond in ("Charmed", "Frightened", "Paralyzed", "Stunned",
                     "Prone", "Exhaustion"):
            self.assertIn(cond, self.t.condition_immunities)
        self.assertIn("poison", self.t.damage_immunities)
        self.assertTrue(any("force" in r for r in self.t.damage_resistances))

    def test_legendary_and_lair_actions(self):
        self.assertEqual(self.t.legendary_action_count, 3)
        self.assertEqual(self.t.legendary_resistance_count, 5)
        leg = [f for f in self.t.features if f.feature_type == "legendary"]
        lair = [f for f in self.t.features if f.feature_type == "lair"]
        self.assertGreaterEqual(len(leg), 3)
        self.assertGreaterEqual(len(lair), 2)

    def test_all_referenced_spells_exist(self):
        for s in list(self.t.spells_known) + list(self.t.cantrips):
            self.assertTrue(has_spell(s.name), s.name)


class TestCazna(unittest.TestCase):
    def setUp(self):
        self.c = library.get_monster("Cazna Icharyd")

    def test_raw_numbers_from_the_dm(self):
        self.assertEqual(self.c.challenge_rating, 26.0)
        self.assertEqual(self.c.xp, 90000)
        self.assertEqual(self.c.hit_points, 350)
        self.assertEqual(self.c.armor_class, 22)
        self.assertEqual(self.c.spell_save_dc, 25)
        a = self.c.abilities
        self.assertEqual(
            (a.strength, a.dexterity, a.constitution,
             a.intelligence, a.wisdom, a.charisma),
            (10, 22, 18, 28, 24, 24))

    def test_two_ninth_level_slots(self):
        self.assertEqual(self.c.spell_slots.get("9th"), 2)

    def test_archmage_supreme_two_spells_per_turn(self):
        feats = {f.name: f for f in self.c.features}
        self.assertIn("Archmage Supreme", feats)
        self.assertIn("KAKSI", feats["Archmage Supreme"].description)
        # bonustoiminto joka on toinen loitsu
        self.assertIn("Toinen loitsu",
                      {a.name for a in self.c.bonus_actions})

    def test_she_is_also_a_skilled_swordfighter(self):
        """DM: 'Matriarkka käyttää myös miekkaa taitavasti'."""
        sword = next(a for a in self.c.actions
                     if a.name == "Icharydin sielumiekka")
        self.assertEqual(sword.attack_bonus, 17)
        self.assertIn("finesse", sword.properties)
        ma = next(a for a in self.c.actions if a.is_multiattack)
        self.assertEqual(ma.multiattack_count, 2)
        feats = {f.name: f for f in self.c.features}
        self.assertIn("Kolmen ja puolen tuhannen vuoden miekkamestari",
                      feats)
        self.assertEqual(
            feats["Kolmen ja puolen tuhannen vuoden miekkamestari"].mechanic,
            "extra_attack")
        self.assertIn("Terälaulu (Bladesong)", feats)
        self.assertIn("Terälaulu (Bladesong)",
                      {a.name for a in self.c.bonus_actions})
        self.assertTrue(any(i.slot == "main_hand" for i in self.c.items))

    def test_soul_machine_absorbs_damage_in_aterterra(self):
        feats = {f.name: f for f in self.c.features}
        self.assertIn("Vanqurionin sielukone", feats)
        desc = feats["Vanqurionin sielukone"].description
        self.assertIn("ATERTERRASSA", desc)
        self.assertIn("5 siirtoa", desc)
        self.assertIn("Sielukoneen siirto",
                      {a.name for a in self.c.reactions})

    def test_crown_of_tarquvas(self):
        feats = {f.name: f for f in self.c.features}
        crown = feats["Tarquvasin kruunu"]
        self.assertEqual(crown.aura_radius, 60)
        self.assertEqual(crown.save_dc, 25)
        self.assertEqual(crown.applies_condition, "Frightened")
        memory = next(a for a in self.c.actions
                      if a.name == "Tarquvasin kruunu: muisto")
        self.assertEqual(memory.damage_type, "psychic")
        self.assertEqual(memory.applies_condition, "Stunned")
        self.assertTrue(any("kruunu" in i.name.lower()
                            for i in self.c.items))

    def test_soul_burst_bypasses_immunity(self):
        burst = next(a for a in self.c.actions
                     if a.name == "Sielujen purkaus")
        self.assertEqual(burst.damage_dice, "10d10")
        self.assertEqual(burst.damage_type, "necrotic")
        self.assertEqual(burst.aoe_radius, 60)
        self.assertEqual(burst.condition_dc, 25)
        self.assertIn("immuniteetin", burst.description)

    def test_mythic_trait_is_foresight_and_extra_reactions(self):
        feats = {f.name: f for f in self.c.features}
        myth = feats["Foresight (Mythic Trait)"]
        self.assertEqual(myth.phase_trigger_hp_pct, 0.5)
        self.assertIn("3 YLIMÄÄRÄISTÄ REAKTIOTA", myth.description)
        self.assertIn("Foresight", myth.phase_description)

    def test_signature_spells_present(self):
        known = {s.name for s in self.c.spells_known}
        for name in ("Time Stop", "Meteor Swarm", "Feeblemind",
                     "Imprisonment", "Foresight", "Counterspell",
                     "Shield", "Dispel Magic", "Misty Step",
                     "Power Word Kill", "Forcecage"):
            self.assertIn(name, known, name)

    def test_all_referenced_spells_exist(self):
        for s in list(self.c.spells_known) + list(self.c.cantrips):
            self.assertTrue(has_spell(s.name), s.name)

    def test_lore_explains_she_did_not_win_alone(self):
        for bit in ("3 500", "sielukone", "Esmer", "Dimerius", "kruunun"):
            self.assertIn(bit, self.c.lore)

    def test_legendary_and_lair_actions(self):
        self.assertEqual(self.c.legendary_action_count, 3)
        self.assertEqual(self.c.legendary_resistance_count, 5)
        self.assertGreaterEqual(
            len([f for f in self.c.features
                 if f.feature_type == "legendary"]), 3)
        self.assertGreaterEqual(
            len([f for f in self.c.features if f.feature_type == "lair"]), 2)


class TestNewSpellsInLibrary(unittest.TestCase):
    """Imprisonment ja Foresight puuttuivat kirjastosta; molemmat ovat
    keskeisiä juuri näille kahdelle hahmolle."""

    def test_imprisonment(self):
        sp = get_spell("Imprisonment")
        self.assertEqual(sp.level, 9)
        self.assertEqual(sp.save_ability, "Wisdom")
        self.assertFalse(sp.repeat_save)
        self.assertIn("Cazna", sp.description)

    def test_foresight(self):
        sp = get_spell("Foresight")
        self.assertEqual(sp.level, 9)
        self.assertEqual(sp.duration, "8 hours")
        # ei ehtoa jota moottori ei tunne
        self.assertEqual(sp.applies_condition, "")

    def test_faerie_fire_outlines_for_real(self):
        """Faerie Fire julisti ehdon "Outlined" jota ei ollut määritelty,
        joten sen koko pointti (etu kaikkiin hyökkäyksiin kohdetta
        vastaan) ei tehnyt mitään."""
        from data.conditions import CONDITIONS, CONDITION_EFFECTS
        self.assertEqual(get_spell("Faerie Fire").applies_condition,
                         "Outlined")
        self.assertIn("Outlined", CONDITIONS)
        self.assertTrue(
            CONDITION_EFFECTS["Outlined"].get("attacked_advantage"))

    def test_bane_uses_the_active_effect_path(self):
        """Bane julisti ehdon "Baned", joten resolveri haarautui ehtoihin
        eikä koskaan asettanut active_effects["Bane"] -arvoa — -1d4 ei
        siis vaikuttanut mihinkään."""
        from engine.entities import Entity as _E
        from data.models import CreatureStats as _CS
        self.assertEqual(get_spell("Bane").applies_condition, "")
        self.assertEqual(get_spell("Bane").save_ability, "Charisma")
        e = _E(_CS(name="Target"), 0, 0, is_player=False)
        base = e.get_attack_bonus_effects()
        e.active_effects["Bane"] = 10
        self.assertLess(e.get_attack_bonus_effects(), base + 1)

    def test_no_spell_declares_an_unknown_condition(self):
        from data.conditions import CONDITIONS
        import data.spells as spells_mod
        for name, sp in spells_mod._spells.items():
            if sp.applies_condition:
                self.assertIn(sp.applies_condition, CONDITIONS, name)


class TestRelativePower(unittest.TestCase):
    def test_tarquvas_outranks_cazna_who_outranks_dimerius(self):
        t = library.get_monster("Keisari Tarquvas Redfei")
        c = library.get_monster("Cazna Icharyd")
        d = library.get_monster("Lordi Dimerius Blackfeet")
        self.assertGreater(t.challenge_rating, c.challenge_rating)
        self.assertGreater(c.challenge_rating, d.challenge_rating)
        self.assertGreater(t.hit_points, c.hit_points)

    def test_both_are_above_the_normal_cr20_ceiling(self):
        for name in ("Keisari Tarquvas Redfei", "Cazna Icharyd"):
            self.assertGreater(library.get_monster(name).challenge_rating,
                               20.0)
            self.assertEqual(library.get_monster(name).proficiency_bonus, 8)

    def test_they_top_every_campaign_boss(self):
        """Vain Tarrasque (CR 30, monsterikirjan katto) on Tarquvasin
        yläpuolella, ja kumpikaan kampanjan omista bosseista ei ohita
        näitä kahta."""
        all_m = library.get_all_monsters()
        higher_than_tarquvas = [m.name for m in all_m
                                if m.challenge_rating > 28.0]
        self.assertEqual(higher_than_tarquvas, ["Tarrasque"])
        campaign_bosses = ("Lordi Dimerius Blackfeet", "Thalgrum",
                           "Aurelia Valtar", "Xalars", "Golbera",
                           "Dantrag Dyrr")
        for name in campaign_bosses:
            self.assertLess(library.get_monster(name).challenge_rating,
                            26.0, name)


class TestAiRunsBothLegends(unittest.TestCase):
    def _battle(self):
        pcs = [Entity(_hero(n), 3, 3 + i, is_player=True)
               for i, n in enumerate(["Magnus Dragonius", "Balthazar",
                                      "Venris Galanodel",
                                      "Padak Onslaught"])]
        foes = [Entity(library.get_monster(n), 14, 4 + i * 2,
                       is_player=False)
                for i, n in enumerate(["Keisari Tarquvas Redfei",
                                       "Cazna Icharyd"])]
        b = BattleSystem(log_callback=lambda s: None,
                         initial_entities=pcs + foes)
        b.start_combat()
        return b, pcs, foes

    def test_ai_plans_a_turn_for_each(self):
        b, _pcs, foes = self._battle()
        ai = TacticalAI()
        for e in foes:
            e.reset_turn()
            plan = ai.calculate_turn(e, b)
            self.assertIsNotNone(plan, e.name)
            self.assertTrue(plan.steps, e.name)

    def test_save_based_aoe_bonus_action_is_not_an_attack_roll(self):
        """Titaanin harppaus on 15 ft purskaus DC 26 STR -pelastuksella.
        Ennen korjausta AI heitti sille osumaheiton +0 vs AC, joten se
        meni käytännössä aina ohi."""
        b, _pcs, foes = self._battle()
        tarquvas = foes[0]
        tarquvas.reset_turn()
        step = TacticalAI()._aoe_bonus_action_step(
            tarquvas,
            next(a for a in tarquvas.stats.bonus_actions
                 if a.name == "Titaanin harppaus"),
            [e for e in b.entities if e.is_player],
            [e for e in b.entities if not e.is_player], b)
        self.assertIsNotNone(step)
        self.assertEqual(step.step_type, "bonus_attack")
        self.assertEqual(step.save_dc, 26)
        self.assertEqual(step.save_ability, "Strength")
        self.assertEqual(step.applies_condition, "Prone")
        self.assertTrue(step.targets)
        self.assertEqual(step.attack_roll, 0)      # ei osumaheittoa

    def test_auto_battle_terminates(self):
        random.seed(5)
        pcs = [Entity(_hero(n), 3 + (i % 3), 3 + i, is_player=True)
               for i, n in enumerate(["Magnus Dragonius", "Balthazar",
                                      "Venris Galanodel",
                                      "Padak Onslaught", "Krusk"])]
        foes = [Entity(library.get_monster(n), 16, 5 + i * 3,
                       is_player=False)
                for i, n in enumerate(["Keisari Tarquvas Redfei",
                                       "Cazna Icharyd"])]
        bs = BattleState(_FM(), entities=pcs + foes)
        bs._set_ai_mode("full_auto")
        # Choosing a mode no longer rolls initiative behind the
        # DM\'s back — deployment stays inert until START COMBAT.
        if not bs.battle.combat_started:
            bs.battle.start_combat()
        for _ in range(2500):
            bs._process_auto_battle()
            if (not [e for e in bs.battle.entities
                     if e.is_player and e.hp > 0]
                    or not [e for e in bs.battle.entities
                            if not e.is_player and e.hp > 0]):
                break
        else:
            self.fail("auto-battle ei päättynyt 2500 askeleessa")
        # CR 26 + CR 28 vs tason 12 ryhmä: bossit voittavat, kuten lore
        # kertoo — Caznan tarvitsi liiton, petoksen ja sielun vangitsemisen.
        self.assertTrue([e for e in foes if e.hp > 0])


class TestRelentlessEnduranceConsumesItsUse(unittest.TestCase):
    """Regressio: Krusk-lehden Relentless Endurance ei kuluttanut
    käyttöään, joten hän pysähtyi ikuisesti 1 HP:hen — auto-battle ei
    voinut päättyä koskaan."""

    def _krusk(self):
        return Entity(_hero("Krusk"), 3, 3, is_player=True)

    def test_first_hit_drops_to_one_hp(self):
        k = self._krusk()
        k.take_damage(k.hp, "slashing")          # exactly to 0
        self.assertEqual(k.hp, 1)

    def test_second_hit_actually_kills(self):
        k = self._krusk()
        k.take_damage(k.hp, "slashing")
        self.assertEqual(k.hp, 1)
        k.take_damage(k.hp, "slashing")          # no uses left
        self.assertLessEqual(k.hp, 0)

    def test_massive_damage_still_kills_outright(self):
        """PHB: damage that exceeds max HP past 0 is instant death and
        Relentless Endurance does not apply."""
        k = self._krusk()
        k.take_damage(10_000, "slashing")
        self.assertLess(k.hp, 0)

    def test_sheet_declares_one_use_per_long_rest(self):
        feat = next(f for f in _hero("Krusk").features
                    if f.name == "Relentless Endurance")
        self.assertEqual(feat.uses_per_day, 1)

    def test_works_even_if_a_sheet_forgets_uses_per_day(self):
        """Moottori ei enää luota pelkkään dataan."""
        from data.models import CreatureStats, AbilityScores, Feature
        stats = CreatureStats(
            name="Half-Orc Test", hit_points=30,
            abilities=AbilityScores(constitution=14),
            features=[Feature("Relentless Endurance", "",
                              mechanic="relentless_endurance")])
        e = Entity(stats, 0, 0, is_player=False)
        e.take_damage(e.hp, "slashing")
        self.assertEqual(e.hp, 1)
        e.take_damage(e.hp, "slashing")
        self.assertLessEqual(e.hp, 0)


class TestWiredIntoTheCampaign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cm = CampaignManagerState(_FM(), build_novus_somnium())

    def test_both_have_npc_sheets(self):
        for nid, src in (("npc_tarquvas",
                          "monster:Keisari Tarquvas Redfei"),
                         ("npc_cazna", "monster:Cazna Icharyd")):
            npc = self.cm.world.npcs.get(nid)
            self.assertIsNotNone(npc, nid)
            self.assertEqual(npc.stat_source, src)
            self.assertIsNotNone(self.cm._get_npc_stats(npc), nid)

    def test_tarquvas_appearance_records_sword_and_armour(self):
        npc = self.cm.world.npcs["npc_tarquvas"]
        low = npc.appearance.lower()
        self.assertIn("obsidiaanin", low)
        self.assertIn("haarniska", low)
        self.assertIn("faerzress", low)

    def test_the_two_are_linked_as_enemies(self):
        from data import npc_directory as nd
        links = {(l["target_id"], l["kind"])
                 for l in nd.npc_links_of(self.cm.world, "npc_cazna")}
        self.assertIn(("npc_tarquvas", "enemy"), links)
        back = {(l["target_id"], l["kind"])
                for l in nd.npc_links_of(self.cm.world, "npc_tarquvas")}
        self.assertIn(("npc_cazna", "enemy"), back)
        self.assertIn(("npc_dimerius", "enemy"), back)

    def test_no_npc_left_without_stats(self):
        broken = [(n.name, n.stat_source)
                  for n in self.cm.world.npcs.values()
                  if n.stat_source and self.cm._get_npc_stats(n) is None]
        self.assertEqual(broken, [])

    def test_codex_has_a_character_article_for_each(self):
        for key in ("tarquvas_redfei", "cazna_icharyd"):
            e = codex.get_entry(key)
            self.assertIsNotNone(e, key)
            self.assertEqual(e.category, "hahmot")
            self.assertTrue(e.spoiler)
        self.assertIn("hahmot", codex.categories())

    def test_codex_explains_how_cazna_won(self):
        e = codex.get_entry("tarquvas_vs_cazna")
        self.assertIsNotNone(e)
        for bit in ("LIITTOUMA", "PETOS", "KIDUTUKSEN"):
            self.assertIn(bit, e.body)

    def test_codex_is_searchable_by_what_the_dm_would_type(self):
        cases = {
            "tarquvas": "tarquvas_redfei",
            "cazna": "cazna_icharyd",
            "matriarkka": "cazna_icharyd",
            "obsidiaanimiekka": "tarquvas_redfei",
            "sielukone": "cazna_icharyd",
            "terälaulu": "cazna_icharyd",
            "cr 28": "tarquvas_redfei",
            "miten voitti": "tarquvas_vs_cazna",
        }
        for query, expected in cases.items():
            keys = [h.key for h in codex.search(query)[:3]]
            self.assertIn(expected, keys, f"{query!r} -> {keys}")

    def test_codex_articles_reach_the_right_sheets(self):
        keys = {e.key for e in codex.entries_for_npc("npc_tarquvas")}
        self.assertTrue({"tarquvas_redfei", "tarquvas_vs_cazna"} <= keys)
        keys = {e.key for e in codex.entries_for_npc("npc_cazna")}
        self.assertIn("cazna_icharyd", keys)

    def test_codex_cross_links_all_resolve(self):
        for key in ("tarquvas_redfei", "cazna_icharyd",
                    "tarquvas_vs_cazna"):
            e = codex.get_entry(key)
            for other in e.see_also:
                self.assertIsNotNone(codex.get_entry(other),
                                     f"{key} -> {other}")
            for nid in e.npc_ids:
                self.assertIn(nid, self.cm.world.npcs, f"{key} -> {nid}")
            for lid in e.location_ids:
                self.assertIn(lid, self.cm.world.locations,
                              f"{key} -> {lid}")

    def test_stat_sheet_modal_renders_both(self):
        screen = pygame.display.get_surface()
        for nid in ("npc_tarquvas", "npc_cazna"):
            self.cm._open_monster_lore(self.cm.world.npcs[nid])
            screen.fill((0, 0, 0))
            self.cm._monster_lore_modal.draw(screen)


if __name__ == "__main__":
    unittest.main()
