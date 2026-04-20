import pygame
import os
import random
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.campaign import Campaign, load_campaign, _timestamp
from states.game_state_base import GameState, ScenarioModal, CampaignPickerModal


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
            Button(cx-bw//2, start_y + (bh+gap),   bw, bh, "Campaign Manager",
                   lambda: self._open_campaign_picker(),
                   color=COLORS["legendary"]),
            Button(cx-bw//2, start_y + (bh+gap)*2, bw, bh, "Combat Roster",
                   lambda: manager.change_state("COMBAT_ROSTER"),
                   color=COLORS["success"]),
            Button(cx-bw//2, start_y + (bh+gap)*3, bw, bh, "Hero Creator",
                   lambda: manager.change_state("HERO_CREATOR"),
                   color=COLORS["player"]),
            Button(cx-bw//2, start_y + (bh+gap)*4, bw, bh, "Load Scenario",
                   lambda: self._open_load_modal(),
                   color=COLORS["panel_light"], style="outline"),
            Button(cx-bw//2, start_y + (bh+gap)*5, bw, bh, "Import from TaleSpire",
                   lambda: self._import_from_talespire(),
                   color=COLORS["accent_dim"], style="outline"),
            Button(cx-bw//2, start_y + (bh+gap)*6, bw, bh, "Exit",
                   lambda: manager.quit(),
                   color=COLORS["danger_dim"]),
        ]
        self.scenario_modal = None
        self.campaign_modal = None  # Campaign picker modal
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
            from states.battle_state import BattleState
            from engine.battle import BattleSystem
            bs = BattleState(self.manager)
            bs.battle = BattleSystem.from_save(filepath, bs._log)
            bs.battle.log = bs._log
            self.manager.states["BATTLE"] = bs
            self.manager.change_state("BATTLE")
        except Exception as ex:
            print(f"Load error: {ex}")

    # ---- Campaign Management ----

    def _open_campaign_picker(self):
        """Open campaign picker: list existing campaigns or create new one."""
        self.campaign_modal = CampaignPickerModal(self._on_campaign_selected)

    def _on_campaign_selected(self, result):
        """Called when a campaign is selected or 'new' is chosen."""
        self.campaign_modal = None
        if result is None:
            return
        from engine import variant_rules
        if result == "__new__":
            campaign = Campaign(name="New Campaign", created=_timestamp())
            variant_rules.load_from_campaign(campaign.settings)
            self.manager.change_state("CAMPAIGN", campaign=campaign)
        elif isinstance(result, str) and os.path.exists(result):
            try:
                campaign = load_campaign(result)
                variant_rules.load_from_campaign(campaign.settings)
                self.manager.change_state("CAMPAIGN", campaign=campaign)
            except Exception as ex:
                print(f"Campaign load error: {ex}")

    def handle_events(self, events):
        for e in events:
            if self.campaign_modal:
                self.campaign_modal.handle_event(e)
                continue
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
        if self.campaign_modal:
            self.campaign_modal.draw(screen, mp)
