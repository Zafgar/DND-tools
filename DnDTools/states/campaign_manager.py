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
import logging
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, Panel, fonts, TabBar, Badge, Divider, draw_gradient_rect
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores
from data.heroes import hero_list
from data.hero_import import export_hero, import_hero, import_heroes_from_file
from data.library import library
from data.campaign import (
    Campaign, PartyMember, CampaignEncounter, EncounterSlot,
    CampaignArea, CampaignNote, HeroRelationship,
    save_campaign, load_campaign,
    list_campaigns, CAMPAIGNS_DIR, _timestamp,
)
from data.world import (
    World, Location, NPC, ShopItem, NPCRelationship, MapRoute, MapPin,
    MapToken, MAP_TOKEN_TYPES,
    Quest, QuestObjective, QUEST_STATUSES, QUEST_TYPES, QUEST_PRIORITIES,
    MAP_PIN_TYPES,
    save_world, load_world, generate_id,
    add_location, add_npc, move_npc, delete_location, delete_npc,
    add_quest, delete_quest, get_quests_by_status, get_quests_for_npc,
    get_quests_for_location, get_active_quests, complete_quest, search_quests,
    get_root_locations, get_children, get_location_path,
    get_npcs_at_location, search_npcs, search_locations,
    populate_shop, get_shop_suggestions, get_shopkeepers,
    get_shopkeepers_at_location, LOCATION_TYPES,
    add_pin, remove_pin, get_pin_by_id, get_visible_pins,
    add_token, remove_token, get_token_by_id,
    get_route_distance_miles, estimate_route_miles_from_scale,
)
from data.shop_catalog import (
    get_item_price, get_item_tooltip, get_price_display,
    generate_shop_inventory, suggest_items_for_shop,
    get_all_shop_types, SHOP_TYPES, PRICE_MODIFIERS,
    apply_price_modifier, ITEM_PRICES, ITEM_TOOLTIPS,
)
from data.services import (
    LIFESTYLE_EXPENSES, INN_ROOM_PRICES, FOOD_AND_DRINK,
    HIRELINGS, SPELLCASTING_SERVICES, MISC_SERVICES, PROPERTY_PRICES,
    SERVICE_CATEGORIES, get_all_services, format_price,
    get_services_for_location_type,
)
from data.inn_templates import (
    INN_TEMPLATES, get_inn_template, get_inn_templates_by_tier,
    get_all_inn_tiers, apply_inn_template,
)
from data.shop_templates import (
    SHOP_TEMPLATES, get_shop_template, get_shop_templates_by_tier,
    get_shop_templates_by_type, apply_shop_template,
)
from data.travel import (
    MOUNTS, VEHICLES_LAND, VEHICLES_WATER, TRAVEL_PACE,
    PASSAGE_COSTS, TERRAIN_MODIFIERS, calculate_travel_time,
    format_travel_time, get_passage_cost,
)
from data.city_templates import (
    CITY_TEMPLATES, get_city_template, get_city_templates_by_tier,
    get_city_templates_by_type, apply_city_template,
)
from data.encounters import (
    calculate_encounter_difficulty, get_xp_for_cr, get_party_thresholds,
    CR_XP_TABLE, XP_THRESHOLDS, RANDOM_ENCOUNTERS,
    roll_random_encounter, get_encounter_environments,
    generate_loot, roll_magic_item, MAGIC_ITEM_TABLES,
)
from states.game_state_base import VariantRulesModal


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

        # NPC location picker
        self._npc_location_picker_open = False
        self._npc_stat_link_mode = False

        # Template browser state
        self.template_view = ""  # "", "inn_templates", "shop_templates"
        self.template_tier_filter = ""  # Filter by tier
        self.template_scroll = 0

        # Services / Travel viewer
        self.services_view = ""  # "", "services", "travel"
        self.services_category = "food_drink"
        self.services_scroll = 0
        self.travel_distance = 24  # Default travel distance in miles

        # Quest viewer
        self.selected_quest_id = ""
        self.quest_filter = "active"  # all, active, completed, failed, not_started, on_hold
        self.quest_search = ""
        self.quest_search_active = False

        # World map view state
        self.world_map_mode = False  # True = map view, False = tree view
        self.map_offset_x = 0
        self.map_offset_y = 0
        self.map_zoom = 1.0
        self.map_dragging = False
        self.map_drag_start = (0, 0)
        self.map_placing_location = ""  # location_id being placed on map

        # Location positions on map (id -> (x, y) percentage)
        self._location_map_positions: dict = {}
        self._load_map_positions()

        # Map background image and route mode
        self._map_bg_surface = None  # pygame.Surface for custom map background
        self._map_bg_scaled_cache = None  # Cached scaled version
        self._map_bg_cache_key = None     # (width, height) key for cache invalidation
        self._map_route_mode = False  # True = click two locations to create route
        self._map_route_from = ""  # First location ID when creating a route
        self._map_dragging_node = ""  # Location ID being dragged on map
        self._click_cooldown = 0  # Frame-based cooldown to prevent draw-loop spam
        self._map_pin_mode = False  # True = click to place a new pin
        self.selected_pin_id = ""  # Currently selected map pin ID
        self._load_map_background()

        # Map tokens
        self._map_dragging_token = ""  # Token ID being dragged
        self._map_token_mode = False   # True = click to place a new token
        self._map_token_type = "party" # Type for new token
        self.selected_token_id = ""    # Currently selected token

        # Map scale mode
        self._map_scale_mode = False   # True = click two points to set scale
        self._map_scale_point1 = None  # First point (pct_x, pct_y)
        self._map_scale_point2 = None  # Second point (pct_x, pct_y)
        self._map_scale_pct = 0.0      # Pct distance between points (set on 2nd click)

        # Map location detail popup
        self._map_detail_location_id = ""  # Location to show detail for
        self._map_detail_scroll = 0

        # Per-location sub-map surfaces
        self._location_map_surfaces: dict = {}  # loc_id -> pygame.Surface
        self._location_map_cache: dict = {}     # loc_id -> (scaled_surface, cache_key)
        self._current_sub_map_id = ""           # Currently viewing sub-map of this location

        # Hero relationship view state
        self.hero_rel_scroll = 0

        # Input state
        self.input_active = ""  # Which input field is active
        self.input_text = ""
        self.modal = None       # Active modal (note edit, encounter edit, etc.)
        self.variant_rules_modal = None  # DMG optional variant rules toggle modal

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
        self.monster_picker_expanded_cr = None    # Which CR category is expanded (None = all collapsed)
        self.monster_picker_expanded_type = None  # Which type subcategory is expanded

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
        self.btn_rules = Button(SCREEN_WIDTH - 250, 15, 110, 35, "Rules",
                                self._open_variant_rules_modal, color=COLORS["accent"])

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
        self.btn_world_shops_view = Button(500, SCREEN_HEIGHT - 60, 100, 45, "Shops",
                                            self._toggle_shops_view, color=COLORS["legendary"])
        self.btn_world_map_view = Button(608, SCREEN_HEIGHT - 60, 80, 45, "Map",
                                          self._toggle_map_view, color=COLORS["cold"])
        self.btn_add_quest = Button(696, SCREEN_HEIGHT - 60, 95, 45, "+ Quest",
                                      self._add_world_quest, color=COLORS["warning"])
        self.btn_world_quests = Button(799, SCREEN_HEIGHT - 60, 95, 45, "Quests",
                                        self._toggle_quests_view, color=COLORS["danger"])
        self.btn_world_templates = Button(902, SCREEN_HEIGHT - 60, 100, 45, "Templates",
                                           self._toggle_templates_view, color=COLORS["spell"])
        self.btn_world_services = Button(1010, SCREEN_HEIGHT - 60, 100, 45, "Services",
                                          self._toggle_services_view, color=COLORS["success"])
        self.btn_world_travel = Button(1118, SCREEN_HEIGHT - 60, 100, 45, "Travel",
                                        self._toggle_travel_view, color=COLORS["warning"])
        self.btn_open_map_editor = Button(1226, SCREEN_HEIGHT - 60, 130, 45, "Karttaeditori",
                                           self._open_map_editor, color=COLORS["accent"])
        # Phase 13a: bulk-import campaign data from a Markdown / text
        # file (Phase 12a). Sits at the right end of the World tab
        # action row.
        self.btn_import_text = Button(1360, SCREEN_HEIGHT - 60, 130, 45,
                                        "Tuo tekstistä...",
                                        self._import_text_file,
                                        color=COLORS["spell"])
        # Status string set by _import_text_file so the user sees what
        # actually happened (e.g. "5+ 2~ locations, 8+ NPCs").
        self._import_status: str = ""
        self._import_status_timer: int = 0

    def _load_world_from_campaign(self) -> World:
        """Load or create World from campaign's world_data."""
        if self.campaign.world_data:
            try:
                from data.world import _deserialize_location, _deserialize_npc, _deserialize_route, _deserialize_quest, MapRoute
                wd = self.campaign.world_data
                return World(
                    name=wd.get("name", self.campaign.name),
                    description=wd.get("description", ""),
                    created=wd.get("created", ""),
                    last_modified=wd.get("last_modified", ""),
                    locations={k: _deserialize_location(v) for k, v in wd.get("locations", {}).items()},
                    npcs={k: _deserialize_npc(v) for k, v in wd.get("npcs", {}).items()},
                    quests={k: _deserialize_quest(v) for k, v in wd.get("quests", {}).items()},
                    next_id=wd.get("next_id", 1),
                    map_routes=[_deserialize_route(r) for r in wd.get("map_routes", [])],
                    map_image_path=wd.get("map_image_path", ""),
                    map_positions=wd.get("map_positions", {}),
                )
            except Exception:
                pass
        return World(name=self.campaign.name)

    def _serialize_world(self) -> dict:
        """Serialize World to dict for campaign save."""
        from data.world import _serialize_location, _serialize_npc, _serialize_route, _serialize_quest
        w = self.world
        # Sync map positions into world before saving
        w.map_positions = dict(self._location_map_positions)
        return {
            "name": w.name,
            "description": w.description,
            "created": w.created,
            "last_modified": w.last_modified,
            "locations": {k: _serialize_location(v) for k, v in w.locations.items()},
            "npcs": {k: _serialize_npc(v) for k, v in w.npcs.items()},
            "quests": {k: _serialize_quest(v) for k, v in w.quests.items()},
            "next_id": w.next_id,
            "map_routes": [_serialize_route(r) for r in w.map_routes],
            "map_image_path": w.map_image_path,
            "map_positions": w.map_positions,
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

    def _open_variant_rules_modal(self):
        """Open DMG optional variant rules toggle modal (flanking, gritty, etc.)."""
        self.variant_rules_modal = VariantRulesModal(
            self.campaign, self._close_variant_rules_modal
        )

    def _close_variant_rules_modal(self, _result=None):
        self.variant_rules_modal = None

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

    # ---- Encounter Helpers ----

    def _calc_encounter_difficulty(self, enc):
        """Calculate difficulty for an encounter using DMG rules."""
        if not enc.slots:
            return None
        # Get party levels
        party_levels = []
        for m in self.campaign.party:
            if m.active:
                party_levels.append(m.hero_data.get("character_level", 1))
        if not party_levels:
            party_levels = [1]

        # Get monster CRs
        monster_crs = []
        for slot in enc.slots:
            if slot.side == "ally":
                continue
            # Try to look up CR from library
            cr_str = "0"
            try:
                stats = library.get_monster(slot.creature_name)
                cr_val = getattr(stats, 'challenge_rating', 0)
                if isinstance(cr_val, float):
                    if cr_val == 0.125:
                        cr_str = "1/8"
                    elif cr_val == 0.25:
                        cr_str = "1/4"
                    elif cr_val == 0.5:
                        cr_str = "1/2"
                    else:
                        cr_str = str(int(cr_val))
                else:
                    cr_str = str(cr_val)
            except (ValueError, AttributeError):
                pass
            for _ in range(slot.count):
                monster_crs.append(cr_str)

        if not monster_crs:
            return None
        return calculate_encounter_difficulty(monster_crs, party_levels)

    def _roll_encounter_loot(self, enc):
        """Generate loot for an encounter and add to loot_items."""
        # Determine CR range from encounter
        max_cr = 0
        for slot in enc.slots:
            if slot.side == "ally":
                continue
            try:
                stats = library.get_monster(slot.creature_name)
                cr = getattr(stats, 'challenge_rating', 0)
                if isinstance(cr, str):
                    cr = float(cr) if '/' not in cr else eval(cr)
                max_cr = max(max_cr, float(cr))
            except (ValueError, AttributeError):
                pass
        if max_cr <= 4:
            cr_range = "cr0-4"
        elif max_cr <= 10:
            cr_range = "cr5-10"
        elif max_cr <= 16:
            cr_range = "cr11-16"
        else:
            cr_range = "cr17+"

        num_enemies = sum(s.count for s in enc.slots if s.side != "ally")
        loot = generate_loot(cr_range, num_enemies, hoard=(num_enemies <= 3))
        if loot["type"] == "hoard":
            enc.loot_items.append(f"Hoard: {loot['coins']}")
            if loot["gems_art_magic"] != "—":
                enc.loot_items.append(f"  + {loot['gems_art_magic']}")
        else:
            for t in loot["treasures"]:
                enc.loot_items.append(t)
        self._status_msg = "Loot generated!"
        self._status_timer = 90

    def _roll_random_encounter(self, enc):
        """Roll a random encounter from tables and add to encounter slots."""
        # Determine environment and tier from current area
        env = "road"
        tier = "tier1"
        if self.campaign.party:
            max_lvl = max(m.hero_data.get("character_level", 1) for m in self.campaign.party if m.active)
            tier = "tier2" if max_lvl >= 5 else "tier1"
        # Check area environment
        if enc.area_name:
            for area in self.campaign.areas:
                if area.name == enc.area_name:
                    env_map = {"underground": "dungeon", "indoor": "urban", "outdoor": "forest"}
                    env = env_map.get(area.environment, "road")
                    break

        result = roll_random_encounter(env, tier)
        if result:
            enc.notes = (enc.notes or "") + f"\nRandom ({env}/{tier}): {result['encounter']} — {result.get('notes', '')}"
            self._status_msg = f"Random: {result['encounter']}"
            self._status_timer = 120

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

    def _toggle_map_view(self):
        self.world_map_mode = not self.world_map_mode
        if self.world_map_mode:
            self.world_view = "locations"

    def _toggle_templates_view(self):
        if self.world_view == "templates":
            self.world_view = "locations"
        else:
            self.world_view = "templates"
            self.template_view = "inn_templates"
            self.template_scroll = 0
            self.scroll_y = 0

    def _toggle_services_view(self):
        if self.world_view == "services":
            self.world_view = "locations"
        else:
            self.world_view = "services"
            self.services_scroll = 0
            self.scroll_y = 0

    def _toggle_travel_view(self):
        if self.world_view == "travel":
            self.world_view = "locations"
        else:
            self.world_view = "travel"
            self.scroll_y = 0

    def _add_world_quest(self):
        q = add_quest(self.world, f"Quest {self.world.next_id}")
        self.selected_quest_id = q.id
        self.world_view = "quests"

    def _toggle_quests_view(self):
        if self.world_view == "quests":
            self.world_view = "locations"
        else:
            self.world_view = "quests"
            self.scroll_y = 0

    def _open_map_editor(self):
        """Launch MapEditorState on the campaign's primary world map.

        Creates a top-level WorldMap the first time the DM opens the editor.
        Subsequent openings reuse the persisted map file.
        """
        import os
        from data.map_engine import (
            WorldMap, MAPS_DIR,
            save_world_map, load_world_map,
        )

        # Persist pending world edits before leaving the screen
        try:
            self.campaign.world_data = self._serialize_world()
        except Exception as ex:
            logging.warning(f"[MAP_EDITOR] Pre-save of world_data failed: {ex}")

        wm = None
        map_id = (self.campaign.active_map_id
                  or self.campaign.primary_world_map_id)
        if map_id:
            path = os.path.join(MAPS_DIR, f"{map_id}.json")
            if os.path.isfile(path):
                try:
                    wm = load_world_map(path)
                except Exception as ex:
                    logging.warning(f"[MAP_EDITOR] Load failed: {ex}")

        if wm is None:
            wm = WorldMap(
                name=f"{self.campaign.name} — maailma",
                map_type="world",
            )
            try:
                save_world_map(wm)
            except Exception as ex:
                logging.warning(f"[MAP_EDITOR] Initial save failed: {ex}")
            self.campaign.primary_world_map_id = wm.id
            self.campaign.active_map_id = wm.id

        self.manager.change_state(
            "MAP_EDITOR",
            world_map=wm,
            campaign=self.campaign,
            world=self.world,
            back_state="CAMPAIGN",
        )

    def _load_map_positions(self):
        """Load location map positions from world data."""
        if self.world.map_positions:
            self._location_map_positions = {k: tuple(v) for k, v in self.world.map_positions.items()}
        # Fallback: check legacy campaign settings
        elif self.campaign.settings and "map_positions" in self.campaign.settings:
            self._location_map_positions = dict(self.campaign.settings["map_positions"])

    def _save_map_positions(self):
        """Save location map positions to world data."""
        self.world.map_positions = {k: list(v) for k, v in self._location_map_positions.items()}

    def _load_map_background(self):
        """Load map background image if path is set. Large images are downscaled for performance."""
        self._map_bg_surface = None
        self._map_bg_scaled_cache = None
        self._map_bg_cache_key = None
        path = self.world.map_image_path
        if not path:
            return
        # Resolve relative paths against the project directory
        if not os.path.isabs(path):
            candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
            if os.path.isfile(candidate):
                path = candidate
        if not os.path.isfile(path):
            logging.warning(f"[MAP] Background image not found: {path}")
            self._status_msg = f"Map image not found: {os.path.basename(path)}"
            self._status_timer = 240
            return
        try:
            raw = pygame.image.load(path).convert()
            # Cap loaded image to max 4096 on longest side for memory/performance
            max_dim = 4096
            w, h = raw.get_size()
            if w > max_dim or h > max_dim:
                scale = max_dim / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                raw = pygame.transform.smoothscale(raw, (new_w, new_h))
            self._map_bg_surface = raw
        except Exception as ex:
            logging.warning(f"[MAP] Failed to load background image: {ex}")
            self._status_msg = f"Map load failed: {ex}"
            self._status_timer = 240
            self._map_bg_surface = None

    def _import_text_file(self):
        """Phase 13a: open a native file picker for a Markdown / text
        notes file and run it through ``data.text_import.import_text``
        + ``data.import_link.link_all`` so locations, NPCs, quests
        and notes are merged into the campaign in one click.

        Idempotent — re-importing the same file updates instead of
        duplicating. Status is shown via _import_status for ~5s.
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Choose a Markdown / text file to import",
                filetypes=[
                    ("Text files", "*.md *.markdown *.txt"),
                    ("All files", "*.*"),
                ],
            )
            root.destroy()
        except Exception as ex:
            self._import_status = f"File picker unavailable: {ex}"
            self._import_status_timer = 300
            logging.warning(f"[IMPORT] picker error: {ex}")
            return
        if not path:
            return
        try:
            from data.text_import import import_file
            from data.import_link import link_all
            report = import_file(self.world, path)
        except OSError as ex:
            self._import_status = f"Failed to read file: {ex}"
            self._import_status_timer = 300
            return
        # Second pass — auto-link to actor registry + place settlement
        # tokens onto the campaign's primary world map.
        link_report = None
        try:
            from data.actors import get_registry
            registry = get_registry()
            world_map = self._get_primary_world_map()
            link_report = link_all(self.world, world_map, registry)
        except Exception as ex:
            logging.warning(f"[IMPORT] link pass failed: {ex}")
        bits = [report.summary()]
        if link_report:
            link_summary = link_report.summary()
            if link_summary != "no links":
                bits.append(link_summary)
        self._import_status = "Tuotu: " + " · ".join(bits)
        self._import_status_timer = 300
        # Push to disk so the merged data survives a crash
        try:
            from data.campaign import save_campaign
            self.campaign.world_data = self._serialize_world(self.world)
            save_campaign(self.campaign)
        except Exception as ex:
            logging.warning(f"[IMPORT] auto-save failed: {ex}")

    def _get_primary_world_map(self):
        """Return the campaign's primary WorldMap, or None when none
        is configured / loadable."""
        wm_id = getattr(self.campaign, "primary_world_map_id", "")
        if not wm_id:
            return None
        try:
            from data.map_engine import (
                MAPS_DIR, load_world_map,
            )
            import os as _os
            path = _os.path.join(MAPS_DIR, f"{wm_id}.json")
            if _os.path.isfile(path):
                return load_world_map(path)
        except Exception:
            return None
        return None

    def _serialize_world(self, world) -> dict:
        """Best-effort World → dict for campaign.world_data."""
        try:
            from data.serialization import serialize
            return serialize(world)
        except Exception:
            try:
                from dataclasses import asdict
                return asdict(world)
            except Exception:
                return {}

    def _pick_image_file(self):
        """Open a native file picker for selecting an image. Returns path or ''."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Select map image",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("All files", "*.*"),
                ],
            )
            root.destroy()
            return path or ""
        except Exception as ex:
            logging.warning(f"[MAP] File picker unavailable: {ex}")
            return ""

    def _import_map_image(self, src_path: str) -> str:
        """Copy a selected image into the project's map backgrounds folder.
        Returns the relative path that should be stored in world.map_image_path."""
        if not src_path or not os.path.isfile(src_path):
            return ""
        try:
            import shutil, time
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dest_dir = os.path.join(base_dir, "saves", "map_backgrounds")
            os.makedirs(dest_dir, exist_ok=True)
            ext = os.path.splitext(src_path)[1].lower() or ".jpg"
            stamp = time.strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() else "_" for c in os.path.splitext(os.path.basename(src_path))[0])[:40]
            dest_name = f"{safe_name}_{stamp}{ext}"
            dest_path = os.path.join(dest_dir, dest_name)
            shutil.copy2(src_path, dest_path)
            # Return project-relative path for portability
            rel = os.path.relpath(dest_path, base_dir)
            return rel
        except Exception as ex:
            logging.warning(f"[MAP] Failed to import image: {ex}")
            return ""

    def _apply_template(self, template_type: str, template_key: str):
        """Apply a template to the current selected location."""
        parent_id = self.selected_location_id or ""
        if template_type == "inn":
            template = get_inn_template(template_key)
            if template:
                result = apply_inn_template(self.world, parent_id, template)
                self.selected_location_id = result["location_id"]
                if parent_id:
                    self.world_location_expanded.add(parent_id)
                self._status_msg = f"Created inn: {template['name']}"
                self._status_timer = 120
        elif template_type == "shop":
            template = get_shop_template(template_key)
            if template:
                result = apply_shop_template(self.world, parent_id, template)
                self.selected_location_id = result["location_id"]
                if parent_id:
                    self.world_location_expanded.add(parent_id)
                self._status_msg = f"Created shop: {template['name']}"
                self._status_timer = 120
        elif template_type == "city":
            template = get_city_template(template_key)
            if template:
                result = apply_city_template(self.world, parent_id, template)
                self.selected_location_id = result["location_id"]
                if parent_id:
                    self.world_location_expanded.add(parent_id)
                self.world_location_expanded.add(result["location_id"])
                self._status_msg = f"Created {template['settlement_type']}: {template['name']}"
                self._status_timer = 120

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
            if self.variant_rules_modal:
                self.variant_rules_modal.handle_event(event)
                continue
            if self.modal:
                self._handle_modal_event(event)
                continue

            # Tab bar
            self.tabs.handle_event(event)

            # Global buttons
            self.btn_back.handle_event(event)
            self.btn_save.handle_event(event)
            self.btn_rules.handle_event(event)
            for tb in self.time_buttons:
                tb.handle_event(event)

            # Scroll / Map zoom
            if event.type == pygame.MOUSEWHEEL:
                if self.active_tab == 4 and self.world_map_mode:
                    grid_area = self._get_map_grid_area()
                    if grid_area.collidepoint(mp):
                        if self._map_token_mode:
                            # Cycle token type while in token placement mode
                            types = list(MAP_TOKEN_TYPES.keys())
                            if types:
                                idx = types.index(self._map_token_type) if self._map_token_type in types else 0
                                self._map_token_type = types[(idx + event.y) % len(types)]
                        else:
                            old_zoom = self.map_zoom
                            self.map_zoom = max(0.2, min(5.0, self.map_zoom + event.y * 0.15))
                            # Zoom toward cursor
                            factor = self.map_zoom / old_zoom if old_zoom != 0 else 1
                            cx = grid_area.x + grid_area.width / 2
                            cy = grid_area.y + grid_area.height / 2
                            self.map_offset_x = (self.map_offset_x + cx - mp[0]) * factor + mp[0] - cx
                            self.map_offset_y = (self.map_offset_y + cy - mp[1]) * factor + mp[1] - cy
                    else:
                        self.scroll_y += event.y * 30
                elif self.hero_picker_open and mp[0] > SCREEN_WIDTH - 300:
                    self.hero_picker_scroll += event.y * 30
                elif self.monster_picker_open and mp[0] > SCREEN_WIDTH - 300:
                    self.monster_picker_scroll += event.y * 30
                else:
                    self.scroll_y += event.y * 30

            # Map pan (middle mouse) and node drag (left mouse)
            if self.active_tab == 4 and self.world_map_mode:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                    # Middle click → start panning
                    self.map_dragging = True
                    self.map_drag_start = mp
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                    self.map_dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.map_dragging:
                        dx = mp[0] - self.map_drag_start[0]
                        dy = mp[1] - self.map_drag_start[1]
                        self.map_offset_x += dx
                        self.map_offset_y += dy
                        self.map_drag_start = mp
                    elif self._map_dragging_node and pygame.mouse.get_pressed()[0]:
                        # Drag location node
                        grid_area = self._get_map_grid_area()
                        pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
                        pct_x = max(1, min(99, pct_x))
                        pct_y = max(1, min(99, pct_y))
                        self._location_map_positions[self._map_dragging_node] = (pct_x, pct_y)
                    elif self._map_dragging_token and pygame.mouse.get_pressed()[0]:
                        # Drag map token
                        grid_area = self._get_map_grid_area()
                        pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
                        pct_x = max(1, min(99, pct_x))
                        pct_y = max(1, min(99, pct_y))
                        tok = get_token_by_id(self.world, self._map_dragging_token)
                        if tok:
                            tok.map_x = pct_x
                            tok.map_y = pct_y
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self._map_dragging_node:
                        self._save_map_positions()
                        self._map_dragging_node = ""
                    if self._map_dragging_token:
                        self._map_dragging_token = ""
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    grid_area = self._get_map_grid_area()
                    if grid_area.collidepoint(mp):
                        try:
                            self._handle_map_click(mp, grid_area)
                        except Exception:
                            pass

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
                if self.quest_search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.quest_search = self.quest_search[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.quest_search_active = False
                    elif event.unicode.isprintable():
                        self.quest_search += event.unicode
                    continue
                if event.key == pygame.K_ESCAPE and (
                    self._map_route_mode or self._map_pin_mode
                    or self._map_token_mode or self._map_scale_mode
                    or self._map_detail_location_id
                ):
                    self._map_route_mode = False
                    self._map_route_from = ""
                    self._map_pin_mode = False
                    self._map_token_mode = False
                    self._map_scale_mode = False
                    self._map_scale_point1 = None
                    self._map_detail_location_id = ""
                    continue
                if event.key == pygame.K_ESCAPE and getattr(self, '_npc_location_picker_open', False):
                    self._npc_location_picker_open = False
                    continue
                if self.input_active:
                    self._handle_input_key(event)
                    continue

            # Tab-specific event handling
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Global: click on campaign name in header to rename
                name_rect = getattr(self, '_campaign_name_rect', None)
                if name_rect is not None and name_rect.collidepoint(mp):
                    self.input_active = "campaign_name"
                    self.input_buffer = self.campaign.name
                    continue
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
                self.btn_world_map_view.handle_event(event)
                self.btn_add_quest.handle_event(event)
                self.btn_world_quests.handle_event(event)
                self.btn_world_templates.handle_event(event)
                self.btn_world_services.handle_event(event)
                self.btn_world_travel.handle_event(event)
                self.btn_open_map_editor.handle_event(event)
                self.btn_import_text.handle_event(event)

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
        panel_x = SCREEN_WIDTH - 310
        if not (self.monster_picker_open and mx > panel_x):
            return False

        # Close button
        close_rect = pygame.Rect(panel_x + 250, 60, 40, 25)
        if close_rect.collidepoint(mp):
            self.monster_picker_open = False
            return True

        # Search box
        search_rect = pygame.Rect(panel_x + 10, 90, 270, 28)
        if search_rect.collidepoint(mp):
            self.monster_search_active = True
            return True
        self.monster_search_active = False

        all_monsters = library.get_all_monsters()
        y = 125 + self.monster_picker_scroll

        if self.monster_search:
            # Flat filtered list
            for m in all_monsters:
                if self.monster_search.lower() not in m.name.lower():
                    continue
                item_rect = pygame.Rect(panel_x + 10, y, 270, 26)
                if item_rect.collidepoint(mp):
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
                    return True
                y += 30
        else:
            # CR -> type -> monsters structure
            from collections import OrderedDict
            cr_groups = OrderedDict()
            for m in all_monsters:
                cr = m.challenge_rating
                if cr not in cr_groups:
                    cr_groups[cr] = {}
                ctype = m.creature_type or "Unknown"
                if ctype not in cr_groups[cr]:
                    cr_groups[cr][ctype] = []
                cr_groups[cr][ctype].append(m)

            for cr, type_groups in cr_groups.items():
                is_cr_expanded = self.monster_picker_expanded_cr == cr

                # CR header click
                cr_rect = pygame.Rect(panel_x + 5, y, 280, 26)
                if cr_rect.collidepoint(mp):
                    if is_cr_expanded:
                        self.monster_picker_expanded_cr = None
                        self.monster_picker_expanded_type = None
                    else:
                        self.monster_picker_expanded_cr = cr
                        self.monster_picker_expanded_type = None
                    return True
                y += 30

                if is_cr_expanded:
                    for ctype, monsters in sorted(type_groups.items()):
                        is_type_expanded = self.monster_picker_expanded_type == (cr, ctype)

                        type_rect = pygame.Rect(panel_x + 18, y, 260, 24)
                        if type_rect.collidepoint(mp):
                            if is_type_expanded:
                                self.monster_picker_expanded_type = None
                            else:
                                self.monster_picker_expanded_type = (cr, ctype)
                            return True
                        y += 28

                        if is_type_expanded:
                            for m in monsters:
                                item_rect = pygame.Rect(panel_x + 30, y, 248, 24)
                                if item_rect.collidepoint(mp):
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
                                    return True
                                y += 26
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

    def _handle_map_click(self, mp, grid_area):
        """Handle left-click on the map grid area."""
        import math as _math

        # --- Scale calibration mode: pick two points, then ask for miles ---
        if self._map_scale_mode:
            pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
            pct_x = max(0, min(100, pct_x))
            pct_y = max(0, min(100, pct_y))
            if not self._map_scale_point1:
                self._map_scale_point1 = (pct_x, pct_y)
                self._status_msg = "Scale: click second point"
                self._status_timer = 120
            else:
                p1 = self._map_scale_point1
                dist_pct = _math.hypot(pct_x - p1[0], pct_y - p1[1])
                if dist_pct > 0.5:
                    self._map_scale_point2 = (pct_x, pct_y)
                    self._map_scale_pct = dist_pct
                    # Open modal to ask for real distance
                    self.modal = ("edit_field", "scale_distance_miles")
                    self.input_active = "scale_distance_miles"
                    self.input_text = ""
                self._map_scale_mode = False
                self._map_scale_point1 = None
            return

        # --- Token click detection (highest priority among markers) ---
        clicked_token_id = ""
        for token in self.world.map_tokens:
            if not token.visible:
                continue
            tx, ty = self._map_to_screen(token.map_x, token.map_y, grid_area)
            tok_size = max(6, int(10 * self.map_zoom))
            hit_dist = tok_size + 4
            if abs(mp[0] - tx) < hit_dist and abs(mp[1] - ty) < hit_dist:
                clicked_token_id = token.id
                break

        # --- Token placement mode ---
        if self._map_token_mode:
            if clicked_token_id:
                # Clicked an existing token in placement mode: just select it
                self.selected_token_id = clicked_token_id
                self._map_dragging_token = clicked_token_id
                return
            pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
            pct_x = max(1, min(99, pct_x))
            pct_y = max(1, min(99, pct_y))
            tok_info = MAP_TOKEN_TYPES.get(self._map_token_type, MAP_TOKEN_TYPES.get("custom", {}))
            default_name = tok_info.get("label", "Token")
            new_tok = add_token(self.world, default_name, self._map_token_type, pct_x, pct_y)
            self.selected_token_id = new_tok.id
            self._map_token_mode = False
            self._status_msg = f"Placed {new_tok.name}"
            self._status_timer = 90
            return

        # --- Clicking an existing token (not in any mode): select + start drag ---
        if clicked_token_id and not self._map_route_mode and not self._map_pin_mode:
            self.selected_token_id = clicked_token_id
            self.selected_pin_id = ""
            self.selected_location_id = ""
            self._map_dragging_token = clicked_token_id
            return

        # Check if clicking on a map pin
        clicked_pin_id = ""
        for pin in self.world.map_pins:
            if not pin.visible:
                continue
            px, py = self._map_to_screen(pin.map_x, pin.map_y, grid_area)
            pin_size = max(4, int(7 * self.map_zoom))
            hit_dist = pin_size + 5
            if abs(mp[0] - px) < hit_dist and abs(mp[1] - py) < hit_dist:
                clicked_pin_id = pin.id
                break

        if clicked_pin_id and not self._map_route_mode and not self._map_pin_mode:
            self.selected_pin_id = clicked_pin_id
            self.selected_location_id = ""
            self.selected_token_id = ""
            return

        # Check if clicking on a location node
        clicked_loc_id = ""
        for loc_id, pos in self._location_map_positions.items():
            loc = self.world.locations.get(loc_id)
            if not loc:
                continue
            px, py = self._map_to_screen(pos[0], pos[1], grid_area)
            size = max(3, int(self._get_loc_size(loc) * self.map_zoom))
            hit_dist = size + 5
            if abs(mp[0] - px) < hit_dist and abs(mp[1] - py) < hit_dist:
                clicked_loc_id = loc_id
                break

        if self._map_route_mode:
            # Route creation mode
            if clicked_loc_id:
                if not self._map_route_from:
                    self._map_route_from = clicked_loc_id
                elif clicked_loc_id != self._map_route_from:
                    # Create route between the two locations
                    dist = estimate_route_miles_from_scale(self.world, self._map_route_from, clicked_loc_id)
                    self.world.map_routes.append(MapRoute(
                        from_id=self._map_route_from,
                        to_id=clicked_loc_id,
                        route_type="road",
                        label="",
                        distance_miles=dist,
                    ))
                    self._map_route_mode = False
                    self._map_route_from = ""
                    self._status_msg = "Route created"
                    self._status_timer = 90
            return

        if self._map_pin_mode:
            # Pin placement mode — place a new pin at clicked position
            pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
            pct_x = max(1, min(99, pct_x))
            pct_y = max(1, min(99, pct_y))
            new_pin = add_pin(self.world, "New Pin", "note", pct_x, pct_y)
            self.selected_pin_id = new_pin.id
            self._map_pin_mode = False
            return

        if clicked_loc_id:
            self.selected_pin_id = ""
            self.selected_token_id = ""
            if self.selected_location_id == clicked_loc_id:
                # Double-select: open location detail popup
                self._map_detail_location_id = clicked_loc_id
                self._map_detail_scroll = 0
            else:
                self.selected_location_id = clicked_loc_id
                self._map_dragging_node = clicked_loc_id
        else:
            # Clicked empty space
            if self.map_placing_location:
                # Place location at clicked position
                pct_x, pct_y = self._screen_to_map(mp[0], mp[1], grid_area)
                pct_x = max(1, min(99, pct_x))
                pct_y = max(1, min(99, pct_y))
                self._location_map_positions[self.map_placing_location] = (pct_x, pct_y)
                self._save_map_positions()
                self.map_placing_location = ""
            else:
                self.selected_location_id = ""
                self.selected_pin_id = ""
                self.selected_token_id = ""
                self._map_route_mode = False
                self._map_route_from = ""

    def _handle_world_click(self, mp):
        mx, my = mp
        # Item tooltip dismiss
        self.tooltip_item = ""

        # Monster picker (for NPC stat linking)
        if self._handle_monster_picker_click(mp):
            return

        if self.world_view == "locations":
            if not self.world_map_mode:
                self._handle_world_locations_click(mp)
        elif self.world_view == "npcs":
            self._handle_world_npcs_click(mp)
        elif self.world_view == "shops":
            self._handle_world_shops_click(mp)
        elif self.world_view == "shop_detail":
            self._handle_world_shop_detail_click(mp)
        elif self.world_view == "templates":
            self._handle_templates_click(mp)
        elif self.world_view == "services":
            self._handle_services_click(mp)
        elif self.world_view == "travel":
            self._handle_travel_click(mp)
        elif self.world_view == "quests":
            self._handle_quests_click(mp)

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

    # Fields that support multiline text input (Enter adds newline instead of saving)
    _MULTILINE_FIELDS = {
        "npc_backstory", "npc_notes", "npc_personality",
        "location_desc", "location_notes", "pin_description",
        "pin_notes", "quest_description", "quest_notes",
        "quest_reward_notes", "member_note", "note", "token_notes",
    }

    def _handle_input_key(self, event):
        if event.key == pygame.K_ESCAPE:
            # For multiline fields, Escape saves (since Enter adds newlines)
            if self.input_active in self._MULTILINE_FIELDS or (
                    self.input_active and self.input_active.startswith(("npc_rel_notes_", "hero_rel_desc_"))):
                self._apply_input()
            else:
                self.input_active = ""
                self.modal = None
            return
        if event.key == pygame.K_RETURN:
            # For multiline fields, Enter adds newline; Ctrl+Enter or Escape saves
            is_multiline = self.input_active in self._MULTILINE_FIELDS or (
                self.input_active and self.input_active.startswith(("npc_rel_notes_", "hero_rel_desc_")))
            mods = pygame.key.get_mods()
            if is_multiline and not (mods & pygame.KMOD_CTRL):
                self.input_text += "\n"
            else:
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
        elif self.input_active == "hero_add_relationship":
            if 0 <= self.selected_member_idx < len(self.campaign.party) and self.input_text.strip():
                member = self.campaign.party[self.selected_member_idx]
                # Auto-detect if target is an NPC or hero
                target_name = self.input_text.strip()
                target_type = "npc"
                target_id = ""
                # Check if it's an NPC in the world
                npc = self._find_npc_by_name(target_name)
                if npc:
                    target_id = npc.id
                    target_type = "npc"
                else:
                    # Check if it's a party member
                    for pm in self.campaign.party:
                        if pm.hero_data.get("name", "") == target_name:
                            target_type = "hero"
                            break
                member.relationships.append(HeroRelationship(
                    target_name=target_name,
                    target_id=target_id,
                    target_type=target_type,
                    attitude="neutral",
                ))
        elif self.input_active and self.input_active.startswith("hero_rel_desc_"):
            if 0 <= self.selected_member_idx < len(self.campaign.party):
                member = self.campaign.party[self.selected_member_idx]
                try:
                    ri = int(self.input_active.split("_")[-1])
                    if 0 <= ri < len(member.relationships):
                        member.relationships[ri].description = self.input_text
                except (ValueError, IndexError):
                    pass
        elif self.input_active == "hero_add_link":
            if 0 <= self.selected_member_idx < len(self.campaign.party) and self.input_text.strip():
                self.campaign.party[self.selected_member_idx].links.append(self.input_text.strip())
        elif self.input_active == "pin_name":
            pin = get_pin_by_id(self.world, self.selected_pin_id)
            if pin:
                pin.name = self.input_text
        elif self.input_active == "pin_description":
            pin = get_pin_by_id(self.world, self.selected_pin_id)
            if pin:
                pin.description = self.input_text
        elif self.input_active == "pin_notes":
            pin = get_pin_by_id(self.world, self.selected_pin_id)
            if pin:
                pin.notes = self.input_text
        elif self.input_active == "pin_add_link":
            pin = get_pin_by_id(self.world, self.selected_pin_id)
            if pin and self.input_text.strip():
                pin.links.append(self.input_text.strip())
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
        elif self.input_active == "npc_gender":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.gender = self.input_text
        elif self.input_active == "npc_age":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.age = self.input_text
        elif self.input_active == "npc_notes":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.notes = self.input_text
        elif self.input_active == "npc_gold":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                try:
                    npc.gold = float(self.input_text)
                except ValueError:
                    pass
        elif self.input_active == "npc_add_item":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc and self.input_text.strip():
                npc.inventory_items.append(self.input_text.strip())
        elif self.input_active == "npc_add_tag":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc and self.input_text.strip():
                npc.tags.append(self.input_text.strip())
        elif self.input_active == "npc_add_relationship":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc and self.input_text.strip():
                npc.relationships.append(NPCRelationship(
                    hero_name=self.input_text.strip(),
                    attitude="neutral",
                    notes=""
                ))
        elif self.input_active and self.input_active.startswith("npc_rel_notes_"):
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                try:
                    ri = int(self.input_active.split("_")[-1])
                    if 0 <= ri < len(npc.relationships):
                        npc.relationships[ri].notes = self.input_text
                except (ValueError, IndexError):
                    pass
        elif self.input_active == "shop_name":
            npc = self.world.npcs.get(self.selected_npc_id)
            if npc:
                npc.shop_name = self.input_text
        elif self.input_active == "map_image_path":
            self.world.map_image_path = self.input_text.strip()
            self._load_map_background()
        elif self.input_active == "map_scale_miles":
            try:
                self.world.map_scale_miles = float(self.input_text)
            except ValueError:
                pass
        elif self.input_active == "scale_distance_miles":
            try:
                miles = float(self.input_text)
                dist_pct = getattr(self, "_map_scale_pct", 0.0)
                if miles > 0 and dist_pct > 0.0:
                    self.world.map_scale_miles = miles * 100.0 / dist_pct
                    self._status_msg = f"Map scale set: {self.world.map_scale_miles:.1f} mi across"
                    self._status_timer = 150
            except ValueError:
                pass
            self._map_scale_point2 = None
            self._map_scale_pct = 0.0
        elif self.input_active == "loc_map_image":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.map_image_path = self.input_text.strip()
                # Clear cached surface
                self._location_map_surfaces.pop(self.selected_location_id, None)
                self._location_map_cache.pop(self.selected_location_id, None)
        elif self.input_active == "route_distance":
            if hasattr(self, '_editing_route_idx') and 0 <= self._editing_route_idx < len(self.world.map_routes):
                try:
                    self.world.map_routes[self._editing_route_idx].distance_miles = float(self.input_text)
                except ValueError:
                    pass
        elif self.input_active == "token_name":
            tok = get_token_by_id(self.world, self.selected_token_id)
            if tok:
                tok.name = self.input_text
        elif self.input_active == "token_notes":
            tok = get_token_by_id(self.world, self.selected_token_id)
            if tok:
                tok.notes = self.input_text
        elif self.input_active == "location_color":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.map_color = self.input_text.strip()
        elif self.input_active == "location_map_note":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.map_note = self.input_text.strip()
        elif self.input_active == "location_population":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                try:
                    loc.population = int(self.input_text)
                except ValueError:
                    pass
        elif self.input_active == "location_map_icon":
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                loc.map_icon = self.input_text.strip()[:4]
        elif self.input_active and self.input_active.startswith("quest_"):
            q = self.world.quests.get(self.selected_quest_id)
            if q:
                field_map = {
                    "quest_name": "name", "quest_description": "description",
                    "quest_notes": "notes", "quest_reward_notes": "reward_notes",
                    "quest_level_range": "level_range",
                }
                fname = field_map.get(self.input_active)
                if fname:
                    setattr(q, fname, self.input_text)
                elif self.input_active == "quest_reward_xp":
                    try:
                        q.reward_xp = int(self.input_text)
                    except ValueError:
                        pass
                elif self.input_active == "quest_reward_gold":
                    try:
                        q.reward_gold = float(self.input_text)
                    except ValueError:
                        pass
                elif self.input_active == "quest_add_tag":
                    if self.input_text.strip():
                        q.tags.append(self.input_text.strip())
                elif self.input_active == "quest_add_reward_item":
                    if self.input_text.strip():
                        q.reward_items.append(self.input_text.strip())
                elif self.input_active == "quest_add_objective":
                    if self.input_text.strip():
                        q.objectives.append(QuestObjective(description=self.input_text.strip()))
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
        if self._click_cooldown > 0:
            self._click_cooldown -= 1
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

        # Campaign name (clickable to rename)
        name_text = self.campaign.name
        nt = fonts.header.render(name_text, True, COLORS["accent"])
        name_rect = pygame.Rect(140, 12, max(nt.get_width() + 20, 120), 30)
        self._campaign_name_rect = name_rect
        if name_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["panel"], name_rect, border_radius=4)
            pygame.draw.rect(screen, COLORS["accent"], name_rect, 1, border_radius=4)
            hint = fonts.small.render("click to rename", True, COLORS["text_dim"])
            screen.blit(hint, (name_rect.right + 6, 20))
        screen.blit(nt, (150, 14))

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
        self.btn_rules.draw(screen, mp)
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

        # NPC location picker overlay
        if getattr(self, '_npc_location_picker_open', False):
            self._draw_npc_location_picker(screen, mp)

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
            self.btn_world_map_view.draw(screen, mp)
            self.btn_add_quest.draw(screen, mp)
            self.btn_world_quests.draw(screen, mp)
            self.btn_world_templates.draw(screen, mp)
            self.btn_world_services.draw(screen, mp)
            self.btn_world_travel.draw(screen, mp)
            self.btn_open_map_editor.draw(screen, mp)
            self.btn_import_text.draw(screen, mp)
            # Phase 13a: status line for text-import results
            if self._import_status_timer > 0:
                self._import_status_timer -= 1
                msg = fonts.small.render(self._import_status, True,
                                            COLORS.get("success",
                                                         (90, 200, 120)))
                screen.blit(msg, (20, SCREEN_HEIGHT - 90))

        # Modal overlay
        if self.modal:
            self._draw_modal(screen, mp)

        # Variant rules modal overlay
        if self.variant_rules_modal:
            self.variant_rules_modal.draw(screen, mp)

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
        y += 70

        # ---- Hero Relationships ----
        rel_label = fonts.small_bold.render("Relationships:", True, COLORS["text_dim"])
        screen.blit(rel_label, (30, y))
        # Add relationship button
        add_rel_btn = pygame.Rect(140, y - 2, 20, 20)
        is_addrel = add_rel_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_addrel else COLORS["panel"],
                         add_rel_btn, border_radius=3)
        pls = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(pls, (add_rel_btn.x + 5, add_rel_btn.y + 3))
        if is_addrel and pygame.mouse.get_pressed()[0]:
            self.input_active = "hero_add_relationship"
            self.input_text = ""
            self.modal = ("edit_field", "hero_add_relationship")
        y += 22

        hero_att_cols = {
            "friendly": COLORS["success"], "allied": (100, 200, 255),
            "neutral": COLORS["text_dim"], "unfriendly": COLORS["warning"],
            "hostile": COLORS["danger"], "romantic": (255, 100, 200),
            "rival": (200, 120, 50),
        }
        hero_attitudes = ["friendly", "allied", "neutral", "unfriendly", "hostile", "romantic", "rival"]

        if member.relationships:
            for ri, rel in enumerate(member.relationships):
                # Target name (clickable — navigates to NPC or hero)
                name_text = f"{rel.target_name}"
                type_tag = f" [{rel.target_type.upper()}]"
                nt_render = fonts.small.render(name_text, True, COLORS["accent"])
                name_rect = pygame.Rect(40, y, nt_render.get_width(), 18)
                screen.blit(nt_render, (40, y))
                tt = fonts.tiny.render(type_tag, True, COLORS["text_muted"])
                screen.blit(tt, (40 + nt_render.get_width() + 2, y + 2))

                # Clicking the name navigates to the NPC/hero
                if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                    if rel.target_type == "npc" and rel.target_id:
                        self.selected_npc_id = rel.target_id
                        self.active_tab = 4
                        self.tabs.active = 4
                        self.world_view = "npcs"
                    elif rel.target_type == "hero":
                        # Find hero in party by name
                        for pi, pm in enumerate(self.campaign.party):
                            if pm.hero_data.get("name", "") == rel.target_name:
                                self.selected_member_idx = pi
                                break
                y += 20

                # Attitude chips
                ax = 50
                for att in hero_attitudes:
                    is_act = rel.attitude == att
                    aw = fonts.tiny.size(att[:3])[0] + 10
                    ar = pygame.Rect(ax, y, aw, 16)
                    bg = hero_att_cols.get(att, COLORS["panel"]) if is_act else COLORS["panel"]
                    if ar.collidepoint(mp):
                        bg = COLORS["hover"]
                        if pygame.mouse.get_pressed()[0]:
                            rel.attitude = att
                    pygame.draw.rect(screen, bg, ar, border_radius=6)
                    at_t = fonts.tiny.render(att[:3], True,
                                             COLORS["text_bright"] if is_act else COLORS["text_muted"])
                    screen.blit(at_t, (ax + 4, y + 1))
                    ax += aw + 3

                # Description (short inline)
                desc_x = ax + 8
                desc_text = rel.description[:30] if rel.description else "(desc)"
                desc_col = COLORS["text_dim"] if rel.description else COLORS["text_muted"]
                dt = fonts.tiny.render(desc_text, True, desc_col)
                desc_rect = pygame.Rect(desc_x, y, dt.get_width() + 6, 16)
                screen.blit(dt, (desc_x, y + 1))
                if desc_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                    self.input_active = f"hero_rel_desc_{ri}"
                    self.input_text = rel.description
                    self.modal = ("edit_field", f"hero_rel_desc_{ri}")

                # Delete button
                del_x = desc_rect.right + 5
                del_r = pygame.Rect(del_x, y, 14, 16)
                if del_r.collidepoint(mp):
                    dxt = fonts.tiny.render("x", True, COLORS["danger"])
                    screen.blit(dxt, (del_x + 2, y + 1))
                    if pygame.mouse.get_pressed()[0]:
                        member.relationships.pop(ri)
                        break
                y += 20
        else:
            empty_rel = fonts.tiny.render("(no relationships — click + to add)", True, COLORS["text_muted"])
            screen.blit(empty_rel, (40, y))
            y += 20

        # ---- Hero Links (hyperlinks) ----
        y += 8
        link_label = fonts.small_bold.render("Links:", True, COLORS["text_dim"])
        screen.blit(link_label, (30, y))
        # Add link button
        add_link_btn = pygame.Rect(80, y - 2, 20, 20)
        is_addlink = add_link_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_addlink else COLORS["panel"],
                         add_link_btn, border_radius=3)
        pls2 = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(pls2, (add_link_btn.x + 5, add_link_btn.y + 3))
        if is_addlink and pygame.mouse.get_pressed()[0]:
            self.input_active = "hero_add_link"
            self.input_text = ""
            self.modal = ("edit_field", "hero_add_link")
        y += 22

        if member.links:
            for li, link in enumerate(member.links):
                # Link icon and text
                prefix = "WEB" if link.startswith("http") else "FILE"
                lp = fonts.tiny.render(f"[{prefix}]", True, COLORS["accent"])
                screen.blit(lp, (40, y + 1))
                lt_text = link if len(link) <= 60 else link[:57] + "..."
                lt_r = fonts.tiny.render(lt_text, True, COLORS["text_main"])
                link_rect = pygame.Rect(40 + lp.get_width() + 4, y, lt_r.get_width(), 16)
                screen.blit(lt_r, (link_rect.x, y + 1))
                # Click to open link
                if link_rect.collidepoint(mp):
                    # Underline effect on hover
                    pygame.draw.line(screen, COLORS["accent"],
                                     (link_rect.x, link_rect.bottom),
                                     (link_rect.right, link_rect.bottom), 1)
                    if pygame.mouse.get_pressed()[0]:
                        import webbrowser
                        try:
                            if link.startswith("http"):
                                webbrowser.open(link)
                            else:
                                os.startfile(link) if hasattr(os, 'startfile') else os.system(f'xdg-open "{link}"')
                        except Exception:
                            pass
                # Delete link
                del_lx = link_rect.right + 5
                del_lr = pygame.Rect(del_lx, y, 14, 16)
                if del_lr.collidepoint(mp):
                    dxt2 = fonts.tiny.render("x", True, COLORS["danger"])
                    screen.blit(dxt2, (del_lx + 2, y + 1))
                    if pygame.mouse.get_pressed()[0]:
                        member.links.pop(li)
                        break
                y += 18
        else:
            empty_link = fonts.tiny.render("(no links — click + to add URL or file path)", True, COLORS["text_muted"])
            screen.blit(empty_link, (40, y))
            y += 18

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

        # --- Encounter Difficulty Calculator ---
        diff_info = self._calc_encounter_difficulty(enc)
        if diff_info:
            diff_colors = {
                "trivial": COLORS["text_muted"], "easy": COLORS["success"],
                "medium": COLORS["warning"], "hard": COLORS["danger"],
                "deadly": (200, 30, 30),
            }
            dc = diff_colors.get(diff_info["difficulty"], COLORS["text_dim"])
            Divider.draw(screen, start_x, y, 480)
            y += 6
            dl = fonts.small_bold.render("Encounter Difficulty:", True, COLORS["text_dim"])
            screen.blit(dl, (start_x, y))
            Badge.draw(screen, start_x + 155, y + 1, diff_info["difficulty"].upper(), dc, fonts.tiny)
            y += 20
            xp_line = (
                f"XP: {diff_info['total_xp']:,} (adj: {diff_info['adjusted_xp']:,}, "
                f"x{diff_info['multiplier']:.1f}) | Per player: {diff_info['xp_per_player']:,}"
            )
            xt = fonts.tiny.render(xp_line, True, COLORS["text_main"])
            screen.blit(xt, (start_x, y))
            y += 16
            thresh = diff_info["thresholds"]
            tl = fonts.tiny.render(
                f"Thresholds — E:{thresh['easy']:,} M:{thresh['medium']:,} "
                f"H:{thresh['hard']:,} D:{thresh['deadly']:,}",
                True, COLORS["text_muted"])
            screen.blit(tl, (start_x, y))
            y += 22

            # Loot generator buttons
            loot_btn = pygame.Rect(start_x, y, 140, 26)
            loot_hover = loot_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["legendary_dim"] if loot_hover else COLORS["panel_light"],
                             loot_btn, border_radius=4)
            pygame.draw.rect(screen, COLORS["legendary"], loot_btn, 1, border_radius=4)
            lbt = fonts.small.render("Roll Loot", True, COLORS["legendary"])
            screen.blit(lbt, (loot_btn.x + 30, loot_btn.y + 4))
            if loot_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                self._roll_encounter_loot(enc)
                self._click_cooldown = 15

            rand_btn = pygame.Rect(start_x + 155, y, 180, 26)
            rand_hover = rand_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["spell_dim"] if rand_hover else COLORS["panel_light"],
                             rand_btn, border_radius=4)
            pygame.draw.rect(screen, COLORS["spell"], rand_btn, 1, border_radius=4)
            rbt = fonts.small.render("Random Encounter", True, COLORS["spell"])
            screen.blit(rbt, (rand_btn.x + 20, rand_btn.y + 4))
            if rand_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                self._roll_random_encounter(enc)
                self._click_cooldown = 15
            y += 35

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
            if self.world_map_mode:
                try:
                    self._draw_world_map(screen, mp)
                except Exception as e:
                    screen.set_clip(None)
                    # Fallback: show error instead of crashing
                    err_msg = fonts.body.render(f"Map error: {e}", True, COLORS["danger"])
                    screen.blit(err_msg, (30, 80))
                    hint = fonts.small.render("Press Map button again to retry, or switch to tree view.", True, COLORS["text_dim"])
                    screen.blit(hint, (30, 110))
            else:
                self._draw_world_locations(screen, mp)
        elif self.world_view == "npcs":
            self._draw_world_npcs(screen, mp)
        elif self.world_view == "shops":
            self._draw_world_shops(screen, mp)
        elif self.world_view == "shop_detail":
            self._draw_world_shop_detail(screen, mp)
        elif self.world_view == "templates":
            self._draw_templates_browser(screen, mp)
        elif self.world_view == "services":
            self._draw_services_viewer(screen, mp)
        elif self.world_view == "travel":
            self._draw_travel_viewer(screen, mp)
        elif self.world_view == "quests":
            self._draw_quests_viewer(screen, mp)

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
        panel_w = SCREEN_WIDTH - start_x - 30

        # Name (editable)
        hdr = fonts.header.render(npc.name, True, COLORS["accent"])
        screen.blit(hdr, (start_x, y))
        name_rect = pygame.Rect(start_x, y, hdr.get_width() + 50, 28)
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_name"
            self.input_text = npc.name
            self.modal = ("edit_field", "npc_name")

        # Alive/Active badges next to name
        badge_x = start_x + hdr.get_width() + 15
        if not npc.alive:
            dead_badge = fonts.tiny.render("DEAD", True, COLORS["danger"])
            pygame.draw.rect(screen, COLORS["danger"], (badge_x, y + 4, dead_badge.get_width() + 8, 18), border_radius=8)
            screen.blit(dead_badge, (badge_x + 4, y + 5))
        y += 32

        # Quick info fields (with age & gender added)
        fields = [
            ("Race", npc.race, "npc_race"),
            ("Gender", npc.gender, "npc_gender"),
            ("Age", npc.age, "npc_age"),
            ("Occupation", npc.occupation, "npc_occupation"),
            ("Appearance", npc.appearance, "npc_appearance"),
            ("Personality", npc.personality, "npc_personality"),
            ("Backstory", npc.backstory, "npc_backstory"),
        ]
        for label, value, field_key in fields:
            fl = fonts.small_bold.render(f"{label}:", True, COLORS["text_dim"])
            screen.blit(fl, (start_x, y))
            field_rect = pygame.Rect(start_x + 95, y - 2, panel_w - 95, 22)
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

        # Location with MOVE button
        loc = self.world.locations.get(npc.location_id)
        loc_label = fonts.small_bold.render("Location:", True, COLORS["text_dim"])
        screen.blit(loc_label, (start_x, y))
        loc_name = loc.name if loc else "(none)"
        lt = fonts.small.render(loc_name, True, COLORS["accent"] if loc else COLORS["text_muted"])
        screen.blit(lt, (start_x + 75, y))
        # Move button
        move_x = start_x + 75 + lt.get_width() + 10
        move_btn = pygame.Rect(move_x, y - 2, 60, 20)
        is_move_hover = move_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if is_move_hover else COLORS["panel"], move_btn, border_radius=3)
        pygame.draw.rect(screen, COLORS["border"], move_btn, 1, border_radius=3)
        mvt = fonts.tiny.render("Move", True, COLORS["accent"])
        screen.blit(mvt, (move_btn.x + 15, move_btn.y + 3))
        if is_move_hover and pygame.mouse.get_pressed()[0]:
            self._npc_location_picker_open = True
        # Unlink button (remove from location)
        if npc.location_id:
            unlink_btn = pygame.Rect(move_btn.right + 5, y - 2, 20, 20)
            is_unlink_hover = unlink_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["danger_hover"] if is_unlink_hover else COLORS["panel"],
                             unlink_btn, border_radius=3)
            xt = fonts.tiny.render("X", True, COLORS["danger"])
            screen.blit(xt, (unlink_btn.x + 5, unlink_btn.y + 3))
            if is_unlink_hover and pygame.mouse.get_pressed()[0]:
                move_npc(self.world, npc.id, "")
        y += 22

        # Stat source with preview
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
        # Clear stat link
        if npc.stat_source:
            clr_btn = pygame.Rect(m_btn.right + 5, y - 2, 50, 20)
            is_clr_hover = clr_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["danger_hover"] if is_clr_hover else COLORS["panel"],
                             clr_btn, border_radius=3)
            clrt = fonts.tiny.render("Clear", True, COLORS["danger"])
            screen.blit(clrt, (clr_btn.x + 8, clr_btn.y + 3))
            if is_clr_hover and pygame.mouse.get_pressed()[0]:
                npc.stat_source = ""
                npc.custom_stats = {}
        y += 22

        # Stat preview (show key stats if linked)
        if npc.stat_source:
            stats = self._get_npc_stats(npc)
            if stats:
                preview_items = [
                    f"HP:{stats.hp}",
                    f"AC:{stats.ac}",
                    f"CR:{stats.cr}",
                ]
                if hasattr(stats, 'abilities') and stats.abilities:
                    preview_items.append(
                        f"STR:{stats.abilities.strength} DEX:{stats.abilities.dexterity} "
                        f"CON:{stats.abilities.constitution}"
                    )
                prev_text = "  ".join(preview_items)
                pt = fonts.tiny.render(prev_text, True, COLORS["text_dim"])
                screen.blit(pt, (start_x + 50, y))
                y += 16
        y += 3

        # Gold & Inventory section
        gold_label = fonts.small_bold.render("Gold:", True, COLORS["text_dim"])
        screen.blit(gold_label, (start_x, y))
        gold_rect = pygame.Rect(start_x + 45, y - 2, 80, 22)
        pygame.draw.rect(screen, COLORS["input_bg"], gold_rect, border_radius=3)
        gt = fonts.small.render(f"{npc.gold:.0f} gp", True, COLORS["legendary"])
        screen.blit(gt, (gold_rect.x + 4, y))
        if gold_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_gold"
            self.input_text = str(int(npc.gold))
            self.modal = ("edit_field", "npc_gold")

        # Personal items (non-shop inventory)
        inv_label = fonts.small_bold.render("Items:", True, COLORS["text_dim"])
        screen.blit(inv_label, (start_x + 140, y))
        inv_text = ", ".join(npc.inventory_items[:5]) if npc.inventory_items else "(none)"
        if len(npc.inventory_items) > 5:
            inv_text += f" +{len(npc.inventory_items)-5} more"
        it = fonts.tiny.render(inv_text[:50], True,
                               COLORS["text_main"] if npc.inventory_items else COLORS["text_muted"])
        screen.blit(it, (start_x + 185, y + 2))
        # Add item button
        add_item_btn = pygame.Rect(start_x + 185 + it.get_width() + 5, y - 2, 20, 20)
        is_add_hover = add_item_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_add_hover else COLORS["panel"],
                         add_item_btn, border_radius=3)
        pt = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(pt, (add_item_btn.x + 5, add_item_btn.y + 3))
        if is_add_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_add_item"
            self.input_text = ""
            self.modal = ("edit_field", "npc_add_item")
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

        # ---- Relationships panel ----
        y += 5
        rel_label = fonts.small_bold.render("Relationships:", True, COLORS["text_dim"])
        screen.blit(rel_label, (start_x, y))
        # Add relationship button
        add_rel_btn = pygame.Rect(start_x + 110, y - 2, 20, 20)
        is_addrel_hover = add_rel_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_addrel_hover else COLORS["panel"],
                         add_rel_btn, border_radius=3)
        art = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(art, (add_rel_btn.x + 5, add_rel_btn.y + 3))
        if is_addrel_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_add_relationship"
            self.input_text = ""
            self.modal = ("edit_field", "npc_add_relationship")
        y += 20
        rel_att_cols = {"friendly": COLORS["success"], "neutral": COLORS["text_dim"],
                        "unfriendly": COLORS["warning"], "hostile": COLORS["danger"]}

        if npc.relationships:
            for ri, rel in enumerate(npc.relationships):
                # Hero name
                rn = fonts.tiny.render(f"{rel.hero_name}:", True, COLORS["text_main"])
                screen.blit(rn, (start_x + 10, y))
                # Attitude chips
                rx = start_x + 10 + rn.get_width() + 8
                for ratt in ["friendly", "neutral", "unfriendly", "hostile"]:
                    is_active = rel.attitude == ratt
                    raw = fonts.tiny.size(ratt[0].upper())[0] + 8
                    rar = pygame.Rect(rx, y, raw, 16)
                    rbg = rel_att_cols.get(ratt, COLORS["panel"]) if is_active else COLORS["panel"]
                    if rar.collidepoint(mp):
                        rbg = COLORS["hover"]
                        if pygame.mouse.get_pressed()[0]:
                            rel.attitude = ratt
                    pygame.draw.rect(screen, rbg, rar, border_radius=6)
                    rat = fonts.tiny.render(ratt[0].upper(), True,
                                            COLORS["text_bright"] if is_active else COLORS["text_muted"])
                    screen.blit(rat, (rx + 3, y + 1))
                    rx += raw + 2
                # Relationship notes (clickable)
                rx += 5
                rn_text = rel.notes[:30] if rel.notes else "(notes)"
                rnc = COLORS["text_dim"] if rel.notes else COLORS["text_muted"]
                rnt = fonts.tiny.render(rn_text, True, rnc)
                rn_rect = pygame.Rect(rx, y, rnt.get_width() + 10, 16)
                screen.blit(rnt, (rx, y + 1))
                if rn_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                    self.input_active = f"npc_rel_notes_{ri}"
                    self.input_text = rel.notes
                    self.modal = ("edit_field", f"npc_rel_notes_{ri}")
                # Delete relationship
                del_rx = rn_rect.right + 5
                del_rr = pygame.Rect(del_rx, y, 14, 16)
                if del_rr.collidepoint(mp):
                    drt = fonts.tiny.render("x", True, COLORS["danger"])
                    screen.blit(drt, (del_rx + 2, y + 1))
                    if pygame.mouse.get_pressed()[0]:
                        npc.relationships.pop(ri)
                        break
                # Click hero name to navigate to that NPC
                hero_npc = self._find_npc_by_name(rel.hero_name)
                if hero_npc:
                    link_rect = pygame.Rect(start_x + 10, y, rn.get_width(), 16)
                    if link_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                        self.selected_npc_id = hero_npc.id
                        return
                y += 18
        else:
            empty_t = fonts.tiny.render("(no relationships — click + to add)", True, COLORS["text_muted"])
            screen.blit(empty_t, (start_x + 10, y))
            y += 18

        # Notes
        y += 8
        notes_label = fonts.small_bold.render("DM Notes:", True, COLORS["text_dim"])
        screen.blit(notes_label, (start_x, y))
        y += 18
        note_rect = pygame.Rect(start_x, y, panel_w, 45)
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

        # Tags
        tag_y = note_rect.bottom + 8
        tag_label = fonts.small_bold.render("Tags:", True, COLORS["text_dim"])
        screen.blit(tag_label, (start_x, tag_y))
        tx = start_x + 45
        for ti, tag in enumerate(npc.tags):
            tw = fonts.tiny.size(tag)[0] + 16
            tr = pygame.Rect(tx, tag_y, tw, 18)
            is_tag_hover = tr.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["hover"] if is_tag_hover else COLORS["panel"],
                             tr, border_radius=8)
            tt = fonts.tiny.render(tag, True, COLORS["accent"])
            screen.blit(tt, (tx + 4, tag_y + 2))
            # X to remove tag
            if is_tag_hover and pygame.mouse.get_pressed()[0]:
                npc.tags.pop(ti)
                break
            tx += tw + 4
        # Add tag button
        add_tag_btn = pygame.Rect(tx, tag_y, 20, 18)
        is_at_hover = add_tag_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_at_hover else COLORS["panel"],
                         add_tag_btn, border_radius=8)
        att = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(att, (add_tag_btn.x + 5, tag_y + 2))
        if is_at_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "npc_add_tag"
            self.input_text = ""
            self.modal = ("edit_field", "npc_add_tag")

        # Delete NPC button
        del_y = tag_y + 28
        del_rect = pygame.Rect(start_x, del_y, 120, 28)
        is_del_hover = del_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if is_del_hover else COLORS["danger"],
                         del_rect, border_radius=4)
        dlt = fonts.small.render("Delete NPC", True, COLORS["text_bright"])
        screen.blit(dlt, (start_x + 10, del_y + 5))
        if is_del_hover and pygame.mouse.get_pressed()[0]:
            self._delete_world_npc(npc.id)

    def _get_npc_stats(self, npc):
        """Get CreatureStats for an NPC from stat_source."""
        if not npc.stat_source:
            return None
        if npc.stat_source.startswith("monster:"):
            monster_name = npc.stat_source[len("monster:"):]
            return library.get(monster_name)
        return None

    def _find_npc_by_name(self, name):
        """Find an NPC by name (for relationship navigation)."""
        for npc in self.world.npcs.values():
            if npc.name.lower() == name.lower():
                return npc
        return None

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
        """Draw monster selection overlay with CR categories and type subcategories."""
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

        # Close button
        close_rect = pygame.Rect(panel_x + 250, 60, 40, 25)
        if close_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["danger"], close_rect, border_radius=3)
        cx_text = fonts.small.render("X", True, COLORS["text_bright"])
        screen.blit(cx_text, (close_rect.x + 15, close_rect.y + 3))

        # Build CR -> type -> monsters structure
        all_monsters = library.get_all_monsters()
        clip_rect = pygame.Rect(panel_x, 125, 305, SCREEN_HEIGHT - 190)
        screen.set_clip(clip_rect)

        y = 125 + self.monster_picker_scroll

        if self.monster_search:
            # When searching, show flat filtered list
            for m in all_monsters:
                if self.monster_search.lower() not in m.name.lower():
                    continue
                if y > SCREEN_HEIGHT - 130:
                    y += 30
                    continue
                if y >= 115:
                    item_rect = pygame.Rect(panel_x + 10, y, 270, 26)
                    is_hover = item_rect.collidepoint(mp)
                    bg = COLORS["hover"] if is_hover else COLORS["panel"]
                    pygame.draw.rect(screen, bg, item_rect, border_radius=3)
                    cr_str = f"CR {m.challenge_rating:.3g}" if m.challenge_rating % 1 != 0 else f"CR {int(m.challenge_rating)}"
                    type_short = m.creature_type[:3].upper()
                    lt = fonts.small.render(f"{m.name} ({cr_str}) [{type_short}]", True, COLORS["text_bright"])
                    screen.blit(lt, (item_rect.x + 8, item_rect.y + 5))
                y += 30
        else:
            # Group by CR, then by creature type
            from collections import OrderedDict
            cr_groups = OrderedDict()
            for m in all_monsters:
                cr = m.challenge_rating
                if cr not in cr_groups:
                    cr_groups[cr] = {}
                ctype = m.creature_type or "Unknown"
                if ctype not in cr_groups[cr]:
                    cr_groups[cr][ctype] = []
                cr_groups[cr][ctype].append(m)

            for cr, type_groups in cr_groups.items():
                cr_str = f"CR {cr:.3g}" if cr % 1 != 0 else f"CR {int(cr)}"
                total = sum(len(v) for v in type_groups.values())
                is_cr_expanded = self.monster_picker_expanded_cr == cr

                # CR header row
                if y >= 115:
                    cr_rect = pygame.Rect(panel_x + 5, y, 280, 26)
                    is_hover = cr_rect.collidepoint(mp)
                    header_bg = COLORS["accent"] if is_cr_expanded else (COLORS["hover"] if is_hover else (35, 38, 48))
                    pygame.draw.rect(screen, header_bg, cr_rect, border_radius=4)
                    arrow = "v" if is_cr_expanded else ">"
                    cr_label = fonts.small_bold.render(f"{arrow} {cr_str}  ({total} creatures)", True,
                                                       (255, 255, 255) if is_cr_expanded else COLORS["text_bright"])
                    screen.blit(cr_label, (cr_rect.x + 8, cr_rect.y + 5))
                y += 30

                if is_cr_expanded:
                    # Show type subcategories
                    for ctype, monsters in sorted(type_groups.items()):
                        is_type_expanded = self.monster_picker_expanded_type == (cr, ctype)

                        if y >= 115:
                            type_rect = pygame.Rect(panel_x + 18, y, 260, 24)
                            is_hover = type_rect.collidepoint(mp)
                            type_bg = (50, 55, 70) if is_type_expanded else (COLORS["hover"] if is_hover else (28, 30, 40))
                            pygame.draw.rect(screen, type_bg, type_rect, border_radius=3)
                            arrow = "v" if is_type_expanded else ">"
                            type_label = fonts.small.render(f"  {arrow} {ctype} ({len(monsters)})", True,
                                                            COLORS["accent"] if is_type_expanded else COLORS["text_main"])
                            screen.blit(type_label, (type_rect.x + 4, type_rect.y + 4))
                        y += 28

                        if is_type_expanded:
                            for m in monsters:
                                if y >= 115:
                                    item_rect = pygame.Rect(panel_x + 30, y, 248, 24)
                                    is_hover = item_rect.collidepoint(mp)
                                    bg = COLORS["hover"] if is_hover else COLORS["panel"]
                                    pygame.draw.rect(screen, bg, item_rect, border_radius=3)
                                    lt = fonts.small.render(f"  {m.name}", True, COLORS["text_bright"])
                                    screen.blit(lt, (item_rect.x + 6, item_rect.y + 4))
                                y += 26

        screen.set_clip(None)

    # ---- NPC Location Picker ----

    def _draw_npc_location_picker(self, screen, mp):
        """Draw a location picker overlay for moving an NPC."""
        panel_x = SCREEN_WIDTH - 310
        panel_rect = pygame.Rect(panel_x, 55, 305, SCREEN_HEIGHT - 120)
        pygame.draw.rect(screen, COLORS["panel_dark"], panel_rect)
        pygame.draw.rect(screen, COLORS["border_light"], panel_rect, 2)

        ht = fonts.header.render("Move NPC to...", True, COLORS["accent"])
        screen.blit(ht, (panel_x + 10, 60))

        # Close button
        close_rect = pygame.Rect(panel_x + 250, 60, 40, 25)
        if close_rect.collidepoint(mp):
            pygame.draw.rect(screen, COLORS["danger"], close_rect, border_radius=3)
        cx = fonts.small.render("X", True, COLORS["text_bright"])
        screen.blit(cx, (close_rect.x + 15, close_rect.y + 3))
        if close_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self._npc_location_picker_open = False

        # Location list (flat, sorted by path)
        y = 95
        for loc_id, loc in sorted(self.world.locations.items(), key=lambda x: x[1].name):
            if y > SCREEN_HEIGHT - 130:
                break
            path = get_location_path(self.world, loc_id)
            path_str = " > ".join(path) if path else loc.name
            item_rect = pygame.Rect(panel_x + 10, y, 270, 28)
            is_hover = item_rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel"]
            pygame.draw.rect(screen, bg, item_rect, border_radius=3)
            icon = {"country": "C", "region": "R", "city": "Ci", "district": "D",
                    "building": "B", "room": "Rm", "wilderness": "W"}.get(loc.location_type, "?")
            it = fonts.tiny.render(f"[{icon}] {path_str}", True, COLORS["text_bright"])
            screen.blit(it, (item_rect.x + 5, item_rect.y + 6))
            if is_hover and pygame.mouse.get_pressed()[0]:
                npc = self.world.npcs.get(self.selected_npc_id)
                if npc:
                    move_npc(self.world, npc.id, loc_id)
                self._npc_location_picker_open = False
            y += 32

    def _handle_npc_location_picker_click(self, mp):
        """Handle clicks in NPC location picker (consumed by draw for simplicity)."""
        pass

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
            hints = fonts.small.render("Ctrl+Enter = Save  |  Escape = Save & Close", True, COLORS["text_dim"])
            screen.blit(hints, (x + 20, y + h - 30))

        elif self.modal[0] == "edit_field":
            # Generic single-line field editor
            field_key = self.modal[1] if len(self.modal) > 1 else ""
            # Pretty label from field key
            label_map = {
                "npc_name": "Name", "npc_race": "Race", "npc_gender": "Gender",
                "npc_age": "Age", "npc_occupation": "Occupation",
                "npc_appearance": "Appearance", "npc_personality": "Personality",
                "npc_backstory": "Backstory", "npc_notes": "DM Notes",
                "npc_gold": "Gold", "npc_add_item": "Add Item",
                "npc_add_tag": "Add Tag", "npc_add_relationship": "Add Relationship",
                "location_name": "Location Name", "location_desc": "Description",
                "location_notes": "Notes", "location_color": "Map Color",
                "location_map_note": "Map Note", "location_map_icon": "Map Icon",
                "location_population": "Population",
                "shop_name": "Shop Name", "map_image_path": "Map Image Path",
                "pin_name": "Pin Name", "pin_description": "Pin Description",
                "pin_notes": "Pin Notes", "pin_add_link": "Add Link",
                "hero_add_relationship": "Add Relationship",
                "hero_add_link": "Add Link",
                "campaign_name": "Campaign Name", "encounter_name": "Encounter Name",
                "area_name": "Area Name", "member_note": "DM Note",
            }
            # Handle relationship/quest sub-fields
            title = "Edit"
            if field_key in label_map:
                title = f"Edit {label_map[field_key]}"
            elif field_key.startswith("npc_rel_notes_"):
                title = "Edit Relationship Notes"
            elif field_key.startswith("hero_rel_desc_"):
                title = "Edit Relationship Description"
            elif field_key.startswith("quest_"):
                title = f"Edit {field_key.replace('quest_', '').replace('_', ' ').title()}"

            tt = fonts.header.render(title, True, COLORS["accent"])
            screen.blit(tt, (x + 20, y + 15))

            # Determine if this is a multiline field
            multiline_fields = {"npc_backstory", "npc_notes", "npc_personality",
                                "location_desc", "location_notes", "pin_description",
                                "pin_notes", "quest_description", "quest_notes",
                                "quest_reward_notes", "member_note"}
            is_multiline = field_key in multiline_fields or field_key.startswith("npc_rel_notes_") or field_key.startswith("hero_rel_desc_")

            if is_multiline:
                area = pygame.Rect(x + 20, y + 55, w - 40, h - 120)
                pygame.draw.rect(screen, COLORS["input_bg"], area, border_radius=4)
                pygame.draw.rect(screen, COLORS["input_focus"], area, 1, border_radius=4)

                text_y = area.y + 5
                for line in self.input_text.split("\n"):
                    lt = fonts.body.render(line, True, COLORS["text_bright"])
                    screen.blit(lt, (area.x + 5, text_y))
                    text_y += 22

                if pygame.time.get_ticks() % 1000 < 500:
                    lines = self.input_text.split("\n")
                    last_line = lines[-1] if lines else ""
                    cursor_x = area.x + 5 + fonts.body.size(last_line)[0]
                    cursor_y = area.y + 5 + (len(lines) - 1) * 22
                    pygame.draw.line(screen, COLORS["accent"], (cursor_x, cursor_y), (cursor_x, cursor_y + 18), 2)
            else:
                # Single-line input
                area = pygame.Rect(x + 20, y + 70, w - 40, 36)
                pygame.draw.rect(screen, COLORS["input_bg"], area, border_radius=4)
                pygame.draw.rect(screen, COLORS["input_focus"], area, 1, border_radius=4)

                lt = fonts.body.render(self.input_text, True, COLORS["text_bright"])
                screen.blit(lt, (area.x + 8, area.y + 7))

                if pygame.time.get_ticks() % 1000 < 500:
                    cursor_x = area.x + 8 + fonts.body.size(self.input_text)[0]
                    pygame.draw.line(screen, COLORS["accent"], (cursor_x, area.y + 6), (cursor_x, area.y + 28), 2)

            if is_multiline:
                hints = fonts.small.render("Ctrl+Enter = Save  |  Escape = Save & Close", True, COLORS["text_dim"])
            else:
                hints = fonts.small.render("Enter = Save  |  Escape = Cancel", True, COLORS["text_dim"])
            screen.blit(hints, (x + 20, y + h - 30))

    # ================================================================
    # WORLD MAP VIEW
    # ================================================================

    _MAP_TYPE_COLORS = {
        "country": (255, 200, 30), "region": (170, 90, 245),
        "city": (88, 130, 230), "town": (88, 130, 230),
        "village": (35, 160, 65), "building": (240, 180, 20),
        "tavern": (255, 100, 30), "shop": (255, 200, 30),
        "temple": (255, 240, 180), "dungeon": (210, 50, 60),
        "castle": (180, 140, 100), "port": (100, 180, 255),
        "wilderness": (35, 160, 65), "cave": (140, 142, 155),
        "camp": (200, 160, 60), "ruins": (160, 120, 80),
    }
    _MAP_TYPE_SIZES = {
        "country": 18, "region": 14, "city": 12, "town": 10,
        "village": 8, "building": 6, "tavern": 7, "shop": 6,
        "temple": 7, "dungeon": 8, "castle": 11, "port": 9,
        "camp": 6, "ruins": 7, "wilderness": 6, "cave": 6,
    }
    _MAP_ROUTE_COLORS = {
        "road": (180, 160, 120), "trail": (120, 110, 80),
        "river": (60, 120, 200), "sea": (40, 80, 160),
        "air": (160, 140, 220), "secret": (200, 50, 50),
    }
    _MAP_ROUTE_STYLES = {
        "road": 3, "trail": 1, "river": 2, "sea": 2, "air": 1, "secret": 1,
    }

    def _hex_to_rgb(self, hex_str):
        """Convert '#RRGGBB' or 'RRGGBB' to (r,g,b) tuple."""
        h = hex_str.lstrip('#')
        if len(h) != 6:
            return None
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return None

    def _get_map_grid_area(self):
        """Get the main map drawing region."""
        map_area = pygame.Rect(20, 65, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 135)
        return pygame.Rect(map_area.x + 10, map_area.y + 55,
                           map_area.width - 20, map_area.height - 65)

    def _map_to_screen(self, pct_x, pct_y, grid_area):
        """Convert percent-based map position to screen pixels with zoom/pan."""
        cx = grid_area.x + grid_area.width / 2 + self.map_offset_x
        cy = grid_area.y + grid_area.height / 2 + self.map_offset_y
        sx = cx + (pct_x - 50) * grid_area.width / 100 * self.map_zoom
        sy = cy + (pct_y - 50) * grid_area.height / 100 * self.map_zoom
        return int(sx), int(sy)

    def _screen_to_map(self, sx, sy, grid_area):
        """Convert screen pixels to percent-based map position."""
        cx = grid_area.x + grid_area.width / 2 + self.map_offset_x
        cy = grid_area.y + grid_area.height / 2 + self.map_offset_y
        zoom = max(0.01, self.map_zoom)
        denom_x = grid_area.width / 100 * zoom
        denom_y = grid_area.height / 100 * zoom
        pct_x = 50 + (sx - cx) / denom_x if denom_x != 0 else 50
        pct_y = 50 + (sy - cy) / denom_y if denom_y != 0 else 50
        return pct_x, pct_y

    def _get_loc_color(self, loc):
        """Get display color for a location (custom or type-based)."""
        if loc.map_color:
            c = self._hex_to_rgb(loc.map_color)
            if c:
                return c
        return self._MAP_TYPE_COLORS.get(loc.location_type, COLORS["text_dim"])

    def _get_loc_size(self, loc):
        """Get display size for a location (custom or type-based)."""
        if loc.map_size > 0:
            return loc.map_size
        return self._MAP_TYPE_SIZES.get(loc.location_type, 6)

    def _draw_world_map(self, screen, mp):
        """Draw an interactive world map with zoom, pan, routes, tooltips."""
        map_area = pygame.Rect(20, 65, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 135)
        grid_area = self._get_map_grid_area()

        # Background image or default
        if self._map_bg_surface and self.world.map_image_path:
            # Fit image into grid preserving aspect ratio, then apply zoom
            src_w, src_h = self._map_bg_surface.get_size()
            if src_w > 0 and src_h > 0 and grid_area.width > 0 and grid_area.height > 0:
                fit_scale = min(grid_area.width / src_w, grid_area.height / src_h)
                base_w = max(1, int(src_w * fit_scale))
                base_h = max(1, int(src_h * fit_scale))
                iw = max(1, int(base_w * self.map_zoom))
                ih = max(1, int(base_h * self.map_zoom))
                cache_key = (iw, ih)
                if self._map_bg_cache_key != cache_key or self._map_bg_scaled_cache is None:
                    # Only re-scale when zoom/size actually changes
                    self._map_bg_scaled_cache = pygame.transform.smoothscale(self._map_bg_surface, (iw, ih))
                    self._map_bg_cache_key = cache_key
                bx = grid_area.x + grid_area.width // 2 + self.map_offset_x - iw // 2
                by = grid_area.y + grid_area.height // 2 + self.map_offset_y - ih // 2
                screen.set_clip(grid_area)
                screen.blit(self._map_bg_scaled_cache, (bx, by))
                screen.set_clip(None)
        else:
            pygame.draw.rect(screen, (16, 18, 26), grid_area, border_radius=4)

        # Grid lines (subtle)
        screen.set_clip(grid_area)
        grid_spacing = max(30, int(60 * self.map_zoom))
        ox = int(self.map_offset_x) % grid_spacing
        oy = int(self.map_offset_y) % grid_spacing
        for gx in range(-grid_spacing, grid_area.width + grid_spacing, grid_spacing):
            x = grid_area.x + gx + ox
            if grid_area.x <= x <= grid_area.right:
                pygame.draw.line(screen, (24, 26, 36), (x, grid_area.y), (x, grid_area.bottom), 1)
        for gy in range(-grid_spacing, grid_area.height + grid_spacing, grid_spacing):
            y = grid_area.y + gy + oy
            if grid_area.y <= y <= grid_area.bottom:
                pygame.draw.line(screen, (24, 26, 36), (grid_area.x, y), (grid_area.right, y), 1)

        # --- Draw routes ---
        for route in self.world.map_routes:
            if route.from_id in self._location_map_positions and route.to_id in self._location_map_positions:
                fp = self._location_map_positions[route.from_id]
                tp = self._location_map_positions[route.to_id]
                start = self._map_to_screen(fp[0], fp[1], grid_area)
                end = self._map_to_screen(tp[0], tp[1], grid_area)
                # Route color
                if route.color:
                    rc = self._hex_to_rgb(route.color) or self._MAP_ROUTE_COLORS.get(route.route_type, (120, 120, 120))
                else:
                    rc = self._MAP_ROUTE_COLORS.get(route.route_type, (120, 120, 120))
                thickness = self._MAP_ROUTE_STYLES.get(route.route_type, 2)
                # Dashed for trail/secret
                if route.route_type in ("trail", "secret", "air"):
                    self._draw_dashed_line(screen, rc, start, end, thickness, 8, 5)
                else:
                    pygame.draw.line(screen, rc, start, end, thickness)
                # Route label (show distance + label)
                route_text_parts = []
                if route.label:
                    route_text_parts.append(route.label)
                if route.distance_miles > 0 and self.map_zoom >= 0.5:
                    route_text_parts.append(f"{route.distance_miles:.0f} mi")
                elif route.distance_miles == 0 and self.world.map_scale_miles > 0 and self.map_zoom >= 0.5:
                    # Auto-estimate from map scale
                    est = estimate_route_miles_from_scale(self.world, route.from_id, route.to_id)
                    if est > 0:
                        route_text_parts.append(f"~{est:.0f} mi")
                if route_text_parts and self.map_zoom >= 0.35:
                    mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
                    route_label_str = " | ".join(route_text_parts)
                    rl = fonts.tiny.render(route_label_str, True, COLORS["text_main"])
                    bg = pygame.Surface((rl.get_width() + 6, rl.get_height() + 2), pygame.SRCALPHA)
                    bg.fill((0, 0, 0, 140))
                    screen.blit(bg, (mid[0] - rl.get_width() // 2 - 3, mid[1] - rl.get_height() // 2 - 1))
                    screen.blit(rl, (mid[0] - rl.get_width() // 2, mid[1] - rl.get_height() // 2))

                    # Route hover: show travel time details
                    mid_rect = pygame.Rect(mid[0] - 30, mid[1] - 10, 60, 20)
                    if mid_rect.collidepoint(mp) and not pygame.mouse.get_pressed()[0]:
                        dist = route.distance_miles
                        if dist <= 0:
                            dist = estimate_route_miles_from_scale(self.world, route.from_id, route.to_id)
                        if dist > 0:
                            from data.travel import calculate_travel_time, format_travel_time, TRAVEL_PACE
                            tip_lines = [f"Distance: {dist:.1f} miles"]
                            for pace_key in ("fast", "normal", "slow"):
                                info = calculate_travel_time(dist, pace=pace_key, terrain=route.terrain_type)
                                tip_lines.append(f"{pace_key.title()}: {format_travel_time(info['total_days'])}")
                            tip_lines.append(f"Terrain: {route.terrain_type}")
                            if route.danger_level != "safe":
                                tip_lines.append(f"Danger: {route.danger_level}")
                            tw = max(fonts.small.size(l)[0] for l in tip_lines) + 16
                            th = len(tip_lines) * 18 + 8
                            tx = min(mp[0] + 12, SCREEN_WIDTH - tw - 10)
                            ty = mp[1] - th - 5
                            tip_rect = pygame.Rect(tx, ty, tw, th)
                            pygame.draw.rect(screen, (20, 22, 30), tip_rect, border_radius=4)
                            pygame.draw.rect(screen, COLORS["border"], tip_rect, 1, border_radius=4)
                            for i, line in enumerate(tip_lines):
                                col = COLORS["accent"] if i == 0 else COLORS["text_main"]
                                lt = fonts.small.render(line, True, col)
                                screen.blit(lt, (tx + 8, ty + 4 + i * 18))

        # --- Draw parent-child connections (thin lines) ---
        for loc_id, loc in self.world.locations.items():
            if loc.parent_id and loc.parent_id in self._location_map_positions and loc_id in self._location_map_positions:
                # Skip if there's already a route between them
                has_route = any(
                    (r.from_id == loc.parent_id and r.to_id == loc_id) or
                    (r.from_id == loc_id and r.to_id == loc.parent_id)
                    for r in self.world.map_routes
                )
                if not has_route:
                    fp = self._location_map_positions[loc.parent_id]
                    cp = self._location_map_positions[loc_id]
                    start = self._map_to_screen(fp[0], fp[1], grid_area)
                    end = self._map_to_screen(cp[0], cp[1], grid_area)
                    pygame.draw.line(screen, (40, 44, 56), start, end, 1)

        # Auto-layout unplaced locations
        roots = get_root_locations(self.world)
        self._auto_layout_locations(roots, grid_area)

        # --- Draw location nodes ---
        hovered_loc_id = ""
        for loc_id, loc in self.world.locations.items():
            pos = self._location_map_positions.get(loc_id)
            if not pos:
                continue
            px, py = self._map_to_screen(pos[0], pos[1], grid_area)
            # Cull off-screen
            if px < grid_area.x - 30 or px > grid_area.right + 30:
                continue
            if py < grid_area.y - 30 or py > grid_area.bottom + 30:
                continue

            color = self._get_loc_color(loc)
            size = max(3, int(self._get_loc_size(loc) * self.map_zoom))
            is_sel = loc_id == self.selected_location_id
            hit_dist = size + 5
            is_hover = abs(mp[0] - px) < hit_dist and abs(mp[1] - py) < hit_dist

            if is_hover:
                hovered_loc_id = loc_id

            # Glow
            if is_sel or is_hover:
                glow_r = size + 6
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 50), (glow_r, glow_r), glow_r)
                screen.blit(glow_surf, (px - glow_r, py - glow_r))

            # Node shape: circle for most, diamond for dungeon, square for building/castle
            if loc.location_type in ("dungeon", "cave", "ruins"):
                # Diamond
                pts = [(px, py - size), (px + size, py), (px, py + size), (px - size, py)]
                pygame.draw.polygon(screen, color, pts)
                if is_sel:
                    pygame.draw.polygon(screen, COLORS["text_bright"], pts, 2)
            elif loc.location_type in ("castle", "building", "shop", "temple"):
                # Rounded square
                r = pygame.Rect(px - size, py - size, size * 2, size * 2)
                pygame.draw.rect(screen, color, r, border_radius=3)
                if is_sel:
                    pygame.draw.rect(screen, COLORS["text_bright"], r, 2, border_radius=3)
            else:
                # Circle
                pygame.draw.circle(screen, color, (px, py), size)
                if is_sel:
                    pygame.draw.circle(screen, COLORS["text_bright"], (px, py), size + 2, 2)

            # Custom icon or type abbreviation
            icon = loc.map_icon or loc.location_type[:2].upper()
            if size >= 6:
                icon_font = fonts.tiny if size < 10 else fonts.small
                it = icon_font.render(icon, True, (0, 0, 0))
                screen.blit(it, (px - it.get_width() // 2, py - it.get_height() // 2))

            # Name label below (zoom-aware: hide at very low zoom, shrink at medium)
            show_label = self.map_zoom >= 0.4 or is_sel or is_hover
            if show_label:
                if self.map_zoom < 0.6 and not is_sel and not is_hover:
                    label_font = fonts.tiny
                    label_alpha = max(60, int(255 * (self.map_zoom - 0.3) / 0.3))
                else:
                    label_font = fonts.small if is_sel else fonts.tiny
                    label_alpha = 255
                label = label_font.render(loc.name, True, COLORS["text_bright"] if is_sel else COLORS["text_main"])
                lx = px - label.get_width() // 2
                ly = py + size + 3
                lbg = pygame.Surface((label.get_width() + 4, label.get_height()), pygame.SRCALPHA)
                lbg.fill((0, 0, 0, min(120, label_alpha)))
                screen.blit(lbg, (lx - 2, ly))
                if label_alpha < 255:
                    label.set_alpha(label_alpha)
                screen.blit(label, (lx, ly))

            # NPC count badge
            npc_count = len([n for n in self.world.npcs.values() if n.location_id == loc_id and n.active])
            if npc_count > 0:
                badge_text = str(npc_count)
                bt = fonts.tiny.render(badge_text, True, COLORS["text_bright"])
                bw = bt.get_width() + 6
                bh = bt.get_height() + 2
                br = pygame.Rect(px + size - 2, py - size - 2, bw, bh)
                pygame.draw.rect(screen, COLORS["player"], br, border_radius=bh // 2)
                screen.blit(bt, (br.x + 3, br.y + 1))

        # --- Draw map pins ---
        hovered_pin_id = ""
        for pin in self.world.map_pins:
            if not pin.visible:
                continue
            px, py = self._map_to_screen(pin.map_x, pin.map_y, grid_area)
            if px < grid_area.x - 20 or px > grid_area.right + 20:
                continue
            if py < grid_area.y - 20 or py > grid_area.bottom + 20:
                continue

            pin_info = MAP_PIN_TYPES.get(pin.pin_type, MAP_PIN_TYPES["custom"])
            color_hex = pin.color or pin_info["color"]
            color = self._hex_to_rgb(color_hex) or (180, 180, 180)
            icon = pin.icon or pin_info["icon"]
            pin_size = max(4, int(7 * self.map_zoom))
            is_sel = pin.id == self.selected_pin_id
            hit_dist = pin_size + 5
            is_hover = abs(mp[0] - px) < hit_dist and abs(mp[1] - py) < hit_dist

            if is_hover:
                hovered_pin_id = pin.id

            # Draw pin marker (inverted triangle / diamond)
            pts = [(px, py + pin_size), (px - pin_size, py - pin_size // 2),
                   (px + pin_size, py - pin_size // 2)]
            pygame.draw.polygon(screen, color, pts)
            if is_sel or is_hover:
                pygame.draw.polygon(screen, COLORS["text_bright"], pts, 2)

            # Icon inside
            if pin_size >= 5:
                it = fonts.tiny.render(icon, True, (0, 0, 0))
                screen.blit(it, (px - it.get_width() // 2, py - pin_size // 2 - 1))

            # Name label below
            label = fonts.tiny.render(pin.name, True, COLORS["text_main"])
            lx = px - label.get_width() // 2
            ly = py + pin_size + 2
            lbg = pygame.Surface((label.get_width() + 4, label.get_height()), pygame.SRCALPHA)
            lbg.fill((0, 0, 0, 120))
            screen.blit(lbg, (lx - 2, ly))
            screen.blit(label, (lx, ly))

        # --- Draw map tokens (party, NPC groups, encounter markers) ---
        for token in self.world.map_tokens:
            if not token.visible:
                continue
            tx, ty = self._map_to_screen(token.map_x, token.map_y, grid_area)
            if tx < grid_area.x - 20 or tx > grid_area.right + 20:
                continue
            if ty < grid_area.y - 20 or ty > grid_area.bottom + 20:
                continue

            tok_info = MAP_TOKEN_TYPES.get(token.token_type, MAP_TOKEN_TYPES["custom"])
            color_hex = token.color or tok_info["color"]
            color = self._hex_to_rgb(color_hex) or (180, 180, 180)
            icon = token.icon or tok_info["icon"]
            tok_size = max(6, int(10 * self.map_zoom))
            is_sel = token.id == self.selected_token_id
            hit_dist = tok_size + 5
            is_hover = abs(mp[0] - tx) < hit_dist and abs(mp[1] - ty) < hit_dist

            # Draw token (distinctive rounded square with border)
            tok_rect = pygame.Rect(tx - tok_size, ty - tok_size, tok_size * 2, tok_size * 2)
            pygame.draw.rect(screen, color, tok_rect, border_radius=tok_size // 2)
            pygame.draw.rect(screen, (255, 255, 255) if is_sel else (0, 0, 0),
                             tok_rect, 2, border_radius=tok_size // 2)

            # Icon
            if tok_size >= 6:
                it = fonts.tiny.render(icon, True, (0, 0, 0))
                screen.blit(it, (tx - it.get_width() // 2, ty - it.get_height() // 2))

            # Name
            if self.map_zoom >= 0.5 or is_sel or is_hover:
                nl = fonts.tiny.render(token.name, True, COLORS["text_bright"])
                nlx = tx - nl.get_width() // 2
                nly = ty + tok_size + 2
                nbg = pygame.Surface((nl.get_width() + 4, nl.get_height()), pygame.SRCALPHA)
                nbg.fill((0, 0, 0, 120))
                screen.blit(nbg, (nlx - 2, nly))
                screen.blit(nl, (nlx, nly))

            # Token hover tooltip
            if is_hover and not pygame.mouse.get_pressed()[0]:
                tip = [f"{token.name} ({tok_info['label']})"]
                if token.notes:
                    tip.append(token.notes[:50])
                if token.npc_ids:
                    tip.append(f"NPCs: {len(token.npc_ids)}")
                tw = max(fonts.small.size(l)[0] for l in tip) + 16
                th = len(tip) * 18 + 8
                ttx = min(mp[0] + 12, SCREEN_WIDTH - tw - 10)
                tty = mp[1] - th - 5
                tip_rect = pygame.Rect(ttx, tty, tw, th)
                pygame.draw.rect(screen, (20, 22, 30), tip_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["border"], tip_rect, 1, border_radius=4)
                for i, line in enumerate(tip):
                    col = COLORS["accent"] if i == 0 else COLORS["text_main"]
                    lt = fonts.small.render(line, True, col)
                    screen.blit(lt, (ttx + 8, tty + 4 + i * 18))

        screen.set_clip(None)  # End map clip

        # --- Pin hover tooltip ---
        if hovered_pin_id and not pygame.mouse.get_pressed()[0]:
            pin = get_pin_by_id(self.world, hovered_pin_id)
            if pin:
                tip_lines = [pin.name]
                if pin.description:
                    tip_lines.append(pin.description[:60])
                if pin.links:
                    tip_lines.append(f"Links: {len(pin.links)}")
                tw = max(fonts.small.size(l)[0] for l in tip_lines) + 16
                th = len(tip_lines) * 18 + 8
                tx = min(mp[0] + 12, SCREEN_WIDTH - tw - 10)
                ty = mp[1] - th - 5
                tip_rect = pygame.Rect(tx, ty, tw, th)
                pygame.draw.rect(screen, (20, 22, 30), tip_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["border"], tip_rect, 1, border_radius=4)
                for i, line in enumerate(tip_lines):
                    col = COLORS["accent"] if i == 0 else COLORS["text_main"]
                    lt = fonts.small.render(line, True, col)
                    screen.blit(lt, (tx + 8, ty + 4 + i * 18))

        # --- Outer frame ---
        pygame.draw.rect(screen, COLORS["border"], map_area, 1, border_radius=8)

        # --- Toolbar at top ---
        tb_y = map_area.y + 5
        title = fonts.body_bold.render(f"World Map: {self.world.name}", True, COLORS["accent"])
        screen.blit(title, (map_area.x + 12, tb_y))

        # Zoom display
        zoom_text = fonts.small.render(f"Zoom: {self.map_zoom:.1f}x", True, COLORS["text_dim"])
        screen.blit(zoom_text, (map_area.x + 12, tb_y + 22))

        # Map mode toolbar buttons (drawn inline)
        tool_x = map_area.x + 200
        tool_btns = [
            ("+ Route", "add_route"), ("+ Pin", "add_pin"), ("+ Token", "add_token"),
            ("Image", "set_image"), ("Scale", "set_scale_value"),
            ("Cal", "set_scale"), ("Reset", "reset_view"), ("Sub-Map", "loc_sub_map"),
        ]
        for btn_label, btn_action in tool_btns:
            bw = fonts.small.size(btn_label)[0] + 14
            btn_rect = pygame.Rect(tool_x, tb_y + 2, bw, 22)
            bh = btn_rect.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["hover"] if bh else COLORS["panel"], btn_rect, border_radius=3)
            pygame.draw.rect(screen, COLORS["border"], btn_rect, 1, border_radius=3)
            bt = fonts.small.render(btn_label, True, COLORS["text_bright"] if bh else COLORS["text_dim"])
            screen.blit(bt, (tool_x + 7, tb_y + 5))
            if bh and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                self._map_tool_action(btn_action)
                self._click_cooldown = 15
            tool_x += bw + 5

        # Mode indicators
        mode_y = tb_y + 40
        if self._map_route_mode:
            rm = fonts.small_bold.render("ROUTE MODE: Click two locations to connect", True, COLORS["warning"])
            screen.blit(rm, (map_area.x + 12, mode_y))
        elif self._map_token_mode:
            tok_type_label = MAP_TOKEN_TYPES.get(self._map_token_type, {}).get("label", "Custom")
            rm = fonts.small_bold.render(f"TOKEN MODE: Click to place {tok_type_label} (scroll to change type)", True, COLORS["warning"])
            screen.blit(rm, (map_area.x + 12, mode_y))
        elif self._map_scale_mode:
            if self._map_scale_point1:
                rm = fonts.small_bold.render("SCALE: Click second point to set distance", True, COLORS["warning"])
            else:
                rm = fonts.small_bold.render("SCALE: Click first point on map", True, COLORS["warning"])
            screen.blit(rm, (map_area.x + 12, mode_y))
        elif self._map_pin_mode:
            rm = fonts.small_bold.render("PIN MODE: Click to place pin", True, COLORS["warning"])
            screen.blit(rm, (map_area.x + 12, mode_y))

        # Scale indicator
        if self.world.map_scale_miles > 0:
            scale_text = f"Map scale: {self.world.map_scale_miles:.0f} miles across"
            st = fonts.tiny.render(scale_text, True, COLORS["text_dim"])
            screen.blit(st, (map_area.right - st.get_width() - 10, tb_y + 2))

        # --- Hover tooltip ---
        if hovered_loc_id and not pygame.mouse.get_pressed()[0]:
            self._draw_map_hover_tooltip(screen, mp, hovered_loc_id)

        # --- Info panel for selected location ---
        if self.selected_location_id:
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                self._draw_map_info_panel(screen, mp, loc)

        # --- Info panel for selected pin ---
        if self.selected_pin_id and not self.selected_location_id:
            pin = get_pin_by_id(self.world, self.selected_pin_id)
            if pin:
                self._draw_pin_info_panel(screen, mp, pin)

        # --- Pin mode indicator ---
        if self._map_pin_mode:
            pm_text = fonts.small_bold.render("PIN MODE: Click to place a new pin", True, COLORS["warning"])
            screen.blit(pm_text, (map_area.x + 12, tb_y + 40))

        # --- Location detail popup (opened by double-clicking a location) ---
        if self._map_detail_location_id:
            self._draw_location_detail_popup(screen, mp)

    def _draw_location_detail_popup(self, screen, mp):
        """Full-screen popup showing NPCs, children, quests for a location."""
        loc = self.world.locations.get(self._map_detail_location_id)
        if not loc:
            self._map_detail_location_id = ""
            return

        # Dimmed backdrop
        backdrop = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 160))
        screen.blit(backdrop, (0, 0))

        pw, ph = 640, 520
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        popup = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(screen, (20, 22, 32), popup, border_radius=8)
        pygame.draw.rect(screen, COLORS["accent"], popup, 2, border_radius=8)

        # Title
        title = fonts.title.render(loc.name, True, COLORS["accent"])
        screen.blit(title, (px + 16, py + 12))
        subtitle = fonts.small.render(
            f"{loc.location_type}  •  Pop: {loc.population}" if loc.population else loc.location_type,
            True, COLORS["text_dim"],
        )
        screen.blit(subtitle, (px + 16, py + 44))

        # Close button (top right)
        close_rect = pygame.Rect(px + pw - 32, py + 10, 22, 22)
        close_hover = close_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger"] if close_hover else COLORS["panel"],
                         close_rect, border_radius=3)
        ct = fonts.small_bold.render("X", True, COLORS["text_bright"])
        screen.blit(ct, (close_rect.x + 7, close_rect.y + 2))
        if close_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
            self._map_detail_location_id = ""
            self._click_cooldown = 15
            return

        # Sub-map button
        submap_rect = pygame.Rect(px + pw - 140, py + 10, 100, 22)
        sh = submap_rect.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if sh else COLORS["panel"],
                         submap_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["border"], submap_rect, 1, border_radius=3)
        sbt = fonts.small.render("Set Sub-Map", True, COLORS["text_bright"])
        screen.blit(sbt, (submap_rect.x + 8, submap_rect.y + 4))
        if sh and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
            self.selected_location_id = loc.id
            self.modal = ("edit_field", "loc_map_image")
            self.input_active = "loc_map_image"
            self.input_text = loc.map_image_path
            self._click_cooldown = 15

        # Description
        y = py + 76
        if loc.description:
            desc_lbl = fonts.small_bold.render("Description", True, COLORS["text_dim"])
            screen.blit(desc_lbl, (px + 16, y))
            y += 20
            # Simple wrap
            words = loc.description.split()
            line = ""
            max_w = pw - 32
            for w in words:
                test = line + " " + w if line else w
                if fonts.small.size(test)[0] > max_w:
                    screen.blit(fonts.small.render(line, True, COLORS["text_main"]), (px + 16, y))
                    y += 18
                    line = w
                    if y > py + 180:
                        break
                else:
                    line = test
            if line:
                screen.blit(fonts.small.render(line, True, COLORS["text_main"]), (px + 16, y))
                y += 18
            y += 6

        # Two columns: NPCs here + Sub-locations
        col_y = max(y, py + 200)
        col1_x = px + 16
        col2_x = px + pw // 2 + 8

        # NPCs at this location
        npcs = get_npcs_at_location(self.world, loc.id)
        lbl = fonts.small_bold.render(f"NPCs ({len(npcs)})", True, COLORS["accent"])
        screen.blit(lbl, (col1_x, col_y))
        ny = col_y + 22
        max_list_h = py + ph - ny - 20
        line_h = 22
        max_rows = max(1, max_list_h // line_h)
        for npc in npcs[:max_rows]:
            row = pygame.Rect(col1_x, ny, pw // 2 - 24, 20)
            rh = row.collidepoint(mp)
            if rh:
                pygame.draw.rect(screen, COLORS["hover"], row, border_radius=3)
            nt = fonts.small.render(f"• {npc.name}", True, COLORS["text_main"])
            screen.blit(nt, (col1_x + 4, ny + 2))
            if rh and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                self.selected_npc_id = npc.id
                self.world_view = "npcs"
                self.world_map_mode = False
                self._map_detail_location_id = ""
                self._click_cooldown = 15
                return
            ny += line_h

        # Sub-locations
        children = get_children(self.world, loc.id)
        lbl2 = fonts.small_bold.render(f"Sub-locations ({len(children)})", True, COLORS["accent"])
        screen.blit(lbl2, (col2_x, col_y))
        cy = col_y + 22
        for child in children[:max_rows]:
            row = pygame.Rect(col2_x, cy, pw // 2 - 24, 20)
            rh = row.collidepoint(mp)
            if rh:
                pygame.draw.rect(screen, COLORS["hover"], row, border_radius=3)
            ct = fonts.small.render(f"• {child.name}", True, COLORS["text_main"])
            screen.blit(ct, (col2_x + 4, cy + 2))
            if rh and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                self.selected_location_id = child.id
                self._map_detail_location_id = child.id
                self._click_cooldown = 15
            cy += line_h

        # Hint
        hint = fonts.tiny.render("Press ESC to close", True, COLORS["text_muted"])
        screen.blit(hint, (px + 16, py + ph - 18))

    def _draw_pin_info_panel(self, screen, mp, pin):
        """Draw an info/edit panel for a selected map pin."""
        pw = 280
        ph = 300
        ix = SCREEN_WIDTH - pw - 40
        iy_start = 130
        info_rect = pygame.Rect(ix - 10, iy_start - 10, pw + 20, ph)
        pygame.draw.rect(screen, (18, 20, 30, 230), info_rect, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], info_rect, 1, border_radius=6)

        iy = iy_start
        pin_info = MAP_PIN_TYPES.get(pin.pin_type, MAP_PIN_TYPES["custom"])
        color_hex = pin.color or pin_info["color"]
        color = self._hex_to_rgb(color_hex) or (180, 180, 180)

        # Pin icon and name
        icon = pin.icon or pin_info["icon"]
        icon_t = fonts.body_bold.render(icon, True, color)
        screen.blit(icon_t, (ix, iy))
        # Name (editable)
        name_t = fonts.body_bold.render(pin.name, True, COLORS["accent"])
        name_rect = pygame.Rect(ix + icon_t.get_width() + 8, iy, name_t.get_width() + 20, 22)
        screen.blit(name_t, (name_rect.x, iy))
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "pin_name"
            self.input_text = pin.name
            self.modal = ("edit_field", "pin_name")
        iy += 28

        # Pin type selector
        tl = fonts.small_bold.render("Type:", True, COLORS["text_dim"])
        screen.blit(tl, (ix, iy))
        tx = ix + 42
        for pt_key, pt_val in MAP_PIN_TYPES.items():
            is_act = pin.pin_type == pt_key
            tw = fonts.tiny.size(pt_key[:4])[0] + 10
            tr = pygame.Rect(tx, iy, tw, 16)
            pt_col = self._hex_to_rgb(pt_val["color"]) or (150, 150, 150)
            bg = pt_col if is_act else COLORS["panel"]
            if tr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    pin.pin_type = pt_key
            pygame.draw.rect(screen, bg, tr, border_radius=6)
            tt = fonts.tiny.render(pt_key[:4], True,
                                   COLORS["text_bright"] if is_act else COLORS["text_muted"])
            screen.blit(tt, (tx + 4, iy + 1))
            tx += tw + 3
        iy += 22

        # Description (editable)
        dl = fonts.small_bold.render("Desc:", True, COLORS["text_dim"])
        screen.blit(dl, (ix, iy))
        desc_rect = pygame.Rect(ix + 42, iy - 2, pw - 42, 20)
        pygame.draw.rect(screen, COLORS["input_bg"], desc_rect, border_radius=3)
        desc_text = pin.description or "(click to set)"
        dc = COLORS["text_main"] if pin.description else COLORS["text_muted"]
        dt = fonts.tiny.render(desc_text[:40], True, dc)
        screen.blit(dt, (desc_rect.x + 3, iy))
        if desc_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "pin_description"
            self.input_text = pin.description
            self.modal = ("edit_field", "pin_description")
        iy += 24

        # Notes (editable)
        nl = fonts.small_bold.render("Notes:", True, COLORS["text_dim"])
        screen.blit(nl, (ix, iy))
        notes_rect = pygame.Rect(ix, iy + 16, pw, 40)
        pygame.draw.rect(screen, COLORS["input_bg"], notes_rect, border_radius=3)
        notes_text = pin.notes or "(click to add notes)"
        nc = COLORS["text_main"] if pin.notes else COLORS["text_muted"]
        nt = fonts.tiny.render(notes_text[:60], True, nc)
        screen.blit(nt, (notes_rect.x + 3, iy + 20))
        if notes_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "pin_notes"
            self.input_text = pin.notes
            self.modal = ("edit_field", "pin_notes")
        iy += 62

        # Links
        ll = fonts.small_bold.render("Links:", True, COLORS["text_dim"])
        screen.blit(ll, (ix, iy))
        # Add link button
        add_btn = pygame.Rect(ix + 48, iy - 2, 18, 18)
        is_add = add_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["success"] if is_add else COLORS["panel"],
                         add_btn, border_radius=3)
        pt = fonts.tiny.render("+", True, COLORS["text_bright"])
        screen.blit(pt, (add_btn.x + 4, add_btn.y + 2))
        if is_add and pygame.mouse.get_pressed()[0]:
            self.input_active = "pin_add_link"
            self.input_text = ""
            self.modal = ("edit_field", "pin_add_link")
        iy += 20
        for li, link in enumerate(pin.links[:4]):
            prefix = "WEB" if link.startswith("http") else "FILE"
            lp = fonts.tiny.render(f"[{prefix}]", True, COLORS["accent"])
            screen.blit(lp, (ix + 4, iy + 1))
            lt_text = link if len(link) <= 35 else link[:32] + "..."
            lt_r = fonts.tiny.render(lt_text, True, COLORS["text_main"])
            link_rect = pygame.Rect(ix + 4 + lp.get_width() + 3, iy, lt_r.get_width(), 14)
            screen.blit(lt_r, (link_rect.x, iy + 1))
            if link_rect.collidepoint(mp):
                pygame.draw.line(screen, COLORS["accent"],
                                 (link_rect.x, link_rect.bottom),
                                 (link_rect.right, link_rect.bottom), 1)
                if pygame.mouse.get_pressed()[0]:
                    import webbrowser
                    try:
                        if link.startswith("http"):
                            webbrowser.open(link)
                        else:
                            os.startfile(link) if hasattr(os, 'startfile') else os.system(f'xdg-open "{link}"')
                    except Exception:
                        pass
            # Delete link
            del_x = link_rect.right + 4
            del_r = pygame.Rect(del_x, iy, 12, 14)
            if del_r.collidepoint(mp):
                dxt = fonts.tiny.render("x", True, COLORS["danger"])
                screen.blit(dxt, (del_x + 1, iy + 1))
                if pygame.mouse.get_pressed()[0]:
                    pin.links.pop(li)
                    break
            iy += 16

        # Visibility toggle
        iy += 8
        vis_btn = pygame.Rect(ix, iy, 80, 20)
        vis_hover = vis_btn.collidepoint(mp)
        vis_col = COLORS["success"] if pin.visible else COLORS["danger"]
        pygame.draw.rect(screen, COLORS["hover"] if vis_hover else vis_col, vis_btn, border_radius=3)
        vt = fonts.tiny.render("Visible" if pin.visible else "Hidden", True, COLORS["text_bright"])
        screen.blit(vt, (ix + 8, iy + 3))
        if vis_hover and pygame.mouse.get_pressed()[0]:
            pin.visible = not pin.visible

        # Delete pin button
        del_btn = pygame.Rect(ix + 90, iy, 80, 20)
        del_hover = del_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if del_hover else COLORS["danger"],
                         del_btn, border_radius=3)
        delt = fonts.tiny.render("Delete Pin", True, COLORS["text_bright"])
        screen.blit(delt, (ix + 96, iy + 3))
        if del_hover and pygame.mouse.get_pressed()[0]:
            remove_pin(self.world, pin.id)
            self.selected_pin_id = ""

    def _draw_dashed_line(self, screen, color, start, end, width, dash_len, gap_len):
        """Draw a dashed line."""
        import math
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        nx, ny = dx / length, dy / length
        pos = 0
        while pos < length:
            seg_end = min(pos + dash_len, length)
            sx = int(start[0] + nx * pos)
            sy = int(start[1] + ny * pos)
            ex = int(start[0] + nx * seg_end)
            ey = int(start[1] + ny * seg_end)
            pygame.draw.line(screen, color, (sx, sy), (ex, ey), width)
            pos += dash_len + gap_len

    def _draw_map_hover_tooltip(self, screen, mp, loc_id):
        """Draw a rich tooltip when hovering a location on the map."""
        loc = self.world.locations.get(loc_id)
        if not loc:
            return
        lines = [loc.name]
        lines.append(f"Type: {loc.location_type}")
        if loc.population:
            lines.append(f"Population: {loc.population:,}")
        if loc.map_note:
            lines.append(f"Note: {loc.map_note}")
        if loc.description:
            desc = loc.description[:120]
            if len(loc.description) > 120:
                desc += "..."
            lines.append(desc)
        npcs = get_npcs_at_location(self.world, loc_id)
        if npcs:
            npc_names = ", ".join(n.name for n in npcs[:4])
            if len(npcs) > 4:
                npc_names += f" +{len(npcs)-4}"
            lines.append(f"NPCs: {npc_names}")
        children = get_children(self.world, loc_id)
        if children:
            child_names = ", ".join(c.name for c in children[:4])
            if len(children) > 4:
                child_names += f" +{len(children)-4}"
            lines.append(f"Contains: {child_names}")
        # Routes from this location
        routes_from = [r for r in self.world.map_routes
                       if r.from_id == loc_id or r.to_id == loc_id]
        if routes_from:
            route_strs = []
            for r in routes_from[:3]:
                other_id = r.to_id if r.from_id == loc_id else r.from_id
                other = self.world.locations.get(other_id)
                if other:
                    info = f"{other.name} ({r.route_type}"
                    if r.distance_miles:
                        info += f", {r.distance_miles:.0f}mi"
                    info += ")"
                    route_strs.append(info)
            if route_strs:
                lines.append(f"Routes: {', '.join(route_strs)}")

        # Draw tooltip
        max_w = 350
        rendered = []
        for line in lines:
            wrapped = self._wrap_text(line, max_w - 16, fonts.small)
            rendered.extend(wrapped)

        if not rendered:
            return
        line_h = 16
        w = min(max_w, max(fonts.small.size(l)[0] for l in rendered) + 16)
        h = len(rendered) * line_h + 12
        tx = min(mp[0] + 15, SCREEN_WIDTH - w - 10)
        ty = min(mp[1] + 15, SCREEN_HEIGHT - h - 10)

        # Shadow + bg
        shadow = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 150), (0, 0, w + 4, h + 4), border_radius=6)
        screen.blit(shadow, (tx - 2, ty - 2))
        pygame.draw.rect(screen, COLORS["panel_light"], (tx, ty, w, h), border_radius=5)
        color = self._get_loc_color(loc)
        pygame.draw.rect(screen, color, (tx, ty, 3, h), border_radius=2)
        pygame.draw.rect(screen, COLORS["border_light"], (tx, ty, w, h), 1, border_radius=5)

        for i, line in enumerate(rendered):
            c = COLORS["text_bright"] if i == 0 else COLORS["text_main"]
            ts = fonts.small.render(line, True, c)
            screen.blit(ts, (tx + 8, ty + 6 + i * line_h))

    def _draw_map_info_panel(self, screen, mp, loc):
        """Draw detailed info panel for selected location on map."""
        info_w = 330
        info_h = min(500, SCREEN_HEIGHT - 140)
        info_rect = pygame.Rect(SCREEN_WIDTH - info_w - 30, 70, info_w, info_h)
        draw_gradient_rect(screen, info_rect, COLORS["panel"], COLORS["panel_dark"], 8)
        pygame.draw.rect(screen, COLORS["border_light"], info_rect, 1, border_radius=8)

        color = self._get_loc_color(loc)
        pygame.draw.rect(screen, color, (info_rect.x, info_rect.y + 2, 4, info_rect.height - 4), border_radius=2)

        iy = info_rect.y + 10
        ix = info_rect.x + 12
        pw = info_w - 24

        # Name
        nt = fonts.header.render(loc.name, True, COLORS["accent"])
        screen.blit(nt, (ix, iy))
        iy += 28

        # Type + population
        Badge.draw(screen, ix, iy, loc.location_type.upper(), color, fonts.tiny)
        if loc.population:
            pop_text = f"Pop: {loc.population:,}"
            pt = fonts.tiny.render(pop_text, True, COLORS["text_dim"])
            screen.blit(pt, (ix + 80, iy + 2))
        iy += 22

        # Map note
        if loc.map_note:
            note_lines = self._wrap_text(f"Note: {loc.map_note}", pw, fonts.small)
            for line in note_lines[:3]:
                nt = fonts.small.render(line, True, COLORS["warning"])
                screen.blit(nt, (ix, iy))
                iy += 16
            iy += 4

        # Description
        if loc.description:
            desc_lines = self._wrap_text(loc.description, pw, fonts.small)
            for line in desc_lines[:4]:
                dt = fonts.small.render(line, True, COLORS["text_main"])
                screen.blit(dt, (ix, iy))
                iy += 16
            iy += 4

        # Environment & lighting
        if loc.environment or loc.lighting != "bright":
            env_info = []
            if loc.environment:
                env_info.append(loc.environment)
            if loc.lighting and loc.lighting != "bright":
                env_info.append(f"Light: {loc.lighting}")
            et = fonts.tiny.render(" | ".join(env_info), True, COLORS["text_dim"])
            screen.blit(et, (ix, iy))
            iy += 16

        # NPCs
        npcs = get_npcs_at_location(self.world, loc.id)
        if npcs:
            Divider.draw(screen, ix, iy, pw)
            iy += 6
            nl = fonts.small_bold.render(f"NPCs ({len(npcs)})", True, COLORS["player"])
            screen.blit(nl, (ix, iy))
            iy += 18
            for npc in npcs[:8]:
                prefix = "[S] " if npc.is_shopkeeper else ""
                occ = f" — {npc.occupation}" if npc.occupation else ""
                att_cols = {"friendly": COLORS["success"], "unfriendly": COLORS["warning"], "hostile": COLORS["danger"]}
                att_col = att_cols.get(npc.attitude, COLORS["text_dim"])
                nt = fonts.tiny.render(f"{prefix}{npc.name}{occ}", True, COLORS["text_main"])
                screen.blit(nt, (ix + 4, iy))
                pygame.draw.circle(screen, att_col, (ix + pw - 8, iy + 6), 4)
                iy += 15
                if iy > info_rect.bottom - 60:
                    remaining = len(npcs) - npcs.index(npc) - 1
                    if remaining > 0:
                        mt = fonts.tiny.render(f"+{remaining} more...", True, COLORS["text_muted"])
                        screen.blit(mt, (ix + 4, iy))
                        iy += 15
                    break

        # Children
        children = get_children(self.world, loc.id)
        if children and iy < info_rect.bottom - 50:
            Divider.draw(screen, ix, iy, pw)
            iy += 6
            cl = fonts.small_bold.render(f"Locations ({len(children)})", True, COLORS["text_dim"])
            screen.blit(cl, (ix, iy))
            iy += 18
            for child in children[:6]:
                cc = self._get_loc_color(child)
                pygame.draw.circle(screen, cc, (ix + 6, iy + 6), 4)
                ct = fonts.tiny.render(f"  {child.name} ({child.location_type})", True, COLORS["text_main"])
                screen.blit(ct, (ix + 12, iy))
                iy += 15
                if iy > info_rect.bottom - 30:
                    break

        # Routes from this location
        routes = [r for r in self.world.map_routes if r.from_id == loc.id or r.to_id == loc.id]
        if routes and iy < info_rect.bottom - 40:
            Divider.draw(screen, ix, iy, pw)
            iy += 6
            rl = fonts.small_bold.render(f"Routes ({len(routes)})", True, COLORS["text_dim"])
            screen.blit(rl, (ix, iy))
            iy += 18
            for route in routes[:4]:
                other_id = route.to_id if route.from_id == loc.id else route.from_id
                other = self.world.locations.get(other_id)
                if other:
                    rc = self._MAP_ROUTE_COLORS.get(route.route_type, (120, 120, 120))
                    pygame.draw.circle(screen, rc, (ix + 6, iy + 6), 3)
                    info = f"  {other.name} ({route.route_type}"
                    if route.distance_miles:
                        info += f", {route.distance_miles:.0f}mi"
                    if route.label:
                        info += f", {route.label}"
                    info += ")"
                    rt = fonts.tiny.render(info[:50], True, COLORS["text_main"])
                    screen.blit(rt, (ix + 12, iy))
                    iy += 15

        # Edit hint
        eh = fonts.tiny.render("Click again to open detail view", True, COLORS["text_muted"])
        screen.blit(eh, (ix, info_rect.bottom - 20))

    def _map_tool_action(self, action):
        """Handle map toolbar button clicks."""
        if action == "add_route":
            self._map_route_mode = not getattr(self, '_map_route_mode', False)
            self._map_route_from = ""
        elif action == "set_image":
            # Try a native file picker first; fall back to text input.
            picked = self._pick_image_file()
            if picked:
                local_path = self._import_map_image(picked)
                if local_path:
                    self.world.map_image_path = local_path
                    self._load_map_background()
                    if self._map_bg_surface:
                        iw, ih = self._map_bg_surface.get_size()
                        self._status_msg = f"Map loaded: {os.path.basename(local_path)} ({iw}x{ih})"
                    else:
                        self._status_msg = f"Map path set but image failed to load: {os.path.basename(local_path)}"
                    self._status_timer = 180
                else:
                    self._status_msg = "Failed to import map image"
                    self._status_timer = 180
            else:
                self.modal = ("edit_field", "map_image_path")
                self.input_active = "map_image_path"
                self.input_text = self.world.map_image_path
        elif action == "reset_view":
            self.map_offset_x = 0
            self.map_offset_y = 0
            self.map_zoom = 1.0
        elif action == "set_color":
            if self.selected_location_id:
                loc = self.world.locations.get(self.selected_location_id)
                if loc:
                    self.modal = ("edit_field", "location_color")
                    self.input_active = "location_color"
                    self.input_text = loc.map_color
        elif action == "set_note":
            if self.selected_location_id:
                loc = self.world.locations.get(self.selected_location_id)
                if loc:
                    self.modal = ("edit_field", "location_map_note")
                    self.input_active = "location_map_note"
                    self.input_text = loc.map_note
        elif action == "add_pin":
            self._map_pin_mode = not self._map_pin_mode
            self._map_route_mode = False
            self._map_token_mode = False
            self._map_scale_mode = False
        elif action == "add_token":
            self._map_token_mode = not self._map_token_mode
            self._map_pin_mode = False
            self._map_route_mode = False
            self._map_scale_mode = False
        elif action == "set_scale":
            self._map_scale_mode = not self._map_scale_mode
            self._map_scale_point1 = None
            self._map_pin_mode = False
            self._map_route_mode = False
            self._map_token_mode = False
        elif action == "set_scale_value":
            self.modal = ("edit_field", "map_scale_miles")
            self.input_active = "map_scale_miles"
            self.input_text = str(self.world.map_scale_miles) if self.world.map_scale_miles else ""
        elif action == "cycle_token_type":
            types = list(MAP_TOKEN_TYPES.keys())
            idx = types.index(self._map_token_type) if self._map_token_type in types else 0
            self._map_token_type = types[(idx + 1) % len(types)]
        elif action == "loc_sub_map":
            if self.selected_location_id:
                loc = self.world.locations.get(self.selected_location_id)
                if loc:
                    self.modal = ("edit_field", "loc_map_image")
                    self.input_active = "loc_map_image"
                    self.input_text = loc.map_image_path

    def _auto_layout_locations(self, roots, grid_area):
        """Auto-assign positions to locations that don't have one yet."""
        import math
        if not roots:
            return
        unplaced = [loc for loc in roots if loc.id not in self._location_map_positions]
        if not unplaced:
            # Still check children
            for root in roots:
                self._auto_layout_children(root)
            return

        cols = max(1, min(5, len(unplaced)))
        for i, loc in enumerate(unplaced):
            row = i // cols
            col = i % cols
            x = 10 + (col + 0.5) * (80 / cols)
            y = 10 + (row + 0.5) * 25
            self._location_map_positions[loc.id] = (x, y)
            self._auto_layout_children(loc)

        # Also handle placed roots' children
        for root in roots:
            if root not in unplaced:
                self._auto_layout_children(root)

    def _auto_layout_children(self, parent_loc):
        """Recursively auto-layout children around their parent."""
        import math
        pos = self._location_map_positions.get(parent_loc.id)
        if not pos:
            return
        px, py = pos
        children = get_children(self.world, parent_loc.id)
        unplaced = [c for c in children if c.id not in self._location_map_positions]
        n = len(unplaced)
        if n > 0:
            radius = 8 + n * 2
            for j, child in enumerate(unplaced):
                angle = (j / n) * 2 * math.pi - math.pi / 2
                cx = px + math.cos(angle) * radius
                cy = py + math.sin(angle) * radius * 0.6
                cx = max(2, min(98, cx))
                cy = max(2, min(98, cy))
                self._location_map_positions[child.id] = (cx, cy)

        # Recurse
        for child in children:
            self._auto_layout_children(child)

    @staticmethod
    def _wrap_text(text, max_width, font):
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # ================================================================
    # TEMPLATE BROWSER
    # ================================================================

    def _draw_templates_browser(self, screen, mp):
        """Draw template browser with inn and shop templates."""
        y = 70
        mid = SCREEN_WIDTH // 2

        # Header
        hdr = fonts.header.render("Template Browser", True, COLORS["accent"])
        screen.blit(hdr, (30, y))
        y += 35

        # Tab buttons for inn vs shop vs city templates
        tabs = [("Inn Templates", "inn_templates"), ("Shop Templates", "shop_templates"), ("City Templates", "city_templates")]
        tx = 30
        for label, view_key in tabs:
            is_active = self.template_view == view_key
            tw = fonts.body.size(label)[0] + 20
            tab_rect = pygame.Rect(tx, y, tw, 28)
            bg = COLORS["accent_dim"] if is_active else COLORS["panel"]
            if tab_rect.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    self.template_view = view_key
                    self.template_scroll = 0
            pygame.draw.rect(screen, bg, tab_rect, border_radius=4)
            if is_active:
                pygame.draw.rect(screen, COLORS["accent"], tab_rect, 1, border_radius=4)
            tt = fonts.body.render(label, True, COLORS["text_bright"] if is_active else COLORS["text_dim"])
            screen.blit(tt, (tx + 10, y + 4))
            tx += tw + 8
        y += 38

        # Current location context
        if self.selected_location_id:
            loc = self.world.locations.get(self.selected_location_id)
            if loc:
                ctx = fonts.small.render(f"Parent: {loc.name} ({loc.location_type})", True, COLORS["text_dim"])
                screen.blit(ctx, (30, y))
                y += 20
        else:
            ctx = fonts.small.render("Select a location first to add templates as children (or adds to root)", True, COLORS["text_muted"])
            screen.blit(ctx, (30, y))
            y += 20

        y += 5

        if self.template_view == "inn_templates":
            self._draw_inn_templates(screen, mp, y)
        elif self.template_view == "shop_templates":
            self._draw_shop_templates(screen, mp, y)
        elif self.template_view == "city_templates":
            self._draw_city_templates(screen, mp, y)

    def _draw_inn_templates(self, screen, mp, start_y):
        """Draw inn template cards."""
        y = start_y + self.template_scroll
        tiers = get_all_inn_tiers()
        tier_labels = {
            "squalid": ("Squalid", COLORS["danger"]),
            "poor": ("Poor", COLORS["warning"]),
            "modest": ("Modest", COLORS["text_main"]),
            "comfortable": ("Comfortable", COLORS["success"]),
            "wealthy": ("Wealthy", COLORS["legendary"]),
            "aristocratic": ("Aristocratic", COLORS["spell"]),
        }

        for tier in tiers:
            label, color = tier_labels.get(tier, (tier, COLORS["text_dim"]))
            # Tier header
            th = fonts.body_bold.render(f"--- {label} ---", True, color)
            screen.blit(th, (30, y))
            y += 25

            templates = get_inn_templates_by_tier(tier)
            for tkey, tdata in INN_TEMPLATES.items():
                if tdata["tier"] != tier:
                    continue

                card_rect = pygame.Rect(30, y, SCREEN_WIDTH - 60, 90)
                is_hover = card_rect.collidepoint(mp)
                bg = COLORS["hover"] if is_hover else COLORS["panel"]
                pygame.draw.rect(screen, bg, card_rect, border_radius=6)
                pygame.draw.rect(screen, color if is_hover else COLORS["border"],
                                 card_rect, 1, border_radius=6)

                # Color strip
                pygame.draw.rect(screen, color, (card_rect.x + 2, card_rect.y + 2, 4, card_rect.height - 4))

                # Name
                nt = fonts.body_bold.render(tdata["name"], True, COLORS["text_bright"])
                screen.blit(nt, (card_rect.x + 14, card_rect.y + 6))

                # Tier badge
                Badge.draw(screen, card_rect.x + 14 + nt.get_width() + 10, card_rect.y + 8,
                           tier.upper(), color, fonts.tiny)

                # Description preview
                desc = tdata.get("description", "")[:150]
                dt = fonts.small.render(desc, True, COLORS["text_dim"])
                screen.blit(dt, (card_rect.x + 14, card_rect.y + 28))

                # Staff count, room count
                staff_count = len(tdata.get("staff", []))
                room_count = len(tdata.get("rooms", {}))
                menu_count = len(tdata.get("menu", {}))
                info = f"Staff: {staff_count} | Rooms: {room_count} | Menu: {menu_count}"
                it = fonts.tiny.render(info, True, COLORS["text_muted"])
                screen.blit(it, (card_rect.x + 14, card_rect.y + 48))

                # Apply button
                apply_rect = pygame.Rect(card_rect.right - 120, card_rect.y + 30, 110, 30)
                apply_hover = apply_rect.collidepoint(mp)
                pygame.draw.rect(screen, COLORS["success_hover"] if apply_hover else COLORS["success"],
                                 apply_rect, border_radius=4)
                at = fonts.small_bold.render("+ Add", True, COLORS["text_bright"])
                screen.blit(at, (apply_rect.x + 30, apply_rect.y + 6))
                if apply_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                    self._apply_template("inn", tkey)
                    self._click_cooldown = 20

                # Special features preview
                features = tdata.get("special_features", [])
                if features:
                    feat_y = card_rect.y + 64
                    for feat in features[:2]:
                        ft = fonts.tiny.render(f"  * {feat[:80]}", True, COLORS["success"])
                        screen.blit(ft, (card_rect.x + 14, feat_y))
                        feat_y += 13

                y += 95

            y += 10

    def _draw_shop_templates(self, screen, mp, start_y):
        """Draw shop template cards."""
        y = start_y + self.template_scroll
        tier_labels = {
            1: ("Tier 1 (Levels 1-4)", COLORS["success"]),
            2: ("Tier 2 (Levels 5-10)", COLORS["accent"]),
            3: ("Tier 3 (Levels 11-16)", COLORS["spell"]),
            4: ("Tier 4 (Levels 17-20)", COLORS["legendary"]),
        }

        for tier in [1, 2, 3, 4]:
            templates = get_shop_templates_by_tier(tier)
            if not templates:
                continue

            label, color = tier_labels[tier]
            th = fonts.body_bold.render(f"--- {label} ---", True, color)
            screen.blit(th, (30, y))
            y += 25

            for tkey, tdata in SHOP_TEMPLATES.items():
                if tdata["tier"] != tier:
                    continue

                card_rect = pygame.Rect(30, y, SCREEN_WIDTH - 60, 85)
                is_hover = card_rect.collidepoint(mp)
                bg = COLORS["hover"] if is_hover else COLORS["panel"]
                pygame.draw.rect(screen, bg, card_rect, border_radius=6)
                pygame.draw.rect(screen, color if is_hover else COLORS["border"],
                                 card_rect, 1, border_radius=6)

                pygame.draw.rect(screen, color, (card_rect.x + 2, card_rect.y + 2, 4, card_rect.height - 4))

                # Name + type
                nt = fonts.body_bold.render(tdata["name"], True, COLORS["text_bright"])
                screen.blit(nt, (card_rect.x + 14, card_rect.y + 6))
                type_badge_x = card_rect.x + 14 + nt.get_width() + 10
                Badge.draw(screen, type_badge_x, card_rect.y + 8,
                           tdata["shop_type"].upper(), color, fonts.tiny)

                # Description
                desc = tdata.get("description", "")[:150]
                dt = fonts.small.render(desc, True, COLORS["text_dim"])
                screen.blit(dt, (card_rect.x + 14, card_rect.y + 28))

                # Item count, staff count
                item_count = len(tdata.get("inventory", []))
                staff_count = len(tdata.get("staff", []))
                info = f"Items: {item_count} | Staff: {staff_count} | Price: {tdata.get('price_modifier', 'normal')}"
                it = fonts.tiny.render(info, True, COLORS["text_muted"])
                screen.blit(it, (card_rect.x + 14, card_rect.y + 48))

                # Apply button
                apply_rect = pygame.Rect(card_rect.right - 120, card_rect.y + 25, 110, 30)
                apply_hover = apply_rect.collidepoint(mp)
                pygame.draw.rect(screen, COLORS["success_hover"] if apply_hover else COLORS["success"],
                                 apply_rect, border_radius=4)
                at = fonts.small_bold.render("+ Add", True, COLORS["text_bright"])
                screen.blit(at, (apply_rect.x + 30, apply_rect.y + 6))
                if apply_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                    self._apply_template("shop", tkey)
                    self._click_cooldown = 20

                # Top items preview
                items = tdata.get("inventory", [])[:3]
                if items:
                    item_strs = [f"{i['name']} ({format_price(i['price_gp'])})" for i in items]
                    preview = "  Items: " + ", ".join(item_strs)
                    pt = fonts.tiny.render(preview[:100], True, COLORS["legendary"])
                    screen.blit(pt, (card_rect.x + 14, card_rect.y + 65))

                y += 90

            y += 10

    def _draw_city_templates(self, screen, mp, start_y):
        """Draw city/settlement template cards."""
        y = start_y + self.template_scroll
        tier_labels = {
            1: ("Tier 1 — Kylät (Levels 1-4)", COLORS["success"]),
            2: ("Tier 2 — Kauppalat (Levels 5-10)", COLORS["accent"]),
            3: ("Tier 3 — Kaupungit (Levels 11-16)", COLORS["spell"]),
        }

        for tier in [1, 2, 3]:
            templates = get_city_templates_by_tier(tier)
            if not templates:
                continue

            label, color = tier_labels[tier]
            th = fonts.body_bold.render(f"--- {label} ---", True, color)
            screen.blit(th, (30, y))
            y += 25

            for tkey, tdata in CITY_TEMPLATES.items():
                if tdata["tier"] != tier:
                    continue

                card_rect = pygame.Rect(30, y, SCREEN_WIDTH - 60, 100)
                is_hover = card_rect.collidepoint(mp)
                bg = COLORS["hover"] if is_hover else COLORS["panel"]
                pygame.draw.rect(screen, bg, card_rect, border_radius=6)
                pygame.draw.rect(screen, color if is_hover else COLORS["border"],
                                 card_rect, 1, border_radius=6)
                pygame.draw.rect(screen, color, (card_rect.x + 2, card_rect.y + 2, 4, card_rect.height - 4))

                # Name + type badge
                nt = fonts.body_bold.render(tdata["name"], True, COLORS["text_bright"])
                screen.blit(nt, (card_rect.x + 14, card_rect.y + 6))
                Badge.draw(screen, card_rect.x + 14 + nt.get_width() + 10, card_rect.y + 8,
                           tdata["settlement_type"].upper(), color, fonts.tiny)

                # Population
                pop = tdata.get("population", 0)
                if pop:
                    pt = fonts.tiny.render(f"Pop: {pop:,}", True, COLORS["text_muted"])
                    screen.blit(pt, (card_rect.x + 14 + nt.get_width() + 90, card_rect.y + 10))

                # Description
                desc = tdata.get("description", "")[:160]
                dt = fonts.small.render(desc, True, COLORS["text_dim"])
                screen.blit(dt, (card_rect.x + 14, card_rect.y + 28))

                # Info line
                dist_count = len(tdata.get("districts", []))
                npc_count = len(tdata.get("key_npcs", []))
                hook_count = len(tdata.get("hooks", []))
                info = f"Districts: {dist_count} | NPCs: {npc_count} | Hooks: {hook_count}"
                it = fonts.tiny.render(info, True, COLORS["text_muted"])
                screen.blit(it, (card_rect.x + 14, card_rect.y + 48))

                # Special features preview
                feats = tdata.get("special_features", [])[:2]
                if feats:
                    feat_y = card_rect.y + 65
                    for feat in feats:
                        ft = fonts.tiny.render(f"  * {feat[:90]}", True, COLORS["success"])
                        screen.blit(ft, (card_rect.x + 14, feat_y))
                        feat_y += 13

                # Apply button
                apply_rect = pygame.Rect(card_rect.right - 120, card_rect.y + 35, 110, 30)
                apply_hover = apply_rect.collidepoint(mp)
                pygame.draw.rect(screen, COLORS["success_hover"] if apply_hover else COLORS["success"],
                                 apply_rect, border_radius=4)
                at = fonts.small_bold.render("+ Add", True, COLORS["text_bright"])
                screen.blit(at, (apply_rect.x + 30, apply_rect.y + 6))
                if apply_hover and pygame.mouse.get_pressed()[0] and self._click_cooldown <= 0:
                    self._apply_template("city", tkey)
                    self._click_cooldown = 20

                y += 105

            y += 10

    def _handle_templates_click(self, mp):
        """Handle clicks in template browser (most handled inline via draw)."""
        pass  # Click handling is done in draw methods via get_pressed()

    # ================================================================
    # SERVICES VIEWER
    # ================================================================

    def _draw_services_viewer(self, screen, mp):
        """Draw services and price list viewer."""
        y = 70
        mid = SCREEN_WIDTH // 2

        hdr = fonts.header.render("Services & Price Lists", True, COLORS["accent"])
        screen.blit(hdr, (30, y))
        y += 35

        # Category tabs
        categories = list(SERVICE_CATEGORIES.items())
        tx = 30
        for cat_key, cat_label in categories:
            is_active = self.services_category == cat_key
            tw = fonts.small.size(cat_label)[0] + 14
            tab_rect = pygame.Rect(tx, y, tw, 24)
            bg = COLORS["accent_dim"] if is_active else COLORS["panel"]
            if tab_rect.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    self.services_category = cat_key
                    self.services_scroll = 0
            pygame.draw.rect(screen, bg, tab_rect, border_radius=4)
            if is_active:
                pygame.draw.rect(screen, COLORS["accent"], tab_rect, 1, border_radius=4)
            tt = fonts.small.render(cat_label, True, COLORS["text_bright"] if is_active else COLORS["text_dim"])
            screen.blit(tt, (tx + 7, y + 4))
            tx += tw + 4
            if tx > SCREEN_WIDTH - 200:
                tx = 30
                y += 28
        y += 32

        # Service list
        all_services = get_all_services()
        services = all_services.get(self.services_category, {})

        # Table header
        pygame.draw.rect(screen, COLORS["panel_header"], (30, y, SCREEN_WIDTH - 60, 24), border_radius=3)
        col_headers = [("Name", 30), ("Price", 350), ("Description", 500)]
        for header_text, hx in col_headers:
            ht = fonts.small_bold.render(header_text, True, COLORS["text_dim"])
            screen.blit(ht, (hx, y + 4))
        y += 28

        row_y = y + self.services_scroll
        for svc_key, svc_data in services.items():
            if row_y < 60 or row_y > SCREEN_HEIGHT - 130:
                row_y += 50
                continue

            row_rect = pygame.Rect(30, row_y, SCREEN_WIDTH - 60, 46)
            is_hover = row_rect.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else (COLORS["panel"] if svc_key.find("_") % 2 == 0 else COLORS["panel_dark"])
            pygame.draw.rect(screen, bg, row_rect, border_radius=3)

            # Name
            name = svc_data.get("name", svc_key)
            nt = fonts.body.render(name, True, COLORS["text_bright"])
            screen.blit(nt, (35, row_y + 3))

            # Price
            price = 0
            for price_field in ["cost_gp", "cost_per_day_gp", "cost_per_night_gp",
                                "cost_per_mile_gp", "cost_buy_gp", "cost_rent_per_month_gp"]:
                if price_field in svc_data:
                    price = svc_data[price_field]
                    break
            price_str = format_price(price)
            # Add per-unit label
            if "cost_per_day_gp" in svc_data:
                price_str += " /day"
            elif "cost_per_night_gp" in svc_data:
                price_str += " /night"
            elif "cost_per_mile_gp" in svc_data:
                price_str += " /mile"
            elif "cost_rent_per_month_gp" in svc_data:
                price_str += " /month"
            pt = fonts.body_bold.render(price_str, True, COLORS["legendary"])
            screen.blit(pt, (350, row_y + 3))

            # Description (wrapped)
            desc = svc_data.get("description", "")
            desc_lines = self._wrap_text(desc, SCREEN_WIDTH - 540, fonts.tiny)
            for i, line in enumerate(desc_lines[:2]):
                dt = fonts.tiny.render(line, True, COLORS["text_dim"])
                screen.blit(dt, (500, row_y + 3 + i * 14))

            # Quality/tier indicator if present
            quality = svc_data.get("quality")
            if quality is not None:
                if isinstance(quality, str):
                    Badge.draw(screen, row_rect.right - 80, row_y + 14, quality.upper(),
                               COLORS["accent_dim"], fonts.tiny)
                elif isinstance(quality, int):
                    quality_names = ["Wretched", "Squalid", "Poor", "Modest", "Comfortable", "Wealthy", "Aristocratic"]
                    if 0 <= quality < len(quality_names):
                        Badge.draw(screen, row_rect.right - 100, row_y + 14,
                                   quality_names[quality], COLORS["accent_dim"], fonts.tiny)

            # Category if present
            cat = svc_data.get("category")
            if cat:
                Badge.draw(screen, row_rect.right - 80, row_y + 28, cat.upper(),
                           COLORS["spell"], fonts.tiny)

            row_y += 50

    def _handle_services_click(self, mp):
        """Handle clicks in services viewer (handled inline via draw)."""
        pass

    # ================================================================
    # TRAVEL VIEWER
    # ================================================================

    def _draw_travel_viewer(self, screen, mp):
        """Draw travel calculator and mount/vehicle browser."""
        y = 70

        hdr = fonts.header.render("Travel & Transportation", True, COLORS["accent"])
        screen.blit(hdr, (30, y))
        y += 35

        # Three columns: Mounts | Vehicles | Travel Calculator
        col_w = (SCREEN_WIDTH - 80) // 3
        col1_x = 30
        col2_x = col1_x + col_w + 10
        col3_x = col2_x + col_w + 10

        # Column 1: Mounts
        self._draw_travel_mounts(screen, mp, col1_x, y, col_w)

        # Column 2: Vehicles
        self._draw_travel_vehicles(screen, mp, col2_x, y, col_w)

        # Column 3: Travel calculator + pace
        self._draw_travel_calculator(screen, mp, col3_x, y, col_w)

    def _draw_travel_mounts(self, screen, mp, x, start_y, w):
        """Draw mount list."""
        y = start_y
        Panel(x, y, w, SCREEN_HEIGHT - start_y - 70, "Mounts & Animals").draw(screen)
        y += 32

        row_y = y + self.scroll_y
        for mkey, mount in MOUNTS.items():
            if row_y < start_y or row_y > SCREEN_HEIGHT - 130:
                row_y += 70
                continue

            card = pygame.Rect(x + 5, row_y, w - 10, 65)
            is_hover = card.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel_dark"]
            pygame.draw.rect(screen, bg, card, border_radius=4)

            # Name
            nt = fonts.small_bold.render(mount["name"], True, COLORS["text_bright"])
            screen.blit(nt, (card.x + 6, card.y + 3))

            # Category badge
            cat_colors = {"common": COLORS["success"], "exotic": COLORS["spell"], "magical": COLORS["legendary"]}
            Badge.draw(screen, card.x + 6 + nt.get_width() + 8, card.y + 4,
                       mount.get("category", "").upper(),
                       cat_colors.get(mount.get("category", ""), COLORS["text_dim"]), fonts.tiny)

            # Prices
            buy = format_price(mount["cost_buy_gp"]) if mount["cost_buy_gp"] else "N/A"
            rent = format_price(mount.get("cost_rent_per_day_gp", 0)) + "/d" if mount.get("cost_rent_per_day_gp", 0) else ""
            price_text = f"Buy: {buy}"
            if rent:
                price_text += f" | Rent: {rent}"
            pt = fonts.tiny.render(price_text, True, COLORS["legendary"])
            screen.blit(pt, (card.x + 6, card.y + 20))

            # Stats
            speed = f"Speed: {mount['speed_ft']} ft"
            if mount.get("fly_speed_ft"):
                speed += f" (Fly: {mount['fly_speed_ft']} ft)"
            carry = f"Carry: {mount['carry_capacity_lb']} lb" if mount.get("carry_capacity_lb") else ""
            stats_text = f"{speed} | {carry}" if carry else speed
            st = fonts.tiny.render(stats_text, True, COLORS["text_dim"])
            screen.blit(st, (card.x + 6, card.y + 35))

            # Description preview
            desc = mount.get("description", "")[:80]
            dt = fonts.tiny.render(desc, True, COLORS["text_muted"])
            screen.blit(dt, (card.x + 6, card.y + 49))

            row_y += 70

    def _draw_travel_vehicles(self, screen, mp, x, start_y, w):
        """Draw vehicle lists (land + water)."""
        y = start_y
        Panel(x, y, w, SCREEN_HEIGHT - start_y - 70, "Vehicles (Land & Water)").draw(screen)
        y += 32

        row_y = y + self.scroll_y

        # Land vehicles header
        lh = fonts.small_bold.render("-- Land --", True, COLORS["warning"])
        screen.blit(lh, (x + 10, row_y))
        row_y += 18

        for vkey, vehicle in VEHICLES_LAND.items():
            if row_y < start_y or row_y > SCREEN_HEIGHT - 130:
                row_y += 55
                continue

            card = pygame.Rect(x + 5, row_y, w - 10, 50)
            is_hover = card.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel_dark"]
            pygame.draw.rect(screen, bg, card, border_radius=4)

            nt = fonts.small_bold.render(vehicle["name"], True, COLORS["text_bright"])
            screen.blit(nt, (card.x + 6, card.y + 3))

            buy = format_price(vehicle["cost_buy_gp"])
            rent = format_price(vehicle.get("cost_rent_per_day_gp", 0)) + "/d" if vehicle.get("cost_rent_per_day_gp") else ""
            price_text = f"Buy: {buy}"
            if rent:
                price_text += f" | Rent: {rent}"
            pt = fonts.tiny.render(price_text, True, COLORS["legendary"])
            screen.blit(pt, (card.x + 6, card.y + 20))

            info = f"Carry: {vehicle['carry_capacity_lb']} lb | Animals: {vehicle.get('animals_needed', '?')}"
            it = fonts.tiny.render(info, True, COLORS["text_dim"])
            screen.blit(it, (card.x + 6, card.y + 34))

            row_y += 55

        # Water vehicles header
        row_y += 10
        wh = fonts.small_bold.render("-- Water & Air --", True, COLORS["cold"])
        screen.blit(wh, (x + 10, row_y))
        row_y += 18

        for vkey, vehicle in VEHICLES_WATER.items():
            if row_y < start_y or row_y > SCREEN_HEIGHT - 130:
                row_y += 55
                continue

            card = pygame.Rect(x + 5, row_y, w - 10, 50)
            is_hover = card.collidepoint(mp)
            bg = COLORS["hover"] if is_hover else COLORS["panel_dark"]
            pygame.draw.rect(screen, bg, card, border_radius=4)

            nt = fonts.small_bold.render(vehicle["name"], True, COLORS["text_bright"])
            screen.blit(nt, (card.x + 6, card.y + 3))

            buy = format_price(vehicle["cost_buy_gp"])
            pt = fonts.tiny.render(f"Buy: {buy}", True, COLORS["legendary"])
            screen.blit(pt, (card.x + 6, card.y + 20))

            info_parts = [f"Speed: {vehicle['speed_mph']} mph"]
            if vehicle.get("passengers"):
                info_parts.append(f"Pass: {vehicle['passengers']}")
            if vehicle.get("crew"):
                info_parts.append(f"Crew: {vehicle['crew']}")
            if vehicle.get("cargo_tons"):
                info_parts.append(f"Cargo: {vehicle['cargo_tons']}t")
            it = fonts.tiny.render(" | ".join(info_parts), True, COLORS["text_dim"])
            screen.blit(it, (card.x + 6, card.y + 34))

            row_y += 55

    def _draw_travel_calculator(self, screen, mp, x, start_y, w):
        """Draw travel pace calculator and passage costs."""
        y = start_y
        Panel(x, y, w, SCREEN_HEIGHT - start_y - 70, "Travel Calculator & Costs").draw(screen)
        y += 35

        # Travel Pace table
        pace_label = fonts.small_bold.render("Travel Pace:", True, COLORS["text_dim"])
        screen.blit(pace_label, (x + 10, y))
        y += 20

        for pkey, pace in TRAVEL_PACE.items():
            card = pygame.Rect(x + 5, y, w - 10, 40)
            pygame.draw.rect(screen, COLORS["panel_dark"], card, border_radius=3)

            nt = fonts.small_bold.render(pace["name"], True, COLORS["text_bright"])
            screen.blit(nt, (card.x + 8, card.y + 3))

            stats = f"{pace['miles_per_hour']} mph | {pace['miles_per_day']} miles/day"
            st = fonts.tiny.render(stats, True, COLORS["accent"])
            screen.blit(st, (card.x + 8, card.y + 20))

            et = fonts.tiny.render(pace["effect"], True, COLORS["text_dim"])
            screen.blit(et, (card.x + w // 2, card.y + 20))

            y += 44

        # Terrain modifiers
        y += 10
        terrain_label = fonts.small_bold.render("Terrain Modifiers:", True, COLORS["text_dim"])
        screen.blit(terrain_label, (x + 10, y))
        y += 18

        for tkey, terrain in TERRAIN_MODIFIERS.items():
            if y > SCREEN_HEIGHT - 140:
                break
            row = pygame.Rect(x + 5, y, w - 10, 22)
            pygame.draw.rect(screen, COLORS["panel_dark"], row, border_radius=2)

            nt = fonts.tiny.render(terrain["name"], True, COLORS["text_bright"])
            screen.blit(nt, (row.x + 6, row.y + 4))

            mod = f"x{terrain['speed_modifier']:.2f}"
            enc = f"Enc: {int(terrain['encounter_chance'] * 100)}%"
            mt = fonts.tiny.render(f"{mod} | {enc}", True, COLORS["text_dim"])
            screen.blit(mt, (row.x + w // 2, row.y + 4))

            y += 24

        # Passage costs
        y += 10
        if y < SCREEN_HEIGHT - 200:
            pass_label = fonts.small_bold.render("Passage Costs:", True, COLORS["text_dim"])
            screen.blit(pass_label, (x + 10, y))
            y += 18

            for pkey, passage in PASSAGE_COSTS.items():
                if y > SCREEN_HEIGHT - 140:
                    break
                row = pygame.Rect(x + 5, y, w - 10, 35)
                pygame.draw.rect(screen, COLORS["panel_dark"], row, border_radius=3)

                nt = fonts.small.render(passage["name"], True, COLORS["text_bright"])
                screen.blit(nt, (row.x + 6, row.y + 3))

                if "cost_per_mile_gp" in passage:
                    cost = format_price(passage["cost_per_mile_gp"]) + "/mile"
                elif "cost_per_use_gp" in passage:
                    cost = format_price(passage["cost_per_use_gp"]) + "/use"
                else:
                    cost = "?"
                ct = fonts.tiny.render(cost, True, COLORS["legendary"])
                screen.blit(ct, (row.x + 6, row.y + 20))

                y += 38

    def _handle_travel_click(self, mp):
        """Handle clicks in travel viewer (handled inline)."""
        pass

    # ================================================================
    # QUESTS VIEWER
    # ================================================================

    def _draw_quests_viewer(self, screen, mp):
        """Draw quest list (left) and selected quest detail (right)."""
        mid = SCREEN_WIDTH // 2

        # Search bar
        search_rect = pygame.Rect(20, 68, 300, 28)
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=3)
        pygame.draw.rect(screen, COLORS["input_focus"] if self.quest_search_active else COLORS["border"],
                         search_rect, 1, border_radius=3)
        st = fonts.small.render(self.quest_search or "Search quests...", True,
                                COLORS["text_main"] if self.quest_search else COLORS["text_muted"])
        screen.blit(st, (search_rect.x + 5, search_rect.y + 5))

        # Filter tabs
        tx = 330
        for filt in ["all", "active", "not_started", "completed", "failed", "on_hold"]:
            is_act = self.quest_filter == filt
            label = filt.replace("_", " ").title()
            tw = fonts.tiny.size(label)[0] + 12
            tab_rect = pygame.Rect(tx, 70, tw, 22)
            bg = COLORS["accent_dim"] if is_act else COLORS["panel"]
            if tab_rect.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    self.quest_filter = filt
            pygame.draw.rect(screen, bg, tab_rect, border_radius=4)
            if is_act:
                pygame.draw.rect(screen, COLORS["accent"], tab_rect, 1, border_radius=4)
            tt = fonts.tiny.render(label, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(tt, (tx + 6, 73))
            tx += tw + 4

        # Quest list
        y = 105 + self.scroll_y
        quests = list(self.world.quests.values())
        if self.quest_search:
            quests = search_quests(self.world, self.quest_search)
        if self.quest_filter != "all":
            quests = [q for q in quests if q.status == self.quest_filter]

        status_cols = {
            "active": COLORS["success"], "completed": COLORS["text_dim"],
            "failed": COLORS["danger"], "not_started": COLORS["warning"],
            "on_hold": COLORS["cold"],
        }
        priority_cols = {
            "urgent": COLORS["danger"], "high": COLORS["warning"],
            "normal": COLORS["text_dim"], "low": COLORS["cold"],
        }

        if not quests:
            hint = fonts.body.render("No quests found. Click '+ Quest' to create one.", True, COLORS["text_muted"])
            screen.blit(hint, (30, y))
        else:
            for quest in quests:
                if y < 50 or y > SCREEN_HEIGHT - 130:
                    y += 56
                    continue
                is_sel = quest.id == self.selected_quest_id
                rect = pygame.Rect(20, y, mid - 40, 50)
                bg = COLORS["selected"] if is_sel else COLORS["panel"]
                if rect.collidepoint(mp):
                    bg = COLORS["hover"]
                pygame.draw.rect(screen, bg, rect, border_radius=5)
                if is_sel:
                    pygame.draw.rect(screen, COLORS["accent_dim"], rect, 1, border_radius=5)

                # Quest name
                nt = fonts.body.render(quest.name, True, COLORS["text_bright"])
                screen.blit(nt, (rect.x + 8, y + 3))

                # Status badge
                scol = status_cols.get(quest.status, COLORS["text_dim"])
                slabel = quest.status.replace("_", " ").upper()
                Badge.draw(screen, rect.x + 8, y + 26, slabel, scol, fonts.tiny)

                # Type badge
                type_x = rect.x + 8 + fonts.tiny.size(slabel)[0] + 20
                Badge.draw(screen, type_x, y + 26, quest.quest_type.upper(), COLORS["spell"], fonts.tiny)

                # Priority indicator
                pcol = priority_cols.get(quest.priority, COLORS["text_dim"])
                if quest.priority in ("urgent", "high"):
                    pt = fonts.tiny.render(quest.priority.upper(), True, pcol)
                    screen.blit(pt, (rect.right - pt.get_width() - 10, y + 5))

                # Objective progress
                total_obj = len(quest.objectives)
                done_obj = sum(1 for o in quest.objectives if o.completed)
                if total_obj > 0:
                    prog = f"{done_obj}/{total_obj}"
                    prt = fonts.tiny.render(prog, True, COLORS["success"] if done_obj == total_obj else COLORS["text_dim"])
                    screen.blit(prt, (rect.right - prt.get_width() - 10, y + 30))

                y += 56

        # Right panel: selected quest detail
        if self.selected_quest_id:
            self._draw_quest_detail(screen, mp, mid + 20)

    def _draw_quest_detail(self, screen, mp, start_x):
        """Draw detailed view of the selected quest."""
        quest = self.world.quests.get(self.selected_quest_id)
        if not quest:
            return
        y = 70
        panel_w = SCREEN_WIDTH - start_x - 30

        # Name (editable)
        hdr = fonts.header.render(quest.name, True, COLORS["accent"])
        screen.blit(hdr, (start_x, y))
        name_rect = pygame.Rect(start_x, y, hdr.get_width() + 50, 28)
        if name_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_name"
            self.input_text = quest.name
            self.modal = ("edit_field", "quest_name")
        y += 32

        # Status selector
        sl = fonts.small_bold.render("Status:", True, COLORS["text_dim"])
        screen.blit(sl, (start_x, y))
        sx = start_x + 60
        status_cols = {
            "active": COLORS["success"], "completed": COLORS["text_dim"],
            "failed": COLORS["danger"], "not_started": COLORS["warning"],
            "on_hold": COLORS["cold"],
        }
        for st in QUEST_STATUSES:
            is_act = quest.status == st
            label = st.replace("_", " ").title()
            sw = fonts.tiny.size(label)[0] + 12
            sr = pygame.Rect(sx, y, sw, 20)
            scol = status_cols.get(st, COLORS["panel"])
            bg = scol if is_act else COLORS["panel"]
            if sr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    quest.status = st
                    if st == "completed":
                        from data.campaign import _timestamp
                        quest.completed_date = _timestamp()
            pygame.draw.rect(screen, bg, sr, border_radius=8)
            stt = fonts.tiny.render(label, True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(stt, (sx + 6, y + 3))
            sx += sw + 4
        y += 26

        # Priority selector
        pl = fonts.small_bold.render("Priority:", True, COLORS["text_dim"])
        screen.blit(pl, (start_x, y))
        px = start_x + 65
        priority_cols = {
            "urgent": COLORS["danger"], "high": COLORS["warning"],
            "normal": COLORS["text_dim"], "low": COLORS["cold"],
        }
        for pr in QUEST_PRIORITIES:
            is_act = quest.priority == pr
            pw = fonts.tiny.size(pr.title())[0] + 12
            prr = pygame.Rect(px, y, pw, 20)
            pcol = priority_cols.get(pr, COLORS["panel"])
            bg = pcol if is_act else COLORS["panel"]
            if prr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    quest.priority = pr
            pygame.draw.rect(screen, bg, prr, border_radius=8)
            ptt = fonts.tiny.render(pr.title(), True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(ptt, (px + 6, y + 3))
            px += pw + 4
        y += 26

        # Type selector
        tl = fonts.small_bold.render("Type:", True, COLORS["text_dim"])
        screen.blit(tl, (start_x, y))
        tx = start_x + 50
        for qt in QUEST_TYPES:
            is_act = quest.quest_type == qt
            tw = fonts.tiny.size(qt.title())[0] + 12
            tr = pygame.Rect(tx, y, tw, 20)
            bg = COLORS["accent_dim"] if is_act else COLORS["panel"]
            if tr.collidepoint(mp):
                bg = COLORS["hover"]
                if pygame.mouse.get_pressed()[0]:
                    quest.quest_type = qt
            pygame.draw.rect(screen, bg, tr, border_radius=8)
            ttt = fonts.tiny.render(qt.title(), True, COLORS["text_bright"] if is_act else COLORS["text_dim"])
            screen.blit(ttt, (tx + 6, y + 3))
            tx += tw + 4
        y += 30

        # Editable text fields
        fields = [
            ("Description", quest.description, "quest_description"),
            ("Level Range", quest.level_range, "quest_level_range"),
        ]
        for label, value, field_key in fields:
            fl = fonts.small_bold.render(f"{label}:", True, COLORS["text_dim"])
            screen.blit(fl, (start_x, y))
            field_rect = pygame.Rect(start_x + 100, y - 2, panel_w - 100, 22)
            pygame.draw.rect(screen, COLORS["input_bg"], field_rect, border_radius=3)
            text = value or f"(set {label.lower()})"
            col = COLORS["text_main"] if value else COLORS["text_muted"]
            ft = fonts.small.render(text[:80], True, col)
            screen.blit(ft, (field_rect.x + 4, y))
            if field_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                self.input_active = field_key
                self.input_text = value
                self.modal = ("edit_field", field_key)
            y += 24

        # Quest giver NPC
        y += 4
        gl = fonts.small_bold.render("Quest Giver:", True, COLORS["text_dim"])
        screen.blit(gl, (start_x, y))
        giver = self.world.npcs.get(quest.giver_npc_id)
        giver_name = giver.name if giver else "(none)"
        gt = fonts.small.render(giver_name, True, COLORS["accent"] if giver else COLORS["text_muted"])
        screen.blit(gt, (start_x + 100, y))
        # NPC picker - cycle through NPCs on click
        pick_btn = pygame.Rect(start_x + 100 + gt.get_width() + 10, y - 2, 50, 20)
        is_pick_hover = pick_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if is_pick_hover else COLORS["panel"], pick_btn, border_radius=3)
        pygame.draw.rect(screen, COLORS["border"], pick_btn, 1, border_radius=3)
        pbt = fonts.tiny.render("Pick", True, COLORS["accent"])
        screen.blit(pbt, (pick_btn.x + 12, pick_btn.y + 3))
        if is_pick_hover and pygame.mouse.get_pressed()[0]:
            npc_list = list(self.world.npcs.keys())
            if npc_list:
                cur_idx = npc_list.index(quest.giver_npc_id) if quest.giver_npc_id in npc_list else -1
                quest.giver_npc_id = npc_list[(cur_idx + 1) % len(npc_list)]
        # Clear
        if quest.giver_npc_id:
            clr = pygame.Rect(pick_btn.right + 5, y - 2, 20, 20)
            is_clr = clr.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["danger_hover"] if is_clr else COLORS["panel"], clr, border_radius=3)
            xt = fonts.tiny.render("X", True, COLORS["danger"])
            screen.blit(xt, (clr.x + 5, clr.y + 3))
            if is_clr and pygame.mouse.get_pressed()[0]:
                quest.giver_npc_id = ""
        y += 24

        # Objectives
        y += 4
        ol = fonts.small_bold.render("Objectives:", True, COLORS["text_dim"])
        screen.blit(ol, (start_x, y))
        y += 20
        for i, obj in enumerate(quest.objectives):
            if y > SCREEN_HEIGHT - 160:
                break
            obj_rect = pygame.Rect(start_x, y, panel_w, 22)
            # Checkbox
            cb = pygame.Rect(start_x, y + 2, 16, 16)
            pygame.draw.rect(screen, COLORS["success"] if obj.completed else COLORS["panel"], cb, border_radius=3)
            pygame.draw.rect(screen, COLORS["border"], cb, 1, border_radius=3)
            if obj.completed:
                ct = fonts.tiny.render("v", True, COLORS["text_bright"])
                screen.blit(ct, (cb.x + 3, cb.y + 1))
            if cb.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                obj.completed = not obj.completed
            # Description
            col = COLORS["text_dim"] if obj.completed else COLORS["text_bright"]
            ot = fonts.small.render(obj.description[:60], True, col)
            screen.blit(ot, (start_x + 22, y + 2))
            # Delete button
            del_btn = pygame.Rect(start_x + panel_w - 20, y + 2, 16, 16)
            is_del = del_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["danger_hover"] if is_del else COLORS["panel"], del_btn, border_radius=3)
            dxt = fonts.tiny.render("X", True, COLORS["danger"])
            screen.blit(dxt, (del_btn.x + 3, del_btn.y + 1))
            if is_del and pygame.mouse.get_pressed()[0]:
                quest.objectives.pop(i)
            y += 24

        # Add objective button
        add_obj_btn = pygame.Rect(start_x, y, 120, 22)
        is_add_hover = add_obj_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if is_add_hover else COLORS["panel"], add_obj_btn, border_radius=3)
        pygame.draw.rect(screen, COLORS["border"], add_obj_btn, 1, border_radius=3)
        aot = fonts.tiny.render("+ Objective", True, COLORS["accent"])
        screen.blit(aot, (add_obj_btn.x + 8, add_obj_btn.y + 4))
        if is_add_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_add_objective"
            self.input_text = ""
            self.modal = ("edit_field", "quest_add_objective")
        y += 28

        # Rewards section
        rl = fonts.small_bold.render("Rewards:", True, COLORS["text_dim"])
        screen.blit(rl, (start_x, y))
        y += 20

        # XP
        xpl = fonts.small.render(f"XP: {quest.reward_xp}", True, COLORS["text_bright"])
        screen.blit(xpl, (start_x, y))
        xp_rect = pygame.Rect(start_x, y - 2, xpl.get_width() + 20, 20)
        if xp_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_reward_xp"
            self.input_text = str(quest.reward_xp)
            self.modal = ("edit_field", "quest_reward_xp")

        # Gold
        gl2 = fonts.small.render(f"Gold: {quest.reward_gold}", True, COLORS["legendary"])
        screen.blit(gl2, (start_x + 120, y))
        gold_rect = pygame.Rect(start_x + 120, y - 2, gl2.get_width() + 20, 20)
        if gold_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_reward_gold"
            self.input_text = str(quest.reward_gold)
            self.modal = ("edit_field", "quest_reward_gold")
        y += 22

        # Reward items
        for i, item in enumerate(quest.reward_items):
            if y > SCREEN_HEIGHT - 140:
                break
            it = fonts.small.render(f"  - {item}", True, COLORS["text_main"])
            screen.blit(it, (start_x, y))
            # Delete item
            del_btn = pygame.Rect(start_x + panel_w - 20, y, 16, 16)
            is_del = del_btn.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["danger_hover"] if is_del else COLORS["panel"], del_btn, border_radius=3)
            dxt = fonts.tiny.render("X", True, COLORS["danger"])
            screen.blit(dxt, (del_btn.x + 3, del_btn.y + 1))
            if is_del and pygame.mouse.get_pressed()[0]:
                quest.reward_items.pop(i)
            y += 20

        # Add reward item
        add_ri_btn = pygame.Rect(start_x, y, 120, 22)
        is_ri_hover = add_ri_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if is_ri_hover else COLORS["panel"], add_ri_btn, border_radius=3)
        pygame.draw.rect(screen, COLORS["border"], add_ri_btn, 1, border_radius=3)
        rit = fonts.tiny.render("+ Item", True, COLORS["accent"])
        screen.blit(rit, (add_ri_btn.x + 8, add_ri_btn.y + 4))
        if is_ri_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_add_reward_item"
            self.input_text = ""
            self.modal = ("edit_field", "quest_add_reward_item")
        y += 28

        # Notes
        nl = fonts.small_bold.render("Notes:", True, COLORS["text_dim"])
        screen.blit(nl, (start_x, y))
        notes_rect = pygame.Rect(start_x + 55, y - 2, panel_w - 55, 22)
        pygame.draw.rect(screen, COLORS["input_bg"], notes_rect, border_radius=3)
        notes_text = quest.notes or "(add notes)"
        ncol = COLORS["text_main"] if quest.notes else COLORS["text_muted"]
        ntt = fonts.small.render(notes_text[:80], True, ncol)
        screen.blit(ntt, (notes_rect.x + 4, y))
        if notes_rect.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_notes"
            self.input_text = quest.notes
            self.modal = ("edit_field", "quest_notes")
        y += 26

        # Tags
        tl2 = fonts.small_bold.render("Tags:", True, COLORS["text_dim"])
        screen.blit(tl2, (start_x, y))
        tag_x = start_x + 45
        for i, tag in enumerate(quest.tags):
            tw = fonts.tiny.size(tag)[0] + 18
            tr = pygame.Rect(tag_x, y, tw, 20)
            is_tag_hover = tr.collidepoint(mp)
            pygame.draw.rect(screen, COLORS["hover"] if is_tag_hover else COLORS["accent_dim"], tr, border_radius=8)
            tgt = fonts.tiny.render(tag, True, COLORS["text_bright"])
            screen.blit(tgt, (tag_x + 5, y + 3))
            # X to remove
            xr = pygame.Rect(tag_x + tw - 14, y + 2, 12, 16)
            xt2 = fonts.tiny.render("x", True, COLORS["danger"])
            screen.blit(xt2, (xr.x + 2, xr.y))
            if xr.collidepoint(mp) and pygame.mouse.get_pressed()[0]:
                quest.tags.pop(i)
            tag_x += tw + 4
        # Add tag
        add_tag = pygame.Rect(tag_x, y, 50, 20)
        is_at_hover = add_tag.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["hover"] if is_at_hover else COLORS["panel"], add_tag, border_radius=8)
        pygame.draw.rect(screen, COLORS["border"], add_tag, 1, border_radius=8)
        att = fonts.tiny.render("+ tag", True, COLORS["accent"])
        screen.blit(att, (add_tag.x + 8, add_tag.y + 3))
        if is_at_hover and pygame.mouse.get_pressed()[0]:
            self.input_active = "quest_add_tag"
            self.input_text = ""
            self.modal = ("edit_field", "quest_add_tag")
        y += 28

        # Delete quest button
        del_q_btn = pygame.Rect(start_x, y + 10, 120, 28)
        is_dq_hover = del_q_btn.collidepoint(mp)
        pygame.draw.rect(screen, COLORS["danger_hover"] if is_dq_hover else COLORS["danger"], del_q_btn, border_radius=5)
        dqt = fonts.small_bold.render("Delete Quest", True, COLORS["text_bright"])
        screen.blit(dqt, (del_q_btn.x + 8, del_q_btn.y + 5))
        if is_dq_hover and pygame.mouse.get_pressed()[0]:
            delete_quest(self.world, self.selected_quest_id)
            self.selected_quest_id = ""

    def _handle_quests_click(self, mp):
        """Handle clicks in quests viewer."""
        mx, my = mp
        # Quest search box
        search_rect = pygame.Rect(20, 68, 300, 28)
        if search_rect.collidepoint(mp):
            self.quest_search_active = True
            return
        self.quest_search_active = False

        # Quest list
        y = 105 + self.scroll_y
        quests = list(self.world.quests.values())
        if self.quest_search:
            quests = search_quests(self.world, self.quest_search)
        if self.quest_filter != "all":
            quests = [q for q in quests if q.status == self.quest_filter]
        for quest in quests:
            rect = pygame.Rect(20, y, SCREEN_WIDTH // 2 - 40, 50)
            if rect.collidepoint(mp):
                self.selected_quest_id = quest.id
                return
            y += 56
