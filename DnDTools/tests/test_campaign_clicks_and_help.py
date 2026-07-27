"""Kampanjanäkymän klikkaukset, paluu taistelusta ja suomenkieliset
selitteet.

Klikkauskohdat laskettiin kahdesti: kerran piirrettäessä ja kerran
klikkiä käsiteltäessä. Ne erosivat toisistaan joka välilehdellä, ja
ryhmäsuodattimen päällä ollessa jokainen sankariklikkaus valitsi väärän
hahmon. Nyt piirto kirjaa rivit ja klikkaus lukee ne.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import unittest

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from data.campaign import (Campaign, PartyMember, PartyGroup,
                           CampaignEncounter, CampaignArea,
                           CampaignNote)
from data.heroes import hero_list
from data.spells import get_spell
from data.library import library
from data.models import Item
from data.ability_help_fi import (explain_spell, explain_action,
                                  explain_feature, explain_item, explain_any,
                                  explain_condition)
from states.campaign_manager import CampaignManagerState


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}
        self.changed_to = None

    def change_state(self, name, **kw):
        self.changed_to = (name, kw)


def _member(h, group=""):
    return PartyMember(hero_data={
        "name": h.name, "character_class": h.character_class,
        "character_level": h.character_level, "race": h.race,
        "hit_points": h.hit_points, "armor_class": h.armor_class},
        group_id=group)


def _campaign(n=8, groups=False):
    c = Campaign(name="Novus Somnium", created="now")
    if groups:
        c.party_groups = [PartyGroup(id="g1", name="Aterterra"),
                          PartyGroup(id="g2", name="Maclebar")]
    for i, h in enumerate(hero_list[:n]):
        c.party.append(_member(h, ("g1" if i < n // 2 else "g2")
                               if groups else ""))
    return c


def _state(c):
    st = CampaignManagerState(_FM(), c)
    return st


# ===================================================================== #
# 1. EVERY LIST ROW ANSWERS THE CLICK THAT LANDS ON IT
# ===================================================================== #
class TestPartyRowClicks(unittest.TestCase):

    def _check(self, st, key, click, read):
        screen = pygame.display.get_surface()
        st.draw(screen)
        rows = st._row_hits.get(key, [])
        self.assertTrue(rows, f"{key}: yhtään riviä ei kirjattu")
        for rect, i in rows:
            read_reset = click(st, rect.center)
            self.assertEqual(read(st), i,
                             f"{key}: rivin {i} klikkaus valitsi "
                             f"{read(st)}")
        return len(rows)

    def test_party_rows_select_the_hero_under_the_cursor(self):
        st = _state(_campaign(8))
        st.active_tab = 0
        n = self._check(st, "party",
                        lambda s, p: s._handle_party_click(p),
                        lambda s: s.selected_member_idx)
        self.assertEqual(n, 8)

    def test_party_rows_are_right_with_a_group_filter_on(self):
        # The screenshot's case: eleven heroes, one group of five shown.
        # The click handler used to count the hidden six as well, so
        # every row picked somebody else entirely.
        c = _campaign(10, groups=True)
        c.active_group_id = "g2"
        st = _state(c)
        st.active_tab = 0
        visible = st._visible_party_indices()
        self.assertLess(len(visible), len(c.party), "suodatin ei suodata")
        n = self._check(st, "party",
                        lambda s, p: s._handle_party_click(p),
                        lambda s: s.selected_member_idx)
        self.assertEqual(n, len(visible))

    def test_party_rows_are_right_after_scrolling(self):
        st = _state(_campaign(8))
        st.active_tab = 0
        st.scroll_y = -120
        self._check(st, "party",
                    lambda s, p: s._handle_party_click(p),
                    lambda s: s.selected_member_idx)

    def test_encounter_rows_select_the_right_encounter(self):
        c = _campaign(2)
        for i in range(5):
            c.encounters.append(CampaignEncounter(name=f"Kohtaaminen {i}"))
        st = _state(c)
        st.active_tab = 1
        self._check(st, "encounters",
                    lambda s, p: s._handle_encounter_click(p),
                    lambda s: s.selected_encounter_idx)

    def test_area_rows_select_the_right_area(self):
        c = _campaign(2)
        for i in range(5):
            c.areas.append(CampaignArea(name=f"Alue {i}"))
        st = _state(c)
        st.active_tab = 2
        self._check(st, "areas",
                    lambda s, p: s._handle_area_click(p),
                    lambda s: s.selected_area_idx)

    def test_note_rows_open_the_note_under_the_cursor(self):
        c = _campaign(2)
        for i in range(4):
            c.notes.append(CampaignNote(text=f"Muistiinpano {i}"))
        st = _state(c)
        st.active_tab = 3
        screen = pygame.display.get_surface()
        st.draw(screen)
        for rect, i in st._row_hits.get("notes", []):
            st.modal = None
            st._handle_notes_click(rect.center)
            self.assertEqual(st.modal, ("edit_note", i))
            self.assertEqual(st.input_text, c.notes[i].text)

    def test_a_click_in_empty_space_selects_nothing_new(self):
        st = _state(_campaign(3))
        st.active_tab = 0
        st.draw(pygame.display.get_surface())
        st.selected_member_idx = 1
        st._handle_party_click((1900, 1050))
        self.assertEqual(st.selected_member_idx, 1)

    def test_rows_are_not_carried_over_between_frames(self):
        st = _state(_campaign(6))
        st.active_tab = 0
        screen = pygame.display.get_surface()
        counts = []
        for _ in range(5):
            st.draw(screen)
            counts.append(len(st._row_hits.get("party", [])))
        self.assertEqual(len(set(counts)), 1, counts)


# ===================================================================== #
# 2. BACK TO THE SAME CAMPAIGN
# ===================================================================== #
class TestReturningToTheCampaign(unittest.TestCase):
    """Encounterista palaaminen rakensi kampanjanäkymän uudestaan ilman
    kampanjaa, eli tilalle tuli tyhjä 'New Campaign'."""

    def _manager(self):
        import main
        mgr = object.__new__(main.GameManager)
        mgr.states = {"MENU": object(), "CAMPAIGN": None, "BATTLE": None}
        mgr.current_state = mgr.states["MENU"]
        mgr.error_banner = ""
        return mgr

    def test_an_open_campaign_is_not_rebuilt(self):
        mgr = self._manager()
        live = _state(_campaign(3))
        live.campaign.name = "Novus Somnium"
        mgr.states["CAMPAIGN"] = live
        mgr.change_state("CAMPAIGN")
        self.assertIs(mgr.states["CAMPAIGN"], live,
                      "kampanjanäkymä rakennettiin uudestaan")
        self.assertIs(mgr.current_state, live)
        self.assertEqual(live.campaign.name, "Novus Somnium")

    def test_the_party_survives_the_round_trip(self):
        mgr = self._manager()
        live = _state(_campaign(4))
        mgr.states["CAMPAIGN"] = live
        before = [m.hero_data["name"] for m in live.campaign.party]
        mgr.change_state("CAMPAIGN")
        after = [m.hero_data["name"]
                 for m in mgr.states["CAMPAIGN"].campaign.party]
        self.assertEqual(before, after)

    def test_opening_a_named_campaign_still_builds_a_fresh_screen(self):
        mgr = self._manager()
        old = _state(_campaign(2))
        mgr.states["CAMPAIGN"] = old
        other = _campaign(3)
        other.name = "Toinen kampanja"
        mgr.change_state("CAMPAIGN", campaign=other)
        self.assertIsNot(mgr.states["CAMPAIGN"], old)
        self.assertEqual(mgr.states["CAMPAIGN"].campaign.name,
                         "Toinen kampanja")

    def test_the_battle_asks_for_the_campaign_by_name(self):
        import copy
        from engine.entities import Entity
        from states.battle_state import BattleState
        fm = _FM()
        live = _state(_campaign(2))
        fm.states["CAMPAIGN"] = live
        ents = [Entity(copy.deepcopy(hero_list[0]), 3.0, 3.0, True),
                Entity(copy.deepcopy(library.get_monster("Ogre")),
                       9.0, 3.0, False)]
        bs = BattleState(fm, entities=ents, return_state="CAMPAIGN")
        bs._return_to_campaign()
        self.assertEqual(fm.changed_to[0], "CAMPAIGN")
        self.assertEqual(fm.changed_to[1], {},
                         "paluu ei saa antaa campaign-argumenttia — se "
                         "pakottaisi uudelleenrakennuksen")

    def test_a_missing_campaign_falls_back_to_the_menu(self):
        import copy
        from engine.entities import Entity
        from states.battle_state import BattleState
        fm = _FM()
        ents = [Entity(copy.deepcopy(hero_list[0]), 3.0, 3.0, True)]
        bs = BattleState(fm, entities=ents, return_state="CAMPAIGN")
        bs._return_to_campaign()
        self.assertEqual(fm.changed_to[0], "MENU")


# ===================================================================== #
# 3. FINNISH RULE NOTES ON HOVER
# ===================================================================== #
class TestFinnishHelp(unittest.TestCase):

    def test_a_spell_explains_save_condition_and_concentration(self):
        txt = explain_spell(get_spell("Hold Person"))
        self.assertIn("2. tason loitsu", txt)
        self.assertIn("Kantama", txt)
        self.assertIn("Paralyzed", txt)
        self.assertIn("KESKITTYMINEN", txt)
        # And the condition's own rules, not just its name.
        self.assertIn("Halvaantunut", txt)

    def test_an_area_spell_explains_the_area_and_half_damage(self):
        txt = explain_spell(get_spell("Fireball"))
        self.assertIn("pallo", txt)
        self.assertIn("Ketteryys (DEX)", txt)
        self.assertIn("puolet", txt)
        self.assertIn("8d6", txt)

    def test_upcasting_is_spelled_out(self):
        txt = explain_spell(get_spell("Fireball"))
        self.assertIn("Korkeammalla paikalla", txt)

    def test_a_healing_spell_says_how_much(self):
        txt = explain_spell(get_spell("Cure Wounds"))
        self.assertIn("Parannus", txt)

    def test_a_summon_spell_names_what_it_summons(self):
        txt = explain_spell(get_spell("Spiritual Weapon"))
        self.assertIn("Kutsuu", txt)

    def test_every_spell_in_the_library_explains_itself(self):
        import data.spells as lib
        empty = []
        for name in lib._spells:
            txt = explain_spell(lib._spells[name])
            if len(txt.strip()) < 30:
                empty.append(name)
        self.assertEqual(empty, [],
                         "näille loitsuille ei synny selitettä")

    def test_the_generated_lines_have_no_gaps_from_missing_data(self):
        # Only the lines this module builds — the stat block's own
        # English description is quoted verbatim at the end and is not
        # ours to tidy. A double space in OUR text means a field came
        # back empty and was interpolated anyway.
        import data.spells as lib
        bad = []
        for name, sp in lib._spells.items():
            generated = explain_spell(sp).split("\n\n", 1)[0]
            for line in generated.split("\n"):
                # "   → ..." continuation lines are indented on purpose.
                if "  " in line.lstrip():
                    bad.append(f"{name}: {line}")
        self.assertEqual(bad, [])

    def test_an_item_explains_its_slot_and_attunement(self):
        it = Item(name="Douk", item_type="weapon", rarity="rare",
                  requires_attunement=True, slot="main_hand",
                  weapon_damage_dice="2d8", weapon_damage_type="piercing",
                  weapon_range=30)
        txt = explain_item(it)
        self.assertIn("harvinainen", txt)
        self.assertIn("virittämisen", txt)
        self.assertIn("lävistävä", txt)
        self.assertIn("pääkäsi", txt)

    def test_actions_and_features_still_explain_themselves(self):
        blitz = next(h for h in hero_list if "Blitz" in h.name) \
            if any("Blitz" in h.name for h in hero_list) else None
        stats = blitz or hero_list[0]
        for act in stats.actions:
            self.assertTrue(explain_action(act).strip(), act.name)
        for feat in stats.features:
            self.assertTrue(explain_feature(feat).strip(), feat.name)

    def test_explain_any_routes_by_type(self):
        self.assertIn("loitsu", explain_any(get_spell("Fireball")))
        self.assertIn("Tyyppi", explain_any(hero_list[0].actions[-1]))
        self.assertTrue(explain_any(hero_list[0].features[0]).strip())
        self.assertIn("Kaatunut", explain_any("Prone"))

    def test_every_condition_the_game_can_apply_has_finnish_rules(self):
        from data.conditions import CONDITIONS
        missing = [c for c in CONDITIONS if not explain_condition(c)]
        self.assertEqual(missing, [],
                         "näille tiloille puuttuu suomenkielinen selite")


if __name__ == "__main__":
    unittest.main()
