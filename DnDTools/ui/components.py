import pygame
from settings import COLORS

pygame.font.init()


class FontManager:
    def __init__(self):
        try:
            main = "segoeui"
            bold = "segoeuib"
            self.title_font   = pygame.font.SysFont(bold, 44, bold=True)
            self.header_font  = pygame.font.SysFont(bold, 26, bold=True)
            self.body_font    = pygame.font.SysFont(main, 18)
            self.body_bold    = pygame.font.SysFont(bold, 18, bold=True)
            self.small_font   = pygame.font.SysFont(main, 15)
            self.small_bold   = pygame.font.SysFont(bold, 15, bold=True)
            self.tiny_font    = pygame.font.SysFont(main, 12)
            self.icon_font    = pygame.font.SysFont(bold, 22, bold=True)
            # Test render to ensure the font exists
            self.title_font.render("T", True, (255,255,255))
        except (pygame.error, Exception):
            try:
                main = "verdana"
                self.title_font   = pygame.font.SysFont(main, 44, bold=True)
                self.header_font  = pygame.font.SysFont(main, 26, bold=True)
                self.body_font    = pygame.font.SysFont(main, 18)
                self.body_bold    = pygame.font.SysFont(main, 18, bold=True)
                self.small_font   = pygame.font.SysFont(main, 15)
                self.small_bold   = pygame.font.SysFont(main, 15, bold=True)
                self.tiny_font    = pygame.font.SysFont(main, 12)
                self.icon_font    = pygame.font.SysFont(main, 22, bold=True)
            except pygame.error:
                self.title_font   = pygame.font.Font(None, 56)
                self.header_font  = pygame.font.Font(None, 34)
                self.body_font    = pygame.font.Font(None, 24)
                self.body_bold    = pygame.font.Font(None, 24)
                self.small_font   = pygame.font.Font(None, 19)
                self.small_bold   = pygame.font.Font(None, 19)
                self.tiny_font    = pygame.font.Font(None, 16)
                self.icon_font    = pygame.font.Font(None, 28)

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


def draw_gradient_rect(surface, rect, color_top, color_bottom, border_radius=0):
    """Draw a vertical gradient rectangle."""
    x, y, w, h = rect
    if h <= 0 or w <= 0:
        return
    grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for row in range(h):
        t = row / max(h - 1, 1)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
        a = color_top[3] if len(color_top) > 3 else 255
        pygame.draw.line(grad_surf, (r, g, b, a), (0, row), (w - 1, row))
    if border_radius > 0:
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=border_radius)
        grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(grad_surf, (x, y))


