"""
BattleEventsMixin – Event handling methods for BattleState.
Extracted from battle_state.py for UI/Logic separation (MVC).
"""
import math
import pygame
import re
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import fonts
from data.library import library
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores
from data.heroes import hero_list

from states.battle_constants import PANEL_W, TOP_BAR_H, GRID_W


class BattleEventsMixin:
    """Mixin containing event handling methods for BattleState."""


    def _handle_damage_modal_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.dmg_modal_open = False
            elif event.key == pygame.K_BACKSPACE:
                self.dmg_value_str = self.dmg_value_str[:-1]
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self._apply_damage_confirm()
            elif event.unicode.isdigit():
                if len(self.dmg_value_str) < 4:
                    self.dmg_value_str += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            w, h = 500, 400
            bx, by = cx - w//2, cy - h//2
            
            # Close if clicked outside
            if not pygame.Rect(bx, by, w, h).collidepoint(mx, my):
                self.dmg_modal_open = False
                return

            # Type buttons
            types = ["slashing", "piercing", "bludgeoning", "fire", "cold", "lightning", 
                     "acid", "poison", "necrotic", "radiant", "force", "psychic", "thunder"]
            
            start_x = bx + 20
            start_y = by + 120
            col_w, row_h = 110, 35
            for i, t in enumerate(types):
                c = i % 4
                r = i // 4
                rect = pygame.Rect(start_x + c*col_w, start_y + r*row_h, 100, 30)
                if rect.collidepoint(mx, my):
                    self.dmg_type = t

            # Numpad buttons (visual only, mostly for touch/mouse users)
            # (Skipping implementation for brevity, keyboard works)

            # Action buttons
            btn_w, btn_h = 140, 45
            btn_y = by + h - 60
            
            # Cancel
            if pygame.Rect(bx + 20, btn_y, btn_w, btn_h).collidepoint(mx, my):
                self.dmg_modal_open = False
            
            # Apply
            if pygame.Rect(bx + w - 20 - btn_w, btn_y, btn_w, btn_h).collidepoint(mx, my):
                self._apply_damage_confirm()

    # ------------------------------------------------------------------ #
    # Terrain Painting Helper                                              #
    # ------------------------------------------------------------------ #



    # ------------------------------------------------------------------ #
    # Event handling                                                       #
    # ------------------------------------------------------------------ #

    def handle_events(self, events):
        try:
            curr = self.battle.get_current_entity()
        except ValueError:
            curr = None

        for event in events:
            # Spell Targeting Interception
            if self.spell_targeting:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Only intercept if clicking on the grid area
                    if mx < GRID_W and my >= TOP_BAR_H:
                        if event.button == 1: # Left click to cast
                            self._execute_manual_spell(event.pos)
                        elif event.button == 3: # Right click to cancel
                            self._cancel_spell_targeting()
                        continue
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._cancel_spell_targeting()
                    continue

            # Action Targeting Interception
            if self.action_targeting:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if mx < GRID_W and my >= TOP_BAR_H:
                        if event.button == 1: # Left click to execute
                            self._execute_manual_action(event.pos)
                        elif event.button == 3: # Right click to cancel
                            self._cancel_action_targeting()
                        continue
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._cancel_action_targeting()
                    continue

            try:
                # Scenario Modal
                if self.scenario_modal:
                    self.scenario_modal.handle_event(event)
                    continue
                if self.notes_modal:
                    self.notes_modal.handle_event(event)
                    continue
                if self.effect_modal:
                    self.effect_modal.handle_event(event)
                    continue

                # Battle Report Modal handling
                if self.report_modal_open:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.report_modal_open = False
                        continue
                    if event.type == pygame.MOUSEWHEEL:
                        self.report_scroll = min(0, self.report_scroll + event.y * 20)
                        continue
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Check close/save button clicks via ui_click_zones
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                        continue
                    continue

                # Save Modal (End of Turn)
                if self.save_modal_open:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                        continue
                    continue

                # Shortcut: ESC to exit terrain mode / close menus
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.terrain_mode: self._toggle_terrain_mode()
                    self.ctx_open = False
                    self.roll_modal_open = False
                    self.map_save_menu_open = False

                # Terrain tool shortcuts (when in terrain mode)
                if event.type == pygame.KEYDOWN and self.terrain_mode:
                    if event.key == pygame.K_1:
                        self.terrain_tool = "paint"
                        self.terrain_rect_start = None
                        self._log("[TERRAIN] Tool: PAINT")
                    elif event.key == pygame.K_2:
                        self.terrain_tool = "move"
                        self._log("[TERRAIN] Tool: MOVE")
                    elif event.key == pygame.K_3:
                        self.terrain_tool = "rect"
                        self.terrain_rect_start = None
                        self._log("[TERRAIN] Tool: RECT")
                    elif event.key == pygame.K_4:
                        self.terrain_tool = "elev"
                        self._log("[TERRAIN] Tool: ELEV")
                    elif event.key == pygame.K_c:
                        # Start copy selection or copy if selection exists
                        if self.terrain_select_start and self.terrain_select_end:
                            self._terrain_copy_selection()
                        else:
                            self._log("[TERRAIN] Click to set selection start, then Shift+click for end. Press C again to copy.")
                    elif event.key == pygame.K_v:
                        if self.terrain_clipboard:
                            self.terrain_paste_preview = True
                            self._log("[TERRAIN] Click to paste terrain. ESC to cancel.")
                    elif event.key == pygame.K_f:
                        self._terrain_add_favorite()
                        self._log(f"[TERRAIN] Added '{self.terrain_selected_type}' to favorites.")
                    elif event.key == pygame.K_TAB:
                        self._cycle_terrain_tool()

                # Undo (Z or Ctrl+Z) - only when not in terrain mode
                if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                    if not self.terrain_mode:
                        self._undo_last_action()

                # Redo (Y or Ctrl+Y or Ctrl+Shift+Z) - only when not in terrain mode
                if event.type == pygame.KEYDOWN and event.key == pygame.K_y:
                    if not self.terrain_mode:
                        self._redo_action()

                # Hotkeys (only when no modals are open)
                if event.type == pygame.KEYDOWN and not self.terrain_mode:
                    mods = pygame.key.get_mods()

                    # Ctrl+S = Quick Save
                    if event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
                        self._perform_autosave()
                        continue

                    # H = Toggle Help Overlay
                    if event.key == pygame.K_h and not self.hp_input_active:
                        self.help_overlay_open = getattr(self, 'help_overlay_open', False)
                        self.help_overlay_open = not self.help_overlay_open
                        continue

                    # Space = Next Turn (when combat started)
                    if event.key == pygame.K_SPACE and self.battle.combat_started:
                        if not self.roll_modal_open and not self.dmg_modal_open:
                            self._do_next_turn()
                            continue

                    # N = AI Turn
                    if event.key == pygame.K_n and self.battle.combat_started:
                        self._do_ai_turn()
                        continue

                    # Quick condition hotkeys (when entity selected)
                    if self.selected_entity and not self.hp_input_active:
                        if event.key == pygame.K_p and not mods & pygame.KMOD_CTRL:
                            self._toggle_condition("Prone")
                        elif event.key == pygame.K_t:
                            self._toggle_condition("Stunned")
                        elif event.key == pygame.K_c and not mods & pygame.KMOD_CTRL:
                            self._toggle_condition("Charmed")
                        elif event.key == pygame.K_r:
                            self._toggle_condition("Restrained")
                        elif event.key == pygame.K_f:
                            self._toggle_condition("Frightened")
                        elif event.key == pygame.K_i:
                            self._toggle_condition("Invisible")
                        elif event.key == pygame.K_x:
                            self._toggle_condition("Poisoned")
                        elif event.key == pygame.K_b:
                            self._toggle_condition("Blinded")

                    # Direct HP input: minus key starts, digits continue, Enter applies
                    if self.selected_entity:
                        if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                            self.hp_input_active = True
                            self.hp_input_text = "-"
                        elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                            self.hp_input_active = True
                            self.hp_input_text = "+"
                        elif self.hp_input_active:
                            if event.unicode.isdigit() and len(self.hp_input_text) < 5:
                                self.hp_input_text += event.unicode
                            elif event.key == pygame.K_BACKSPACE:
                                self.hp_input_text = self.hp_input_text[:-1]
                                if len(self.hp_input_text) == 0:
                                    self.hp_input_active = False
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                                self._apply_hp_input()
                            elif event.key == pygame.K_ESCAPE:
                                self.hp_input_active = False
                                self.hp_input_text = ""

                    # Numpad quick damage (1-9 mapped to -1 to -9 on selected)
                    if self.selected_entity and not self.hp_input_active:
                        numpad_map = {
                            pygame.K_KP1: -1, pygame.K_KP2: -2, pygame.K_KP3: -3,
                            pygame.K_KP4: -4, pygame.K_KP5: -5, pygame.K_KP6: -6,
                            pygame.K_KP7: -7, pygame.K_KP8: -8, pygame.K_KP9: -9,
                            pygame.K_KP0: 10,  # Numpad 0 = heal 10
                        }
                        if event.key in numpad_map:
                            self._modify_hp(numpad_map[event.key])

                # Roll Result Modal - Close on any click or key
                if self.roll_modal_open:
                    if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)):
                        self.roll_modal_open = False
                    continue

                # Damage Modal
                if self.dmg_modal_open:
                    self._handle_damage_modal_event(event)
                    continue

                # Condition reminder: any click dismisses it
                if self.condition_reminder:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.condition_reminder = None
                    continue

                # Add Entity Modal
                if self.add_entity_open:
                    self._handle_add_entity_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                    continue

                # Context menu
                if self.ctx_open:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        clicked = False
                        for rect, cb, _ in self.ctx_rects:
                            if rect.collidepoint(event.pos):
                                cb()
                                clicked = True
                                break
                        self.ctx_open = False
                    continue

                # Terrain palette
                if self.terrain_palette_open:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Calculate palette bounds (matching _draw_terrain_palette)
                        pal_x, pal_y = 10, TOP_BAR_H + 10
                        pal_w = 165
                        item_h = 24
                        toolbar_h = 28
                        fav_h = 28
                        header_h = 48 + toolbar_h + fav_h
                        max_vis = (SCREEN_HEIGHT - TOP_BAR_H - 120 - toolbar_h - fav_h) // item_h
                        scroll = getattr(self, 'terrain_palette_scroll', 0)
                        pal_h = min(max_vis, len(TERRAIN_TYPES)) * item_h + 8 * 2 + header_h
                        pal_rect = pygame.Rect(pal_x, pal_y, pal_w, pal_h)

                        if pal_rect.collidepoint(event.pos):
                            # Scroll with mouse wheel
                            if event.button == 4:  # scroll up
                                self.terrain_palette_scroll = max(0, scroll - 1)
                            elif event.button == 5:  # scroll down
                                self.terrain_palette_scroll = min(
                                    len(TERRAIN_TYPES) - max_vis,
                                    scroll + 1)
                            elif event.button == 1:
                                # Check ui_click_zones first (toolbar, favorites)
                                handled = False
                                for rect, callback in self.ui_click_zones:
                                    if rect.collidepoint(event.pos):
                                        callback()
                                        handled = True
                                        break
                                if not handled:
                                    # Click on terrain type item
                                    keys = list(TERRAIN_TYPES.keys())
                                    visible = keys[scroll:scroll + max_vis]
                                    list_start_y = pal_y + 8 + header_h
                                    for i, ttype in enumerate(visible):
                                        r = pygame.Rect(pal_x + 4, list_start_y + i * item_h,
                                                        pal_w - 8, item_h - 2)
                                        if r.collidepoint(event.pos):
                                            self.terrain_selected_type = ttype
                                            break
                            continue

                        # Map save menu clicks
                        if self.map_save_menu_open and event.button == 1:
                            for rect, callback in self.ui_click_zones:
                                if rect.collidepoint(event.pos):
                                    callback()
                                    break
                            continue

                        # Middle-click on grid to toggle doors
                        if event.button == 2:
                            mx, raw_my = event.pos
                            if mx < GRID_W and raw_my >= TOP_BAR_H:
                                gx, gy = self._screen_to_grid(mx, raw_my)
                                gx, gy = int(gx), int(gy)
                                self.battle.toggle_door_at(gx, gy)
                                continue

                # Pending AI confirmation
                if self.pending_plan:
                    # Check dynamic resolution buttons
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                    
                    # Global buttons
                    if self.pending_step_idx < len(self.pending_plan.steps):
                        self.btn_confirm.handle_event(event)
                        self.btn_deny.handle_event(event)
                        self.btn_approve_all.handle_event(event)
                        self.btn_cancel_ai.handle_event(event)
                    continue

                # Pending Aura Trigger
                if self.current_aura_trigger:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                    # Block other input while modal is open
                    continue

                # Pending Reaction (Opportunity Attack)
                if self.reaction_pending:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break
                    continue

                # Player action panel
                if self.player_action_mode:
                    for i, b in enumerate(self.player_action_btns):
                        b.rect.topleft = (GRID_W + 20 + (i % 4) * 128, SCREEN_HEIGHT - 200 + (i // 4) * 42)
                        b.handle_event(event)

                # Mouse clicks on grid
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, raw_my = event.pos

                    # Check Top Bar (Initiative Cards) selection
                    if raw_my < TOP_BAR_H:
                        # Calculate dynamic start X based on Round text width (matches _draw_top_bar)
                        round_text = f"ROUND {self.battle.round}"
                        rt_w = fonts.header.size(round_text)[0]
                        round_bg_w = rt_w + 20
                        card_x = 10 + round_bg_w + 15  # 10(margin) + width + 15(gap)
                        
                        card_w, card_h = 120, 88
                        for ent in self.battle.entities:
                            if card_x > SCREEN_WIDTH - 180:
                                break
                            if pygame.Rect(card_x, 6, card_w, card_h).collidepoint(event.pos):
                                self.selected_entity = ent
                                self._center_camera_on(ent)
                                break
                            card_x += card_w + 5

                    my = raw_my - TOP_BAR_H
                    if mx < GRID_W and my >= 0:
                        gx, gy = self._screen_to_grid(mx, raw_my)
                        igx, igy = int(gx), int(gy)
                        if self.terrain_mode:
                            # Paste mode intercept
                            if self.terrain_paste_preview:
                                self._terrain_paste_at(igx, igy)
                                continue
                            # Selection mode (shift+click sets selection)
                            mods = pygame.key.get_mods()
                            if mods & pygame.KMOD_SHIFT:
                                if self.terrain_select_start is None:
                                    self.terrain_select_start = (igx, igy)
                                    self._log(f"[TERRAIN] Selection start: ({igx},{igy}). Shift+click again for end.")
                                else:
                                    self.terrain_select_end = (igx, igy)
                                    self._log(f"[TERRAIN] Selection end: ({igx},{igy}). Press C to copy.")
                                continue
                            # Normal tool behavior
                            self.drawing_button = 1
                            self._paint_terrain_at(event.pos, 1)
                        else:
                            ent = self.battle.get_entity_at(gx, gy)
                            if ent:
                                self.selected_entity = ent
                                self.dragging = ent
                                self.drag_start = (ent.grid_x, ent.grid_y)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    mx, raw_my = event.pos
                    my = raw_my - TOP_BAR_H
                    if mx < GRID_W and my >= 0:
                        gx, gy = self._screen_to_grid(mx, raw_my)
                        if self.terrain_mode:
                            # Start erasing
                            self.drawing_button = 3
                            self._paint_terrain_at(event.pos, 3)
                        else:
                            ent = self.battle.get_entity_at(gx, gy)
                            if ent:
                                self._open_ctx_menu(event.pos, ent)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.terrain_mode:
                        self.drawing_button = None
                        if self.terrain_tool == "move" and self.terrain_drag_obj:
                            self._terrain_move_release(event.pos)

                    if self.dragging:
                        mx, raw_my = event.pos
                        my = raw_my - TOP_BAR_H
                        if mx < GRID_W and my >= 0:
                            # Calculate grid position based on CENTER of the token (free placement)
                            gx, gy = self._screen_to_grid(mx - self.battle.grid_size / 2, raw_my - self.battle.grid_size / 2)

                            if not self.battle.is_occupied(gx, gy, exclude=self.dragging):
                                old_x, old_y = self.dragging.grid_x, self.dragging.grid_y

                                if not self.battle.combat_started:
                                    # Deployment phase: free placement, no OA checks
                                    self.dragging.grid_x = gx
                                    self.dragging.grid_y = gy
                                    self._log(f"[DEPLOY] {self.dragging.name} placed at ({gx:.0f}, {gy:.0f}).")
                                else:
                                    # Combat: check opportunity attacks
                                    self.dragging.grid_x = gx
                                    self.dragging.grid_y = gy
                                    oas = self.battle.check_opportunity_attacks(self.dragging, old_x, old_y)

                                    # Revert position for now
                                    self.dragging.grid_x = old_x
                                    self.dragging.grid_y = old_y

                                    if oas:
                                        self.reaction_pending = oas
                                        self.reaction_type = "oa"
                                        self.pending_move = (self.dragging, gx, gy)
                                        self._log(f"[REACTION] Movement triggered {len(oas)} opportunity attack(s)!")
                                    else:
                                        # No OA, commit move
                                        self.dragging.grid_x = gx
                                        self.dragging.grid_y = gy
                                        # Save full state for Undo
                                        self._save_undo_snapshot()

                                        dist_ft = math.hypot(gx - old_x, gy - old_y) * 5
                                        self._log(f"[MOVE] {self.dragging.name} moved {dist_ft:.0f} ft.")
                            else:
                                self._log("Cannot move: space occupied.")
                        self.dragging = None

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                    if self.terrain_mode:
                        self.drawing_button = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.terrain_mode:
                        if self.drawing_button and self.terrain_tool == "paint":
                            self._paint_terrain_at(event.pos, self.drawing_button)
                        if self.terrain_tool == "rect":
                            self._terrain_rect_update_preview(event.pos)

                # Tab clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_w = PANEL_W // len(TABS)
                    for i, tab in enumerate(TABS):
                        tab_rect = pygame.Rect(GRID_W + i * tab_w, TOP_BAR_H + 38, tab_w - 2, 30)
                        if tab_rect.collidepoint(event.pos):
                            self.active_tab = i
                            self.panel_scroll = 0

                    # Check dynamic UI zones (Conditions, Spells, Saves)
                    # We check if the click is within the visible panel area to avoid clicking hidden scrolled items
                    panel_clip_rect = pygame.Rect(GRID_W, TOP_BAR_H+68, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H - 68 - 80)
                    if panel_clip_rect.collidepoint(event.pos):
                        for rect, callback in self.ui_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break

                # Right click on panel (Spell slots increment)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    panel_clip_rect = pygame.Rect(GRID_W, TOP_BAR_H+68, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H - 68 - 80)
                    if panel_clip_rect.collidepoint(event.pos):
                        for rect, callback in self.ui_right_click_zones:
                            if rect.collidepoint(event.pos):
                                callback()
                                break

                    # HP buttons (always visible at bottom)
                    if self.selected_entity:
                        for b in self.hp_btns:
                            b.handle_event(event)
                        for b in self.init_btns:
                            b.handle_event(event)

                # Panel scroll
                if event.type == pygame.MOUSEWHEEL:
                    mx = pygame.mouse.get_pos()[0]
                    if mx > GRID_W:
                        self.panel_scroll = max(-600, min(0, self.panel_scroll + event.y * 20))
                    else:
                        # Zoom grid
                        self.battle.grid_size = max(20, min(150, self.battle.grid_size + event.y * 5))

                # Global buttons
                if not self.battle.combat_started:
                    self.btn_start.handle_event(event)
                else:
                    self.btn_next.handle_event(event)
                    if curr:
                        self.btn_ai.handle_event(event)

                self.btn_menu.handle_event(event)
                self.btn_log_pl.handle_event(event)
                self.btn_save.handle_event(event)
                self.btn_load.handle_event(event)
                self.btn_terrain.handle_event(event)
                self.btn_weather.handle_event(event)
                self.btn_undo.handle_event(event)
                self.btn_auto.handle_event(event)
                self.btn_auto_mode.handle_event(event)
                if self.auto_battle:
                    self.btn_pause.handle_event(event)
                    self.btn_speed_down.handle_event(event)
                    self.btn_speed_up.handle_event(event)
                self.btn_advisor.handle_event(event)
                self.btn_maps.handle_event(event)
                self.btn_save_map.handle_event(event)
                self.btn_add_entity.handle_event(event)

                # Map browser clicks
                if self.map_browser_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    from data.maps import get_map_names
                    maps = get_map_names()
                    bw, bh_total = 350, 50 * len(maps) + 60
                    bx = (SCREEN_WIDTH - bw) // 2
                    by = (SCREEN_HEIGHT - bh_total) // 2
                    y = by + 44
                    for key, name, desc in maps:
                        r = pygame.Rect(bx + 8, y, bw - 16, 42)
                        if r.collidepoint(event.pos):
                            self._load_premade_map(key)
                            break
                        y += 50
                    # Click outside closes
                    outer = pygame.Rect(bx, by, bw, bh_total)
                    if not outer.collidepoint(event.pos):
                        self.map_browser_open = False

                for b in self.hp_btns:
                    b.handle_event(event)
                for b in self.init_btns:
                    b.handle_event(event)

            except Exception as ex:
                import traceback
                print(f"Event error: {ex}")
                traceback.print_exc()
                self._log(f"[ERROR] {ex}")

    def _handle_add_entity_event(self, event):
        """Handle events for the add entity modal."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.add_entity_open = False
            elif event.key == pygame.K_BACKSPACE:
                self.add_entity_search = self.add_entity_search[:-1]
                self.add_entity_scroll = 0
            elif event.unicode.isprintable() and len(self.add_entity_search) < 30:
                self.add_entity_search += event.unicode
                self.add_entity_scroll = 0
        elif event.type == pygame.MOUSEWHEEL:
            all_count = len(library.get_all_monsters()) + len(hero_list)
            self.add_entity_scroll = max(0, self.add_entity_scroll - event.y * 3)
            self.add_entity_scroll = min(self.add_entity_scroll, max(0, all_count - 10))


