import pygame
import math
import os
import json
import copy
import random
import re
import logging
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_TYPE_COLORS, CREATURE_ICONS, SIZE_RADIUS
from ui.components import Button, Panel, fonts, hp_bar, TabBar, Badge, Divider, draw_gradient_rect, Tooltip
from engine.battle import BattleSystem
from engine.ai import TurnPlan, ActionStep
from engine.terrain import TerrainObject, TERRAIN_TYPES
from engine.dice import roll_d20, roll_dice, roll_attack, roll_dice_critical
from data.library import library
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores, Action, SpellInfo
from data.heroes import hero_list
from data.conditions import CONDITIONS
from engine.battle_report import generate_battle_report, format_report_text, save_report, save_report_text
from engine.win_probability import assess_encounter_danger
from data.hero_import import import_heroes_from_file, export_heroes_to_file
from data.campaign import Campaign, load_campaign, list_campaigns, CAMPAIGNS_DIR, _timestamp
from states.game_state_base import GameState, ScenarioModal, NotesModal, EffectModal, SAVES_DIR
from states.battle_constants import PANEL_W, TOP_BAR_H, GRID_W, TABS, DAMAGE_TYPE_COLORS, CONDITION_BADGES
from states.battle_renderer import BattleRendererMixin
from states.battle_events import BattleEventsMixin

