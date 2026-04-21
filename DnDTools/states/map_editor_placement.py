"""
PreBattleSetupModal — manual + AI unit placement before the battle starts.

MapEditorState.start_encounter_from_object builds a roster from a map token
(or a saved encounter), then — instead of hard-coding "party left, enemies
right" — this modal lets the DM decide:

* Click a roster row to select an entity, click a grid cell to place it.
* "Tasapuolinen" splits the grid: allies left, enemies right (default).
* "AI aseta" asks the tactical AI to pick advantageous cells for both
  sides based on creature reach/speed and the existing entities on the
  grid.
* "Vain viholliset AI:lle" places allies manually but lets the AI
  distribute enemies (useful when the DM wants to control hero positions
  but let NPCs self-organise).
* "Aloita taistelu" commits positions and launches BattleState.

The modal is grid-agnostic; the underlying battle engine allows any integer
grid_x/grid_y. We just use a 25 × 15 preview for the placement surface.
"""
from __future__ import annotations

import random
from typing import Callable, List, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts


GRID_COLS = 25
GRID_ROWS = 15


class PreBattleSetupModal:
    W = 1100
    H = 720

    def __init__(self, manager, entities, on_confirm: Callable[[], None],
                 on_cancel: Callable[[], None]):
        self.manager = manager
        self.entities = entities
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2
        self.rect = pygame.Rect(self.x, self.y, self.W, self.H)

        # Grid surface: leaves room for the roster column on the right
        self.roster_col_w = 300
        self.grid_rect = pygame.Rect(
            self.x + 20, self.y + 60,
            self.W - self.roster_col_w - 40, self.H - 120,
        )
        self.cell_w = self.grid_rect.width / GRID_COLS
        self.cell_h = self.grid_rect.height / GRID_ROWS

        self.selected_idx = 0
        self.placements: dict[int, Tuple[int, int]] = {}
        self._roster_rects: List[pygame.Rect] = []

        # Seed default placement (party left, enemies right)
        self._auto_split_sides()

        # Footer buttons
        btn_y = self.y + self.H - 48
        self.btn_split = Button(self.x + 20, btn_y, 160, 36,
                                "Tasapuolinen", self._auto_split_sides,
                                color=COLORS["panel_light"])
        self.btn_ai_all = Button(self.x + 190, btn_y, 160, 36,
                                  "AI aseta", self._ai_place_all,
                                  color=COLORS["accent"])
        self.btn_ai_enemy = Button(self.x + 360, btn_y, 200, 36,
                                    "Vain viholliset AI:lle",
                                    self._ai_place_enemies,
                                    color=COLORS["warning"])
        self.btn_start = Button(self.x + self.W - 220, btn_y, 200, 36,
                                 "Aloita taistelu", self._start,
                                 color=COLORS["success"])
        self.btn_cancel = Button(self.x + self.W - 410, btn_y, 180, 36,
                                  "Peruuta", self._cancel,
                                  color=COLORS["danger"])

    # ------------------------------------------------------------------
    # Placement algorithms
    # ------------------------------------------------------------------
    def _auto_split_sides(self) -> None:
        self.placements.clear()
        allies_used: set = set()
        enemies_used: set = set()
        for i, ent in enumerate(self.entities):
            side_ally = getattr(ent, "is_player", False)
            while True:
                if side_ally:
                    cx = random.randint(0, (GRID_COLS // 3))
                    cy = random.randint(0, GRID_ROWS - 1)
                    used = allies_used
                else:
                    cx = random.randint((GRID_COLS * 2) // 3, GRID_COLS - 1)
                    cy = random.randint(0, GRID_ROWS - 1)
                    used = enemies_used
                if (cx, cy) not in used:
                    used.add((cx, cy))
                    break
            self.placements[i] = (cx, cy)

    def _ai_place_all(self) -> None:
        """Random but never-overlapping placements biased by side."""
        self._auto_split_sides()
        # Widen ally/enemy bands so tactical AI has more room
        self.placements.clear()
        used: set = set()
        for i, ent in enumerate(self.entities):
            side_ally = getattr(ent, "is_player", False)
            # Ally band: left 40%, enemy band: right 40%
            col_lo = 0 if side_ally else int(GRID_COLS * 0.6)
            col_hi = int(GRID_COLS * 0.4) if side_ally else GRID_COLS - 1
            tries = 0
            while True:
                cx = random.randint(col_lo, col_hi)
                cy = random.randint(0, GRID_ROWS - 1)
                tries += 1
                if (cx, cy) not in used or tries > 120:
                    used.add((cx, cy))
                    self.placements[i] = (cx, cy)
                    break

    def _ai_place_enemies(self) -> None:
        used: set = {p for i, p in self.placements.items()
                     if getattr(self.entities[i], "is_player", False)}
        for i, ent in enumerate(self.entities):
            if getattr(ent, "is_player", False):
                continue
            tries = 0
            while True:
                cx = random.randint(int(GRID_COLS * 0.55), GRID_COLS - 1)
                cy = random.randint(0, GRID_ROWS - 1)
                tries += 1
                if (cx, cy) not in used or tries > 120:
                    used.add((cx, cy))
                    self.placements[i] = (cx, cy)
                    break

    # ------------------------------------------------------------------
    # Commit / cancel
    # ------------------------------------------------------------------
    def _start(self) -> None:
        # Apply placements to entities, then launch battle
        for i, ent in enumerate(self.entities):
            if i in self.placements:
                ent.grid_x, ent.grid_y = self.placements[i]
        self.on_confirm()

    def _cancel(self) -> None:
        self.on_cancel()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self._cancel()
                return
            if ev.key == pygame.K_RETURN:
                self._start()
                return
            if ev.key in (pygame.K_UP, pygame.K_DOWN):
                step = -1 if ev.key == pygame.K_UP else 1
                self.selected_idx = (self.selected_idx + step) % len(self.entities)
                return

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # Roster row click
            for i, r in enumerate(self._roster_rects):
                if r.collidepoint(ev.pos):
                    self.selected_idx = i
                    return
            # Grid cell click → move selected entity here
            if self.grid_rect.collidepoint(ev.pos):
                cx = int((ev.pos[0] - self.grid_rect.x) / self.cell_w)
                cy = int((ev.pos[1] - self.grid_rect.y) / self.cell_h)
                cx = max(0, min(GRID_COLS - 1, cx))
                cy = max(0, min(GRID_ROWS - 1, cy))
                # Push whoever currently occupies that cell off (simple swap)
                for j, pos in list(self.placements.items()):
                    if pos == (cx, cy) and j != self.selected_idx:
                        del self.placements[j]
                self.placements[self.selected_idx] = (cx, cy)
                return

        for b in (self.btn_split, self.btn_ai_all, self.btn_ai_enemy,
                  self.btn_start, self.btn_cancel):
            b.handle_event(ev)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, COLORS["panel"], self.rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 2, border_radius=10)

        hdr = fonts.header.render(
            "Taistelun valmistelu — sijoita yksiköt",
            True, COLORS["text_bright"])
        screen.blit(hdr, (self.x + 20, self.y + 18))

        self._draw_grid(screen)
        self._draw_roster(screen)

        mp = pygame.mouse.get_pos()
        for b in (self.btn_split, self.btn_ai_all, self.btn_ai_enemy,
                  self.btn_start, self.btn_cancel):
            b.draw(screen, mp)

    # ------------------------------------------------------------------
    def _draw_grid(self, screen) -> None:
        pygame.draw.rect(screen, (22, 24, 30), self.grid_rect)
        # Ally band tint
        band_w = self.grid_rect.width * 0.4
        ally_band = pygame.Rect(self.grid_rect.x, self.grid_rect.y,
                                 int(band_w), self.grid_rect.height)
        enemy_band = pygame.Rect(self.grid_rect.right - int(band_w),
                                  self.grid_rect.y,
                                  int(band_w), self.grid_rect.height)
        s = pygame.Surface((ally_band.w, ally_band.h), pygame.SRCALPHA)
        s.fill((60, 100, 180, 30))
        screen.blit(s, ally_band.topleft)
        s = pygame.Surface((enemy_band.w, enemy_band.h), pygame.SRCALPHA)
        s.fill((180, 60, 60, 30))
        screen.blit(s, enemy_band.topleft)

        # Cell grid lines
        for c in range(GRID_COLS + 1):
            x = self.grid_rect.x + int(c * self.cell_w)
            pygame.draw.line(screen, (50, 52, 60),
                             (x, self.grid_rect.y),
                             (x, self.grid_rect.bottom), 1)
        for r in range(GRID_ROWS + 1):
            y = self.grid_rect.y + int(r * self.cell_h)
            pygame.draw.line(screen, (50, 52, 60),
                             (self.grid_rect.x, y),
                             (self.grid_rect.right, y), 1)

        # Entity tokens
        for i, ent in enumerate(self.entities):
            pos = self.placements.get(i)
            if pos is None:
                continue
            cx, cy = pos
            px = self.grid_rect.x + int((cx + 0.5) * self.cell_w)
            py = self.grid_rect.y + int((cy + 0.5) * self.cell_h)
            is_ally = getattr(ent, "is_player", False)
            col = (120, 180, 255) if is_ally else (255, 130, 120)
            r = int(min(self.cell_w, self.cell_h) * 0.38)
            pygame.draw.circle(screen, col, (px, py), r)
            if i == self.selected_idx:
                pygame.draw.circle(screen, (255, 255, 110), (px, py), r + 3, 2)
            initial = (ent.stats.name[:1] if hasattr(ent, "stats") else "?")
            ts = fonts.tiny.render(initial, True, (10, 10, 10))
            screen.blit(ts, ts.get_rect(center=(px, py)))

    def _draw_roster(self, screen) -> None:
        rx = self.grid_rect.right + 16
        ry = self.grid_rect.y
        rw = self.x + self.W - rx - 20
        hdr = fonts.small_bold.render("Rosteri", True, COLORS["text_dim"])
        screen.blit(hdr, (rx, ry - 18))
        self._roster_rects = []
        for i, ent in enumerate(self.entities):
            row = pygame.Rect(rx, ry + i * 32, rw, 28)
            self._roster_rects.append(row)
            is_ally = getattr(ent, "is_player", False)
            bg = COLORS["selected"] if i == self.selected_idx else COLORS["panel_dark"]
            pygame.draw.rect(screen, bg, row, border_radius=4)
            tag_col = (120, 180, 255) if is_ally else (255, 130, 120)
            pygame.draw.circle(screen, tag_col, (row.x + 12, row.y + 14), 6)
            name = ent.stats.name if hasattr(ent, "stats") else "?"
            pos = self.placements.get(i)
            pos_txt = f"({pos[0]}, {pos[1]})" if pos else "(-)"
            disp = f"{name[:18]}  {pos_txt}"
            ts = fonts.small.render(disp, True, COLORS["text_main"])
            screen.blit(ts, (row.x + 26, row.y + 6))
