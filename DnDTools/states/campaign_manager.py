"""
Campaign Manager State — Off-combat DM tool for managing party, encounters, and areas.

Features:
- Party overview with passive abilities and day/night effects
- DM notes per hero and campaign
- Encounter builder with NPC/monster selection and loot
- Area management with lighting conditions
- Quick transition to combat from any encounter
- Full campaign save/load
"""
import pygame
import os
import copy
import re
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, Panel, fonts, TabBar, Badge, Divider, draw_gradient_rect
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores
from data.heroes import hero_list
from data.hero_import import export_hero, import_hero, import_heroes_from_file
from data.library import library
from data.campaign import (
    Campaign, PartyMember, CampaignEncounter, EncounterSlot,
    CampaignArea, CampaignNote, save_campaign, load_campaign,
    list_campaigns, CAMPAIGNS_DIR, _timestamp,
)


# ============================================================================
# Passive Ability Helpers
# ============================================================================

def _get_passive_perception(stats: CreatureStats) -> int:
    """PHB p.175: 10 + all modifiers that apply."""
    base = 10 + stats.abilities.get_mod("wisdom")
    bonus = stats.skills.get("Perception", 0)
    if bonus:
        # Skills dict already includes proficiency + ability mod
        base = 10 + bonus
    return base

def _get_passive_investigation(stats: CreatureStats) -> int:
    base = 10 + stats.abilities.get_mod("intelligence")
    bonus = stats.skills.get("Investigation", 0)
    if bonus:
        base = 10 + bonus
    return base

def _get_passive_insight(stats: CreatureStats) -> int:
    base = 10 + stats.abilities.get_mod("wisdom")
    bonus = stats.skills.get("Insight", 0)
    if bonus:
        base = 10 + bonus
    return base