class FloatingText:
    def __init__(self, gx, gy, text, color):
        self.gx = gx
        self.gy = gy
        self.text = str(text)
        self.color = color
        self.life = 90  # frames (1.5 sec)
        self.anim_offset = 0.0

    def update(self):
        self.anim_offset -= 0.015  # float up
        self.life -= 1

    def draw(self, screen, get_screen_pos_func, grid_size):
        if self.life > 0:
            sx, sy = get_screen_pos_func(self.gx, self.gy)
            cx = sx + grid_size // 2
            cy = sy + grid_size // 2 + int(self.anim_offset * grid_size)
            
            # Outline for readability
            txt = fonts.header.render(self.text, True, self.color)
            outline = fonts.header.render(self.text, True, (0,0,0))
            
            alpha = 255
            if self.life < 20:
                alpha = int(255 * (self.life / 20))
            
            txt.set_alpha(alpha)
            outline.set_alpha(alpha)
            
            screen.blit(outline, (cx - txt.get_width()//2 + 2, cy + 2))
            screen.blit(txt, (cx - txt.get_width()//2, cy))



class ImpactFlash:
    """Expanding, fading ring at a grid position — color-coded by damage type."""
    def __init__(self, gx, gy, damage_type="slashing", is_heal=False):
        self.gx = gx
        self.gy = gy
        if is_heal:
            self.color = (80, 255, 140)
        else:
            self.color = DAMAGE_TYPE_COLORS.get(damage_type, (220, 220, 220))
        self.life = 24  # frames (~0.4 sec at 60 fps)
        self.max_life = 24
        self.is_heal = is_heal

    def update(self):
        self.life -= 1

    def draw(self, screen, get_screen_pos_func, grid_size):
        if self.life <= 0:
            return
        t = 1.0 - (self.life / self.max_life)  # 0→1 over lifetime
        sx, sy = get_screen_pos_func(self.gx, self.gy)
        cx = sx + grid_size // 2
        cy = sy + grid_size // 2

        max_r = int(grid_size * 0.6)
        r = int(max_r * (0.3 + 0.7 * t))
        alpha = int(200 * (1.0 - t))

        surf = pygame.Surface((max_r * 2 + 4, max_r * 2 + 4), pygame.SRCALPHA)
        center = (max_r + 2, max_r + 2)
        # Filled glow
        glow_a = max(0, alpha // 3)
        pygame.draw.circle(surf, (*self.color, glow_a), center, r)
        # Bright ring
        ring_w = max(2, int(3 * (1.0 - t)))
        pygame.draw.circle(surf, (*self.color, alpha), center, r, ring_w)

        screen.blit(surf, (cx - max_r - 2, cy - max_r - 2))


class WeatherParticle:
    """A single persistent weather particle."""
    __slots__ = ("x", "y", "vx", "vy", "life", "size", "color")
    def __init__(self, x, y, vx, vy, life, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.size = size
        self.color = color


class BattleState(BattleRendererMixin, BattleEventsMixin, GameState):
    def __init__(self, manager, entities=None):
        super().__init__(manager)
        self.logs = []
        self.battle = BattleSystem(self._log, initial_entities=entities)
        self.selected_entity: Entity | None = None
        self.dragging: Entity | None = None
        self.drag_start = (0.0, 0.0)
        self.token_cache = {}
        self.active_tab = 0
        self.panel_scroll = 0
        self.camera_x = 0
        self.camera_y = 0
        self.active_tooltip = None  # For drawing tooltips on top of everything
        self.pending_move = None    # (entity, x, y) for delayed movement (OA)
        self.undo_stack = []        # Stack of full state dicts
        self.redo_stack = []        # Stack of undone states for redo
        self.ts_last_update = 0     # Timestamp of last TaleSpire update
        self.auto_battle = False    # Auto-play toggle
        self.auto_battle_paused = False  # Pause without fully stopping
        self.auto_timer = 0         # Timer for auto-play ticks
        self.auto_battle_speed = 10 # Frames per tick (lower = faster). Options: 3, 6, 10, 20, 40
        self.auto_battle_mode = "full"  # "full" = AI plays everyone, "npc" = AI plays NPCs only
        self.log_filter_mode = "all" # "all", "selected", "damage", "healing", "conditions", "rolls"

        # Direct HP input mode (type "-17" Enter to apply damage)
        self.hp_input_active = False
        self.hp_input_text = ""

        # Collapsible panel sections
        self.collapsed_sections = set()  # e.g. {"ABILITIES", "SAVES", "FEATURES"}

        # Autosave tracking
        self.autosave_turn_counter = 0

        # Visual FX
        self.floating_texts = []
        self.impact_flashes = []
        self.weather_particles = []
        self.turn_banner_text = ""
        self.turn_banner_timer = 0

        # AI turn state
        self.pending_plan: TurnPlan | None = None
        self.pending_step_idx: int = 0
        self.current_step_outcomes = {} # target -> "hit"/"miss"/"save"/"fail"
        self.current_step_rolls = {}    # target -> "15+5=20" (for saves)
        self._pre_plan_state = None     # Saved entity state before AI planning

        # Player action panel state
        self.player_action_mode = False
        self.player_action_type = None   # "attack","spell","move","item","other"
        self.player_action_target = None

        # Reaction popup
        self.reaction_pending = []  # list of (reactor, mover)
        self.reaction_type = None   # "oa" or "counterspell"
        self.reaction_context = None # dict with extra info

        # Aura / Turn Start triggers
        self.aura_triggers = []
        self.current_aura_trigger = None

        # Context menu
        self.ctx_open = False
        self.ctx_pos = (0, 0)
        self.ctx_rects = []   # [(rect, callback, text)]

        # Terrain mode
        self.terrain_mode = False
        self.terrain_selected_type = "wall"
        self.terrain_palette_open = False
        self.terrain_palette_scroll = 0
        self.drawing_button = None  # None, 1 (left/paint), or 3 (right/erase)
        # Terrain tool mode: "paint", "move", "rect", "elev"
        self.terrain_tool = "paint"
        # Move tool state
        self.terrain_drag_obj = None       # TerrainObject being moved
        self.terrain_drag_offset = (0, 0)  # Grid offset from click to obj origin
        # Rectangle tool state
        self.terrain_rect_start = None     # (gx, gy) start corner
        self.terrain_rect_preview = []     # list of (gx, gy) cells to preview
        # Elevation edit state
        self.terrain_elev_target = None    # TerrainObject being edited
        # Copy/paste
        self.terrain_clipboard = []        # list of dicts {terrain_type, dx, dy, elevation, ...}
        self.terrain_select_start = None   # (gx, gy) selection start for copy
        self.terrain_select_end = None     # (gx, gy) selection end
        self.terrain_paste_preview = False # True when pasting
        # Quick-access favorites (terrain types)
        self.terrain_favorites = ["wall", "rock", "tree", "door", "platform_10",
                                  "difficult", "water", "cover", "pillar", "fire"]

        # Help Overlay
        self.help_overlay_open = False

        # Encounter Balance Indicator
        self.encounter_danger_cache = None  # Cached danger assessment dict
        self.encounter_danger_timer = 0     # Recalculate every N frames

        # Roll Result Modal
        self.roll_modal_open = False
        self.roll_modal_title = ""
        self.roll_modal_expression = ""
        self.roll_modal_total = 0
        self.roll_modal_nat = 0

        # Dynamic UI click zones (rect, callback) - populated during draw
        self.ui_click_zones = []
        self.ui_right_click_zones = []

        # Damage Application Modal
        self.dmg_modal_open = False
        self.dmg_target: Entity | None = None
        self.dmg_value_str = ""
        self.dmg_type = "slashing"

        # Condition reminder (set when player turn starts with active conditions)
        self.condition_reminder: Entity | None = None

        # Scenario Modal
        self.scenario_modal = None
        self.notes_modal = None
        self.effect_modal = None

        # Battle Report / Win Probability / DM Advisor state
        self.battle_report = None              # Generated report dict when combat ends
        self.battle_report_text = ""           # Formatted text of report
        self.report_modal_open = False
        self.report_scroll = 0
        self.win_prob_cache = None             # Cached win probability result
        self.pending_saves = []                # For manual end-of-turn saves
        self.save_modal_open = False
        self.dm_suggestion_cache = None        # Cached DM advisor suggestion
        self.dm_rating_cache = None            # Cached player action rating
        self.show_advisor_panel = False        # Toggle for DM advisor panel

        # Manual Spell Targeting
        self.spell_targeting: SpellInfo | None = None
        self.spell_caster: Entity | None = None

        # Manual Action Targeting
        self.action_targeting: Action | None = None
        self.action_caster: Entity | None = None

        self._build_buttons()

        if not self.battle.combat_started:
            self._log("=== DEPLOYMENT PHASE ===")
            self._log("Drag characters to position them. Click START COMBAT when ready.")

    def update_external_positions(self, minis_data):
        """Updates entity positions based on external JSON data (e.g. from TaleSpire)."""
        self.ts_last_update = pygame.time.get_ticks()
        
        for mini in minis_data:
            name = mini.get("name", "").strip()
            raw_x = float(mini.get("x", 0))
            raw_z = float(mini.get("z", 0)) # TaleSpire uses Z for depth/ground plane

            # Requirement: Convert to feet by multiplying by 5
            feet_x = raw_x * 5
            feet_y = raw_z * 5

            # Engine uses grid units (1 unit = 5 ft). Convert feet back to grid units.
            gx = feet_x / 5.0
            gy = feet_y / 5.0

            # Find and update the entity
            # We use 'base_name' or 'name' matching.
            for ent in self.battle.entities:
                if ent.name.lower() == name.lower():
                    ent.grid_x = gx
                    ent.grid_y = gy

    # ------------------------------------------------------------------ #
    # Build UI buttons                                                     #
    # ------------------------------------------------------------------ #

    def _build_buttons(self):
        bx = SCREEN_WIDTH - PANEL_W
        # Bottom bar
        self.btn_next   = Button(bx+20,  SCREEN_HEIGHT-65, 145, 50, "NEXT TURN >>", self._do_next_turn,      color=COLORS["success"])
        self.btn_ai     = Button(bx+175, SCREEN_HEIGHT-65, 145, 50, "AI AUTO-PLAY", self._do_ai_turn,        color=COLORS["accent"])
        self.btn_start  = Button(bx+20,  SCREEN_HEIGHT-65, 300, 50, "START COMBAT", self._do_start_combat,   color=COLORS["success"])
        self.btn_menu   = Button(10, 10, 80, 30, "Menu",          lambda: self.manager.change_state("MENU"), color=COLORS["panel"])
        self.btn_log_pl = Button(bx+330, SCREEN_HEIGHT-65, 165, 50, "LOG PLAYER ACTION", self._open_player_action_panel, color=COLORS["neutral"])
        # Grid area bottom-left utilities
        self.btn_save    = Button(10,  SCREEN_HEIGHT-65, 72, 35, "SAVE",    self._open_save_modal,      color=COLORS["panel"])
        self.btn_load    = Button(87,  SCREEN_HEIGHT-65, 72, 35, "LOAD",    self._open_load_modal,      color=COLORS["panel"])
        self.btn_terrain = Button(164, SCREEN_HEIGHT-65, 100, 35, "TERRAIN", self._toggle_terrain_mode, color=COLORS["panel"])
        self.btn_save_map = Button(696, SCREEN_HEIGHT-65, 82, 35, "MAP S/L", self._toggle_map_save_menu, color=COLORS["panel"])
        self.map_save_menu_open = False
        self.btn_weather = Button(270, SCREEN_HEIGHT-65, 100, 35, "WEATHER", self._cycle_weather,       color=COLORS["panel"])
        self.btn_undo    = Button(376, SCREEN_HEIGHT-65, 72, 35, "UNDO",      self._undo_last_action,     color=COLORS["warning"])
        self.btn_auto    = Button(454, SCREEN_HEIGHT-65, 72, 35, "AUTO",      self._toggle_auto_battle,   color=COLORS["panel"])
        self.btn_auto_mode = Button(530, SCREEN_HEIGHT-65, 50, 35, "FULL",    self._toggle_auto_mode,     color=COLORS["accent"])
        self.btn_pause   = Button(454, SCREEN_HEIGHT-28, 72, 24, "PAUSE",     self._toggle_pause_auto,    color=COLORS["panel"])
        self.btn_speed_down = Button(530, SCREEN_HEIGHT-28, 24, 24, "-",       self._auto_speed_down,      color=COLORS["panel"])
        self.btn_speed_lbl  = Button(554, SCREEN_HEIGHT-28, 36, 24, "1x",      lambda: None,               color=COLORS["text_dim"])
        self.btn_speed_up   = Button(590, SCREEN_HEIGHT-28, 24, 24, "+",       self._auto_speed_up,        color=COLORS["panel"])
        self.btn_advisor = Button(532, SCREEN_HEIGHT-65, 80, 35, "ADVISOR",  self._toggle_advisor_panel, color=COLORS["spell"])
        self.btn_maps    = Button(618, SCREEN_HEIGHT-65, 72, 35, "MAPS",     self._toggle_map_browser,   color=COLORS["panel"])
        self.map_browser_open = False
        self.btn_add_entity = Button(784, SCREEN_HEIGHT-65, 72, 35, "ADD", self._toggle_add_entity_modal, color=COLORS["spell"])
        self.add_entity_open = False
        self.add_entity_search = ""
        self.add_entity_scroll = 0
        self.add_entity_is_player = False  # Toggle: add as player or enemy

        # HP quick buttons
        vals = [-10, -5, -1, 1, 5, 10]
        self.hp_btns = []
        for v in vals:
            c = COLORS["danger"] if v < 0 else COLORS["success"]
            self.hp_btns.append(Button(0, 0, 44, 26, f"{v:+d}", lambda val=v: self._modify_hp(val), color=c))

        # Initiative quick buttons
        self.init_btns = [
            Button(0, 0, 38, 24, "+1", lambda: self._modify_init(1),  color=COLORS["success"]),
            Button(0, 0, 38, 24, "-1", lambda: self._modify_init(-1), color=COLORS["danger"]),
        ]

        # Confirm / deny for AI actions
        self.btn_confirm = Button(SCREEN_WIDTH//2-130, SCREEN_HEIGHT//2+120, 120, 48,
                                  "CONFIRM", lambda: self._confirm_step(), color=COLORS["success"])
        self.btn_deny    = Button(SCREEN_WIDTH//2+10,  SCREEN_HEIGHT//2+120, 120, 48,
                                  "DENY",    lambda: self._skip_step(),   color=COLORS["danger"])
        self.btn_approve_all = Button(SCREEN_WIDTH//2-65, SCREEN_HEIGHT//2+180, 130, 38,
                                      "APPROVE ALL", lambda: self._approve_all(), color=COLORS["accent"])
        self.btn_cancel_ai  = Button(SCREEN_WIDTH//2-65, SCREEN_HEIGHT//2+225, 130, 38,
                                      "DO MANUALLY", lambda: self._cancel_ai_plan(), color=COLORS["warning"])

        # Player action buttons
        self.player_action_btns = [
            Button(0, 0, 120, 35, "Attack",   lambda: self._pl_set_type("attack"),  color=COLORS["danger"]),
            Button(0, 0, 120, 35, "Cast Spell",lambda: self._pl_set_type("spell"),  color=COLORS["spell"]),
            Button(0, 0, 120, 35, "Move",      lambda: self._pl_set_type("move"),   color=COLORS["success"]),
            Button(0, 0, 120, 35, "Use Item",  lambda: self._pl_set_type("item"),   color=COLORS["warning"]),
            Button(0, 0, 120, 35, "Dash",      lambda: self._pl_set_type("dash"),   color=COLORS["accent"]),
            Button(0, 0, 120, 35, "Dodge",     lambda: self._pl_set_type("dodge"),  color=COLORS["accent"]),
            Button(0, 0, 120, 35, "Disengage", lambda: self._pl_set_type("disengage"), color=COLORS["accent"]),
            Button(0, 0, 120, 35, "Help",      lambda: self._pl_set_type("help"),   color=COLORS["accent"]),
            Button(0, 0, 120, 35, "Done",      lambda: self._close_player_panel(),  color=COLORS["text_dim"]),
        ]

    def _toggle_auto_battle(self):
        self.auto_battle = not self.auto_battle
        self.auto_battle_paused = False
        if self.auto_battle:
            self.btn_auto.color = COLORS["success"]
            self.btn_auto.text = "STOP"
            self.btn_pause.color = COLORS["warning"]
            self.btn_pause.text = "PAUSE"
            mode_label = "FULL (Players+NPCs)" if self.auto_battle_mode == "full" else "NPC Only"
            self._log(f"[SYSTEM] Auto-Battle STARTED – Mode: {mode_label}")
        else:
            self.btn_auto.color = COLORS["panel"]
            self.btn_auto.text = "AUTO"
            self.btn_pause.color = COLORS["panel"]
            self.btn_pause.text = "PAUSE"
            self._log("[SYSTEM] Auto-Battle STOPPED.")

    def _toggle_auto_mode(self):
        """Toggle between 'full' (AI plays everyone) and 'npc' (AI plays NPCs only)."""
        if self.auto_battle_mode == "full":
            self.auto_battle_mode = "npc"
            self.btn_auto_mode.text = "NPC"
            self.btn_auto_mode.color = COLORS["panel"]
            self._log("[SYSTEM] Auto mode: NPC only (players manual).")
        else:
            self.auto_battle_mode = "full"
            self.btn_auto_mode.text = "FULL"
            self.btn_auto_mode.color = COLORS["accent"]
            self._log("[SYSTEM] Auto mode: FULL (AI plays everyone).")

    def _toggle_pause_auto(self):
        if not self.auto_battle:
            return
        self.auto_battle_paused = not self.auto_battle_paused
        if self.auto_battle_paused:
            self.btn_pause.color = COLORS["accent"]
            self.btn_pause.text = "RESUME"
            self._log("[SYSTEM] Auto-Battle PAUSED.")
        else:
            self.btn_pause.color = COLORS["warning"]
            self.btn_pause.text = "PAUSE"
            self._log("[SYSTEM] Auto-Battle RESUMED.")

    def _auto_speed_up(self):
        speeds = [40, 20, 10, 6, 3]
        idx = speeds.index(self.auto_battle_speed) if self.auto_battle_speed in speeds else 2
        if idx < len(speeds) - 1:
            self.auto_battle_speed = speeds[idx + 1]
        labels = {3: "5x", 6: "3x", 10: "1x", 20: "0.5x", 40: "0.25x"}
        self.btn_speed_lbl.text = labels.get(self.auto_battle_speed, "1x")
        self._log(f"[SYSTEM] Auto speed: {labels.get(self.auto_battle_speed, '?')}")

    def _auto_speed_down(self):
        speeds = [40, 20, 10, 6, 3]
        idx = speeds.index(self.auto_battle_speed) if self.auto_battle_speed in speeds else 2
        if idx > 0:
            self.auto_battle_speed = speeds[idx - 1]
        labels = {3: "5x", 6: "3x", 10: "1x", 20: "0.5x", 40: "0.25x"}
        self.btn_speed_lbl.text = labels.get(self.auto_battle_speed, "1x")
        self._log(f"[SYSTEM] Auto speed: {labels.get(self.auto_battle_speed, '?')}")

    def _process_auto_battle(self):
        """Handle one tick of auto-battle logic."""
        # 1. Handle Aura Triggers (Auto-roll saves)
        if self.current_aura_trigger:
            feat = self.current_aura_trigger["feature"]
            target = self.current_aura_trigger["target"]
            bonus = target.get_save_bonus(feat.save_ability)
            roll = random.randint(1, 20) + bonus
            success = roll >= feat.save_dc
            self._resolve_aura(success)
            return

        # 2. Handle Reactions (smart AI decisions)
        if self.reaction_pending:
            if self.reaction_type == "counterspell":
                reactor = self.reaction_pending[0]
                ctx = self.reaction_context or {}
                spell_level = ctx.get("level", 1)
                should_counter = spell_level >= 3 or reactor.has_spell_slot(4)
                self._resolve_reaction(should_counter)
            else:
                self._resolve_reaction(True)
            return

        # 3. Handle Pending Saves modal (auto-roll in auto battle)
        if self.save_modal_open and self.pending_saves:
            self._auto_resolve_pending_saves()
            return

        # 4. Handle Pending Plan (Execute steps)
        if self.pending_plan:
            self._confirm_step()
            return

        # 5. Decide Next Action
        try:
            curr = self.battle.get_current_entity()
        except ValueError:
            self.auto_battle = False
            return

        # Check if this entity should be AI-controlled
        if curr.is_player and self.auto_battle_mode == "npc":
            # NPC-only mode: skip player turns, let DM handle
            return

        # If current entity has done nothing yet, try to generate AI plan
        if not curr.action_used and not curr.is_incapacitated():
            self._do_ai_turn(force_auto=True)

            if not self.pending_plan:
                self._do_next_turn()
        else:
            self._do_next_turn()

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #

    def update(self):
        # Camera movement
        keys = pygame.key.get_pressed()
        speed = 15  # pixels per frame
        if keys[pygame.K_w]: self.camera_y -= speed
        if keys[pygame.K_s]: self.camera_y += speed
        if keys[pygame.K_a]: self.camera_x -= speed
        if keys[pygame.K_d]: self.camera_x += speed

        # Weather particle animation
        self._update_weather_fx()

        self.battle.validate_grapples()

        # Update FX
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]
        for fx in self.impact_flashes:
            fx.update()
        self.impact_flashes = [fx for fx in self.impact_flashes if fx.life > 0]
        if self.turn_banner_timer > 0:
            self.turn_banner_timer -= 1
            
        # Auto Battle Tick
        if self.auto_battle and not self.auto_battle_paused and self.battle.combat_started:
            self.auto_timer += 1
            if self.auto_timer > self.auto_battle_speed:
                self.auto_timer = 0
                self._process_auto_battle()

    def _update_weather_fx(self):
        w = self.battle.weather
        if w == "Clear":
            self.weather_particles.clear()
            return

        # Spawn new particles
        spawn_rate = 6 if w == "Rain" else 3  # particles per frame
        for _ in range(spawn_rate):
            x = random.randint(0, GRID_W + 40)
            if w == "Rain":
                y = TOP_BAR_H - 10
                vx = -1.5
                vy = random.uniform(8, 14)
                life = random.randint(40, 70)
                size = 1
                color = (150, 160, 255, 140)
            elif w == "Ash":
                y = random.choice([TOP_BAR_H - 10, random.randint(TOP_BAR_H, SCREEN_HEIGHT)])
                vx = random.uniform(-0.5, 0.5)
                vy = random.uniform(0.8, 2.5)
                life = random.randint(80, 160)
                size = random.randint(1, 3)
                color = (180, 80, 60, 120)
            else:
                continue
            self.weather_particles.append(
                WeatherParticle(x, y, vx, vy, life, size, color))

        # Update existing
        for p in self.weather_particles:
            p.x += p.vx
            p.y += p.vy
            p.life -= 1
        self.weather_particles = [p for p in self.weather_particles
                                  if p.life > 0 and p.y < SCREEN_HEIGHT + 20]

    def _screen_to_grid(self, mx, my):
        world_x = mx + self.camera_x
        world_y = (my - TOP_BAR_H) + self.camera_y
        return world_x / self.battle.grid_size, world_y / self.battle.grid_size

    def _grid_to_screen(self, gx, gy):
        gsz = self.battle.grid_size
        sx = gx * gsz - self.camera_x
        sy = gy * gsz - self.camera_y + TOP_BAR_H
        return int(sx), int(sy)

    def _center_camera_on(self, entity):
        gsz = self.battle.grid_size
        # Center of entity in world pixels
        world_cx = entity.grid_x * gsz + gsz / 2
        world_cy = entity.grid_y * gsz + gsz / 2
        
        # Viewport dimensions
        view_w = GRID_W
        view_h = SCREEN_HEIGHT - TOP_BAR_H
        
        self.camera_x = world_cx - view_w / 2
        self.camera_y = world_cy - view_h / 2

    def _log(self, msg):
        logging.info(f"[BATTLE] {msg}")
        self.logs.append(msg)
        if len(self.logs) > 200:
            self.logs.pop(0)

    def _cleanup_dropped_spell_terrain(self):
        """Check all entities for pending spell terrain cleanup from broken concentration."""
        for ent in self.battle.entities:
            info = getattr(ent, '_dropped_spell_terrain', None)
            if info:
                caster_name, spell_name = info
                self.battle.remove_spell_terrain(caster_name, spell_name)
                ent._dropped_spell_terrain = None

    def _spawn_damage_text(self, entity, amount, is_heal=False, damage_type=""):
        color = COLORS["success"] if is_heal else COLORS["danger"]
        prefix = "+" if is_heal else "-"
        text = f"{prefix}{abs(amount)}"
        ft = FloatingText(entity.grid_x, entity.grid_y, text, color)
        self.floating_texts.append(ft)
        # Impact flash effect
        flash = ImpactFlash(entity.grid_x, entity.grid_y, damage_type, is_heal)
        self.impact_flashes.append(flash)

    def _save_undo_snapshot(self):
        """Save current state to undo stack."""
        state = self.battle.get_state_dict()
        self.undo_stack.append(state)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        # New action clears redo stack
        self.redo_stack.clear()

    def _undo_last_action(self):
        if not self.undo_stack:
            self._log("[UNDO] Nothing to undo.")
            return
        # Save current state for redo before restoring
        self.redo_stack.append(self.battle.get_state_dict())
        state = self.undo_stack.pop()
        self.battle.restore_state(state)
        self.selected_entity = None
        self.pending_plan = None
        self.condition_reminder = None
        self._log("[UNDO] Reverted to previous state.")

    def _redo_action(self):
        if not self.redo_stack:
            self._log("[REDO] Nothing to redo.")
            return
        self.undo_stack.append(self.battle.get_state_dict())
        state = self.redo_stack.pop()
        self.battle.restore_state(state)
        self.selected_entity = None
        self.pending_plan = None
        self.condition_reminder = None
        self._log("[REDO] Re-applied action.")

    # ------------------------------------------------------------------ #
    # Turn management                                                      #
    # ------------------------------------------------------------------ #

    def _do_start_combat(self):
        if not self.battle.entities:
            self._log("[ERROR] Cannot start combat with no entities!")
            return
        try:
            self.battle.start_combat()
            self._log("Combat started! Initiative rolled.")
            curr = self.battle.get_current_entity()
            self._log(f"--- Round {self.battle.round}: {curr.name}'s turn ---")
        except ValueError as e:
            self._log(f"[ERROR] Failed to start combat: {e}")

    def _do_next_turn(self):
        self._save_undo_snapshot()
        # 1. Check for pending Legendary Actions from the previous turn
        leg_ent, leg_step = self.battle.get_pending_legendary_action()
        if leg_ent and leg_step:
            # Create a temporary plan for this single legendary action
            plan = TurnPlan(entity=leg_ent)
            plan.steps.append(leg_step)
            self.pending_plan = plan
            self.pending_step_idx = 0
            self._prepare_step_outcomes()
            self._log(f"[LEGENDARY] {leg_ent.name} is taking a Legendary Action!")
            # Remove from queue so we don't loop forever on the same action
            self.battle.commit_legendary_action(leg_ent)
            return

        # 2. Check for End-of-Turn Saves
        try:
            curr = self.battle.get_current_entity()
            if curr.hp > 0:
                saves = []
                for cond, meta in curr.condition_metadata.items():
                    if meta.get("save") and meta.get("dc"):
                        saves.append((curr, cond, meta["save"], meta["dc"]))
                if saves:
                    if self.auto_battle:
                        # Auto-roll all saves immediately
                        self.pending_saves = saves
                        self._auto_resolve_pending_saves()
                        return
                    elif curr.is_player:
                        # Manual mode: show save modal for players
                        self.pending_saves = saves
                        self.save_modal_open = True
                        return
        except ValueError:
            pass

        self._complete_next_turn(skip_saves=False)

    def _complete_next_turn(self, skip_saves=False):
        self.pending_plan = None
        self.player_action_mode = False
        self.condition_reminder = None
        curr = self.battle.next_turn(skip_saves=skip_saves)
        if curr is None:
            self._log("[SYSTEM] No entities in battle.")
            return

        self.selected_entity = curr
        # Determine if player is AI-controlled
        player_ai = curr.is_player and self.auto_battle and self.auto_battle_mode == "full"
        # If player, open action panel hint and show condition reminder
        if curr.is_player:
            if player_ai:
                self._log(f"[AI PLAYER] {curr.name}'s turn (AI-controlled)")
            else:
                self._log(f"[PLAYER TURN] {curr.name} – log their action with 'LOG PLAYER ACTION'")
            if curr.conditions or curr.concentrating_on:
                self.condition_reminder = curr
            # DM Advisor: generate suggestion for this player's turn
            if self.show_advisor_panel and not player_ai:
                self.dm_suggestion_cache = self.battle.get_dm_suggestion(curr)
                self.dm_rating_cache = None
        else:
            self.dm_suggestion_cache = None
            self.dm_rating_cache = None

        # Track that entity is active this round
        self.battle.stats_tracker.record_round_active(curr.name, curr.is_player)

        # Update win probability
        self._update_win_probability()

        # Turn Banner
        if player_ai:
            self.turn_banner_text = f"{curr.name}'s Turn  [AI]"
        else:
            self.turn_banner_text = f"{curr.name}'s Turn"
        self.turn_banner_timer = 120 # 2 seconds

        # Check auras
        auras = self.battle.check_turn_start_auras(curr)
        if auras:
            self.aura_triggers = auras
            self._open_next_aura_modal()

        # Autosave every 3 turns
        self.autosave_turn_counter += 1
        if self.autosave_turn_counter >= 3:
            self.autosave_turn_counter = 0
            self._perform_autosave()

    def _perform_autosave(self):
        """Autosave current battle state and sync to campaign."""
        try:
            if not os.path.exists(SAVES_DIR):
                os.makedirs(SAVES_DIR)
            filepath = os.path.join(SAVES_DIR, "_autosave.json")
            self.battle.save_state(filepath)
            self._log("[AUTOSAVE] Battle state saved.")
            # Also sync mid-battle state to campaign for crash recovery
            try:
                from engine.campaign_bridge import sync_battle_results_to_campaign, get_campaign_from_manager
                from data.campaign import save_campaign
                campaign = get_campaign_from_manager(self.manager)
                if campaign:
                    sync_battle_results_to_campaign(campaign, self.battle.entities)
                    save_campaign(campaign)
            except Exception:
                pass  # Campaign sync during autosave is best-effort
        except Exception as ex:
            self._log(f"[ERROR] Autosave failed: {ex}")

    def _do_ai_turn(self, force_auto=False):
        curr = self.battle.get_current_entity()
        if self.pending_plan and self.pending_plan.entity == curr:
            self._log("AI plan already pending – confirm or skip each step.")
            return
        # Save entity state before AI planning (planning mutates flags)
        self._pre_plan_state = {
            "action_used": curr.action_used,
            "bonus_action_used": curr.bonus_action_used,
            "reaction_used": curr.reaction_used,
            "movement_left": curr.movement_left,
            "grid_x": curr.grid_x,
            "grid_y": curr.grid_y,
            "reckless_attack_active": curr.reckless_attack_active,
        }
        plan = self.battle.compute_ai_turn(curr)
        if plan.skipped:
            self._log(f"[AI] {curr.name}: {plan.skip_reason}")
            return
        self.pending_plan = plan
        self.pending_step_idx = 0
        if plan.steps:
            self._log(f"[AI PLAN] {curr.name}: {len(plan.steps)} step(s) queued – review below.")
            self._prepare_step_outcomes()

    def _prepare_step_outcomes(self):
        """Pre-calculate hits/saves for the current step so the DM just reviews them."""
        self.current_step_outcomes = {}
        self.current_step_rolls = {}
        if not self.pending_plan or self.pending_step_idx >= len(self.pending_plan.steps):
            return

        step = self.pending_plan.steps[self.pending_step_idx]
        targets = step.targets if step.targets else ([step.target] if step.target else [])

        for t in targets:
            if step.save_dc > 0:
                # Logic change: If target is player and NOT auto-battle, don't auto-roll save.
                # Let DM check TaleSpire and toggle result manually. Default to 'fail' (full damage).
                if t.is_player and not self.auto_battle:
                    self.current_step_outcomes[t] = "fail"
                else:
                    # Auto mode or NPC target: Engine rolls automatically
                    if step.save_ability:
                        # Use make_saving_throw for comprehensive rules (Magic Resistance,
                        # racial traits, Danger Sense, exhaustion, Paladin Aura, etc.)
                        from engine.rules import make_saving_throw
                        cond = step.applies_condition or (step.spell.applies_condition if step.spell else "")
                        dmg_dice = step.spell.damage_dice if step.spell else ""
                        dmg_type = step.damage_type or (step.spell.damage_type if step.spell else "")
                        success, total, msg = make_saving_throw(
                            t, step.save_ability, step.save_dc, self.battle,
                            applies_condition=cond, damage_dice=dmg_dice,
                            damage_type=dmg_type)
                        self.current_step_rolls[t] = msg.split(": ", 1)[-1] if ": " in msg else msg
                        if success:
                            # Check if Legendary Resistance was used (already consumed by make_saving_throw)
                            if "Legendary Resistance" in msg:
                                self._log(f"[LEGENDARY] {msg}")
                            self.current_step_outcomes[t] = "save"
                        else:
                            self.current_step_outcomes[t] = "fail"
                    else:
                        self.current_step_outcomes[t] = "fail"
            elif step.step_type in ("attack", "multiattack", "reaction", "bonus_attack", "legendary") or (step.step_type == "spell" and step.attack_roll > 0):
                # Attack roll already done by AI
                if step.is_hit:
                    self.current_step_outcomes[t] = "hit"
                else:
                    self.current_step_outcomes[t] = "miss"
            else:
                # Auto-hit / buff / heal
                self.current_step_outcomes[t] = "hit"

    def _confirm_step(self):
        if not self.pending_plan:
            return
        self._save_undo_snapshot()
        steps = self.pending_plan.steps
        if self.pending_step_idx < len(steps):
            step = steps[self.pending_step_idx]
            
            # --- Counterspell Check ---
            if step.step_type == "spell" and not step.counter_checked:
                step.counter_checked = True
                # Check if any enemy can counterspell
                lvl = step.slot_used if step.slot_used > 0 else (step.spell.level if step.spell else 0)
                potential = self.battle.check_counterspell_reaction(step.attacker, lvl)
                if potential:
                    self.reaction_pending = potential
                    self.reaction_type = "counterspell"
                    self.reaction_context = {"caster": step.attacker, "level": lvl, "step_idx": self.pending_step_idx}
                    return # Pause confirmation to ask for reaction

            # Handle summon spawning
            if step.step_type == "summon" and step.summon_name:
                new_ent = self.battle.spawn_summon(
                    owner=step.attacker,
                    name=step.summon_name,
                    x=step.summon_x,
                    y=step.summon_y,
                    hp=step.summon_hp,
                    ac=step.summon_ac,
                    damage_dice=step.spell.summon_damage_dice if step.spell else "1d8",
                    damage_type=step.spell.summon_damage_type if step.spell else "force",
                    duration=step.summon_duration,
                    spell_name=step.summon_spell or "",
                )
                self._log(f"  [SUMMON] {step.description}")
                
                # Handle immediate attack (e.g. Spiritual Weapon on cast)
                if step.summon_immediate_attack and step.target and new_ent.stats.actions:
                    action = new_ent.stats.actions[0]
                    atk_step = self.battle.ai._execute_attack(new_ent, action, step.target, self.battle)
                    atk_step.step_type = "bonus_attack"
                    atk_step.description = f"{new_ent.name} attacks immediately!"
                    # Insert into plan so it executes next
                    self.pending_plan.steps.insert(self.pending_step_idx + 1, atk_step)
            else:
                self._log(f"[ACTION] {step.description}")
                # Apply all outcomes
                for t, outcome in self.current_step_outcomes.items():
                    self._resolve_target_outcome(step, t, outcome)

            # Spawn spell terrain if the spell creates persistent effects
            if step.spell and step.spell.creates_terrain and step.aoe_center and step.attacker:
                self.battle.spawn_spell_terrain(step.spell, step.attacker,
                                                step.aoe_center[0], step.aoe_center[1])

            # Clean up terrain from any broken concentration (damage, incapacitation, etc.)
            self._cleanup_dropped_spell_terrain()

            self.pending_step_idx += 1
            self._prepare_step_outcomes()

        if self.pending_step_idx >= len(steps):
            self.pending_plan = None
            self._log("[AI] Turn complete.")

    def _skip_step(self):
        if not self.pending_plan:
            return
        steps = self.pending_plan.steps
        if self.pending_step_idx < len(steps):
            step = steps[self.pending_step_idx]

            # Revert Movement if it happened
            if step.step_type == "move" and step.attacker:
                step.attacker.grid_x = step.old_x
                step.attacker.grid_y = step.old_y
                step.attacker.movement_left += step.movement_ft

            self._log(f"[SKIPPED] {step.description}")

            # Try to suggest an alternative for action/spell steps (once per step)
            is_already_alternative = getattr(step, '_is_alternative', False)
            if step.step_type in ("spell", "attack", "multiattack") and not is_already_alternative:
                alt = self.battle.ai.suggest_alternative(step.attacker, self.battle, step)
                if alt:
                    alt._is_alternative = True  # Prevent infinite re-suggestion
                    steps[self.pending_step_idx] = alt
                    self._log(f"[AI ALTERNATIVE] {alt.description}")
                    self._prepare_step_outcomes()
                    return  # Don't advance - show the alternative for review
                else:
                    self._log("[AI] No alternative available.")

            self.pending_step_idx += 1
            self._prepare_step_outcomes()
        if self.pending_step_idx >= len(steps):
            self.pending_plan = None

    def _approve_all(self):
        if not self.pending_plan:
            return
        for step in self.pending_plan.steps[self.pending_step_idx:]:
            # Auto-resolve everything (assuming hits/fails for speed)
            targets = step.targets if step.targets else ([step.target] if step.target else [])
            for t in targets:
                self._resolve_target_outcome(step, t, "hit" if step.step_type=="attack" else "fail")
            # Spawn spell terrain
            if step.spell and step.spell.creates_terrain and step.aoe_center and step.attacker:
                self.battle.spawn_spell_terrain(step.spell, step.attacker,
                                                step.aoe_center[0], step.aoe_center[1])
            self._cleanup_dropped_spell_terrain()
            self._log(f"[AUTO-CONFIRM] {step.description}")
        self.pending_plan = None
        self._log("[AI] All steps approved.")

    def _cancel_ai_plan(self):
        """Cancel remaining AI plan and let DM take over manually."""
        if not self.pending_plan:
            return
        entity = self.pending_plan.entity
        steps = self.pending_plan.steps
        remaining = len(steps) - self.pending_step_idx

        # Restore entity action economy flags so DM can use them manually
        if hasattr(self, '_pre_plan_state') and self._pre_plan_state and entity:
            entity.action_used = self._pre_plan_state.get("action_used", False)
            entity.bonus_action_used = self._pre_plan_state.get("bonus_action_used", False)
            entity.reaction_used = self._pre_plan_state.get("reaction_used", False)
            entity.movement_left = self._pre_plan_state.get("movement_left", entity.get_speed())
            entity.grid_x = self._pre_plan_state.get("grid_x", entity.grid_x)
            entity.grid_y = self._pre_plan_state.get("grid_y", entity.grid_y)
            entity.reckless_attack_active = self._pre_plan_state.get("reckless_attack_active", False)
            self._pre_plan_state = None

        self.pending_plan = None
        self.pending_step_idx = 0
        self.current_step_outcomes = {}
        self.current_step_rolls = {}
        self._log(f"[AI] Plan cancelled ({remaining} step(s) remaining). Take over manually.")

    def _resolve_target_outcome(self, step, target, outcome):
        """Apply effects based on user choice."""
        if not target: return

        # Ensure applies_condition is set from spell if missing in the step
        if not step.applies_condition and step.spell and step.spell.applies_condition:
            step.applies_condition = step.spell.applies_condition

        # Handle Legendary Resistance outcome
        if outcome == "legendary":
            target.legendary_resistances_left -= 1
            self._log(f"[LEGENDARY] {target.name} uses Legendary Resistance! ({target.legendary_resistances_left} left)")
            outcome = "save"

        dmg = step.damage
        cond = step.applies_condition
        attacker_name = step.attacker.name if step.attacker else "Unknown"
        ability_name = step.action_name or (step.spell.name if step.spell else "")
        is_aoe = bool(step.aoe_center) if hasattr(step, 'aoe_center') else False
        rnd = self.battle.round

        # Track attack results
        is_attack = step.step_type in ("attack", "multiattack", "bonus_attack", "legendary", "reaction") or (step.step_type == "spell" and step.attack_roll > 0)
        
        if is_attack:
            is_hit = outcome in ("hit", "crit", "fail")
            if step.attacker:
                step.attacker.record_attack()
            self.battle.stats_tracker.record_attack(
                rnd, attacker_name, is_hit,
                is_critical=(outcome == "crit"),
                is_fumble=False,
                attacker_is_player=step.attacker.is_player if step.attacker else False)
            
            # Guiding Bolt consumption: The advantage is used on the next attack (hit, miss, or crit)
            if target.has_condition("Guiding Bolt"):
                target.remove_condition("Guiding Bolt")
                self._log(f"  [EFFECT] Guiding Bolt on {target.name} consumed.")

        if outcome == "hit" or outcome == "fail":
            # --- AI REACTION CHECK (Shield) ---
            # If target is NPC, has Shield, reaction available, and Shield would make it miss
            if not target.is_player and not target.reaction_used and outcome in ("hit", "crit"):
                shield = next((s for s in target.stats.spells_known if s.name == "Shield"), None)
                if shield and target.has_spell_slot(shield.level):
                    should_cast = False
                    # If we know the roll, check if AC+5 saves us
                    if step.attack_roll > 0:
                        if target.armor_class + 5 >= step.attack_roll:
                            should_cast = True
                    # If manual/unknown roll, cast if low HP
                    elif target.hp < target.max_hp * 0.5:
                        should_cast = True
                    
                    if should_cast:
                        target.use_spell_slot(shield.level)
                        target.reaction_used = True
                        target.active_effects["Shield"] = 1
                        self._log(f"[REACTION] {target.name} casts Shield! AC +5.")
                        self._spawn_damage_text(target, "Shield!", is_heal=True)
                        
                        # Re-evaluate hit
                        if step.attack_roll > 0 and step.attack_roll < target.armor_class:
                            outcome = "miss"
                            self._log(f"  -> Attack now MISSES!")
                            # Correct stats (remove the hit we just added)
                            if step.step_type in ("attack", "multiattack", "bonus_attack", "legendary"):
                                self.battle.stats_tracker.entity_stats[attacker_name].attacks_hit -= 1
                            
                            # Skip damage application
                            return
            
            # --- AI REACTION CHECK (Silvery Barbs) ---
            # TCoE p.108: When a creature within 60ft succeeds on an attack roll,
            # a caster ally within 60ft can force it to reroll (use the lower).
            # Handled automatically for NPCs (AI) defending an NPC ally that was hit.
            if (not target.is_player and outcome in ("hit", "crit")
                    and step.step_type in ("attack", "multiattack", "bonus_attack",
                                           "legendary", "reaction")
                    and step.attack_roll > 0 and step.attacker):
                barb_caster = None
                barb_spell = None
                for ally in self.battle.get_allies_of(target):
                    if ally is target or ally.hp <= 0 or ally.reaction_used:
                        continue
                    if ally.is_incapacitated():
                        continue
                    sb = next((s for s in ally.stats.spells_known
                               if s.name == "Silvery Barbs"), None)
                    if not sb or not ally.has_spell_slot(sb.level):
                        continue
                    # 60ft from caster to the attacker
                    if self.battle.get_distance(ally, step.attacker) * 5 > 60:
                        continue
                    if not self.battle.has_line_of_sight(ally, step.attacker):
                        continue
                    barb_caster = ally
                    barb_spell = sb
                    break
                if barb_caster is not None and barb_spell is not None:
                    barb_caster.use_spell_slot(barb_spell.level)
                    barb_caster.reaction_used = True
                    # Reroll the attack: new d20 + original bonus, use lower
                    attack_bonus = step.attack_roll - step.nat_roll if step.nat_roll else 0
                    new_roll = random.randint(1, 20)
                    new_total = new_roll + attack_bonus
                    chosen_total = min(step.attack_roll, new_total)
                    chosen_nat = new_roll if new_total < step.attack_roll else step.nat_roll
                    self._log(f"[REACTION] {barb_caster.name} casts Silvery Barbs! "
                              f"{step.attacker.name} rerolls ({new_roll}+{attack_bonus}"
                              f"={new_total}) -> uses {chosen_total}.")
                    self._spawn_damage_text(target, "Barbs!", is_heal=True)
                    step.attack_roll = chosen_total
                    step.nat_roll = chosen_nat
                    # A natural 1 on the chosen roll is no longer a crit; nat 20 stays
                    if chosen_nat != 20 and outcome == "crit":
                        outcome = "hit"
                    if chosen_total < target.armor_class and chosen_nat != 20:
                        outcome = "miss"
                        self._log(f"  -> Attack now MISSES!")
                        if step.step_type in ("attack", "multiattack", "bonus_attack", "legendary"):
                            self.battle.stats_tracker.entity_stats[attacker_name].attacks_hit -= 1
                        return

            # --- AI REACTION CHECK (Parry) ---
            # Generic Parry: Adds AC (usually 2 or 3) against melee attack
            if not target.is_player and not target.reaction_used and outcome in ("hit", "crit") and step.step_type in ("attack", "multiattack", "bonus_attack", "legendary", "reaction"):
                # Check if attack is melee (range <= 5 or adjacent)
                is_melee = (step.action and step.action.range <= 5) or (self.battle.get_distance(target, step.attacker) <= 1.5)
                
                if is_melee:
                    parry = next((r for r in target.stats.reactions if "Parry" in r.name), None)
                    if parry:
                        # Determine bonus (parse description or default to 2)
                        bonus = 2
                        if "3" in parry.description: bonus = 3
                        if "4" in parry.description: bonus = 4
                        
                        # Use if it changes the outcome OR if low HP
                        should_parry = (step.attack_roll > 0 and target.armor_class + bonus >= step.attack_roll) or (target.hp < target.max_hp * 0.5)
                        
                        if should_parry:
                            target.reaction_used = True
                            self._log(f"[REACTION] {target.name} uses Parry! AC +{bonus}.")
                            self._spawn_damage_text(target, "Parry!", is_heal=True)
                            
                            if step.attack_roll > 0 and step.attack_roll <= target.armor_class + bonus:
                                outcome = "miss"
                                self._log(f"  -> Attack now MISSES!")
                                if step.step_type in ("attack", "multiattack", "bonus_attack", "legendary"):
                                    self.battle.stats_tracker.entity_stats[attacker_name].attacks_hit -= 1
                                return

            # Full effect
            if dmg > 0:
                # --- HEALING CHECK ---
                if step.damage_type == "healing":
                    old_hp = target.hp
                    target.heal(dmg)
                    actual_heal = target.hp - old_hp
                    self._log(f"  -> {target.name} heals {actual_heal} HP.")
                    self._spawn_damage_text(target, actual_heal, is_heal=True)
                    self.battle.stats_tracker.record_heal(
                        rnd, attacker_name, target.name, actual_heal,
                        ability_name=ability_name,
                        source_is_player=step.attacker.is_player if step.attacker else False,
                        target_is_player=target.is_player)
                    return

                # --- AI REACTION CHECK (Absorb Elements) ---
                # Reaction to acid/cold/fire/lightning/thunder damage: gain resistance
                _ABSORB_ELEMENTS_TYPES = {"acid", "cold", "fire", "lightning", "thunder"}
                if (not target.is_player and not target.reaction_used
                        and step.damage_type in _ABSORB_ELEMENTS_TYPES):
                    absorb = next((s for s in target.stats.spells_known
                                   if s.name == "Absorb Elements"), None)
                    if absorb and target.has_spell_slot(absorb.level):
                        # Cast if damage is significant (≥15% max HP)
                        if dmg >= target.max_hp * 0.15:
                            target.use_spell_slot(absorb.level)
                            target.reaction_used = True
                            dmg = dmg // 2  # Resistance = half damage
                            # Store absorbed type for next melee hit bonus
                            target.active_effects["Absorb Elements"] = 1
                            self._log(f"[REACTION] {target.name} casts Absorb Elements! "
                                      f"Resistance to {step.damage_type}, damage halved.")
                            self._spawn_damage_text(target, "Absorb!", is_heal=True)

                # --- AI REACTION CHECK (Uncanny Dodge) ---
                # Halve damage from an attack you can see
                if not target.is_player and not target.reaction_used and step.attacker and target.has_feature("uncanny_dodge"):
                    target.reaction_used = True
                    dmg = dmg // 2
                    self._log(f"[REACTION] {target.name} uses Uncanny Dodge! Damage halved.")
                    self._spawn_damage_text(target, "Dodge!", is_heal=True)

                # PHB p.170: Evasion (Fail) - half damage instead of full
                # Must apply BEFORE take_damage so it actually reduces damage dealt
                evasion_on_fail = False
                if outcome == "fail" and step.save_ability == "Dexterity" and target.has_feature("evasion"):
                    dmg = dmg // 2
                    evasion_on_fail = True

                old_hp = target.hp
                dealt, broke = target.take_damage(dmg, step.damage_type, is_magical=step.is_magical)

                # --- AI REACTION CHECK (Hellish Rebuke) ---
                if not target.is_player and not target.reaction_used and dealt > 0 and step.attacker:
                    rebuke = next((s for s in target.stats.spells_known if s.name == "Hellish Rebuke"), None)
                    if rebuke and target.has_spell_slot(rebuke.level) and self.battle.get_distance(target, step.attacker) * 5 <= 60:
                        target.use_spell_slot(rebuke.level)
                        target.reaction_used = True
                        
                        # Resolve Rebuke damage immediately
                        rebuke_dmg = roll_dice(rebuke.damage_dice)
                        # DEX save for half
                        save_bonus = step.attacker.get_save_bonus("Dexterity")
                        dc = target.stats.spell_save_dc
                        save_roll = random.randint(1, 20) + save_bonus
                        if save_roll >= dc:
                            rebuke_dmg //= 2
                            self._log(f"[REACTION] {target.name} casts Hellish Rebuke! {step.attacker.name} saves.")
                        else:
                            self._log(f"[REACTION] {target.name} casts Hellish Rebuke! {step.attacker.name} fails save.")
                        
                        r_dealt, _ = step.attacker.take_damage(rebuke_dmg, "fire")
                        self._spawn_damage_text(step.attacker, r_dealt, damage_type="fire")
                        self._log(f"  -> {step.attacker.name} takes {r_dealt} fire damage.")

                # --- AI REACTION CHECK (Generic "When hit" effects) ---
                if not target.is_player and not target.reaction_used and dealt > 0 and step.attacker:
                    for reaction in target.stats.reactions:
                        # Unnerving Mask (Chain Devil)
                        if "Unnerving Mask" in reaction.name:
                            target.reaction_used = True
                            self._log(f"[REACTION] {target.name} uses {reaction.name}!")
                            # DC 13 WIS or Frightened
                            dc = 13
                            match = re.search(r"DC (\d+)", reaction.description)
                            if match: dc = int(match.group(1))
                            
                            save_bonus = step.attacker.get_save_bonus("Wisdom")
                            roll = random.randint(1, 20) + save_bonus
                            if roll >= dc:
                                self._log(f"  -> {step.attacker.name} saves vs Unnerving Mask.")
                            else:
                                self._log(f"  -> {step.attacker.name} failed save! Frightened.")
                                step.attacker.add_condition("Frightened", source=target)
                            break

                if outcome == "fail":
                    if evasion_on_fail:
                        self._log(f"  [EVASION] {target.name} fails save but takes half damage (Evasion).")

                    roll_str = self.current_step_rolls.get(target, "")
                    roll_msg = f" (Rolled {roll_str} vs DC {step.save_dc})" if roll_str else ""
                    self._log(f"  -> {target.name} FAILED save{roll_msg}: takes {dealt} {step.damage_type}")
                else:
                    self._log(f"  -> {target.name} takes {dealt} {step.damage_type}")
                self._spawn_damage_text(target, dealt, damage_type=step.damage_type or "")
                # Track damage
                self.battle.stats_tracker.record_damage(
                    rnd, attacker_name, target.name, dealt, step.damage_type,
                    ability_name=ability_name, is_aoe=is_aoe,
                    was_saved=False,
                    source_is_player=step.attacker.is_player if step.attacker else False,
                    target_is_player=target.is_player)
                self.battle._last_damage_source = attacker_name
                # Check for down/kill
                if target.hp <= 0 and old_hp > 0:
                    self.battle.stats_tracker.record_downed(rnd, target.name, target.is_player)
                    if not target.is_player:
                        self.battle.stats_tracker.record_kill(
                            rnd, attacker_name, target.name,
                            killer_is_player=step.attacker.is_player if step.attacker else False,
                            target_is_player=target.is_player)
                
                # Check for death save failure (Damage at 0 HP)
                elif target.hp <= 0 and old_hp <= 0 and target.is_player:
                    failures = 2 if outcome == "crit" else 1
                    target.death_save_failures += failures
                    target.death_save_history.extend(["F"] * failures)
                    self._log(f"  -> {target.name} suffers {failures} death save failure(s)!")
                    if target.death_save_failures >= 3:
                        self._log(f"  -> {target.name} has DIED!")
                        # Record kill if not already recorded
                        # (Logic for recording kill is usually on drop to 0, but here they die for real)

            if cond:
                # Determine DC and Save Ability for the condition
                dc = step.condition_dc if step.condition_dc else step.save_dc
                save_ab = step.save_ability

                # Fix: Check if spell allows repeating saves (e.g. Banishment does not)
                if step.spell and not step.spell.repeat_save:
                    save_ab = None

                # Pass source entity for source-dependent conditions (Frightened, Charmed, Banished)
                condition_source = step.attacker if cond in ("Frightened", "Charmed", "Banished") else None
                target.add_condition(cond, save_ability=save_ab, save_dc=dc, source=condition_source)
                self.battle.stats_tracker.record_condition(
                    rnd, target.name, cond, applied_by=attacker_name,
                    target_is_player=target.is_player,
                    applier_is_player=step.attacker.is_player if step.attacker else False)

                if step.spell and step.spell.concentration and step.attacker:
                    dropped_spell = step.attacker.start_concentration(step.spell)
                    if dropped_spell:
                        self._log(f"  -> {step.attacker.name} stops concentrating on {dropped_spell.name}.")
                self._log(f"  -> {target.name} is {cond}")

                # Special handling for Banishment: Remove from map immediately
                if cond == "Banished":
                    target.banished_from = (target.grid_x, target.grid_y)
                    target.grid_x = -1000.0  # Move off-map
                    target.grid_y = -1000.0
                    self._log(f"  [BANISHMENT] {target.name} vanishes to a demiplane!")
        
        # Handle Transformation (Wild Shape)
        if step.step_type == "transform" and step.attacker and step.transform_stats:
            step.attacker.transform_into(step.transform_stats)
            self._log(f"  -> {step.attacker.name} transforms into {step.transform_stats.name}!")
            self._spawn_damage_text(step.attacker, "Wild Shape!", is_heal=True)
        
        # Handle special actions (Shake Awake, Cleansing Touch)
        if step.action_name == "Shake Awake":
            if target.has_condition("Unconscious") and target.hp > 0:
                target.remove_condition("Unconscious")
                self._log(f"  -> {target.name} wakes up!")
        
        elif step.action_name == "Cleansing Touch" or step.action_name == "Lesser Restoration":
            # Remove one spell or condition
            removed = False
            for c in ["Paralyzed", "Blinded", "Deafened", "Poisoned", "Stunned"]:
                if target.has_condition(c):
                    target.remove_condition(c)
                    self._log(f"  -> {target.name} is no longer {c}.")
                    removed = True
                    break
            
            # Apply duration effects (Buffs/Debuffs that aren't conditions, e.g. Bless, Haste)
            # Also track duration for Banishment (critical for permanent banishment logic)
            if step.spell and step.spell.duration:
                 # Skip if it's a condition-applying spell that ISN'T Banishment (usually handled by save repeats)
                 if step.applies_condition and step.applies_condition not in ("Banished", "Guiding Bolt"):
                     pass
                 else:
                     # Parse duration roughly
                     rounds = 10 # default 1 min
                     if "minute" in step.spell.duration: rounds = 10
                     elif "hour" in step.spell.duration: rounds = 600
                     elif "round" in step.spell.duration: rounds = int(step.spell.duration.split()[0])
                     
                     target.active_effects[step.spell.name] = rounds
                     self._log(f"  -> {step.spell.name} applied ({rounds} rnds)")

        elif outcome == "save":
            # Half damage (usually), no condition
            half_dmg = dmg // 2
            
            # Evasion (Success): No damage instead of half
            if step.save_ability == "Dexterity" and target.has_feature("evasion"):
                half_dmg = 0
                self._log(f"  [EVASION] {target.name} succeeds save and takes NO damage.")

            self.battle.stats_tracker.record_saving_throw(rnd, target.name, True,
                                                          entity_is_player=target.is_player)
            if half_dmg > 0:
                old_hp = target.hp
                dealt, broke = target.take_damage(half_dmg, step.damage_type, is_magical=step.is_magical)
                roll_str = self.current_step_rolls.get(target, "")
                roll_msg = f" (Rolled {roll_str} vs DC {step.save_dc})" if roll_str else ""
                self._log(f"  -> {target.name} SAVED{roll_msg}: takes {dealt} {step.damage_type}")
                self._spawn_damage_text(target, dealt, damage_type=step.damage_type or "")
                self.battle.stats_tracker.record_damage(
                    rnd, attacker_name, target.name, dealt, step.damage_type,
                    ability_name=ability_name, was_saved=True, is_aoe=is_aoe,
                    source_is_player=step.attacker.is_player if step.attacker else False,
                    target_is_player=target.is_player)
                if target.hp <= 0 and old_hp > 0:
                    self.battle.stats_tracker.record_downed(rnd, target.name, target.is_player)
                
                # Check for death save failure (Damage at 0 HP)
                elif target.hp <= 0 and old_hp <= 0 and target.is_player:
                    target.death_save_failures += 1
                    target.death_save_history.append("F")
                    self._log(f"  -> {target.name} suffers 1 death save failure!")
                    if target.death_save_failures >= 3:
                        self._log(f"  -> {target.name} has DIED!")

            else:
                roll_str = self.current_step_rolls.get(target, "")
                roll_msg = f" (Rolled {roll_str} vs DC {step.save_dc})" if roll_str else ""
                self._log(f"  -> {target.name} SAVED{roll_msg}: no damage")

        elif outcome == "crit":
            # Double dice damage (simplified here as 1.5x or just raw since we pre-rolled)
            final_dmg = dmg
            # If AI didn't crit but user forced crit, roll extra dice
            if not step.is_crit:
                dice_str = ""
                if step.action: dice_str = step.action.damage_dice
                elif step.spell: dice_str = step.spell.damage_dice

                if dice_str:
                    extra = roll_dice(dice_str)
                    final_dmg += extra
                    self._log(f"[DM] Crit override! Added {extra} extra damage.")

            if final_dmg > 0:
                old_hp = target.hp
                dealt, broke = target.take_damage(final_dmg, step.damage_type, is_magical=step.is_magical)
                self._log(f"  -> {target.name} takes {dealt} {step.damage_type} (CRIT)")
                self._spawn_damage_text(target, dealt)
                self.battle.stats_tracker.record_damage(
                    rnd, attacker_name, target.name, dealt, step.damage_type,
                    ability_name=ability_name, is_critical=True,
                    source_is_player=step.attacker.is_player if step.attacker else False,
                    target_is_player=target.is_player)
                if target.hp <= 0 and old_hp > 0:
                    self.battle.stats_tracker.record_downed(rnd, target.name, target.is_player)
                    if not target.is_player:
                        self.battle.stats_tracker.record_kill(
                            rnd, attacker_name, target.name,
                            killer_is_player=step.attacker.is_player if step.attacker else False,
                            target_is_player=target.is_player)
                
                # Check for death save failure (Damage at 0 HP)
                elif target.hp <= 0 and old_hp <= 0 and target.is_player:
                    failures = 2 # Crits cause 2 failures
                    target.death_save_failures += failures
                    target.death_save_history.extend(["F"] * failures)
                    self._log(f"  -> {target.name} suffers {failures} death save failures (CRIT)!")
                    if target.death_save_failures >= 3:
                        self._log(f"  -> {target.name} has DIED!")

            # Apply conditions as normal
            if cond:
                dc = step.condition_dc if step.condition_dc else step.save_dc
                save_ab = step.save_ability
                condition_source = step.attacker if cond in ("Frightened", "Charmed") else None
                target.add_condition(cond, save_ability=save_ab, save_dc=dc, source=condition_source)

        # Track spell usage
        if step.spell and step.spell.level > 0:
            self.battle.stats_tracker.record_spell(
                rnd, attacker_name, step.spell.name, step.spell.level,
                targets=[target.name],
                total_damage=dmg if outcome in ("hit", "fail", "crit") else dmg // 2,
                applied_condition=cond,
                caster_is_player=step.attacker.is_player if step.attacker else False)

        # Update win probability after each resolution
        self._update_win_probability()

        # Check for battle end
        self._check_battle_end()

    def _toggle_outcome(self, target):
        if target not in self.current_step_outcomes: return
        curr = self.current_step_outcomes[target]
        if curr == "hit": new = "crit"
        elif curr == "crit": new = "miss"
        elif curr == "miss": new = "hit"
        elif curr == "fail": new = "save"
        elif curr == "save": 
            if target.legendary_resistances_left > 0:
                new = "legendary"
            else:
                new = "fail"
        elif curr == "legendary": new = "fail"
        else: new = curr
        self.current_step_outcomes[target] = new

    # ------------------------------------------------------------------ #
    # Player action panel                                                  #
    # ------------------------------------------------------------------ #

    def _open_player_action_panel(self):
        curr = self.battle.get_current_entity()
        if curr.is_player:
            self.player_action_mode = True
            self.player_action_type = None

    def _pl_set_type(self, action_type):
        curr = self.battle.get_current_entity()
        self.player_action_type = action_type
        if action_type == "attack":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} attacks. (Mark damage manually or use HP buttons)")
        elif action_type == "spell":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} casts a spell. (Use spell slot tracking if needed)")
        elif action_type == "move":
            self._log(f"[PLAYER] {curr.name} moves. (Drag token to new position)")
        elif action_type == "dash":
            curr.action_used = True
            curr.movement_left += curr.stats.speed
            self._log(f"[PLAYER] {curr.name} Dashes. Movement doubled.")
        elif action_type == "disengage":
            curr.action_used = True
            curr.is_disengaging = True
            self._log(f"[PLAYER] {curr.name} Disengages. Movement won't provoke Opportunity Attacks.")
        elif action_type == "dodge":
            curr.action_used = True
            curr.is_dodging = True
            self._log(f"[PLAYER] {curr.name} Dodges. Attacks against have Disadvantage.")
        elif action_type == "help":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} Helps an ally. Ally gets Advantage on next attack/check.")
        elif action_type == "item":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} uses an item. (Apply effect manually)")

        # Rate the player's action using DM advisor
        self._rate_player_action(action_type)

    def _close_player_panel(self):
        self.player_action_mode = False
        self.player_action_type = None

    # ------------------------------------------------------------------ #
    # HP / conditions / init                                               #
    # ------------------------------------------------------------------ #

    def _modify_hp(self, amount):
        sel = self.selected_entity
        if not sel:
            return
        self._save_undo_snapshot()
        old_hp = sel.hp
        if amount < 0:
            dealt, broke = sel.take_damage(-amount)
            action_str = f"takes {dealt} damage"
            if broke:
                action_str += " [CONCENTRATION BROKEN]"
            self._spawn_damage_text(sel, dealt)
            # Track damage in stats
            source = self.battle._last_damage_source or "DM"
            self.battle.stats_tracker.record_damage(
                self.battle.round, source, sel.name, dealt, "untyped",
                ability_name="Manual", source_is_player=False,
                target_is_player=sel.is_player)
            if sel.hp <= 0 and old_hp > 0:
                self.battle.stats_tracker.record_downed(
                    self.battle.round, sel.name, sel.is_player)
        else:
            sel.heal(amount)
            actual_heal = sel.hp - old_hp
            action_str = f"healed {actual_heal} HP"
            self._spawn_damage_text(sel, actual_heal, is_heal=True)
            if actual_heal > 0:
                self.battle.stats_tracker.record_heal(
                    self.battle.round, "DM", sel.name, actual_heal,
                    ability_name="Manual", target_is_player=sel.is_player)
        self._log(f"[DM] {sel.name} {action_str}. HP: {sel.hp}/{sel.max_hp}")
        self._update_win_probability()
        self._check_battle_end()

    def _modify_init(self, delta):
        if self.selected_entity:
            self._save_undo_snapshot()
            self.battle.update_initiative(self.selected_entity, delta)

    def _toggle_condition(self, cond):
        sel = self.selected_entity
        if not sel:
            return
        self._save_undo_snapshot()
        if sel.has_condition(cond):
            sel.remove_condition(cond)
            self._log(f"[DM] {sel.name}: {cond} removed.")
        else:
            sel.add_condition(cond)
            self._log(f"[DM] {sel.name}: {cond} applied.")

    def _use_spell_slot(self, level):
        self._modify_spell_slot(level, -1)

    def _modify_spell_slot(self, level, delta):
        sel = self.selected_entity
        if not sel:
            return
        self._save_undo_snapshot()
        key = {1:"1st",2:"2nd",3:"3rd"}.get(level, f"{level}th")
        
        current = sel.spell_slots.get(key, 0)
        max_slots = sel.stats.spell_slots.get(key, 0)
        
        # Calculate new value clamped between 0 and max
        new_val = max(0, min(max_slots, current + delta))
        
        if new_val != current:
            sel.spell_slots[key] = new_val
            action = "uses" if delta < 0 else "restores"
            self._log(f"[DM] {sel.name} {action} {key}-level slot. ({new_val}/{max_slots})")
            
            # Check Counterspell only if using a slot (casting)
            if delta < 0:
                counters = self.battle.check_counterspell_reaction(sel, level)
                if counters:
                    self.reaction_pending = counters
                    self.reaction_type = "counterspell"
                    self.reaction_context = {"caster": sel, "level": level}

    def _apply_hp_input(self):
        """Apply direct HP input like '-17' or '+5'."""
        if not self.hp_input_text or not self.selected_entity:
            self.hp_input_active = False
            self.hp_input_text = ""
            return
        try:
            amount = int(self.hp_input_text)
        except ValueError:
            amount = 0
        if amount != 0:
            self._modify_hp(amount)
        self.hp_input_active = False
        self.hp_input_text = ""

    # ------------------------------------------------------------------ #
    # Context menu                                                         #
    # ------------------------------------------------------------------ #

    def _open_ctx_menu(self, pos, entity):
        self.selected_entity = entity
        self.ctx_open = True
        self.ctx_pos = pos
        options = [
            (f"APPLY DAMAGE...", lambda: self._open_damage_modal(entity)),
            (f"Dmg  5", lambda: self._modify_hp(-5)),
            (f"Dmg 10", lambda: self._modify_hp(-10)),
            (f"Heal  5", lambda: self._modify_hp(5)),
            (f"Heal 10", lambda: self._modify_hp(10)),
            (f"Toggle Prone",     lambda: self._toggle_condition("Prone")),
            (f"Toggle Stunned",   lambda: self._toggle_condition("Stunned")),
            (f"Toggle Poisoned",  lambda: self._toggle_condition("Poisoned")),
            (f"Toggle Restrained",lambda: self._toggle_condition("Restrained")),
            (f"Init +1", lambda: self._modify_init(1)),
            (f"Init -1", lambda: self._modify_init(-1)),
            (f"Drop Concentration", lambda: (entity.drop_concentration(), self._cleanup_dropped_spell_terrain(), self._log(f"{entity.name} drops concentration."))),
            (f"Add Effect...", lambda: self._open_effect_modal(entity)),
            (f"Edit Notes...", lambda: self._open_notes_modal(entity)),
            (f"SET AI TARGET", lambda: self._set_ai_forced_target(entity)),
            (f"Clear Dead", lambda: self._clear_dead_monsters()),
        ]
        x, y = pos
        w, h = 170, 28
        self.ctx_rects = []
        for i, (txt, cb) in enumerate(options):
            self.ctx_rects.append((pygame.Rect(x, y + i*h, w, h), cb, txt))

    def _open_notes_modal(self, entity):
        self.ctx_open = False
        self.notes_modal = NotesModal(entity, self._close_notes_modal)

    def _close_notes_modal(self, result):
        if result is not None: self._save_undo_snapshot()
        self.notes_modal = None

    def _open_effect_modal(self, entity):
        self.ctx_open = False
        self.effect_modal = EffectModal(entity, self._close_effect_modal)

    def _close_effect_modal(self, result):
        if result: self._save_undo_snapshot()
        self.effect_modal = None
        if result: self._log(f"[DM] Added effect: {result}")

    def _set_ai_forced_target(self, target_entity):
        """DM forces the current active entity to target a specific enemy on next AI turn."""
        self.ctx_open = False
        try:
            curr = self.battle.get_current_entity()
        except ValueError:
            self._log("[DM] No active entity to assign target to.")
            return
        if curr == target_entity:
            self._log("[DM] Can't target self.")
            return
        curr.dm_forced_target = target_entity
        self._log(f"[DM TARGET] {curr.name} will target {target_entity.name} on next AI turn.")

    def _clear_dead_monsters(self):
        self._save_undo_snapshot()
        # Remove non-player entities with <= 0 HP
        before = len(self.battle.entities)
        
        # Save current entity to restore index
        current_ent = None
        if self.battle.entities and 0 <= self.battle.turn_index < len(self.battle.entities):
             current_ent = self.battle.entities[self.battle.turn_index]

        self.battle.entities = [e for e in self.battle.entities if e.is_player or e.hp > 0 or e.is_lair]
        
        # Re-calculate turn_index
        if current_ent and current_ent in self.battle.entities:
            self.battle.turn_index = self.battle.entities.index(current_ent)
        elif self.battle.entities:
            self.battle.turn_index = self.battle.turn_index % len(self.battle.entities)
        else:
            self.battle.turn_index = 0

        removed = before - len(self.battle.entities)
        self._log(f"[DM] Removed {removed} dead monsters.")

    def _cycle_weather(self):
        self._save_undo_snapshot()
        modes = ["Clear", "Rain", "Fog", "Ash"]
        try:
            idx = modes.index(self.battle.weather)
        except ValueError:
            idx = 0
        new_idx = (idx + 1) % len(modes)
        self.battle.weather = modes[new_idx]
        self.btn_weather.text = self.battle.weather.upper()
        self._log(f"[DM] Weather changed to {self.battle.weather}")
    def _roll_save(self, ability, bonus):
        val, text = roll_d20()
        total = val + bonus
        self._log(f"[SAVE] {self.selected_entity.name} {ability} Save: {text} + {bonus} = {total}")
        
        self.roll_modal_title = f"{ability} Save"
        self.roll_modal_expression = f"d20({val}) + {bonus}"
        self.roll_modal_total = total
        self.roll_modal_nat = val
        self.roll_modal_open = True

    def _roll_skill(self, skill, bonus):
        # Check for Guidance
        guidance_bonus = 0
        if self.selected_entity and "Guidance" in self.selected_entity.active_effects:
            guidance_bonus = random.randint(1, 4)
            self.selected_entity.active_effects.pop("Guidance")
            self._log(f"[EFFECT] Guidance used on {skill}.")

        val, text = roll_d20()
        total = val + bonus + guidance_bonus
        
        expr = f"d20({val}) + {bonus}" + (f" + {guidance_bonus}(Guidance)" if guidance_bonus else "")
        self._log(f"[SKILL] {self.selected_entity.name} {skill}: {expr} = {total}")

        self.roll_modal_title = f"{skill} Check"
        self.roll_modal_expression = expr
        self.roll_modal_total = total
        self.roll_modal_nat = val
        self.roll_modal_open = True

    # ------------------------------------------------------------------ #
    # Damage Application Modal                                             #
    # ------------------------------------------------------------------ #

    def _open_damage_modal(self, entity):
        self.dmg_modal_open = True
        self.dmg_target = entity
        self.dmg_value_str = ""
        self.dmg_type = "slashing"
        self.ctx_open = False  # Close context menu

    def _apply_damage_confirm(self):
        self._save_undo_snapshot()
        if not self.dmg_target:
            self.dmg_modal_open = False
            return
        try:
            amount = int(self.dmg_value_str) if self.dmg_value_str else 0
        except ValueError:
            amount = 0

        if amount > 0:
            # Calculate damage using entity's logic (handles resistances)
            dealt, broke = self.dmg_target.take_damage(amount, self.dmg_type)
            
            # Log the result
            log_msg = f"[DMG] {self.dmg_target.name} takes {dealt} {self.dmg_type} damage"
            if dealt < amount:
                log_msg += f" (resisted from {amount})"
            if broke:
                log_msg += " [CONC BROKEN]"
            self._log(log_msg)
            self._spawn_damage_text(self.dmg_target, dealt)
        
        self.dmg_modal_open = False
    def _paint_terrain_at(self, pos, button):
        mx, raw_my = pos
        if mx < GRID_W and raw_my >= TOP_BAR_H:
            gx, gy = self._screen_to_grid(mx, raw_my)
            gx, gy = int(gx), int(gy)
            if self.terrain_tool == "paint":
                if button == 1:  # Paint
                    t = TerrainObject(self.terrain_selected_type, gx, gy)
                    self.battle.add_terrain(t)
                elif button == 3:  # Erase
                    self.battle.remove_terrain_at(gx, gy)
            elif self.terrain_tool == "move":
                if button == 1:
                    self._terrain_move_start(gx, gy)
                elif button == 3:
                    self.battle.remove_terrain_at(gx, gy)
            elif self.terrain_tool == "rect":
                if button == 1:
                    self._terrain_rect_click(gx, gy)
                elif button == 3:
                    self.battle.remove_terrain_at(gx, gy)
            elif self.terrain_tool == "elev":
                if button == 1:
                    self._terrain_elev_click(gx, gy)
                elif button == 3:
                    self._terrain_elev_click(gx, gy, decrease=True)

    # --- Terrain Move Tool ---
    def _terrain_move_start(self, gx, gy):
        t = self.battle.get_terrain_at(gx, gy)
        if t:
            self.terrain_drag_obj = t
            self.terrain_drag_offset = (gx - t.grid_x, gy - t.grid_y)

    def _terrain_move_release(self, pos):
        if not self.terrain_drag_obj:
            return
        mx, raw_my = pos
        if mx < GRID_W and raw_my >= TOP_BAR_H:
            gx, gy = self._screen_to_grid(mx, raw_my)
            gx, gy = int(gx), int(gy)
            dx, dy = self.terrain_drag_offset
            self.terrain_drag_obj.grid_x = gx - dx
            self.terrain_drag_obj.grid_y = gy - dy
        self.terrain_drag_obj = None

    # --- Terrain Rectangle Tool ---
    def _terrain_rect_click(self, gx, gy):
        if self.terrain_rect_start is None:
            self.terrain_rect_start = (gx, gy)
        else:
            # Fill rectangle with selected terrain
            sx, sy = self.terrain_rect_start
            x1, x2 = min(sx, gx), max(sx, gx)
            y1, y2 = min(sy, gy), max(sy, gy)
            for rx in range(x1, x2 + 1):
                for ry in range(y1, y2 + 1):
                    t = TerrainObject(self.terrain_selected_type, rx, ry)
                    self.battle.add_terrain(t)
            self.terrain_rect_start = None
            self.terrain_rect_preview = []

    def _terrain_rect_update_preview(self, pos):
        """Update rect preview while mouse moves after first click."""
        if self.terrain_rect_start is None:
            self.terrain_rect_preview = []
            return
        mx, raw_my = pos
        if mx < GRID_W and raw_my >= TOP_BAR_H:
            gx, gy = self._screen_to_grid(mx, raw_my)
            gx, gy = int(gx), int(gy)
            sx, sy = self.terrain_rect_start
            x1, x2 = min(sx, gx), max(sx, gx)
            y1, y2 = min(sy, gy), max(sy, gy)
            self.terrain_rect_preview = [(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)]

    # --- Terrain Elevation Editor ---
    def _terrain_elev_click(self, gx, gy, decrease=False):
        t = self.battle.get_terrain_at(gx, gy)
        if t:
            step = -5 if decrease else 5
            t.elevation = t.elevation + step
            self._log(f"[TERRAIN] {t.name} elevation -> {t.elevation}ft")

    # --- Terrain Copy/Paste ---
    def _terrain_copy_selection(self):
        """Copy terrain in selection rectangle to clipboard."""
        if self.terrain_select_start and self.terrain_select_end:
            sx, sy = self.terrain_select_start
            ex, ey = self.terrain_select_end
            x1, x2 = min(sx, ex), max(sx, ex)
            y1, y2 = min(sy, ey), max(sy, ey)
            self.terrain_clipboard = []
            for t in self.battle.terrain:
                if x1 <= t.grid_x <= x2 and y1 <= t.grid_y <= y2:
                    self.terrain_clipboard.append({
                        "terrain_type": t.terrain_type,
                        "dx": t.grid_x - x1,
                        "dy": t.grid_y - y1,
                        "elevation": t.elevation,
                        "door_open": t.door_open,
                    })
            self._log(f"[TERRAIN] Copied {len(self.terrain_clipboard)} terrain objects.")
            self.terrain_select_start = None
            self.terrain_select_end = None

    def _terrain_paste_at(self, gx, gy):
        """Paste clipboard terrain at grid position."""
        if not self.terrain_clipboard:
            return
        count = 0
        for item in self.terrain_clipboard:
            t = TerrainObject(
                item["terrain_type"],
                gx + item["dx"],
                gy + item["dy"],
                elevation=item.get("elevation", -1),
                door_open=item.get("door_open", False),
            )
            self.battle.add_terrain(t)
            count += 1
        self._log(f"[TERRAIN] Pasted {count} terrain objects.")
        self.terrain_paste_preview = False

    # --- Terrain Favorites ---
    def _terrain_add_favorite(self):
        """Add current terrain type to favorites."""
        if self.terrain_selected_type not in self.terrain_favorites:
            if len(self.terrain_favorites) >= 10:
                self.terrain_favorites.pop()
            self.terrain_favorites.insert(0, self.terrain_selected_type)

    def _terrain_remove_favorite(self, ttype):
        """Remove a terrain type from favorites."""
        if ttype in self.terrain_favorites:
            self.terrain_favorites.remove(ttype)
    def _start_spell_targeting(self, entity, spell):
        self.spell_caster = entity
        self.spell_targeting = spell
        self._log(f"[TARGETING] Select target/area for {spell.name} (Range: {spell.range}ft)")

    def _cancel_spell_targeting(self):
        self.spell_caster = None
        self.spell_targeting = None
        self._log("[TARGETING] Cancelled.")
    def _execute_manual_spell(self, mp):
        mx, my = mp
        if mx > GRID_W or my < TOP_BAR_H:
            return

        caster = self.spell_caster
        spell = self.spell_targeting
        gx, gy = self._screen_to_grid(mx, my)
        
        # Validate Range
        dist_ft = math.hypot(gx - caster.grid_x, gy - caster.grid_y) * 5
        if dist_ft > spell.range + 5: # Small buffer
            self._log("[TARGETING] Out of range!")
            return

        # Identify Targets
        targets = []
        aoe_center = None
        
        if spell.aoe_radius > 0:
            # AoE Logic
            aoe_center = (gx, gy)
            # Simple sphere check for now
            for ent in self.battle.entities:
                if ent.hp <= 0: continue
                d = math.hypot(ent.grid_x - gx, ent.grid_y - gy) * 5
                if d <= spell.aoe_radius:
                    targets.append(ent)
        else:
            # Single Target
            t = self.battle.get_entity_at(gx, gy)
            if t and t.hp > 0:
                targets.append(t)

        if not targets and spell.aoe_radius == 0:
            self._log("[TARGETING] No target selected.")
            return

        # Roll Damage/Healing
        dmg = roll_dice(spell.damage_dice)
        heal = roll_dice(spell.heals)

        # Determine whether this is a healing cast — the resolver uses
        # damage_type == "healing" to route to target.heal() instead of damage.
        is_healing = bool(spell.heals) and heal > 0
        step_damage = heal if is_healing else dmg
        step_damage_type = "healing" if is_healing else spell.damage_type

        # Create ActionStep
        step = ActionStep(
            step_type="spell",
            description=f"{caster.name} casts {spell.name}.",
            attacker=caster,
            targets=targets,
            spell=spell,
            damage=step_damage,
            damage_type=step_damage_type,
            save_dc=caster.stats.spell_save_dc,
            save_ability=spell.save_ability,
            applies_condition=spell.applies_condition,
            condition_dc=caster.stats.spell_save_dc,
            aoe_center=aoe_center if aoe_center else tuple()
        )

        # Create Plan and Queue
        plan = TurnPlan(entity=caster, steps=[step])
        self.pending_plan = plan
        self.pending_step_idx = 0
        self._prepare_step_outcomes()
        self._cancel_spell_targeting()
        self._log(f"[ACTION] Casting {spell.name} on {len(targets)} targets...")

    # ------------------------------------------------------------------ #
    # Manual Action Targeting & Execution                                  #
    # ------------------------------------------------------------------ #

    def _start_action_targeting(self, entity, action):
        self.action_caster = entity
        self.action_targeting = action
        self._log(f"[TARGETING] Select target for {action.name} ({action.range}ft)")

    def _cancel_action_targeting(self):
        self.action_caster = None
        self.action_targeting = None
        self._log("[TARGETING] Cancelled.")
    def _execute_manual_action(self, mp):
        mx, my = mp
        if mx > GRID_W or my < TOP_BAR_H: return

        caster = self.action_caster
        action = self.action_targeting
        gx, gy = self._screen_to_grid(mx, my)

        # Targets
        targets = []
        aoe_center = None
        
        if action.aoe_radius > 0:
            aoe_center = (gx, gy)
            for ent in self.battle.entities:
                if ent.hp <= 0: continue
                d = math.hypot(ent.grid_x - gx, ent.grid_y - gy) * 5
                if d <= action.aoe_radius:
                    targets.append(ent)
        else:
            t = self.battle.get_entity_at(gx, gy)
            if t and t.hp > 0:
                targets.append(t)

        if not targets and action.aoe_radius == 0:
            self._log("[TARGETING] No target selected.")
            return

        # Roll damage
        dmg = roll_dice(action.damage_dice)
        if action.damage_bonus:
            dmg += action.damage_bonus

        step = ActionStep(
            step_type=action.action_type if action.action_type in ("legendary","reaction","bonus_attack") else "attack",
            description=f"{caster.name} uses {action.name}.",
            attacker=caster, targets=targets, action=action,
            damage=dmg, damage_type=action.damage_type,
            action_name=action.name,
            save_dc=action.condition_dc, save_ability=action.condition_save,
            applies_condition=action.applies_condition,
            aoe_center=aoe_center if aoe_center else tuple()
        )

        plan = TurnPlan(entity=caster, steps=[step])
        self.pending_plan = plan
        self.pending_step_idx = 0
        self._prepare_step_outcomes()
        self._cancel_action_targeting()
        self._log(f"[ACTION] Using {action.name}...")

    def _use_legendary_resistance_manual(self, entity):
        if entity.legendary_resistances_left > 0:
            entity.legendary_resistances_left -= 1
            self._log(f"[DM] {entity.name} manually expends a Legendary Resistance. ({entity.legendary_resistances_left} left)")
            self._save_undo_snapshot()

    def _use_feature_manual(self, entity, feature):
        if entity.can_use_feature(feature.name):
            entity.use_feature(feature.name)
            self._log(f"[DM] {entity.name} uses {feature.name}.")
            self._save_undo_snapshot()

    _LOG_FILTERS = [
        ("all", "ALL"),
        ("selected", "ENTITY"),
        ("damage", "DMG"),
        ("healing", "HEAL"),
        ("conditions", "COND"),
        ("rolls", "ROLLS"),
    ]

    def _log_matches_filter(self, msg, mode, sel):
        if mode == "all":
            return True
        if mode == "selected" and sel:
            return sel.name in msg
        if mode == "damage":
            ml = msg.lower()
            return "damage" in ml or "hit" in ml or "[DMG]" in msg or "CRIT" in msg or "MISS" in msg
        if mode == "healing":
            ml = msg.lower()
            return "heal" in ml or "[REGEN]" in msg
        if mode == "conditions":
            ml = msg.lower()
            return any(kw in ml for kw in ("condition", "prone", "stunned", "charmed",
                       "frightened", "restrained", "poisoned", "paralyzed", "blinded",
                       "incapacitated", "petrified", "grappled", "unconscious",
                       "invisible", "deafened", "exhaustion"))
        if mode == "rolls":
            return "[SAVE]" in msg or "[SKILL]" in msg or "rolled" in msg.lower()
        return True
    def _resolve_reaction(self, allowed):
        self._save_undo_snapshot()
        if not self.reaction_pending: return
        
        reactor = self.reaction_pending[0]
        
        if self.reaction_type == "oa" and self.pending_move:
            mover, dest_x, dest_y = self.pending_move
            
            if allowed:
                # Execute attack
                melee_action = next((a for a in reactor.stats.actions if a.range <= 5 and not a.is_multiattack), None)
                if not melee_action:
                    melee_action = Action("Opportunity Attack", "Melee", 0, "1d4", 0, "bludgeoning")
                
                self._log(f"[REACTION] {reactor.name} attacks {mover.name}!")
                
                # Roll attack
                from engine.dice import roll_attack, roll_dice_critical, roll_dice
                adv = reactor.has_attack_advantage(mover)
                dis = reactor.has_attack_disadvantage(mover, battle=self.battle)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(melee_action.attack_bonus, adv, dis)
                
                hit = total >= mover.stats.armor_class and not is_fumble
                if hit:
                    d_str = f"{melee_action.damage_dice}+{melee_action.damage_bonus}" if melee_action.damage_bonus else melee_action.damage_dice
                    dmg = roll_dice_critical(d_str) if is_crit else roll_dice(d_str)
                    dealt, broke = mover.take_damage(dmg, melee_action.damage_type)
                    self._spawn_damage_text(mover, dealt)
                    self._log(f"  -> {'CRIT!' if is_crit else 'HIT'} ({total})! Dealt {dealt} {melee_action.damage_type}.")
                    
                    # SENTINEL FEAT: Speed becomes 0 and movement stops
                    if reactor.has_feature("sentinel"):
                        self._log(f"[SENTINEL] {mover.name}'s speed becomes 0!")
                        mover.movement_left = 0
                        # Cancel the move destination (stay in current square)
                        dest_x, dest_y = mover.grid_x, mover.grid_y
                else:
                    self._log(f"  -> MISS ({total}).")
                
                reactor.reaction_used = True
            
            self.reaction_pending.pop(0)
            if not self.reaction_pending:
                mover.grid_x = dest_x
                mover.grid_y = dest_y
                self.pending_move = None
        
        elif self.reaction_type == "counterspell":
            if allowed:
                self._log(f"[REACTION] {reactor.name} uses Counterspell (Slot expended).")
                # Consume spell slot (assume lowest available >= 3)
                slot = reactor.get_slot_for_level(3)
                if slot > 0:
                    reactor.use_spell_slot(slot)
                
                reactor.reaction_used = True
                
                # Cancel the spell effect in the pending plan
                idx = self.reaction_context.get("step_idx", -1)
                if self.pending_plan and idx == self.pending_step_idx:
                    step = self.pending_plan.steps[idx]
                    step.description += " [COUNTERED]"
                    step.damage = 0
                    step.applies_condition = ""
                    step.targets = [] # No targets affected
                    self._log(f"  -> The spell fizzles!")

            self.reaction_pending.pop(0)
            
            # Auto-resume confirmation (will proceed with fizzled spell if countered)
            if not self.reaction_pending:
                self._confirm_step()

    # --- Aura Trigger Modal ---
    def _open_next_aura_modal(self):
        if self.aura_triggers:
            self.current_aura_trigger = self.aura_triggers.pop(0)
        else:
            self.current_aura_trigger = None
    def _resolve_aura(self, success):
        self._save_undo_snapshot()
        trig = self.current_aura_trigger
        target = trig["target"]
        feat = trig["feature"]
        
        if success:
            self._log(f"[SAVE] {target.name} succeeded save vs {feat.name}.")
            # Usually half damage or no effect. For now assume no effect on save for conditions.
            if feat.damage_dice:
                from engine.dice import roll_dice
                dmg = roll_dice(feat.damage_dice) // 2
                if dmg > 0:
                    dealt, _ = target.take_damage(dmg, feat.damage_type)
                    self._log(f"  -> Takes {dealt} {feat.damage_type} damage (half).")
                    self._spawn_damage_text(target, dealt)
        else:
            self._log(f"[SAVE] {target.name} FAILED save vs {feat.name}.")
            if feat.damage_dice:
                from engine.dice import roll_dice
                dmg = roll_dice(feat.damage_dice)
                dealt, _ = target.take_damage(dmg, feat.damage_type)
                self._log(f"  -> Takes {dealt} {feat.damage_type} damage.")
                self._spawn_damage_text(target, dealt)
            if feat.applies_condition:
                # Pass source entity for Frightened/Charmed auras (e.g. Pit Fiend Aura of Fear)
                aura_source = trig.get("source", None)
                target.add_condition(feat.applies_condition, save_ability=feat.save_ability,
                                     save_dc=feat.save_dc, source=aura_source)
                self._log(f"  -> Condition applied: {feat.applies_condition}")

        self._open_next_aura_modal()
    def _auto_resolve_pending_saves(self):
        """Auto-roll all pending end-of-turn saves (used in auto battle)."""
        while self.pending_saves:
            entity, cond, ability, dc = self.pending_saves.pop(0)
            bonus = entity.get_save_bonus(ability)
            raw = random.randint(1, 20)
            total = raw + bonus
            success = total >= dc
            if success:
                entity.remove_condition(cond)
                self._log(f"[SAVE] {entity.name} saves vs {cond} ({raw}+{bonus}={total} vs DC {dc}) – removed!")
            else:
                self._log(f"[SAVE] {entity.name} fails vs {cond} ({raw}+{bonus}={total} vs DC {dc})")
        self.save_modal_open = False
        self._complete_next_turn(skip_saves=False)

    def _resolve_manual_save(self, index, success):
        if index >= len(self.pending_saves): return
        entity, cond, ability, dc = self.pending_saves.pop(index)
        
        if success:
            entity.remove_condition(cond)
            self._log(f"[SAVE] {entity.name} succeeded save (Manual) and is no longer {cond}!")
        else:
            self._log(f"[SAVE] {entity.name} failed save (Manual) and remains {cond}.")
    def _set_terrain_tool(self, tool_id):
        """Set terrain tool from palette click."""
        self.terrain_tool = tool_id
        self.terrain_rect_start = None
        self.terrain_rect_preview = []
        self.terrain_drag_obj = None

    def _set_terrain_fav(self, fav_type):
        """Set selected terrain type from favorites click."""
        self.terrain_selected_type = fav_type
    def _map_save_prompt(self):
        """Save current terrain as a map file with auto-generated name."""
        import time
        name = f"map_{time.strftime('%Y%m%d_%H%M%S')}"
        self._save_map_only(name)

    def _map_clear_all(self):
        """Clear all terrain from the map."""
        self.battle.terrain = []
        self.map_save_menu_open = False
        self._log("[MAP] Cleared all terrain.")

    # ------------------------------------------------------------------ #
    # Win Probability & DM Advisor                                         #
    # ------------------------------------------------------------------ #

    def _update_win_probability(self):
        """Refresh the win probability cache."""
        if self.battle.combat_started:
            self.win_prob_cache = self.battle.get_win_probability()

    def _toggle_advisor_panel(self):
        """Toggle the DM advisor panel visibility."""
        self.show_advisor_panel = not self.show_advisor_panel
        if self.show_advisor_panel:
            self.btn_advisor.color = COLORS["success"]
            self.btn_advisor.text = "ADVSR ON"
            curr = self.battle.get_current_entity()
            if curr.is_player:
                self.dm_suggestion_cache = self.battle.get_dm_suggestion(curr)
            self._log("[ADVISOR] DM Advisor enabled. Shows AI suggestions for player turns.")
        else:
            self.btn_advisor.color = COLORS["spell"]
            self.btn_advisor.text = "ADVISOR"
            self.dm_suggestion_cache = None
            self.dm_rating_cache = None

    def _rate_player_action(self, action_type, target=None, damage_dealt=0,
                            spell_name="", moved_distance=0):
        """Rate a player's action using the DM advisor."""
        if not self.show_advisor_panel:
            return
        curr = self.battle.get_current_entity()
        if not curr.is_player:
            return
        self.dm_rating_cache = self.battle.rate_player_action(
            curr, action_type, target, damage_dealt, spell_name, moved_distance)

    def _check_battle_end(self):
        """Check if combat is over and generate report."""
        result = self.battle.check_battle_over()
        if result:
            self.battle.finalize_battle(result)
            self.battle_report = generate_battle_report(
                self.battle.stats_tracker, self.logs)
            self.battle_report_text = format_report_text(self.battle_report)
            self.report_modal_open = True
            self.auto_battle = False
            winner_str = "PLAYERS WIN!" if result == "players" else "ENEMIES WIN!"
            self._log(f"=== COMBAT OVER: {winner_str} ===")
            # Sync battle results back to campaign (if launched from campaign)
            self._sync_to_campaign()

    def _sync_to_campaign(self):
        """Sync battle results (HP, conditions, slots) back to the active campaign."""
        try:
            from engine.campaign_bridge import sync_battle_results_to_campaign, get_campaign_from_manager
            from data.campaign import save_campaign
            campaign = get_campaign_from_manager(self.manager)
            if campaign:
                sync_battle_results_to_campaign(campaign, self.battle.entities)
                save_campaign(campaign)
                self._log("[CAMPAIGN] Party state synced back to campaign (HP, conditions, slots).")
        except Exception as ex:
            self._log(f"[CAMPAIGN] Sync error: {ex}")

    def _save_battle_report(self):
        """Save the battle report to file."""
        if not self.battle_report:
            return
        saves_dir = os.path.join(os.path.dirname(__file__), "..", "saves")
        os.makedirs(saves_dir, exist_ok=True)

        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save both JSON and text
        json_path = os.path.join(saves_dir, f"report_{ts}.json")
        text_path = os.path.join(saves_dir, f"report_{ts}.txt")
        save_report(self.battle_report, json_path)
        save_report_text(self.battle_report, text_path)
        self._log(f"[REPORT] Saved to report_{ts}.json/txt")
    def _toggle_terrain_mode(self):
        self.terrain_mode = not self.terrain_mode
        self.terrain_palette_open = self.terrain_mode
        if self.terrain_mode:
            self.terrain_tool = "paint"
            self.terrain_rect_start = None
            self.terrain_rect_preview = []
            self.terrain_drag_obj = None
            self.terrain_paste_preview = False
            self.terrain_select_start = None
            self.terrain_select_end = None
            self.btn_terrain.text = "STOP PAINTING"
            self.btn_terrain.color = COLORS["warning"]
            self._log("[TERRAIN] Terrain mode ON. Tools: 1=Paint 2=Move 3=Rect 4=Elev | C=Copy V=Paste F=Favorite")
        else:
            self.btn_terrain.text = "TERRAIN"
            self.btn_terrain.color = COLORS["panel"]
            self._log("[TERRAIN] Terrain mode OFF.")

    def _cycle_terrain_tool(self):
        """Cycle through terrain tools: paint -> move -> rect -> elev."""
        tools = ["paint", "move", "rect", "elev"]
        idx = tools.index(self.terrain_tool) if self.terrain_tool in tools else 0
        self.terrain_tool = tools[(idx + 1) % len(tools)]
        self.terrain_rect_start = None
        self.terrain_rect_preview = []
        self.terrain_drag_obj = None
        self._log(f"[TERRAIN] Tool: {self.terrain_tool.upper()}")

    # --- Map Save/Load (terrain only) ---
    def _toggle_map_save_menu(self):
        self.map_save_menu_open = not self.map_save_menu_open

    def _save_map_only(self, name):
        """Save only terrain data to a map file."""
        if not name:
            self.map_save_menu_open = False
            return
        maps_dir = os.path.join(os.path.dirname(__file__), "..", "saves", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        if not name.endswith(".json"):
            name += ".json"
        filepath = os.path.join(maps_dir, name)
        data = {"terrain": [t.to_dict() for t in self.battle.terrain],
                "grid_size": self.battle.grid_size}
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        self._log(f"[MAP] Saved map to {name}")
        self.map_save_menu_open = False

    def _load_map_only(self, filepath):
        """Load only terrain data from a map file."""
        if not filepath:
            self.map_save_menu_open = False
            return
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            new_terrain = []
            for t in data.get("terrain", []):
                try:
                    new_terrain.append(TerrainObject.from_dict(t))
                except Exception as inner:
                    self._log(f"[WARN] Skipped bad terrain entry: {inner}")
            self.battle.terrain = new_terrain
            # Restore grid size if saved
            saved_gsz = data.get("grid_size")
            if isinstance(saved_gsz, int) and saved_gsz > 0:
                self.battle.grid_size = saved_gsz
            # Invalidate selections/targeting that may reference old terrain
            self.pending_plan = None
            self.pending_step_idx = 0
            self.spell_targeting = False
            self.spell_caster = None
            self._log(f"[MAP] Loaded map: {os.path.basename(filepath)} ({len(new_terrain)} tiles)")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self._log(f"[ERROR] Map load failed: {ex}")
        self.map_save_menu_open = False

    def _toggle_map_browser(self):
        self.map_browser_open = not self.map_browser_open

    def _load_premade_map(self, map_key):
        """Load a premade map, replacing current terrain."""
        try:
            from data.maps import load_map_terrain
            terrain_list = load_map_terrain(map_key)
            if not terrain_list:
                self._log(f"[ERROR] Premade map '{map_key}' is empty or missing")
                self.map_browser_open = False
                return
            self.battle.terrain = terrain_list
            # Invalidate selections/targeting that may reference old terrain
            self.pending_plan = None
            self.pending_step_idx = 0
            self.spell_targeting = False
            self.spell_caster = None
            self.map_browser_open = False
            self._log(f"[MAP] Loaded premade map: {map_key} ({len(terrain_list)} tiles)")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self._log(f"[ERROR] Premade map load failed: {ex}")
            self.map_browser_open = False
    def _open_save_modal(self):
        self.scenario_modal = ScenarioModal("save", self._perform_save)

    def _open_load_modal(self):
        self.scenario_modal = ScenarioModal("load", self._perform_load)

    def _perform_save(self, filepath):
        self.scenario_modal = None
        if not filepath: return
        try:
            self.battle.save_state(filepath)
            self._log(f"[SAVE] Saved to {os.path.basename(filepath)}")
        except Exception as ex:
            self._log(f"[ERROR] Save failed: {ex}")

    def _perform_load(self, filepath):
        self.scenario_modal = None
        if not filepath: return
        try:
            new_battle = BattleSystem.from_save(filepath, self._log)
            new_battle.log = self._log
            self.battle = new_battle
            self.selected_entity = None
            self.pending_plan = None
            self.condition_reminder = None
            self._log(f"[LOAD] Loaded {os.path.basename(filepath)}")
        except Exception as ex:
            self._log(f"[ERROR] Load failed: {ex}")

    # ------------------------------------------------------------------ #
    # Mid-battle entity add                                                #
    # ------------------------------------------------------------------ #

    def _toggle_add_entity_modal(self):
        self.add_entity_open = not self.add_entity_open
        self.add_entity_search = ""
        self.add_entity_scroll = 0

    def _add_entity_to_battle(self, stats, is_player=False):
        """Add a new entity to the active battle from the monster/hero library."""
        self._save_undo_snapshot()
        # Place near center of current view
        cx = (self.camera_x + GRID_W // 2) / self.battle.grid_size
        cy = (self.camera_y + (SCREEN_HEIGHT - TOP_BAR_H) // 2) / self.battle.grid_size
        # Offset slightly to avoid overlap
        offset = len(self.battle.entities) * 0.5
        ent = Entity(copy.deepcopy(stats), cx + offset, cy, is_player=is_player)
        # If combat already started, roll initiative
        if self.battle.combat_started:
            init_mod = stats.abilities.get_mod("dexterity")
            ent.initiative = random.randint(1, 20) + init_mod
        self.battle.entities.append(ent)
        self.selected_entity = ent
        self.add_entity_open = False
        self._log(f"[DM] Added {ent.name} to battle (Init {ent.initiative}).")
