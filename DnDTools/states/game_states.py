import pygame
import math
import os
import json
import copy
import random
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, hp_bar
from engine.battle import BattleSystem
from engine.ai import TurnPlan, ActionStep
from engine.terrain import TerrainObject, TERRAIN_TYPES
from data.library import library
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores, Action
from data.heroes import hero_list
from data.conditions import CONDITIONS

SAVE_FILE = os.path.join(os.path.dirname(__file__), "..", "saves", "encounter.json")


# ============================================================
# Base GameState
# ============================================================
class GameState:
    def __init__(self, manager): self.manager = manager
    def handle_events(self, events): pass
    def update(self): pass
    def draw(self, screen): pass


# ============================================================
# MenuState
# ============================================================
class MenuState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.buttons = [
            Button(cx-160, cy-70,  320, 60, "New Encounter",    lambda: manager.change_state("SETUP")),
            Button(cx-160, cy+10,  320, 60, "Load Encounter",   lambda: self._load_from_menu(manager),
                   color=COLORS["panel"]),
            Button(cx-160, cy+90,  320, 60, "Exit",             lambda: manager.quit()),
        ]

    def _load_from_menu(self, manager):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            bs = BattleState(manager)
            bs.battle = BattleSystem.from_save(SAVE_FILE, bs._log)
            bs.battle.log = bs._log
            manager.states["BATTLE"] = bs
            manager.change_state("BATTLE")
        except Exception as ex:
            import traceback; traceback.print_exc()
            print(f"Load error: {ex}")

    def handle_events(self, events):
        for e in events:
            for b in self.buttons:
                b.handle_event(e)

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        title = fonts.title.render("D&D 5e AI Encounter Manager", True, COLORS["accent"])
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 160))
        sub = fonts.header.render("2014 Edition  •  Endgame Ready", True, COLORS["text_dim"])
        screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 230))
        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, mp)


# ============================================================
# EncounterSetupState
# ============================================================
class EncounterSetupState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.roster = []
        self.scroll_monster = 0
        self.scroll_hero    = 0
        all_monsters = library.get_all_monsters()
        self.monsters_by_cr: dict = {}
        for m in all_monsters:
            cr = m.challenge_rating
            self.monsters_by_cr.setdefault(cr, []).append(m)
        self.sorted_crs = sorted(self.monsters_by_cr.keys())
        self.selected_cr = None
        self.active_monster_btns = []

        self.cr_btns = []
        y = 130
        for cr in self.sorted_crs:
            label = f"CR {cr:.3g}" if cr % 1 != 0 else f"CR {int(cr)}"
            self.cr_btns.append(Button(30, y, 110, 35, label, lambda c=cr: self._select_cr(c),
                                       color=COLORS["panel"]))
            y += 40

        self.hero_btns = []
        y = 130
        for h in hero_list:
            self.hero_btns.append(Button(430, y, 220, 35, f"+ {h.name}",
                                         lambda hero=h: self._add_hero(hero),
                                         color=COLORS["player"]))
            y += 40

        self.action_btns = [
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-100, 230, 55, "START BATTLE",
                   self._start_battle, color=COLORS["success"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-165, 230, 45, "Long Rest All",
                   self._long_rest, color=COLORS["accent"]),
            Button(20, 20, 110, 35, "< Menu",
                   lambda: manager.change_state("MENU"), color=COLORS["panel"]),
            Button(SCREEN_WIDTH-270, SCREEN_HEIGHT-220, 230, 45, "Clear Roster",
                   lambda: self.roster.clear(), color=COLORS["danger"]),
        ]

    def _select_cr(self, cr):
        self.selected_cr = cr
        self.scroll_monster = 0
        self.active_monster_btns = []
        for m in self.monsters_by_cr[cr]:
            self.active_monster_btns.append(
                Button(160, 0, 250, 35, m.name, lambda mon=m: self._add_monster(mon),
                       color=COLORS["panel"]))

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

    def _start_battle(self):
        if not self.roster:
            return
        self.manager.states["BATTLE"] = BattleState(self.manager, list(self.roster))
        self.manager.change_state("BATTLE")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                if pygame.mouse.get_pos()[0] < 160:
                    self.scroll_hero = min(0, self.scroll_hero + event.y * 25)
                else:
                    self.scroll_monster = min(0, self.scroll_monster + event.y * 25)
            for b in self.action_btns + self.cr_btns:
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
        # Action buttons
        for b in self.action_btns:
            b.draw(screen, mp)


# ============================================================
# BattleState  –  The main DM interface
# ============================================================
PANEL_W = 520
TOP_BAR_H = 105
GRID_W = SCREEN_WIDTH - PANEL_W

