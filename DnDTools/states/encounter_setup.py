import pygame
import os
import re
import copy
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from engine.entities import Entity
from data.models import CreatureStats
from data.library import library
from data.heroes import hero_list
from data.hero_import import import_heroes_from_file, export_heroes_to_file
from engine.win_probability import assess_encounter_danger
from states.game_state_base import GameState

class EncounterSetupState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.roster = []
        self.scroll_monster = 0
        self.scroll_hero    = 0
        self.importing = False
        self.ts_last_update = 0
        all_monsters = library.get_all_monsters()
        self.monsters_by_cr: dict = {}
        for m in all_monsters:
            cr = m.challenge_rating
            self.monsters_by_cr.setdefault(cr, []).append(m)
        self.sorted_crs = sorted(self.monsters_by_cr.keys())
        self.selected_cr = None
        self.active_monster_btns = []
        self.search_text = ""
        self.search_active = False
        self.difficulty_cache = None
        self.last_roster_hash = 0
        
        self.planes = ["Material Plane", "Feywild", "Shadowfell", "Nine Hells", "Abyss", "Elemental Plane", "Astral Plane", "Ethereal Plane", "Far Realm"]
        self.current_plane_idx = 0
        
        self.btn_plane = Button(SCREEN_WIDTH-270, 20, 230, 35, f"Plane: {self.planes[0]}",
                                self._cycle_plane, color=COLORS["panel"])

        self.cr_btns = []
        y = 130
        for cr in self.sorted_crs:
            label = f"CR {cr:.3g}" if cr % 1 != 0 else f"CR {int(cr)}"
            self.cr_btns.append(Button(30, y, 110, 35, label, lambda c=cr: self._select_cr(c),
                                       color=COLORS["panel"]))
            y += 40

        # Load disk-saved heroes into hero_list (if not already present)
        self._load_disk_heroes()
        self.hero_btns = []
        self._rebuild_hero_buttons()

        # Lair toggle: when enabled, creatures with lair actions will use them at initiative 20
        self.lair_active = False
        self.btn_lair = Button(SCREEN_WIDTH-270, 60, 230, 35, "Lair: OFF",
                               self._toggle_lair, color=COLORS["panel"])

        self.action_btns = [
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-100, 230, 55, "START BATTLE",
                   self._start_battle, color=COLORS["success"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-165, 230, 45, "Long Rest All",
                   self._long_rest, color=COLORS["accent"]),
            Button(20, 20, 110, 35, "< Menu",
                   lambda: manager.change_state("MENU"), color=COLORS["panel"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-220, 230, 45, "Clear Roster",
                   lambda: self.roster.clear(), color=COLORS["danger"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-275, 230, 45, "Import Heroes (JSON)",
                   self._import_heroes_file, color=COLORS["spell"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-330, 230, 45, "Export Heroes (JSON)",
                   self._export_heroes_file, color=COLORS["neutral"]),
        ]

        # Hero import/export directories
        self.heroes_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        os.makedirs(self.heroes_dir, exist_ok=True)

    def _cycle_plane(self):
        self.current_plane_idx = (self.current_plane_idx + 1) % len(self.planes)
        self.btn_plane.text = f"Plane: {self.planes[self.current_plane_idx]}"

    def _toggle_lair(self):
        """Toggle lair mode on/off. When on, creatures with lair actions use them at init 20."""
        self.lair_active = not self.lair_active
        if self.lair_active:
            self.btn_lair.text = "Lair: ON"
            self.btn_lair.color = COLORS["danger"]
        else:
            self.btn_lair.text = "Lair: OFF"
            self.btn_lair.color = COLORS["panel"]

    def enable_import(self):
        self.importing = True
        self.roster.clear()

    def update_external_data(self, data):
        """Called by main.py when TaleSpire data arrives."""
        if not self.importing:
            return

        self.ts_last_update = pygame.time.get_ticks()

        new_roster = []
        for mini in data:
            name = mini.get("name", "Unknown").strip()
            raw_x = float(mini.get("x", 0))
            raw_z = float(mini.get("z", 0))
            
            # Convert coordinates (TaleSpire units -> Grid units)
            # Assuming 1 TS unit = 5ft = 1 Grid unit
            gx = raw_x
            gy = raw_z

            # Try to match stats
            stats = None
            is_player = False

            # 1. Check Heroes
            for h in hero_list:
                if h.name.lower() == name.lower():
                    stats = h
                    is_player = True
                    break
            
            # 2. Check Monsters
            if not stats:
                try:
                    stats = library.get_monster(name)
                except ValueError:
                    # Try stripping numbers (e.g. "Goblin 1" -> "Goblin")
                    base = re.sub(r'\s+\d+$', '', name)
                    try:
                        stats = library.get_monster(base)
                    except ValueError:
                        # 3. Fallback
                        from data.models import CreatureStats
                        stats = CreatureStats(name=name, hit_points=10, armor_class=10, challenge_rating=0)

            # Create entity
            ent = Entity(stats, gx, gy, is_player=is_player)
            # Ensure name matches TaleSpire exactly (for tracking)
            ent.name = name
            new_roster.append(ent)

        self.roster = new_roster

    def _calculate_difficulty(self):
        # Check cache to avoid heavy recalculation every frame
        current_sig = tuple((e.name, e.hp, e.max_hp, e.is_player) for e in self.roster)
        current_hash = hash(current_sig)
        
        if self.difficulty_cache and self.last_roster_hash == current_hash:
            return self.difficulty_cache

        heroes = [e for e in self.roster if e.is_player]
        monsters = [e for e in self.roster if not e.is_player]
        if not heroes or not monsters:
            return "N/A", 0, 0, None, None

        # Use the enhanced encounter danger assessment
        danger = assess_encounter_danger(heroes, monsters)

        # NEW: Calculate win probability
        from engine.battle import BattleSystem
        win_prob = None
        try:
            # Create a temporary battle system to use its calculator
            # This is a bit heavy but ensures we use the same logic as in-battle
            temp_battle = BattleSystem(log_callback=lambda msg: None, initial_entities=list(self.roster))
            win_prob = temp_battle.get_win_probability()
        except Exception as e:
            print(f"Win prob calc error: {e}")

        self.difficulty_cache = (danger["difficulty"], danger["xp_total"], danger["adjusted_xp"], danger, win_prob)
        self.last_roster_hash = current_hash
        return self.difficulty_cache

    def _update_monster_list(self):
        self.active_monster_btns = []
        self.scroll_monster = 0
        if self.search_text:
            # Search mode
            all_mons = library.get_all_monsters()
            filtered = [m for m in all_mons if self.search_text.lower() in m.name.lower()]
            for m in filtered:
                self.active_monster_btns.append(
                    Button(160, 0, 250, 35, m.name, lambda mon=m: self._add_monster(mon),
                           color=COLORS["panel"]))
        elif self.selected_cr is not None:
            # CR mode
            for m in self.monsters_by_cr[self.selected_cr]:
                self.active_monster_btns.append(
                    Button(160, 0, 250, 35, m.name, lambda mon=m: self._add_monster(mon),
                           color=COLORS["panel"]))

    def _select_cr(self, cr):
        self.selected_cr = cr
        self.search_text = "" # Clear search when picking CR
        self._update_monster_list()

    def _load_disk_heroes(self):
        """Auto-load heroes saved to disk into hero_list if not already present."""
        heroes_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        if not os.path.exists(heroes_dir):
            return
        for f in sorted(os.listdir(heroes_dir)):
            if not f.endswith(".json"):
                continue
            try:
                heroes = import_heroes_from_file(os.path.join(heroes_dir, f))
                for h in heroes:
                    if not any(existing.name == h.name for existing in hero_list):
                        hero_list.append(h)
            except Exception:
                pass

    def _rebuild_hero_buttons(self):
        """Rebuild hero selection buttons from current hero_list."""
        self.hero_btns = []
        for h in hero_list:
            lvl_info = ""
            if h.character_level > 0:
                lvl_info = f" Lv{h.character_level}"
                if h.character_class:
                    lvl_info = f" {h.character_class[:3]}Lv{h.character_level}"
            label = f"+ {h.name}{lvl_info}"
            self.hero_btns.append(Button(430, 0, 220, 35, label,
                                         lambda hero=h: self._add_hero(hero),
                                         color=COLORS["player"]))

    def _add_hero(self, stats):
        y_pos = 2 + len([e for e in self.roster if e.is_player]) * 2
        self.roster.append(Entity(stats, 3, y_pos, is_player=True))

    def _add_monster(self, stats):
        import copy
        stats_copy = copy.deepcopy(stats)
        # Give duplicate monsters numbered names
        same = sum(1 for e in self.roster if not e.is_player and e.name.startswith(stats.name))
        if same > 0:
            stats_copy.name = f"{stats.name} {same+1}"
        count = len([e for e in self.roster if not e.is_player])
        x_pos = 14 + (count % 3) * 2
        y_pos = 3 + (count // 3) * 2
        self.roster.append(Entity(stats_copy, x_pos, y_pos, is_player=False))

    def _long_rest(self):
        for e in self.roster:
            e.long_rest()

    def _import_heroes_file(self):
        """Import heroes from JSON files in the heroes/ directory and refresh buttons."""
        if not os.path.exists(self.heroes_dir):
            return
        json_files = [f for f in os.listdir(self.heroes_dir) if f.endswith(".json")]
        if not json_files:
            return
        for f in json_files:
            try:
                heroes = import_heroes_from_file(os.path.join(self.heroes_dir, f))
                for h in heroes:
                    # Add to hero_list if not already present
                    if not any(existing.name == h.name for existing in hero_list):
                        hero_list.append(h)
                    y_pos = 2 + len([e for e in self.roster if e.is_player]) * 2
                    self.roster.append(Entity(h, 3, y_pos, is_player=True))
            except Exception as ex:
                print(f"Import error ({f}): {ex}")
        self._rebuild_hero_buttons()

    def _export_heroes_file(self):
        """Export all player heroes in roster to heroes/ directory."""
        player_heroes = [e.stats for e in self.roster if e.is_player]
        if not player_heroes:
            return
        filepath = os.path.join(self.heroes_dir, "exported_heroes.json")
        export_heroes_to_file(player_heroes, filepath)

    def _start_battle(self):
        if not self.roster:
            return
        from states.battle_state import BattleState
        self.manager.states["BATTLE"] = BattleState(self.manager, list(self.roster))
        self.manager.states["BATTLE"].battle.current_plane = self.planes[self.current_plane_idx]
        # Pass lair enabled setting to battle system
        self.manager.states["BATTLE"].battle.lair_enabled = self.lair_active
        self.importing = False  # Stop syncing setup
        self.manager.change_state("BATTLE")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(160, 75, 250, 30).collidepoint(event.pos):
                    self.search_active = True
                else:
                    self.search_active = False
            
            if event.type == pygame.KEYDOWN and self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                elif event.unicode.isprintable():
                    self.search_text += event.unicode
                self._update_monster_list()

            if event.type == pygame.MOUSEWHEEL:
                if pygame.mouse.get_pos()[0] < 160:
                    self.scroll_hero = min(0, self.scroll_hero + event.y * 25)
                else:
                    self.scroll_monster = min(0, self.scroll_monster + event.y * 25)
            for b in self.action_btns + self.cr_btns + [self.btn_plane, self.btn_lair]:
                b.handle_event(event)
            for i, b in enumerate(self.hero_btns):
                b.rect.y = 130 + i * 40 + self.scroll_hero
                b.handle_event(event)
            for i, b in enumerate(self.active_monster_btns):
                b.rect.y = 130 + i * 40 + self.scroll_monster
                b.handle_event(event)

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        mp = pygame.mouse.get_pos()
        # Header
        t = fonts.header.render("Encounter Setup", True, COLORS["accent"])
        screen.blit(t, (30, 80))
        
        if self.importing:
            is_connected = (pygame.time.get_ticks() - self.ts_last_update) < 3000
            color = COLORS["success"] if is_connected else COLORS["warning"]
            text = "SYNCING WITH TALESPIRE..." if is_connected else "WAITING FOR TALESPIRE..."
            imp_msg = fonts.header.render(text, True, color)
            screen.blit(imp_msg, (450, 80))

        # Search box
        search_rect = pygame.Rect(160, 75, 250, 30)
        col = COLORS["accent"] if self.search_active else COLORS["border"]
        pygame.draw.rect(screen, (10,10,10), search_rect)
        pygame.draw.rect(screen, col, search_rect, 2)
        txt_surf = fonts.small.render(self.search_text, True, COLORS["text_main"])
        screen.blit(txt_surf, (search_rect.x + 5, search_rect.y + 5))
        if not self.search_text and not self.search_active:
            placeholder = fonts.small.render("Search...", True, COLORS["text_dim"])
            screen.blit(placeholder, (search_rect.x + 5, search_rect.y + 5))

        # Column labels
        for lbl, x in [("CR Level", 30), ("Monsters", 160), ("Heroes", 430), ("Roster", 700)]:
            screen.blit(fonts.small.render(lbl, True, COLORS["text_dim"]), (x, 110))
        # CR buttons
        for b in self.cr_btns:
            if self.selected_cr is not None and b.text == (f"CR {self.selected_cr:.3g}" if self.selected_cr % 1 != 0 else f"CR {int(self.selected_cr)}"):
                pygame.draw.rect(screen, COLORS["accent"], b.rect.inflate(4, 4), 2, border_radius=6)
            b.draw(screen, mp)
        # Monster buttons (clipped)
        clip = pygame.Rect(160, 120, 260, SCREEN_HEIGHT - 200)
        screen.set_clip(clip)
        for i, b in enumerate(self.active_monster_btns):
            b.rect.y = 130 + i * 40 + self.scroll_monster
            b.draw(screen, mp)
        screen.set_clip(None)
        # Hero buttons (clipped)
        clip2 = pygame.Rect(430, 120, 240, SCREEN_HEIGHT - 200)
        screen.set_clip(clip2)
        for i, b in enumerate(self.hero_btns):
            b.rect.y = 130 + i * 40 + self.scroll_hero
            b.draw(screen, mp)
        screen.set_clip(None)
        # Roster
        y = 130
        for e in self.roster:
            c = COLORS["player"] if e.is_player else COLORS["enemy"]
            txt = fonts.small.render(f"{'[P]' if e.is_player else '[M]'} {e.name}  HP:{e.hp}/{e.max_hp}  AC:{e.stats.armor_class}", True, c)
            screen.blit(txt, (700, y))
            y += 22
            
        # Difficulty Display (enhanced with danger assessment)
        diff, raw_xp, adj_xp, danger, win_prob = self._calculate_difficulty()
        diff_colors = {
            "Trivial": COLORS["text_dim"], "Easy": COLORS["success"],
            "Medium": COLORS["warning"], "Hard": COLORS["danger"],
            "Deadly": (255, 40, 40), "TPK Risk": (255, 0, 0),
        }
        diff_c = diff_colors.get(diff, COLORS["success"])
        stats_s = fonts.header.render(f"Difficulty: {diff}  (XP: {raw_xp} / Adj: {adj_xp})", True, diff_c)
        screen.blit(stats_s, (700, SCREEN_HEIGHT - 130))

        if danger:
            # Show danger score and combat estimates
            ds = danger.get("danger_score", 0)
            bar_w = 200
            bar_h = 12
            bar_x = 700
            bar_y = SCREEN_HEIGHT - 100
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            fill = int(bar_w * min(1.0, ds / 100))
            bc = (200, 60, 60) if ds > 60 else (200, 180, 40) if ds > 30 else (40, 180, 80)
            if fill > 0:
                pygame.draw.rect(screen, bc, (bar_x, bar_y, fill, bar_h), border_radius=4)
            ds_txt = fonts.tiny.render(f"Danger: {ds}/100", True, COLORS["text_main"])
            screen.blit(ds_txt, (bar_x + bar_w + 10, bar_y - 1))

            est = danger.get("combat_estimate", {})
            if est:
                e_txt = fonts.tiny.render(
                    f"Est. {est.get('expected_rounds', '?')} rounds | "
                    f"P-DPR:{est.get('player_dpr', 0):.0f} vs E-DPR:{est.get('enemy_dpr', 0):.0f}",
                    True, COLORS["text_dim"])
                screen.blit(e_txt, (700, SCREEN_HEIGHT - 82))

            surv = danger.get("survival_estimate", "")
            if surv:
                surv_txt = fonts.tiny.render(surv, True, diff_c)
                screen.blit(surv_txt, (700, SCREEN_HEIGHT - 68))

        # Win Probability Bar
        if win_prob:
            self._draw_win_probability_bar(screen, win_prob, 700, SCREEN_HEIGHT - 45, 460, 22)

        # Action buttons
        for b in self.action_btns:
            b.draw(screen, mp)
        self.btn_plane.draw(screen, mp)
        self.btn_lair.draw(screen, mp)

    def _draw_win_probability_bar(self, screen, win_prob_cache, x, y, w, h):
        """Draw the win probability bar on the UI (setup screen version)."""
        if not win_prob_cache:
            return

        prob = win_prob_cache["probability"]
        pct = win_prob_cache["percentage"]
        
        cx = x + w // 2
        pygame.draw.rect(screen, (20, 22, 25), (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], (x, y, w, h), 1, border_radius=4)
        pygame.draw.line(screen, (80, 80, 80), (cx, y), (cx, y+h), 1)

        if prob > 0.5:
            bar_w = int((prob - 0.5) * w)
            bar_w = min(bar_w, w//2 - 2)
            if bar_w > 0:
                r = pygame.Rect(cx, y+2, bar_w, h-4)
                g_val = min(255, 100 + int((prob-0.5)*300))
                pygame.draw.rect(screen, (40, g_val, 60), r, border_top_right_radius=3, border_bottom_right_radius=3)
            txt_str = f"Win Chance: {pct:.0f}%"
            txt_col = (150, 255, 150)
        else:
            loss_prob = 1.0 - prob
            bar_w = int((0.5 - prob) * w)
            bar_w = min(bar_w, w//2 - 2)
            if bar_w > 0:
                r = pygame.Rect(cx - bar_w, y+2, bar_w, h-4)
                r_val = min(255, 100 + int((loss_prob-0.5)*300))
                pygame.draw.rect(screen, (r_val, 60, 60), r, border_top_left_radius=3, border_bottom_left_radius=3)
            txt_str = f"Loss Risk: {loss_prob*100:.0f}%"
            txt_col = (255, 150, 150)

        txt = fonts.tiny.render(txt_str, True, txt_col)
        screen.blit(txt, (x + w//2 - txt.get_width()//2, y + (h - txt.get_height()) // 2))

