"""Party picker modal — lataa sijaintipohjainen pelaajaryhmä kentälle.

Kampanjan hahmot eivät aina ole yhdessä, joten pelinjohtaja voi valita
esim. "Aterterra — Velve Dro" tai "Ravenstone — Padak" ja saada juuri
sen porukan roosteriin yhdellä klikkauksella. Itsenäinen mini-state
kuten ScenarioPickerModal: ``open_party_picker`` avaa, modaali hoitaa
omat eventtinsä/piirtonsa kun ``is_open``.
"""
import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect
from data import party_presets


class PartyPickerModal:
    WIDTH = 860
    HEIGHT = 560

    def __init__(self, on_load):
        """``on_load(preset)`` is called when the DM confirms a pick."""
        self.is_open = False
        self.on_load = on_load
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2

        self.selected = None
        self.scroll = 0

        self.btn_load = Button(
            self.x + self.WIDTH - 240, self.y + self.HEIGHT - 55,
            110, 40, "Lataa", self._confirm_load, color=COLORS["success"],
        )
        self.btn_close = Button(
            self.x + self.WIDTH - 125, self.y + self.HEIGHT - 55,
            110, 40, "Peruuta", self.close, color=COLORS["panel"],
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.selected = None
        self.scroll = 0

    def close(self):
        self.is_open = False

    # ------------------------------------------------------------------ #
    # Selection
    # ------------------------------------------------------------------ #
    def _confirm_load(self):
        if self.selected is None:
            return
        self.on_load(self.selected)
        self.close()

    def _presets(self):
        return party_presets.list_presets()

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event):
        if not self.is_open:
            return False
        self.btn_load.handle_event(event)
        self.btn_close.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            list_x = self.x + 15
            list_y = self.y + 60
            list_w = 360
            row_h = 62
            if list_x <= mx <= list_x + list_w:
                for idx, p in enumerate(self._presets()):
                    ry = list_y + idx * row_h + self.scroll
                    if ry <= my <= ry + row_h - 4 and \
                            list_y <= my <= list_y + self.HEIGHT - 130:
                        self.selected = p
                        break

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self.x + 15 <= mx <= self.x + 375:
                self.scroll = min(0, self.scroll + event.y * 25)

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
        pygame.draw.rect(screen, COLORS["border_light"], rect, 2,
                         border_radius=10)

        title = fonts.header.render("Lataa party (sijainti)", True,
                                    COLORS["accent"])
        screen.blit(title, (self.x + 20, self.y + 15))

        self._draw_list(screen, mp)
        self._draw_preview(screen)

        self.btn_load.enabled = self.selected is not None
        self.btn_load.draw(screen, mp)
        self.btn_close.draw(screen, mp)

    def _draw_list(self, screen, mp):
        list_x = self.x + 15
        list_y = self.y + 60
        list_w = 360
        list_h = self.HEIGHT - 130
        row_h = 62

        bg = pygame.Rect(list_x, list_y, list_w, list_h)
        pygame.draw.rect(screen, COLORS["bg_dark"], bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=6)
        prev_clip = screen.get_clip()
        screen.set_clip(bg)

        for idx, p in enumerate(self._presets()):
            ry = list_y + idx * row_h + self.scroll
            row = pygame.Rect(list_x + 3, ry + 2, list_w - 6, row_h - 4)
            if p is self.selected:
                pygame.draw.rect(screen, COLORS["accent"], row, border_radius=4)
            elif row.collidepoint(mp):
                pygame.draw.rect(screen, COLORS["panel"], row, border_radius=4)

            screen.blit(fonts.small_bold.render(p.name, True,
                                                COLORS["text_main"]),
                        (list_x + 10, ry + 6))
            found, missing = party_presets.resolve_members(p)
            cnt = f"{p.location} · {len(found)} hahmoa"
            if missing:
                cnt += f" (+{len(missing)} tulossa)"
            screen.blit(fonts.tiny.render(cnt, True, COLORS["text_dim"]),
                        (list_x + 10, ry + 28))

        screen.set_clip(prev_clip)

    def _draw_preview(self, screen):
        px = self.x + 390
        py = self.y + 60
        pw = self.WIDTH - 405
        ph = self.HEIGHT - 130

        bg = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(screen, COLORS["bg_dark"], bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=6)

        p = self.selected
        if p is None:
            screen.blit(fonts.body.render("Valitse party", True,
                                          COLORS["text_dim"]),
                        (px + 15, py + 15))
            return

        y = py + 10
        screen.blit(fonts.body_bold.render(p.name, True, COLORS["accent"]),
                    (px + 12, y))
        y += 26
        screen.blit(fonts.small.render(p.location, True, COLORS["text_dim"]),
                    (px + 12, y))
        y += 24
        y = self._blit_wrapped(screen, p.description, px + 12, y, pw - 24,
                               fonts.small, COLORS["text_main"])
        y += 8

        found, missing = party_presets.resolve_members(p)
        screen.blit(fonts.small_bold.render("Hahmot:", True,
                                            COLORS["text_main"]),
                    (px + 12, y))
        y += 20
        for h in found:
            line = f"  • {h.name} ({h.character_class} {h.character_level})"
            screen.blit(fonts.tiny.render(line, True, COLORS["text_dim"]),
                        (px + 12, y))
            y += 16
        for name in missing:
            line = f"  • {name} (lisätään myöhemmin)"
            screen.blit(fonts.tiny.render(line, True, COLORS["text_faint"]
                                          if "text_faint" in COLORS
                                          else COLORS["text_dim"]),
                        (px + 12, y))
            y += 16

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
            y += font.get_height() + 2
        return y
