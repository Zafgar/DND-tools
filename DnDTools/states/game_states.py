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

SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


# ============================================================
# Base GameState
# ============================================================
class GameState:
    def __init__(self, manager): self.manager = manager
    def handle_events(self, events): pass
    def update(self): pass
    def draw(self, screen): pass

# ============================================================
# Scenario Modal (Save/Load UI)
# ============================================================
class ScenarioModal:
    def __init__(self, mode, callback):
        self.mode = mode  # "save" or "load"
        self.callback = callback
        self.w, self.h = 600, 500
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2
        
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)
        self.files = sorted([f for f in os.listdir(SAVES_DIR) if f.endswith(".json")])
        
        self.selected_file = None
        self.input_text = "encounter" if mode == "save" else ""
        self.scroll_y = 0
        
        self.btn_action = Button(self.x + self.w - 150, self.y + self.h - 60, 130, 45, 
                                 "SAVE" if mode == "save" else "LOAD", self._confirm, color=COLORS["success"])
        self.btn_cancel = Button(self.x + 20, self.y + self.h - 60, 130, 45, 
                                 "CANCEL", lambda: self.callback(None), color=COLORS["danger"])

    def _confirm(self):
        fname = self.input_text
        if self.mode == "load":
            if not self.selected_file: return
            fname = self.selected_file
        
        if not fname: return
        if not fname.endswith(".json"): fname += ".json"
        self.callback(os.path.join(SAVES_DIR, fname))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.callback(None)
            elif self.mode == "save":
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    self._confirm()
                elif event.unicode.isprintable() and len(self.input_text) < 30:
                    self.input_text += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # File list
            list_rect = pygame.Rect(self.x + 20, self.y + 60, self.w - 40, self.h - 140)
            if list_rect.collidepoint(mx, my):
                rel_y = my - (self.y + 60) - self.scroll_y
                idx = rel_y // 30
                if 0 <= idx < len(self.files):
                    self.selected_file = self.files[int(idx)]
                    if self.mode == "save":
                        self.input_text = self.selected_file.replace(".json", "")
            
            # Scroll (simple)
            if event.button == 4: self.scroll_y = min(0, self.scroll_y + 20)
            if event.button == 5: self.scroll_y = max(-(len(self.files)*30 - list_rect.height), self.scroll_y - 20)

        self.btn_action.handle_event(event)
        self.btn_cancel.handle_event(event)

    def draw(self, screen, mp):
        # Overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        screen.blit(ov, (0,0))
        
        # Box
        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h), 2, border_radius=10)
        
        # Header
        title = "Save Scenario" if self.mode == "save" else "Load Scenario"
        t = fonts.header.render(title, True, COLORS["accent"])
        screen.blit(t, (self.x + 20, self.y + 15))
        
        # File list area
        list_rect = pygame.Rect(self.x + 20, self.y + 60, self.w - 40, self.h - 140)
        pygame.draw.rect(screen, (20,22,25), list_rect)
        pygame.draw.rect(screen, COLORS["border"], list_rect, 1)
        
        screen.set_clip(list_rect)
        fy = self.y + 60 + self.scroll_y
        for f in self.files:
            col = COLORS["text_main"]
            if f == self.selected_file:
                pygame.draw.rect(screen, COLORS["accent"], (self.x+22, fy, self.w-44, 28))
                col = (255,255,255)
            
            txt = fonts.body.render(f, True, col)
            screen.blit(txt, (self.x + 30, fy + 2))
            fy += 30
        screen.set_clip(None)
        
        # Input box (Save mode)
        if self.mode == "save":
            lbl = fonts.small.render("Filename:", True, COLORS["text_dim"])
            screen.blit(lbl, (self.x + 20, self.y + self.h - 110))
            
            in_rect = pygame.Rect(self.x + 100, self.y + self.h - 115, 300, 30)
            pygame.draw.rect(screen, (10,10,10), in_rect)
            pygame.draw.rect(screen, COLORS["border"], in_rect, 1)
            
            it = fonts.body.render(self.input_text, True, (255,255,255))
            screen.blit(it, (in_rect.x + 5, in_rect.y + 2))
            
        self.btn_action.draw(screen, mp)
        self.btn_cancel.draw(screen, mp)