class Button:
    def __init__(self, x, y, width, height, text, on_click, color=None, hover_color=None,
                 font=None, icon=None, style="default"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.on_click = on_click
        self.color = color or COLORS["accent"]
        self.hover_color = hover_color or self._brighten(self.color, 25)
        self.is_hovered = False
        self._font = font or fonts.body
        self.icon = icon
        self.style = style  # "default", "flat", "outline", "danger"
        self.enabled = True
        self._press_anim = 0

    @staticmethod
    def _brighten(color, amount):
        return tuple(min(255, c + amount) for c in color[:3])

    @staticmethod
    def _darken(color, amount):
        return tuple(max(0, c - amount) for c in color[:3])

    def handle_event(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.on_click:
                self._press_anim = 4
                self.on_click()

    def draw(self, screen, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled

        if self._press_anim > 0:
            self._press_anim -= 1

        r = self.rect.copy()
        if self._press_anim > 0:
            r.inflate_ip(-2, -2)

        if not self.enabled:
            pygame.draw.rect(screen, COLORS["disabled"], r, border_radius=6)
            surf = self._font.render(self.text, True, COLORS["text_muted"])
            screen.blit(surf, surf.get_rect(center=r.center))
            return

        if self.style == "outline":
            bg = self.color if self.is_hovered else COLORS["panel"]
            pygame.draw.rect(screen, bg, r, border_radius=6)
            pygame.draw.rect(screen, self.color, r, 2, border_radius=6)
        elif self.style == "flat":
            bg = COLORS["hover"] if self.is_hovered else COLORS["panel"]
            pygame.draw.rect(screen, bg, r, border_radius=6)
        else:
            base = self.hover_color if self.is_hovered else self.color
            top = self._brighten(base, 15)
            bot = self._darken(base, 15)
            draw_gradient_rect(screen, r, top, bot, border_radius=6)
            if self.is_hovered:
                glow = pygame.Surface((r.width + 4, r.height + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*base, 40), (0, 0, r.width + 4, r.height + 4), border_radius=8)
                screen.blit(glow, (r.x - 2, r.y - 2))

        # Text
        text_color = COLORS["text_bright"] if self.style != "flat" else COLORS["text_main"]
        surf = self._font.render(self.text, True, text_color)
        screen.blit(surf, surf.get_rect(center=r.center))


class Panel:
    """A styled panel with optional title and subtle gradient."""
    def __init__(self, x, y, w, h, title="", color=None, border_color=None, style="default"):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.color = color or COLORS["panel"]
        self.border_color = border_color or COLORS["border"]
        self.style = style

    def draw(self, screen):
        # Background with subtle gradient
        top = tuple(min(255, c + 4) for c in self.color)
        bot = tuple(max(0, c - 4) for c in self.color)
        draw_gradient_rect(screen, self.rect, top, bot, border_radius=8)

        # Border
        pygame.draw.rect(screen, self.border_color, self.rect, 1, border_radius=8)

        # Title bar
        if self.title:
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 28)
            pygame.draw.rect(screen, COLORS["panel_header"], title_rect,
                             border_top_left_radius=8, border_top_right_radius=8)
            pygame.draw.line(screen, COLORS["separator"],
                             (self.rect.x, self.rect.y + 28),
                             (self.rect.x + self.rect.width, self.rect.y + 28))
            surf = fonts.small_bold.render(self.title, True, COLORS["text_dim"])
            screen.blit(surf, (self.rect.x + 10, self.rect.y + 5))


class HPBar:
    def draw(self, screen, cx, cy, w, hp, max_hp, height=7, show_text=False):
        pct = max(0.0, hp / max_hp) if max_hp > 0 else 0.0

        # Color gradient based on HP%
        if pct > 0.6:
            color = COLORS["hp_full"]
        elif pct > 0.3:
            # Interpolate between yellow and green
            t = (pct - 0.3) / 0.3
            color = (
                int(COLORS["hp_mid"][0] + (COLORS["hp_full"][0] - COLORS["hp_mid"][0]) * t),
                int(COLORS["hp_mid"][1] + (COLORS["hp_full"][1] - COLORS["hp_mid"][1]) * t),
                int(COLORS["hp_mid"][2] + (COLORS["hp_full"][2] - COLORS["hp_mid"][2]) * t),
            )
        elif pct > 0.0:
            t = pct / 0.3
            color = (
                int(COLORS["hp_low"][0] + (COLORS["hp_mid"][0] - COLORS["hp_low"][0]) * t),
                int(COLORS["hp_low"][1] + (COLORS["hp_mid"][1] - COLORS["hp_low"][1]) * t),
                int(COLORS["hp_low"][2] + (COLORS["hp_mid"][2] - COLORS["hp_low"][2]) * t),
            )
        else:
            color = COLORS["hp_low"]

        bg = pygame.Rect(cx - w // 2, cy, w, height)
        fill = pygame.Rect(cx - w // 2, cy, max(1, int(w * pct)), height)

        # Background with subtle rounded corners
        pygame.draw.rect(screen, COLORS["hp_bg"], bg, border_radius=height // 2)
        if pct > 0:
            pygame.draw.rect(screen, color, fill, border_radius=height // 2)
            # Highlight line on top of fill
            if height >= 5:
                highlight = (*tuple(min(255, c + 40) for c in color), 80)
                hl_surf = pygame.Surface((fill.width, 1), pygame.SRCALPHA)
                hl_surf.fill(highlight)
                screen.blit(hl_surf, (fill.x, fill.y))

        # Outer border
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=height // 2)

        if show_text and max_hp > 0:
            txt = f"{hp}/{max_hp}"
            ts = fonts.tiny.render(txt, True, COLORS["text_bright"])
            screen.blit(ts, (cx - ts.get_width() // 2, cy - 1))


class TabBar:
    """A styled tab bar component."""
    def __init__(self, x, y, width, tabs, active=0, on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.tabs = tabs
        self.active = active
        self.on_change = on_change
        self.tab_width = width // max(len(tabs), 1)
        self.height = 32

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.y <= my <= self.y + self.height:
                for i in range(len(self.tabs)):
                    tx = self.x + i * self.tab_width
                    if tx <= mx <= tx + self.tab_width:
                        self.active = i
                        if self.on_change:
                            self.on_change(i)
                        break

    def draw(self, screen, mouse_pos):
        for i, tab in enumerate(self.tabs):
            tr = pygame.Rect(self.x + i * self.tab_width, self.y, self.tab_width - 2, self.height)
            is_active = i == self.active
            is_hover = tr.collidepoint(mouse_pos)

            if is_active:
                pygame.draw.rect(screen, COLORS["accent_dim"], tr, border_radius=4)
                pygame.draw.rect(screen, COLORS["accent"], tr, 1, border_radius=4)
                # Active indicator line
                pygame.draw.line(screen, COLORS["accent"],
                                 (tr.x + 4, tr.bottom - 2), (tr.right - 4, tr.bottom - 2), 2)
                color = COLORS["text_bright"]
            else:
                if is_hover:
                    pygame.draw.rect(screen, COLORS["hover"], tr, border_radius=4)
                color = COLORS["text_dim"] if not is_hover else COLORS["text_main"]

            tt = fonts.small_bold.render(tab, True, color)
            screen.blit(tt, tt.get_rect(center=tr.center))


class Tooltip:
    """Floating tooltip that follows mouse."""
    @staticmethod
    def draw(screen, text, pos, max_width=300):
        lines = []
        for raw_line in text.split('\n'):
            words = raw_line.split(' ')
            current = ""
            for w in words:
                test = current + " " + w if current else w
                tw = fonts.small.size(test)[0]
                if tw > max_width - 16:
                    if current:
                        lines.append(current)
                    current = w
                else:
                    current = test
            if current:
                lines.append(current)

        if not lines:
            return

        line_h = 18
        w = min(max_width, max(fonts.small.size(l)[0] for l in lines) + 16)
        h = len(lines) * line_h + 10

        mx, my = pos
        x = min(mx + 12, 1920 - w - 5)
        y = min(my + 12, 1080 - h - 5)

        # Shadow
        shadow = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (0, 0, w + 4, h + 4), border_radius=6)
        screen.blit(shadow, (x - 2, y - 2))

        # Background
        pygame.draw.rect(screen, COLORS["panel_light"], (x, y, w, h), border_radius=5)
        pygame.draw.rect(screen, COLORS["border_light"], (x, y, w, h), 1, border_radius=5)

        for i, line in enumerate(lines):
            ts = fonts.small.render(line, True, COLORS["text_main"])
            screen.blit(ts, (x + 8, y + 5 + i * line_h))


class ProgressBar:
    """Generic progress bar with label."""
    @staticmethod
    def draw(screen, x, y, w, h, value, max_value, color, label="", show_pct=False):
        pct = max(0.0, min(1.0, value / max_value)) if max_value > 0 else 0
        bg = pygame.Rect(x, y, w, h)
        fill = pygame.Rect(x, y, max(1, int(w * pct)), h)

        pygame.draw.rect(screen, COLORS["hp_bg"], bg, border_radius=h // 2)
        if pct > 0:
            pygame.draw.rect(screen, color, fill, border_radius=h // 2)
        pygame.draw.rect(screen, COLORS["border"], bg, 1, border_radius=h // 2)

        if label:
            ts = fonts.tiny.render(label, True, COLORS["text_bright"])
            screen.blit(ts, (x + 4, y + (h - ts.get_height()) // 2))
        if show_pct:
            ps = fonts.tiny.render(f"{int(pct * 100)}%", True, COLORS["text_bright"])
            screen.blit(ps, (x + w - ps.get_width() - 4, y + (h - ps.get_height()) // 2))


class Badge:
    """Small colored badge/chip for displaying status info."""
    @staticmethod
    def draw(screen, x, y, text, color, font=None):
        f = font or fonts.tiny
        ts = f.render(text, True, COLORS["text_bright"])
        w = ts.get_width() + 10
        h = ts.get_height() + 4
        bg_color = (*color, 180) if len(color) == 3 else color
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg_color, (0, 0, w, h), border_radius=h // 2)
        screen.blit(surf, (x, y))
        screen.blit(ts, (x + 5, y + 2))
        return w


class Divider:
    """Horizontal divider line."""
    @staticmethod
    def draw(screen, x, y, w):
        pygame.draw.line(screen, COLORS["separator"], (x, y), (x + w, y))


hp_bar = HPBar()
