import pygame
from settings import COLORS

# Pygame-fonttien alustus
pygame.font.init()

class FontManager:
    def __init__(self):
        try:
            # Yritetään ladata järjestelmän oletusfontteja, jotka ovat yleensä saatavilla
            self.main = "verdana" # Tai "arial", "helvetica"
            self.title_font = pygame.font.SysFont(self.main, 50, bold=True)
            self.header_font = pygame.font.SysFont(self.main, 32, bold=True)
            self.body_font = pygame.font.SysFont(self.main, 20)
            self.small_font = pygame.font.SysFont(self.main, 16)
        except pygame.error:
            # Fallback perusfonttiin, jos järjestelmäfontteja ei löydy
            print("Warning: Default fonts not found. Falling back to pygame's default font.")
            self.title_font = pygame.font.Font(None, 64)
            self.header_font = pygame.font.Font(None, 40)
            self.body_font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 22)
            
    @property
    def title(self):
        return self.title_font

    @property
    def header(self):
        return self.header_font

    @property
    def body(self):
        return self.body_font

    @property
    def small(self):
        return self.small_font

# Globaali instanssi fonteille
fonts = FontManager()


class Button:
    def __init__(self, x, y, width, height, text, on_click, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.on_click = on_click
        
        # Määritä värit tai käytä oletusarvoja
        self.color = color if color else COLORS["accent"]
        self.hover_color = hover_color if hover_color else COLORS["accent_hover"]
        
        self.current_color = self.color
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.on_click:
                self.on_click()

    def draw(self, screen, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.color
        
        # Piirrä nappi
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        
        # Piirrä teksti
        text_surf = fonts.body.render(self.text, True, COLORS["text_main"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
