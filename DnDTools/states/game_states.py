import pygame
import math
import os
import random
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from engine.battle import BattleSystem
from data.library import library
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores, Action
from data.heroes import hero_list
from data.conditions import CONDITIONS

class GameState:
    def __init__(self, manager):
        self.manager = manager
    def handle_events(self, events): pass
    def update(self): pass
    def draw(self, screen): pass

class MenuState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.buttons = [
            Button(cx - 150, cy - 50, 300, 60, "New Encounter", lambda: self.manager.change_state("SETUP")),
            Button(cx - 150, cy + 30, 300, 60, "Load Campaign", lambda: print("Load...")),
            Button(cx - 150, cy + 110, 300, 60, "Exit", lambda: self.manager.quit())
        ]

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        title = fonts.title.render("D&D 5e AI Toolset", True, COLORS["accent"])
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        sub = fonts.header.render("Endgame Encounter Manager", True, COLORS["text_dim"])
        screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 230))
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.draw(screen, mouse_pos)

class EncounterSetupState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.available_monsters = library.get_all_monsters()
        
        self.roster = [] # Lista valituista Entity-olioista
        self.available_heroes = hero_list

        self.buttons = [
            Button(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 60, "START BATTLE", self.start_battle, color=COLORS["success"]),
            Button(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 180, 200, 60, "Long Rest All", self.do_long_rest, color=COLORS["accent"]),
            Button(20, 20, 120, 40, "< Menu", lambda: self.manager.change_state("MENU"))
        ]
        
        # --- 1. Ryhmitellään monsterit CR:n mukaan ---
        self.monsters_by_cr = {}
        for m in self.available_monsters:
            cr = m.challenge_rating
            if cr not in self.monsters_by_cr:
                self.monsters_by_cr[cr] = []
            self.monsters_by_cr[cr].append(m)
        
        self.sorted_crs = sorted(self.monsters_by_cr.keys())
        self.selected_cr = None
        self.scroll_y = 0
        
        # Luodaan CR-valintanapit vasempaan reunaan
        self.cr_buttons = []
        y_off = 120
        for cr in self.sorted_crs:
            label = f"CR {cr}" if cr % 1 == 0 else f"CR {cr:.3g}"
            btn = Button(50, y_off, 100, 40, label, lambda c=cr: self.select_cr(c), color=COLORS["panel"])
            self.cr_buttons.append(btn)
            y_off += 45
            
        self.active_monster_buttons = [] # Generoidaan kun CR valitaan
            
        # Luodaan napit sankareille
        self.hero_buttons = []
        y_off = 120
        for h in self.available_heroes:
            btn = Button(500, y_off, 250, 40, f"Add {h.name}", 
                         lambda hero=h: self.add_hero(hero), color=COLORS["player"])
            self.hero_buttons.append(btn)
            y_off += 45

    def add_hero(self, stats):
        # Sijoitetaan vasemmalle
        y_pos = 2 + len([e for e in self.roster if e.is_player]) * 2
        self.roster.append(Entity(stats, 3, y_pos, is_player=True))

    def add_monster(self, stats):
        # Luodaan uusi instanssi monsterista
        # Sijoitetaan oikealle
        enemies_count = len([e for e in self.roster if not e.is_player])
        x_pos = 15 + (enemies_count % 2) * 2
        y_pos = 2 + (enemies_count * 2)
        
        new_entity = Entity(stats, x_pos, y_pos, is_player=False)
        self.roster.append(new_entity)

    def select_cr(self, cr):
        self.selected_cr = cr
        self.scroll_y = 0
        self.active_monster_buttons = []
        
        # Luo napit valitun CR:n monstereille
        for i, m in enumerate(self.monsters_by_cr[cr]):
            btn = Button(170, 0, 300, 40, f"{m.name}", lambda mon=m: self.add_monster(mon), color=COLORS["panel"])
            self.active_monster_buttons.append(btn)

    def do_long_rest(self):
        for entity in self.roster:
            entity.long_rest()

    def start_battle(self):
        if not self.roster: return
        # Siirrytään taisteluun ja annetaan valittu rosteri
        self.manager.states["BATTLE"] = BattleState(self.manager, self.roster)
        self.manager.change_state("BATTLE")

    def handle_events(self, events):
        for event in events:
            # Scrollaus (Mouse Wheel)
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_y += event.y * 20
                # Rajoita scrollausta
                if self.scroll_y > 0: self.scroll_y = 0
                
            for btn in self.buttons + self.hero_buttons + self.cr_buttons:
                btn.handle_event(event)
            
            # Käsittele monster-napit (huomioi scrollaus osumatarkistuksessa on vaikeaa Button-luokalla suoraan,
            # joten päivitämme nappien rect-sijainnin draw-loopissa tai tässä)
            # Yksinkertaisempi tapa: Button.handle_event tarkistaa hiiren sijainnin vs rect.
            # Meidän pitää päivittää rectit ennen handle_eventiä draw-funktiossa, 
            # mutta handle_events ajetaan usein ensin.
            # Päivitetään rectit tässä väliaikaisesti osumatarkistusta varten.
            for i, btn in enumerate(self.active_monster_buttons):
                btn.rect.y = 120 + i * 45 + self.scroll_y
                btn.handle_event(event)

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        
        # Otsikko
        title = fonts.header.render("Encounter Setup", True, COLORS["accent"])
        screen.blit(title, (50, 80))

        # Sarakkeet
        sub1 = fonts.body.render("CR Level:", True, COLORS["text_dim"])
        screen.blit(sub1, (50, 120))
        
        sub2 = fonts.body.render("Heroes:", True, COLORS["text_dim"])
        screen.blit(sub2, (500, 120))

        mouse_pos = pygame.mouse.get_pos()
        
        # 1. CR Napit
        for btn in self.cr_buttons:
            # Korosta valittu
            if self.selected_cr is not None:
                # Parsitaan luku tekstistä vertailua varten tai käytetään lambda-arvoa
                pass 
            btn.draw(screen, mouse_pos)
            
        # 2. Monsterilista (Scrollattava alue)
        if self.selected_cr is not None:
            # Määritellään leikkausalue (clipping rect)
            clip_rect = pygame.Rect(170, 120, 310, SCREEN_HEIGHT - 200)
            screen.set_clip(clip_rect)
            
            for i, btn in enumerate(self.active_monster_buttons):
                # Päivitetään sijainti scrollauksen mukaan
                btn.rect.y = 120 + i * 45 + self.scroll_y
                btn.draw(screen, mouse_pos)
            
            screen.set_clip(None) # Poista leikkaus
            
        for btn in self.hero_buttons:
            btn.draw(screen, mouse_pos)

        # Oikea puoli: Rosteri
        sub3 = fonts.body.render("Current Roster:", True, COLORS["text_dim"])
        screen.blit(sub3, (800, 120))
        
        y_off = 150
        for entity in self.roster:
            color = COLORS["player"] if entity.is_player else COLORS["enemy"]
            txt = fonts.body.render(f"{entity.name} (HP: {entity.hp}/{entity.max_hp})", True, color)
            screen.blit(txt, (800, y_off))
            y_off += 30

        # Napit
        for btn in self.buttons:
            btn.draw(screen, mouse_pos)

