import pygame
import os
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.campaign import list_campaigns, CAMPAIGNS_DIR

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
# ============================================================
# Conditions Modal: full toggle panel for all PHB conditions
# ============================================================
class ConditionsModal:
    """DM-only modal showing every PHB condition with a visible on/off state.
    Click a row to toggle. Immune conditions are shown greyed-out.
    Exhaustion is adjusted with +/-; its level sits on entity.exhaustion."""

    ORDERED_CONDITIONS = [
        "Blinded", "Charmed", "Deafened", "Frightened", "Grappled", "Incapacitated",
        "Invisible", "Paralyzed", "Petrified", "Poisoned", "Prone", "Restrained",
        "Stunned", "Unconscious",
    ]

    def __init__(self, entity, callback):
        from data.conditions import CONDITIONS
        self.entity = entity
        self.callback = callback
        self.w, self.h = 640, 560
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2
        self.conditions = CONDITIONS

        self.row_rects = []
        row_h = 28
        start_y = self.y + 60
        for i, cond in enumerate(self.ORDERED_CONDITIONS):
            self.row_rects.append((cond, pygame.Rect(self.x + 20, start_y + i * row_h, self.w - 40, row_h - 4)))

        # Exhaustion row at bottom
        exh_y = start_y + len(self.ORDERED_CONDITIONS) * row_h + 10
        self.exh_minus_rect = pygame.Rect(self.x + self.w - 180, exh_y, 32, 30)
        self.exh_plus_rect = pygame.Rect(self.x + self.w - 60, exh_y, 32, 30)
        self.exh_label_y = exh_y

        self.btn_close = Button(self.x + self.w - 120, self.y + self.h - 50, 100, 40, "CLOSE",
                                lambda: callback(True), color=COLORS["success"])

    def _is_immune(self, cond: str) -> bool:
        immune = [x.lower() for x in self.entity.stats.condition_immunities]
        return cond.lower() in immune

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.callback(True)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for cond, rect in self.row_rects:
                if rect.collidepoint(mp):
                    if self._is_immune(cond):
                        return
                    if self.entity.has_condition(cond):
                        self.entity.remove_condition(cond)
                    else:
                        self.entity.add_condition(cond)
                    return
            if self.exh_minus_rect.collidepoint(mp):
                self.entity.exhaustion = max(0, self.entity.exhaustion - 1)
                return
            if self.exh_plus_rect.collidepoint(mp):
                self.entity.exhaustion = min(6, self.entity.exhaustion + 1)
                # Level 6 exhaustion = death (PHB)
                if self.entity.exhaustion >= 6:
                    self.entity.hp = 0
                return
        self.btn_close.handle_event(event)

    def draw(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h), 2, border_radius=10)

        title = fonts.header.render(f"Conditions — {self.entity.name}", True, COLORS["accent"])
        screen.blit(title, (self.x + 20, self.y + 15))

        for cond, rect in self.row_rects:
            active = self.entity.has_condition(cond)
            immune = self._is_immune(cond)
            if immune:
                bg = (40, 40, 50)
                fg = (110, 110, 120)
                tag = "[IMMUNE]"
            elif active:
                bg = (70, 120, 70)
                fg = (240, 240, 240)
                tag = "[ON]"
            else:
                bg = (35, 35, 42)
                fg = (200, 200, 210)
                tag = ""
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            if rect.collidepoint(mp) and not immune:
                pygame.draw.rect(screen, COLORS["accent"], rect, 1, border_radius=4)
            label = fonts.body.render(cond, True, fg)
            screen.blit(label, (rect.x + 10, rect.y + 4))
            if tag:
                t = fonts.small.render(tag, True, fg)
                screen.blit(t, (rect.right - 90, rect.y + 6))

        # Exhaustion row
        lvl = self.entity.exhaustion
        exh_text = fonts.body.render(f"Exhaustion: {lvl}/6", True, COLORS["text_main"])
        screen.blit(exh_text, (self.x + 20, self.exh_label_y + 4))
        pygame.draw.rect(screen, (60, 60, 70), self.exh_minus_rect, border_radius=4)
        m = fonts.body.render("-", True, (255, 255, 255))
        screen.blit(m, (self.exh_minus_rect.x + 12, self.exh_minus_rect.y + 4))
        pygame.draw.rect(screen, (60, 60, 70), self.exh_plus_rect, border_radius=4)
        p = fonts.body.render("+", True, (255, 255, 255))
        screen.blit(p, (self.exh_plus_rect.x + 10, self.exh_plus_rect.y + 4))

        self.btn_close.draw(screen, mp)


