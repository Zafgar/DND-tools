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
