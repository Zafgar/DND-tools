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
from data.world import (
    World, Location, NPC, ShopItem, NPCRelationship,
    save_world, load_world, generate_id,
    add_location, add_npc, move_npc, delete_location, delete_npc,
    get_root_locations, get_children, get_location_path,
    get_npcs_at_location, search_npcs, search_locations,
    populate_shop, get_shop_suggestions, get_shopkeepers,
    get_shopkeepers_at_location, LOCATION_TYPES,
)
from data.shop_catalog import (
    get_item_price, get_item_tooltip, get_price_display,
    generate_shop_inventory, suggest_items_for_shop,
    get_all_shop_types, SHOP_TYPES, PRICE_MODIFIERS,
    apply_price_modifier, ITEM_PRICES, ITEM_TOOLTIPS,
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

        # World data — linked to campaign
        self.world = self._load_world_from_campaign()

        # UI state
        self.active_tab = 0  # 0=Party, 1=Encounters, 2=Areas, 3=Notes, 4=World
        self.tabs = TabBar(250, 15, 900, ["Party", "Encounters", "Areas", "Notes", "World"],
                           active=0, on_change=self._on_tab_change)
        self.scroll_y = 0
        self.selected_member_idx = -1
        self.selected_encounter_idx = -1
        self.selected_area_idx = -1

        # World tab state
        self.selected_location_id = ""
        self.selected_npc_id = ""
        self.world_view = "locations"  # "locations", "npcs", "shop_detail"
        self.npc_search = ""
        self.npc_search_active = False
        self.world_location_expanded: set = set()  # Expanded location IDs in tree
        self.shop_item_search = ""
        self.shop_item_search_active = False
        self.tooltip_item = ""  # Item name for tooltip popup
        self.tooltip_pos = (0, 0)
        self.shop_suggestions = []  # Cached suggestions

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

        # World tab buttons
        self.btn_add_location = Button(20, SCREEN_HEIGHT - 60, 170, 45, "+ Location",
                                        self._add_world_location, color=COLORS["spell"])
        self.btn_add_npc = Button(200, SCREEN_HEIGHT - 60, 140, 45, "+ NPC",
                                   self._add_world_npc, color=COLORS["player"])
        self.btn_world_npcs_view = Button(350, SCREEN_HEIGHT - 60, 140, 45, "All NPCs",
                                           self._toggle_npc_view, color=COLORS["accent"])
        self.btn_world_shops_view = Button(500, SCREEN_HEIGHT - 60, 140, 45, "Shops",
                                            self._toggle_shops_view, color=COLORS["legendary"])

    def _load_world_from_campaign(self) -> World:
        """Load or create World from campaign's world_data."""
        if self.campaign.world_data:
            try:
                # Reconstruct World from serialized dict
                from data.world import _deserialize_location, _deserialize_npc
                wd = self.campaign.world_data
                return World(
                    name=wd.get("name", self.campaign.name),
                    description=wd.get("description", ""),
                    created=wd.get("created", ""),
                    last_modified=wd.get("last_modified", ""),
                    locations={k: _deserialize_location(v) for k, v in wd.get("locations", {}).items()},
                    npcs={k: _deserialize_npc(v) for k, v in wd.get("npcs", {}).items()},
                    next_id=wd.get("next_id", 1),
                )
            except Exception:
                pass
        return World(name=self.campaign.name)

    def _serialize_world(self) -> dict:
        """Serialize World to dict for campaign save."""
        from data.world import _serialize_location, _serialize_npc
        w = self.world
        return {
            "name": w.name,
            "description": w.description,
            "created": w.created,
            "last_modified": w.last_modified,
            "locations": {k: _serialize_location(v) for k, v in w.locations.items()},
            "npcs": {k: _serialize_npc(v) for k, v in w.npcs.items()},
            "next_id": w.next_id,
        }

    def _on_tab_change(self, idx):
        self.active_tab = idx
        self.scroll_y = 0
        self.hero_picker_open = False
        self.monster_picker_open = False
        self.modal = None

    def _set_time(self, tod):
        self.campaign.time_of_day = tod

    def _save_campaign(self):
        self.campaign.world_data = self._serialize_world()
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

    # ---- World Management ----

    def _add_world_location(self):
        parent = self.selected_location_id if self.selected_location_id else ""
        loc = add_location(self.world, f"Location {self.world.next_id}", "region", parent)
        self.selected_location_id = loc.id
        if parent:
            self.world_location_expanded.add(parent)

    def _add_world_npc(self):
        loc_id = self.selected_location_id or ""
        npc = add_npc(self.world, f"NPC {self.world.next_id}", loc_id)
        self.selected_npc_id = npc.id
        self.world_view = "npcs"

    def _toggle_npc_view(self):
        self.world_view = "npcs" if self.world_view != "npcs" else "locations"
        self.scroll_y = 0

    def _toggle_shops_view(self):
        self.world_view = "shops" if self.world_view != "shops" else "locations"
        self.scroll_y = 0

    def _delete_world_location(self, loc_id):
        delete_location(self.world, loc_id)
        if self.selected_location_id == loc_id:
            self.selected_location_id = ""

    def _delete_world_npc(self, npc_id):
        delete_npc(self.world, npc_id)
        if self.selected_npc_id == npc_id:
            self.selected_npc_id = ""

    def _toggle_shopkeeper(self, npc_id):
        npc = self.world.npcs.get(npc_id)
        if not npc:
            return
        npc.is_shopkeeper = not npc.is_shopkeeper
        if npc.is_shopkeeper and not npc.shop_name:
            npc.shop_name = f"{npc.name}'s Shop"
        if npc.is_shopkeeper and not npc.shop_type:
            npc.shop_type = "general_store"

    def _auto_populate_shop(self, npc_id):
        npc = self.world.npcs.get(npc_id)
        if not npc:
            return
        # Get party level from campaign
        party_level = 1
        if self.campaign.party:
            levels = [m.hero_data.get("character_level", 1) for m in self.campaign.party if m.active]
            if levels:
                party_level = max(levels)
        npc.target_party_level = party_level
        populate_shop(npc, party_level)
        self._status_msg = f"Generated {len(npc.shop_items)} items for {npc.shop_name}"
        self._status_timer = 120

    def _refresh_shop_suggestions(self, npc_id):
        npc = self.world.npcs.get(npc_id)
        if npc:
            self.shop_suggestions = get_shop_suggestions(npc, 8)

    def _add_shop_item_to_npc(self, npc_id, item_name):
        npc = self.world.npcs.get(npc_id)
        if not npc:
            return
        base_price = get_item_price(item_name)
        adj_price = apply_price_modifier(base_price, npc.price_modifier)
        npc.shop_items.append(ShopItem(
            item_name=item_name,
            base_price_gp=base_price,
            current_price_gp=adj_price,
            quantity=-1,
        ))

    def _remove_shop_item(self, npc_id, idx):
        npc = self.world.npcs.get(npc_id)
        if npc and 0 <= idx < len(npc.shop_items):
            npc.shop_items.pop(idx)

    def _add_custom_shop_item(self, npc_id, item_name, price):
        npc = self.world.npcs.get(npc_id)
        if not npc:
            return
        adj = apply_price_modifier(price, npc.price_modifier)
        npc.shop_items.append(ShopItem(
            item_name=item_name, base_price_gp=price,
            current_price_gp=adj, quantity=-1,
        ))

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
                if self.npc_search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.npc_search = self.npc_search[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.npc_search_active = False
                    elif event.unicode.isprintable():
                        self.npc_search += event.unicode
                    continue
                if self.shop_item_search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.shop_item_search = self.shop_item_search[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.shop_item_search_active = False
                    elif event.unicode.isprintable():
                        self.shop_item_search += event.unicode
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
                elif self.active_tab == 4:
                    self._handle_world_click(mp)

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
            elif self.active_tab == 4:
                self.btn_add_location.handle_event(event)
                self.btn_add_npc.handle_event(event)
                self.btn_world_npcs_view.handle_event(event)
                self.btn_world_shops_view.handle_event(event)

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

    def _handle_monster_picker_click(self, mp):
        """Handle clicks in the monster picker overlay (shared across tabs)."""
        mx, my = mp
        if not (self.monster_picker_open and mx > SCREEN_WIDTH - 300):
            return False
        if pygame.Rect(SCREEN_WIDTH - 290, 60, 270, 28).collidepoint(mp):
            self.monster_search_active = True
            return True
        self.monster_search_active = False
        y = 95 + self.monster_picker_scroll
        all_monsters = library.get_all_monsters()
        for m in all_monsters:
            if self.monster_search and self.monster_search.lower() not in m.name.lower():
                continue
            if pygame.Rect(SCREEN_WIDTH - 290, y, 270, 32).collidepoint(mp):
                # Check if linking NPC stat source
                if getattr(self, '_npc_stat_link_mode', False):
                    npc = self.world.npcs.get(self.selected_npc_id)
                    if npc:
                        npc.stat_source = f"monster:{m.name}"
                    self._npc_stat_link_mode = False
                    self.monster_picker_open = False
                    return True
                side = getattr(self, '_next_add_side', 'enemy')
                self._add_monster_to_encounter(m.name, side=side)
                self._next_add_side = "enemy"
                self.monster_picker_open = False
                return True
            y += 35
        return True

    def _handle_encounter_click(self, mp):
        mx, my = mp
        # Monster picker
        if self._handle_monster_picker_click(mp):
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

    def _handle_world_click(self, mp):
        mx, my = mp
        # Item tooltip dismiss
        self.tooltip_item = ""

        # Monster picker (for NPC stat linking)
        if self._handle_monster_picker_click(mp):
            return

        if self.world_view == "locations":
            self._handle_world_locations_click(mp)
        elif self.world_view == "npcs":
            self._handle_world_npcs_click(mp)
        elif self.world_view == "shops":
            self._handle_world_shops_click(mp)
        elif self.world_view == "shop_detail":
            self._handle_world_shop_detail_click(mp)

    def _handle_world_locations_click(self, mp):
        mx, my = mp
        y = 70 + self.scroll_y
        # Render location tree and check clicks
        roots = get_root_locations(self.world)
        for loc in roots:
            y = self._check_location_tree_click(loc, mp, y, 0)

        # Right panel NPC list clicks at location
        if self.selected_location_id:
            npcs = get_npcs_at_location(self.world, self.selected_location_id)
            npc_y = 280
            for npc in npcs:
                rect = pygame.Rect(SCREEN_WIDTH // 2 + 30, npc_y, SCREEN_WIDTH // 2 - 70, 40)
                if rect.collidepoint(mp):
                    self.selected_npc_id = npc.id
                    self.world_view = "npcs"
                    return
                npc_y += 45

    def _check_location_tree_click(self, loc, mp, y, depth):
        indent = 20 + depth * 25
        rect = pygame.Rect(indent, y, SCREEN_WIDTH // 2 - indent - 20, 35)
        if rect.collidepoint(mp):
            if self.selected_location_id == loc.id:
                # Toggle expand
                if loc.id in self.world_location_expanded:
                    self.world_location_expanded.discard(loc.id)
                else:
                    self.world_location_expanded.add(loc.id)
            else:
                self.selected_location_id = loc.id
            return y + 40
        y += 40
        if loc.id in self.world_location_expanded:
            children = get_children(self.world, loc.id)
            for child in children:
                y = self._check_location_tree_click(child, mp, y, depth + 1)
        return y

    def _handle_world_npcs_click(self, mp):
        mx, my = mp
        # NPC search box
        search_rect = pygame.Rect(20, 68, 300, 28)
        if search_rect.collidepoint(mp):
            self.npc_search_active = True
            return
        self.npc_search_active = False

        # NPC list
        y = 105 + self.scroll_y
        npcs = list(self.world.npcs.values())
        if self.npc_search:
            npcs = search_npcs(self.world, self.npc_search)
        for npc in npcs:
            if not npc.active:
                continue
            rect = pygame.Rect(20, y, SCREEN_WIDTH // 2 - 40, 42)
            if rect.collidepoint(mp):
                self.selected_npc_id = npc.id
                return
            y += 48

    def _handle_world_shops_click(self, mp):
        # Shop list view
        y = 70 + self.scroll_y
        shopkeepers = get_shopkeepers(self.world)
        for npc in shopkeepers:
            rect = pygame.Rect(20, y, SCREEN_WIDTH // 2 - 40, 50)
            if rect.collidepoint(mp):
                self.selected_npc_id = npc.id
                self.world_view = "shop_detail"
                self._refresh_shop_suggestions(npc.id)
                return
            y += 55

    def _handle_world_shop_detail_click(self, mp):
        mx, my = mp
        npc = self.world.npcs.get(self.selected_npc_id)
        if not npc:
            return

        # Item search for adding
        search_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 68, 300, 28)
        if search_rect.collidepoint(mp):
            self.shop_item_search_active = True
            return
        self.shop_item_search_active = False

        # Check item list clicks for adding from search
        if self.shop_item_search:
            y = 105
            q = self.shop_item_search.lower()
            count = 0
            for name in sorted(ITEM_PRICES.keys()):
                if q not in name.lower():
                    continue
                rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, y, SCREEN_WIDTH // 2 - 60, 28)
                if rect.collidepoint(mp):
                    self._add_shop_item_to_npc(npc.id, name)
                    self.shop_item_search = ""
                    return
                y += 32
                count += 1
                if count >= 12:
                    break

        # Check suggestion clicks
        if self.shop_suggestions:
            sug_y = SCREEN_HEIGHT - 230
            for sug in self.shop_suggestions:
                rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, sug_y, SCREEN_WIDTH // 2 - 60, 24)
                if rect.collidepoint(mp):
                    self._add_shop_item_to_npc(npc.id, sug["name"])
                    self._refresh_shop_suggestions(npc.id)
                    return
                sug_y += 28

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
        elif self.input_active == "location_name":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.name = self.input_text
        elif self.input_active == "location_desc":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.description = self.input_text
        elif self.input_active == "location_notes":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.notes = self.input_text
        elif self.input_active == "npc_name":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.name = self.input_text
        elif self.input_active == "npc_race":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.race = self.input_text
        elif self.input_active == "npc_occupation":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.occupation = self.input_text
        elif self.input_active == "npc_appearance":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.appearance = self.input_text
        elif self.input_active == "npc_personality":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.personality = self.input_text
        elif self.input_active == "npc_backstory":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.backstory = self.input_text
        elif self.input_active == "npc_notes":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.notes = self.input_text
        elif self.input_active == "shop_name":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.shop_name = self.input_text
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
        # Clear tooltip if not in world tab or mouse moved away
        if self.active_tab != 4:
            self.tooltip_item = ""

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
        elif self.active_tab == 4:
            self._draw_world_tab(screen, mp)

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
        elif self.active_tab == 4:
            self.btn_add_location.draw(screen, mp)
            self.btn_add_npc.draw(screen, mp)
            self.btn_world_npcs_view.draw(screen, mp)
            self.btn_world_shops_view.draw(screen, mp)

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

    # ---- World Tab Drawing ----

    def _draw_world_tab(self, screen, mp):
        if self.world_view == "locations":
            self._draw_world_locations(screen, mp)
        elif self.world_view == "npcs":
            self._draw_world_npcs(screen, mp)
        elif self.world_view == "shops":
            self._draw_world_shops(screen, mp)
        elif self.world_view == "shop_detail":
            self._draw_world_shop_detail(screen, mp)

        # Draw tooltip if hovering an item
        if self.tooltip_item:
            self._draw_item_tooltip(screen, mp)

    def _draw_world_locations(self, screen, mp):
        """Draw location tree (left) and selected location detail (right)."""
        y = 70 + self.scroll_y
        mid = SCREEN_WIDTH // 2

        # Left panel header
        hl = fonts.small_bold.render("Locations", True, COLORS["text_dim"])
        screen.blit(hl, (30, y))
        loc_count = len(self.world.locations)
        ct = fonts.tiny.render(f"({loc_count})", True, COLORS["text_muted"])
        screen.blit(ct, (110, y + 3))
        y += 25

        # Location tree
        roots = get_root_locations(self.world)
        if not roots:
            hint = fonts.body.render("No locations yet. Click '+ Location' to add one.", True, COLORS["text_muted"])
            screen.blit(hint, (30, y))
        else:
            for loc in roots:
                y = self._draw_location_tree_item(screen, mp, loc, y, 0, mid)

        # Right panel: selected location detail
        if self.selected_location_id:
            self._draw_location_detail(screen, mp, mid + 20)

    def _draw_location_tree_item(self, screen, mp, loc, y, depth, max_x):
        indent = 20 + depth * 25
        w = max_x - indent - 20
        is_sel = loc.id == self.selected_location_id
        is_expanded = loc.id in self.world_location_expanded
        has_children = bool(loc.children_ids)

        rect = pygame.Rect(indent, y, w, 32)
        bg = COLORS["selected"] if is_sel else COLORS["panel"]
        if rect.collidepoint(mp):
            bg = COLORS["hover"]
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        if is_sel:
            pygame.draw.rect(screen, COLORS["accent_dim"], rect, 1, border_radius=4)

        # Expand/collapse indicator
        if has_children:
            arrow = "v" if is_expanded else ">"
            at = fonts.small.render(arrow, True, COLORS["text_dim"])
            screen.blit(at, (indent + 4, y + 8))

        # Type icon
        type_colors = {
            "country": COLORS["legendary"], "region": COLORS["spell"],
            "city": COLORS["accent"], "town": COLORS["accent"],
            "village": COLORS["success"], "building": COLORS["warning"],
            "tavern": COLORS["fire"], "shop": COLORS["legendary"],
            "temple": COLORS["radiant"], "dungeon": COLORS["danger"],
            "wilderness": COLORS["success"], "cave": COLORS["text_dim"],
        }
        tc = type_colors.get(loc.location_type, COLORS["text_dim"])
        tt = fonts.tiny.render(loc.location_type[:5].upper(), True, tc)
        screen.blit(tt, (indent + 18, y + 10))

        # Name
        nt = fonts.body.render(loc.name, True, COLORS["text_bright"])
        screen.blit(nt, (indent + 65, y + 6))

        # NPC count
        npc_count = len([n for n in self.world.npcs.values() if n.location_id == loc.id and n.active])
        if npc_count > 0:
            nc = fonts.tiny.render(f"{npc_count} NPC", True, COLORS["player"])
            screen.blit(nc, (indent + w - 60, y + 10))

        y += 38
        if is_expanded:
            children = get_children(self.world, loc.id)
            for child in children:
                y = self._draw_location_tree_item(screen, mp, child, y, depth + 1, max_x)
        return y

    def _draw_location_detail(self, screen, mp, start_x):
        loc = self.world.locations.get(self.selected_location_id)
        if not loc:
            return
        y = 70

        # Breadcrumb
        path = get_location_path(self.world, loc.id)
        if len(path) > 1:
            crumbs = " > ".join(p.name for p in path)
            bt = fonts.tiny.render(crumbs, True, COLORS["text_muted"])
            screen.blit(bt, (start_x, y))
            y += 18

        # Name (editable)
        hdr = fonts.header.render(loc.name, True, COLORS["accent"])
        screen.blit(hdr, (start_x, y))
        name_rect = pygame.Rect(start_x, y, hdr.get_width() + 50, 28)
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "location_name"
            self.input_text = loc.name
            self.modal = ("edit_field", "location_name")
        y += 32

        # Type selector
        tt = fonts.small_bold.render("Type:", True, COLORS["text_dim"])
        screen.blit(tt, (start_x, y))
        tx = start_x + 50
        for lt in LOCATION_TYPES[:12]:
            is_active = loc.location_type == lt
            pill_w = fonts.tiny.size(lt)[0] + 12
            pill_rect = pygame.Rect(tx, y, pill_w, 20)
            bg = COLORS["accent_dim"] if is_active else COLORS["panel"]
            if pill_rect.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    loc.location_type = lt
            pygame.draw.rect(screen, bg, pill_rect, border_radius=8)
            pt = fonts.tiny.render(lt, True, COLORS["text_bright"] if is_active else COLORS["text_dim"])
            screen.blit(pt, (tx + 6, y + 3))
            tx += pill_w + 4
            if tx > SCREEN_WIDTH - 50:
                tx = start_x + 50
                y += 24
        y += 28

        # Environment & Lighting
        env_label = fonts.small_bold.render("Env:", True, COLORS["text_dim"])
        screen.blit(env_label, (start_x, y))
        envs = ["outdoor", "indoor", "underground", "underwater"]
        ex = start_x + 40
        for env in envs:
            is_act = loc.environment == env
            ew = fonts.tiny.size(env)[0] + 12
            er = pygame.Rect(ex, y, ew, 20)
            bg = COLORS["success"] if is_act else COLORS["panel"]
            if er.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    loc.environment = env
            pygame.draw.rect(screen, bg, er, border_radius=8)
            et = fonts.tiny.render(env, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(et, (ex + 6, y + 3))
            ex += ew + 4
        y += 25

        light_label = fonts.small_bold.render("Light:", True, COLORS["text_dim"])
        screen.blit(light_label, (start_x, y))
        lights = ["bright", "dim", "darkness"]
        lx = start_x + 50
        for lt in lights:
            is_act = loc.lighting == lt
            lw = fonts.tiny.size(lt)[0] + 12
            lr = pygame.Rect(lx, y, lw, 20)
            light_cols = {"bright": COLORS["warning"], "dim": (120, 100, 80), "darkness": (40, 40, 60)}
            bg = light_cols.get(lt, COLORS["panel"]) if is_act else COLORS["panel"]
            if lr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    loc.lighting = lt
            pygame.draw.rect(screen, bg, lr, border_radius=8)
            ft = fonts.tiny.render(lt, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(ft, (lx + 6, y + 3))
            lx += lw + 4
        y += 30

        # Description
        desc_label = fonts.small_bold.render("Description:", True, COLORS["text_dim"])
        screen.blit(desc_label, (start_x, y))
        y += 18
        desc_rect = pygame.Rect(start_x, y, SCREEN_WIDTH - start_x - 30, 40)
        pygame.draw.rect(screen, COLORS["input_bg"], desc_rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], desc_rect, 1, border_radius=4)
        dt = loc.description or "(Click to add description)"
        dc = COLORS["text_main"] if loc.description else COLORS["text_muted"]
        ds = fonts.small.render(dt[:90], True, dc)
        screen.blit(ds, (start_x + 5, y + 5))
        if desc_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "location_desc"
            self.input_text = loc.description
            self.modal = ("edit_field", "location_desc")
        y += 48

        # NPCs at this location
        npcs = get_npcs_at_location(self.world, loc.id)
        nl = fonts.small_bold.render(f"NPCs here ({len(npcs)}):", True, COLORS["text_dim"])
        screen.blit(nl, (start_x, y))
        y += 20
        for npc in npcs:
            npc_rect = pygame.Rect(start_x, y, SCREEN_WIDTH - start_x - 30, 35)
            is_hover = npc_rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, npc_rect, border_radius=4)

            # Shopkeeper badge
            nx = start_x + 8
            if npc.is_shopkeeper:
                badge_w = Badge.draw(screen, nx, y + 8, "SHOP", COLORS["legendary"], fonts.tiny)
                nx += badge_w + 5

            nt = fonts.body.render(npc.name, True, COLORS["text_bright"])
            screen.blit(nt, (nx, y + 3))
            if npc.occupation:
                ot = fonts.tiny.render(npc.occupation, True, COLORS["text_dim"])
                screen.blit(ot, (nx, y + 21))
            if npc.race:
                rt = fonts.tiny.render(npc.race, True, COLORS["text_muted"])
                screen.blit(rt, (nx + nt.get_width() + 10, y + 6))

            # Attitude indicator
            att_cols = {"friendly": COLORS["success"], "neutral": COLORS["text_dim"],
                        "unfriendly": COLORS["warning"], "hostile": COLORS["danger"]}
            att_col = att_cols.get(npc.attitude, COLORS["text_dim"])
            at = fonts.tiny.render(npc.attitude, True, att_col)
            screen.blit(at, (npc_rect.right - at.get_width() - 10, y + 12))

            y += 40

        # Notes
        y += 10
        notes_label = fonts.small_bold.render("Location Notes:", True, COLORS["text_dim"])
        screen.blit(notes_label, (start_x, y))
        y += 18
        note_rect = pygame.Rect(start_x, y, SCREEN_WIDTH - start_x - 30, 45)
        pygame.draw.rect(screen, COLORS["input_bg"], note_rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], note_rect, 1, border_radius=4)
        note_text = loc.notes or "(Click to add notes)"
        nc = COLORS["text_main"] if loc.notes else COLORS["text_muted"]
        ns = fonts.small.render(note_text[:100], True, nc)
        screen.blit(ns, (start_x + 5, y + 5))
        if note_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "location_notes"
            self.input_text = loc.notes
            self.modal = ("edit_field", "location_notes")

        # Delete location button
        del_y = note_rect.bottom + 15
        del_rect = pygame.Rect(start_x, del_y, 140, 30)
        is_del_hover = del_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if is_del_hover else COLORS["danger"],
                         del_rect, border_radius=4)
        dlt = fonts.small.render("Delete Location", True, COLORS["text_bright"])
        screen.blit(dlt, (start_x + 10, del_y + 6))
        if is_del_hover and pygame.mouse.get_pressed()[0]:
            self._delete_world_location(loc.id)

    def _draw_world_npcs(self, screen, mp):
        """Draw NPC list (left) and selected NPC detail (right)."""
        mid = SCREEN_WIDTH // 2

        # Search bar
        search_rect = pygame.Rect(20, 68, 300, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["input_focus"] if self.npc_search_active else COLORS["border"],
                         search_rect, 1, border_radius=3)
        st = fonts.small.render(self.npc_search or "Search NPCs...", True,
                                COLORS["text_main"] if self.npc_search else COLORS["text_muted"])
        screen.blit(st, (search_rect.x + 5, search_rect.y + 5))

        # NPC list
        y = 105 + self.scroll_y
        npcs = list(self.world.npcs.values())
        if self.npc_search:
            npcs = search_npcs(self.world, self.npc_search)
        active_npcs = [n for n in npcs if n.active]

        if not active_npcs:
            hint = fonts.body.render("No NPCs yet. Click '+ NPC' to create one.", True, COLORS["text_muted"])
            screen.blit(hint, (30, y))
        else:
            for npc in active_npcs:
                is_sel = npc.id == self.selected_npc_id
                rect = pygame.Rect(20, y, mid - 40, 42)
                bg = COLORS["selected"] if is_sel else COLORS["panel"]
                if rect.collidepoint(mp):
                    bg = COLORS["hover"]
                pygame.draw.rect(screen, bg, rect, border_radius=5)
                if is_sel:
                    pygame.draw.rect(screen, COLORS["accent_dim"], rect, 1, border_radius=5)

                # Shopkeeper icon
                nx = rect.x + 8
                if npc.is_shopkeeper:
                    badge_w = Badge.draw(screen, nx, y + 12, "SHOP", COLORS["legendary"], fonts.tiny)
                    nx += badge_w + 5

                nt = fonts.body.render(npc.name, True, COLORS["text_bright"])
                screen.blit(nt, (nx, y + 3))

                info_parts = []
                if npc.race:
                    info_parts.append(npc.race)
                if npc.occupation:
                    info_parts.append(npc.occupation)
                # Location name
                loc = self.world.locations.get(npc.location_id)
                if loc:
                    info_parts.append(f"@ {loc.name}")
                info = " | ".join(info_parts)
                it = fonts.tiny.render(info, True, COLORS["text_dim"])
                screen.blit(it, (nx, y + 24))

                # Attitude color dot
                att_cols = {"friendly": COLORS["success"], "neutral": COLORS["text_dim"],
                            "unfriendly": COLORS["warning"], "hostile": COLORS["danger"]}
                att_col = att_cols.get(npc.attitude, COLORS["text_dim"])
                pygame.draw.circle(screen, att_col, (rect.right - 15, y + 21), 5)

                y += 48

        # Right panel: selected NPC detail
        if self.selected_npc_id:
            self._draw_npc_detail(screen, mp, mid + 20)

    def _draw_npc_detail(self, screen, mp, start_x):
        npc = self.world.npcs.get(self.selected_npc_id)
        if not npc:
            return
        y = 70

        # Name (editable)
        hdr = fonts.header.render(npc.name, True, COLORS["accent"])
        screen.blit(hdr, (start_x, y))
        name_rect = pygame.Rect(start_x, y, hdr.get_width() + 50, 28)
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_name"
            self.input_text = npc.name
            self.modal = ("edit_field", "npc_name")
        y += 32

        # Quick info fields
        fields = [
            ("Race", npc.race, "npc_race"),
            ("Occupation", npc.occupation, "npc_occupation"),
            ("Appearance", npc.appearance, "npc_appearance"),
            ("Personality", npc.personality, "npc_personality"),
            ("Backstory", npc.backstory, "npc_backstory"),
        ]
        for label, value, field_key in fields:
            fl = fonts.small_bold.render(f"{label}:", True, COLORS["text_dim"])
            screen.blit(fl, (start_x, y))
            field_rect = pygame.Rect(start_x + 95, y - 2, SCREEN_WIDTH - start_x - 130, 22)
            pygame.draw.rect(screen, COLORS["input_bg"], field_rect, border_radius=3)
            text = value or f"(set {label.lower()})"
            col = COLORS["text_main"] if value else COLORS["text_muted"]
            ft = fonts.small.render(text[:60], True, col)
            screen.blit(ft, (field_rect.x + 4, y))
            if field_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                self.input_active = field_key
                self.input_text = value
                self.modal = ("edit_field", field_key)
            y += 24

        # Attitude selector
        y += 5
        att_label = fonts.small_bold.render("Attitude:", True, COLORS["text_dim"])
        screen.blit(att_label, (start_x, y))
        ax = start_x + 75
        attitudes = ["friendly", "neutral", "unfriendly", "hostile"]
        att_cols = {"friendly": COLORS["success"], "neutral": COLORS["text_dim"],
                    "unfriendly": COLORS["warning"], "hostile": COLORS["danger"]}
        for att in attitudes:
            is_act = npc.attitude == att
            aw = fonts.tiny.size(att)[0] + 12
            ar = pygame.Rect(ax, y, aw, 20)
            bg = att_cols.get(att, COLORS["panel"]) if is_act else COLORS["panel"]
            if ar.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    npc.attitude = att
            pygame.draw.rect(screen, bg, ar, border_radius=8)
            at = fonts.tiny.render(att, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(at, (ax + 6, y + 3))
            ax += aw + 4
        y += 28

        # Location
        loc = self.world.locations.get(npc.location_id)
        loc_label = fonts.small_bold.render("Location:", True, COLORS["text_dim"])
        screen.blit(loc_label, (start_x, y))
        loc_name = loc.name if loc else "(none)"
        lt = fonts.small.render(loc_name, True, COLORS["accent"] if loc else COLORS["text_muted"])
        screen.blit(lt, (start_x + 75, y))
        y += 22

        # Stat source
        ss_label = fonts.small_bold.render("Stats:", True, COLORS["text_dim"])
        screen.blit(ss_label, (start_x, y))
        ss_text = npc.stat_source or "(no stat sheet linked)"
        ss_col = COLORS["text_main"] if npc.stat_source else COLORS["text_muted"]
        sst = fonts.small.render(ss_text, True, ss_col)
        screen.blit(sst, (start_x + 50, y))

        # Stat source picker buttons
        btn_x = start_x + 50 + sst.get_width() + 10
        # Link to monster
        m_btn = pygame.Rect(btn_x, y - 2, 80, 20)
        if m_btn.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["danger_hover"], m_btn, border_radius=3)
        else:
            pygame.draw.rect(screen, COLORS["danger"], m_btn, border_radius=3)
        mt = fonts.tiny.render("Monster", True, COLORS["text_bright"])
        screen.blit(mt, (m_btn.x + 5, m_btn.y + 3))
        if m_btn.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.monster_picker_open = True
            self.monster_search = ""
            self._npc_stat_link_mode = True
        y += 25

        # Shopkeeper toggle
        shop_btn = pygame.Rect(start_x, y, 140, 28)
        is_shop_hover = shop_btn.collidepoint(mp)
        shop_bg = COLORS["legendary"] if npc.is_shopkeeper else COLORS["panel"]
        if is_shop_hover:
            shop_bg = COLORS["hover"]
        pygame.draw.rect(screen, shop_bg, shop_btn, border_radius=5)
        shop_label = "Shopkeeper ON" if npc.is_shopkeeper else "Make Shopkeeper"
        slt = fonts.small.render(shop_label, True, COLORS["text_bright"])
        screen.blit(slt, (start_x + 10, y + 5))
        if is_shop_hover and pygame.mouse.get_pressed()[0]:
            self._toggle_shopkeeper(npc.id)
        y += 35

        # If shopkeeper, show shop info
        if npc.is_shopkeeper:
            self._draw_npc_shop_info(screen, mp, npc, start_x, y)
            y += 200  # Reserve space

        # Notes
        y += 5
        notes_label = fonts.small_bold.render("DM Notes:", True, COLORS["text_dim"])
        screen.blit(notes_label, (start_x, y))
        y += 18
        note_rect = pygame.Rect(start_x, y, SCREEN_WIDTH - start_x - 30, 45)
        pygame.draw.rect(screen, COLORS["input_bg"], note_rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], note_rect, 1, border_radius=4)
        note_text = npc.notes or "(Click to add notes)"
        nc = COLORS["text_main"] if npc.notes else COLORS["text_muted"]
        ns = fonts.small.render(note_text[:100], True, nc)
        screen.blit(ns, (start_x + 5, y + 5))
        if note_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_notes"
            self.input_text = npc.notes
            self.modal = ("edit_field", "npc_notes")

        # Delete NPC button
        del_y = note_rect.bottom + 10
        del_rect = pygame.Rect(start_x, del_y, 120, 28)
        is_del_hover = del_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if is_del_hover else COLORS["danger"],
                         del_rect, border_radius=4)
        dlt = fonts.small.render("Delete NPC", True, COLORS["text_bright"])
        screen.blit(dlt, (start_x + 10, del_y + 5))
        if is_del_hover and pygame.mouse.get_pressed()[0]:
            self._delete_world_npc(npc.id)

    def _draw_npc_shop_info(self, screen, mp, npc, start_x, y):
        """Draw inline shop info for a shopkeeper NPC."""
        # Shop name
        sn_label = fonts.small_bold.render("Shop:", True, COLORS["text_dim"])
        screen.blit(sn_label, (start_x, y))
        sn_rect = pygame.Rect(start_x + 45, y - 2, 250, 22)
        pygame.draw.rect(screen, COLORS["input_bg"], sn_rect, border_radius=3)
        snt = fonts.small.render(npc.shop_name or "(name)", True,
                                  COLORS["text_main"] if npc.shop_name else COLORS["text_muted"])
        screen.blit(snt, (sn_rect.x + 4, y))
        if sn_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "shop_name"
            self.input_text = npc.shop_name
            self.modal = ("edit_field", "shop_name")
        y += 25

        # Shop type selector
        st_label = fonts.small_bold.render("Type:", True, COLORS["text_dim"])
        screen.blit(st_label, (start_x, y))
        tx = start_x + 45
        for stype in get_all_shop_types():
            is_act = npc.shop_type == stype["key"]
            sw = fonts.tiny.size(stype["icon"])[0] + 12
            sr = pygame.Rect(tx, y, sw + 4, 20)
            bg = COLORS["legendary"] if is_act else COLORS["panel"]
            if sr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    npc.shop_type = stype["key"]
                # Show tooltip with name
                self.tooltip_item = f"__shop_type__{stype['key']}"
                self.tooltip_pos = mp
            pygame.draw.rect(screen, bg, sr, border_radius=3)
            sit = fonts.tiny.render(stype["icon"], True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(sit, (tx + 4, y + 3))
            tx += sw + 8
        y += 25

        # Price modifier selector
        pm_label = fonts.small_bold.render("Prices:", True, COLORS["text_dim"])
        screen.blit(pm_label, (start_x, y))
        px = start_x + 55
        price_labels = [("very_cheap", "Very Cheap"), ("cheap", "Cheap"),
                        ("normal", "Normal"), ("expensive", "Expensive"),
                        ("very_expensive", "Very Exp."), ("ripoff", "Ripoff")]
        for key, label in price_labels:
            is_act = npc.price_modifier == key
            pw = fonts.tiny.size(label)[0] + 10
            pr = pygame.Rect(px, y, pw, 18)
            bg = COLORS["success"] if is_act and key in ("very_cheap", "cheap") else (
                COLORS["danger"] if is_act and key in ("very_expensive", "ripoff") else (
                    COLORS["accent"] if is_act else COLORS["panel"]))
            if pr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    npc.price_modifier = key
                    # Recalculate prices
                    for si in npc.shop_items:
                        si.current_price_gp = apply_price_modifier(si.base_price_gp, key)
            pygame.draw.rect(screen, bg, pr, border_radius=8)
            pt = fonts.tiny.render(label, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(pt, (px + 5, y + 2))
            px += pw + 4
        y += 22

        # Auto-populate button
        auto_rect = pygame.Rect(start_x, y, 150, 25)
        auto_hover = auto_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["accent_hover"] if auto_hover else COLORS["accent"],
                         auto_rect, border_radius=4)
        aut = fonts.small.render("Auto-Fill Stock", True, COLORS["text_bright"])
        screen.blit(aut, (start_x + 10, y + 4))
        if auto_hover and pygame.mouse.get_pressed()[0]:
            self._auto_populate_shop(npc.id)

        # View full shop button
        view_rect = pygame.Rect(start_x + 160, y, 140, 25)
        view_hover = view_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["legendary"] if view_hover else COLORS["warning"],
                         view_rect, border_radius=4)
        vt = fonts.small.render("Full Shop View", True, COLORS["text_bright"])
        screen.blit(vt, (start_x + 170, y + 4))
        if view_hover and pygame.mouse.get_pressed()[0]:
            self.world_view = "shop_detail"
            self._refresh_shop_suggestions(npc.id)
        y += 30

        # Item count
        ic = fonts.tiny.render(f"{len(npc.shop_items)} items in stock", True, COLORS["text_dim"])
        screen.blit(ic, (start_x, y))

    def _draw_world_shops(self, screen, mp):
        """Draw all shopkeepers list view."""
        y = 70 + self.scroll_y
        hl = fonts.header.render("Shops & Merchants", True, COLORS["legendary"])
        screen.blit(hl, (30, y))
        y += 35

        shopkeepers = get_shopkeepers(self.world)
        if not shopkeepers:
            hint = fonts.body.render("No shopkeepers yet. Create an NPC and toggle 'Shopkeeper'.", True, COLORS["text_muted"])
            screen.blit(hint, (30, y))
            return

        for npc in shopkeepers:
            rect = pygame.Rect(20, y, SCREEN_WIDTH - 60, 48)
            is_hover = rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, COLORS["border"], rect, 1, border_radius=5)

            # Shop type icon
            shop_info = SHOP_TYPES.get(npc.shop_type, {})
            icon = shop_info.get("icon", "??")
            icon_t = fonts.body_bold.render(icon, True, COLORS["legendary"])
            screen.blit(icon_t, (rect.x + 10, y + 5))

            # Shop name
            snt = fonts.body_bold.render(npc.shop_name or npc.name, True, COLORS["text_bright"])
            screen.blit(snt, (rect.x + 45, y + 3))

            # NPC name and info
            info_parts = [npc.name]
            loc = self.world.locations.get(npc.location_id)
            if loc:
                info_parts.append(f"@ {loc.name}")
            info_parts.append(f"{len(npc.shop_items)} items")
            price_label = npc.price_modifier.replace("_", " ").title()
            if npc.price_modifier != "normal":
                info_parts.append(price_label)
            info = " | ".join(info_parts)
            it = fonts.tiny.render(info, True, COLORS["text_dim"])
            screen.blit(it, (rect.x + 45, y + 25))

            y += 55

    def _draw_world_shop_detail(self, screen, mp):
        """Full shop inventory view with item tooltips."""
        npc = self.world.npcs.get(self.selected_npc_id)
        if not npc:
            self.world_view = "shops"
            return

        mid = SCREEN_WIDTH // 2

        # Left panel: current inventory
        y = 70
        # Back button
        back_rect = pygame.Rect(20, y, 70, 25)
        if back_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["accent_hover"], back_rect, border_radius=3)
            if pygame.mouse.get_pressed()[0]:
                self.world_view = "npcs"
        else:
            pygame.draw.rect(screen, COLORS["accent"], back_rect, border_radius=3)
        bt = fonts.small.render("< Back", True, COLORS["text_bright"])
        screen.blit(bt, (back_rect.x + 8, back_rect.y + 4))

        # Shop header
        shop_name = npc.shop_name or npc.name
        shop_type_info = SHOP_TYPES.get(npc.shop_type, {})
        hdr = fonts.header.render(shop_name, True, COLORS["legendary"])
        screen.blit(hdr, (100, y))
        if shop_type_info:
            st = fonts.small.render(shop_type_info.get("name", ""), True, COLORS["text_dim"])
            screen.blit(st, (100, y + 26))

        price_label = npc.price_modifier.replace("_", " ").title()
        mult = PRICE_MODIFIERS.get(npc.price_modifier, 1.0)
        pm_col = COLORS["success"] if mult < 1 else (COLORS["danger"] if mult > 1 else COLORS["text_dim"])
        pt = fonts.small.render(f"Prices: {price_label} ({mult:.0%})", True, pm_col)
        screen.blit(pt, (100, y + 42))
        y += 65

        # Inventory list
        il = fonts.small_bold.render(f"Inventory ({len(npc.shop_items)} items):", True, COLORS["text_dim"])
        screen.blit(il, (20, y))
        y += 20

        # Column headers
        headers = [("Item", 20), ("Base", 330), ("Price", 420), ("Qty", 510)]
        for label, hx in headers:
            ht = fonts.tiny.render(label, True, COLORS["text_muted"])
            screen.blit(ht, (hx, y))
        y += 16

        for idx, si in enumerate(npc.shop_items):
            if y > SCREEN_HEIGHT - 130:
                more = fonts.tiny.render(f"... {len(npc.shop_items) - idx} more items", True, COLORS["text_muted"])
                screen.blit(more, (20, y))
                break

            item_rect = pygame.Rect(18, y, mid - 35, 22)
            is_hover = item_rect.collidepoint(mp)
            if is_hover:
                pygame.draw.rect(screen, COLORS["hover"], item_rect, border_radius=2)
                self.tooltip_item = si.item_name
                self.tooltip_pos = mp

            # Item name
            rarity_cols = {"common": COLORS["text_main"], "uncommon": COLORS["success"],
                           "rare": COLORS["accent"], "very_rare": COLORS["spell"],
                           "legendary": COLORS["legendary"]}
            price = si.base_price_gp
            rarity = "common"
            if price > 50000:
                rarity = "legendary"
            elif price > 5000:
                rarity = "very_rare"
            elif price > 500:
                rarity = "rare"
            elif price > 100:
                rarity = "uncommon"
            name_col = rarity_cols.get(rarity, COLORS["text_main"])
            nt = fonts.small.render(si.item_name[:35], True, name_col)
            screen.blit(nt, (20, y + 2))

            # Base price
            bp = fonts.tiny.render(get_price_display(si.base_price_gp), True, COLORS["text_dim"])
            screen.blit(bp, (330, y + 4))

            # Current price
            cp_col = COLORS["success"] if si.current_price_gp < si.base_price_gp else (
                COLORS["danger"] if si.current_price_gp > si.base_price_gp else COLORS["text_main"])
            cp = fonts.small.render(get_price_display(si.current_price_gp), True, cp_col)
            screen.blit(cp, (420, y + 2))

            # Quantity
            qty_text = "inf" if si.quantity < 0 else str(si.quantity)
            qt = fonts.tiny.render(qty_text, True, COLORS["text_dim"])
            screen.blit(qt, (510, y + 4))

            # Remove button
            rm_rect = pygame.Rect(mid - 50, y + 2, 18, 18)
            if rm_rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["danger"], rm_rect, border_radius=2)
                if pygame.mouse.get_pressed()[0]:
                    self._remove_shop_item(npc.id, idx)
                    return
            xt = fonts.tiny.render("X", True, COLORS["text_dim"])
            screen.blit(xt, (rm_rect.x + 4, rm_rect.y + 1))

            y += 24

        # Right panel: add items
        rx = mid + 20
        ry = 70

        # Search items to add
        al = fonts.small_bold.render("Add Items:", True, COLORS["text_dim"])
        screen.blit(al, (rx, ry))
        ry += 22

        search_rect = pygame.Rect(rx, ry - 4, 300, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["input_focus"] if self.shop_item_search_active else COLORS["border"],
                         search_rect, 1, border_radius=3)
        sst = fonts.small.render(self.shop_item_search or "Search all items...", True,
                                  COLORS["text_main"] if self.shop_item_search else COLORS["text_muted"])
        screen.blit(sst, (search_rect.x + 5, search_rect.y + 5))
        ry += 30

        # Search results
        if self.shop_item_search:
            q = self.shop_item_search.lower()
            count = 0
            for name in sorted(ITEM_PRICES.keys()):
                if q not in name.lower():
                    continue
                price = ITEM_PRICES[name]
                result_rect = pygame.Rect(rx, ry, SCREEN_WIDTH - rx - 30, 26)
                is_hover = result_rect.collidepoint(mp)
                if is_hover:
                    pygame.draw.rect(screen, COLORS["hover"], result_rect, border_radius=3)
                    self.tooltip_item = name
                    self.tooltip_pos = mp
                nt = fonts.small.render(f"{name}", True, COLORS["text_bright"])
                screen.blit(nt, (rx + 5, ry + 4))
                pt = fonts.tiny.render(get_price_display(price), True, COLORS["text_dim"])
                screen.blit(pt, (rx + 300, ry + 6))
                # Add button
                add_r = pygame.Rect(SCREEN_WIDTH - 70, ry + 2, 30, 20)
                if add_r.collidepoint(mp):
                    pygame.draw.rect(screen, COLORS["success"], add_r, border_radius=3)
                else:
                    pygame.draw.rect(screen, COLORS["panel_light"], add_r, border_radius=3)
                at = fonts.tiny.render("+", True, COLORS["text_bright"])
                screen.blit(at, (add_r.x + 10, add_r.y + 2))

                ry += 30
                count += 1
                if count >= 12:
                    break
        else:
            # Show suggestions
            sl = fonts.small_bold.render("Suggestions:", True, COLORS["text_dim"])
            screen.blit(sl, (rx, ry))
            ry += 20
            # Refresh button
            ref_rect = pygame.Rect(rx + 100, ry - 20, 70, 20)
            if ref_rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["accent_hover"], ref_rect, border_radius=3)
                if pygame.mouse.get_pressed()[0]:
                    self._refresh_shop_suggestions(npc.id)
            else:
                pygame.draw.rect(screen, COLORS["accent"], ref_rect, border_radius=3)
            rt = fonts.tiny.render("Refresh", True, COLORS["text_bright"])
            screen.blit(rt, (ref_rect.x + 10, ref_rect.y + 3))

            for sug in self.shop_suggestions:
                result_rect = pygame.Rect(rx, ry, SCREEN_WIDTH - rx - 30, 24)
                is_hover = result_rect.collidepoint(mp)
                if is_hover:
                    pygame.draw.rect(screen, COLORS["hover"], result_rect, border_radius=3)
                    self.tooltip_item = sug["name"]
                    self.tooltip_pos = mp
                nt = fonts.small.render(sug["name"][:40], True, COLORS["text_bright"])
                screen.blit(nt, (rx + 5, ry + 3))
                pt = fonts.tiny.render(sug.get("price_display", ""), True, COLORS["text_dim"])
                screen.blit(pt, (rx + 320, ry + 5))
                ry += 28

    def _draw_item_tooltip(self, screen, mp):
        """Draw floating tooltip for hovered item."""
        name = self.tooltip_item
        if not name:
            return

        # Shop type tooltip
        if name.startswith("__shop_type__"):
            key = name[13:]
            stype = SHOP_TYPES.get(key, {})
            text = f"{stype.get('name', key)}: {stype.get('description', '')}"
        else:
            text = get_item_tooltip(name)
            if not text:
                # Fallback: just show price
                price = get_item_price(name)
                text = f"{name} — {get_price_display(price)}" if price else name

        if not text:
            return

        # Word wrap
        max_w = 350
        words = text.split()
        lines = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if fonts.small.size(test)[0] > max_w:
                if current:
                    lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        line_h = 18
        pad = 8
        tip_w = max(fonts.small.size(l)[0] for l in lines) + pad * 2
        tip_h = len(lines) * line_h + pad * 2

        # Position near mouse, keep on screen
        tx = min(mp[0] + 15, SCREEN_WIDTH - tip_w - 5)
        ty = min(mp[1] - tip_h - 5, SCREEN_HEIGHT - tip_h - 5)
        ty = max(5, ty)

        # Draw tooltip background
        tip_surf = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        tip_surf.fill((20, 20, 30, 230))
        screen.blit(tip_surf, (tx, ty))
        pygame.draw.rect(screen, COLORS["accent_dim"], (tx, ty, tip_w, tip_h), 1, border_radius=4)

        for i, line in enumerate(lines):
            lt = fonts.small.render(line, True, COLORS["text_bright"])
            screen.blit(lt, (tx + pad, ty + pad + i * line_h))

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