# ============================================================
# Notes Modal
# ============================================================
class NotesModal:
    def __init__(self, entity, callback):
        self.entity = entity
        self.callback = callback
        self.text = entity.notes
        self.w, self.h = 600, 400
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2
        self.btn_save = Button(self.x + self.w - 120, self.y + self.h - 50, 100, 40, "SAVE", self._save, color=COLORS["success"])
        self.btn_cancel = Button(self.x + 20, self.y + self.h - 50, 100, 40, "CANCEL", lambda: callback(None), color=COLORS["danger"])

    def _save(self):
        self.entity.notes = self.text
        self.callback(self.text)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.callback(None)
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.text += "\n"
            elif event.unicode.isprintable():
                self.text += event.unicode
        self.btn_save.handle_event(event)
        self.btn_cancel.handle_event(event)

    def draw(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        screen.blit(ov, (0,0))
        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h), 2, border_radius=10)
        
        t = fonts.header.render(f"Notes: {self.entity.name}", True, COLORS["accent"])
        screen.blit(t, (self.x + 20, self.y + 15))

        # Text area
        area = pygame.Rect(self.x + 20, self.y + 60, self.w - 40, self.h - 120)
        pygame.draw.rect(screen, (20,22,25), area)
        pygame.draw.rect(screen, COLORS["border"], area, 1)
        
        # Draw text (simple wrap)
        y = area.y + 5
        lines = self.text.split('\n')
        for line in lines:
            # Simple char wrap would be better but simple line split is ok for now
            s = fonts.body.render(line, True, COLORS["text_main"])
            screen.blit(s, (area.x + 5, y))
            y += 24

        self.btn_save.draw(screen, mp)
        self.btn_cancel.draw(screen, mp)

# ============================================================
# Add Effect Modal
# ============================================================
class EffectModal:
    def __init__(self, entity, callback):
        self.entity = entity
        self.callback = callback
        self.name = ""
        self.duration = 10 # default 1 min
        self.w, self.h = 500, 350
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2
        
        self.presets = [
            ("1 Rnd", 1), ("1 Min", 10), ("10 Min", 100), ("1 Hr", 600)
        ]
        self.preset_btns = []
        bx = self.x + 20
        for lbl, val in self.presets:
            self.preset_btns.append(Button(bx, self.y + 140, 100, 35, lbl, lambda v=val: self._set_dur(v), color=COLORS["panel"]))
            bx += 110

        self.btn_add = Button(self.x + self.w - 120, self.y + self.h - 50, 100, 40, "ADD", self._confirm, color=COLORS["success"])
        self.btn_cancel = Button(self.x + 20, self.y + self.h - 50, 100, 40, "CANCEL", lambda: callback(None), color=COLORS["danger"])

    def _set_dur(self, v): self.duration = v
    def _confirm(self):
        if self.name:
            self.entity.active_effects[self.name] = self.duration
            self.callback(f"{self.name} ({self.duration} rnds)")
        else:
            self.callback(None)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.callback(None)
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.unicode.isprintable() and len(self.name) < 30:
                self.name += event.unicode
        for b in self.preset_btns: b.handle_event(event)
        self.btn_add.handle_event(event)
        self.btn_cancel.handle_event(event)

    def draw(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,180))
        screen.blit(ov, (0,0))
        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h), 2, border_radius=10)
        
        t = fonts.header.render(f"Add Effect: {self.entity.name}", True, COLORS["accent"])
        screen.blit(t, (self.x + 20, self.y + 15))

        # Name input
        lbl = fonts.body.render("Effect Name:", True, COLORS["text_dim"])
        screen.blit(lbl, (self.x + 20, self.y + 70))
        pygame.draw.rect(screen, (20,20,20), (self.x + 150, self.y + 65, 300, 30))
        nm = fonts.body.render(self.name, True, (255,255,255))
        screen.blit(nm, (self.x + 155, self.y + 67))

        # Duration
        dl = fonts.body.render(f"Duration: {self.duration} rounds", True, COLORS["text_main"])
        screen.blit(dl, (self.x + 20, self.y + 110))

        for b in self.preset_btns: b.draw(screen, mp)
        self.btn_add.draw(screen, mp)
        self.btn_cancel.draw(screen, mp)

