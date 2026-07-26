"""Lore Codex — maailmanlore on löydettävissä sekunneissa.

Kampanjan kosmologia (Garrutha, Vendilit, Kristallikupu, Veru, Tarquvas)
ei mahdu litteään muistiinpanolistaan, joten se on rakenteisena codexina.
Tämä testi varmistaa että

  * artikkelit ovat olemassa ja niillä on tiivistelmä + leipäteksti,
  * haku löytää oikean artikkelin niillä sanoilla joita pelinjohtaja
    pöydässä kirjoittaa,
  * kaikki ristiviittaukset (see_also / npc_ids / location_ids)
    osoittavat todellisiin kohteisiin — ei kuolleita linkkejä,
  * selain-modaali avautuu, suodattuu, valitsee ja tuottaa klikattavat
    linkit NPC:ihin ja paikkoihin,
  * codex on kytketty kampanjanäkymään (napit + modaalin reititys).
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

from data import lore_codex as codex
from data.novus_somnium import build_novus_somnium
from states.campaign_manager import CampaignManagerState
from states.lore_codex_modal import LoreCodexModal


class _FM:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.running = True
        self.states = {}

    def change_state(self, *a, **k):
        pass


class TestCodexContent(unittest.TestCase):
    def test_entries_exist_and_are_written(self):
        entries = codex.all_entries()
        self.assertGreaterEqual(len(entries), 12)
        for e in entries:
            self.assertTrue(e.key, e.title)
            self.assertTrue(e.title)
            self.assertGreater(len(e.summary), 20, e.key)
            self.assertGreater(len(e.body), 200, e.key)
            self.assertIn(e.category, codex.CATEGORIES, e.key)
            self.assertTrue(e.keywords, e.key)

    def test_keys_unique(self):
        keys = [e.key for e in codex.all_entries()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_core_cosmology_present(self):
        for key in ("garrutha", "vendilit", "kristallikupu", "veru",
                    "clavise", "tarquvas"):
            self.assertIsNotNone(codex.get_entry(key), key)

    def test_categories_are_ordered_and_present(self):
        cats = codex.categories()
        self.assertIn("kosmologia", cats)
        self.assertEqual(cats, [c for c in codex.CATEGORIES if c in cats])
        for c in cats:
            self.assertTrue(codex.by_category(c))

    def test_secrets_flagged_as_spoilers(self):
        """Titaanin tila ja Verun juoni ovat pelaajilta salassa."""
        self.assertTrue(codex.get_entry("garrutha").spoiler)
        self.assertTrue(codex.get_entry("veru").spoiler)


class TestCodexSearch(unittest.TestCase):
    def test_finds_by_the_words_a_dm_types(self):
        cases = {
            "garrutha": "garrutha",
            "titaani": "garrutha",
            "kupu": "kristallikupu",
            "clavise": "clavise",
            "veru": "veru",
            "tarquvas": "tarquvas",
        }
        for query, expected in cases.items():
            hits = codex.search(query)
            self.assertTrue(hits, query)
            self.assertIn(expected, [h.key for h in hits[:3]],
                          f"{query!r} -> {[h.key for h in hits[:3]]}")

    def test_title_beats_body_mention(self):
        hits = codex.search("garrutha")
        self.assertEqual(hits[0].key, "garrutha")

    def test_empty_query_lists_everything(self):
        self.assertEqual(len(codex.search("")), len(codex.all_entries()))

    def test_category_filter(self):
        hits = codex.search("", category="kosmologia")
        self.assertTrue(hits)
        self.assertTrue(all(h.category == "kosmologia" for h in hits))

    def test_multi_word_query_ranks_the_overlap_first(self):
        hits = codex.search("kristallikupu veru")
        self.assertTrue(hits)
        self.assertIn(hits[0].key, ("kristallikupu", "veru"))

    def test_unknown_query_returns_nothing(self):
        self.assertEqual(codex.search("xyzzy-ei-olemassa"), [])

    def test_case_insensitive(self):
        self.assertEqual([e.key for e in codex.search("GARRUTHA")],
                         [e.key for e in codex.search("garrutha")])


class TestCodexCrossLinks(unittest.TestCase):
    """No dead links: every id must resolve in the real campaign world."""

    @classmethod
    def setUpClass(cls):
        cls.cm = CampaignManagerState(_FM(), build_novus_somnium())
        cls.world = cls.cm.world

    def test_see_also_targets_exist(self):
        for e in codex.all_entries():
            for key in e.see_also:
                self.assertIsNotNone(codex.get_entry(key),
                                     f"{e.key} -> see_also {key}")

    def test_npc_ids_exist(self):
        for e in codex.all_entries():
            for nid in e.npc_ids:
                self.assertIn(nid, self.world.npcs, f"{e.key} -> {nid}")

    def test_location_ids_exist(self):
        for e in codex.all_entries():
            for lid in e.location_ids:
                self.assertIn(lid, self.world.locations, f"{e.key} -> {lid}")

    def test_reverse_lookup_from_a_character(self):
        keys = [e.key for e in codex.entries_for_npc("npc_krusk")]
        self.assertIn("kruskin_valinta", keys)

    def test_reverse_lookup_from_a_place(self):
        self.assertTrue(codex.entries_for_location("loc_ravenstone"))

    def test_reverse_lookup_unknown_id_is_empty(self):
        self.assertEqual(codex.entries_for_npc("npc_ei_ole"), [])
        self.assertEqual(codex.entries_for_location("loc_ei_ole"), [])

    def test_every_article_is_reachable_from_somewhere(self):
        """Jokainen artikkeli löytyy joko ristiviittauksella tai
        NPC-/paikkakytkennällä — mikään ei jää orvoksi."""
        linked = set()
        for e in codex.all_entries():
            linked.update(e.see_also)
        for e in codex.all_entries():
            reachable = (e.key in linked or e.npc_ids or e.location_ids)
            self.assertTrue(reachable, f"{e.key} on saavuttamaton")


class TestCodexNotesMirror(unittest.TestCase):
    def test_as_campaign_notes(self):
        notes = codex.as_campaign_notes()
        self.assertEqual(len(notes), len(codex.all_entries()))
        for n in notes:
            self.assertEqual(n.category, "lore")
            self.assertTrue(n.text)

    def test_spoilers_are_marked_in_notes(self):
        notes = {n.text.split("—")[0] for n in codex.as_campaign_notes()}
        self.assertTrue(any("[SPOILER]" in t for t in notes))

    def test_mirror_into_campaign_is_idempotent(self):
        cm = CampaignManagerState(_FM(), build_novus_somnium())
        before = len(cm.campaign.notes)
        cm._mirror_codex_to_notes()
        after = len(cm.campaign.notes)
        self.assertEqual(after, before + len(codex.all_entries()))
        cm._mirror_codex_to_notes()          # second press adds nothing
        self.assertEqual(len(cm.campaign.notes), after)


class TestCodexModal(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())
        self.opened_npc = []
        self.opened_loc = []
        self.modal = LoreCodexModal(
            self.cm.world, self.cm.campaign,
            on_open_npc=self.opened_npc.append,
            on_open_location=self.opened_loc.append)
        self.screen = pygame.display.get_surface()

    def _frame(self):
        self.screen.fill((0, 0, 0))
        self.modal.draw(self.screen)

    def test_opens_with_a_selected_article(self):
        self.modal.open()
        self.assertTrue(self.modal.is_open)
        self.assertIsNotNone(self.modal.entry())

    def test_open_jumps_to_a_named_article(self):
        self.modal.open(entry_key="tarquvas")
        self.assertEqual(self.modal.entry().key, "tarquvas")

    def test_open_ignores_unknown_key(self):
        self.modal.open(entry_key="ei-ole-olemassa")
        self.assertIsNotNone(self.modal.entry())

    def test_draw_does_not_crash_for_every_article(self):
        for e in codex.all_entries():
            self.modal.open(entry_key=e.key)
            self._frame()

    def test_typing_filters_the_list(self):
        self.modal.open()
        self.modal.field_active = True
        for ch in "veru":
            self.modal.handle_event(pygame.event.Event(
                pygame.KEYDOWN, key=ord(ch), unicode=ch))
        self.assertEqual(self.modal.query, "veru")
        self.assertIn("veru", [e.key for e in self.modal._hits()])
        self.modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode=""))
        self.assertEqual(self.modal.query, "ver")

    def test_escape_clears_then_closes(self):
        self.modal.open()
        self.modal.query = "veru"
        esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE,
                                 unicode="\x1b")
        self.modal.handle_event(esc)
        self.assertEqual(self.modal.query, "")
        self.assertTrue(self.modal.is_open)
        self.modal.handle_event(esc)
        self.assertFalse(self.modal.is_open)

    def test_arrow_keys_walk_the_hits(self):
        self.modal.open()
        first = self.modal.entry().key
        self.modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_DOWN, unicode=""))
        self.assertNotEqual(self.modal.entry().key, first)
        self.modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_UP, unicode=""))
        self.assertEqual(self.modal.entry().key, first)

    def test_category_chip_filters(self):
        self.modal.open()
        self._frame()
        chip = next(r for r, cat in self.modal._cat_rects
                    if cat == "kosmologia")
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=chip.center))
        self.assertEqual(self.modal.filter_category, "kosmologia")
        self.assertTrue(all(e.category == "kosmologia"
                            for e in self.modal._hits()))
        # clicking again clears it
        self._frame()
        chip = next(r for r, cat in self.modal._cat_rects
                    if cat == "kosmologia")
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=chip.center))
        self.assertEqual(self.modal.filter_category, "")

    def test_clicking_a_row_opens_that_article(self):
        self.modal.open()
        self._frame()
        self.assertTrue(self.modal._row_rects)
        rect, key = self.modal._row_rects[-1]
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(self.modal.entry().key, key)

    def test_see_also_chip_navigates(self):
        self.modal.open(entry_key="veru")
        self._frame()
        self.assertTrue(self.modal._see_rects)
        rect, key = self.modal._see_rects[0]
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(self.modal.entry().key, key)

    def test_npc_and_location_chips_fire_callbacks(self):
        entry = next(e for e in codex.all_entries()
                     if e.npc_ids and e.location_ids)
        self.modal.open(entry_key=entry.key)
        self._frame()
        rect, npc_id = self.modal._npc_rects[0]
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(self.opened_npc, [npc_id])
        self._frame()
        rect, loc_id = self.modal._loc_rects[0]
        self.modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(self.opened_loc, [loc_id])

    def test_chips_show_real_names_not_ids(self):
        entry = next(e for e in codex.all_entries() if e.npc_ids)
        nid = entry.npc_ids[0]
        self.assertEqual(self.modal._npc_name(nid),
                         self.cm.world.npcs[nid].name)

    def test_spoiler_toggle_hides_secret_articles(self):
        self.modal.open()
        self.modal._toggle_spoilers()
        self.assertFalse(self.modal.show_spoilers)
        self.assertTrue(all(not e.spoiler for e in self.modal._hits()))
        self._frame()          # must still render with nothing selected
        self.modal._toggle_spoilers()
        self.assertTrue(any(e.spoiler for e in self.modal._hits()))

    def test_modal_swallows_events_while_open(self):
        self.modal.open()
        handled = self.modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_d, unicode="d"))
        self.assertTrue(handled)
        self.assertEqual(self.modal.query, "d")

    def test_closed_modal_passes_events_through(self):
        self.assertFalse(self.modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_d, unicode="d")))


class TestCodexWiredIntoCampaign(unittest.TestCase):
    def setUp(self):
        self.cm = CampaignManagerState(_FM(), build_novus_somnium())
        self.screen = pygame.display.get_surface()

    def test_entry_point_buttons_exist(self):
        self.assertTrue(hasattr(self.cm, "btn_lore_codex"))
        self.assertTrue(hasattr(self.cm, "btn_notes_codex"))
        self.assertTrue(hasattr(self.cm, "btn_notes_import_lore"))

    def test_notes_buttons_do_not_overlap(self):
        rects = [self.cm.btn_new_note.rect, self.cm.btn_notes_codex.rect,
                 self.cm.btn_notes_import_lore.rect]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                self.assertFalse(a.colliderect(b), f"{a} vs {b}")

    def test_world_row_buttons_stay_on_screen(self):
        from settings import SCREEN_WIDTH
        self.assertLessEqual(self.cm.btn_lore_codex.rect.right, SCREEN_WIDTH)

    def test_open_and_close_codex(self):
        self.cm._open_lore_codex()
        self.assertTrue(self.cm._lore_codex_open)
        self.cm._lore_codex_modal.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="\x1b"))
        self.assertFalse(self.cm._lore_codex_open)

    def test_open_specific_entry_from_a_sheet(self):
        self.cm._open_codex_from_sheet("kristallikupu")
        self.assertTrue(self.cm._lore_codex_open)
        self.assertEqual(self.cm._lore_codex_modal.entry().key,
                         "kristallikupu")

    def test_codex_intercepts_typing_before_global_hotkeys(self):
        """'D' avaa normaalisti noppalaatikon; codexin hakukentässä se
        on pelkkä kirjain."""
        self.cm._open_lore_codex()
        self.cm._lore_codex_modal.field_active = True
        self.cm.handle_events([pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_d, unicode="d")])
        self.assertEqual(self.cm._lore_codex_modal.query, "d")
        self.assertFalse(self.cm._dice_tray.is_open)

    def test_codex_npc_link_opens_the_character_sheet(self):
        entry = next(e for e in codex.all_entries() if e.npc_ids)
        self.cm._open_lore_codex(entry_key=entry.key)
        self.cm._jump_to_npc_id(entry.npc_ids[0])
        self.assertTrue(self.cm._npc_detail_open)
        self.assertEqual(self.cm._npc_detail_modal.npc.id, entry.npc_ids[0])
        # the codex stepped aside so the sheet is the top-most panel
        self.assertFalse(self.cm._lore_codex_open)

    def test_codex_location_link_jumps_to_the_place(self):
        entry = next(e for e in codex.all_entries() if e.location_ids)
        lid = entry.location_ids[0]
        self.cm._open_lore_codex(entry_key=entry.key)
        self.cm._jump_to_location_id(lid)
        self.assertEqual(self.cm.active_tab, 4)
        self.assertEqual(self.cm.world_view, "locations")
        self.assertEqual(self.cm.selected_location_id, lid)
        self.assertFalse(self.cm._lore_codex_open)

    def test_unknown_link_targets_are_ignored(self):
        self.cm._jump_to_npc_id("npc_ei_ole")
        self.cm._jump_to_location_id("loc_ei_ole")
        self.assertFalse(self.cm._npc_detail_open)

    def test_npc_sheet_shows_why_this_character_matters(self):
        entry = next(e for e in codex.all_entries() if e.npc_ids)
        npc = self.cm.world.npcs[entry.npc_ids[0]]
        self.cm._open_npc_detail(npc)
        self.screen.fill((0, 0, 0))
        self.cm._npc_detail_modal.draw(self.screen)
        keys = {k for _r, k in self.cm._npc_detail_modal._codex_chips}
        self.assertIn(entry.key, keys)

    def test_npc_sheet_codex_chip_opens_the_article(self):
        entry = next(e for e in codex.all_entries() if e.npc_ids)
        npc = self.cm.world.npcs[entry.npc_ids[0]]
        self.cm._open_npc_detail(npc)
        self.screen.fill((0, 0, 0))
        self.cm._npc_detail_modal.draw(self.screen)
        rect, key = self.cm._npc_detail_modal._codex_chips[0]
        self.cm._npc_detail_modal.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertTrue(self.cm._lore_codex_open)
        self.assertEqual(self.cm._lore_codex_modal.entry().key, key)

    def test_location_sheet_renders_codex_chips(self):
        entry = next(e for e in codex.all_entries() if e.location_ids)
        lid = entry.location_ids[0]
        self.cm.active_tab = 4
        self.cm._show_locations_view()
        self.cm.selected_location_id = lid
        self.screen.fill((0, 0, 0))
        y = self.cm._draw_location_codex_links(
            self.screen, (0, 0), 400, 300,
            self.cm.world.locations[lid])
        self.assertGreater(y, 300)          # chips took vertical space

    def test_full_campaign_frame_with_codex_open(self):
        self.cm.active_tab = 4
        self.cm._open_lore_codex(entry_key="garrutha")
        self.screen.fill((0, 0, 0))
        self.cm.draw(self.screen)
        self.cm.active_tab = 3
        self.screen.fill((0, 0, 0))
        self.cm.draw(self.screen)


if __name__ == "__main__":
    unittest.main()
