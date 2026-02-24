import pygame
from settings import COLORS

pygame.font.init()


class FontManager:
    def __init__(self):
        try:
            main = "verdana"
            self.title_font   = pygame.font.SysFont(main, 46, bold=True)
            self.header_font  = pygame.font.SysFont(main, 28, bold=True)
            self.body_font    = pygame.font.SysFont(main, 19)
            self.small_font   = pygame.font.SysFont(main, 15)
            self.tiny_font    = pygame.font.SysFont(main, 13)
        except pygame.error:
            self.title_font   = pygame.font.Font(None, 60)
            self.header_font  = pygame.font.Font(None, 38)
            self.body_font    = pygame.font.Font(None, 26)
            self.small_font   = pygame.font.Font(None, 20)
            self.tiny_font    = pygame.font.Font(None, 17)

    @property
    def title(self): return self.title_font
    @property
    def header(self): return self.header_font
    @property
    def body(self): return self.body_font
    @property
    def small(self): return self.small_font
    @property
    def tiny(self): return self.tiny_font


fonts = FontManager()


class Button:
    def __init__(self, x, y, width, height, text, on_click, color=None, hover_color=None, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.on_click = on_click
        self.color = color or COLORS["accent"]
        self.hover_color = hover_color or COLORS["accent_hover"]
        self.is_hovered = False
        self._font = font or fonts.body

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.on_click:
                self.on_click()

    def draw(self, screen, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        surf = self._font.render(self.text, True, COLORS["text_main"])
        screen.blit(surf, surf.get_rect(center=self.rect.center))


class Panel:
    """A simple filled rectangle with an optional title."""
    def __init__(self, x, y, w, h, title="", color=None, border_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.color = color or COLORS["panel"]
        self.border_color = border_color or COLORS["border"]

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=6)
        if self.title:
            surf = fonts.small.render(self.title, True, COLORS["text_dim"])
            screen.blit(surf, (self.rect.x + 8, self.rect.y + 4))


class HPBar:
    def draw(self, screen, cx, cy, w, hp, max_hp):
        pct = max(0.0, hp / max_hp) if max_hp > 0 else 0.0
        color = COLORS["success"] if pct > 0.5 else COLORS["warning"] if pct > 0.25 else COLORS["danger"]
        bg = pygame.Rect(cx - w // 2, cy, w, 5)
        fill = pygame.Rect(cx - w // 2, cy, int(w * pct), 5)
        pygame.draw.rect(screen, (20, 20, 20), bg)
        pygame.draw.rect(screen, color, fill)


hp_bar = HPBar()