class VariantRulesModal:
    """Toggle DMG optional rules for the active campaign. Flags are persisted
    on Campaign.settings and applied immediately via engine.variant_rules."""

    FLAGS = [
        ("flanking_advantage",        "Flanking (DMG 251)",
         "Two allies on opposite sides of a target give melee advantage."),
        ("slow_natural_healing",      "Slow Natural Healing (DMG 267)",
         "Long rest no longer restores HP; hit dice are the only recovery."),
        ("gritty_realism",            "Gritty Realism (DMG 267)",
         "Short rest = 8 hours; long rest = 7 days."),
        ("healers_kit_required",      "Healer's Kit Dependency (DMG 266)",
         "Hit dice spent on a short rest consume one use of a Healer's Kit."),
        ("cleaving_through_creatures","Cleaving Through Creatures (DMG 272)",
         "Melee kill with excess damage rolls over to an adjacent target."),
    ]

    def __init__(self, campaign, callback):
        from engine import variant_rules
        self.campaign = campaign
        self.callback = callback
        self.variant_rules = variant_rules
        self.w, self.h = 720, 480
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2

        # Make sure settings dict carries every flag so UI state stays stable.
        for key, _, _ in self.FLAGS:
            self.campaign.settings.setdefault(key, variant_rules.get(key))

        self.row_rects = []
        row_h = 60
        start_y = self.y + 60
        for i, (key, _, _) in enumerate(self.FLAGS):
            self.row_rects.append((key, pygame.Rect(self.x + 20, start_y + i * row_h,
                                                    self.w - 40, row_h - 8)))

        self.btn_close = Button(self.x + self.w - 130, self.y + self.h - 50, 110, 40,
                                "CLOSE", lambda: callback(True), color=COLORS["success"])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.callback(True)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.row_rects:
                if rect.collidepoint(event.pos):
                    cur = self.campaign.settings.get(key, False)
                    self.campaign.settings[key] = not cur
                    self.variant_rules.set_flag(key, not cur)
                    return
        self.btn_close.handle_event(event)

    def draw(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h),
                         border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h),
                         2, border_radius=10)

        title = fonts.header.render("Variant Rules", True, COLORS["accent"])
        screen.blit(title, (self.x + 20, self.y + 15))

        for key, rect in self.row_rects:
            _, label, desc = next(f for f in self.FLAGS if f[0] == key)
            on = self.campaign.settings.get(key, False)
            bg = (70, 120, 70) if on else (35, 35, 42)
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            if rect.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["accent"], rect, 1, border_radius=4)
            tag = "[ON]" if on else "[OFF]"
            name_s = fonts.body.render(f"{tag}  {label}", True,
                                       (240, 240, 240) if on else (200, 200, 210))
            screen.blit(name_s, (rect.x + 10, rect.y + 6))
            desc_s = fonts.small.render(desc, True, (180, 180, 200))
            screen.blit(desc_s, (rect.x + 10, rect.y + 30))

        self.btn_close.draw(screen, mp)


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
# Campaign Picker Modal
# ============================================================
class CampaignPickerModal:
    """Modal for selecting an existing campaign or creating a new one."""
    def __init__(self, callback):
        self.callback = callback
        self.w, self.h = 600, 500
        self.x = SCREEN_WIDTH // 2 - self.w // 2
        self.y = SCREEN_HEIGHT // 2 - self.h // 2
        self.scroll_y = 0
        self.selected_file = None

        # Load campaign list
        self.files = list_campaigns()

        self.btn_new = Button(self.x + 20, self.y + self.h - 60, 150, 45,
                              "NEW CAMPAIGN", lambda: callback("__new__"), color=COLORS["success"])
        self.btn_load = Button(self.x + self.w - 170, self.y + self.h - 60, 150, 45,
                               "LOAD", self._load, color=COLORS["accent"])
        self.btn_cancel = Button(self.x + 190, self.y + self.h - 60, 120, 45,
                                 "CANCEL", lambda: callback(None), color=COLORS["danger"])

    def _load(self):
        if self.selected_file:
            filepath = os.path.join(CAMPAIGNS_DIR, self.selected_file)
            self.callback(filepath)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.callback(None)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            list_rect = pygame.Rect(self.x + 20, self.y + 60, self.w - 40, self.h - 140)
            if list_rect.collidepoint(mx, my):
                rel_y = my - (self.y + 60) - self.scroll_y
                idx = int(rel_y // 35)
                if 0 <= idx < len(self.files):
                    self.selected_file = self.files[idx]
            if event.button == 4:
                self.scroll_y = min(0, self.scroll_y + 20)
            if event.button == 5:
                self.scroll_y = max(-(len(self.files) * 35 - (self.h - 140)), self.scroll_y - 20)

        self.btn_new.handle_event(event)
        self.btn_load.handle_event(event)
        self.btn_cancel.handle_event(event)

    def draw(self, screen, mp):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, COLORS["panel"], (self.x, self.y, self.w, self.h), border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], (self.x, self.y, self.w, self.h), 2, border_radius=10)

        t = fonts.header.render("Campaign Manager", True, COLORS["legendary"])
        screen.blit(t, (self.x + 20, self.y + 15))

        list_rect = pygame.Rect(self.x + 20, self.y + 60, self.w - 40, self.h - 140)
        pygame.draw.rect(screen, (20, 22, 25), list_rect)
        pygame.draw.rect(screen, COLORS["border"], list_rect, 1)

        if not self.files:
            hint = fonts.body.render("No campaigns yet. Click 'New Campaign' to start.", True, COLORS["text_dim"])
            screen.blit(hint, (self.x + 40, self.y + 100))
        else:
            screen.set_clip(list_rect)
            fy = self.y + 60 + self.scroll_y
            for f in self.files:
                col = COLORS["text_main"]
                if f == self.selected_file:
                    pygame.draw.rect(screen, COLORS["accent"], (self.x + 22, fy, self.w - 44, 32))
                    col = (255, 255, 255)
                name = f.replace(".json", "")
                txt = fonts.body.render(name, True, col)
                screen.blit(txt, (self.x + 30, fy + 5))
                fy += 35
            screen.set_clip(None)

        self.btn_new.draw(screen, mp)
        self.btn_load.draw(screen, mp)
        self.btn_cancel.draw(screen, mp)