# ============================================================
# MenuState
# ============================================================
class MenuState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        bw, bh = 340, 54
        gap = 12
        start_y = cy - 100
        self.buttons = [
            Button(cx-bw//2, start_y,              bw, bh, "New Encounter",
                   lambda: manager.change_state("SETUP")),
            Button(cx-bw//2, start_y + (bh+gap),   bw, bh, "Combat Roster",
                   lambda: manager.change_state("COMBAT_ROSTER"),
                   color=COLORS["success"]),
            Button(cx-bw//2, start_y + (bh+gap)*2, bw, bh, "Hero Creator",
                   lambda: manager.change_state("HERO_CREATOR"),
                   color=COLORS["player"]),
            Button(cx-bw//2, start_y + (bh+gap)*3, bw, bh, "Load Scenario",
                   lambda: self._open_load_modal(),
                   color=COLORS["panel_light"], style="outline"),
            Button(cx-bw//2, start_y + (bh+gap)*4, bw, bh, "Import from TaleSpire",
                   lambda: self._import_from_talespire(),
                   color=COLORS["accent_dim"], style="outline"),
            Button(cx-bw//2, start_y + (bh+gap)*5, bw, bh, "Exit",
                   lambda: manager.quit(),
                   color=COLORS["danger_dim"]),
        ]
        self.scenario_modal = None
        self._bg_particles = []
        for _ in range(40):
            self._bg_particles.append([
                random.randint(0, SCREEN_WIDTH),
                random.randint(0, SCREEN_HEIGHT),
                random.uniform(0.2, 0.8),
                random.randint(1, 3),
            ])

    def _import_from_talespire(self):
        self.manager.change_state("SETUP")
        if hasattr(self.manager.current_state, "enable_import"):
            self.manager.current_state.enable_import()

    def _open_load_modal(self):
        self.scenario_modal = ScenarioModal("load", self._on_load_file)

    def _on_load_file(self, filepath):
        self.scenario_modal = None
        if not filepath or not os.path.exists(filepath):
            return
        try:
            bs = BattleState(self.manager)
            bs.battle = BattleSystem.from_save(filepath, bs._log)
            bs.battle.log = bs._log
            self.manager.states["BATTLE"] = bs
            self.manager.change_state("BATTLE")
        except Exception as ex:
            print(f"Load error: {ex}")

    def handle_events(self, events):
        for e in events:
            if self.scenario_modal:
                self.scenario_modal.handle_event(e)
                continue
            for b in self.buttons:
                b.handle_event(e)

    def draw(self, screen):
        screen.fill(COLORS["bg"])

        # Animated background particles (subtle floating dots)
        for p in self._bg_particles:
            p[1] -= p[2]
            if p[1] < 0:
                p[1] = SCREEN_HEIGHT
                p[0] = random.randint(0, SCREEN_WIDTH)
            alpha = int(40 * p[2])
            s = pygame.Surface((p[3]*2, p[3]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*COLORS["accent"], alpha), (p[3], p[3]), p[3])
            screen.blit(s, (int(p[0]), int(p[1])))

        # Decorative line
        cx = SCREEN_WIDTH // 2
        pygame.draw.line(screen, COLORS["border"], (cx - 250, 260), (cx + 250, 260), 1)

        # Title with glow effect
        title_text = "D&D 5e AI Encounter Manager"
        # Glow layer
        glow = fonts.title.render(title_text, True, COLORS["accent_dim"])
        glow.set_alpha(60)
        screen.blit(glow, (cx - glow.get_width()//2 + 2, 142))
        # Main title
        title = fonts.title.render(title_text, True, COLORS["accent"])
        screen.blit(title, (cx - title.get_width()//2, 140))

        sub = fonts.header.render("2014 Edition  |  Endgame Ready", True, COLORS["text_dim"])
        screen.blit(sub, (cx - sub.get_width()//2, 200))

        # Version badge
        ver = fonts.tiny.render("v2.0", True, COLORS["text_muted"])
        screen.blit(ver, (cx - ver.get_width()//2, 240))

        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, mp)

        # Footer
        footer = fonts.tiny.render("TaleSpire Integration  |  AI-Powered Combat  |  Full 5e 2014 Rules", True, COLORS["text_muted"])
        screen.blit(footer, (cx - footer.get_width()//2, SCREEN_HEIGHT - 40))

        if self.scenario_modal:
            self.scenario_modal.draw(screen, mp)


# ============================================================
# EncounterSetupState
# ============================================================
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


# ============================================================
# BattleState  –  The main DM interface
# ============================================================
PANEL_W = 520
TOP_BAR_H = 105
GRID_W = SCREEN_WIDTH - PANEL_W

TABS = ["Stats", "Spells", "Log"]

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


class BattleState(GameState):
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
        self.ts_last_update = 0     # Timestamp of last TaleSpire update
        self.auto_battle = False    # Auto-play toggle
        self.auto_timer = 0         # Timer for auto-play ticks
        self.log_filter_mode = "all" # "all" or "selected"

        # Visual FX
        self.floating_texts = []
        self.turn_banner_text = ""
        self.turn_banner_timer = 0

        # AI turn state
        self.pending_plan: TurnPlan | None = None
        self.pending_step_idx: int = 0
        self.current_step_outcomes = {} # target -> "hit"/"miss"/"save"/"fail"
        self.current_step_rolls = {}    # target -> "15+5=20" (for saves)

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
        self.btn_weather = Button(270, SCREEN_HEIGHT-65, 100, 35, "WEATHER", self._cycle_weather,       color=COLORS["panel"])
        self.btn_undo    = Button(376, SCREEN_HEIGHT-65, 72, 35, "UNDO",      self._undo_last_action,     color=COLORS["warning"])
        self.btn_auto    = Button(454, SCREEN_HEIGHT-65, 72, 35, "AUTO",      self._toggle_auto_battle,   color=COLORS["panel"])
        self.btn_advisor = Button(532, SCREEN_HEIGHT-65, 80, 35, "ADVISOR",  self._toggle_advisor_panel, color=COLORS["spell"])
        self.btn_maps    = Button(618, SCREEN_HEIGHT-65, 72, 35, "MAPS",     self._toggle_map_browser,   color=COLORS["panel"])
        self.map_browser_open = False

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
        if self.auto_battle:
            self.btn_auto.color = COLORS["success"]
            self.btn_auto.text = "STOP"
            self._log("[SYSTEM] Auto-Battle STARTED.")
        else:
            self.btn_auto.color = COLORS["panel"]
            self.btn_auto.text = "AUTO"
            self._log("[SYSTEM] Auto-Battle STOPPED.")

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

        # 2. Handle Reactions (Auto-accept for maximum chaos)
        if self.reaction_pending:
            self._resolve_reaction(True)
            return

        # 3. Handle Pending Plan (Execute steps)
        if self.pending_plan:
            self._confirm_step()
            return

        # 4. Decide Next Action
        try:
            curr = self.battle.get_current_entity()
        except ValueError:
            self.auto_battle = False
            return
        
        # If current entity has done nothing yet, try to generate AI plan
        # (Even for players in auto mode)
        if not curr.action_used and not curr.is_incapacitated():
            # Try to generate a plan
            self._do_ai_turn(force_auto=True)
            
            # If no plan was generated (e.g. skipped/no targets), end turn
            if not self.pending_plan:
                self._do_next_turn()
        else:
            # Turn done, next
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

        # Rain animation
        if self.battle.weather in ("Rain", "Ash"):
            self._update_weather_fx()

        self.battle.validate_grapples()

        # Update FX
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]
        if self.turn_banner_timer > 0:
            self.turn_banner_timer -= 1
            
        # Auto Battle Tick
        if self.auto_battle and self.battle.combat_started:
            self.auto_timer += 1
            if self.auto_timer > 10:  # Adjust speed here (frames per tick)
                self.auto_timer = 0
                self._process_auto_battle()

    def _update_weather_fx(self):
        # Simple particle system could go here, for now we just use draw time randomization
        pass

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

    def _spawn_damage_text(self, entity, amount, is_heal=False):
        color = COLORS["success"] if is_heal else COLORS["danger"]
        prefix = "+" if is_heal else "-"
        text = f"{prefix}{abs(amount)}"
        ft = FloatingText(entity.grid_x, entity.grid_y, text, color)
        self.floating_texts.append(ft)

    def _save_undo_snapshot(self):
        """Save current state to undo stack."""
        state = self.battle.get_state_dict()
        self.undo_stack.append(state)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def _undo_last_action(self):
        if not self.undo_stack:
            self._log("[UNDO] Nothing to undo.")
            return
        state = self.undo_stack.pop()
        self.battle.restore_state(state)
        self.selected_entity = None
        self.pending_plan = None
        self.condition_reminder = None
        self._log("[UNDO] Reverted to previous state.")

    # ------------------------------------------------------------------ #
    # Turn management                                                      #
    # ------------------------------------------------------------------ #

    def _do_start_combat(self):
        self.battle.start_combat()
        self._log("Combat started! Initiative rolled.")
        # Refresh current entity since order changed
        curr = self.battle.get_current_entity()
        self._log(f"--- Round {self.battle.round}: {curr.name}'s turn ---")

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

        # 2. Check for End-of-Turn Saves for current player (Manual Mode)
        try:
            curr = self.battle.get_current_entity()
            if curr.is_player and not self.auto_battle and curr.hp > 0:
                saves = []
                for cond, meta in curr.condition_metadata.items():
                    if meta.get("save") and meta.get("dc"):
                        saves.append((curr, cond, meta["save"], meta["dc"]))
                if saves:
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
        # If player, open action panel hint and show condition reminder
        if curr.is_player:
            self._log(f"[PLAYER TURN] {curr.name} – log their action with 'LOG PLAYER ACTION'")
            if curr.conditions or curr.concentrating_on:
                self.condition_reminder = curr
            # DM Advisor: generate suggestion for this player's turn
            if self.show_advisor_panel:
                self.dm_suggestion_cache = self.battle.get_dm_suggestion(curr)
                self.dm_rating_cache = None  # Clear previous rating
        else:
            self.dm_suggestion_cache = None
            self.dm_rating_cache = None

        # Track that entity is active this round
        self.battle.stats_tracker.record_round_active(curr.name, curr.is_player)

        # Update win probability
        self._update_win_probability()

        # Turn Banner
        self.turn_banner_text = f"{curr.name}'s Turn"
        self.turn_banner_timer = 120 # 2 seconds

        # Check auras
        auras = self.battle.check_turn_start_auras(curr)
        if auras:
            self.aura_triggers = auras
            self._open_next_aura_modal()

    def _do_ai_turn(self, force_auto=False):
        curr = self.battle.get_current_entity()
        if self.pending_plan and self.pending_plan.entity == curr:
            self._log("AI plan already pending – confirm or skip each step.")
            return
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
                        bonus = t.get_save_bonus(step.save_ability)
                        
                        # Paladin Aura of Protection check
                        if self.battle:
                            for ally in self.battle.get_allies_of(t):
                                if ally.hp > 0 and not ally.is_incapacitated():
                                    aura = ally.get_feature("aura_of_protection")
                                    if aura and self.battle.get_distance(t, ally) * 5 <= (aura.aura_radius or 10):
                                        bonus += max(1, ally.get_modifier("Charisma"))
                                        break
                        
                        raw = random.randint(1, 20)
                        total = raw + bonus
                        self.current_step_rolls[t] = f"{raw}+{bonus}={total}"
                        if total >= step.save_dc:
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
            self._log(f"[AUTO-CONFIRM] {step.description}")
        self.pending_plan = None
        self._log("[AI] All steps approved.")

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

                # --- AI REACTION CHECK (Uncanny Dodge) ---
                # Halve damage from an attack you can see
                if not target.is_player and not target.reaction_used and step.attacker and target.has_feature("uncanny_dodge"):
                    target.reaction_used = True
                    dmg = dmg // 2
                    self._log(f"[REACTION] {target.name} uses Uncanny Dodge! Damage halved.")
                    self._spawn_damage_text(target, "Dodge!", is_heal=True)

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
                        self._spawn_damage_text(step.attacker, r_dealt)
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
                    # Evasion (Fail): Half damage instead of full
                    if step.save_ability == "Dexterity" and target.has_feature("evasion"):
                        dealt = dealt // 2
                        self._log(f"  [EVASION] {target.name} fails save but takes half damage.")

                    roll_str = self.current_step_rolls.get(target, "")
                    roll_msg = f" (Rolled {roll_str} vs DC {step.save_dc})" if roll_str else ""
                    self._log(f"  -> {target.name} FAILED save{roll_msg}: takes {dealt} {step.damage_type}")
                else:
                    self._log(f"  -> {target.name} takes {dealt} {step.damage_type}")
                self._spawn_damage_text(target, dealt)
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
                self._spawn_damage_text(target, dealt)
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
            (f"Drop Concentration", lambda: entity.drop_concentration() or self._log(f"{entity.name} drops concentration.")),
            (f"Add Effect...", lambda: self._open_effect_modal(entity)),
            (f"Edit Notes...", lambda: self._open_notes_modal(entity)),
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

        # Condition badges (top-right, stacked)
        if entity.conditions:
            n = len(entity.conditions)
            badge_r = 8
            badge_cx = cx + radius - 2
            badge_cy = cy - radius + 2
            # Background circle
            pygame.draw.circle(screen, COLORS["spell"], (badge_cx, badge_cy), badge_r)
            pygame.draw.circle(screen, (255, 255, 255), (badge_cx, badge_cy), badge_r, 1)
            ns = fonts.tiny.render(str(n), True, (255, 255, 255))
            screen.blit(ns, (badge_cx - ns.get_width()//2, badge_cy - ns.get_height()//2))

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

    def _paint_terrain_at(self, pos, button):
        mx, raw_my = pos
        if mx < GRID_W and raw_my >= TOP_BAR_H:
            gx, gy = self._screen_to_grid(mx, raw_my)
            gx, gy = int(gx), int(gy)
            if button == 1:  # Paint
                t = TerrainObject(self.terrain_selected_type, gx, gy)
                self.battle.add_terrain(t)
            elif button == 3:  # Erase
                self.battle.remove_terrain_at(gx, gy)

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
                
                # Undo Move (Z)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                    self._undo_last_action()

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
                        # Calculate palette bounds
                        pal_x, pal_y = 10, TOP_BAR_H + 10
                        pal_w = 165
                        item_h = 24
                        max_vis = (SCREEN_HEIGHT - TOP_BAR_H - 120) // item_h
                        scroll = getattr(self, 'terrain_palette_scroll', 0)
                        pal_h = min(max_vis, len(TERRAIN_TYPES)) * item_h + 8 * 2 + 48
                        pal_rect = pygame.Rect(pal_x, pal_y, pal_w, pal_h)

                        if pal_rect.collidepoint(event.pos):
                            # Scroll with mouse wheel
                            if event.button == 4:  # scroll up
                                self.terrain_palette_scroll = max(0, scroll - 1)
                            elif event.button == 5:  # scroll down
                                self.terrain_palette_scroll = min(
                                    len(TERRAIN_TYPES) - max_vis,
                                    scroll + 1)
                            else:
                                # Click on item
                                keys = list(TERRAIN_TYPES.keys())
                                visible = keys[scroll:scroll + max_vis]
                                for i, ttype in enumerate(visible):
                                    r = pygame.Rect(pal_x + 4, pal_y + 38 + 8 + i * item_h,
                                                    pal_w - 8, item_h - 2)
                                    if r.collidepoint(event.pos):
                                        self.terrain_selected_type = ttype
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
                            # Start painting
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
                    
                    if self.dragging:
                        mx, raw_my = event.pos
                        my = raw_my - TOP_BAR_H
                        if mx < GRID_W and my >= 0:
                            # Calculate grid position based on CENTER of the token (free placement)
                            gx, gy = self._screen_to_grid(mx - self.battle.grid_size / 2, raw_my - self.battle.grid_size / 2)
                            
                            if not self.battle.is_occupied(gx, gy, exclude=self.dragging):
                                old_x, old_y = self.dragging.grid_x, self.dragging.grid_y
                                
                                # Temporarily move to check OA
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
                    if self.terrain_mode and self.drawing_button:
                        self._paint_terrain_at(event.pos, self.drawing_button)

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
                self.btn_advisor.handle_event(event)
                self.btn_maps.handle_event(event)

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
            txt = fonts.title.render(self.turn_banner_text, True, (255, 255, 255))
            txt.set_alpha(alpha)
            
            # Background strip
            bg_h = 80
            bg_y = SCREEN_HEIGHT // 2 - bg_h // 2 - 100
            s = pygame.Surface((GRID_W, bg_h), pygame.SRCALPHA)
            s.fill((0, 0, 0, int(180 * (alpha/255))))
            screen.blit(s, (0, bg_y))
            screen.blit(txt, (GRID_W//2 - txt.get_width()//2, bg_y + bg_h//2 - txt.get_height()//2))

        if self.terrain_palette_open:
            self._draw_terrain_palette(screen, mp)
        if self.map_browser_open:
            self._draw_map_browser(screen, mp)
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
        for t in self.battle.terrain:
            rx, ry = self._grid_to_screen(t.grid_x, t.grid_y)
            rw = t.width * gsz
            rh = t.height * gsz
            # Filled tile
            s = pygame.Surface((rw, rh), pygame.SRCALPHA)
            r, g, b = t.color
            s.fill((r, g, b, 200))
            screen.blit(s, (rx, ry))
            # Border color: brighter for elevated, darker for lowered
            border_color = tuple(min(255, c+40) for c in t.color)
            if t.elevation > 0:
                border_color = (200, 200, 255)  # blue-ish for elevated
            elif t.elevation < 0:
                border_color = (100, 50, 50)    # dark red for pits/chasms
            pygame.draw.rect(screen, border_color, (rx, ry, rw, rh), 2)
            # Label (top-left)
            lbl_text = t.label[:8]
            lbl = fonts.tiny.render(lbl_text, True, (255, 255, 255))
            screen.blit(lbl, (rx + 2, ry + 2))
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

    # --- Weather Effects ---
    def _draw_weather(self, screen):
        w = self.battle.weather
        if w == "Clear":
            return
        
        if w == "Fog":
            # Simple fog overlay
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((200, 200, 220, 40))
            screen.blit(s, (0, 0))
        
        elif w == "Rain":
            # Draw random rain drops
            for _ in range(100):
                rx = random.randint(0, GRID_W)
                ry = random.randint(TOP_BAR_H, SCREEN_HEIGHT)
                pygame.draw.line(screen, (150, 150, 255, 100), (rx, ry), (rx-2, ry+10), 1)

        elif w == "Ash":
            # Draw falling ash
            for _ in range(50):
                rx = random.randint(0, GRID_W)
                ry = random.randint(TOP_BAR_H, SCREEN_HEIGHT)
                pygame.draw.circle(screen, (100, 50, 50), (rx, ry), 2)

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
        for b in (self.btn_save, self.btn_load, self.btn_terrain, self.btn_weather, self.btn_undo, self.btn_auto, self.btn_advisor, self.btn_maps):
            b.draw(screen, mp)
        # Terrain mode indicator
        if self.terrain_mode:
            tc = COLORS["warning"]
            pygame.draw.rect(screen, tc, self.btn_terrain.rect, 2, border_radius=5)
            sel = fonts.tiny.render(f"[{self.terrain_selected_type}]", True, tc)
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

    def _draw_stats_tab(self, screen, sel, x0, y, mp):

        def ln(text, color=COLORS["text_main"], indent=0):
            nonlocal y
            s = fonts.small.render(text, True, color)
            screen.blit(s, (x0+indent, y))
            y += 20

        # Name, type, AC, HP
        ln(f"{sel.name}", COLORS["accent"] if not sel.is_player else COLORS["player"])
        cr_str = f"CR {sel.stats.challenge_rating:.3g}" if sel.stats.challenge_rating else "Player"
        ln(f"{sel.stats.size} {sel.stats.creature_type}  |  {cr_str}  |  XP {sel.stats.xp}", COLORS["text_dim"])
        ln("")
        hp_pct = sel.hp/sel.max_hp if sel.max_hp>0 else 0
        hp_c = COLORS["success"] if hp_pct>0.5 else COLORS["warning"] if hp_pct>0.25 else COLORS["danger"]
        ln(f"HP: {sel.hp}/{sel.max_hp}  TempHP: {sel.temp_hp}", hp_c)
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

        # Ability scores
        ab = sel.stats.abilities
        ln("ABILITIES:", COLORS["text_dim"])
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
        
        # Ability Checks (Raw checks for contests etc)
        ln("ABILITY CHECKS:", COLORS["text_dim"])
        sx = x0
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

        # Action economy indicators
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
            ln(f"Concentrating: {sel.concentrating_on.name}", COLORS["concentration"])

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

        # Class Resources
        if sel.stats.character_class:
            ln("")
            ln(f"CLASS: {sel.stats.character_class} {sel.stats.character_level} ({sel.stats.subclass})", COLORS["accent"])
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

        # Conditions
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

        # Features summary
        if sel.stats.features:
            ln("")
            ln("FEATURES:", COLORS["text_dim"])
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

        # Helper to draw action lists
        def draw_action_section(title, actions):
            nonlocal y
            if not actions: return
            ln("")
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

        draw_action_section("ACTIONS:", sel.stats.actions)
        draw_action_section("BONUS ACTIONS:", sel.stats.bonus_actions)
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

    def _start_spell_targeting(self, entity, spell):
        self.spell_caster = entity
        self.spell_targeting = spell
        self._log(f"[TARGETING] Select target/area for {spell.name} (Range: {spell.range}ft)")

    def _cancel_spell_targeting(self):
        self.spell_caster = None
        self.spell_targeting = None
        self._log("[TARGETING] Cancelled.")

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
        
        # Create ActionStep
        step = ActionStep(
            step_type="spell",
            description=f"{caster.name} casts {spell.name}.",
            attacker=caster,
            targets=targets,
            spell=spell,
            damage=dmg if dmg > 0 else heal, # Reuse damage field for heal if needed, logic handles it
            damage_type=spell.damage_type,
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

    def _draw_log_tab(self, screen, sel, x0, y, mp):
        # Filter Buttons
        btn_w = 110
        btn_h = 24
        
        # Global Button
        r_global = pygame.Rect(x0, y, btn_w, btn_h)
        is_global = (self.log_filter_mode == "all")
        c_global = COLORS["accent"] if is_global else (60, 60, 60)
        pygame.draw.rect(screen, c_global, r_global, border_radius=4)
        t_global = fonts.tiny.render("GLOBAL LOG", True, (255,255,255))
        screen.blit(t_global, (r_global.centerx - t_global.get_width()//2, r_global.centery - t_global.get_height()//2))
        self.ui_click_zones.append((r_global, lambda: setattr(self, 'log_filter_mode', 'all')))
        
        # Entity Button
        r_ent = pygame.Rect(x0 + btn_w + 10, y, btn_w + 40, btn_h)
        is_ent = (self.log_filter_mode == "selected")
        c_ent = COLORS["accent"] if is_ent else (60, 60, 60)
        pygame.draw.rect(screen, c_ent, r_ent, border_radius=4)
        
        ent_name = sel.name if sel else "Entity"
        if len(ent_name) > 15: ent_name = ent_name[:13] + ".."
        t_ent = fonts.tiny.render(f"LOG: {ent_name}", True, (255,255,255))
        screen.blit(t_ent, (r_ent.centerx - t_ent.get_width()//2, r_ent.centery - t_ent.get_height()//2))
        self.ui_click_zones.append((r_ent, lambda: setattr(self, 'log_filter_mode', 'selected')))
        
        y += 32

        # Filter logic
        display_logs = self.logs
        if self.log_filter_mode == "selected" and sel:
            # Show logs containing the selected entity's name
            name = sel.name
            display_logs = [msg for msg in self.logs if name in msg]

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
        
        self.btn_approve_all.rect.topleft = (bx + bw//2 - 65, by + bh - 100)
        self.btn_confirm.draw(screen, mp)
        self.btn_deny.draw(screen, mp)
        self.btn_approve_all.draw(screen, mp)

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
                dis = reactor.has_attack_disadvantage(mover)
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

    def _resolve_manual_save(self, index, success):
        if index >= len(self.pending_saves): return
        entity, cond, ability, dc = self.pending_saves.pop(index)
        
        if success:
            entity.remove_condition(cond)
            self._log(f"[SAVE] {entity.name} succeeded save (Manual) and is no longer {cond}!")
        else:
            self._log(f"[SAVE] {entity.name} failed save (Manual) and remains {cond}.")

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
        max_visible = (SCREEN_HEIGHT - TOP_BAR_H - 120) // item_h
        scroll = getattr(self, 'terrain_palette_scroll', 0)

        keys = list(TERRAIN_TYPES.keys())
        total = len(keys)
        bh = min(max_visible, total) * item_h + pad * 2 + 48

        bx = 10
        by = TOP_BAR_H + 10

        pygame.draw.rect(screen, (35, 37, 42), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 1, border_radius=6)
        hdr = fonts.small.render("Terrain Palette", True, COLORS["accent"])
        screen.blit(hdr, (bx + 6, by + 6))
        # Door toggle hint
        hint = fonts.tiny.render("Middle-click: toggle door", True, COLORS["text_dim"])
        screen.blit(hint, (bx + 6, by + 22))

        y = by + pad + 38
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
            screen.blit(up_arrow, (bx + bw//2 - up_arrow.get_width()//2, by + 36))
        if scroll + max_visible < total:
            dn_arrow = fonts.tiny.render("v more v", True, COLORS["text_dim"])
            screen.blit(dn_arrow, (bx + bw//2 - dn_arrow.get_width()//2, by + bh - 14))

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
    def _toggle_terrain_mode(self):
        self.terrain_mode = not self.terrain_mode
        self.terrain_palette_open = self.terrain_mode
        if self.terrain_mode:
            self.btn_terrain.text = "STOP PAINTING"
            self.btn_terrain.color = COLORS["warning"]
            self._log("[TERRAIN] Terrain placement mode ON. Left-click=place, Right-click=remove, Middle-click=toggle door.")
        else:
            self.btn_terrain.text = "TERRAIN"
            self.btn_terrain.color = COLORS["panel"]
            self._log("[TERRAIN] Terrain placement mode OFF.")

    def _toggle_map_browser(self):
        self.map_browser_open = not self.map_browser_open

    def _load_premade_map(self, map_key):
        """Load a premade map, replacing current terrain."""
        from data.maps import load_map_terrain
        terrain_list = load_map_terrain(map_key)
        if terrain_list:
            self.battle.terrain = terrain_list
            self.map_browser_open = False
            self._log(f"[MAP] Loaded premade map: {map_key}")

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
