"""
Combat Roster State
Directory-style hero browser with multi-team combat setup.
Select heroes from the roster, assign team colors, and launch battle.
"""
import pygame
import os
import copy
from settings import (COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, TEAM_COLORS, TEAM_NAMES)
from ui.components import Button, Panel, fonts, Badge, Divider, draw_gradient_rect
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores
from data.heroes import hero_list
from data.hero_import import import_heroes_from_file
from data.library import library


class CombatRosterState:
    """Combat Roster: browse heroes directory-style, assign teams, start multi-team battle."""

    def __init__(self, manager):
        self.manager = manager

        # Combat roster: list of (Entity, team_name)
        self.roster = []

        # Directory browsing
        self.search_text = ""
        self.search_active = False
        self.hero_scroll = 0
        self.monster_scroll = 0
        self.roster_scroll = 0

        # Filter mode for hero list
        self.filter_mode = "heroes"  # "heroes", "monsters", "all"
        self.selected_cr = None

        # Monster CR data
        all_monsters = library.get_all_monsters()
        self.monsters_by_cr = {}
        for m in all_monsters:
            cr = m.challenge_rating
            self.monsters_by_cr.setdefault(cr, []).append(m)
        self.sorted_crs = sorted(self.monsters_by_cr.keys())
        self.active_monster_list = []

        # Current team for adding
        self.current_team_idx = 0
        self.current_team = TEAM_NAMES[0]

        # Load saved heroes from disk
        self._load_disk_heroes()

        # Status
        self.status_message = ""
        self.status_timer = 0
        self.status_color = COLORS["success"]

        # UI Buttons
        self._build_buttons()

    def _load_disk_heroes(self):
        """Load heroes from heroes/ directory into hero_list if not already there."""
        heroes_dir = os.path.join(os.path.dirname(__file__), "..", "heroes")
        if not os.path.exists(heroes_dir):
            return
        for f in sorted(os.listdir(heroes_dir)):
            if f.endswith(".json"):
                try:
                    heroes = import_heroes_from_file(os.path.join(heroes_dir, f))
                    for h in heroes:
                        if not any(existing.name == h.name for existing in hero_list):
                            hero_list.append(h)
                except Exception:
                    pass

    def _build_buttons(self):
        # Tab buttons for filter
        self.btn_heroes = Button(30, 70, 120, 35, "HEROES",
                                 lambda: self._set_filter("heroes"),
                                 color=COLORS["player"])
        self.btn_monsters = Button(160, 70, 120, 35, "MONSTERS",
                                   lambda: self._set_filter("monsters"),
                                   color=COLORS["enemy"])

        # Team selector buttons
        self.team_buttons = []
        tx = SCREEN_WIDTH - 420
        for i, name in enumerate(TEAM_NAMES):
            tc = TEAM_COLORS[name]["color"]
            self.team_buttons.append(
                Button(tx + i * 100, 70, 90, 35, name,
                       lambda n=name, idx=i: self._set_team(n, idx),
                       color=tc)
            )

        # Action buttons
        self.btn_start = Button(
            SCREEN_WIDTH - 250, SCREEN_HEIGHT - 80, 220, 55, "START BATTLE",
            self._start_battle, color=COLORS["success"]
        )
        self.btn_clear = Button(
            SCREEN_WIDTH - 250, SCREEN_HEIGHT - 145, 220, 45, "Clear Roster",
            lambda: self.roster.clear(), color=COLORS["danger"]
        )
        self.btn_back = Button(
            30, SCREEN_HEIGHT - 70, 160, 45, "< BACK",
            lambda: self.manager.change_state("MENU"),
            color=COLORS["panel"]
        )

        # CR buttons for monster browsing
        self.cr_btns = []

    def _set_filter(self, mode):
        self.filter_mode = mode
        self.hero_scroll = 0
        self.monster_scroll = 0

    def _set_team(self, name, idx):
        self.current_team_idx = idx
        self.current_team = name

    def _get_filtered_heroes(self):
        """Get heroes matching current filter/search."""
        heroes = list(hero_list)
        if self.search_text:
            query = self.search_text.lower()
            heroes = [h for h in heroes if query in h.name.lower() or
                      query in (h.character_class or "").lower() or
                      query in (h.race or "").lower()]
        return heroes

    def _get_filtered_monsters(self):
        """Get monsters matching current filter/search."""
        if self.search_text:
            query = self.search_text.lower()
            all_mons = library.get_all_monsters()
            return [m for m in all_mons if query in m.name.lower()]
        elif self.selected_cr is not None:
            return self.monsters_by_cr.get(self.selected_cr, [])
        return []

    def _add_to_roster(self, stats, is_player=True):
        """Add a character/monster to the combat roster."""
        stats_copy = copy.deepcopy(stats)
        # Numbered duplicates
        base_name = stats.name
        same = sum(1 for e, _ in self.roster if e.name.startswith(base_name))
        if same > 0:
            stats_copy.name = f"{base_name} {same + 1}"

        # Position
        count = len(self.roster)
        x = 3 + (count % 5) * 2
        y = 2 + (count // 5) * 2
        ent = Entity(stats_copy, x, y, is_player=is_player)
        ent.team = self.current_team

        # Set color based on team
        tc = TEAM_COLORS.get(self.current_team, TEAM_COLORS["Blue"])
        ent.color = tc["color"]

        self.roster.append((ent, self.current_team))

    def _remove_from_roster(self, idx):
        """Remove entity from roster by index."""
        if 0 <= idx < len(self.roster):
            self.roster.pop(idx)

    def _cycle_entity_team(self, idx):
        """Cycle team of an existing roster entry."""
        if 0 <= idx < len(self.roster):
            ent, old_team = self.roster[idx]
            old_idx = TEAM_NAMES.index(old_team) if old_team in TEAM_NAMES else 0
            new_idx = (old_idx + 1) % len(TEAM_NAMES)
            new_team = TEAM_NAMES[new_idx]
            ent.team = new_team
            tc = TEAM_COLORS.get(new_team, TEAM_COLORS["Blue"])
            ent.color = tc["color"]
            self.roster[idx] = (ent, new_team)

    def _start_battle(self):
        if not self.roster:
            self.status_message = "Add heroes/monsters to roster first!"
            self.status_timer = 120
            self.status_color = COLORS["warning"]
            return

        # Determine is_player based on team (first team = players, rest = enemies)
        # Actually for multi-team, we need to set is_player for entities
        # Use team to determine allies/enemies in battle
        teams_present = set(team for _, team in self.roster)

        entities = []
        for ent, team in self.roster:
            # First team alphabetically is "players" for the purpose of the battle system
            ent.is_player = (team == sorted(teams_present)[0])
            entities.append(ent)

        from states.game_states import BattleState
        bs = BattleState(self.manager, entities)
        self.manager.states["BATTLE"] = bs
        self.manager.change_state("BATTLE")

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                return

            # Search box
            search_rect = pygame.Rect(300, 73, 300, 30)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if search_rect.collidepoint(event.pos):
                    self.search_active = True
                else:
                    self.search_active = False

            if event.type == pygame.KEYDOWN and self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.search_active = False
                    self.search_text = ""
                elif event.unicode.isprintable() and len(self.search_text) < 40:
                    self.search_text += event.unicode

            # Scrolling
            if event.type == pygame.MOUSEWHEEL:
                if mouse_pos[0] < 620:
                    # Left panel scroll
                    if self.filter_mode == "heroes":
                        self.hero_scroll = min(0, self.hero_scroll + event.y * 30)
                    else:
                        self.monster_scroll = min(0, self.monster_scroll + event.y * 30)
                elif mouse_pos[0] >= 640:
                    # Right panel scroll (roster)
                    self.roster_scroll = min(0, self.roster_scroll + event.y * 30)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if mouse_pos[0] < 620:
                        if self.filter_mode == "heroes":
                            self.hero_scroll = min(0, self.hero_scroll + 30)
                        else:
                            self.monster_scroll = min(0, self.monster_scroll + 30)
                    else:
                        self.roster_scroll = min(0, self.roster_scroll + 30)
                elif event.button == 5:
                    if mouse_pos[0] < 620:
                        if self.filter_mode == "heroes":
                            self.hero_scroll -= 30
                        else:
                            self.monster_scroll -= 30
                    else:
                        self.roster_scroll -= 30

            # Handle clicks on hero/monster list items
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_list_click(mouse_pos)
                self._handle_roster_click(mouse_pos)

            # Button handlers
            self.btn_heroes.handle_event(event)
            self.btn_monsters.handle_event(event)
            self.btn_start.handle_event(event)
            self.btn_clear.handle_event(event)
            self.btn_back.handle_event(event)
            for b in self.team_buttons:
                b.handle_event(event)

            # CR buttons
            if self.filter_mode == "monsters":
                for cr, btn_rect in self._get_cr_btn_rects():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_rect.collidepoint(event.pos):
                            self.selected_cr = cr
                            self.monster_scroll = 0

    def _get_cr_btn_rects(self):
        """Get clickable CR button rects for monster browsing."""
        rects = []
        y = 130
        for cr in self.sorted_crs:
            rects.append((cr, pygame.Rect(30, y + self.monster_scroll, 90, 28)))
            y += 32
        return rects

    def _handle_list_click(self, pos):
        """Handle click on the hero/monster directory list."""
        list_x = 30 if self.filter_mode == "heroes" else 130
        list_w = 570 if self.filter_mode == "heroes" else 470
        list_y_start = 120
        item_h = 44

        if pos[0] < list_x or pos[0] > list_x + list_w:
            return
        if pos[1] < list_y_start or pos[1] > SCREEN_HEIGHT - 100:
            return

        if self.filter_mode == "heroes":
            heroes = self._get_filtered_heroes()
            scroll = self.hero_scroll
            rel_y = pos[1] - list_y_start - scroll
            idx = int(rel_y // item_h)
            if 0 <= idx < len(heroes):
                self._add_to_roster(heroes[idx], is_player=True)
        else:
            monsters = self._get_filtered_monsters()
            scroll = self.monster_scroll
            rel_y = pos[1] - list_y_start - scroll
            idx = int(rel_y // item_h)
            if 0 <= idx < len(monsters):
                self._add_to_roster(monsters[idx], is_player=False)

    def _handle_roster_click(self, pos):
        """Handle click on roster panel items (right side)."""
        roster_x = 640
        roster_w = SCREEN_WIDTH - roster_x - 30
        list_y_start = 120
        item_h = 48

        if pos[0] < roster_x or pos[0] > roster_x + roster_w:
            return
        if pos[1] < list_y_start or pos[1] > SCREEN_HEIGHT - 100:
            return

        rel_y = pos[1] - list_y_start - self.roster_scroll
        idx = int(rel_y // item_h)
        if 0 <= idx < len(self.roster):
            # Right side = remove button area
            remove_x = roster_x + roster_w - 35
            team_cycle_x = roster_x + roster_w - 80
            if pos[0] >= remove_x:
                self._remove_from_roster(idx)
            elif pos[0] >= team_cycle_x:
                self._cycle_entity_team(idx)

    def update(self):
        if self.status_timer > 0:
            self.status_timer -= 1

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()

        # Background
        screen.fill(COLORS["bg"])

        # Title bar
        draw_gradient_rect(screen, (0, 0, SCREEN_WIDTH, 60),
                           COLORS["panel_header"], COLORS["panel_dark"])
        title_surf = fonts.title_font.render("COMBAT ROSTER", True, COLORS["text_bright"])
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 8))

        # Filter tabs
        self.btn_heroes.draw(screen, mouse_pos)
        self.btn_monsters.draw(screen, mouse_pos)

        # Active filter indicator
        if self.filter_mode == "heroes":
            pygame.draw.rect(screen, COLORS["player"], (30, 107, 120, 3))
        else:
            pygame.draw.rect(screen, COLORS["enemy"], (160, 107, 120, 3))

        # Search box
        search_rect = pygame.Rect(300, 73, 300, 30)
        col = COLORS["accent"] if self.search_active else COLORS["border"]
        pygame.draw.rect(screen, COLORS["input_bg"], search_rect, border_radius=5)
        pygame.draw.rect(screen, col, search_rect, 1 if not self.search_active else 2,
                         border_radius=5)
        if self.search_text:
            st = fonts.body_font.render(self.search_text, True, COLORS["text_main"])
            screen.blit(st, (search_rect.x + 8, search_rect.y + 5))
        else:
            ph = fonts.body_font.render("Search heroes & monsters...", True, COLORS["text_muted"])
            screen.blit(ph, (search_rect.x + 8, search_rect.y + 5))

        # Team selector
        team_label = fonts.small_bold.render("ASSIGN TEAM:", True, COLORS["text_dim"])
        screen.blit(team_label, (SCREEN_WIDTH - 430, 55))
        for i, btn in enumerate(self.team_buttons):
            btn.draw(screen, mouse_pos)
            if i == self.current_team_idx:
                pygame.draw.rect(screen, COLORS["text_bright"],
                                 btn.rect.inflate(4, 4), 2, border_radius=6)

        # Left panel: hero/monster directory
        self._draw_directory_panel(screen, mouse_pos)

        # Right panel: roster
        self._draw_roster_panel(screen, mouse_pos)

        # Team summary
        self._draw_team_summary(screen)

        # Action buttons
        self.btn_start.draw(screen, mouse_pos)
        self.btn_clear.draw(screen, mouse_pos)
        self.btn_back.draw(screen, mouse_pos)

        # Status message
        if self.status_timer > 0:
            alpha = min(255, self.status_timer * 4)
            msg_surf = fonts.body_bold.render(self.status_message, True, self.status_color)
            bar_y = SCREEN_HEIGHT // 2 - 20
            overlay = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
            overlay.fill((*COLORS["panel_dark"], min(220, alpha)))
            screen.blit(overlay, (0, bar_y))
            screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, bar_y + 8))

    def _draw_directory_panel(self, screen, mouse_pos):
        """Draw the left directory panel (heroes or monsters)."""
        panel_x = 20
        panel_w = 600
        panel_y = 115
        panel_h = SCREEN_HEIGHT - panel_y - 90

        panel = Panel(panel_x, panel_y, panel_w, panel_h,
                      title="HERO DIRECTORY" if self.filter_mode == "heroes" else "MONSTER DIRECTORY")
        panel.draw(screen)

        clip_rect = pygame.Rect(panel_x + 2, panel_y + 30, panel_w - 4, panel_h - 35)
        screen.set_clip(clip_rect)

        if self.filter_mode == "heroes":
            self._draw_hero_directory(screen, mouse_pos, panel_x, panel_y + 32, panel_w)
        else:
            self._draw_monster_directory(screen, mouse_pos, panel_x, panel_y + 32, panel_w)

        screen.set_clip(None)

    def _draw_hero_directory(self, screen, mouse_pos, px, py, pw):
        """Draw scrollable hero list."""
        heroes = self._get_filtered_heroes()
        item_h = 44
        y = py + self.hero_scroll

        if not heroes:
            no_heroes = fonts.body_font.render("No heroes found. Create some in Hero Creator!",
                                               True, COLORS["text_muted"])
            screen.blit(no_heroes, (px + 20, py + 20))
            return

        for i, hero in enumerate(heroes):
            iy = y + i * item_h
            if iy + item_h < py - 10 or iy > SCREEN_HEIGHT:
                continue

            item_rect = pygame.Rect(px + 8, iy, pw - 16, item_h - 4)
            is_hover = item_rect.collidepoint(mouse_pos)

            # Background
            bg_col = COLORS["hover"] if is_hover else (
                COLORS["panel_light"] if i % 2 == 0 else COLORS["panel_dark"])
            pygame.draw.rect(screen, bg_col, item_rect, border_radius=4)

            # Class color bar
            class_key = (hero.character_class or "Fighter").lower()
            class_col = COLORS.get(class_key, COLORS["accent"])
            pygame.draw.rect(screen, class_col, (px + 8, iy, 4, item_h - 4), border_radius=2)

            # Name
            name_surf = fonts.body_bold.render(hero.name, True, COLORS["text_bright"])
            screen.blit(name_surf, (px + 20, iy + 4))

            # Class/Race/Level info
            info_parts = []
            if hero.race:
                info_parts.append(hero.race)
            if hero.character_class:
                info_parts.append(hero.character_class)
                if hero.subclass:
                    info_parts[-1] += f" ({hero.subclass})"
            if hero.character_level:
                info_parts.append(f"Lv.{hero.character_level}")
            info_txt = " | ".join(info_parts)
            info_surf = fonts.small_font.render(info_txt, True, COLORS["text_dim"])
            screen.blit(info_surf, (px + 20, iy + 23))

            # HP/AC on right
            hp_txt = f"HP:{hero.hit_points}"
            ac_txt = f"AC:{hero.armor_class}"
            hp_surf = fonts.small_bold.render(hp_txt, True, COLORS["hp_full"])
            ac_surf = fonts.small_bold.render(ac_txt, True, COLORS["accent"])
            screen.blit(hp_surf, (px + pw - 130, iy + 6))
            screen.blit(ac_surf, (px + pw - 65, iy + 6))

            # Add indicator
            if is_hover:
                add_txt = fonts.small_bold.render("+ ADD", True, COLORS["success"])
                screen.blit(add_txt, (px + pw - 65, iy + 25))

    def _draw_monster_directory(self, screen, mouse_pos, px, py, pw):
        """Draw monster directory with CR sidebar."""
        # CR sidebar
        cr_x = px + 5
        cr_w = 85
        cr_y = py
        for cr in self.sorted_crs:
            if cr_y + 28 > SCREEN_HEIGHT - 100:
                break
            cr_rect = pygame.Rect(cr_x, cr_y, cr_w, 26)
            is_sel = cr == self.selected_cr
            is_hover = cr_rect.collidepoint(mouse_pos)

            if is_sel:
                pygame.draw.rect(screen, COLORS["accent_dim"], cr_rect, border_radius=4)
                pygame.draw.rect(screen, COLORS["accent"], cr_rect, 1, border_radius=4)
            elif is_hover:
                pygame.draw.rect(screen, COLORS["hover"], cr_rect, border_radius=4)

            label = f"CR {cr:.3g}" if cr % 1 != 0 else f"CR {int(cr)}"
            col = COLORS["text_bright"] if is_sel else COLORS["text_dim"]
            cs = fonts.small_font.render(label, True, col)
            screen.blit(cs, (cr_x + 8, cr_y + 4))
            cr_y += 30

        # Monster list
        monsters = self._get_filtered_monsters()
        list_x = px + cr_w + 15
        list_w = pw - cr_w - 25
        item_h = 44
        y = py + self.monster_scroll

        for i, mon in enumerate(monsters):
            iy = y + i * item_h
            if iy + item_h < py - 10 or iy > SCREEN_HEIGHT:
                continue

            item_rect = pygame.Rect(list_x, iy, list_w, item_h - 4)
            is_hover = item_rect.collidepoint(mouse_pos)

            bg_col = COLORS["hover"] if is_hover else (
                COLORS["panel_light"] if i % 2 == 0 else COLORS["panel_dark"])
            pygame.draw.rect(screen, bg_col, item_rect, border_radius=4)

            # Red indicator
            pygame.draw.rect(screen, COLORS["enemy"], (list_x, iy, 4, item_h - 4), border_radius=2)

            # Name
            name_surf = fonts.body_bold.render(mon.name, True, COLORS["text_bright"])
            screen.blit(name_surf, (list_x + 12, iy + 4))

            # Type and CR
            cr_label = f"CR {mon.challenge_rating:.3g}" if mon.challenge_rating % 1 != 0 else f"CR {int(mon.challenge_rating)}"
            info = f"{mon.creature_type} | {cr_label}"
            info_surf = fonts.small_font.render(info, True, COLORS["text_dim"])
            screen.blit(info_surf, (list_x + 12, iy + 23))

            # HP/AC
            hp_surf = fonts.small_bold.render(f"HP:{mon.hit_points}", True, COLORS["hp_full"])
            ac_surf = fonts.small_bold.render(f"AC:{mon.armor_class}", True, COLORS["accent"])
            screen.blit(hp_surf, (list_x + list_w - 130, iy + 6))
            screen.blit(ac_surf, (list_x + list_w - 65, iy + 6))

            if is_hover:
                add_txt = fonts.small_bold.render("+ ADD", True, COLORS["success"])
                screen.blit(add_txt, (list_x + list_w - 65, iy + 25))

    def _draw_roster_panel(self, screen, mouse_pos):
        """Draw the right roster panel showing selected combatants."""
        panel_x = 640
        panel_w = SCREEN_WIDTH - panel_x - 270
        panel_y = 115
        panel_h = SCREEN_HEIGHT - panel_y - 90

        panel = Panel(panel_x, panel_y, panel_w, panel_h,
                      title=f"BATTLE ROSTER ({len(self.roster)} combatants)")
        panel.draw(screen)

        clip_rect = pygame.Rect(panel_x + 2, panel_y + 30, panel_w - 4, panel_h - 35)
        screen.set_clip(clip_rect)

        item_h = 48
        y = panel_y + 32 + self.roster_scroll

        if not self.roster:
            empty_txt = fonts.body_font.render("Click heroes/monsters to add them here",
                                               True, COLORS["text_muted"])
            screen.blit(empty_txt, (panel_x + 20, panel_y + 50))
            screen.set_clip(None)
            return

        for i, (ent, team) in enumerate(self.roster):
            iy = y + i * item_h
            if iy + item_h < panel_y + 25 or iy > SCREEN_HEIGHT:
                continue

            item_rect = pygame.Rect(panel_x + 8, iy, panel_w - 16, item_h - 4)
            tc = TEAM_COLORS.get(team, TEAM_COLORS["Blue"])

            # Background with team tint
            bg = (tc["dim"][0] // 2, tc["dim"][1] // 2, tc["dim"][2] // 2)
            pygame.draw.rect(screen, bg, item_rect, border_radius=4)
            pygame.draw.rect(screen, tc["color"], item_rect, 1, border_radius=4)

            # Team color bar
            pygame.draw.rect(screen, tc["color"], (panel_x + 8, iy, 5, item_h - 4),
                             border_radius=2)

            # Name
            name_surf = fonts.body_bold.render(ent.name, True, COLORS["text_bright"])
            screen.blit(name_surf, (panel_x + 20, iy + 4))

            # Stats info
            info_parts = []
            if ent.stats.character_class:
                info_parts.append(f"Lv.{ent.stats.character_level} {ent.stats.character_class}")
            else:
                cr = ent.stats.challenge_rating
                cr_str = f"CR {cr:.3g}" if cr % 1 != 0 else f"CR {int(cr)}"
                info_parts.append(cr_str)
            info_parts.append(f"HP:{ent.max_hp}")
            info_parts.append(f"AC:{ent.stats.armor_class}")
            info_txt = " | ".join(info_parts)
            info_surf = fonts.small_font.render(info_txt, True, COLORS["text_dim"])
            screen.blit(info_surf, (panel_x + 20, iy + 25))

            # Team badge
            team_badge_x = panel_x + panel_w - 85
            Badge.draw(screen, team_badge_x, iy + 4, team, tc["color"], font=fonts.small_bold)

            # Remove button (X)
            remove_rect = pygame.Rect(panel_x + panel_w - 35, iy + 10, 24, 24)
            remove_hover = remove_rect.collidepoint(mouse_pos)
            remove_col = COLORS["danger_hover"] if remove_hover else COLORS["danger_dim"]
            pygame.draw.rect(screen, remove_col, remove_rect, border_radius=4)
            x_surf = fonts.body_bold.render("X", True, COLORS["text_bright"])
            screen.blit(x_surf, (remove_rect.centerx - x_surf.get_width() // 2,
                                 remove_rect.centery - x_surf.get_height() // 2))

        screen.set_clip(None)

        # Scrollbar
        total_h = len(self.roster) * item_h
        visible_h = panel_h - 35
        if total_h > visible_h:
            sb_h = max(20, int(visible_h * visible_h / total_h))
            max_scroll = total_h - visible_h
            scroll_pct = abs(self.roster_scroll) / max_scroll if max_scroll > 0 else 0
            sb_y = panel_y + 32 + int((visible_h - sb_h) * scroll_pct)
            sb_rect = pygame.Rect(panel_x + panel_w - 10, sb_y, 6, sb_h)
            pygame.draw.rect(screen, COLORS["scrollbar_thumb"], sb_rect, border_radius=3)

    def _draw_team_summary(self, screen):
        """Draw team composition summary on the right side."""
        summary_x = SCREEN_WIDTH - 250
        summary_y = 120
        summary_w = 220

        panel = Panel(summary_x, summary_y, summary_w, 260, title="TEAMS")
        panel.draw(screen)

        ty = summary_y + 35
        for team_name in TEAM_NAMES:
            tc = TEAM_COLORS[team_name]
            count = sum(1 for _, t in self.roster if t == team_name)

            if count == 0:
                col = COLORS["text_muted"]
            else:
                col = tc["color"]

            # Team color dot
            pygame.draw.circle(screen, col, (summary_x + 18, ty + 9), 6)
            if self.current_team == team_name:
                pygame.draw.circle(screen, COLORS["text_bright"],
                                   (summary_x + 18, ty + 9), 8, 2)

            # Team name and count
            team_txt = f"{team_name}: {count} combatants"
            ts = fonts.body_font.render(team_txt, True, col)
            screen.blit(ts, (summary_x + 30, ty))

            # Total HP
            if count > 0:
                total_hp = sum(ent.max_hp for ent, t in self.roster if t == team_name)
                hp_txt = f"Total HP: {total_hp}"
                hs = fonts.small_font.render(hp_txt, True, COLORS["text_dim"])
                screen.blit(hs, (summary_x + 30, ty + 20))

            ty += 50

        # Total count
        Divider.draw(screen, summary_x + 10, ty, summary_w - 20)
        ty += 8
        total_txt = f"Total: {len(self.roster)} combatants"
        tt = fonts.body_bold.render(total_txt, True, COLORS["text_main"])
        screen.blit(tt, (summary_x + 15, ty))
