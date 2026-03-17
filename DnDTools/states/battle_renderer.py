"""
BattleRendererMixin – All drawing methods for BattleState.
Extracted from battle_state.py for UI/Logic separation (MVC).
"""
import pygame
import math
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, CREATURE_TYPE_COLORS, CREATURE_ICONS, SIZE_RADIUS
from ui.components import Button, Panel, fonts, hp_bar, TabBar, Badge, Divider, draw_gradient_rect, Tooltip
from data.conditions import CONDITIONS
from engine.terrain import TERRAIN_TYPES
from engine.win_probability import assess_encounter_danger

from states.battle_constants import (
    PANEL_W, TOP_BAR_H, GRID_W, TABS,
    DAMAGE_TYPE_COLORS, CONDITION_BADGES,
)


class BattleRendererMixin:
    """Mixin containing all _draw_* methods for BattleState."""


    # ------------------------------------------------------------------ #
    # Token images                                                         #
    # ------------------------------------------------------------------ #

    def _get_token_image(self, name):
        if name in self.token_cache:
            return self.token_cache[name]

        search_dir = os.path.join("data", "tokens")
        
        def find_image_path(target_name):
            if not os.path.exists(search_dir):
                return None
            # 1. Exact match with extensions
            for ext in [".png", ".jpg", ".jpeg"]:
                path = os.path.join(search_dir, target_name + ext)
                if os.path.exists(path):
                    return path
            # 2. Case-insensitive match
            try:
                target_lower = target_name.lower()
                for f in os.listdir(search_dir):
                    base, ext = os.path.splitext(f)
                    if base.lower() == target_lower and ext.lower() in [".png", ".jpg", ".jpeg"]:
                        return os.path.join(search_dir, f)
            except OSError:
                pass
            return None

        path = find_image_path(name)
        if not path:
            base_name = re.sub(r'\s+\d+$', '', name)
            if base_name != name: 
                path = find_image_path(base_name)

        img = None
        if path:
            try:
                img = pygame.image.load(path).convert_alpha()
            except Exception:
                pass

        self.token_cache[name] = img
        return img

    def _draw_token(self, screen, entity, cx, cy, radius):
        # Get creature type color tint
        ctype = entity.stats.creature_type if hasattr(entity.stats, 'creature_type') else "Humanoid"
        type_color = CREATURE_TYPE_COLORS.get(ctype, (160, 160, 160))
        type_icon = CREATURE_ICONS.get(ctype, "??")

        # Drop shadow (larger, softer)
        shadow_size = radius * 2 + 10
        shadow_surf = pygame.Surface((shadow_size, shadow_size), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 50), (shadow_size//2, shadow_size//2), radius + 3)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 30), (shadow_size//2, shadow_size//2), radius + 5)
        screen.blit(shadow_surf, (cx - shadow_size//2, cy - shadow_size//2))

        img = self._get_token_image(entity.name)
        if img:
            scaled = pygame.transform.smoothscale(img, (radius*2, radius*2))
            mask_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255,255,255,255), (radius, radius), radius)
            scaled.blit(mask_surf, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(scaled, (cx - radius, cy - radius))
            # Polished border
            if entity.is_player:
                border = (255, 215, 0)
                pygame.draw.circle(screen, border, (cx, cy), radius, 3)
                pygame.draw.circle(screen, (255, 240, 150), (cx, cy), radius + 1, 1)
            else:
                border = type_color
                pygame.draw.circle(screen, border, (cx, cy), radius, 3)
        else:
            # HP-based border color
            hp_pct = entity.hp / entity.max_hp if entity.max_hp > 0 else 0
            if entity.is_player:
                border_outer = (255, 215, 0)
                # Class-based inner color
                cls = entity.stats.character_class.lower() if entity.stats.character_class else ""
                inner = COLORS.get(cls, COLORS["player"])
            else:
                if hp_pct > 0.6:
                    border_outer = type_color
                elif hp_pct > 0.3:
                    border_outer = COLORS["warning"]
                else:
                    border_outer = COLORS["danger"]
                inner = tuple(max(0, c - 40) for c in type_color)

            if entity.has_condition("Prone"):
                pygame.draw.ellipse(screen, border_outer, (cx-radius, cy-radius//2, radius*2, radius))
                pygame.draw.ellipse(screen, COLORS["bg_dark"], (cx-radius+3, cy-radius//2+3, radius*2-6, radius-6))
                pygame.draw.ellipse(screen, inner, (cx-radius+6, cy-radius//2+6, radius*2-12, radius-12), 4)
            else:
                # Outer ring
                pygame.draw.circle(screen, border_outer, (cx, cy), radius)
                # Dark fill
                pygame.draw.circle(screen, COLORS["bg_dark"], (cx, cy), radius - 3)

                if entity.is_player:
                    # Class-colored inner fill (subtle radial gradient effect)
                    dim_inner = tuple(max(0, c // 4) for c in inner)
                    pygame.draw.circle(screen, dim_inner, (cx, cy), radius - 4)
                    # Inner colored ring (thicker for players)
                    pygame.draw.circle(screen, inner, (cx, cy), radius - 5, 5)
                    # Subtle gradient highlight at top (class-tinted)
                    highlight = pygame.Surface((radius*2, radius), pygame.SRCALPHA)
                    pygame.draw.ellipse(highlight, (*inner, 45), (4, 0, radius*2 - 8, radius - 4))
                    screen.blit(highlight, (cx - radius, cy - radius))
                else:
                    # Inner colored ring for monsters
                    pygame.draw.circle(screen, inner, (cx, cy), radius - 5, 4)
                    # Subtle gradient highlight at top
                    highlight = pygame.Surface((radius*2, radius), pygame.SRCALPHA)
                    pygame.draw.ellipse(highlight, (*inner, 30), (4, 0, radius*2 - 8, radius - 4))
                    screen.blit(highlight, (cx - radius, cy - radius))

            # Creature type icon + initials
            if entity.is_player:
                # Show class abbreviation for players
                cls_name = entity.stats.character_class[:3].upper() if entity.stats.character_class else entity.name[:2].upper()
                display_text = cls_name
            else:
                # Show creature type icon for monsters
                display_text = type_icon

            ts = fonts.small_bold.render(display_text, True, (0, 0, 0))
            # Use bright class color for player text, white for monsters
            if entity.is_player:
                text_col = tuple(min(255, c + 80) for c in inner)
            else:
                text_col = (240, 240, 240)
            tf = fonts.small_bold.render(display_text, True, text_col)
            tx = cx - tf.get_width() // 2
            ty = cy - tf.get_height() // 2
            for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
                screen.blit(ts, (tx+ox, ty+oy))
            screen.blit(tf, (tx, ty))

            # Name label below token
            name_label = entity.name[:12]
            nl = fonts.tiny.render(name_label, True, COLORS["text_main"])
            nl_bg = pygame.Surface((nl.get_width() + 6, nl.get_height() + 2), pygame.SRCALPHA)
            nl_bg.fill((0, 0, 0, 140))
            screen.blit(nl_bg, (cx - nl.get_width()//2 - 3, cy + radius + 12))
            screen.blit(nl, (cx - nl.get_width()//2, cy + radius + 13))

            # CR badge for monsters (bottom-right of token)
            if not entity.is_player and entity.stats.challenge_rating:
                cr = entity.stats.challenge_rating
                cr_str = f"CR{cr:.3g}" if cr < 1 else f"CR{int(cr)}"
                badge_f = fonts.tiny.render(cr_str, True, (255, 220, 100))
                bx = cx + radius - badge_f.get_width()
                by = cy + radius - badge_f.get_height() + 2
                badge_bg = pygame.Surface((badge_f.get_width() + 6, badge_f.get_height() + 2), pygame.SRCALPHA)
                pygame.draw.rect(badge_bg, (0, 0, 0, 200), (0, 0, badge_bg.get_width(), badge_bg.get_height()), border_radius=3)
                screen.blit(badge_bg, (bx - 3, by - 1))
                screen.blit(badge_f, (bx, by))

        # Concentration ring (animated teal pulse)
        if entity.concentrating_on:
            pulse = int(math.sin(pygame.time.get_ticks() * 0.005) * 30 + 225)
            conc_color = (COLORS["concentration"][0], COLORS["concentration"][1], COLORS["concentration"][2])
            pygame.draw.circle(screen, conc_color, (cx, cy), radius + 5, 2)
            # Spell name below concentration ring
            sp_name = entity.concentrating_on.name[:10]
            sn = fonts.tiny.render(sp_name, True, COLORS["concentration"])
            screen.blit(sn, (cx - sn.get_width()//2, cy - radius - 14))

        # Condition badges (individual, arranged around top of token)
        if entity.conditions:
            cond_list = list(entity.conditions.keys()) if isinstance(entity.conditions, dict) else list(entity.conditions)
            badge_w = 22
            badge_h = 12
            total_w = len(cond_list) * (badge_w + 2)
            start_x = cx - total_w // 2
            by = cy - radius - badge_h - 2
            for i, cond_name in enumerate(cond_list):
                bx = start_x + i * (badge_w + 2)
                abbr, col = CONDITION_BADGES.get(cond_name, (cond_name[:3].upper(), (170, 90, 245)))
                # Badge background
                badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
                pygame.draw.rect(badge_surf, (*col, 200), (0, 0, badge_w, badge_h), border_radius=3)
                pygame.draw.rect(badge_surf, (255, 255, 255, 120), (0, 0, badge_w, badge_h), 1, border_radius=3)
                screen.blit(badge_surf, (bx, by))
                # Badge text
                bt = fonts.tiny.render(abbr, True, (255, 255, 255))
                screen.blit(bt, (bx + badge_w // 2 - bt.get_width() // 2, by + badge_h // 2 - bt.get_height() // 2))

        # Death Save Display (below token for dying players)
        if entity.is_player and entity.hp <= 0 and entity.death_save_failures < 3 and not entity.is_stable:
            ds_y = cy + radius + 4
            for i in range(3):
                px = cx - 15 + i * 12
                color = (0, 220, 50) if i < entity.death_save_successes else (50, 50, 50)
                pygame.draw.circle(screen, color, (px, ds_y), 5)
                pygame.draw.circle(screen, (100, 100, 100), (px, ds_y), 5, 1)
            for i in range(3):
                px = cx - 15 + i * 12
                color = (230, 40, 40) if i < entity.death_save_failures else (50, 50, 50)
                pygame.draw.circle(screen, color, (px, ds_y + 13), 5)
                pygame.draw.circle(screen, (100, 100, 100), (px, ds_y + 13), 5, 1)
            if entity.death_save_history:
                hist_str = " ".join(entity.death_save_history[-5:])
                ht = fonts.tiny.render(hist_str, True, (200, 200, 200))
                screen.blit(ht, (cx - ht.get_width()//2, ds_y + 22))
        elif entity.is_player and entity.is_stable and entity.hp <= 0:
            st = fonts.small_bold.render("STABLE", True, (0, 220, 120))
            screen.blit(st, (cx - st.get_width()//2, cy + radius + 4))

        # Rage indicator (pulsing red glow)
        if hasattr(entity, 'rage_active') and entity.rage_active:
            pulse = int(math.sin(pygame.time.get_ticks() * 0.008) * 40 + 200)
            rage_surf = pygame.Surface((radius*2+20, radius*2+20), pygame.SRCALPHA)
            pygame.draw.circle(rage_surf, (255, 30, 0, min(pulse, 80)), (radius+10, radius+10), radius + 8)
            pygame.draw.circle(rage_surf, (255, 50, 20, min(pulse, 50)), (radius+10, radius+10), radius + 6)
            screen.blit(rage_surf, (cx - radius - 10, cy - radius - 10))

        # Summon indicator (cyan ring with timer)
        if hasattr(entity, 'is_summon') and entity.is_summon:
            pygame.draw.circle(screen, (0, 200, 200), (cx, cy), radius + 5, 2)
            rnds = fonts.tiny.render(f"{entity.summon_rounds_left}r", True, (0, 200, 200))
            screen.blit(rnds, (cx - rnds.get_width()//2, cy + radius + 3))

        # Marked target indicator (crosshair overlay)
        if hasattr(entity, 'is_marked') and entity.is_marked:
            xh_color = (255, 80, 80)
            pygame.draw.line(screen, xh_color, (cx - radius + 3, cy), (cx + radius - 3, cy), 1)
            pygame.draw.line(screen, xh_color, (cx, cy - radius + 3), (cx, cy + radius - 3), 1)

    # ------------------------------------------------------------------ #
    # Dice Rolling Helpers                                                 #
    # ------------------------------------------------------------------ #



    # ------------------------------------------------------------------ #
    # Drawing                                                              #
    # ------------------------------------------------------------------ #

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        mp = pygame.mouse.get_pos()
        
        # Safely get current entity
        try:
            curr = self.battle.get_current_entity()
        except ValueError:
            curr = None
            
        sel = self.selected_entity or curr

        if curr:
            self._draw_top_bar(screen, curr)
        else:
            # Minimal top bar if no entities
            self.btn_menu.draw(screen, mp)

        self._draw_grid(screen)
        self._draw_terrain(screen)
        self._draw_weather(screen)
        
        if curr:
            self._draw_aoe_overlays(screen)
            self._draw_entities(screen, curr, sel)
            self._draw_drag(screen)
        elif not self.battle.entities:
            # Draw empty battle message
            msg = fonts.title.render("Battle Empty", True, COLORS["text_dim"])
            screen.blit(msg, (GRID_W//2 - msg.get_width()//2, SCREEN_HEIGHT//2))

        for fx in self.impact_flashes:
            fx.draw(screen, self._grid_to_screen, self.battle.grid_size)
        for ft in self.floating_texts:
            ft.draw(screen, self._grid_to_screen, self.battle.grid_size)
        self._draw_grid_buttons(screen, mp)
        
        if curr:
            self._draw_panel(screen, curr, sel, mp)
            self._draw_bottom_bar(screen, curr, mp)

        if not self.battle.combat_started:
            # Draw Deployment Banner
            ban = fonts.title.render("DEPLOYMENT PHASE", True, COLORS["accent"])
            screen.blit(ban, (GRID_W//2 - ban.get_width()//2, TOP_BAR_H + 30))

        # Turn Banner
        if self.turn_banner_timer > 0:
            alpha = 255
            if self.turn_banner_timer < 30:
                alpha = int(255 * (self.turn_banner_timer / 30))
            
            # Draw centered banner
            is_ai_player = "[AI]" in self.turn_banner_text
            banner_color = (120, 180, 255) if is_ai_player else (255, 255, 255)
            txt = fonts.title.render(self.turn_banner_text, True, banner_color)
            txt.set_alpha(alpha)

            # Background strip - blue tint for AI player
            bg_h = 80
            bg_y = SCREEN_HEIGHT // 2 - bg_h // 2 - 100
            s = pygame.Surface((GRID_W, bg_h), pygame.SRCALPHA)
            bg_color = (20, 40, 80, int(180 * (alpha/255))) if is_ai_player else (0, 0, 0, int(180 * (alpha/255)))
            s.fill(bg_color)
            screen.blit(s, (0, bg_y))
            screen.blit(txt, (GRID_W//2 - txt.get_width()//2, bg_y + bg_h//2 - txt.get_height()//2))

        if self.terrain_palette_open:
            self._draw_terrain_palette(screen, mp)
            self._draw_terrain_overlays(screen, mp)
        if self.map_save_menu_open:
            self._draw_map_save_menu(screen, mp)
        if self.map_browser_open:
            self._draw_map_browser(screen, mp)
        if self.add_entity_open:
            self._draw_add_entity_modal(screen, mp)
        if self.condition_reminder:
            self._draw_condition_reminder(screen, mp)
        if self.pending_plan:
            self._draw_ai_confirm_dialog(screen, mp)
        if self.player_action_mode:
            self._draw_player_action_panel(screen, mp)
        if self.dmg_modal_open:
            self._draw_damage_modal(screen, mp)
        if self.roll_modal_open:
            self._draw_roll_result_modal(screen)
        if self.reaction_pending:
            self._draw_reaction_modal(screen, mp)
        if self.current_aura_trigger:
            self._draw_aura_highlight(screen)
            self._draw_aura_modal(screen, mp)
        if self.ctx_open:
            self._draw_ctx_menu(screen, mp)
        if self.spell_targeting:
            self._draw_spell_targeting_overlay(screen, mp)
        if self.action_targeting:
            self._draw_action_targeting_overlay(screen, mp)

        if self.scenario_modal:
            self.scenario_modal.draw(screen, mp)
        if self.notes_modal:
            self.notes_modal.draw(screen, mp)
        if self.effect_modal:
            self.effect_modal.draw(screen, mp)
        
        self._draw_hover_info(screen, mp)

        # Draw tooltip last so it's on top of everything
        if self.active_tooltip:
            self._draw_tooltip(screen)

        # Battle Report Modal (on top of everything)
        if self.report_modal_open:
            self._draw_battle_report_modal(screen)

        if self.save_modal_open:
            self._draw_save_modal(screen, mp)

    # --- Top bar ---
    def _draw_top_bar(self, screen, curr):
        # Top bar background with subtle gradient
        draw_gradient_rect(screen, (0, 0, SCREEN_WIDTH, TOP_BAR_H),
                           COLORS["panel_header"], COLORS["panel_dark"])
        pygame.draw.line(screen, COLORS["border_light"], (0, TOP_BAR_H), (SCREEN_WIDTH, TOP_BAR_H), 2)

        # Round counter with styled badge
        round_text = f"ROUND {self.battle.round}"
        rt = fonts.header.render(round_text, True, COLORS["accent"])
        # Round badge background
        round_bg_w = rt.get_width() + 20
        round_bg = pygame.Rect(10, TOP_BAR_H//2 - rt.get_height()//2 - 4, round_bg_w, rt.get_height() + 8)
        pygame.draw.rect(screen, COLORS["accent_dim"], round_bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["accent"], round_bg, 1, border_radius=6)
        screen.blit(rt, (20, TOP_BAR_H//2 - rt.get_height()//2))

        # TaleSpire Indicator
        if pygame.time.get_ticks() - self.ts_last_update < 3000:
            ts_lbl = fonts.tiny.render("TaleSpire Linked", True, COLORS["success"])
            screen.blit(ts_lbl, (SCREEN_WIDTH - 130, 12))
            # Pulsing green dot
            pulse = int(math.sin(pygame.time.get_ticks() * 0.004) * 2 + 5)
            pygame.draw.circle(screen, COLORS["success"], (SCREEN_WIDTH - 140, 19), pulse)

        self.btn_menu.draw(screen, pygame.mouse.get_pos())

        # Initiative cards
        card_x = round_bg.right + 15
        card_w, card_h = 120, 88
        for i, ent in enumerate(self.battle.entities):
            if card_x > SCREEN_WIDTH - 180:
                break
            is_curr = (ent == curr) and self.battle.combat_started

            # Card colors based on entity type
            if ent.is_lair:
                bg_top = (65, 40, 85)
                bg_bot = (50, 30, 65)
            elif is_curr:
                bg_top = (50, 70, 120)
                bg_bot = (35, 50, 90)
            elif ent.is_player:
                bg_top = (35, 45, 55)
                bg_bot = (28, 35, 42)
            else:
                bg_top = (45, 38, 38)
                bg_bot = (35, 28, 28)

            bord = COLORS["accent"] if is_curr else COLORS["border"]
            r = pygame.Rect(card_x, 6, card_w, card_h)
            draw_gradient_rect(screen, r, bg_top, bg_bot, border_radius=8)
            # Active glow
            if is_curr:
                glow = pygame.Surface((card_w + 4, card_h + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*COLORS["accent"], 40), (0, 0, card_w + 4, card_h + 4), border_radius=10)
                screen.blit(glow, (card_x - 2, 4))
            pygame.draw.rect(screen, bord, r, 2 if is_curr else 1, border_radius=8)

            # Dead overlay
            if ent.hp <= 0:
                s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 160))
                screen.blit(s, (card_x, 6))
                # Skull indicator
                skull = fonts.body_bold.render("X", True, COLORS["danger"])
                screen.blit(skull, (card_x + card_w//2 - skull.get_width()//2,
                                    6 + card_h//2 - skull.get_height()//2))

            # HP bar (polished)
            hp_bar.draw(screen, card_x + card_w//2, 78, card_w - 10, ent.hp, ent.max_hp, height=6)

            # Name
            name_col = COLORS["text_main"]
            if ent.is_lair:
                name_col = COLORS["legendary"]
            elif ent.is_player:
                name_col = COLORS["player"]
            ns = fonts.tiny.render(ent.name[:13], True, name_col)
            screen.blit(ns, (card_x + 5, 10))

            # Initiative number (large)
            is_ = fonts.header.render(str(ent.initiative), True, COLORS["text_bright"])
            screen.blit(is_, (card_x + 5, 24))

            # HP text
            pct = max(0, ent.hp / ent.max_hp) if ent.max_hp > 0 else 0
            hp_c = COLORS["hp_full"] if pct > 0.5 else COLORS["hp_mid"] if pct > 0.25 else COLORS["hp_low"]
            hp_s = fonts.tiny.render(f"{ent.hp}/{ent.max_hp}", True, hp_c)
            screen.blit(hp_s, (card_x + 5, 54))

            # Status icons (right side)
            icon_x = card_x + card_w - 12
            icon_y = 14
            if ent.action_used:
                pygame.draw.circle(screen, COLORS["danger"], (icon_x, icon_y), 4)
                at = fonts.tiny.render("A", True, (255,255,255))
                screen.blit(at, (icon_x - at.get_width()//2, icon_y - at.get_height()//2))
                icon_x -= 12
            if ent.reaction_used:
                pygame.draw.circle(screen, COLORS["reaction"], (icon_x, icon_y), 4)
                icon_x -= 12
            if ent.concentrating_on:
                pygame.draw.circle(screen, COLORS["concentration"], (icon_x, icon_y), 4)
                ct = fonts.tiny.render("C", True, (0,0,0))
                screen.blit(ct, (icon_x - ct.get_width()//2, icon_y - ct.get_height()//2))

            # Conditions indicator
            if ent.conditions:
                cond_txt = fonts.tiny.render(f"{len(ent.conditions)} cond", True, COLORS["spell"])
                screen.blit(cond_txt, (card_x + card_w - cond_txt.get_width() - 4, 54))

            card_x += card_w + 5

    # --- Grid ---
    def _draw_grid(self, screen):
        gsz = self.battle.grid_size

        # Grid background
        grid_bg = pygame.Rect(0, TOP_BAR_H, GRID_W, SCREEN_HEIGHT - TOP_BAR_H)
        screen.fill(COLORS["bg_dark"], grid_bg)

        # Draw grid lines with alternating subtle tones
        start_x = int(self.camera_x // gsz) * gsz
        sx = start_x - self.camera_x
        col_idx = int(self.camera_x // gsz)
        while sx < GRID_W:
            if sx >= 0:
                # Every 5th line is brighter (25ft = 5 squares)
                is_major = (col_idx % 5 == 0)
                color = COLORS["border"] if is_major else COLORS["grid_line"]
                width = 1
                pygame.draw.line(screen, color, (int(sx), TOP_BAR_H), (int(sx), SCREEN_HEIGHT), width)
            sx += gsz
            col_idx += 1

        start_y = int(self.camera_y // gsz) * gsz
        sy = start_y - self.camera_y + TOP_BAR_H
        row_idx = int(self.camera_y // gsz)
        while sy < SCREEN_HEIGHT:
            if sy >= TOP_BAR_H:
                is_major = (row_idx % 5 == 0)
                color = COLORS["border"] if is_major else COLORS["grid_line"]
                pygame.draw.line(screen, color, (0, int(sy)), (GRID_W, int(sy)), 1)
            sy += gsz
            row_idx += 1

    # --- Terrain tiles ---
    def _draw_terrain(self, screen):
        gsz = self.battle.grid_size
        ticks = pygame.time.get_ticks()
        for t in self.battle.terrain:
            rx, ry = self._grid_to_screen(t.grid_x, t.grid_y)
            rw = t.width * gsz
            rh = t.height * gsz
            # Filled tile
            s = pygame.Surface((rw, rh), pygame.SRCALPHA)
            r, g, b = t.color

            # Animated VFX for spell terrain
            if t.is_spell_terrain:
                self._draw_spell_terrain_vfx(s, t, rw, rh, ticks)
            else:
                s.fill((r, g, b, 200))

            screen.blit(s, (rx, ry))
            # Border color: brighter for elevated, darker for lowered
            if t.is_spell_terrain:
                # Pulsing border for spell terrain
                pulse = int(20 * math.sin(ticks * 0.004 + hash(t.spell_name) * 0.1))
                border_color = tuple(min(255, max(0, c + 60 + pulse)) for c in t.color)
            elif t.elevation > 0:
                border_color = (200, 200, 255)  # blue-ish for elevated
            elif t.elevation < 0:
                border_color = (100, 50, 50)    # dark red for pits/chasms
            else:
                border_color = tuple(min(255, c+40) for c in t.color)
            pygame.draw.rect(screen, border_color, (rx, ry, rw, rh), 2)
            # Label (top-left)
            lbl_text = t.label[:8]
            lbl = fonts.tiny.render(lbl_text, True, (255, 255, 255))
            screen.blit(lbl, (rx + 2, ry + 2))
            # Spell owner indicator for spell terrain
            if t.is_spell_terrain and t.spell_owner:
                owner_txt = fonts.tiny.render(t.spell_owner[:6], True, (200, 200, 255))
                screen.blit(owner_txt, (rx + 2, ry + 12))
            # Elevation indicator (top-right)
            if t.elevation != 0:
                elev_color = (180, 200, 255) if t.elevation > 0 else (255, 150, 150)
                elev_txt = fonts.tiny.render(f"{t.elevation:+d}ft", True, elev_color)
                screen.blit(elev_txt, (rx + rw - elev_txt.get_width() - 2, ry + 2))
            # Door state indicator
            if t.is_door:
                door_txt = "OPEN" if t.door_open else "SHUT"
                door_color = (100, 255, 100) if t.door_open else (255, 100, 100)
                dt = fonts.tiny.render(door_txt, True, door_color)
                screen.blit(dt, (rx + rw//2 - dt.get_width()//2, ry + rh//2 - 6))
            # Hazard indicator (bottom-left)
            if t.is_hazard:
                hz = fonts.tiny.render(t.hazard_damage, True, (255, 220, 0))
                screen.blit(hz, (rx + 2, ry + gsz - 16))
            # LOS blocking indicator
            if t.blocks_los and not t.is_door:
                los_mark = fonts.tiny.render("LOS", True, (255, 80, 80))
                screen.blit(los_mark, (rx + rw - los_mark.get_width() - 2, ry + rh - 14))

    def _draw_spell_terrain_vfx(self, surface, terrain, rw, rh, ticks):
        """Draw animated VFX for spell-created terrain tiles."""
        tt = terrain.terrain_type
        r, g, b = terrain.color
        t_sec = ticks * 0.001  # seconds

        if tt == "darkness":
            # Deep pulsing darkness
            pulse = int(15 * math.sin(t_sec * 2.0 + terrain.grid_x * 0.5))
            surface.fill((max(0, r + pulse), max(0, g + pulse), max(0, b + pulse), 220))
            # Dark swirl particles
            for i in range(3):
                px = int((rw * 0.5) + math.sin(t_sec * 1.5 + i * 2.1) * rw * 0.3)
                py = int((rh * 0.5) + math.cos(t_sec * 1.2 + i * 1.7) * rh * 0.3)
                sz = 3 + int(2 * math.sin(t_sec * 2 + i))
                pygame.draw.circle(surface, (20, 10, 30, 150), (px, py), sz)

        elif tt == "fog_cloud":
            # Drifting translucent fog
            alpha = 140 + int(30 * math.sin(t_sec * 0.8 + terrain.grid_y * 0.3))
            surface.fill((r, g, b, alpha))
            # Fog wisps
            for i in range(2):
                wx = int((t_sec * 8 + i * 20 + terrain.grid_x * 10) % rw)
                wy = int(rh * 0.3 + i * rh * 0.3)
                pygame.draw.ellipse(surface, (220, 220, 230, 60),
                                    (wx - 8, wy - 3, 16, 6))

        elif tt == "wall_fire":
            # Flickering fire
            flicker = int(40 * math.sin(t_sec * 8 + terrain.grid_x * 2.0))
            surface.fill((min(255, r + flicker), max(0, g - 10 + flicker // 2), 0, 200))
            # Fire particles
            for i in range(4):
                px = int(rw * (0.2 + 0.6 * ((i + t_sec * 3) % 1.0)))
                py = int(rh * (0.8 - 0.6 * ((i * 0.3 + t_sec * 2) % 1.0)))
                sz = 2 + int(2 * math.sin(t_sec * 5 + i * 1.5))
                pygame.draw.circle(surface, (255, 200, 50, 180), (px, py), sz)

        elif tt == "wall_thorns":
            # Thorny green-brown
            pulse = int(10 * math.sin(t_sec * 1.5 + terrain.grid_x))
            surface.fill((r + pulse, g + pulse, b, 200))
            # Thorn spikes
            for i in range(3):
                bx = int(rw * (0.2 + i * 0.3))
                by = int(rh * 0.5 + math.sin(t_sec + i) * rh * 0.2)
                pygame.draw.line(surface, (80, 60, 20, 200),
                                 (bx, by), (bx + 4, by - 6), 2)

        elif tt == "spike_growth":
            # Shimmering green spikes
            pulse = int(15 * math.sin(t_sec * 2.5 + terrain.grid_x * 0.7))
            surface.fill((r, g + pulse, b, 180))
            # Spike glints
            for i in range(2):
                sx = int(rw * (0.3 + i * 0.4))
                sy = int(rh * (0.3 + math.sin(t_sec * 3 + i * 2) * 0.2))
                pygame.draw.circle(surface, (200, 255, 150, 160), (sx, sy), 2)

        elif tt == "spirit_guardians":
            # Orbiting golden light
            surface.fill((r, g, b, 140))
            for i in range(3):
                angle = t_sec * 2.0 + i * 2.094
                px = int(rw * 0.5 + math.cos(angle) * rw * 0.3)
                py = int(rh * 0.5 + math.sin(angle) * rh * 0.3)
                pygame.draw.circle(surface, (255, 255, 180, 200), (px, py), 3)

        elif tt == "moonbeam":
            # Silvery light beam with shimmer
            shimmer = int(30 * math.sin(t_sec * 3.0))
            surface.fill((min(255, r + shimmer), min(255, g + shimmer), 255, 160))
            # Light rays
            cx, cy = rw // 2, rh // 2
            for i in range(4):
                angle = t_sec * 1.5 + i * 1.57
                ex = int(cx + math.cos(angle) * rw * 0.4)
                ey = int(cy + math.sin(angle) * rh * 0.4)
                pygame.draw.line(surface, (240, 240, 255, 100), (cx, cy), (ex, ey), 1)

        elif tt == "web":
            # Sticky web pattern
            surface.fill((r, g, b, 160))
            # Web strands
            cx, cy = rw // 2, rh // 2
            for i in range(6):
                angle = i * 1.047
                ex = int(cx + math.cos(angle) * rw * 0.45)
                ey = int(cy + math.sin(angle) * rh * 0.45)
                pygame.draw.line(surface, (230, 230, 230, 120), (cx, cy), (ex, ey), 1)

        elif tt in ("cloudkill", "stinking_cloud"):
            # Toxic drifting cloud
            alpha = 150 + int(25 * math.sin(t_sec * 1.2 + terrain.grid_x * 0.4))
            surface.fill((r, g, b, alpha))
            for i in range(2):
                px = int((t_sec * 6 + i * 15 + terrain.grid_x * 8) % rw)
                py = int(rh * 0.4 + i * rh * 0.2)
                pygame.draw.ellipse(surface, (min(255, r + 40), min(255, g + 20), b, 80),
                                    (px - 6, py - 3, 12, 6))

        elif tt == "sleet_storm":
            # Icy sleet particles
            alpha = 160 + int(20 * math.sin(t_sec * 1.8))
            surface.fill((r, g, b, alpha))
            for i in range(3):
                sx = int((t_sec * 12 + i * 11 + terrain.grid_x * 7) % rw)
                sy = int((t_sec * 8 + i * 9 + terrain.grid_y * 5) % rh)
                pygame.draw.circle(surface, (220, 230, 255, 140), (sx, sy), 2)

        elif tt == "entangle":
            # Writhing vines
            pulse = int(10 * math.sin(t_sec * 1.0 + terrain.grid_x * 0.8))
            surface.fill((r + pulse, g + pulse, b, 190))
            for i in range(2):
                vx = int(rw * (0.3 + i * 0.4))
                vy = int(rh * 0.5 + math.sin(t_sec * 1.5 + i * 2.5) * rh * 0.25)
                pygame.draw.circle(surface, (30, 80, 20, 160), (vx, vy), 3)

        elif tt == "silence":
            # Subtle shimmer indicating silence zone
            alpha = 120 + int(20 * math.sin(t_sec * 0.6))
            surface.fill((r, g, b, alpha))
            # Muted symbol
            cx, cy = rw // 2, rh // 2
            pygame.draw.circle(surface, (100, 100, 140, 80), (cx, cy), min(rw, rh) // 3, 1)

        else:
            # Fallback for unknown spell terrain
            surface.fill((r, g, b, 200))

    # --- Weather Effects ---
    def _draw_weather(self, screen):
        w = self.battle.weather
        if w == "Clear":
            return

        if w == "Fog":
            # Layered fog overlay with subtle drift
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((200, 200, 220, 35))
            screen.blit(s, (0, 0))
            # Drifting fog patches
            t = pygame.time.get_ticks() * 0.001
            for i in range(5):
                fx = int((t * 15 + i * 250) % (GRID_W + 200)) - 100
                fy = TOP_BAR_H + 100 + i * 120
                patch = pygame.Surface((300, 80), pygame.SRCALPHA)
                pygame.draw.ellipse(patch, (210, 210, 230, 18), (0, 0, 300, 80))
                screen.blit(patch, (fx, fy))
            return

        # Draw persistent particles (Rain / Ash)
        for p in self.weather_particles:
            alpha = min(p.color[3], int(255 * min(p.life / 15.0, 1.0)))
            if w == "Rain":
                end_x = int(p.x + p.vx * 2)
                end_y = int(p.y + p.vy * 2)
                col = (p.color[0], p.color[1], p.color[2])
                line_surf = pygame.Surface((abs(end_x - int(p.x)) + 4, abs(end_y - int(p.y)) + 4), pygame.SRCALPHA)
                ox = 2 - min(0, end_x - int(p.x))
                oy = 2 - min(0, end_y - int(p.y))
                pygame.draw.line(line_surf, (*col, alpha),
                                 (ox, oy),
                                 (ox + end_x - int(p.x), oy + end_y - int(p.y)), 1)
                screen.blit(line_surf, (min(int(p.x), end_x) - 2, min(int(p.y), end_y) - 2))
            elif w == "Ash":
                ash_surf = pygame.Surface((p.size * 2 + 2, p.size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ash_surf, (*p.color[:3], alpha),
                                   (p.size + 1, p.size + 1), p.size)
                screen.blit(ash_surf, (int(p.x) - p.size - 1, int(p.y) - p.size - 1))

    # --- AOE spell overlays ---
    def _draw_aoe_overlays(self, screen):
        if not self.pending_plan:
            return
        steps = self.pending_plan.steps
        idx = self.pending_step_idx
        if idx >= len(steps):
            return
        step = steps[idx]
        
        # Determine AoE properties from Spell OR Action
        radius = 0
        shape = ""
        name = ""
        dtype = ""
        
        if step.spell:
            radius = step.spell.aoe_radius
            shape = step.spell.aoe_shape
            name = step.spell.name
            dtype = step.spell.damage_type
        elif step.action and step.action.aoe_radius > 0:
            radius = step.action.aoe_radius
            shape = step.action.aoe_shape
            name = step.action.name
            dtype = step.action.damage_type
            
        if radius <= 0 or not step.aoe_center:
            return

        gsz = self.battle.grid_size
        cx_grid, cy_grid = step.aoe_center
        sx, sy = self._grid_to_screen(cx_grid, cy_grid)
        
        # For Cone, origin is attacker. For Sphere, origin is target point.
        origin_x, origin_y = cx_grid, cy_grid
        if shape == "cone" and step.attacker:
            size = step.attacker.size_in_squares
            origin_x = step.attacker.grid_x + size / 2.0
            origin_y = step.attacker.grid_y + size / 2.0
            sx, sy = self._grid_to_screen(origin_x, origin_y)

        cx_px = int(sx)
        cy_px = int(sy)
        radius_px = int(radius / 5 * gsz)

        # Semi-transparent overlay
        aoe_surf = pygame.Surface((radius_px * 2 + 4, radius_px * 2 + 4), pygame.SRCALPHA)
        if dtype == "fire":
            color = (255, 80, 20, 60)
            border = (255, 140, 0, 200)
        elif dtype == "cold":
            color = (80, 180, 255, 60)
            border = (140, 210, 255, 200)
        elif dtype == "lightning":
            color = (200, 200, 50, 60)
            border = (255, 255, 100, 200)
        elif dtype in ("necrotic", "poison"):
            color = (100, 50, 150, 60)
            border = (170, 80, 220, 200)
        else:
            color = (100, 100, 200, 60)
            border = (150, 150, 255, 200)

        if shape == "cone":
            # Calculate angle from attacker to target point
            dx = cx_grid - origin_x
            dy = cy_grid - origin_y
            angle_rad = math.atan2(dy, dx)
            
            pts = [(radius_px + 2, radius_px + 2)]
            # 60 degree cone
            for deg in range(-30, 31, 10):
                rad = angle_rad + math.radians(deg)
                px = radius_px + 2 + math.cos(rad) * radius_px
                py = radius_px + 2 + math.sin(rad) * radius_px
                pts.append((px, py))
            if len(pts) >= 3:
                pygame.draw.polygon(aoe_surf, color, pts)
                pygame.draw.lines(aoe_surf, border, True, pts, 2)
        else:
            pygame.draw.circle(aoe_surf, color, (radius_px + 2, radius_px + 2), radius_px)
            pygame.draw.circle(aoe_surf, border, (radius_px + 2, radius_px + 2), radius_px, 3)

        screen.blit(aoe_surf, (cx_px - radius_px - 2, cy_px - radius_px - 2))

        # Label
        lbl = fonts.tiny.render(f"{name} ({radius}ft)", True, (255, 255, 200))
        screen.blit(lbl, (cx_px - lbl.get_width() // 2, cy_px - radius_px - 20))

    # --- Grid-area utility buttons (Save/Load/Terrain) ---
    def _draw_grid_buttons(self, screen, mp):
        for b in (self.btn_save, self.btn_load, self.btn_terrain, self.btn_weather, self.btn_undo, self.btn_auto, self.btn_advisor, self.btn_maps, self.btn_save_map, self.btn_add_entity):
            b.draw(screen, mp)
        # Auto mode button always visible next to AUTO
        self.btn_auto_mode.draw(screen, mp)
        # Auto battle controls (pause + speed) - only visible when auto battle is active
        if self.auto_battle:
            self.btn_pause.draw(screen, mp)
            self.btn_speed_down.draw(screen, mp)
            self.btn_speed_lbl.draw(screen, mp)
            self.btn_speed_up.draw(screen, mp)
        # Terrain mode indicator
        if self.terrain_mode:
            tc = COLORS["warning"]
            pygame.draw.rect(screen, tc, self.btn_terrain.rect, 2, border_radius=5)
            tool_names = {"paint": "PAINT", "move": "MOVE", "rect": "RECT", "elev": "ELEV"}
            tool_label = tool_names.get(self.terrain_tool, "PAINT")
            sel = fonts.tiny.render(f"[{self.terrain_selected_type}] {tool_label}", True, tc)
            screen.blit(sel, (self.btn_terrain.rect.right + 4, self.btn_terrain.rect.y + 8))

        # Win probability bar (above grid buttons, left side)
        if self.battle.combat_started and self.win_prob_cache:
            self._draw_win_probability_bar(screen, 10, SCREEN_HEIGHT - 105, 350, 22)

        # DM Advisor panel (above win prob, left side)
        if self.show_advisor_panel and self.battle.combat_started:
            advisor_h = 180
            self._draw_advisor_panel(screen, 10, SCREEN_HEIGHT - 105 - advisor_h - 5, 350, advisor_h)

    # --- Entities on grid ---
    def _draw_entities(self, screen, curr, sel):
        gsz = self.battle.grid_size
        for ent in self.battle.entities:
            if ent == self.dragging:
                continue
            if ent.is_lair:
                continue
            sx, sy = self._grid_to_screen(ent.grid_x, ent.grid_y)
            
            size = ent.size_in_squares
            pixel_w = size * gsz
            cx = int(sx + pixel_w // 2)
            cy = int(sy + pixel_w // 2)
            r = (pixel_w // 2) - 3

            if ent == sel:
                pygame.draw.circle(screen, COLORS["warning"], (cx, cy), r+6, 2)
            if ent == curr:
                pygame.draw.circle(screen, (255,255,255,80), (cx, cy), r+2)
            
            self._draw_token(screen, ent, cx, cy, r)
            hp_bar.draw(screen, cx, cy+r+4, pixel_w-10, ent.hp, ent.max_hp)
            # Dead X
            if ent.hp <= 0:
                pygame.draw.line(screen, COLORS["danger"], (cx-r, cy-r), (cx+r, cy+r), 2)
                pygame.draw.line(screen, COLORS["danger"], (cx+r, cy-r), (cx-r, cy+r), 2)
            # Elevation badge (top-right of token)
            if ent.elevation != 0:
                elev_color = (150, 180, 255) if ent.elevation > 0 else (255, 150, 100)
                elev_txt = fonts.tiny.render(f"{ent.elevation}ft", True, elev_color)
                etx = cx + r - elev_txt.get_width()
                ety = cy - r - 4
                bg_rect = pygame.Rect(etx - 2, ety - 1, elev_txt.get_width() + 4, 14)
                pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect, border_radius=2)
                screen.blit(elev_txt, (etx, ety))
            # Flying indicator (wing icon above token)
            if ent.is_flying:
                fly_txt = fonts.tiny.render("FLY", True, (180, 220, 255))
                screen.blit(fly_txt, (cx - fly_txt.get_width()//2, cy - r - 16))
            # Climbing indicator
            if ent.is_climbing:
                climb_txt = fonts.tiny.render("CLIMB", True, (200, 180, 120))
                screen.blit(climb_txt, (cx - climb_txt.get_width()//2, cy - r - 16))

    # --- Drag visual ---
    def _draw_drag(self, screen):
        if not self.dragging:
            return
        mx, my = pygame.mouse.get_pos()
        gsz = self.battle.grid_size
        screen_sx, screen_sy = self._grid_to_screen(self.drag_start[0], self.drag_start[1])
        sx = int(screen_sx + gsz//2)
        sy = int(screen_sy + gsz//2)
        dist_ft = math.hypot(mx-sx, my-sy) / gsz * 5
        can_move = dist_ft <= self.dragging.stats.speed
        lc = COLORS["success"] if can_move else COLORS["danger"]
        pygame.draw.line(screen, lc, (sx, sy), (mx, my), 2)
        dt = fonts.small.render(f"{dist_ft:.0f} ft", True, (255,255,255))
        screen.blit(dt, (mx+12, my+10))
        
        size = self.dragging.size_in_squares
        pixel_w = size * gsz
        r = (pixel_w // 2) - 3
        self._draw_token(screen, self.dragging, mx, my, r)
        # Distance to enemies
        for e in self.battle.entities:
            if e == self.dragging or e.hp <= 0:
                continue
            esx, esy = self._grid_to_screen(e.grid_x, e.grid_y)
            
            # Calculate center based on size
            e_size = e.size_in_squares
            e_pixel_w = e_size * gsz
            ex = int(esx + e_pixel_w//2)
            ey = int(esy + e_pixel_w//2)
            
            edf = math.hypot(mx-ex, my-ey) / gsz * 5
            line_col = COLORS["danger"] if e.is_player != self.dragging.is_player else COLORS["success"]
            pygame.draw.line(screen, line_col, (mx,my), (ex,ey), 1)
            
            # Draw text above token with background
            eds = fonts.tiny.render(f"{edf:.0f}ft", True, COLORS["text_dim"])
            text_rect = eds.get_rect(center=(ex, ey - (e_pixel_w//2) - 15))
            pygame.draw.rect(screen, (0,0,0,180), text_rect.inflate(6,4), border_radius=3)
            screen.blit(eds, text_rect)

    # --- Right panel ---
    def _draw_panel(self, screen, curr, sel, mp):
        self.active_tooltip = None # Reset tooltip
        # Clear dynamic click zones for this frame
        self.ui_click_zones.clear()
        self.ui_right_click_zones.clear()

        panel_rect = pygame.Rect(GRID_W, TOP_BAR_H, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H)
        draw_gradient_rect(screen, panel_rect,
                           COLORS["panel_dark"], tuple(max(0, c - 3) for c in COLORS["panel_dark"]))
        pygame.draw.line(screen, COLORS["border_light"], (GRID_W, TOP_BAR_H), (GRID_W, SCREEN_HEIGHT), 2)

        # Active creature header
        hdr_rect = pygame.Rect(GRID_W, TOP_BAR_H, PANEL_W, 38)
        draw_gradient_rect(screen, hdr_rect, COLORS["panel_header"], COLORS["panel_dark"])
        pygame.draw.line(screen, COLORS["separator"], (GRID_W, TOP_BAR_H + 38), (SCREEN_WIDTH, TOP_BAR_H + 38))
        if not self.battle.combat_started:
            at = fonts.body_bold.render("DEPLOYMENT PHASE", True, COLORS["accent"])
        else:
            side_indicator = "[PLAYER]" if curr.is_player else "[NPC]"
            side_color = COLORS["player"] if curr.is_player else COLORS["enemy"]
            at = fonts.body_bold.render(f"{side_indicator} {curr.name}  (Init {curr.initiative})", True, side_color)
        screen.blit(at, (GRID_W + 12, TOP_BAR_H + 8))

        # Tabs (polished)
        tab_w = PANEL_W // len(TABS)
        for i, tab in enumerate(TABS):
            tr = pygame.Rect(GRID_W + i * tab_w, TOP_BAR_H + 38, tab_w - 2, 30)
            is_active = i == self.active_tab
            is_hover = tr.collidepoint(mp)
            if is_active:
                draw_gradient_rect(screen, tr, COLORS["accent_dim"], COLORS["panel_dark"], border_radius=4)
                pygame.draw.line(screen, COLORS["accent"],
                                 (tr.x + 4, tr.bottom - 2), (tr.right - 4, tr.bottom - 2), 2)
                tt = fonts.small_bold.render(tab, True, COLORS["text_bright"])
            else:
                if is_hover:
                    pygame.draw.rect(screen, COLORS["hover"], tr, border_radius=4)
                tt = fonts.small.render(tab, True, COLORS["text_dim"] if not is_hover else COLORS["text_main"])
            screen.blit(tt, tt.get_rect(center=tr.center))

        content_y = TOP_BAR_H + 70 + self.panel_scroll
        x0 = GRID_W + 12

        # Clip panel content
        clip = pygame.Rect(GRID_W, TOP_BAR_H+68, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H - 68 - 80)
        screen.set_clip(clip)

        if self.active_tab == 0:
            content_y = self._draw_stats_tab(screen, sel, x0, content_y, mp)
        elif self.active_tab == 1:
            content_y = self._draw_spells_tab(screen, sel, x0, content_y, mp)
        elif self.active_tab == 2:
            content_y = self._draw_log_tab(screen, sel, x0, content_y, mp)

        screen.set_clip(None)

        # HP buttons strip
        btn_y = SCREEN_HEIGHT - 130
        lbl = fonts.tiny.render("HP:", True, COLORS["text_dim"])
        screen.blit(lbl, (x0, btn_y))
        bx = x0 + 30
        for b in self.hp_btns:
            b.rect.topleft = (bx, btn_y)
            b.draw(screen, mp)
            bx += 47

        # Init buttons
        btn_y += 32
        il = fonts.tiny.render("Init:", True, COLORS["text_dim"])
        screen.blit(il, (x0, btn_y))
        bx = x0 + 35
        for b in self.init_btns:
            b.rect.topleft = (bx, btn_y)
            b.draw(screen, mp)
            bx += 42

    def _draw_section_header(self, screen, section_key, label, x0, y, mp):
        """Draw a collapsible section header. Returns (new_y, is_collapsed)."""
        collapsed = section_key in self.collapsed_sections
        arrow = ">" if collapsed else "v"
        txt = f"{arrow} {label}"
        s = fonts.small.render(txt, True, COLORS["text_dim"])
        r = pygame.Rect(x0, y, s.get_width() + 10, 20)
        if r.collidepoint(mp):
            s = fonts.small.render(txt, True, COLORS["accent_hover"])
        screen.blit(s, (x0, y))
        self.ui_click_zones.append((r, lambda k=section_key: (
            self.collapsed_sections.discard(k) if k in self.collapsed_sections
            else self.collapsed_sections.add(k))))
        return y + 20, collapsed

    def _draw_stats_tab(self, screen, sel, x0, y, mp):

        def ln(text, color=COLORS["text_main"], indent=0):
            nonlocal y
            s = fonts.small.render(text, True, color)
            screen.blit(s, (x0+indent, y))
            y += 20

        # Name, type, AC, HP (always visible)
        ln(f"{sel.name}", COLORS["accent"] if not sel.is_player else COLORS["player"])
        cr_str = f"CR {sel.stats.challenge_rating:.3g}" if sel.stats.challenge_rating else "Player"
        ln(f"{sel.stats.size} {sel.stats.creature_type}  |  {cr_str}  |  XP {sel.stats.xp}", COLORS["text_dim"])
        ln("")
        hp_pct = sel.hp/sel.max_hp if sel.max_hp>0 else 0
        hp_c = COLORS["success"] if hp_pct>0.5 else COLORS["warning"] if hp_pct>0.25 else COLORS["danger"]
        ln(f"HP: {sel.hp}/{sel.max_hp}  TempHP: {sel.temp_hp}", hp_c)

        # Direct HP input indicator
        if self.hp_input_active and self.hp_input_text:
            input_c = COLORS["danger"] if self.hp_input_text.startswith("-") else COLORS["success"]
            ln(f"  HP Input: {self.hp_input_text}_ (Enter to apply)", input_c)

        ln(f"AC: {sel.stats.armor_class}  Speed: {sel.stats.speed}ft  Move left: {sel.movement_left:.0f}ft", COLORS["text_main"])
        if sel.stats.fly_speed:   ln(f"Fly: {sel.stats.fly_speed}ft", COLORS["text_dim"])
        if sel.stats.swim_speed:  ln(f"Swim: {sel.stats.swim_speed}ft", COLORS["text_dim"])

        # Resistances & Immunities
        if sel.stats.damage_immunities:
            ln(f"Immune: {', '.join(sel.stats.damage_immunities)}", COLORS["success"])
        if sel.stats.damage_resistances:
            ln(f"Resist: {', '.join(sel.stats.damage_resistances)}", COLORS["warning"])
        if sel.stats.damage_vulnerabilities:
            ln(f"Vuln: {', '.join(sel.stats.damage_vulnerabilities)}", COLORS["danger"])
        if sel.stats.condition_immunities:
            ln(f"Cond Imm: {', '.join(sel.stats.condition_immunities)}", COLORS["text_dim"])

        ln("")

        # Ability scores (collapsible)
        y, collapsed = self._draw_section_header(screen, "ABILITIES", "ABILITIES / SAVES / SKILLS", x0, y, mp)
        if not collapsed:
            ab = sel.stats.abilities
            scores = [("STR",ab.strength),("DEX",ab.dexterity),("CON",ab.constitution),
                      ("INT",ab.intelligence),("WIS",ab.wisdom),("CHA",ab.charisma)]
            row = ""
            for name, val in scores:
                mod = (val-10)//2
                row += f"{name} {val}({mod:+d})  "
            s = fonts.tiny.render(row.strip(), True, COLORS["text_main"])
            screen.blit(s, (x0, y))
            y += 18

            # Saves
            ln("SAVES (click to roll):", COLORS["text_dim"])
            sx = x0
            abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
            for ab in abilities:
                bonus = sel.get_save_bonus(ab)
                is_prof = ab in sel.stats.saving_throws
                txt = f"{ab[:3]} {bonus:+d}"
                s_surf = fonts.tiny.render(txt, True, COLORS["text_main"] if not is_prof else COLORS["accent"])
                w = s_surf.get_width() + 10
                if sx + w > SCREEN_WIDTH - 20:
                    sx = x0
                    y += 24
                r = pygame.Rect(sx, y, w, 20)
                bg = (60, 63, 65)
                if r.collidepoint(mp): bg = (80, 83, 85)
                pygame.draw.rect(screen, bg, r, border_radius=4)
                screen.blit(s_surf, (sx+5, y+2))
                self.ui_click_zones.append((r, lambda a=ab, b=bonus: self._roll_save(a, b)))
                sx += w + 5
            y += 24

            # Skills
            if sel.stats.skills:
                ln("SKILLS (click to roll):", COLORS["text_dim"])
                sx = x0
                for sk, bonus in sel.stats.skills.items():
                    txt = f"{sk} {bonus:+d}"
                    s_surf = fonts.tiny.render(txt, True, COLORS["text_main"])
                    w = s_surf.get_width() + 10
                    if sx + w > SCREEN_WIDTH - 20:
                        sx = x0
                        y += 24
                    r = pygame.Rect(sx, y, w, 20)
                    bg = (60, 63, 65)
                    if r.collidepoint(mp): bg = (80, 83, 85)
                    pygame.draw.rect(screen, bg, r, border_radius=4)
                    screen.blit(s_surf, (sx+5, y+2))
                    self.ui_click_zones.append((r, lambda s=sk, b=bonus: self._roll_skill(s, b)))
                    sx += w + 5
                y += 24

            # Ability Checks
            ln("ABILITY CHECKS:", COLORS["text_dim"])
            sx = x0
            abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
            for ab in abilities:
                bonus = sel.get_modifier(ab)
                txt = f"{ab[:3]} {bonus:+d}"
                s_surf = fonts.tiny.render(txt, True, COLORS["text_main"])
                w = s_surf.get_width() + 10
                if sx + w > SCREEN_WIDTH - 20:
                    sx = x0
                    y += 24
                r = pygame.Rect(sx, y, w, 20)
                pygame.draw.rect(screen, (60, 63, 65) if not r.collidepoint(mp) else (80, 83, 85), r, border_radius=4)
                screen.blit(s_surf, (sx+5, y+2))
                self.ui_click_zones.append((r, lambda a=ab, b=bonus: self._roll_skill(f"{a} Check", b)))
                sx += w + 5
            y += 24

        # Action economy indicators (always visible)
        ln("")
        ln("TURN RESOURCES:", COLORS["text_dim"])
        def indicator(label, used):
            c = COLORS["danger"] if used else COLORS["success"]
            t = fonts.tiny.render(f"{'[X]' if used else '[O]'} {label}", True, c)
            screen.blit(t, (x0, y))
            return 0
        indicator("Action", sel.action_used); y+=18
        indicator("Bonus Action", sel.bonus_action_used); y+=18
        indicator("Reaction", sel.reaction_used); y+=18
        if sel.concentrating_on:
            conc_text = f"Concentrating: {sel.concentrating_on.name}"
            if hasattr(sel, 'concentration_rounds_left') and sel.concentration_rounds_left is not None:
                conc_text += f" ({sel.concentration_rounds_left} rnds)"
            ln(conc_text, COLORS["concentration"])

        # Legendary resources
        if sel.stats.legendary_action_count:
            txt = f"Legendary Actions: {sel.legendary_actions_left}/{sel.stats.legendary_action_count}"
            ln(txt, COLORS["legendary"])

        if sel.stats.legendary_resistance_count:
            txt = f"Legendary Resist: {sel.legendary_resistances_left}/{sel.stats.legendary_resistance_count}"
            s = fonts.small.render(txt, True, COLORS["legendary"])
            r = pygame.Rect(x0, y, s.get_width(), 20)
            screen.blit(s, (x0, y))
            if sel.legendary_resistances_left > 0:
                self.ui_click_zones.append((r, lambda: self._use_legendary_resistance_manual(sel)))
            y += 20

        # Class Resources (collapsible)
        if sel.stats.character_class:
            ln("")
            y, collapsed = self._draw_section_header(screen, "CLASS", f"CLASS: {sel.stats.character_class} {sel.stats.character_level}", x0, y, mp)
            if not collapsed:
                if sel.stats.subclass:
                    ln(f"Subclass: {sel.stats.subclass}", COLORS["accent"])
                if sel.stats.race:
                    ln(f"Race: {sel.stats.race}", COLORS["text_dim"])
                if hasattr(sel, 'rage_active') and sel.stats.rage_count > 0:
                    rage_str = "ACTIVE" if sel.rage_active else "Inactive"
                    if sel.rage_active:
                        if sel.attacked_this_turn or sel.rage_damage_taken:
                            rage_str += " (Sustained)"
                        else:
                            rage_str += " (Ending)"
                    rage_c = COLORS["danger"] if sel.rage_active else COLORS["text_dim"]
                    ln(f"Rage: {rage_str} ({sel.rages_left}/{sel.stats.rage_count} uses)", rage_c)
                if sel.stats.ki_points > 0:
                    ln(f"Ki: {sel.ki_points_left}/{sel.stats.ki_points}", COLORS["spell"])
                if sel.stats.sorcery_points > 0:
                    ln(f"Sorcery Points: {sel.sorcery_points_left}/{sel.stats.sorcery_points}", COLORS["spell"])
                if sel.stats.lay_on_hands_pool > 0:
                    ln(f"Lay on Hands: {sel.lay_on_hands_left}/{sel.stats.lay_on_hands_pool} HP", COLORS["success"])
                if sel.stats.bardic_inspiration_count > 0:
                    ln(f"Bardic Inspiration: {sel.bardic_inspiration_left}/{sel.stats.bardic_inspiration_count} ({sel.stats.bardic_inspiration_dice})", COLORS["spell"])
                if hasattr(sel, 'marked_target') and sel.marked_target:
                    ln(f"Marked: {sel.marked_target.name}", COLORS["warning"])
        else:
            # Non-class resources still shown
            if hasattr(sel, 'rage_active') and sel.stats.rage_count > 0:
                rage_str = "ACTIVE" if sel.rage_active else "Inactive"
                rage_c = COLORS["danger"] if sel.rage_active else COLORS["text_dim"]
                ln(f"Rage: {rage_str} ({sel.rages_left}/{sel.stats.rage_count} uses)", rage_c)

        # Conditions (always visible - important for DM)
        ln("")
        ln("CONDITIONS:", COLORS["text_dim"])
        start_x = x0
        start_y = y
        col_w, row_h = 120, 22
        for i, (cond, desc) in enumerate(CONDITIONS.items()):
            col = i % 4
            row = i // 4
            r = pygame.Rect(start_x + col*col_w, start_y + row*row_h, 116, 20)
            is_active = sel.has_condition(cond)
            bg = COLORS["accent"] if is_active else (45,47,52)
            if r.collidepoint(mp):
                bg = COLORS["accent_hover"] if is_active else (60,62,67)
                self.active_tooltip = f"{cond}: {desc}"
            pygame.draw.rect(screen, bg, r, border_radius=3)
            self.ui_click_zones.append((r, lambda c=cond: self._toggle_condition(c)))
            ct = fonts.tiny.render(cond, True, COLORS["text_main"])
            screen.blit(ct, (r.x+4, r.y+3))
        y = start_y + (((len(CONDITIONS)-1)//4)+1) * row_h + 8

        # Active Effects
        if sel.active_effects:
            ln("")
            ln("ACTIVE EFFECTS:", COLORS["text_dim"])
            for eff, dur in sel.active_effects.items():
                ln(f"• {eff} ({dur} rnds)", COLORS["spell"], 8)

        # Notes
        if sel.notes:
            ln("")
            ln("NOTES:", COLORS["text_dim"])
            # Simple wrap for notes display
            lines = sel.notes.split('\n')
            for line in lines:
                # Wrap long lines roughly
                parts = [line[i:i+50] for i in range(0, len(line), 50)]
                for p in parts: ln(p, COLORS["text_main"], 8)

        # Features summary (collapsible)
        if sel.stats.features:
            ln("")
            y, feat_collapsed = self._draw_section_header(screen, "FEATURES", f"FEATURES ({len(sel.stats.features)})", x0, y, mp)
            if not feat_collapsed:
                for feat in sel.stats.features:
                    uses_str = ""
                    if feat.uses_per_day > 0:
                        remaining = sel.feature_uses.get(feat.name, feat.uses_per_day)
                        uses_str = f" [{remaining}/{feat.uses_per_day}]"
                    elif feat.recharge:
                        remaining = sel.feature_uses.get(feat.name, 0)
                        uses_str = f" [{remaining}/1]"

                    # Render manually to check hover
                    txt_str = f"• {feat.name}{uses_str}"
                    s = fonts.small.render(txt_str, True, COLORS["text_main"])
                    line_rect = pygame.Rect(x0+8, y, s.get_width(), 20)

                    if line_rect.collidepoint(mp):
                        s = fonts.small.render(txt_str, True, COLORS["accent_hover"])
                        self.active_tooltip = f"{feat.name}: {feat.description}"

                    # Click to use feature (if it has uses)
                    if feat.uses_per_day > 0 or feat.recharge:
                        self.ui_click_zones.append((line_rect, lambda f=feat: self._use_feature_manual(sel, f)))

                    screen.blit(s, (x0+8, y))
                    y += 20

        # Helper to draw action lists (collapsible)
        def draw_action_section(title, actions, section_key=None):
            nonlocal y
            if not actions: return
            ln("")
            if section_key:
                y, collapsed = self._draw_section_header(screen, section_key, f"{title} ({len(actions)})", x0, y, mp)
                if collapsed:
                    return
            else:
                ln(title, COLORS["text_dim"])
            for act in actions:
                # Build summary string (e.g. "+7, 1d8+4")
                info = []
                if act.is_multiattack:
                    info.append("Multiattack")
                elif act.attack_bonus:
                    info.append(f"+{act.attack_bonus}")
                    if act.damage_dice:
                        dmg = act.damage_dice
                        if act.damage_bonus: dmg += f"+{act.damage_bonus}"
                        info.append(dmg)
                elif act.damage_dice:
                    info.append(act.damage_dice)
                
                summary = f"• {act.name}"
                if info:
                    summary += f" ({', '.join(info)})"
                
                # Render
                s = fonts.small.render(summary, True, COLORS["text_main"])
                line_rect = pygame.Rect(x0+8, y, s.get_width(), 20)
                
                if line_rect.collidepoint(mp):
                    s = fonts.small.render(summary, True, COLORS["accent_hover"])
                    # Generate tooltip description
                    desc = act.description
                    if not desc:
                        parts = []
                        if act.is_multiattack:
                            parts.append(f"Multiattack: {act.multiattack_count} attacks ({', '.join(act.multiattack_targets)})")
                        else:
                            parts.append(f"Type: {act.action_type}")
                            if act.range: parts.append(f"Range: {act.range}ft")
                            if act.attack_bonus: parts.append(f"Hit: +{act.attack_bonus}")
                            if act.damage_dice: 
                                d = act.damage_dice
                                if act.damage_bonus: d += f"+{act.damage_bonus}"
                                parts.append(f"Damage: {d} {act.damage_type}")
                            if act.applies_condition:
                                c = f"Applies {act.applies_condition}"
                                if act.condition_dc: c += f" (DC {act.condition_dc} {act.condition_save})"
                                parts.append(c)
                        desc = ". ".join(parts)
                    self.active_tooltip = f"{act.name}: {desc}"

                # Click to target action
                self.ui_click_zones.append((line_rect, lambda a=act: self._start_action_targeting(sel, a)))

                screen.blit(s, (x0+8, y))
                y += 20

        draw_action_section("ACTIONS:", sel.stats.actions, "ACTIONS")
        draw_action_section("BONUS ACTIONS:", sel.stats.bonus_actions, "BONUS_ACTIONS")
        draw_action_section("REACTIONS:", sel.stats.reactions)
        
        # Filter and draw Legendary Actions
        leg_actions = [a for a in sel.stats.actions if a.action_type == "legendary"]
        if leg_actions:
            draw_action_section("LEGENDARY ACTIONS:", leg_actions)

        return y

    def _draw_spells_tab(self, screen, sel, x0, y, mp):
        def ln(text, color=COLORS["text_main"], indent=0):
            nonlocal y
            s = fonts.small.render(text, True, color)
            screen.blit(s, (x0+indent, y))
            y += 20

        if sel.stats.spellcasting_ability:
            ln(f"Spellcasting: {sel.stats.spellcasting_ability}  DC {sel.stats.spell_save_dc}  +{sel.stats.spell_attack_bonus}", COLORS["accent"])
        else:
            ln("No spellcasting", COLORS["text_dim"])
            return y

        # Spell slots
        ln("SPELL SLOTS (click pip to use):", COLORS["text_dim"])
        _LEVEL_NAMES = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th"}
        for lvl in range(1, 10):
            key = _LEVEL_NAMES[lvl]
            total = sel.stats.spell_slots.get(key, 0)
            remaining = sel.spell_slots.get(key, 0)
            if total == 0:
                continue
            label_s = fonts.tiny.render(f"{key}:", True, COLORS["text_dim"])
            screen.blit(label_s, (x0, y))
            px = x0 + 34
            for pip in range(total):
                pr = pygame.Rect(px, y+1, 16, 16)
                filled = pip < remaining
                c = COLORS["spell"] if filled else (50,50,50)
                pygame.draw.rect(screen, c, pr, border_radius=3)
                if filled:
                    pygame.draw.rect(screen, COLORS["accent"], pr, 1, border_radius=3)
                    self.ui_click_zones.append((pr, lambda l=lvl: self._use_spell_slot(l)))
                    self.ui_right_click_zones.append((pr, lambda l=lvl: self._modify_spell_slot(l, 1)))
                else:
                    # Empty slot - allow right click to refill
                    self.ui_right_click_zones.append((pr, lambda l=lvl: self._modify_spell_slot(l, 1)))
                px += 20
            y += 22

        # Cantrips
        if sel.stats.cantrips:
            ln("")
            ln("CANTRIPS:", COLORS["text_dim"])
            for sp in sel.stats.cantrips:
                # Render text
                txt = f"  {sp.name}"
                s = fonts.small.render(txt, True, COLORS["text_main"])
                line_rect = pygame.Rect(x0+4, y, s.get_width(), 20)
                
                # Hover logic
                if line_rect.collidepoint(mp):
                    s = fonts.small.render(txt, True, COLORS["accent_hover"])
                    desc = f"{sp.name} (Cantrip)\nRange: {sp.range}ft\n"
                    if sp.damage_dice: desc += f"Damage: {sp.damage_dice} {sp.damage_type}\n"
                    if sp.save_ability: desc += f"Save: {sp.save_ability}\n"
                    desc += f"\n{sp.description}"
                    self.active_tooltip = desc
                
                screen.blit(s, (x0+4, y))
                
                # Extra info string
                info = f"({sp.range}ft, {sp.damage_dice or sp.description[:30]})"
                s_info = fonts.small.render(info, True, COLORS["text_dim"])
                screen.blit(s_info, (x0+4 + s.get_width() + 10, y))
                y += 20

        # Spells
        if sel.stats.spells_known:
            ln("")
            ln("SPELLS KNOWN:", COLORS["text_dim"])
            for sp in sel.stats.spells_known:
                key2 = _LEVEL_NAMES.get(sp.level, f"{sp.level}th")
                conc = " [C]" if sp.concentration else ""
                
                # Main text
                txt = f"  [{key2}]{conc} {sp.name}"
                color = COLORS["spell"] if sel.has_spell_slot(sp.level) else COLORS["text_dim"]
                s = fonts.small.render(txt, True, color)
                line_rect = pygame.Rect(x0+4, y, s.get_width(), 20)

                # Hover logic
                if line_rect.collidepoint(mp):
                    s = fonts.small.render(txt, True, COLORS["accent_hover"])
                    desc = f"{sp.name} (Level {sp.level})\nRange: {sp.range}ft\n"
                    if sp.damage_dice: desc += f"Damage: {sp.damage_dice} {sp.damage_type}\n"
                    if sp.heals: desc += f"Heals: {sp.heals}\n"
                    if sp.save_ability: desc += f"Save: {sp.save_ability} (Half: {sp.half_on_save})\n"
                    if sp.concentration: desc += "Requires Concentration\n"
                    desc += f"\n{sp.description}"
                    self.active_tooltip = desc
                
                # Click to target
                self.ui_click_zones.append((line_rect, lambda s=sp: self._start_spell_targeting(sel, s)))

                screen.blit(s, (x0+4, y))

                # Info suffix
                dmg_str = sp.damage_dice or sp.heals or sp.applies_condition or sp.description[:25] or ""
                if dmg_str:
                    s_info = fonts.small.render(f": {dmg_str}", True, COLORS["text_dim"])
                    screen.blit(s_info, (x0+4 + s.get_width(), y))
                
                y += 20

        return y

    # ------------------------------------------------------------------ #
    # Manual Spell Targeting                                               #
    # ------------------------------------------------------------------ #



    def _draw_spell_targeting_overlay(self, screen, mp):
        if not self.spell_targeting or not self.spell_caster:
            return

        mx, my = mp
        if mx > GRID_W or my < TOP_BAR_H:
            return # Mouse outside grid

        caster = self.spell_caster
        spell = self.spell_targeting
        gsz = self.battle.grid_size

        # Caster screen pos
        cx, cy = self._grid_to_screen(caster.grid_x, caster.grid_y)
        size = caster.size_in_squares
        caster_px = (cx + (size * gsz)//2, cy + (size * gsz)//2)

        # Mouse grid pos
        gx, gy = self._screen_to_grid(mx, my)
        
        # Distance check
        dist_ft = math.hypot(gx - caster.grid_x, gy - caster.grid_y) * 5
        in_range = dist_ft <= spell.range
        
        # Draw Range Circle
        range_px = int(spell.range / 5 * gsz)
        pygame.draw.circle(screen, (255, 255, 255), caster_px, range_px, 1)

        # Draw Template at Mouse
        color = (0, 255, 0, 100) if in_range else (255, 0, 0, 100)
        border = (0, 255, 0) if in_range else (255, 0, 0)
        
        # Snap to grid center for cleaner targeting
        snap_gx, snap_gy = int(gx) + 0.5, int(gy) + 0.5
        sx, sy = self._grid_to_screen(snap_gx, snap_gy)
        
        # AoE Visualization
        if spell.aoe_radius > 0:
            radius_px = int(spell.aoe_radius / 5 * gsz)
            aoe_surf = pygame.Surface((radius_px*2, radius_px*2), pygame.SRCALPHA)
            
            if spell.aoe_shape == "cone":
                # Cone from caster to mouse
                dx = mx - caster_px[0]
                dy = my - caster_px[1]
                angle = math.atan2(dy, dx)
                pts = [(radius_px, radius_px)] # Center of surface
                for deg in range(-30, 31, 10):
                    rad = angle + math.radians(deg)
                    px = radius_px + math.cos(rad) * radius_px
                    py = radius_px + math.sin(rad) * radius_px
                    pts.append((px, py))
                pygame.draw.polygon(aoe_surf, color, pts)
                pygame.draw.lines(aoe_surf, border, True, pts, 2)
                # Draw at caster position for cone origin? 
                # Usually cones start at caster. Let's draw it at caster.
                screen.blit(aoe_surf, (caster_px[0]-radius_px, caster_px[1]-radius_px))
            else:
                # Sphere/Cube/Cylinder at mouse
                pygame.draw.circle(aoe_surf, color, (radius_px, radius_px), radius_px)
                pygame.draw.circle(aoe_surf, border, (radius_px, radius_px), radius_px, 2)
                screen.blit(aoe_surf, (sx - radius_px, sy - radius_px))
        else:
            # Single Target Line
            pygame.draw.line(screen, border, caster_px, (mx, my), 2)
            pygame.draw.circle(screen, border, (mx, my), 5)

        # Tooltip
        txt = f"{spell.name}: {dist_ft:.1f}ft / {spell.range}ft"
        t_surf = fonts.small.render(txt, True, border)
        screen.blit(t_surf, (mx + 15, my + 15))



    def _draw_action_targeting_overlay(self, screen, mp):
        if not self.action_targeting or not self.action_caster:
            return

        mx, my = mp
        if mx > GRID_W or my < TOP_BAR_H:
            return

        caster = self.action_caster
        action = self.action_targeting
        gsz = self.battle.grid_size
        cx, cy = self._grid_to_screen(caster.grid_x, caster.grid_y)
        size = caster.size_in_squares
        caster_px = (cx + (size * gsz)//2, cy + (size * gsz)//2)
        gx, gy = self._screen_to_grid(mx, my)
        
        # Range check
        dist_ft = math.hypot(gx - caster.grid_x, gy - caster.grid_y) * 5
        in_range = dist_ft <= action.range + 2 # tolerance
        
        color = (255, 200, 50, 100) if in_range else (255, 50, 50, 100)
        border = (255, 200, 50) if in_range else (255, 50, 50)

        # Draw Range Circle
        range_px = int(action.range / 5 * gsz)
        pygame.draw.circle(screen, (255, 255, 255), caster_px, range_px, 1)

        # Draw Template
        if action.aoe_radius > 0:
            radius_px = int(action.aoe_radius / 5 * gsz)
            aoe_surf = pygame.Surface((radius_px*2, radius_px*2), pygame.SRCALPHA)
            pygame.draw.circle(aoe_surf, color, (radius_px, radius_px), radius_px)
            pygame.draw.circle(aoe_surf, border, (radius_px, radius_px), radius_px, 2)
            
            snap_gx, snap_gy = int(gx) + 0.5, int(gy) + 0.5
            sx, sy = self._grid_to_screen(snap_gx, snap_gy)
            screen.blit(aoe_surf, (sx - radius_px, sy - radius_px))
        else:
            pygame.draw.line(screen, border, caster_px, (mx, my), 2)
            pygame.draw.circle(screen, border, (mx, my), 5)

        txt = f"{action.name}: {dist_ft:.1f}ft / {action.range}ft"
        t_surf = fonts.small.render(txt, True, border)
        screen.blit(t_surf, (mx + 15, my + 15))



    def _draw_log_tab(self, screen, sel, x0, y, mp):
        # Filter Buttons - draw as compact pill row
        btn_h = 22
        sx = x0
        for mode, label in self._LOG_FILTERS:
            # For entity filter, show entity name
            if mode == "selected":
                ent_name = sel.name[:10] if sel else "Entity"
                label = ent_name
            tw = fonts.tiny.size(label)[0] + 12
            r = pygame.Rect(sx, y, tw, btn_h)
            is_active = (self.log_filter_mode == mode)
            bg = COLORS["accent"] if is_active else (50, 52, 57)
            if r.collidepoint(mp) and not is_active:
                bg = (70, 72, 77)
            pygame.draw.rect(screen, bg, r, border_radius=4)
            t = fonts.tiny.render(label, True, (255, 255, 255))
            screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
            self.ui_click_zones.append((r, lambda m=mode: setattr(self, 'log_filter_mode', m)))
            sx += tw + 4
            if sx > SCREEN_WIDTH - 30:
                sx = x0
                y += btn_h + 2

        y += btn_h + 6

        # Filter logic
        display_logs = [msg for msg in self.logs if self._log_matches_filter(msg, self.log_filter_mode, sel)]

        for msg in reversed(display_logs):
            c = COLORS["accent"] if msg.startswith("[AI") else \
                COLORS["player"] if msg.startswith("[PLAYER") else \
                COLORS["danger"] if "damage" in msg.lower() or "hit" in msg.lower() else \
                COLORS["success"] if "heal" in msg.lower() else \
                COLORS["text_dim"] if msg.startswith("---") else \
                COLORS["text_main"]
            parts = [msg[i:i+62] for i in range(0, len(msg), 62)]
            for part in parts:
                s = fonts.tiny.render(part, True, c)
                screen.blit(s, (x0, y))
                y += 16
                if y > SCREEN_HEIGHT - 140:
                    return y
        return y

    # --- Bottom bar ---
    def _draw_bottom_bar(self, screen, curr, mp):
        bar_y = SCREEN_HEIGHT - 70
        pygame.draw.rect(screen, (25,27,30), (GRID_W, bar_y-8, PANEL_W, 80))
        pygame.draw.line(screen, COLORS["border"], (GRID_W, bar_y-8), (SCREEN_WIDTH, bar_y-8), 1)

        self.btn_log_pl.draw(screen, mp)

        if not self.battle.combat_started:
            self.btn_start.draw(screen, mp)
        else:
            self.btn_next.draw(screen, mp)
            if curr:
                if curr.action_used:
                    self.btn_ai.text  = "AI DONE"
                    self.btn_ai.color = COLORS["text_dim"]
                else:
                    self.btn_ai.text  = "AI TURN" if curr.is_player else "AI AUTO-PLAY"
                    self.btn_ai.color = COLORS["accent"]
                self.btn_ai.draw(screen, mp)

    # --- AI confirm dialog ---
    def _draw_ai_confirm_dialog(self, screen, mp):
        # Clear dynamic zones for this dialog
        self.ui_click_zones.clear()

        plan = self.pending_plan
        steps = plan.steps
        idx = self.pending_step_idx
        if idx >= len(steps):
            self.pending_plan = None
            return

        step = steps[idx]

        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))

        bw, bh = 700, 450
        bx = SCREEN_WIDTH//2 - bw//2
        by = SCREEN_HEIGHT//2 - bh//2

        pygame.draw.rect(screen, (38,40,44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["accent"], (bx, by, bw, 44), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        title_str = f"AI Action  –  Step {idx+1}/{len(steps)}"
        if plan.entity:
            title_str = f"{plan.entity.name}  –  Step {idx+1}/{len(steps)}"
        title = fonts.header.render(title_str, True, (255,255,255))
        screen.blit(title, (bx+14, by+8))

        # Step info
        y = by + 54
        step_type_c = {"attack":COLORS["danger"],"spell":COLORS["spell"],
                       "move":COLORS["success"],"legendary":COLORS["legendary"],
                       "reaction":COLORS["reaction"],"bonus_attack":COLORS["warning"]}.get(step.step_type, COLORS["text_main"])
        type_lbl = fonts.body.render(f"[{step.step_type.upper()}]", True, step_type_c)
        screen.blit(type_lbl, (bx+14, y))
        y += 30

        # Description (wrap)
        desc = step.description
        words = desc.split()
        line = ""
        for w in words:
            test = line + w + " "
            if fonts.body.size(test)[0] > bw - 30:
                ds = fonts.body.render(line, True, COLORS["text_main"])
                screen.blit(ds, (bx+14, y))
                y += 24
                line = w + " "
            else:
                line = test
        if line:
            ds = fonts.body.render(line.strip(), True, COLORS["text_main"])
            screen.blit(ds, (bx+14, y))
            y += 24

        # --- TARGET RESOLUTION LIST ---
        targets = step.targets if step.targets else ([step.target] if step.target else [])
        
        if targets:
            y += 10
            pygame.draw.line(screen, COLORS["border"], (bx+10, y), (bx+bw-10, y), 1)
            y += 10
            
            # Headers
            screen.blit(fonts.tiny.render("TARGET", True, COLORS["text_dim"]), (bx+20, y))
            screen.blit(fonts.tiny.render("RESULT (Click to change)", True, COLORS["text_dim"]), (bx+200, y))
            y += 20

            for t in targets:
                # Name
                name_str = t.name[:20]
                
                # Show Roll or DC info for DM to announce
                info_str = ""
                if step.save_dc > 0:
                    info_str = f" (DC {step.save_dc} {step.save_ability[:3]})"
                elif step.attack_roll > 0:
                    info_str = f" (Rolled {step.attack_roll} vs AC)"

                screen.blit(fonts.small.render(name_str + info_str, True, COLORS["text_main"]), (bx+20, y+4))

                # Outcome Toggle
                outcome = self.current_step_outcomes.get(t, "hit")
                
                # Color & Text
                if outcome == "hit":   txt, col = f"HIT ({step.damage})", COLORS["danger"]
                elif outcome == "crit": txt, col = "CRIT!", COLORS["legendary"]
                elif outcome == "miss": txt, col = "MISS", COLORS["text_dim"]
                elif outcome == "fail": txt, col = "FAIL (Full)", COLORS["danger"]
                elif outcome == "save": txt, col = "SAVE (Half)", COLORS["success"]
                elif outcome == "legendary": txt, col = "LEGENDARY RESIST", COLORS["legendary"]
                else: txt, col = outcome.upper(), COLORS["text_main"]

                r_toggle = pygame.Rect(bx+200, y, 140, 26)
                pygame.draw.rect(screen, (50,52,55), r_toggle, border_radius=4)
                pygame.draw.rect(screen, col, r_toggle, 1, border_radius=4)
                
                ts = fonts.small.render(txt, True, col)
                screen.blit(ts, (r_toggle.centerx - ts.get_width()//2, r_toggle.centery - ts.get_height()//2))
                
                self.ui_click_zones.append((r_toggle, lambda t=t: self._toggle_outcome(t)))

                y += 32

        # Upcoming steps
        if len(steps) > idx + 1:
            next_lbl = fonts.tiny.render(f"Next: {steps[idx+1].step_type.upper()} – {steps[idx+1].description[:60]}", True, COLORS["text_dim"])
            screen.blit(next_lbl, (bx+14, by+bh-55))

        self.btn_confirm.rect.topleft = (bx + bw//2 - 135, by + bh - 55)
        self.btn_confirm.text = "NEXT STEP" if len(steps) > idx+1 else "FINISH TURN"
        # Disable confirm if targets pending? Optional. For now allow skipping.
        
        self.btn_deny.rect.topleft    = (bx + bw//2 + 10,  by + bh - 55)
        self.btn_deny.text = "SKIP STEP"
        
        self.btn_approve_all.rect.topleft = (bx + bw//2 - 150, by + bh - 100)
        self.btn_cancel_ai.rect.topleft  = (bx + bw//2 + 20,  by + bh - 100)
        self.btn_confirm.draw(screen, mp)
        self.btn_deny.draw(screen, mp)
        self.btn_approve_all.draw(screen, mp)
        self.btn_cancel_ai.draw(screen, mp)

    # --- Reaction / Opportunity Attack Modal ---
    def _draw_reaction_modal(self, screen, mp):
        self.ui_click_zones.clear()
        
        reactor = self.reaction_pending[0]
        
        title_text = "REACTION AVAILABLE"
        msg_text = ""
        
        if self.reaction_type == "oa":
            mover = self.pending_move[0]
            title_text = "OPPORTUNITY ATTACK!"
            msg_text = f"{reactor.name} can react to {mover.name}'s movement."
        elif self.reaction_type == "counterspell":
            caster = self.reaction_context["caster"]
            lvl = self.reaction_context["level"]
            title_text = "COUNTERSPELL!"
            msg_text = f"{reactor.name} can Counterspell {caster.name}'s Lvl {lvl} spell."

        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))

        bw, bh = 500, 250
        bx = SCREEN_WIDTH//2 - bw//2
        by = SCREEN_HEIGHT//2 - bh//2

        pygame.draw.rect(screen, (38,40,44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["reaction"], (bx, by, bw, 44), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        title = fonts.header.render(title_text, True, (255,255,255))
        screen.blit(title, (bx+14, by+8))

        y = by + 60
        msg1 = fonts.body.render(msg_text, True, COLORS["text_main"])
        screen.blit(msg1, (bx+20, y))
        y += 30
        msg2 = fonts.small.render("Allow this reaction?", True, COLORS["text_dim"])
        screen.blit(msg2, (bx+20, y))

        # Buttons
        btn_y = by + bh - 60
        
        # ALLOW
        r_allow = pygame.Rect(bx + bw - 160, btn_y, 140, 45)
        pygame.draw.rect(screen, COLORS["danger"], r_allow, border_radius=5)
        lbl = fonts.body.render("ALLOW", True, (255,255,255))
        screen.blit(lbl, (r_allow.centerx - lbl.get_width()//2, r_allow.centery - lbl.get_height()//2))
        self.ui_click_zones.append((r_allow, lambda: self._resolve_reaction(True)))

        # DENY
        r_deny = pygame.Rect(bx + 20, btn_y, 140, 45)
        pygame.draw.rect(screen, COLORS["panel"], r_deny, border_radius=5)
        lbl = fonts.body.render("DENY", True, (255,255,255))
        screen.blit(lbl, (r_deny.centerx - lbl.get_width()//2, r_deny.centery - lbl.get_height()//2))
        self.ui_click_zones.append((r_deny, lambda: self._resolve_reaction(False)))



    def _draw_aura_highlight(self, screen):
        trig = self.current_aura_trigger
        if not trig: return
        
        source = trig["source"]
        feat = trig["feature"]
        radius = feat.aura_radius
        
        gsz = self.battle.grid_size
        sx, sy = self._grid_to_screen(source.grid_x, source.grid_y)
        
        # Center of source
        size = source.size_in_squares
        cx = int(sx + (size * gsz) // 2)
        cy = int(sy + (size * gsz) // 2)
        
        # Radius in pixels
        r_px = int(radius / 5 * gsz)
        
        # Draw aura circle
        surf = pygame.Surface((r_px*2 + 4, r_px*2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 50, 50, 60), (r_px+2, r_px+2), r_px)
        pygame.draw.circle(surf, (255, 0, 0, 180), (r_px+2, r_px+2), r_px, 2)
        screen.blit(surf, (cx - r_px - 2, cy - r_px - 2))

    def _draw_aura_modal(self, screen, mp):
        self.ui_click_zones.clear()
        trig = self.current_aura_trigger
        if not trig: return

        source = trig["source"]
        target = trig["target"]
        feat = trig["feature"]

        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))

        bw, bh = 500, 280
        bx = SCREEN_WIDTH//2 - bw//2
        by = SCREEN_HEIGHT//2 - bh//2

        pygame.draw.rect(screen, (38,40,44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], (bx, by, bw, 44), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        title = fonts.header.render("AURA TRIGGERED!", True, (0,0,0))
        screen.blit(title, (bx+14, by+8))

        y = by + 60
        msg1 = fonts.body.render(f"{target.name} starts turn near {source.name}.", True, COLORS["text_main"])
        screen.blit(msg1, (bx+20, y))
        y += 26
        msg2 = fonts.body.render(f"Feature: {feat.name}", True, COLORS["accent"])
        screen.blit(msg2, (bx+20, y))
        y += 30
        
        req = f"Roll DC {feat.save_dc} {feat.save_ability} Save"
        msg3 = fonts.header.render(req, True, COLORS["text_main"])
        screen.blit(msg3, (bx+bw//2 - msg3.get_width()//2, y))

        # Buttons
        btn_y = by + bh - 70
        
        # FAIL
        r_fail = pygame.Rect(bx + 20, btn_y, 140, 45)
        pygame.draw.rect(screen, COLORS["danger"], r_fail, border_radius=5)
        lbl = fonts.body.render("FAIL", True, (255,255,255))
        screen.blit(lbl, (r_fail.centerx - lbl.get_width()//2, r_fail.centery - lbl.get_height()//2))
        self.ui_click_zones.append((r_fail, lambda: self._resolve_aura(False)))

        # SUCCESS
        r_succ = pygame.Rect(bx + bw - 160, btn_y, 140, 45)
        pygame.draw.rect(screen, COLORS["success"], r_succ, border_radius=5)
        lbl = fonts.body.render("SUCCESS", True, (255,255,255))
        screen.blit(lbl, (r_succ.centerx - lbl.get_width()//2, r_succ.centery - lbl.get_height()//2))
        self.ui_click_zones.append((r_succ, lambda: self._resolve_aura(True)))



    # --- End of Turn Save Modal ---
    def _draw_save_modal(self, screen, mp):
        self.ui_click_zones.clear()
        if not self.pending_saves:
            self.save_modal_open = False
            self._complete_next_turn(skip_saves=True)
            return

        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))

        bw, bh = 600, 100 + len(self.pending_saves) * 50
        bx = SCREEN_WIDTH//2 - bw//2
        by = SCREEN_HEIGHT//2 - bh//2

        pygame.draw.rect(screen, (38,40,44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["accent"], (bx, by, bw, 44), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        ent = self.pending_saves[0][0]
        title = fonts.header.render(f"End of Turn Saves: {ent.name}", True, (255,255,255))
        screen.blit(title, (bx+14, by+8))

        y = by + 60
        for i, (entity, cond, ability, dc) in enumerate(self.pending_saves):
            bonus = self.battle.get_total_save_bonus(entity, ability)
            bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
            
            txt = f"{cond}: DC {dc} {ability} ({bonus_str})"
            ts = fonts.body.render(txt, True, COLORS["text_main"])
            screen.blit(ts, (bx+20, y+10))

            # Fail Button
            r_fail = pygame.Rect(bx + bw - 220, y, 90, 36)
            pygame.draw.rect(screen, COLORS["danger"], r_fail, border_radius=4)
            fl = fonts.small_bold.render("FAIL", True, (255,255,255))
            screen.blit(fl, (r_fail.centerx - fl.get_width()//2, r_fail.centery - fl.get_height()//2))
            self.ui_click_zones.append((r_fail, lambda idx=i: self._resolve_manual_save(idx, False)))

            # Success Button
            r_succ = pygame.Rect(bx + bw - 110, y, 90, 36)
            pygame.draw.rect(screen, COLORS["success"], r_succ, border_radius=4)
            sl = fonts.small_bold.render("SUCCESS", True, (255,255,255))
            screen.blit(sl, (r_succ.centerx - sl.get_width()//2, r_succ.centery - sl.get_height()//2))
            self.ui_click_zones.append((r_succ, lambda idx=i: self._resolve_manual_save(idx, True)))

            y += 50



    # --- Player action panel ---
    def _draw_player_action_panel(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,140))
        screen.blit(ov, (0,0))

        bw, bh = 580, 280
        bx = SCREEN_WIDTH//2 - bw//2
        by = SCREEN_HEIGHT//2 - bh//2

        pygame.draw.rect(screen, (38,40,44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["neutral"], (bx, by, bw, 40), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        curr = self.battle.get_current_entity()
        t = fonts.header.render(f"Player Action  –  {curr.name}", True, (255,255,255))
        screen.blit(t, (bx+14, by+6))

        y = by + 50
        hint = fonts.small.render("Select what the player is doing. Then confirm and update manually.", True, COLORS["text_dim"])
        screen.blit(hint, (bx+14, y))
        y += 26

        # Action type buttons
        for i, b in enumerate(self.player_action_btns):
            b.rect.topleft = (bx + 14 + (i % 4) * 138, y + (i // 4) * 44)
            if self.player_action_type == ["attack","spell","move","item","dash","dodge","help",""][i if i < 8 else 7]:
                pygame.draw.rect(screen, COLORS["warning"], b.rect.inflate(4,4), 2, border_radius=6)
            b.draw(screen, mp)

        # Resources of current player
        y2 = by + 50
        x2 = bx + bw - 180
        ls = fonts.tiny.render("Resources:", True, COLORS["text_dim"])
        screen.blit(ls, (x2, y2))
        y2 += 18
        _KEYS = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th"}
        for lvl in range(1, 6):
            key = _KEYS.get(lvl, f"{lvl}th")
            total = curr.stats.spell_slots.get(key, 0)
            remain = curr.spell_slots.get(key, 0)
            if total == 0: continue
            ss = fonts.tiny.render(f"{key}: {remain}/{total}", True, COLORS["spell"] if remain > 0 else COLORS["text_dim"])
            screen.blit(ss, (x2, y2))
            y2 += 18

    # --- Damage Modal Draw ---
    def _draw_damage_modal(self, screen, mp):
        # Dim background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        screen.blit(ov, (0,0))

        w, h = 500, 400
        bx = SCREEN_WIDTH//2 - w//2
        by = SCREEN_HEIGHT//2 - h//2

        # Window
        pygame.draw.rect(screen, (35, 37, 42), (bx, by, w, h), border_radius=10)
        pygame.draw.rect(screen, COLORS["danger"], (bx, by, w, 50), border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, w, h), 2, border_radius=10)

        # Title
        t = fonts.header.render(f"Apply Damage: {self.dmg_target.name}", True, (255,255,255))
        screen.blit(t, (bx+20, by+10))

        # Value display
        val_rect = pygame.Rect(bx+20, by+65, w-40, 40)
        pygame.draw.rect(screen, (20,20,20), val_rect, border_radius=5)
        val_s = fonts.title.render(self.dmg_value_str or "0", True, COLORS["text_main"])
        screen.blit(val_s, (val_rect.right - val_s.get_width() - 10, val_rect.y + 2))

        # Type grid
        types = ["slashing", "piercing", "bludgeoning", "fire", "cold", "lightning", 
                 "acid", "poison", "necrotic", "radiant", "force", "psychic", "thunder"]
        start_x = bx + 20
        start_y = by + 120
        col_w, row_h = 110, 35
        for i, ttype in enumerate(types):
            c = i % 4
            r = i // 4
            rect = pygame.Rect(start_x + c*col_w, start_y + r*row_h, 100, 30)
            is_sel = (ttype == self.dmg_type)
            bg = COLORS["accent"] if is_sel else (50,52,57)
            if rect.collidepoint(mp): bg = COLORS["accent_hover"]
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            lbl = fonts.tiny.render(ttype.capitalize(), True, COLORS["text_main"])
            screen.blit(lbl, (rect.x + 5, rect.y + 8))

        # Buttons
        cancel_btn = Button(bx+20, by+h-60, 140, 45, "CANCEL", lambda: None, color=COLORS["panel"])
        apply_btn = Button(bx+w-160, by+h-60, 140, 45, "APPLY", lambda: None, color=COLORS["danger"])
        cancel_btn.draw(screen, mp)
        apply_btn.draw(screen, mp)

    # --- Roll Result Modal ---
    def _draw_roll_result_modal(self, screen):
        # Dim background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,100))
        screen.blit(ov, (0,0))

        w, h = 300, 200
        bx = SCREEN_WIDTH//2 - w//2
        by = SCREEN_HEIGHT//2 - h//2

        # Box
        pygame.draw.rect(screen, (40, 42, 46), (bx, by, w, h), border_radius=12)
        pygame.draw.rect(screen, COLORS["accent"], (bx, by, w, h), 2, border_radius=12)

        # Title
        ts = fonts.header.render(self.roll_modal_title, True, COLORS["text_dim"])
        screen.blit(ts, (bx + w//2 - ts.get_width()//2, by + 20))

        # Total (Big)
        color = COLORS["text_main"]
        if self.roll_modal_nat == 20: color = COLORS["success"]
        elif self.roll_modal_nat == 1: color = COLORS["danger"]
        
        total_s = fonts.title.render(str(self.roll_modal_total), True, color)
        screen.blit(total_s, (bx + w//2 - total_s.get_width()//2, by + 70))

        # Expression
        es = fonts.body.render(self.roll_modal_expression, True, COLORS["text_dim"])
        screen.blit(es, (bx + w//2 - es.get_width()//2, by + 130))

        # Hint
        hs = fonts.tiny.render("(Click anywhere to dismiss)", True, (100,100,100))
        screen.blit(hs, (bx + w//2 - hs.get_width()//2, by + h - 25))

    # --- Tooltip ---
    def _draw_tooltip(self, screen):
        if not self.active_tooltip: return
        
        mx, my = pygame.mouse.get_pos()
        tip = fonts.tiny.render(self.active_tooltip, True, (255,255,255))
        tw, th = tip.get_width() + 10, tip.get_height() + 8
        
        # Default position: right-down
        tx = mx + 15
        ty = my + 10
        
        # Flip to left if off-screen right
        if tx + tw > SCREEN_WIDTH:
            tx = mx - tw - 10
        
        # Flip up if off-screen bottom
        if ty + th > SCREEN_HEIGHT:
            ty = my - th - 10
        
        pygame.draw.rect(screen, (20,20,20), (tx, ty, tw, th))
        pygame.draw.rect(screen, COLORS["border"], (tx, ty, tw, th), 1)
        screen.blit(tip, (tx+5, ty+4))

    # --- Hover Info (DM Helper) ---
    def _draw_hover_info(self, screen, mp):
        # Only show if not dragging and not in a modal
        if self.dragging or self.ctx_open or self.dmg_modal_open or self.scenario_modal:
            return
        
        mx, raw_my = mp
        if mx < GRID_W and raw_my >= TOP_BAR_H:
            gx, gy = self._screen_to_grid(mx, raw_my)
            ent = self.battle.get_entity_at(gx, gy)
            if ent and ent.hp > 0:
                # Draw info box
                lines = [
                    f"{ent.name}",
                    f"HP: {ent.hp}/{ent.max_hp}  AC: {ent.stats.armor_class}",
                    f"Speed: {ent.stats.speed}ft",
                    f"P.Perc: {10 + ent.get_skill_bonus('Perception')}"
                ]
                
                bx, by = mx + 20, raw_my + 20
                w, h = 160, 10 + len(lines)*18
                pygame.draw.rect(screen, (30,32,35), (bx, by, w, h), border_radius=5)
                pygame.draw.rect(screen, COLORS["border"], (bx, by, w, h), 1, border_radius=5)
                for i, line in enumerate(lines):
                    c = COLORS["accent"] if i == 0 else COLORS["text_main"]
                    s = fonts.tiny.render(line, True, c)
                    screen.blit(s, (bx+8, by+5 + i*18))

    # --- Context menu ---
    def _draw_ctx_menu(self, screen, mp):
        total_h = len(self.ctx_rects) * 28
        if not self.ctx_rects: return
        bx, by = self.ctx_pos
        bg_r = pygame.Rect(bx, by, 172, total_h)
        pygame.draw.rect(screen, COLORS["panel"], bg_r)
        pygame.draw.rect(screen, COLORS["border"], bg_r, 1)
        for rect, _, txt in self.ctx_rects:
            if rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["accent"], rect)
            t = fonts.tiny.render(txt, True, COLORS["text_main"])
            screen.blit(t, (rect.x+8, rect.y+5))

    # --- Condition reminder popup ---
    def _draw_condition_reminder(self, screen, mp):
        ent = self.condition_reminder
        if not ent:
            return
        lines = [f"=== {ent.name}'s Turn ==="]
        if ent.concentrating_on:
            lines.append(f"[C] Concentrating: {ent.concentrating_on.name}")
        for cond in sorted(ent.conditions):
            desc = CONDITIONS.get(cond, "")
            lines.append(f"• {cond}: {desc[:70]}")
        lines.append("")
        lines.append("(Click anywhere to dismiss)")

        pad = 14
        line_h = 22
        bw = 580
        bh = pad * 2 + len(lines) * line_h + 10
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = TOP_BAR_H + 20

        # Dim everything else slightly
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, (38, 40, 44), (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], (bx, by, bw, 36),
                         border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=10)

        y = by + pad
        for i, line in enumerate(lines):
            if i == 0:
                t = fonts.body.render(line, True, (255, 255, 255))
            elif line.startswith("[C]"):
                t = fonts.small.render(line, True, COLORS["concentration"])
            elif line.startswith("•"):
                t = fonts.small.render(line, True, COLORS["warning"])
            else:
                t = fonts.tiny.render(line, True, COLORS["text_dim"])
            screen.blit(t, (bx + pad, y))
            y += line_h

    # --- Terrain palette ---
    def _draw_terrain_palette(self, screen, mp):
        bw = 165
        pad = 8
        item_h = 24
        toolbar_h = 28  # Tool selector row
        fav_h = 28      # Favorites row
        header_h = 48 + toolbar_h + fav_h
        max_visible = (SCREEN_HEIGHT - TOP_BAR_H - 120 - toolbar_h - fav_h) // item_h
        scroll = getattr(self, 'terrain_palette_scroll', 0)

        keys = list(TERRAIN_TYPES.keys())
        total = len(keys)
        bh = min(max_visible, total) * item_h + pad * 2 + header_h

        bx = 10
        by = TOP_BAR_H + 10

        pygame.draw.rect(screen, (35, 37, 42), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 1, border_radius=6)
        hdr = fonts.small.render("Terrain Palette", True, COLORS["accent"])
        screen.blit(hdr, (bx + 6, by + 6))
        hint = fonts.tiny.render("Mid-click:door  Shift:select", True, COLORS["text_dim"])
        screen.blit(hint, (bx + 6, by + 22))

        # --- Tool selector toolbar ---
        ty = by + 38
        tool_names = [("paint", "P"), ("move", "M"), ("rect", "R"), ("elev", "E")]
        tw = (bw - 12) // len(tool_names)
        for i, (tool_id, tool_lbl) in enumerate(tool_names):
            tr = pygame.Rect(bx + 4 + i * tw, ty, tw - 2, toolbar_h - 4)
            is_active = self.terrain_tool == tool_id
            bg = COLORS["accent"] if is_active else (60, 62, 67)
            if tr.collidepoint(mp):
                bg = COLORS["accent_hover"]
            pygame.draw.rect(screen, bg, tr, border_radius=3)
            tl = fonts.tiny.render(tool_lbl, True, COLORS["text_main"])
            screen.blit(tl, (tr.centerx - tl.get_width()//2, tr.centery - tl.get_height()//2))
            # Store click zone
            self.ui_click_zones.append((tr, lambda tid=tool_id: self._set_terrain_tool(tid)))

        # --- Favorites bar ---
        fy = ty + toolbar_h
        fx = bx + 4
        fav_size = 14
        fav_gap = 2
        for fi, fav_type in enumerate(self.terrain_favorites):
            if fi >= 10:
                break
            props = TERRAIN_TYPES.get(fav_type, {})
            fr = pygame.Rect(fx, fy + 2, fav_size, fav_size)
            is_sel = fav_type == self.terrain_selected_type
            pygame.draw.rect(screen, props.get("color", (80, 80, 80)), fr, border_radius=2)
            if is_sel:
                pygame.draw.rect(screen, COLORS["warning"], fr, 2, border_radius=2)
            else:
                pygame.draw.rect(screen, (0, 0, 0), fr, 1, border_radius=2)
            self.ui_click_zones.append((fr, lambda ft=fav_type: self._set_terrain_fav(ft)))
            fx += fav_size + fav_gap

        # --- Terrain type list ---
        y = by + pad + header_h
        visible_keys = keys[scroll:scroll + max_visible]
        for i, ttype in enumerate(visible_keys):
            props = TERRAIN_TYPES[ttype]
            r = pygame.Rect(bx + 4, y, bw - 8, item_h - 2)
            is_sel = ttype == self.terrain_selected_type
            bg = COLORS["accent"] if is_sel else (50, 52, 57)
            if r.collidepoint(mp):
                bg = COLORS["accent_hover"]
            pygame.draw.rect(screen, bg, r, border_radius=3)
            # Color swatch
            pygame.draw.rect(screen, props["color"], (r.x + 3, r.y + 3, 14, 14), border_radius=2)
            pygame.draw.rect(screen, (0, 0, 0), (r.x + 3, r.y + 3, 14, 14), 1, border_radius=2)
            # Label with property indicators
            label = props["label"][:10]
            indicators = ""
            if props.get("elevation_ft", 0) != 0:
                indicators += f" {props['elevation_ft']:+d}"
            if props.get("door"):
                indicators += " D"
            if props.get("blocks_los"):
                indicators += " #"
            lbl = fonts.tiny.render(label + indicators, True, COLORS["text_main"])
            screen.blit(lbl, (r.x + 20, r.y + 4))
            y += item_h

        # Scroll indicators
        if scroll > 0:
            up_arrow = fonts.small.render("^ scroll up ^", True, COLORS["text_dim"])
            screen.blit(up_arrow, (bx + bw//2 - up_arrow.get_width()//2, by + header_h - 4))
        if scroll + max_visible < total:
            dn_arrow = fonts.tiny.render("v more v", True, COLORS["text_dim"])
            screen.blit(dn_arrow, (bx + bw//2 - dn_arrow.get_width()//2, by + bh - 14))



    def _draw_terrain_overlays(self, screen, mp):
        """Draw terrain mode overlays: rect preview, selection, move ghost, paste preview."""
        gsz = self.battle.grid_size

        # Rectangle brush preview
        if self.terrain_tool == "rect" and self.terrain_rect_preview:
            props = TERRAIN_TYPES.get(self.terrain_selected_type, {})
            r, g, b = props.get("color", (80, 80, 80))
            for (gx, gy) in self.terrain_rect_preview:
                sx, sy = self._grid_to_screen(gx, gy)
                s = pygame.Surface((gsz, gsz), pygame.SRCALPHA)
                s.fill((r, g, b, 100))
                screen.blit(s, (sx, sy))
                pygame.draw.rect(screen, (255, 255, 255, 80), (sx, sy, gsz, gsz), 1)

        # Move tool: ghost of dragged object
        if self.terrain_tool == "move" and self.terrain_drag_obj:
            mx_s, my_s = mp
            if mx_s < GRID_W and my_s >= TOP_BAR_H:
                gx, gy = self._screen_to_grid(mx_s, my_s)
                gx, gy = int(gx), int(gy)
                dx, dy = self.terrain_drag_offset
                ox, oy = gx - dx, gy - dy
                sx, sy = self._grid_to_screen(ox, oy)
                t = self.terrain_drag_obj
                s = pygame.Surface((t.width * gsz, t.height * gsz), pygame.SRCALPHA)
                rr, gg, bb = t.color
                s.fill((rr, gg, bb, 120))
                screen.blit(s, (sx, sy))
                pygame.draw.rect(screen, (255, 255, 0), (sx, sy, t.width * gsz, t.height * gsz), 2)

        # Selection rectangle
        if self.terrain_select_start:
            sx1, sy1 = self.terrain_select_start
            sx_s, sy_s = self._grid_to_screen(sx1, sy1)
            if self.terrain_select_end:
                ex, ey = self.terrain_select_end
                ex_s, ey_s = self._grid_to_screen(ex + 1, ey + 1)
                sel_r = pygame.Rect(min(sx_s, ex_s), min(sy_s, ey_s),
                                    abs(ex_s - sx_s), abs(ey_s - sy_s))
            else:
                sel_r = pygame.Rect(sx_s, sy_s, gsz, gsz)
            sel_surf = pygame.Surface((sel_r.width, sel_r.height), pygame.SRCALPHA)
            sel_surf.fill((0, 150, 255, 40))
            screen.blit(sel_surf, sel_r.topleft)
            pygame.draw.rect(screen, (0, 150, 255), sel_r, 2)

        # Paste preview
        if self.terrain_paste_preview and self.terrain_clipboard:
            mx_s, my_s = mp
            if mx_s < GRID_W and my_s >= TOP_BAR_H:
                gx, gy = self._screen_to_grid(mx_s, my_s)
                gx, gy = int(gx), int(gy)
                for item in self.terrain_clipboard:
                    px, py = gx + item["dx"], gy + item["dy"]
                    sx, sy = self._grid_to_screen(px, py)
                    props = TERRAIN_TYPES.get(item["terrain_type"], {})
                    r, g, b = props.get("color", (80, 80, 80))
                    s = pygame.Surface((gsz, gsz), pygame.SRCALPHA)
                    s.fill((r, g, b, 90))
                    screen.blit(s, (sx, sy))
                    pygame.draw.rect(screen, (0, 255, 150), (sx, sy, gsz, gsz), 1)

        # Elevation tool: highlight terrain under cursor
        if self.terrain_tool == "elev":
            mx_s, my_s = mp
            if mx_s < GRID_W and my_s >= TOP_BAR_H:
                gx, gy = self._screen_to_grid(mx_s, my_s)
                gx, gy = int(gx), int(gy)
                t = self.battle.get_terrain_at(gx, gy)
                if t:
                    sx, sy = self._grid_to_screen(t.grid_x, t.grid_y)
                    pygame.draw.rect(screen, (255, 200, 0), (sx, sy, t.width * gsz, t.height * gsz), 3)
                    elbl = fonts.small.render(f"Elev: {t.elevation}ft  (L:+5 R:-5)", True, (255, 220, 0))
                    screen.blit(elbl, (sx, sy - 20))

    def _draw_map_save_menu(self, screen, mp):
        """Draw map save/load dropdown menu."""
        maps_dir = os.path.join(os.path.dirname(__file__), "..", "saves", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        map_files = sorted([f for f in os.listdir(maps_dir) if f.endswith(".json")])

        mw, item_h = 200, 30
        mx_pos = 696
        items = ["[Save Current Map]", "[Clear All Terrain]"] + map_files
        mh = len(items) * item_h + 10
        my_pos = SCREEN_HEIGHT - 65 - mh - 5

        pygame.draw.rect(screen, (35, 37, 42), (mx_pos, my_pos, mw, mh), border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], (mx_pos, my_pos, mw, mh), 1, border_radius=6)

        y = my_pos + 5
        for item in items:
            r = pygame.Rect(mx_pos + 4, y, mw - 8, item_h - 2)
            bg = (50, 52, 57)
            if r.collidepoint(mp):
                bg = COLORS["accent_hover"]
            pygame.draw.rect(screen, bg, r, border_radius=3)
            color = COLORS["success"] if item.startswith("[Save") else COLORS["danger"] if item.startswith("[Clear") else COLORS["text_main"]
            lbl = fonts.tiny.render(item.replace(".json", "")[:22], True, color)
            screen.blit(lbl, (r.x + 6, r.y + 6))
            if item == "[Save Current Map]":
                self.ui_click_zones.append((r, self._map_save_prompt))
            elif item == "[Clear All Terrain]":
                self.ui_click_zones.append((r, self._map_clear_all))
            else:
                filepath = os.path.join(maps_dir, item)
                self.ui_click_zones.append((r, lambda fp=filepath: self._load_map_only(fp)))
            y += item_h



    def _draw_win_probability_bar(self, screen, x, y, w, h):
        """Draw the win probability bar on the UI."""
        if not self.win_prob_cache:
            return

        prob = self.win_prob_cache["probability"]
        pct = self.win_prob_cache["percentage"]
        label = self.win_prob_cache["label"]
        
        # Center point
        cx = x + w // 2

        # Background
        pygame.draw.rect(screen, (20, 22, 25), (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], (x, y, w, h), 1, border_radius=4)
        
        # Center line
        pygame.draw.line(screen, (80, 80, 80), (cx, y), (cx, y+h), 1)

        # Tug of War Logic
        # 0.0 = Full Red (Left), 0.5 = Empty (Center), 1.0 = Full Green (Right)
        
        if prob > 0.5:
            # Winning (Green to right)
            bar_w = int((prob - 0.5) * w) # Scale 0.5->1.0 to 0->w/2
            # Cap at w/2 - 2
            bar_w = min(bar_w, w//2 - 2)
            if bar_w > 0:
                r = pygame.Rect(cx, y+2, bar_w, h-4)
                # Gradient-ish color based on intensity
                g_val = min(255, 100 + int((prob-0.5)*300))
                pygame.draw.rect(screen, (40, g_val, 60), r, border_top_right_radius=3, border_bottom_right_radius=3)
            
            txt_str = f"Win Chance: {pct:.0f}%"
            txt_col = (150, 255, 150)
        else:
            # Losing (Red to left)
            loss_prob = 1.0 - prob
            bar_w = int((0.5 - prob) * w)
            bar_w = min(bar_w, w//2 - 2)
            if bar_w > 0:
                r = pygame.Rect(cx - bar_w, y+2, bar_w, h-4)
                r_val = min(255, 100 + int((loss_prob-0.5)*300))
                pygame.draw.rect(screen, (r_val, 60, 60), r, border_top_left_radius=3, border_bottom_left_radius=3)
            
            txt_str = f"Loss Risk: {loss_prob*100:.0f}%"
            txt_col = (255, 150, 150)

        # Text
        txt = fonts.tiny.render(txt_str, True, txt_col)
        # Center text
        screen.blit(txt, (x + w//2 - txt.get_width()//2, y + (h - txt.get_height()) // 2))

        # Trend arrow
        trend = self.battle.win_calculator.get_trend()
        if trend == "improving":
            arrow = fonts.tiny.render("^", True, (0, 200, 0))
            screen.blit(arrow, (x + w - 15, y + 2))
        elif trend == "declining":
            arrow = fonts.tiny.render("v", True, (200, 0, 0))
            screen.blit(arrow, (x + w - 15, y + 2))

    def _draw_advisor_panel(self, screen, x, y, w, h):
        """Draw the DM advisor panel showing AI suggestions and ratings."""
        if not self.show_advisor_panel:
            return

        # Background
        pygame.draw.rect(screen, (25, 28, 35), (x, y, w, h), border_radius=6)
        pygame.draw.rect(screen, COLORS["spell"], (x, y, w, h), 1, border_radius=6)

        # Header
        header = fonts.small.render("DM ADVISOR", True, COLORS["spell"])
        screen.blit(header, (x + 4, y + 2))

        cy = y + 20

        # AI Suggestion
        if self.dm_suggestion_cache:
            sug = self.dm_suggestion_cache

            # Suggestion text
            if sug.ai_suggestion:
                lbl = fonts.tiny.render("AI Recommends:", True, COLORS["accent"])
                screen.blit(lbl, (x + 4, cy))
                cy += 14

                # Wrap suggestion text
                words = sug.ai_suggestion.split()
                line = ""
                for word in words:
                    test = line + " " + word if line else word
                    if fonts.tiny.size(test)[0] > w - 10:
                        t = fonts.tiny.render(line, True, COLORS["text_main"])
                        screen.blit(t, (x + 6, cy))
                        cy += 12
                        line = word
                    else:
                        line = test
                if line:
                    t = fonts.tiny.render(line, True, COLORS["text_main"])
                    screen.blit(t, (x + 6, cy))
                    cy += 14

            # Tactical notes
            for note in sug.tactical_notes[:4]:
                color = COLORS["danger"] if "URGENT" in note else COLORS["warning"] if "WARNING" in note else COLORS["text_dim"]
                # Truncate long notes
                display = note[:60] + "..." if len(note) > 60 else note
                t = fonts.tiny.render(display, True, color)
                screen.blit(t, (x + 6, cy))
                cy += 12

        # Rating of last action
        if self.dm_rating_cache:
            r = self.dm_rating_cache
            cy += 4
            pygame.draw.line(screen, COLORS["border"], (x + 4, cy), (x + w - 4, cy))
            cy += 4

            rating_colors = {
                "Optimal": (0, 200, 80),
                "Good": (100, 200, 60),
                "Decent": (200, 180, 40),
                "Suboptimal": (200, 120, 40),
                "Poor": (200, 60, 60),
            }
            r_color = rating_colors.get(r.rating_label, COLORS["text_main"])

            t = fonts.tiny.render(f"Last: {r.player_action}", True, COLORS["text_main"])
            screen.blit(t, (x + 4, cy))
            cy += 12

            t = fonts.tiny.render(f"Rating: {r.rating_label} ({r.rating:.0%})", True, r_color)
            screen.blit(t, (x + 4, cy))
            cy += 14

    def _draw_battle_report_modal(self, screen):
        """Draw the post-battle report modal."""
        if not self.report_modal_open or not self.battle_report_text:
            return

        # Full-screen overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        # Modal dimensions
        mw, mh = min(900, SCREEN_WIDTH - 40), SCREEN_HEIGHT - 80
        mx = (SCREEN_WIDTH - mw) // 2
        my = 40

        # Background
        pygame.draw.rect(screen, COLORS["panel"], (mx, my, mw, mh), border_radius=10)
        pygame.draw.rect(screen, COLORS["accent"], (mx, my, mw, mh), 2, border_radius=10)

        # Title
        title = fonts.header.render("BATTLE REPORT", True, COLORS["accent"])
        screen.blit(title, (mx + 20, my + 10))

        # Close / Save buttons
        btn_close_rect = pygame.Rect(mx + mw - 120, my + 10, 100, 30)
        pygame.draw.rect(screen, COLORS["danger"], btn_close_rect, border_radius=4)
        ct = fonts.small.render("CLOSE", True, (255, 255, 255))
        screen.blit(ct, (btn_close_rect.x + 30, btn_close_rect.y + 5))

        btn_save_rect = pygame.Rect(mx + mw - 240, my + 10, 100, 30)
        pygame.draw.rect(screen, COLORS["success"], btn_save_rect, border_radius=4)
        st = fonts.small.render("SAVE", True, (255, 255, 255))
        screen.blit(st, (btn_save_rect.x + 30, btn_save_rect.y + 5))

        # Register button click zones
        self.ui_click_zones.append((btn_close_rect, lambda: setattr(self, 'report_modal_open', False)))
        self.ui_click_zones.append((btn_save_rect, self._save_battle_report))

        # Content area (scrollable text)
        content_rect = pygame.Rect(mx + 10, my + 50, mw - 20, mh - 60)
        pygame.draw.rect(screen, (15, 17, 20), content_rect)

        screen.set_clip(content_rect)
        lines = self.battle_report_text.split("\n")
        ly = content_rect.y + 5 + self.report_scroll
        for line in lines:
            if ly > content_rect.bottom:
                break
            if ly + 14 >= content_rect.y:
                color = COLORS["accent"] if line.startswith("=") or line.startswith("-") else COLORS["text_main"]
                if "MVP:" in line:
                    color = (255, 215, 0)
                elif "[Player]" in line or "ALIVE" in line:
                    color = COLORS["success"]
                elif "DEAD" in line:
                    color = COLORS["danger"]
                elif "CRIT" in line:
                    color = (255, 100, 100)
                t = fonts.tiny.render(line, True, color)
                screen.blit(t, (content_rect.x + 5, ly))
            ly += 14
        screen.set_clip(None)

        # MVP highlight bar
        mvp = self.battle_report.get("mvp", {})
        if mvp.get("name") and mvp["name"] != "N/A":
            mvp_text = f"MVP: {mvp['name']} - DMG:{mvp.get('damage_dealt', 0)} HEAL:{mvp.get('healing_done', 0)} KILLS:{mvp.get('kills', 0)}"
            mvp_bar = pygame.Rect(mx + 10, my + mh - 8, mw - 20, 6)
            pygame.draw.rect(screen, (255, 215, 0), mvp_bar, border_radius=3)

    # --- Terrain mode toggle ---


    def _draw_map_browser(self, screen, mp):
        """Draw the premade map selection overlay."""
        from data.maps import get_map_names
        maps = get_map_names()

        bw, bh = 350, 50 * len(maps) + 60
        bx = (SCREEN_WIDTH - bw) // 2
        by = (SCREEN_HEIGHT - bh) // 2

        # Background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, (35, 37, 42), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(screen, COLORS["accent"], (bx, by, bw, 36),
                         border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 2, border_radius=8)

        hdr = fonts.body.render("Load Premade Map", True, (255, 255, 255))
        screen.blit(hdr, (bx + 10, by + 8))

        y = by + 44
        for key, name, desc in maps:
            r = pygame.Rect(bx + 8, y, bw - 16, 42)
            bg = COLORS["accent_hover"] if r.collidepoint(mp) else (50, 52, 57)
            pygame.draw.rect(screen, bg, r, border_radius=4)
            nt = fonts.small.render(name, True, COLORS["text_main"])
            screen.blit(nt, (r.x + 8, r.y + 4))
            dt = fonts.tiny.render(desc[:45], True, COLORS["text_dim"])
            screen.blit(dt, (r.x + 8, r.y + 24))
            y += 50

    # Re-implementing separate callbacks for clarity


    def _draw_add_entity_modal(self, screen, mp):
        """Draw the mid-battle entity add modal."""
        bw, bh = 500, 500
        bx = SCREEN_WIDTH // 2 - bw // 2
        by = SCREEN_HEIGHT // 2 - bh // 2

        # Background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        screen.blit(ov, (0, 0))
        pygame.draw.rect(screen, (38, 40, 44), (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(screen, COLORS["accent"], (bx, by, bw, 40), border_top_left_radius=8, border_top_right_radius=8)

        # Title
        t = fonts.body_bold.render("ADD ENTITY TO BATTLE", True, (255, 255, 255))
        screen.blit(t, (bx + 10, by + 8))

        # Search bar
        search_y = by + 50
        pygame.draw.rect(screen, (55, 58, 62), (bx + 10, search_y, bw - 100, 28), border_radius=4)
        st = fonts.small.render(f"Search: {self.add_entity_search}_", True, COLORS["text_main"])
        screen.blit(st, (bx + 15, search_y + 4))

        # Player/Enemy toggle
        toggle_r = pygame.Rect(bx + bw - 85, search_y, 75, 28)
        toggle_c = COLORS["player"] if self.add_entity_is_player else COLORS["enemy"]
        pygame.draw.rect(screen, toggle_c, toggle_r, border_radius=4)
        toggle_txt = "PLAYER" if self.add_entity_is_player else "ENEMY"
        tt = fonts.tiny.render(toggle_txt, True, (255, 255, 255))
        screen.blit(tt, (toggle_r.centerx - tt.get_width() // 2, toggle_r.centery - tt.get_height() // 2))
        self.ui_click_zones.append((toggle_r, lambda: setattr(self, 'add_entity_is_player', not self.add_entity_is_player)))

        # Monster/Hero list
        list_y = search_y + 36
        all_monsters = library.get_all_monsters()
        all_heroes = hero_list

        # Combine and filter
        combined = [(m, False) for m in all_monsters] + [(h, True) for h in all_heroes]
        if self.add_entity_search:
            search_lower = self.add_entity_search.lower()
            combined = [(s, p) for s, p in combined if search_lower in s.name.lower()]

        # Sort: heroes first, then by CR
        combined.sort(key=lambda x: (not x[1], x[0].challenge_rating, x[0].name))

        max_visible = (bh - 120) // 26
        visible = combined[self.add_entity_scroll:self.add_entity_scroll + max_visible]

        for i, (stats, is_hero) in enumerate(visible):
            iy = list_y + i * 26
            cr_str = f"CR {stats.challenge_rating:.3g}" if stats.challenge_rating else "Hero"
            label = f"{'[H]' if is_hero else '[M]'} {stats.name} ({cr_str})"
            r = pygame.Rect(bx + 10, iy, bw - 20, 24)
            bg = (55, 58, 62)
            if r.collidepoint(mp):
                bg = (80, 83, 88)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            c = COLORS["player"] if is_hero else COLORS["text_main"]
            s = fonts.tiny.render(label, True, c)
            screen.blit(s, (r.x + 6, r.y + 4))
            self.ui_click_zones.append((r, lambda st=stats, ip=is_hero: self._add_entity_to_battle(st, is_player=ip)))

        # Scroll indicator
        if len(combined) > max_visible:
            total_pages = (len(combined) + max_visible - 1) // max_visible
            current_page = self.add_entity_scroll // max_visible + 1
            pg_txt = fonts.tiny.render(f"Page {current_page}/{total_pages} (scroll to browse)", True, COLORS["text_dim"])
            screen.blit(pg_txt, (bx + 10, by + bh - 25))