TABS = ["Stats", "Spells", "Log"]

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

        # AI turn state
        self.pending_plan: TurnPlan | None = None
        self.pending_step_idx: int = 0

        # Player action panel state
        self.player_action_mode = False
        self.player_action_type = None   # "attack","spell","move","item","other"
        self.player_action_target = None

        # Reaction popup
        self.reaction_pending = []  # list of (reactor, mover)

        # Context menu
        self.ctx_open = False
        self.ctx_pos = (0, 0)
        self.ctx_rects = []   # [(rect, callback, text)]

        # Terrain mode
        self.terrain_mode = False
        self.terrain_selected_type = "wall"
        self.terrain_palette_open = False

        # Condition reminder (set when player turn starts with active conditions)
        self.condition_reminder: Entity | None = None

        self._build_buttons()

    # ------------------------------------------------------------------ #
    # Build UI buttons                                                     #
    # ------------------------------------------------------------------ #

    def _build_buttons(self):
        bx = SCREEN_WIDTH - PANEL_W
        # Bottom bar
        self.btn_next   = Button(bx+20,  SCREEN_HEIGHT-65, 145, 50, "NEXT TURN >>", self._do_next_turn,      color=COLORS["success"])
        self.btn_ai     = Button(bx+175, SCREEN_HEIGHT-65, 145, 50, "AI AUTO-PLAY", self._do_ai_turn,        color=COLORS["accent"])
        self.btn_menu   = Button(10, 10, 80, 30, "Menu",          lambda: self.manager.change_state("MENU"), color=COLORS["panel"])
        self.btn_log_pl = Button(bx+330, SCREEN_HEIGHT-65, 165, 50, "LOG PLAYER ACTION", self._open_player_action_panel, color=COLORS["neutral"])
        # Grid area bottom-left utilities
        self.btn_save    = Button(10,  SCREEN_HEIGHT-65, 72, 35, "SAVE",    self._save_encounter,       color=COLORS["panel"])
        self.btn_load    = Button(87,  SCREEN_HEIGHT-65, 72, 35, "LOAD",    self._load_encounter,       color=COLORS["panel"])
        self.btn_terrain = Button(164, SCREEN_HEIGHT-65, 100, 35, "TERRAIN", self._toggle_terrain_mode, color=COLORS["panel"])

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
                                  "SKIP",    lambda: self._skip_step(),   color=COLORS["danger"])
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
            Button(0, 0, 120, 35, "Help",      lambda: self._pl_set_type("help"),   color=COLORS["accent"]),
            Button(0, 0, 120, 35, "Done",      lambda: self._close_player_panel(),  color=COLORS["text_dim"]),
        ]

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #

    def _log(self, msg):
        self.logs.append(msg)
        if len(self.logs) > 80:
            self.logs.pop(0)

    # ------------------------------------------------------------------ #
    # Turn management                                                      #
    # ------------------------------------------------------------------ #

    def _do_next_turn(self):
        self.pending_plan = None
        self.player_action_mode = False
        self.condition_reminder = None
        curr = self.battle.next_turn()
        self.selected_entity = curr
        # If player, open action panel hint and show condition reminder
        if curr.is_player:
            self._log(f"[PLAYER TURN] {curr.name} – log their action with 'LOG PLAYER ACTION'")
            if curr.conditions or curr.concentrating_on:
                self.condition_reminder = curr

    def _do_ai_turn(self):
        curr = self.battle.get_current_entity()
        if curr.is_player:
            self._log("Current turn is a player – use 'Log Player Action' instead.")
            return
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

    def _confirm_step(self):
        if not self.pending_plan:
            return
        steps = self.pending_plan.steps
        if self.pending_step_idx < len(steps):
            step = steps[self.pending_step_idx]
            self._log(f"[CONFIRMED] {step.description}")
            self.pending_step_idx += 1
        if self.pending_step_idx >= len(steps):
            self.pending_plan = None
            self._log("[AI] Turn complete.")

    def _skip_step(self):
        if not self.pending_plan:
            return
        steps = self.pending_plan.steps
        if self.pending_step_idx < len(steps):
            step = steps[self.pending_step_idx]
            self._log(f"[SKIPPED] {step.description}")
            self.pending_step_idx += 1
        if self.pending_step_idx >= len(steps):
            self.pending_plan = None

    def _approve_all(self):
        if not self.pending_plan:
            return
        for step in self.pending_plan.steps[self.pending_step_idx:]:
            self._log(f"[CONFIRMED] {step.description}")
        self.pending_plan = None
        self._log("[AI] All steps approved.")

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
        elif action_type == "dodge":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} Dodges. Attacks against have Disadvantage.")
        elif action_type == "help":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} Helps an ally. Ally gets Advantage on next attack/check.")
        elif action_type == "item":
            curr.action_used = True
            self._log(f"[PLAYER] {curr.name} uses an item. (Apply effect manually)")

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
        if amount < 0:
            dealt, broke = sel.take_damage(-amount)
            action_str = f"takes {dealt} damage"
            if broke:
                action_str += " [CONCENTRATION BROKEN]"
        else:
            sel.heal(amount)
            action_str = f"healed {amount} HP"
        self._log(f"[DM] {sel.name} {action_str}. HP: {sel.hp}/{sel.max_hp}")

    def _modify_init(self, delta):
        if self.selected_entity:
            self.battle.update_initiative(self.selected_entity, delta)

    def _toggle_condition(self, cond):
        sel = self.selected_entity
        if not sel:
            return
        if sel.has_condition(cond):
            sel.remove_condition(cond)
            self._log(f"[DM] {sel.name}: {cond} removed.")
        else:
            sel.add_condition(cond)
            self._log(f"[DM] {sel.name}: {cond} applied.")

    def _use_spell_slot(self, level):
        sel = self.selected_entity
        if not sel:
            return
        key = {1:"1st",2:"2nd",3:"3rd"}.get(level, f"{level}th")
        if sel.spell_slots.get(key, 0) > 0:
            sel.spell_slots[key] -= 1
            self._log(f"[DM] {sel.name} uses {key}-level slot. Remaining: {sel.spell_slots[key]}")
        else:
            self._log(f"[DM] {sel.name} has no {key}-level slots left!")

    # ------------------------------------------------------------------ #
    # Context menu                                                         #
    # ------------------------------------------------------------------ #

    def _open_ctx_menu(self, pos, entity):
        self.selected_entity = entity
        self.ctx_open = True
        self.ctx_pos = pos
        options = [
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
        ]
        x, y = pos
        w, h = 170, 28
        self.ctx_rects = []
        for i, (txt, cb) in enumerate(options):
            self.ctx_rects.append((pygame.Rect(x, y + i*h, w, h), cb, txt))

    # ------------------------------------------------------------------ #
    # Token images                                                         #
    # ------------------------------------------------------------------ #

    def _get_token_image(self, name):
        if name in self.token_cache:
            return self.token_cache[name]
        path = os.path.join("data", "tokens", f"{name}.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.token_cache[name] = img
                return img
            except Exception:
                pass
        self.token_cache[name] = None
        return None

    def _draw_token(self, screen, entity, cx, cy, radius):
        # Drop shadow
        shadow_surf = pygame.Surface((radius*2+6, radius*2+6), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0,0,0,60), (radius+3, radius+3), radius+2)
        screen.blit(shadow_surf, (cx - radius - 3, cy - radius - 3))

        img = self._get_token_image(entity.name)
        if img:
            scaled = pygame.transform.smoothscale(img, (radius*2, radius*2))
            # Clip to circle via mask
            mask_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255,255,255,255), (radius, radius), radius)
            scaled.blit(mask_surf, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(scaled, (cx - radius, cy - radius))
            border = (255, 215, 0) if entity.is_player else (192, 192, 192)
            pygame.draw.circle(screen, border, (cx, cy), radius, 3)
        else:
            # HP-based border color
            hp_pct = entity.hp / entity.max_hp if entity.max_hp > 0 else 0
            if entity.is_player:
                border = (255, 215, 0)   # gold for players always
            elif hp_pct > 0.6:
                border = (160, 200, 160)
            elif hp_pct > 0.3:
                border = (220, 160, 50)
            else:
                border = (200, 60, 60)

            if entity.has_condition("Prone"):
                pygame.draw.ellipse(screen, border, (cx-radius, cy-radius//2, radius*2, radius))
                pygame.draw.ellipse(screen, (30, 32, 36), (cx-radius+3, cy-radius//2+3, radius*2-6, radius-6))
                pygame.draw.ellipse(screen, entity.color, (cx-radius+6, cy-radius//2+6, radius*2-12, radius-12), 4)
            else:
                pygame.draw.circle(screen, border, (cx, cy), radius)
                pygame.draw.circle(screen, (30, 32, 36), (cx, cy), radius - 4)
                pygame.draw.circle(screen, entity.color, (cx, cy), radius - 7, 5)

            # Initials text with outline
            initials = entity.name[:2].upper()
            ts = fonts.small.render(initials, True, (0, 0, 0))
            tf = fonts.small.render(initials, True, (240, 240, 240))
            tx = cx - tf.get_width() // 2
            ty = cy - tf.get_height() // 2
            for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
                screen.blit(ts, (tx+ox, ty+oy))
            screen.blit(tf, (tx, ty))

            # CR badge for monsters (bottom-right of token)
            if not entity.is_player and entity.stats.challenge_rating:
                cr = entity.stats.challenge_rating
                cr_str = f"{cr:.3g}" if cr < 1 else str(int(cr))
                badge = fonts.tiny.render(cr_str, True, (255, 220, 100))
                bx = cx + radius - badge.get_width() - 1
                by = cy + radius - badge.get_height()
                pygame.draw.rect(screen, (0,0,0,180), (bx-2, by-1, badge.get_width()+4, badge.get_height()+2))
                screen.blit(badge, (bx, by))

        # Concentration ring (teal)
        if entity.concentrating_on:
            pygame.draw.circle(screen, COLORS["concentration"], (cx, cy), radius + 5, 2)

        # Condition count badge (top-right)
        if entity.conditions:
            n = len(entity.conditions)
            pygame.draw.circle(screen, COLORS["spell"], (cx + radius - 3, cy - radius + 3), 6)
            ns = fonts.tiny.render(str(n), True, (255, 255, 255))
            screen.blit(ns, (cx + radius - 3 - ns.get_width()//2, cy - radius + 3 - ns.get_height()//2))

    # ------------------------------------------------------------------ #
    # Event handling                                                       #
    # ------------------------------------------------------------------ #

    def handle_events(self, events):
        curr = self.battle.get_current_entity()
        for event in events:
            try:
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
                        clicked = False
                        for i, (ttype, props) in enumerate(TERRAIN_TYPES.items()):
                            r = pygame.Rect(10, TOP_BAR_H + 10 + i * 30, 130, 28)
                            if r.collidepoint(event.pos):
                                self.terrain_selected_type = ttype
                                clicked = True
                                break
                        if not clicked:
                            self.terrain_palette_open = False

                # Pending AI confirmation
                if self.pending_plan:
                    self.btn_confirm.handle_event(event)
                    self.btn_deny.handle_event(event)
                    self.btn_approve_all.handle_event(event)
                    continue

                # Player action panel
                if self.player_action_mode:
                    for i, b in enumerate(self.player_action_btns):
                        b.rect.topleft = (GRID_W + 20 + (i % 4) * 128, SCREEN_HEIGHT - 200 + (i // 4) * 42)
                        b.handle_event(event)

                # Mouse clicks on grid
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, raw_my = event.pos
                    my = raw_my - TOP_BAR_H
                    if mx < GRID_W and my >= 0:
                        gx = mx / self.battle.grid_size
                        gy = my / self.battle.grid_size
                        igx, igy = int(gx), int(gy)
                        if self.terrain_mode:
                            # Place terrain
                            t = TerrainObject(self.terrain_selected_type, igx, igy)
                            self.battle.add_terrain(t)
                            self._log(f"[TERRAIN] Placed {t.label} at ({igx},{igy})")
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
                        gx = mx / self.battle.grid_size
                        gy = my / self.battle.grid_size
                        if self.terrain_mode:
                            # Remove terrain at right-click
                            igx, igy = int(gx), int(gy)
                            self.battle.remove_terrain_at(igx, igy)
                            self._log(f"[TERRAIN] Removed terrain at ({igx},{igy})")
                        else:
                            ent = self.battle.get_entity_at(gx, gy)
                            if ent:
                                self._open_ctx_menu(event.pos, ent)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragging:
                        mx, raw_my = event.pos
                        my = raw_my - TOP_BAR_H
                        if mx < GRID_W and my >= 0:
                            gx = mx / self.battle.grid_size
                            gy = my / self.battle.grid_size
                            if not self.battle.is_occupied(gx, gy, exclude=self.dragging):
                                old_x, old_y = self.dragging.grid_x, self.dragging.grid_y
                                self.dragging.grid_x = gx
                                self.dragging.grid_y = gy
                                dist_ft = math.hypot(gx - old_x, gy - old_y) * 5
                                self._log(f"[MOVE] {self.dragging.name} moved {dist_ft:.0f} ft.")
                            else:
                                self._log("Cannot move: space occupied.")
                        self.dragging = None

                # Tab clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, tab in enumerate(TABS):
                        tab_rect = pygame.Rect(GRID_W + i * 120, TOP_BAR_H + 5, 115, 28)
                        if tab_rect.collidepoint(event.pos):
                            self.active_tab = i
                            self.panel_scroll = 0

                    # Condition toggles
                    if self.selected_entity:
                        start_x = GRID_W + 20
                        start_y = TOP_BAR_H + 285
                        col_w, row_h = 120, 24
                        mx2, my2 = event.pos
                        for i, cond in enumerate(CONDITIONS.keys()):
                            col = i % 4
                            row = i // 4
                            r = pygame.Rect(start_x + col * col_w, start_y + row * row_h, 115, 22)
                            if r.collidepoint(mx2, my2):
                                self._toggle_condition(cond)

                    # HP buttons
                    if self.selected_entity:
                        for b in self.hp_btns:
                            b.handle_event(event)
                        for b in self.init_btns:
                            b.handle_event(event)

                # Spell slot quick-use (click on slot pip)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.active_tab == 1:
                    if self.selected_entity:
                        mx2, my2 = event.pos
                        sx = GRID_W + 20
                        sy = TOP_BAR_H + 50
                        for lvl in range(1, 10):
                            key = {1:"1st",2:"2nd",3:"3rd"}.get(lvl, f"{lvl}th")
                            slots = self.selected_entity.spell_slots.get(key, 0)
                            if slots == 0:
                                continue
                            for pip in range(slots):
                                pr = pygame.Rect(sx + pip * 22, sy, 18, 18)
                                if pr.collidepoint(mx2, my2):
                                    self._use_spell_slot(lvl)
                            sy += 25

                # Panel scroll
                if event.type == pygame.MOUSEWHEEL:
                    if pygame.mouse.get_pos()[0] > GRID_W:
                        self.panel_scroll = max(-600, min(0, self.panel_scroll + event.y * 20))

                # Global buttons
                self.btn_next.handle_event(event)
                self.btn_menu.handle_event(event)
                self.btn_log_pl.handle_event(event)
                self.btn_save.handle_event(event)
                self.btn_load.handle_event(event)
                self.btn_terrain.handle_event(event)
                if not curr.is_player:
                    self.btn_ai.handle_event(event)

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
        curr = self.battle.get_current_entity()
        sel = self.selected_entity or curr

        self._draw_top_bar(screen, curr)
        self._draw_grid(screen)
        self._draw_terrain(screen)
        self._draw_aoe_overlays(screen)
        self._draw_entities(screen, curr, sel)
        self._draw_drag(screen)
        self._draw_grid_buttons(screen, mp)
        self._draw_panel(screen, curr, sel, mp)
        self._draw_bottom_bar(screen, curr, mp)

        if self.terrain_palette_open:
            self._draw_terrain_palette(screen, mp)
        if self.condition_reminder:
            self._draw_condition_reminder(screen, mp)
        if self.pending_plan:
            self._draw_ai_confirm_dialog(screen, mp)
        if self.player_action_mode:
            self._draw_player_action_panel(screen, mp)
        if self.ctx_open:
            self._draw_ctx_menu(screen, mp)

    # --- Top bar ---
    def _draw_top_bar(self, screen, curr):
        pygame.draw.rect(screen, (28,30,33), (0, 0, SCREEN_WIDTH, TOP_BAR_H))
        pygame.draw.line(screen, COLORS["border"], (0, TOP_BAR_H), (SCREEN_WIDTH, TOP_BAR_H), 2)
        # Round counter
        rt = fonts.header.render(f"ROUND {self.battle.round}", True, COLORS["accent"])
        screen.blit(rt, (15, TOP_BAR_H//2 - rt.get_height()//2))
        self.btn_menu.draw(screen, pygame.mouse.get_pos())
        # Initiative cards
        card_x = 130
        card_w, card_h = 130, 82
        for i, ent in enumerate(self.battle.entities):
            if card_x > SCREEN_WIDTH - 200:
                break
            is_curr = (ent == curr)
            bg   = COLORS["accent"] if is_curr else (45, 47, 52)
            bord = COLORS["success"] if is_curr else COLORS["border"]
            r = pygame.Rect(card_x, 8, card_w, card_h)
            pygame.draw.rect(screen, bg, r, border_radius=7)
            pygame.draw.rect(screen, bord, r, 2, border_radius=7)
            # Dead overlay
            if ent.hp <= 0:
                s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                s.fill((0,0,0,150))
                screen.blit(s, (card_x, 8))
            # HP bar
            pct = max(0, ent.hp / ent.max_hp) if ent.max_hp > 0 else 0
            bar_c = COLORS["success"] if pct>0.5 else COLORS["warning"] if pct>0.25 else COLORS["danger"]
            pygame.draw.rect(screen, (20,20,20), (card_x+4, 75, card_w-8, 6))
            pygame.draw.rect(screen, bar_c,      (card_x+4, 75, int((card_w-8)*pct), 6))
            # Name & initiative
            ns = fonts.tiny.render(ent.name[:14], True, COLORS["text_main"])
            is_ = fonts.header.render(str(ent.initiative), True, (255,255,255))
            hp_s = fonts.tiny.render(f"{ent.hp}/{ent.max_hp}", True, bar_c)
            screen.blit(ns, (card_x+6, 12))
            screen.blit(is_, (card_x+6, 30))
            screen.blit(hp_s, (card_x+6, 58))
            # Icons
            icon_x = card_x + card_w - 14
            if ent.action_used:
                pygame.draw.circle(screen, COLORS["danger"],  (icon_x, 18), 5)
                icon_x -= 14
            if ent.reaction_used:
                pygame.draw.circle(screen, COLORS["reaction"],(icon_x, 18), 5)
                icon_x -= 14
            if ent.concentrating_on:
                pygame.draw.circle(screen, COLORS["concentration"], (icon_x, 18), 5)
            card_x += card_w + 6

    # --- Grid ---
    def _draw_grid(self, screen):
        gsz = self.battle.grid_size
        for x in range(0, GRID_W, gsz):
            pygame.draw.line(screen, COLORS["grid"], (x, TOP_BAR_H), (x, SCREEN_HEIGHT))
        for y in range(TOP_BAR_H, SCREEN_HEIGHT, gsz):
            pygame.draw.line(screen, COLORS["grid"], (0, y), (GRID_W, y))

    # --- Terrain tiles ---
    def _draw_terrain(self, screen):
        gsz = self.battle.grid_size
        for t in self.battle.terrain:
            rx = t.grid_x * gsz
            ry = t.grid_y * gsz + TOP_BAR_H
            rw = t.width * gsz
            rh = t.height * gsz
            # Filled tile
            s = pygame.Surface((rw, rh), pygame.SRCALPHA)
            r, g, b = t.color
            s.fill((r, g, b, 200))
            screen.blit(s, (rx, ry))
            # Border
            pygame.draw.rect(screen, tuple(min(255, c+40) for c in t.color), (rx, ry, rw, rh), 2)
            # Label
            lbl = fonts.tiny.render(t.label[:6], True, (255, 255, 255))
            screen.blit(lbl, (rx + 2, ry + 2))
            # Hazard indicator
            if t.is_hazard:
                hz = fonts.tiny.render(t.hazard_damage, True, (255, 220, 0))
                screen.blit(hz, (rx + 2, ry + gsz - 16))

    # --- AOE spell overlays ---
    def _draw_aoe_overlays(self, screen):
        if not self.pending_plan:
            return
        steps = self.pending_plan.steps
        idx = self.pending_step_idx
        if idx >= len(steps):
            return
        step = steps[idx]
        if step.step_type != "spell" or not step.spell:
            return
        sp = step.spell
        if sp.aoe_radius <= 0 or not step.aoe_center:
            return

        gsz = self.battle.grid_size
        cx_grid, cy_grid = step.aoe_center
        cx_px = int(cx_grid * gsz + gsz // 2)
        cy_px = int(cy_grid * gsz + gsz // 2 + TOP_BAR_H)
        radius_px = int(sp.aoe_radius / 5 * gsz)

        # Semi-transparent overlay
        aoe_surf = pygame.Surface((radius_px * 2 + 4, radius_px * 2 + 4), pygame.SRCALPHA)
        if sp.damage_type == "fire":
            color = (255, 80, 20, 60)
            border = (255, 140, 0, 200)
        elif sp.damage_type == "cold":
            color = (80, 180, 255, 60)
            border = (140, 210, 255, 200)
        elif sp.damage_type == "lightning":
            color = (200, 200, 50, 60)
            border = (255, 255, 100, 200)
        elif sp.damage_type in ("necrotic", "poison"):
            color = (100, 50, 150, 60)
            border = (170, 80, 220, 200)
        else:
            color = (100, 100, 200, 60)
            border = (150, 150, 255, 200)

        if sp.aoe_shape == "cone":
            # Draw a 60-degree cone toward the nearest enemy cluster
            pts = [(radius_px + 2, radius_px + 2)]
            for deg in range(-30, 31, 5):
                rad = math.radians(deg)
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
        lbl = fonts.tiny.render(f"{sp.name} ({sp.aoe_radius}ft)", True, (255, 255, 200))
        screen.blit(lbl, (cx_px - lbl.get_width() // 2, cy_px - radius_px - 20))

    # --- Grid-area utility buttons (Save/Load/Terrain) ---
    def _draw_grid_buttons(self, screen, mp):
        for b in (self.btn_save, self.btn_load, self.btn_terrain):
            b.draw(screen, mp)
        # Terrain mode indicator
        if self.terrain_mode:
            tc = COLORS["warning"]
            pygame.draw.rect(screen, tc, self.btn_terrain.rect, 2, border_radius=5)
            sel = fonts.tiny.render(f"[{self.terrain_selected_type}]", True, tc)
            screen.blit(sel, (self.btn_terrain.rect.right + 4, self.btn_terrain.rect.y + 8))

    # --- Entities on grid ---
    def _draw_entities(self, screen, curr, sel):
        gsz = self.battle.grid_size
        for ent in self.battle.entities:
            if ent == self.dragging:
                continue
            cx = int(ent.grid_x * gsz + gsz//2)
            cy = int(ent.grid_y * gsz + gsz//2 + TOP_BAR_H)
            if ent == sel:
                pygame.draw.circle(screen, COLORS["warning"], (cx, cy), gsz//2+3, 2)
            if ent == curr:
                pygame.draw.circle(screen, (255,255,255,80), (cx, cy), gsz//2+1)
            r = gsz//2 - 3
            self._draw_token(screen, ent, cx, cy, r)
            hp_bar.draw(screen, cx, cy+r+4, gsz-10, ent.hp, ent.max_hp)
            # Dead X
            if ent.hp <= 0:
                pygame.draw.line(screen, COLORS["danger"], (cx-r, cy-r), (cx+r, cy+r), 2)
                pygame.draw.line(screen, COLORS["danger"], (cx+r, cy-r), (cx-r, cy+r), 2)

    # --- Drag visual ---
    def _draw_drag(self, screen):
        if not self.dragging:
            return
        mx, my = pygame.mouse.get_pos()
        gsz = self.battle.grid_size
        sx = int(self.drag_start[0] * gsz + gsz//2)
        sy = int(self.drag_start[1] * gsz + gsz//2 + TOP_BAR_H)
        dist_ft = math.hypot(mx-sx, my-sy) / gsz * 5
        can_move = dist_ft <= self.dragging.stats.speed
        lc = COLORS["success"] if can_move else COLORS["danger"]
        pygame.draw.line(screen, lc, (sx, sy), (mx, my), 2)
        dt = fonts.small.render(f"{dist_ft:.0f} ft", True, (255,255,255))
        screen.blit(dt, (mx+12, my+10))
        r = self.battle.grid_size//2 - 3
        self._draw_token(screen, self.dragging, mx, my, r)
        # Distance to enemies
        for e in self.battle.entities:
            if e.is_player == self.dragging.is_player or e.hp <= 0:
                continue
            ex = int(e.grid_x * gsz + gsz//2)
            ey = int(e.grid_y * gsz + gsz//2 + TOP_BAR_H)
            edf = math.hypot(mx-ex, my-ey) / gsz * 5
            pygame.draw.line(screen, (80,80,80), (mx,my), (ex,ey), 1)
            eds = fonts.tiny.render(f"{edf:.0f}ft", True, COLORS["text_dim"])
            screen.blit(eds, (ex, ey-14))

    # --- Right panel ---
    def _draw_panel(self, screen, curr, sel, mp):
        panel_rect = pygame.Rect(GRID_W, TOP_BAR_H, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H)
        pygame.draw.rect(screen, COLORS["panel_dark"], panel_rect)
        pygame.draw.line(screen, COLORS["border"], (GRID_W, TOP_BAR_H), (GRID_W, SCREEN_HEIGHT), 3)

        # Active creature header
        hdr_rect = pygame.Rect(GRID_W, TOP_BAR_H, PANEL_W, 38)
        pygame.draw.rect(screen, (35,37,41), hdr_rect)
        at = fonts.body.render(f"Active: {curr.name}  (Init {curr.initiative})", True, COLORS["accent"])
        screen.blit(at, (GRID_W+12, TOP_BAR_H+8))

        # Tabs
        for i, tab in enumerate(TABS):
            tr = pygame.Rect(GRID_W + i*118, TOP_BAR_H+38, 116, 28)
            bg = COLORS["accent"] if i == self.active_tab else (45,47,52)
            pygame.draw.rect(screen, bg, tr, border_radius=4)
            tt = fonts.small.render(tab, True, COLORS["text_main"])
            screen.blit(tt, tt.get_rect(center=tr.center))

        content_y = TOP_BAR_H + 70 + self.panel_scroll
        x0 = GRID_W + 12

        # Clip panel content
        clip = pygame.Rect(GRID_W, TOP_BAR_H+68, PANEL_W, SCREEN_HEIGHT - TOP_BAR_H - 68 - 70)
        screen.set_clip(clip)

        if self.active_tab == 0:
            content_y = self._draw_stats_tab(screen, sel, x0, content_y, mp)
        elif self.active_tab == 1:
            content_y = self._draw_spells_tab(screen, sel, x0, content_y, mp)
        elif self.active_tab == 2:
            content_y = self._draw_log_tab(screen, x0, content_y)

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
        if sel.stats.saving_throws:
            saves_str = "  ".join(f"{k[:3]}:{v:+d}" for k,v in sel.stats.saving_throws.items())
            ln(f"Saves: {saves_str}", COLORS["text_dim"])

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
            ln(f"Legendary Actions: {sel.legendary_actions_left}/{sel.stats.legendary_action_count}", COLORS["legendary"])
        if sel.stats.legendary_resistance_count:
            ln(f"Legendary Resist: {sel.legendary_resistances_left}/{sel.stats.legendary_resistance_count}", COLORS["legendary"])

        # Conditions
        ln("")
        ln("CONDITIONS:", COLORS["text_dim"])
        start_x = x0
        start_y = y
        col_w, row_h = 120, 22
        hovered_desc = None
        for i, (cond, desc) in enumerate(CONDITIONS.items()):
            col = i % 4
            row = i // 4
            r = pygame.Rect(start_x + col*col_w, start_y + row*row_h, 116, 20)
            is_active = sel.has_condition(cond)
            bg = COLORS["accent"] if is_active else (45,47,52)
            if r.collidepoint(mp):
                bg = COLORS["accent_hover"] if is_active else (60,62,67)
                hovered_desc = f"{cond}: {desc}"
            pygame.draw.rect(screen, bg, r, border_radius=3)
            ct = fonts.tiny.render(cond, True, COLORS["text_main"])
            screen.blit(ct, (r.x+4, r.y+3))
        y = start_y + (((len(CONDITIONS)-1)//4)+1) * row_h + 8

        if hovered_desc:
            mx2, my2 = mp
            tip = fonts.tiny.render(hovered_desc[:90], True, (255,255,255))
            tip_bg = pygame.Rect(mx2+15, my2+10, tip.get_width()+10, tip.get_height()+8)
            pygame.draw.rect(screen, (20,20,20), tip_bg)
            screen.blit(tip, (mx2+20, my2+14))

        # Features summary
        if sel.stats.features:
            ln("")
            ln("FEATURES:", COLORS["text_dim"])
            for feat in sel.stats.features[:8]:
                uses_str = ""
                if feat.uses_per_day > 0:
                    remaining = sel.feature_uses.get(feat.name, feat.uses_per_day)
                    uses_str = f" [{remaining}/{feat.uses_per_day}]"
                ln(f"• {feat.name}{uses_str}", COLORS["text_main"], 8)

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
                px += 20
            y += 22

        # Cantrips
        if sel.stats.cantrips:
            ln("")
            ln("CANTRIPS:", COLORS["text_dim"])
            for sp in sel.stats.cantrips:
                ln(f"  {sp.name}  ({sp.range}ft, {sp.damage_dice or sp.description[:30]})", COLORS["text_main"], 4)

        # Spells
        if sel.stats.spells_known:
            ln("")
            ln("SPELLS KNOWN:", COLORS["text_dim"])
            for sp in sel.stats.spells_known:
                key2 = _LEVEL_NAMES.get(sp.level, f"{sp.level}th")
                conc = " [C]" if sp.concentration else ""
                dmg_str = sp.damage_dice or sp.heals or sp.applies_condition or sp.description[:25] or ""
                ln(f"  [{key2}]{conc} {sp.name}: {dmg_str}", COLORS["spell"], 4)

        return y

    def _draw_log_tab(self, screen, x0, y):
        for msg in reversed(self.logs):
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

        self.btn_next.draw(screen, mp)
        self.btn_log_pl.draw(screen, mp)

        if not curr.is_player:
            if curr.action_used:
                self.btn_ai.text  = "AI DONE"
                self.btn_ai.color = COLORS["text_dim"]
            else:
                self.btn_ai.text  = "AI AUTO-PLAY"
                self.btn_ai.color = COLORS["accent"]
            self.btn_ai.draw(screen, mp)

    # --- AI confirm dialog ---
    def _draw_ai_confirm_dialog(self, screen, mp):
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

        bw, bh = 620, 360
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

        # Hit/damage summary
        if step.step_type in ("attack","spell") and step.target:
            y += 8
            if step.is_crit:
                cr = fonts.body.render("CRITICAL HIT!", True, COLORS["legendary"])
                screen.blit(cr, (bx+14, y))
                y += 28
            elif step.is_hit:
                hs = fonts.body.render(f"HIT: {step.damage} {step.damage_type} damage", True, COLORS["danger"])
                screen.blit(hs, (bx+14, y))
                y += 28
            else:
                ms = fonts.body.render("MISS", True, COLORS["text_dim"])
                screen.blit(ms, (bx+14, y))
                y += 28
            if step.target.hp <= 0:
                dead = fonts.body.render(f"{step.target.name} is DOWN!", True, COLORS["danger"])
                screen.blit(dead, (bx+14, y))
                y += 28
            elif step.is_hit:
                rem = fonts.body.render(f"{step.target.name} HP: {step.target.hp}/{step.target.max_hp}", True, COLORS["text_dim"])
                screen.blit(rem, (bx+14, y))

        # Upcoming steps
        if len(steps) > idx + 1:
            next_lbl = fonts.tiny.render(f"Next: {steps[idx+1].step_type.upper()} – {steps[idx+1].description[:60]}", True, COLORS["text_dim"])
            screen.blit(next_lbl, (bx+14, by+bh-55))

        self.btn_confirm.rect.topleft = (bx + bw//2 - 135, by + bh - 55)
        self.btn_deny.rect.topleft    = (bx + bw//2 + 10,  by + bh - 55)
        self.btn_approve_all.rect.topleft = (bx + bw//2 - 65, by + bh - 100)
        self.btn_confirm.draw(screen, mp)
        self.btn_deny.draw(screen, mp)
        self.btn_approve_all.draw(screen, mp)

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
        bw = 150
        pad = 8
        item_h = 28
        n = len(TERRAIN_TYPES)
        bh = n * item_h + pad * 2 + 30

        bx = 10
        by = TOP_BAR_H + 10

        pygame.draw.rect(screen, (35, 37, 42), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], (bx, by, bw, bh), 1, border_radius=6)
        hdr = fonts.small.render("Select Terrain", True, COLORS["accent"])
        screen.blit(hdr, (bx + 6, by + 6))

        y = by + pad + 22
        for ttype, props in TERRAIN_TYPES.items():
            r = pygame.Rect(bx + 4, y, bw - 8, item_h - 2)
            is_sel = ttype == self.terrain_selected_type
            bg = COLORS["accent"] if is_sel else (50, 52, 57)
            if r.collidepoint(mp):
                bg = COLORS["accent_hover"]
            pygame.draw.rect(screen, bg, r, border_radius=3)
            # Color swatch
            pygame.draw.rect(screen, props["color"], (r.x + 3, r.y + 4, 16, 16), border_radius=2)
            pygame.draw.rect(screen, (0, 0, 0), (r.x + 3, r.y + 4, 16, 16), 1, border_radius=2)
            lbl = fonts.tiny.render(props["label"], True, COLORS["text_main"])
            screen.blit(lbl, (r.x + 22, r.y + 6))
            y += item_h

    # --- Terrain mode toggle ---
    def _toggle_terrain_mode(self):
        self.terrain_mode = not self.terrain_mode
        self.terrain_palette_open = self.terrain_mode
        if self.terrain_mode:
            self._log("[TERRAIN] Terrain placement mode ON. Left-click=place, Right-click=remove.")
        else:
            self._log("[TERRAIN] Terrain placement mode OFF.")

    # --- Save / Load ---
    def _save_encounter(self):
        try:
            self.battle.save_state(SAVE_FILE)
            self._log("[SAVE] Encounter saved.")
        except Exception as ex:
            self._log(f"[SAVE ERROR] {ex}")

    def _load_encounter(self):
        if not os.path.exists(SAVE_FILE):
            self._log("[LOAD] No save file found.")
            return
        try:
            new_battle = BattleSystem.from_save(SAVE_FILE, self._log)
            new_battle.log = self._log
            self.battle = new_battle
            self.selected_entity = None
            self.pending_plan = None
            self.condition_reminder = None
            self._log("[LOAD] Encounter loaded.")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._log(f"[LOAD ERROR] {ex}")