class BattleState(GameState):
    def __init__(self, manager, entities=None):
        super().__init__(manager)
        self.logs = ["Taistelu alkaa..."]
        # Välitetään entities BattleSystemille
        self.battle_sys = BattleSystem(self.add_log, initial_entities=entities)
        self.pending_action = None
        
        self.selected_entity = None # DM valinta
        
        # Drag & Drop tilat
        self.dragging_entity = None
        self.drag_start_pos = (0, 0) # Grid x, y
        
        self.top_bar_height = 100
        self.token_images = {} # Välimuisti kuville

        # Context Menu State
        self.ctx_menu_open = False
        self.ctx_menu_pos = (0, 0)
        self.ctx_menu_options = [] # list of (text, callback)
        self.ctx_menu_rects = []

        # Buttons
        self.btn_next = Button(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 70, 160, 50, "NEXT TURN >>", self.do_next_turn, color=COLORS["success"])
        self.btn_ai = Button(SCREEN_WIDTH - 350, SCREEN_HEIGHT - 70, 160, 50, "AI AUTO-PLAY", self.do_ai_turn, color=COLORS["accent"])
        self.btn_menu = Button(10, 10, 80, 30, "Menu", lambda: self.manager.change_state("MENU"))
        
        # DM Panel Buttons (HP)
        self.hp_btns = []
        vals = [-10, -5, -1, 1, 5, 10]
        for v in vals:
            c = COLORS["danger"] if v < 0 else COLORS["success"]
            txt = f"{v}" if v < 0 else f"+{v}"
            self.hp_btns.append(Button(0, 0, 40, 25, txt, lambda val=v: self.modify_hp(val), color=c))
            
        # DM Panel Buttons (Rolls)
        self.btn_roll_save = Button(0, 0, 110, 30, "Save Throw", lambda: self.open_save_menu(), color=COLORS["panel"])
        self.btn_roll_skill = Button(0, 0, 110, 30, "Skill Check", lambda: self.open_skill_menu(), color=COLORS["panel"])

        # Confirmation buttons
        self.confirm_btn = Button(SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 100, 120, 50, "FORCE HIT", lambda: self.resolve_action(True), color=COLORS["success"])
        self.deny_btn = Button(SCREEN_WIDTH//2 + 10, SCREEN_HEIGHT//2 + 100, 120, 50, "FORCE MISS", lambda: self.resolve_action(False), color=COLORS["danger"])

    def add_log(self, msg):
        self.logs.append(msg)
        if len(self.logs) > 30: self.logs.pop(0) # Enemmän historiaa näkyviin

    def modify_hp(self, amount):
        if self.selected_entity:
            self.selected_entity.hp += amount
            # Rajoita max HP:hen
            if self.selected_entity.hp > self.selected_entity.max_hp:
                self.selected_entity.hp = self.selected_entity.max_hp
            
            action_txt = "healed" if amount > 0 else "took damage"
            self.add_log(f"MANUAL: {self.selected_entity.name} {action_txt} ({abs(amount)}).")

    def modify_init(self, amount):
        if self.selected_entity:
            self.battle_sys.update_initiative(self.selected_entity, amount)

    def toggle_condition(self, condition):
        if not self.selected_entity: return
        
        if self.selected_entity.has_condition(condition):
            self.selected_entity.remove_condition(condition)
            self.add_log(f"{self.selected_entity.name} is no longer {condition}.")
        else:
            self.selected_entity.add_condition(condition)
            self.add_log(f"{self.selected_entity.name} is now {condition}.")

    def do_next_turn(self):
        current = self.battle_sys.next_turn()
        self.selected_entity = current # Auto-select active character

    def do_ai_turn(self):
        current = self.battle_sys.get_current_entity()
        if not current.is_player:
            action = self.battle_sys.calculate_ai_turn(current)
            if action["type"] == "attack":
                self.pending_action = action
                # self.add_log(f"AI: {action['message']}") # Logataan vasta kun vahvistetaan
            elif action["type"] == "done":
                pass # Button handles visual feedback
            else:
                self.add_log(action["message"])

    def resolve_action(self, hit):
        if self.pending_action:
            self.battle_sys.resolve_attack(self.pending_action, hit)
            self.pending_action = None
            
            # Jatka AI:n vuoroa automaattisesti jos mahdollista
            curr = self.battle_sys.get_current_entity()
            if not curr.is_player:
                self.do_ai_turn()

    def show_context_menu(self, options, pos):
        self.ctx_menu_open = True
        self.ctx_menu_pos = pos
        self.ctx_menu_options = options
        
        # Lasketaan rectit
        x, y = pos
        w, h = 160, 30
        self.ctx_menu_rects = []
        for i, (txt, cb) in enumerate(self.ctx_menu_options):
            rect = pygame.Rect(x, y + i*h, w, h)
            self.ctx_menu_rects.append((rect, cb, txt))

    def open_context_menu(self, pos, entity):
        self.selected_entity = entity
        options = [
            (f"Damage 5", lambda: self.modify_hp(-5)),
            (f"Damage 10", lambda: self.modify_hp(-10)),
            (f"Heal 5", lambda: self.modify_hp(5)),
            (f"Toggle Prone", lambda: self.toggle_condition("Prone")),
            (f"Toggle Stunned", lambda: self.toggle_condition("Stunned")),
            (f"Init +1", lambda: self.modify_init(1)),
            (f"Init -1", lambda: self.modify_init(-1)),
        ]
        self.show_context_menu(options, pos)

    def open_save_menu(self):
        if not self.selected_entity: return
        options = []
        for attr in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            options.append((attr, lambda a=attr: self.roll_save(a)))
        self.show_context_menu(options, pygame.mouse.get_pos())

    def roll_save(self, attr):
        ent = self.selected_entity
        bonus = ent.stats.saving_throws.get(attr, ent.get_modifier(attr))
        roll = random.randint(1, 20)
        self.add_log(f"{ent.name} {attr} Save: {roll+bonus} ({roll}{'+' if bonus>=0 else ''}{bonus})")

    def open_skill_menu(self):
        if not self.selected_entity: return
        options = []
        if self.selected_entity.stats.skills:
            for skill, bonus in self.selected_entity.stats.skills.items():
                options.append((f"{skill} ({bonus:+})", lambda s=skill, b=bonus: self.roll_skill(s, b)))
        else:
            options.append(("No skills defined", lambda: None))
        self.show_context_menu(options, pygame.mouse.get_pos())

    def roll_skill(self, skill, bonus):
        ent = self.selected_entity
        roll = random.randint(1, 20)
        self.add_log(f"{ent.name} {skill}: {roll+bonus} ({roll}{'+' if bonus>=0 else ''}{bonus})")

    def get_token_image(self, name):
        """Lataa tai hakee välimuistista token-kuvan."""
        if name in self.token_images:
            return self.token_images[name]
        
        # Yritetään ladata tiedostosta (esim. data/tokens/Wolf.png)
        # Huom: Käyttäjän pitää luoda kansio ja lisätä kuvat
        path = os.path.join("data", "tokens", f"{name}.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.token_images[name] = img
                return img
            except Exception as e:
                print(f"Error loading token {name}: {e}")
        
        self.token_images[name] = None # Ei löytynyt, merkitään None
        return None

    def draw_token(self, screen, entity, cx, cy, radius):
        # 1. Varjo (Shadow)
        pygame.draw.circle(screen, (0, 0, 0, 80), (cx + 4, cy + 4), radius)
        
        img = self.get_token_image(entity.name)
        if img:
            # Skaalataan kuva sopivaksi
            scaled = pygame.transform.smoothscale(img, (int(radius*2), int(radius*2)))
            rect = scaled.get_rect(center=(cx, cy))
            screen.blit(scaled, rect)
            
            # Reunus kuvan päälle
            border_color = (255, 215, 0) if entity.is_player else (192, 192, 192)
            pygame.draw.circle(screen, border_color, (cx, cy), radius, 3)
        else:
            # Fallback: Hieno proseduuraalinen token
            # Ulkoreuna (Kulta pelaajille, Hopea vihollisille)
            border_color = (255, 215, 0) if entity.is_player else (169, 169, 169)
            pygame.draw.circle(screen, border_color, (cx, cy), radius)
            
            # Sisäosa (Tummempi tausta)
            pygame.draw.circle(screen, (30, 30, 30), (cx, cy), radius - 4)
            
            # Tiimin väri (Rengas)
            pygame.draw.circle(screen, entity.color, (cx, cy), radius - 6, 4)
            
            # Nimikirjaimet
            initials = entity.name[:2].upper()
            txt = fonts.header.render(initials, True, (240, 240, 240))
            # Tekstin varjo
            txt_s = fonts.header.render(initials, True, (0, 0, 0))
            screen.blit(txt_s, (cx - txt.get_width()//2 + 2, cy - txt.get_height()//2 + 2))
            screen.blit(txt, (cx - txt.get_width()//2, cy - txt.get_height()//2))
            
            # Kiilto (Gloss effect) - Yläosan heijastus
            gloss_surf = pygame.Surface((radius*2, radius), pygame.SRCALPHA)
            pygame.draw.ellipse(gloss_surf, (255, 255, 255, 40), (0, 0, radius*2, radius))
            screen.blit(gloss_surf, (cx - radius, cy - radius + 2))

    def handle_events(self, events):
        for event in events:
            try:
                if self.pending_action:
                    self.confirm_btn.handle_event(event)
                    self.deny_btn.handle_event(event)
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 1. Context Menu Click
                    if self.ctx_menu_open:
                        clicked_menu = False
                        for rect, cb, txt in self.ctx_menu_rects:
                            if rect.collidepoint(event.pos):
                                cb()
                                clicked_menu = True
                                self.ctx_menu_open = False
                                break
                        if not clicked_menu:
                            self.ctx_menu_open = False # Sulje jos klikkaa ohi
                        continue # Älä tee muuta

                    # 2. Drag & Drop Logic (DM voi liikuttaa kaikkia)
                    grid_sz = self.battle_sys.grid_size
                    mx, raw_my = event.pos
                    my = raw_my - self.top_bar_height # Adjust for top bar
                    
                    # Tarkista osuuko gridiin
                    if mx < SCREEN_WIDTH - 500 and my >= 0:
                        # Käytetään float-koordinaatteja haussa
                        clicked_ent = self.battle_sys.get_entity_at(mx / grid_sz, my / grid_sz)
                        if clicked_ent:
                            self.selected_entity = clicked_ent
                            self.dragging_entity = clicked_ent
                            self.drag_start_pos = (clicked_ent.grid_x, clicked_ent.grid_y)
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    # Right Click -> Context Menu
                    grid_sz = self.battle_sys.grid_size
                    mx, raw_my = event.pos
                    my = raw_my - self.top_bar_height
                    if mx < SCREEN_WIDTH - 500 and my >= 0:
                        clicked_ent = self.battle_sys.get_entity_at(mx / grid_sz, my / grid_sz)
                        if clicked_ent:
                            self.open_context_menu(event.pos, clicked_ent)
                
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragging_entity:
                        grid_sz = self.battle_sys.grid_size
                        
                        # Vapaa liikkuminen (float koordinaatit), ei grid-lukitusta
                        float_x = event.pos[0] / grid_sz
                        float_y = (event.pos[1] - self.top_bar_height) / grid_sz
                        
                        if event.pos[0] < SCREEN_WIDTH - 500 and event.pos[1] > self.top_bar_height:
                            # Tarkista päällekkäisyys
                            if not self.battle_sys.is_occupied(float_x, float_y, exclude=self.dragging_entity):
                                self.dragging_entity.grid_x = float_x
                                self.dragging_entity.grid_y = float_y
                                
                                dist = math.hypot(float_x - self.drag_start_pos[0], float_y - self.drag_start_pos[1]) * 5
                                if dist > 0:
                                    self.add_log(f"{self.dragging_entity.name} moved {dist:.1f} ft.")
                            else:
                                self.add_log("Cannot move: Space occupied.")
                        
                        self.dragging_entity = None

                # DM Panel Buttons
                if self.selected_entity:
                    for btn in self.hp_btns:
                        btn.handle_event(event)
                    
                    # Roll buttons
                    self.btn_roll_save.handle_event(event)
                    self.btn_roll_skill.handle_event(event)
                    
                    # Condition toggles
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        start_x = SCREEN_WIDTH - 480
                        start_y = 365 # Adjusted to match draw logic (TopBar 100 + offsets)
                        col_w, row_h = 115, 25
                        
                        i = 0
                        for cond in CONDITIONS.keys():
                            col = i % 4
                            row = i // 4
                            rect = pygame.Rect(start_x + col * col_w, start_y + row * row_h, 110, 22)
                            if rect.collidepoint(mx, my):
                                self.toggle_condition(cond)
                            i += 1
                
                self.btn_next.handle_event(event)
                self.btn_menu.handle_event(event)
                
                # AI Nappi vain jos NPC vuoro
                curr = self.battle_sys.get_current_entity()
                if not curr.is_player:
                    self.btn_ai.handle_event(event)
            except Exception as e:
                print(f"Error handling event: {e}")

    def draw(self, screen):
        screen.fill(COLORS["bg"])
        
        grid_area_width = SCREEN_WIDTH - 500 # Leveämpi paneeli
        grid_sz = self.battle_sys.grid_size
        top_bar_h = self.top_bar_height
        
        # --- TOP BAR (Initiative & Round) ---
        pygame.draw.rect(screen, (30, 30, 35), (0, 0, SCREEN_WIDTH, top_bar_h))
        pygame.draw.line(screen, COLORS["border"], (0, top_bar_h), (SCREEN_WIDTH, top_bar_h), 2)
        
        # Round Counter
        round_txt = fonts.header.render(f"ROUND {self.battle_sys.round}", True, COLORS["accent"])
        screen.blit(round_txt, (20, top_bar_h // 2 - round_txt.get_height() // 2))
        
        # Initiative Scroll
        init_start_x = 200
        card_w, card_h = 140, 80
        gap = 10
        
        # Järjestetään entiteetit (BattleSystem pitää ne järjestyksessä, mutta varmistetaan)
        # Piirretään kortit
        for i, ent in enumerate(self.battle_sys.entities):
            x = init_start_x + i * (card_w + gap)
            if x > SCREEN_WIDTH: break # Ei piirretä ruudun ulkopuolelle
            
            is_curr = (ent == self.battle_sys.get_current_entity())
            bg_c = COLORS["accent"] if is_curr else (50, 52, 55)
            border_c = COLORS["success"] if is_curr else COLORS["border"]
            
            card_rect = pygame.Rect(x, 10, card_w, card_h)
            pygame.draw.rect(screen, bg_c, card_rect, border_radius=8)
            pygame.draw.rect(screen, border_c, card_rect, 2, border_radius=8)
            
            name_s = fonts.small.render(ent.name[:12], True, COLORS["text_main"])
            init_s = fonts.header.render(str(ent.initiative), True, (255, 255, 255))
            screen.blit(name_s, (x + 10, 15))
            screen.blit(init_s, (x + 10, 40))

        # --- GRID AREA ---
        # 1. Piirrä ruudukko
        for x in range(0, grid_area_width, grid_sz):
            pygame.draw.line(screen, (30, 32, 35), (x, top_bar_h), (x, SCREEN_HEIGHT))
        for y in range(top_bar_h, SCREEN_HEIGHT, grid_sz):
            pygame.draw.line(screen, (30, 32, 35), (0, y), (grid_area_width, y))

        # 2. Piirrä entiteetit
        for ent in self.battle_sys.entities:
            if ent == self.dragging_entity: continue 
            
            cx = ent.grid_x * grid_sz + grid_sz // 2
            cy = ent.grid_y * grid_sz + grid_sz // 2 + top_bar_h
            
            # Highlight valitulle
            if ent == self.selected_entity:
                pygame.draw.circle(screen, (255, 255, 0, 100), (cx, cy), grid_sz // 2 + 2, 2)

            if ent == self.battle_sys.get_current_entity():
                pygame.draw.circle(screen, (255, 255, 255, 50), (cx, cy), grid_sz // 2)

            # --- TOKEN GRAPHICS ---
            # Käytetään uutta piirtofunktiota
            self.draw_token(screen, ent, cx, cy, grid_sz // 2 - 3)
            
            # HP Bar
            hp_pct = max(0, ent.hp / ent.max_hp)
            bar_color = COLORS["success"] if hp_pct > 0.5 else (255, 193, 7) if hp_pct > 0.25 else COLORS["danger"]
            pygame.draw.rect(screen, (0, 0, 0), (cx - 20, cy + 20, 40, 6))
            pygame.draw.rect(screen, bar_color, (cx - 19, cy + 21, 38 * hp_pct, 4))
            
            # Status indicator (pieni piste jos statuksia)
            if ent.conditions:
                pygame.draw.circle(screen, (200, 50, 200), (cx + 15, cy - 15), 5)

        # 3. Dragging Visuals (Viivat ja haamu)
        if self.dragging_entity:
            mx, my = pygame.mouse.get_pos()
            start_cx = self.drag_start_pos[0] * grid_sz + grid_sz // 2
            start_cy = self.drag_start_pos[1] * grid_sz + grid_sz // 2 + top_bar_h
            
            # Laske etäisyys lähtöpisteestä
            dist_px = math.hypot(mx - start_cx, my - start_cy)
            dist_ft = (dist_px / grid_sz) * 5
            
            # Väri: Vihreä jos speed riittää, punainen jos ei
            line_color = COLORS["success"] if dist_ft <= self.dragging_entity.stats.speed else COLORS["danger"]
            
            # Piirrä viiva lähtöpisteestä
            pygame.draw.line(screen, line_color, (start_cx, start_cy), (mx, my), 2)
            
            # Piirrä etäisyysteksti viivan keskelle
            mid_x, mid_y = (start_cx + mx) // 2, (start_cy + my) // 2
            dist_txt = fonts.small.render(f"{dist_ft:.1f} ft", True, (255, 255, 255))
            screen.blit(dist_txt, (mx + 10, my + 10))
            
            # Draw ghost token
            self.draw_token(screen, self.dragging_entity, mx, my, grid_sz // 2 - 3)

            # Piirrä viivat vihollisiin (Range indicators)
            for enemy in [e for e in self.battle_sys.entities if not e.is_player and e.hp > 0]:
                ex = enemy.grid_x * grid_sz + grid_sz // 2
                ey = enemy.grid_y * grid_sz + grid_sz // 2 + top_bar_h
                enemy_dist = (math.hypot(ex - mx, ey - my) / grid_sz) * 5
                
                # Ohut harmaa viiva
                pygame.draw.line(screen, (100, 100, 100), (mx, my), (ex, ey), 1)
                # Etäisyys vihollisen päälle
                edist_txt = fonts.small.render(f"{enemy_dist:.0f}ft", True, COLORS["text_dim"])
                screen.blit(edist_txt, (ex, ey))

        # --- UI PANEL ---
        panel_rect = pygame.Rect(grid_area_width, top_bar_h, 500, SCREEN_HEIGHT - top_bar_h)
        pygame.draw.rect(screen, (25, 27, 30), panel_rect) # Hieman tummempi tausta
        pygame.draw.line(screen, COLORS["border"], (grid_area_width, top_bar_h), (grid_area_width, SCREEN_HEIGHT), 3)

        curr = self.battle_sys.get_current_entity()
        sel = self.selected_entity if self.selected_entity else curr
        
        # Header Box
        header_rect = pygame.Rect(grid_area_width, top_bar_h, 500, 60)
        pygame.draw.rect(screen, (35, 37, 40), header_rect)
        pygame.draw.line(screen, COLORS["border"], (grid_area_width, top_bar_h + 60), (SCREEN_WIDTH, top_bar_h + 60), 1)
        
        turn_txt = fonts.header.render(f"Active: {curr.name}", True, COLORS["accent"])
        screen.blit(turn_txt, (grid_area_width + 20, top_bar_h + 15))

        # --- SELECTED ENTITY STATS ---
        stat_y = top_bar_h + 80
        sel_title = fonts.header.render(f"Selected: {sel.name}", True, sel.color)
        screen.blit(sel_title, (grid_area_width + 20, stat_y))
        
        stat_y += 35
        stats_to_show = [
            f"AC: {sel.stats.armor_class}  |  Speed: {sel.stats.speed} ft",
            f"HP: {sel.hp} / {sel.max_hp}"
        ]
            
        for line in stats_to_show:
            txt = fonts.body.render(line, True, COLORS["text_main"])
            screen.blit(txt, (grid_area_width + 20, stat_y))
            stat_y += 25

        # --- DM CONTROLS (HP) ---
        stat_y += 10
        hp_label = fonts.small.render("Modify HP:", True, COLORS["text_dim"])
        screen.blit(hp_label, (grid_area_width + 20, stat_y))
        stat_y += 25
        
        # Piirrä HP napit
        btn_x = grid_area_width + 20
        for btn in self.hp_btns:
            btn.rect.x = btn_x
            btn.rect.y = stat_y
            btn.draw(screen, pygame.mouse.get_pos())
            btn_x += 45
            
        # --- CONDITIONS ---
        stat_y += 40
        cond_label = fonts.small.render("Conditions (Hover for info):", True, COLORS["text_dim"])
        screen.blit(cond_label, (grid_area_width + 20, stat_y))
        stat_y += 25
        
        start_x = grid_area_width + 20
        col_w, row_h = 115, 25
        i = 0
        hovered_desc = None
        
        for cond, desc in CONDITIONS.items():
            col = i % 4
            row = i // 4
            rect = pygame.Rect(start_x + col * col_w, stat_y + row * row_h, 110, 22)
            
            # Onko aktiivinen?
            is_active = sel.has_condition(cond)
            bg_color = COLORS["accent"] if is_active else (50, 50, 50)
            
            # Hover check
            if rect.collidepoint(pygame.mouse.get_pos()):
                bg_color = (80, 80, 80) if not is_active else COLORS["accent_hover"]
                hovered_desc = f"{cond}: {desc}"
            
            pygame.draw.rect(screen, bg_color, rect, border_radius=4)
            txt = fonts.small.render(cond, True, COLORS["text_main"])
            screen.blit(txt, (rect.x + 5, rect.y + 5))
            i += 1
            
        # --- ROLLS ---
        stat_y += (i // 4 + 1) * 25 + 15
        roll_label = fonts.small.render("Rolls:", True, COLORS["text_dim"])
        screen.blit(roll_label, (grid_area_width + 20, stat_y))
        stat_y += 25
        
        self.btn_roll_save.rect.topleft = (grid_area_width + 20, stat_y)
        self.btn_roll_skill.rect.topleft = (grid_area_width + 140, stat_y)
        
        self.btn_roll_save.draw(screen, mouse_pos)
        self.btn_roll_skill.draw(screen, mouse_pos)

        # --- HOVER TOOLTIP ---
        if hovered_desc:
            mx, my = pygame.mouse.get_pos()
            tip_surf = fonts.small.render(hovered_desc, True, (255, 255, 255))
            tip_bg = pygame.Rect(mx + 15, my + 15, tip_surf.get_width() + 10, tip_surf.get_height() + 10)
            pygame.draw.rect(screen, (20, 20, 20), tip_bg)
            pygame.draw.rect(screen, COLORS["border"], tip_bg, 1)
            screen.blit(tip_surf, (mx + 20, my + 20))

        # Log Area
        # Lasketaan logille tilaa statusten ja nappien väliin
        log_start_y = stat_y + 45
        log_end_y = SCREEN_HEIGHT - 90 # Jätä tilaa napeille
        log_h = log_end_y - log_start_y
        
        log_title = fonts.body.render("Battle Log:", True, COLORS["text_dim"])
        screen.blit(log_title, (grid_area_width + 20, log_start_y - 25))
        
        # Log background
        log_bg = pygame.Rect(grid_area_width + 10, log_start_y, 480, log_h)
        pygame.draw.rect(screen, (15, 17, 20), log_bg, border_radius=5)
        
        # Piirrä logi alhaalta ylös
        draw_y = log_start_y + 10
        for msg in self.logs:
            if draw_y > log_end_y - 20: break
            txt = fonts.small.render(f"> {msg}", True, COLORS["text_main"])
            screen.blit(txt, (grid_area_width + 25, draw_y))
            draw_y += 20

        mouse_pos = pygame.mouse.get_pos()
        
        if self.pending_action:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0, 150))
            screen.blit(overlay, (0,0))
            
            # Isompi DM-ikkuna
            box_w, box_h = 500, 350
            box_x, box_y = SCREEN_WIDTH//2 - box_w//2, SCREEN_HEIGHT//2 - box_h//2
            
            # Header bar
            pygame.draw.rect(screen, (40, 42, 45), (box_x, box_y, box_w, 50), border_top_left_radius=10, border_top_right_radius=10)
            # Body
            pygame.draw.rect(screen, COLORS["panel"], (box_x, box_y + 50, box_w, box_h - 50), border_bottom_left_radius=10, border_bottom_right_radius=10)
            # Border
            pygame.draw.rect(screen, COLORS["border"], (box_x, box_y, box_w, box_h), 3, border_radius=10)
            
            act, target = self.pending_action, self.pending_action['target']
            
            title_text = "Action Confirmation"
            title = fonts.header.render(title_text, True, COLORS["text_main"])
            screen.blit(title, (box_x + 20, box_y + 10))
            
            y = box_y + 70
            
            # Info
            info1 = fonts.body.render(f"{act['attacker'].name} attacks {target.name}", True, COLORS["accent"])
            screen.blit(info1, (box_x + 20, y))
            y += 40
            
            # Roll
            is_hit = act['attack_roll'] >= target.stats.armor_class
            roll_color = COLORS["success"] if is_hit else COLORS["danger"]
            
            roll_lbl = fonts.body.render("Attack Roll:", True, COLORS["text_dim"])
            roll_val = fonts.header.render(str(act['attack_roll']), True, roll_color)
            
            vs_lbl = fonts.body.render("vs AC:", True, COLORS["text_dim"])
            vs_val = fonts.header.render(str(target.stats.armor_class), True, COLORS["text_main"])
            
            screen.blit(roll_lbl, (box_x + 20, y))
            screen.blit(roll_val, (box_x + 120, y - 5))
            screen.blit(vs_lbl, (box_x + 250, y))
            screen.blit(vs_val, (box_x + 310, y - 5))
            y += 50
            
            # Damage
            dmg_lbl = fonts.body.render("Damage:", True, COLORS["text_dim"])
            dmg_val = fonts.header.render(f"{act['damage']} ({act['action_name']})", True, COLORS["danger"])
            screen.blit(dmg_lbl, (box_x + 20, y))
            screen.blit(dmg_val, (box_x + 120, y - 5))
            
            self.confirm_btn.draw(screen, mouse_pos)
            self.deny_btn.draw(screen, mouse_pos)
        else:
            self.btn_next.draw(screen, mouse_pos)
            self.btn_menu.draw(screen, mouse_pos)
            
            if not curr.is_player:
                # Päivitä AI napin tila
                if curr.action_used:
                    self.btn_ai.text = "AI DONE"
                    self.btn_ai.color = COLORS["text_dim"]
                else:
                    self.btn_ai.text = "AI AUTO-PLAY"
                    self.btn_ai.color = COLORS["accent"]
                self.btn_ai.draw(screen, mouse_pos)

            # Draw Context Menu
            if self.ctx_menu_open:
                # Background
                total_h = len(self.ctx_menu_rects) * 30
                bg_rect = pygame.Rect(self.ctx_menu_pos[0], self.ctx_menu_pos[1], 160, total_h)
                pygame.draw.rect(screen, COLORS["panel"], bg_rect)
                pygame.draw.rect(screen, COLORS["border"], bg_rect, 1)
                
                for rect, _, txt in self.ctx_menu_rects:
                    # Hover effect
                    if rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, COLORS["accent"], rect)
                    
                    t_surf = fonts.small.render(txt, True, COLORS["text_main"])
                    screen.blit(t_surf, (rect.x + 10, rect.y + 5))