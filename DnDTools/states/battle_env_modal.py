"""Battle Environment modal — in-battle settings for:

  * JPG/PNG map background (path, alpha, cells_w/h, offsets)
  * Indoor ceiling (feet, limits flyer altitude)

Opens via the "ENV" button in battle_state. Self-contained events and
drawing while ``is_open`` — BattleState intercepts events accordingly.
"""
import logging
import os

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect


class BattleEnvironmentModal:
    WIDTH = 620
    HEIGHT = 460

    CEILING_PRESETS = (0, 8, 10, 12, 15, 20, 25)

    def __init__(self, battle, log_callback=None):
        """``battle`` is the live BattleSystem. ``log_callback`` is the
        battle log sink (defaults to a no-op)."""
        self.battle = battle
        self.log = log_callback or (lambda *a: None)
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        # Background buttons
        self.btn_load_bg = Button(
            self.x + 20, self.y + 80, 170, 35,
            "Load image...", self._load_bg, color=COLORS["success"],
        )
        self.btn_clear_bg = Button(
            self.x + 200, self.y + 80, 110, 35,
            "Clear", self._clear_bg, color=COLORS["danger"],
        )

        # Alpha steppers
        self.btn_alpha_down = Button(
            self.x + 20, self.y + 135, 45, 30, "-",
            lambda: self._nudge_alpha(-25), color=COLORS["panel"],
        )
        self.btn_alpha_up = Button(
            self.x + 200, self.y + 135, 45, 30, "+",
            lambda: self._nudge_alpha(+25), color=COLORS["panel"],
        )

        # Cells steppers
        self.btn_w_down = Button(
            self.x + 20, self.y + 185, 45, 30, "-",
            lambda: self._nudge_cells(dw=-5), color=COLORS["panel"],
        )
        self.btn_w_up = Button(
            self.x + 200, self.y + 185, 45, 30, "+",
            lambda: self._nudge_cells(dw=+5), color=COLORS["panel"],
        )
        self.btn_h_down = Button(
            self.x + 300, self.y + 185, 45, 30, "-",
            lambda: self._nudge_cells(dh=-5), color=COLORS["panel"],
        )
        self.btn_h_up = Button(
            self.x + 480, self.y + 185, 45, 30, "+",
            lambda: self._nudge_cells(dh=+5), color=COLORS["panel"],
        )

        # Ceiling preset buttons
        self.ceiling_btns = []
        for i, ft in enumerate(self.CEILING_PRESETS):
            label = "Open sky" if ft == 0 else f"{ft} ft"
            bx = self.x + 20 + i * 80
            self.ceiling_btns.append(Button(
                bx, self.y + 290, 72, 35, label,
                lambda f=ft: self._set_ceiling(f),
                color=COLORS["panel"],
            ))

        # Close button
        self.btn_close = Button(
            self.x + self.WIDTH - 115, self.y + self.HEIGHT - 55,
            95, 40, "Close", self.close, color=COLORS["panel"],
        )

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def _pick_file(self) -> str:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Select battle-map background",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                    ("All files", "*.*"),
                ],
            )
            root.destroy()
            return path or ""
        except Exception as ex:
            logging.warning(f"[BG] File picker unavailable: {ex}")
            return ""

    def _load_bg(self):
        path = self._pick_file()
        if not path:
            return
        ok = self.battle.set_background_image(path)
        if ok:
            self.log(f"[BG] Loaded: {os.path.basename(path)}")
        else:
            self.log(f"[BG] Failed to load: {path}")

    def _clear_bg(self):
        if not self.battle.background_image_path:
            return
        self.battle.set_background_image("")
        self.log("[BG] Background cleared.")

    def _nudge_alpha(self, delta):
        new_a = max(0, min(255, int(self.battle.background_alpha) + delta))
        self.battle.background_alpha = new_a

    def _nudge_cells(self, dw=0, dh=0):
        self.battle.background_world_cells_w = max(
            1, self.battle.background_world_cells_w + dw
        )
        self.battle.background_world_cells_h = max(
            1, self.battle.background_world_cells_h + dh
        )

    def _set_ceiling(self, ft: int):
        self.battle.ceiling_ft = max(0, int(ft))
        # Immediately clamp any flyers that would now be above the cap
        if ft > 0:
            for ent in self.battle.entities:
                self.battle.clamp_fly_altitude(ent)
        self.log(
            f"[ENV] Ceiling set to {'open sky' if ft == 0 else f'{ft} ft'}."
        )

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        for b in (self.btn_load_bg, self.btn_clear_bg,
                   self.btn_alpha_down, self.btn_alpha_up,
                   self.btn_w_down, self.btn_w_up,
                   self.btn_h_down, self.btn_h_up,
                   self.btn_close, *self.ceiling_btns):
            b.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        return True

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        draw_gradient_rect(screen, rect,
                           COLORS["bg_dark"], COLORS["bg"], border_radius=10)
        pygame.draw.rect(screen, COLORS["border_light"], rect, 2, border_radius=10)

        # Title
        t = fonts.header.render("Battle Environment", True, COLORS["accent"])
        screen.blit(t, (self.x + 20, self.y + 15))

        # --- Background section ---
        self._label(screen, "Map background", self.x + 20, self.y + 55)
        self.btn_load_bg.draw(screen, mp)
        self.btn_clear_bg.draw(screen, mp)

        # Current path
        path = self.battle.background_image_path
        if path:
            txt = fonts.tiny.render(os.path.basename(path),
                                    True, COLORS["text_dim"])
            screen.blit(txt, (self.x + 330, self.y + 90))
        else:
            txt = fonts.tiny.render("(none)", True, COLORS["text_dim"])
            screen.blit(txt, (self.x + 330, self.y + 90))

        # Alpha row
        self.btn_alpha_down.draw(screen, mp)
        self.btn_alpha_up.draw(screen, mp)
        alpha_lbl = fonts.small.render(
            f"Opacity: {self.battle.background_alpha}/255",
            True, COLORS["text"],
        )
        screen.blit(alpha_lbl, (self.x + 70, self.y + 140))

        # Cells w / h
        self.btn_w_down.draw(screen, mp)
        self.btn_w_up.draw(screen, mp)
        w_lbl = fonts.small.render(
            f"Width: {self.battle.background_world_cells_w} cells",
            True, COLORS["text"],
        )
        screen.blit(w_lbl, (self.x + 70, self.y + 190))

        self.btn_h_down.draw(screen, mp)
        self.btn_h_up.draw(screen, mp)
        h_lbl = fonts.small.render(
            f"Height: {self.battle.background_world_cells_h} cells",
            True, COLORS["text"],
        )
        screen.blit(h_lbl, (self.x + 350, self.y + 190))

        # --- Ceiling section ---
        pygame.draw.line(screen, COLORS["border"],
                         (self.x + 20, self.y + 245),
                         (self.x + self.WIDTH - 20, self.y + 245), 1)
        self._label(screen, "Indoor ceiling (caps flyer altitude)",
                     self.x + 20, self.y + 260)
        for btn, ft in zip(self.ceiling_btns, self.CEILING_PRESETS):
            if self.battle.ceiling_ft == ft:
                btn.color = COLORS["accent"]
            else:
                btn.color = COLORS["panel"]
            btn.draw(screen, mp)

        current_ft = self.battle.ceiling_ft
        cur = ("No ceiling (outdoor)" if current_ft == 0
               else f"Currently {current_ft} ft — max flying altitude "
                    f"{self.battle.max_fly_altitude()} ft")
        cur_surf = fonts.tiny.render(cur, True, COLORS["text_dim"])
        screen.blit(cur_surf, (self.x + 20, self.y + 340))

        # Hint text
        hint = ("Tip: walls / trees now block line-of-sight in 3D; a wall "
                "10 ft tall won't hide a flier 15 ft up.")
        self._blit_wrapped(screen, hint, self.x + 20, self.y + 370,
                            self.WIDTH - 40, fonts.tiny, COLORS["text_dim"])

        self.btn_close.draw(screen, mp)

    def _label(self, screen, txt, x, y):
        s = fonts.body_bold.render(txt, True, COLORS["text"])
        screen.blit(s, (x, y))

    @staticmethod
    def _blit_wrapped(screen, text, x, y, max_w, font, color):
        words = text.split()
        line = ""
        for w in words:
            cand = (line + " " + w).strip()
            if font.size(cand)[0] > max_w:
                screen.blit(font.render(line, True, color), (x, y))
                y += font.get_height() + 2
                line = w
            else:
                line = cand
        if line:
            screen.blit(font.render(line, True, color), (x, y))