def _get_darkvision(stats: CreatureStats) -> int:
    """Get darkvision range from racial traits, features, or senses."""
    # Check racial traits
    for rt in stats.racial_traits:
        if getattr(rt, 'mechanic', '') == "darkvision":
            val = getattr(rt, 'mechanic_value', '60')
            try:
                return int(val)
            except ValueError:
                return 60
    # Check features
    for f in stats.features:
        if f.mechanic == "darkvision":
            try:
                return int(f.mechanic_value) if f.mechanic_value else 60
            except ValueError:
                return 60
    # Check senses string (monsters)
    if stats.senses:
        m = re.search(r'darkvision\s+(\d+)', stats.senses, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0

def _get_night_effects(stats: CreatureStats) -> list:
    """Get list of night-time effects for a character."""
    effects = []
    dv = _get_darkvision(stats)
    if dv > 0:
        effects.append(f"Darkvision {dv} ft")
    else:
        effects.append("No darkvision — disadvantage on Perception (sight)")

    # Check for special night abilities
    for rt in stats.racial_traits:
        mech = getattr(rt, 'mechanic', '')
        if mech == "sunlight_sensitivity":
            effects.append("Sunlight Sensitivity (disadv in sunlight)")
        elif mech == "superior_darkvision":
            effects.append("Superior Darkvision 120 ft")
        elif mech == "mask_of_wild":
            effects.append("Mask of the Wild (hide in light foliage)")
    for f in stats.features:
        if f.mechanic == "shadow_step":
            effects.append("Shadow Step (bonus: teleport 60ft dim/dark)")
        elif f.mechanic == "shadow_arts":
            effects.append("Shadow Arts (minor illusion, darkness)")
    return effects

def _get_passive_abilities_summary(stats: CreatureStats) -> list:
    """Get all passive abilities as list of (label, value) tuples."""
    abilities = [
        ("Passive Perception", _get_passive_perception(stats)),
        ("Passive Investigation", _get_passive_investigation(stats)),
        ("Passive Insight", _get_passive_insight(stats)),
    ]
    dv = _get_darkvision(stats)
    if dv > 0:
        abilities.append(("Darkvision", f"{dv} ft"))
    # Check for special senses
    if stats.senses:
        if "blindsight" in stats.senses.lower():
            m = re.search(r'blindsight\s+(\d+)', stats.senses, re.IGNORECASE)
            if m:
                abilities.append(("Blindsight", f"{m.group(1)} ft"))
        if "tremorsense" in stats.senses.lower():
            m = re.search(r'tremorsense\s+(\d+)', stats.senses, re.IGNORECASE)
            if m:
                abilities.append(("Tremorsense", f"{m.group(1)} ft"))
    # Skill proficiencies
    if stats.skills:
        for skill, bonus in sorted(stats.skills.items()):
            sign = "+" if bonus >= 0 else ""
            abilities.append((f"  {skill}", f"{sign}{bonus}"))
    return abilities


# ============================================================================
# Campaign Manager State
# ============================================================================

class CampaignManagerState:
    """Off-combat campaign management view."""

    def __init__(self, manager, campaign: Campaign = None):
        self.manager = manager
        self.campaign = campaign or Campaign(name="New Campaign", created=_timestamp())

        # UI state
        self.active_tab = 0  # 0=Party, 1=Encounters, 2=Areas, 3=Notes
        self.tabs = TabBar(250, 15, 700, ["Party", "Encounters", "Areas", "Notes"],
                           active=0, on_change=self._on_tab_change)
        self.scroll_y = 0
        self.selected_member_idx = -1
        self.selected_encounter_idx = -1
        self.selected_area_idx = -1

        # Input state
        self.input_active = ""  # Which input field is active
        self.input_text = ""
        self.modal = None       # Active modal (note edit, encounter edit, etc.)

        # Hero picker for adding to party
        self.hero_picker_open = False
        self.hero_picker_scroll = 0
        self.hero_search = ""
        self.hero_search_active = False

        # Monster picker for encounters
        self.monster_picker_open = False
        self.monster_picker_scroll = 0
        self.monster_search = ""
        self.monster_search_active = False

        # Cached hero stats (rebuilt from hero_data when needed)
        self._hero_stats_cache: dict = {}

        # Build buttons
        self._build_buttons()

    def _build_buttons(self):
        """Build all UI buttons."""
        self.btn_back = Button(20, 15, 100, 35, "< Menu",
                               lambda: self.manager.change_state("MENU"),
                               color=COLORS["panel"])
        self.btn_save = Button(SCREEN_WIDTH - 130, 15, 110, 35, "Save",
                               self._save_campaign, color=COLORS["success"])

        # Time of day buttons
        self.time_buttons = []
        times = [("Dawn", "dawn"), ("Day", "day"), ("Dusk", "dusk"), ("Night", "night")]
        for i, (label, val) in enumerate(times):
            self.time_buttons.append(
                Button(SCREEN_WIDTH - 490 + i * 85, 15, 80, 35, label,
                       lambda v=val: self._set_time(v),
                       color=COLORS["panel"])
            )

        # Party tab buttons
        self.btn_add_hero = Button(20, SCREEN_HEIGHT - 60, 160, 45, "+ Add Hero",
                                    self._toggle_hero_picker, color=COLORS["player"])
        self.btn_long_rest = Button(200, SCREEN_HEIGHT - 60, 160, 45, "Long Rest All",
                                     self._long_rest_all, color=COLORS["accent"])
        self.btn_short_rest = Button(380, SCREEN_HEIGHT - 60, 160, 45, "Short Rest All",
                                      self._short_rest_all, color=COLORS["accent_dim"])

        # Encounter tab buttons
        self.btn_new_encounter = Button(20, SCREEN_HEIGHT - 60, 180, 45, "+ New Encounter",
                                         self._add_encounter, color=COLORS["danger"])
        self.btn_launch_encounter = Button(220, SCREEN_HEIGHT - 60, 200, 45, "Launch Combat",
                                            self._launch_encounter, color=COLORS["success"])

        # Area tab buttons
        self.btn_new_area = Button(20, SCREEN_HEIGHT - 60, 160, 45, "+ New Area",
                                    self._add_area, color=COLORS["spell"])

        # Notes tab buttons
        self.btn_new_note = Button(20, SCREEN_HEIGHT - 60, 160, 45, "+ Add Note",
                                    self._add_note, color=COLORS["warning"])

    def _on_tab_change(self, idx):
        self.active_tab = idx
        self.scroll_y = 0
        self.hero_picker_open = False
        self.monster_picker_open = False
        self.modal = None

    def _set_time(self, tod):
        self.campaign.time_of_day = tod

    def _save_campaign(self):
        path = save_campaign(self.campaign)
        self._status_msg = f"Saved to {os.path.basename(path)}"
        self._status_timer = 120

    # ---- Party Management ----

    def _get_hero_stats(self, member: PartyMember) -> CreatureStats:
        """Reconstruct CreatureStats from serialized hero_data."""
        key = id(member)
        if key in self._hero_stats_cache:
            return self._hero_stats_cache[key]
        if member.hero_data:
            try:
                stats = import_hero(member.hero_data)
            except Exception:
                stats = CreatureStats(name=member.hero_data.get("name", "Unknown"))
            self._hero_stats_cache[key] = stats
            return stats
        return CreatureStats(name="Unknown")

    def _add_hero_to_party(self, hero_stats: CreatureStats):
        """Add a hero to the campaign party."""
        hero_data = export_hero(hero_stats)
        member = PartyMember(
            hero_data=hero_data,
            current_hp=hero_stats.hit_points,
        )
        self.campaign.party.append(member)
        self._hero_stats_cache.clear()
        self.hero_picker_open = False

    def _remove_member(self, idx):
        if 0 <= idx < len(self.campaign.party):
            self.campaign.party.pop(idx)
            self._hero_stats_cache.clear()
            if self.selected_member_idx >= len(self.campaign.party):
                self.selected_member_idx = len(self.campaign.party) - 1

    def _toggle_hero_picker(self):
        self.hero_picker_open = not self.hero_picker_open
        self.hero_search = ""

    def _long_rest_all(self):
        for member in self.campaign.party:
            member.current_hp = member.hero_data.get("hit_points", 0)
            member.temp_hp = 0
            member.conditions.clear()
            member.spell_slots_used.clear()
            member.feature_uses_used.clear()
            member.exhaustion = max(0, member.exhaustion - 1)
            member.death_saves = {"success": 0, "failure": 0}

    def _short_rest_all(self):
        for member in self.campaign.party:
            member.feature_uses_used.clear()
            # Recover some HP (simplified: heal 25% of max)
            max_hp = member.hero_data.get("hit_points", 0)
            heal = max_hp // 4
            member.current_hp = min(max_hp, member.current_hp + heal)

    # ---- Encounter Management ----

    def _add_encounter(self):
        enc = CampaignEncounter(
            name=f"Encounter {len(self.campaign.encounters) + 1}",
            area_name=self.campaign.current_area,
        )
        self.campaign.encounters.append(enc)
        self.selected_encounter_idx = len(self.campaign.encounters) - 1

    def _add_monster_to_encounter(self, monster_name, is_hero=False, side="enemy"):
        if self.selected_encounter_idx < 0:
            return
        enc = self.campaign.encounters[self.selected_encounter_idx]
        # Check if already in encounter, increment count
        for slot in enc.slots:
            if slot.creature_name == monster_name and slot.side == side:
                slot.count += 1
                return
        enc.slots.append(EncounterSlot(
            creature_name=monster_name, count=1, side=side, is_hero=is_hero))

    def _remove_slot_from_encounter(self, slot_idx):
        if self.selected_encounter_idx < 0:
            return
        enc = self.campaign.encounters[self.selected_encounter_idx]
        if 0 <= slot_idx < len(enc.slots):
            enc.slots.pop(slot_idx)

    def _launch_encounter(self):
        """Build entity roster from selected encounter and launch combat."""
        if self.selected_encounter_idx < 0:
            return
        enc = self.campaign.encounters[self.selected_encounter_idx]
        roster = []

        # Add party members
        px, py = 3, 2
        for member in self.campaign.party:
            if not member.active:
                continue
            stats = self._rebuild_stats(member)
            if stats:
                ent = Entity(stats, px, py, is_player=True)
                # Apply campaign HP state
                if member.current_hp >= 0:
                    ent.hp = member.current_hp
                ent.temp_hp = member.temp_hp
                for cond in member.conditions:
                    ent.add_condition(cond)
                ent.exhaustion = member.exhaustion
                roster.append(ent)
                py += 2

        # Add encounter slots (enemies, allies)
        ex, ey = 14, 3
        for slot in enc.slots:
            if slot.is_hero:
                continue  # Party heroes already added
            for i in range(slot.count):
                try:
                    stats = library.get_monster(slot.creature_name)
                    stats = copy.deepcopy(stats)
                    if slot.count > 1:
                        stats.name = f"{slot.creature_name} {i + 1}"
                except ValueError:
                    continue
                is_ally = slot.side == "ally"
                ent = Entity(stats, ex, ey, is_player=is_ally)
                roster.append(ent)
                ey += 2
                if ey > 15:
                    ey = 3
                    ex += 2

        if roster:
            from states.game_states import BattleState
            bs = BattleState(self.manager, roster)
            self.manager.states["BATTLE"] = bs
            self.manager.change_state("BATTLE")

    def _rebuild_stats(self, member: PartyMember) -> CreatureStats:
        """Rebuild CreatureStats from member hero_data."""
        if not member.hero_data:
            return None
        try:
            return import_hero(member.hero_data)
        except Exception:
            return None

    # ---- Area Management ----

    def _add_area(self):
        area = CampaignArea(name=f"Area {len(self.campaign.areas) + 1}")
        self.campaign.areas.append(area)
        self.selected_area_idx = len(self.campaign.areas) - 1

    # ---- Notes ----

    def _add_note(self):
        note = CampaignNote(text="", timestamp=_timestamp(), category="general")
        self.campaign.notes.append(note)

    # ================================================================
    # EVENT HANDLING
    # ================================================================

    def handle_events(self, events):
        mp = pygame.mouse.get_pos()
        for event in events:
            if self.modal:
                self._handle_modal_event(event)
                continue

            # Tab bar
            self.tabs.handle_event(event)

            # Global buttons
            self.btn_back.handle_event(event)
            self.btn_save.handle_event(event)
            for tb in self.time_buttons:
                tb.handle_event(event)

            # Scroll
            if event.type == pygame.MOUSEWHEEL:
                if self.hero_picker_open and mp[0] > SCREEN_WIDTH - 300:
                    self.hero_picker_scroll += event.y * 30
                elif self.monster_picker_open and mp[0] > SCREEN_WIDTH - 300:
                    self.monster_picker_scroll += event.y * 30
                else:
                    self.scroll_y += event.y * 30

            # Keyboard input
            if event.type == pygame.KEYDOWN:
                if self.hero_search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.hero_search = self.hero_search[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.hero_search_active = False
                    elif event.unicode.isprintable():
                        self.hero_search += event.unicode
                    continue
                if self.monster_search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.monster_search = self.monster_search[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.monster_search_active = False
                    elif event.unicode.isprintable():
                        self.monster_search += event.unicode
                    continue
                if self.input_active:
                    self._handle_input_key(event)
                    continue

            # Tab-specific event handling
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.active_tab == 0:
                    self._handle_party_click(mp)
                elif self.active_tab == 1:
                    self._handle_encounter_click(mp)
                elif self.active_tab == 2:
                    self._handle_area_click(mp)
                elif self.active_tab == 3:
                    self._handle_notes_click(mp)

            # Tab-specific buttons
            if self.active_tab == 0:
                self.btn_add_hero.handle_event(event)
                self.btn_long_rest.handle_event(event)
                self.btn_short_rest.handle_event(event)
            elif self.active_tab == 1:
                self.btn_new_encounter.handle_event(event)
                self.btn_launch_encounter.handle_event(event)
            elif self.active_tab == 2:
                self.btn_new_area.handle_event(event)
            elif self.active_tab == 3:
                self.btn_new_note.handle_event(event)

    def _handle_party_click(self, mp):
        mx, my = mp
        # Hero picker click
        if self.hero_picker_open and mx > SCREEN_WIDTH - 300:
            # Search box
            if pygame.Rect(SCREEN_WIDTH - 290, 60, 270, 28).collidepoint(mp):
                self.hero_search_active = True
                return
            self.hero_search_active = False
            # Hero list items
            y = 95 + self.hero_picker_scroll
            for h in hero_list:
                if self.hero_search and self.hero_search.lower() not in h.name.lower():
                    continue
                if pygame.Rect(SCREEN_WIDTH - 290, y, 270, 32).collidepoint(mp):
                    self._add_hero_to_party(h)
                    return
                y += 35
            return

        # Party member selection
        y = 70 + self.scroll_y
        for i, member in enumerate(self.campaign.party):
            card_rect = pygame.Rect(20, y, SCREEN_WIDTH - 60, 55)
            if card_rect.collidepoint(mp):
                self.selected_member_idx = i
                return
            y += 60

    def _handle_encounter_click(self, mp):
        mx, my = mp
        # Monster picker
        if self.monster_picker_open and mx > SCREEN_WIDTH - 300:
            if pygame.Rect(SCREEN_WIDTH - 290, 60, 270, 28).collidepoint(mp):
                self.monster_search_active = True
                return
            self.monster_search_active = False
            y = 95 + self.monster_picker_scroll
            all_monsters = library.get_all_monsters()
            for m in all_monsters:
                if self.monster_search and self.monster_search.lower() not in m.name.lower():
                    continue
                if pygame.Rect(SCREEN_WIDTH - 290, y, 270, 32).collidepoint(mp):
                    side = getattr(self, '_next_add_side', 'enemy')
                    self._add_monster_to_encounter(m.name, side=side)
                    self._next_add_side = "enemy"  # Reset
                    self.monster_picker_open = False
                    return
                y += 35
            return

        # Encounter list (left panel)
        y = 70 + self.scroll_y
        for i, enc in enumerate(self.campaign.encounters):
            rect = pygame.Rect(20, y, 300, 45)
            if rect.collidepoint(mp):
                self.selected_encounter_idx = i
                return
            y += 50

    def _handle_area_click(self, mp):
        y = 70 + self.scroll_y
        for i, area in enumerate(self.campaign.areas):
            rect = pygame.Rect(20, y, 400, 45)
            if rect.collidepoint(mp):
                self.selected_area_idx = i
                return
            y += 50

    def _handle_notes_click(self, mp):
        y = 70 + self.scroll_y
        for i, note in enumerate(self.campaign.notes):
            rect = pygame.Rect(20, y, SCREEN_WIDTH - 60, 80)
            if rect.collidepoint(mp):
                self.modal = ("edit_note", i)
                self.input_text = note.text
                self.input_active = "note"
                return
            y += 90

    def _handle_input_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.input_active = ""
            return
        if event.key == pygame.K_RETURN:
            self._apply_input()
            return
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.unicode.isprintable():
            self.input_text += event.unicode

    def _apply_input(self):
        if self.input_active == "note" and self.modal and self.modal[0] == "edit_note":
            idx = self.modal[1]
            if 0 <= idx < len(self.campaign.notes):
                self.campaign.notes[idx].text = self.input_text
                self.campaign.notes[idx].timestamp = _timestamp()
        elif self.input_active == "campaign_name":
            self.campaign.name = self.input_text
        elif self.input_active == "encounter_name":
            if 0 <= self.selected_encounter_idx < len(self.campaign.encounters):
                self.campaign.encounters[self.selected_encounter_idx].name = self.input_text
        elif self.input_active == "area_name":
            if 0 <= self.selected_area_idx < len(self.campaign.areas):
                self.campaign.areas[self.selected_area_idx].name = self.input_text
        elif self.input_active == "member_note":
            if 0 <= self.selected_member_idx < len(self.campaign.party):
                self.campaign.party[self.selected_member_idx].notes = self.input_text
        self.input_active = ""
        self.modal = None

    def _handle_modal_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.modal = None
                self.input_active = ""
                return
            self._handle_input_key(event)

    # ================================================================
    # UPDATE
    # ================================================================

    def update(self):
        if hasattr(self, '_status_timer') and self._status_timer > 0:
            self._status_timer -= 1

    # ================================================================
    # DRAWING
    # ================================================================

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        mp = pygame.mouse.get_pos()

        # Header bar
        pygame.draw.rect(screen, COLORS["panel_dark"], (0, 0, SCREEN_WIDTH, 55))
        pygame.draw.line(screen, COLORS["border"], (0, 55), (SCREEN_WIDTH, 55))

        # Campaign name
        name_text = self.campaign.name
        nt = fonts.header.render(name_text, True, COLORS["accent"])
        screen.blit(nt, (140, 14))

        # Time of day indicator
        tod = self.campaign.time_of_day
        tod_colors = {
            "dawn": (255, 180, 100), "day": (255, 240, 180),
            "dusk": (180, 100, 140), "night": (60, 60, 120),
        }
        tod_col = tod_colors.get(tod, (200, 200, 200))
        tod_txt = fonts.body.render(f"Time: {tod.capitalize()}", True, tod_col)
        screen.blit(tod_txt, (SCREEN_WIDTH - 500, 48))

        # Session number
        sess = fonts.small.render(f"Session #{self.campaign.session_number}", True, COLORS["text_dim"])
        screen.blit(sess, (SCREEN_WIDTH - 280, 48))

        # Draw buttons
        self.btn_back.draw(screen, mp)
        self.btn_save.draw(screen, mp)
        self.tabs.draw(screen, mp)
        for tb in self.time_buttons:
            # Highlight active time
            if tb.text.lower() == tod:
                tb.color = tod_col
            else:
                tb.color = COLORS["panel"]
            tb.draw(screen, mp)

        # Status message
        if hasattr(self, '_status_timer') and self._status_timer > 0:
            sm = fonts.small.render(self._status_msg, True, COLORS["success"])
            screen.blit(sm, (SCREEN_WIDTH - 350, 38))

        # Draw active tab content
        clip_rect = pygame.Rect(0, 60, SCREEN_WIDTH, SCREEN_HEIGHT - 120)
        screen.set_clip(clip_rect)

        if self.active_tab == 0:
            self._draw_party_tab(screen, mp)
        elif self.active_tab == 1:
            self._draw_encounters_tab(screen, mp)
        elif self.active_tab == 2:
            self._draw_areas_tab(screen, mp)
        elif self.active_tab == 3:
            self._draw_notes_tab(screen, mp)

        screen.set_clip(None)

        # Hero picker overlay
        if self.hero_picker_open:
            self._draw_hero_picker(screen, mp)

        # Monster picker overlay
        if self.monster_picker_open:
            self._draw_monster_picker(screen, mp)

        # Bottom buttons
        if self.active_tab == 0:
            self.btn_add_hero.draw(screen, mp)
            self.btn_long_rest.draw(screen, mp)
            self.btn_short_rest.draw(screen, mp)
        elif self.active_tab == 1:
            self.btn_new_encounter.draw(screen, mp)
            self.btn_launch_encounter.draw(screen, mp)
        elif self.active_tab == 2:
            self.btn_new_area.draw(screen, mp)
        elif self.active_tab == 3:
            self.btn_new_note.draw(screen, mp)

        # Modal overlay
        if self.modal:
            self._draw_modal(screen, mp)

    # ---- Party Tab Drawing ----

    def _draw_party_tab(self, screen, mp):
        y = 70 + self.scroll_y
        is_night = self.campaign.time_of_day in ("night", "dusk")

        if not self.campaign.party:
            txt = fonts.header.render("No heroes in party. Click '+ Add Hero' to begin.", True, COLORS["text_dim"])
            screen.blit(txt, (40, y))
            return

        for i, member in enumerate(self.campaign.party):
            data = member.hero_data
            name = data.get("name", "Unknown")
            cls = data.get("character_class", "")
            lvl = data.get("character_level", 0)
            race = data.get("race", "")
            max_hp = data.get("hit_points", 0)
            hp = member.current_hp if member.current_hp >= 0 else max_hp
            ac = data.get("armor_class", 10)

            is_selected = i == self.selected_member_idx
            card_h = 50
            card_rect = pygame.Rect(20, y, SCREEN_WIDTH - 60, card_h)

            # Card background
            bg_color = COLORS["selected"] if is_selected else COLORS["panel"]
            if not member.active:
                bg_color = COLORS["panel_dark"]
            pygame.draw.rect(screen, bg_color, card_rect, border_radius=6)
            pygame.draw.rect(screen, COLORS["border_light"] if is_selected else COLORS["border"],
                             card_rect, 1, border_radius=6)

            # Class color indicator
            cls_col = COLORS.get(cls.lower(), COLORS["text_dim"]) if cls else COLORS["text_dim"]
            pygame.draw.rect(screen, cls_col, (card_rect.x + 2, card_rect.y + 2, 4, card_h - 4))

            # Name and class
            name_surf = fonts.body_bold.render(f"{name}", True, COLORS["text_bright"])
            screen.blit(name_surf, (card_rect.x + 14, y + 4))
            if cls:
                info = f"Lv{lvl} {race} {cls}"
                info_surf = fonts.small.render(info, True, COLORS["text_dim"])
                screen.blit(info_surf, (card_rect.x + 14, y + 26))

            # HP bar
            hp_pct = hp / max(max_hp, 1)
            hp_col = COLORS["hp_full"] if hp_pct > 0.5 else (COLORS["hp_mid"] if hp_pct > 0.25 else COLORS["hp_low"])
            bar_x = 350
            bar_w = 120
            pygame.draw.rect(screen, COLORS["hp_bg"], (bar_x, y + 8, bar_w, 14), border_radius=3)
            pygame.draw.rect(screen, hp_col, (bar_x, y + 8, int(bar_w * hp_pct), 14), border_radius=3)
            hp_txt = fonts.small.render(f"HP {hp}/{max_hp}", True, COLORS["text_bright"])
            screen.blit(hp_txt, (bar_x + 4, y + 8))

            # AC
            ac_txt = fonts.small.render(f"AC {ac}", True, COLORS["text_main"])
            screen.blit(ac_txt, (bar_x + bar_w + 15, y + 8))

            # Temp HP
            if member.temp_hp > 0:
                thp = fonts.small.render(f"+{member.temp_hp} THP", True, COLORS["cold"])
                screen.blit(thp, (bar_x + bar_w + 15, y + 26))

            # Conditions
            cond_x = bar_x + bar_w + 80
            for cond in member.conditions:
                cs = fonts.tiny.render(cond, True, COLORS["warning"])
                screen.blit(cs, (cond_x, y + 10))
                cond_x += cs.get_width() + 8

            # Exhaustion
            if member.exhaustion > 0:
                ex_txt = fonts.small.render(f"Exhaustion {member.exhaustion}", True, COLORS["danger"])
                screen.blit(ex_txt, (cond_x, y + 10))

            # Passive abilities (right side)
            passives_x = SCREEN_WIDTH - 420
            abilities_data = data.get("abilities", {})
            if abilities_data:
                wis_mod = (abilities_data.get("wisdom", 10) - 10) // 2
                perc_bonus = data.get("skills", {}).get("Perception", 0)
                passive_perc = 10 + (perc_bonus if perc_bonus else wis_mod)
                pp = fonts.small.render(f"PP {passive_perc}", True, COLORS["text_main"])
                screen.blit(pp, (passives_x, y + 6))

                # Darkvision indicator
                dv = 0
                for rt_data in data.get("racial_traits", []):
                    if rt_data.get("mechanic") == "darkvision":
                        dv = int(rt_data.get("mechanic_value", "60") or "60")
                if dv > 0:
                    dv_col = COLORS["success"] if not is_night else COLORS["heal"]
                    dv_txt = fonts.small.render(f"DV {dv}ft", True, dv_col)
                    screen.blit(dv_txt, (passives_x + 55, y + 6))
                elif is_night:
                    no_dv = fonts.small.render("No DV!", True, COLORS["danger"])
                    screen.blit(no_dv, (passives_x + 55, y + 6))

            # Night effects
            if is_night:
                night_indicator = fonts.tiny.render("NIGHT", True, (60, 60, 120))
                screen.blit(night_indicator, (passives_x + 130, y + 8))

            # Remove button (small X)
            remove_rect = pygame.Rect(card_rect.right - 30, y + 15, 20, 20)
            if remove_rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["danger"], remove_rect, border_radius=3)
                if pygame.mouse.get_pressed()[0]:
                    self._remove_member(i)
                    return
            rx = fonts.small.render("X", True, COLORS["text_dim"])
            screen.blit(rx, (remove_rect.x + 5, remove_rect.y + 1))

            y += 60

        # Selected member detail panel
        if 0 <= self.selected_member_idx < len(self.campaign.party):
            self._draw_member_detail(screen, mp, y + 20)

    def _draw_member_detail(self, screen, mp, start_y):
        """Draw detailed view of selected party member."""
        member = self.campaign.party[self.selected_member_idx]
        data = member.hero_data
        y = start_y

        # Divider
        pygame.draw.line(screen, COLORS["border"], (20, y), (SCREEN_WIDTH - 40, y))
        y += 10

        name = data.get("name", "Unknown")
        cls = data.get("character_class", "")
        lvl = data.get("character_level", 0)

        # Header
        hdr = fonts.header.render(f"{name} — Detail", True, COLORS["accent"])
        screen.blit(hdr, (30, y))
        y += 35

        # Ability Scores
        abilities = data.get("abilities", {})
        ab_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        ax = 30
        for ab in ab_names:
            score = abilities.get(ab, 10)
            mod = (score - 10) // 2
            sign = "+" if mod >= 0 else ""
            label = ab[:3].upper()
            # Score box
            pygame.draw.rect(screen, COLORS["panel_light"], (ax, y, 65, 50), border_radius=4)
            pygame.draw.rect(screen, COLORS["border"], (ax, y, 65, 50), 1, border_radius=4)
            lt = fonts.tiny.render(label, True, COLORS["text_dim"])
            screen.blit(lt, (ax + 32 - lt.get_width() // 2, y + 2))
            sv = fonts.header.render(str(score), True, COLORS["text_bright"])
            screen.blit(sv, (ax + 32 - sv.get_width() // 2, y + 14))
            mv = fonts.small.render(f"{sign}{mod}", True, COLORS["accent"])
            screen.blit(mv, (ax + 32 - mv.get_width() // 2, y + 36))
            ax += 75
        y += 60

        # Passive abilities
        is_night = self.campaign.time_of_day in ("night", "dusk")

        # Build temporary CreatureStats for passive calc
        wis_mod = (abilities.get("wisdom", 10) - 10) // 2
        int_mod = (abilities.get("intelligence", 10) - 10) // 2
        skills = data.get("skills", {})
        pp = 10 + (skills.get("Perception", 0) or wis_mod)
        pi = 10 + (skills.get("Investigation", 0) or int_mod)
        pins = 10 + (skills.get("Insight", 0) or wis_mod)

        passives = [
            ("Passive Perception", pp),
            ("Passive Investigation", pi),
            ("Passive Insight", pins),
        ]
        px = 30
        for label, val in passives:
            # Night penalty for perception (no darkvision)
            display_val = val
            col = COLORS["text_main"]
            if is_night and label == "Passive Perception":
                has_dv = any(rt.get("mechanic") == "darkvision" for rt in data.get("racial_traits", []))
                if not has_dv:
                    display_val = val - 5  # Disadvantage = -5 to passive
                    col = COLORS["danger"]
            vt = fonts.body.render(f"{label}: {display_val}", True, col)
            screen.blit(vt, (px, y))
            px += vt.get_width() + 30
        y += 28

        # Darkvision & night effects
        dv = 0
        for rt_data in data.get("racial_traits", []):
            if rt_data.get("mechanic") == "darkvision":
                dv = int(rt_data.get("mechanic_value", "60") or "60")
        if dv:
            dvt = fonts.body.render(f"Darkvision: {dv} ft", True, COLORS["success"])
            screen.blit(dvt, (30, y))
        else:
            dvt = fonts.body.render("No Darkvision", True,
                                     COLORS["danger"] if is_night else COLORS["text_dim"])
            screen.blit(dvt, (30, y))
        if is_night and not dv:
            warn = fonts.small.render("(Disadvantage on sight-based Perception checks at night)", True, COLORS["warning"])
            screen.blit(warn, (200, y + 2))
        y += 25

        # Speed
        speed = data.get("speed", 30)
        spd_txt = fonts.body.render(f"Speed: {speed} ft", True, COLORS["text_main"])
        screen.blit(spd_txt, (30, y))
        fly = data.get("fly_speed", 0)
        if fly:
            ft = fonts.body.render(f"  Fly: {fly} ft", True, COLORS["accent"])
            screen.blit(ft, (160, y))
        y += 25

        # Saving throws
        saves = data.get("saving_throws", {})
        if saves:
            st = fonts.small_bold.render("Saving Throws:", True, COLORS["text_dim"])
            screen.blit(st, (30, y))
            sx = 160
            for ab, val in saves.items():
                sign = "+" if val >= 0 else ""
                sv = fonts.small.render(f"{ab[:3]} {sign}{val}", True, COLORS["text_main"])
                screen.blit(sv, (sx, y))
                sx += sv.get_width() + 15
            y += 22

        # Skills
        if skills:
            sk_label = fonts.small_bold.render("Skills:", True, COLORS["text_dim"])
            screen.blit(sk_label, (30, y))
            sx = 100
            for skill, val in sorted(skills.items()):
                sign = "+" if val >= 0 else ""
                sv = fonts.small.render(f"{skill} {sign}{val}", True, COLORS["text_main"])
                screen.blit(sv, (sx, y))
                sx += sv.get_width() + 15
                if sx > SCREEN_WIDTH - 100:
                    sx = 100
                    y += 18
            y += 22

        # Features
        features = data.get("features", [])
        if features:
            fl = fonts.small_bold.render("Features:", True, COLORS["text_dim"])
            screen.blit(fl, (30, y))
            y += 18
            for f_data in features:
                fname = f_data.get("name", "")
                ftype = f_data.get("feature_type", "")
                uses = f_data.get("uses_per_day", -1)
                use_str = f" ({uses}/day)" if uses > 0 else ""
                ft = fonts.small.render(f"  {fname}{use_str}", True, COLORS["text_main"])
                screen.blit(ft, (30, y))
                y += 16
            y += 5

        # Items
        items = data.get("items", [])
        if items:
            il = fonts.small_bold.render("Inventory:", True, COLORS["text_dim"])
            screen.blit(il, (30, y))
            y += 18
            for item_data in items:
                iname = item_data.get("name", "")
                equipped = item_data.get("equipped", False)
                uses = item_data.get("uses", -1)
                tag = " [E]" if equipped else ""
                use_tag = f" (x{uses})" if uses > 0 else ""
                col = COLORS["accent"] if equipped else COLORS["text_main"]
                it = fonts.small.render(f"  {iname}{tag}{use_tag}", True, col)
                screen.blit(it, (30, y))
                y += 16

        # DM Notes
        y += 10
        nl = fonts.small_bold.render("DM Notes:", True, COLORS["text_dim"])
        screen.blit(nl, (30, y))
        y += 18
        note_rect = pygame.Rect(30, y, SCREEN_WIDTH - 100, 60)
        pygame.draw.rect(screen, COLORS["input_bg"], note_rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], note_rect, 1, border_radius=4)
        note_text = member.notes or "(Click to add notes)"
        nt_col = COLORS["text_main"] if member.notes else COLORS["text_muted"]
        nt = fonts.small.render(note_text[:80], True, nt_col)
        screen.blit(nt, (35, y + 5))
        if note_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "member_note"
            self.input_text = member.notes
            self.modal = ("edit_member_note", self.selected_member_idx)

    # ---- Encounters Tab Drawing ----

    def _draw_encounters_tab(self, screen, mp):
        y = 70 + self.scroll_y

        # Encounter list (left side)
        left_w = 320
        el = fonts.small_bold.render("Encounters", True, COLORS["text_dim"])
        screen.blit(el, (30, y))
        y += 22

        for i, enc in enumerate(self.campaign.encounters):
            is_sel = i == self.selected_encounter_idx
            rect = pygame.Rect(20, y, left_w, 42)
            bg = COLORS["selected"] if is_sel else COLORS["panel"]
            if enc.completed:
                bg = COLORS["panel_dark"]
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, COLORS["border_light"] if is_sel else COLORS["border"],
                             rect, 1, border_radius=5)

            ename = fonts.body.render(enc.name, True, COLORS["text_bright"])
            screen.blit(ename, (rect.x + 10, y + 3))

            slot_count = sum(s.count for s in enc.slots)
            info = f"{slot_count} creatures"
            if enc.area_name:
                info += f" | {enc.area_name}"
            if enc.completed:
                info += " [DONE]"
            ei = fonts.tiny.render(info, True, COLORS["text_dim"])
            screen.blit(ei, (rect.x + 10, y + 24))

            y += 50

        # Selected encounter detail (right side)
        if 0 <= self.selected_encounter_idx < len(self.campaign.encounters):
            self._draw_encounter_detail(screen, mp, left_w + 40)

    def _draw_encounter_detail(self, screen, mp, start_x):
        enc = self.campaign.encounters[self.selected_encounter_idx]
        y = 70

        # Encounter name (editable)
        hdr = fonts.header.render(enc.name, True, COLORS["accent"])
        screen.blit(hdr, (start_x, y))
        # Edit name hint
        edit_hint = fonts.tiny.render("(Click to rename)", True, COLORS["text_muted"])
        screen.blit(edit_hint, (start_x + hdr.get_width() + 10, y + 8))
        name_rect = pygame.Rect(start_x, y, hdr.get_width() + 100, 30)
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "encounter_name"
            self.input_text = enc.name
        y += 35

        # Creature slots
        sl = fonts.small_bold.render("Creatures:", True, COLORS["text_dim"])
        screen.blit(sl, (start_x, y))
        y += 20

        for idx, slot in enumerate(enc.slots):
            side_col = COLORS["danger"] if slot.side == "enemy" else (
                COLORS["player"] if slot.side == "ally" else COLORS["neutral"])
            side_label = slot.side.upper()

            st = fonts.body.render(
                f"{slot.creature_name} x{slot.count} [{side_label}]",
                True, side_col)
            screen.blit(st, (start_x + 10, y))

            # Remove button
            rx = start_x + 400
            rm_rect = pygame.Rect(rx, y, 20, 18)
            if rm_rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["danger"], rm_rect, border_radius=2)
                if pygame.mouse.get_pressed()[0]:
                    self._remove_slot_from_encounter(idx)
                    return
            xt = fonts.small.render("X", True, COLORS["text_dim"])
            screen.blit(xt, (rx + 4, y + 1))

            # +/- count
            plus_rect = pygame.Rect(rx + 30, y, 20, 18)
            minus_rect = pygame.Rect(rx + 55, y, 20, 18)
            pygame.draw.rect(screen, COLORS["panel_light"], plus_rect, border_radius=2)
            pygame.draw.rect(screen, COLORS["panel_light"], minus_rect, border_radius=2)
            pt = fonts.small.render("+", True, COLORS["success"])
            mt = fonts.small.render("-", True, COLORS["danger"])
            screen.blit(pt, (plus_rect.x + 5, plus_rect.y))
            screen.blit(mt, (minus_rect.x + 6, minus_rect.y))
            if plus_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                slot.count += 1
            if minus_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                slot.count = max(1, slot.count - 1)

            y += 24

        # Add monster button
        add_btn_rect = pygame.Rect(start_x, y + 5, 160, 35)
        is_hover = add_btn_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if is_hover else COLORS["danger"],
                         add_btn_rect, border_radius=5)
        at = fonts.body.render("+ Add Monster", True, COLORS["text_bright"])
        screen.blit(at, (add_btn_rect.x + 15, add_btn_rect.y + 7))
        if is_hover and pygame.mouse.get_pressed()[0]:
            self.monster_picker_open = True
            self.monster_search = ""

        # Add ally button
        ally_btn_rect = pygame.Rect(start_x + 180, y + 5, 160, 35)
        is_hover2 = ally_btn_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["accent_hover"] if is_hover2 else COLORS["accent"],
                         ally_btn_rect, border_radius=5)
        alt = fonts.body.render("+ Add Ally NPC", True, COLORS["text_bright"])
        screen.blit(alt, (ally_btn_rect.x + 15, ally_btn_rect.y + 7))
        if is_hover2 and pygame.mouse.get_pressed()[0]:
            self.monster_picker_open = True
            self.monster_search = ""
            # Tag next addition as ally
            self._next_add_side = "ally"

        y += 50

        # Loot items
        lt = fonts.small_bold.render("Loot:", True, COLORS["text_dim"])
        screen.blit(lt, (start_x, y))
        y += 18
        for loot_name in enc.loot_items:
            li = fonts.small.render(f"  {loot_name}", True, COLORS["legendary"])
            screen.blit(li, (start_x, y))
            y += 16

        # Notes
        y += 10
        nt = fonts.small_bold.render("Encounter Notes:", True, COLORS["text_dim"])
        screen.blit(nt, (start_x, y))
        y += 18
        if enc.notes:
            for line in enc.notes.split("\n")[:5]:
                nl = fonts.small.render(line[:80], True, COLORS["text_main"])
                screen.blit(nl, (start_x, y))
                y += 16

    # ---- Areas Tab Drawing ----

    def _draw_areas_tab(self, screen, mp):
        y = 70 + self.scroll_y

        al = fonts.small_bold.render("Areas", True, COLORS["text_dim"])
        screen.blit(al, (30, y))
        y += 22

        for i, area in enumerate(self.campaign.areas):
            is_sel = i == self.selected_area_idx
            rect = pygame.Rect(20, y, 400, 42)
            bg = COLORS["selected"] if is_sel else COLORS["panel"]
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, COLORS["border_light"] if is_sel else COLORS["border"],
                             rect, 1, border_radius=5)

            aname = fonts.body.render(area.name, True, COLORS["text_bright"])
            screen.blit(aname, (rect.x + 10, y + 3))

            light_col = {"bright": COLORS["warning"], "dim": COLORS["text_dim"],
                         "darkness": (40, 40, 60)}.get(area.lighting, COLORS["text_dim"])
            info = f"{area.environment} | {area.lighting} light"
            ai = fonts.tiny.render(info, True, light_col)
            screen.blit(ai, (rect.x + 10, y + 24))

            encs = len(area.encounter_names)
            if encs:
                ec = fonts.tiny.render(f"{encs} encounters", True, COLORS["text_dim"])
                screen.blit(ec, (rect.x + 300, y + 24))

            y += 50

        # Selected area detail
        if 0 <= self.selected_area_idx < len(self.campaign.areas):
            area = self.campaign.areas[self.selected_area_idx]
            y += 20
            pygame.draw.line(screen, COLORS["border"], (20, y), (SCREEN_WIDTH - 40, y))
            y += 10

            hdr = fonts.header.render(area.name, True, COLORS["accent"])
            screen.blit(hdr, (30, y))
            y += 30

            dt = fonts.body.render(f"Environment: {area.environment}  |  Lighting: {area.lighting}", True, COLORS["text_main"])
            screen.blit(dt, (30, y))
            y += 25

            if area.description:
                dd = fonts.small.render(area.description[:120], True, COLORS["text_dim"])
                screen.blit(dd, (30, y))
                y += 20

            if area.notes:
                nl = fonts.small_bold.render("Notes:", True, COLORS["text_dim"])
                screen.blit(nl, (30, y))
                y += 18
                for line in area.notes.split("\n")[:5]:
                    nt = fonts.small.render(line[:80], True, COLORS["text_main"])
                    screen.blit(nt, (30, y))
                    y += 16

    # ---- Notes Tab Drawing ----

    def _draw_notes_tab(self, screen, mp):
        y = 70 + self.scroll_y

        nl = fonts.small_bold.render("Campaign Notes", True, COLORS["text_dim"])
        screen.blit(nl, (30, y))
        y += 22

        for i, note in enumerate(self.campaign.notes):
            rect = pygame.Rect(20, y, SCREEN_WIDTH - 60, 75)
            is_hover = rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, COLORS["border"], rect, 1, border_radius=5)

            # Category badge
            cat_colors = {"general": COLORS["text_dim"], "combat": COLORS["danger"],
                          "lore": COLORS["spell"], "quest": COLORS["warning"],
                          "loot": COLORS["legendary"]}
            cat_col = cat_colors.get(note.category, COLORS["text_dim"])
            ct = fonts.tiny.render(note.category.upper(), True, cat_col)
            screen.blit(ct, (rect.x + 10, y + 5))

            # Timestamp
            ts = fonts.tiny.render(note.timestamp, True, COLORS["text_muted"])
            screen.blit(ts, (rect.right - ts.get_width() - 10, y + 5))

            # Note text (truncated)
            text = note.text or "(Empty note — click to edit)"
            col = COLORS["text_main"] if note.text else COLORS["text_muted"]
            for li, line in enumerate(text.split("\n")[:3]):
                lt = fonts.small.render(line[:100], True, col)
                screen.blit(lt, (rect.x + 10, y + 22 + li * 16))

            y += 85

    # ---- Pickers ----

    def _draw_hero_picker(self, screen, mp):
        """Draw hero selection overlay on the right side."""
        panel_x = SCREEN_WIDTH - 310
        panel_rect = pygame.Rect(panel_x, 55, 305, SCREEN_HEIGHT - 120)
        pygame.draw.rect(screen, COLORS["panel_dark"], panel_rect)
        pygame.draw.rect(screen, COLORS["border_light"], panel_rect, 2)

        ht = fonts.header.render("Add Hero", True, COLORS["accent"])
        screen.blit(ht, (panel_x + 10, 60))

        # Search box
        search_rect = pygame.Rect(panel_x + 10, 90, 270, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["input_focus"] if self.hero_search_active else COLORS["border"],
                         search_rect, 1, border_radius=3)
        st = fonts.small.render(self.hero_search or "Search heroes...", True,
                                COLORS["text_main"] if self.hero_search else COLORS["text_muted"])
        screen.blit(st, (search_rect.x + 5, search_rect.y + 5))

        # Hero list
        y = 125 + self.hero_picker_scroll
        for h in hero_list:
            if self.hero_search and self.hero_search.lower() not in h.name.lower():
                continue
            if y < 55 or y > SCREEN_HEIGHT - 130:
                y += 35
                continue
            item_rect = pygame.Rect(panel_x + 10, y, 270, 30)
            is_hover = item_rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, item_rect, border_radius=3)

            cls_col = COLORS.get(h.character_class.lower(), COLORS["text_dim"]) if h.character_class else COLORS["text_dim"]
            pygame.draw.rect(screen, cls_col, (item_rect.x, item_rect.y + 2, 3, 26))

            label = h.name
            if h.character_class:
                label += f" (L{h.character_level} {h.character_class[:3]})"
            lt = fonts.small.render(label, True, COLORS["text_bright"])
            screen.blit(lt, (item_rect.x + 8, item_rect.y + 6))
            y += 35

        # Close button
        close_rect = pygame.Rect(panel_x + 250, 60, 40, 25)
        if close_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["danger"], close_rect, border_radius=3)
        cx = fonts.small.render("X", True, COLORS["text_bright"])
        screen.blit(cx, (close_rect.x + 15, close_rect.y + 3))
        if close_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.hero_picker_open = False

    def _draw_monster_picker(self, screen, mp):
        """Draw monster selection overlay on the right side."""
        panel_x = SCREEN_WIDTH - 310
        panel_rect = pygame.Rect(panel_x, 55, 305, SCREEN_HEIGHT - 120)
        pygame.draw.rect(screen, COLORS["panel_dark"], panel_rect)
        pygame.draw.rect(screen, COLORS["border_light"], panel_rect, 2)

        ht = fonts.header.render("Add Creature", True, COLORS["danger"])
        screen.blit(ht, (panel_x + 10, 60))

        # Search box
        search_rect = pygame.Rect(panel_x + 10, 90, 270, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["input_focus"] if self.monster_search_active else COLORS["border"],
                         search_rect, 1, border_radius=3)
        st = fonts.small.render(self.monster_search or "Search monsters...", True,
                                COLORS["text_main"] if self.monster_search else COLORS["text_muted"])
        screen.blit(st, (search_rect.x + 5, search_rect.y + 5))

        # Monster list
        y = 125 + self.monster_picker_scroll
        all_monsters = library.get_all_monsters()
        for m in all_monsters:
            if self.monster_search and self.monster_search.lower() not in m.name.lower():
                continue
            if y < 55 or y > SCREEN_HEIGHT - 130:
                y += 35
                continue
            item_rect = pygame.Rect(panel_x + 10, y, 270, 30)
            is_hover = item_rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, item_rect, border_radius=3)

            cr_str = f"CR {m.challenge_rating:.3g}" if m.challenge_rating % 1 != 0 else f"CR {int(m.challenge_rating)}"
            lt = fonts.small.render(f"{m.name} ({cr_str})", True, COLORS["text_bright"])
            screen.blit(lt, (item_rect.x + 8, item_rect.y + 6))
            y += 35

        # Close button
        close_rect = pygame.Rect(panel_x + 250, 60, 40, 25)
        if close_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["danger"], close_rect, border_radius=3)
        cx = fonts.small.render("X", True, COLORS["text_bright"])
        screen.blit(cx, (close_rect.x + 15, close_rect.y + 3))
        if close_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.monster_picker_open = False

    # ---- Modal Drawing ----

    def _draw_modal(self, screen, mp):
        """Draw modal overlay for editing notes etc."""
        # Darken background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))

        w, h = 600, 300
        x = SCREEN_WIDTH // 2 - w // 2
        y = SCREEN_HEIGHT // 2 - h // 2

        pygame.draw.rect(screen, COLORS["panel"], (x, y, w, h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border_light"], (x, y, w, h), 2, border_radius=10)

        if self.modal[0] in ("edit_note", "edit_member_note"):
            title = "Edit Note" if self.modal[0] == "edit_note" else "Edit DM Note"
            tt = fonts.header.render(title, True, COLORS["accent"])
            screen.blit(tt, (x + 20, y + 15))

            # Text area
            area = pygame.Rect(x + 20, y + 55, w - 40, h - 120)
            pygame.draw.rect(screen, COLORS["input_bg"], area, border_radius=4)
            pygame.draw.rect(screen, COLORS["input_focus"], area, 1, border_radius=4)

            # Draw text with cursor
            text_y = area.y + 5
            for line in self.input_text.split("\n"):
                lt = fonts.body.render(line, True, COLORS["text_bright"])
                screen.blit(lt, (area.x + 5, text_y))
                text_y += 22

            # Cursor blink
            if pygame.time.get_ticks() % 1000 < 500:
                lines = self.input_text.split("\n")
                last_line = lines[-1] if lines else ""
                cursor_x = area.x + 5 + fonts.body.size(last_line)[0]
                cursor_y = area.y + 5 + (len(lines) - 1) * 22
                pygame.draw.line(screen, COLORS["accent"], (cursor_x, cursor_y), (cursor_x, cursor_y + 18), 2)

            # Save / Cancel hints
            hints = fonts.small.render("Enter = Save  |  Escape = Cancel", True, COLORS["text_dim"])
            screen.blit(hints, (x + 20, y + h - 30))
