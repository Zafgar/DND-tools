"""
ArmyBattleModal — DM-facing readout for an army-vs-army Monte Carlo run.

The map editor produces two ``Army`` objects (usually from ``army_token``
map objects pointing to a monster entry + unit_count) and hands them to
this modal.  The modal runs :func:`data.army_sim.monte_carlo`, shows the
win rate + mean casualties, and lets the DM re-roll with a new trial
count or a different random seed.

The module keeps the simulation logic out — it's purely a view layer on
top of :mod:`data.army_sim`.  Tests live in ``tests/test_army_sim.py``.
"""
from __future__ import annotations

import random
from typing import Callable, Optional

import pygame

from data.army_sim import Army, MonteCarloResult, monte_carlo, simulate
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts


TRIAL_PRESETS = (10, 50, 200)


class ArmyBattleModal:
    W = 760
    H = 560

    def __init__(self, army_a: Army, army_b: Army,
                  on_close: Callable[[], None],
                  trials: int = 50):
        self.army_a = army_a
        self.army_b = army_b
        self.on_close = on_close
        self.trials = trials
        self.rng = random.Random()
        self.result: Optional[MonteCarloResult] = None
        self.last_sample = None  # one deterministic trial for the graph

        self.x = SCREEN_WIDTH // 2 - self.W // 2
        self.y = SCREEN_HEIGHT // 2 - self.H // 2
        self.rect = pygame.Rect(self.x, self.y, self.W, self.H)

        self.btn_close = Button(self.x + self.W - 110, self.y + self.H - 50,
                                 90, 38, "Sulje", self._close,
                                 color=COLORS["danger"])
        self.btn_rerun = Button(self.x + 20, self.y + self.H - 50,
                                 160, 38, "Simuloi uudelleen", self._rerun,
                                 color=COLORS["accent"])
        self._trial_btns = []
        bx = self.x + 200
        for n in TRIAL_PRESETS:
            self._trial_btns.append(
                Button(bx, self.y + self.H - 50, 70, 38, f"{n}x",
                        lambda n=n: self._set_trials(n),
                        color=COLORS["panel_light"])
            )
            bx += 80
        self._rerun()

    # ------------------------------------------------------------------
    def _close(self) -> None:
        self.on_close()

    def _set_trials(self, n: int) -> None:
        self.trials = int(n)
        self._rerun()

    def _rerun(self) -> None:
        # Deep copies happen inside monte_carlo; army_a/_b remain pristine.
        self.result = monte_carlo(self.army_a, self.army_b,
                                   trials=self.trials, rng=self.rng)
        # Also grab one trial log for the damage chart.
        import copy
        self.last_sample = simulate(copy.deepcopy(self.army_a),
                                     copy.deepcopy(self.army_b),
                                     rng=random.Random(self.rng.random()))

    # ------------------------------------------------------------------
    def handle_event(self, ev: pygame.event.Event) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._close()
            return
        self.btn_close.handle_event(ev)
        self.btn_rerun.handle_event(ev)
        for b in self._trial_btns:
            b.handle_event(ev)

    # ------------------------------------------------------------------
    def draw(self, screen) -> None:
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, COLORS["panel"], self.rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 2, border_radius=12)

        hdr = fonts.header.render(
            f"Armeijasimulaatio: {self.army_a.name} vs {self.army_b.name}",
            True, COLORS["text_bright"])
        screen.blit(hdr, (self.x + 20, self.y + 16))

        self._draw_summary(screen)
        self._draw_winrate_bar(screen)
        self._draw_chart(screen)

        mp = pygame.mouse.get_pos()
        self.btn_close.draw(screen, mp)
        self.btn_rerun.draw(screen, mp)
        for b in self._trial_btns:
            b.draw(screen, mp)

    # ------------------------------------------------------------------
    def _draw_summary(self, screen) -> None:
        y0 = self.y + 58
        col_w = (self.W - 60) // 2
        for i, army in enumerate((self.army_a, self.army_b)):
            bx = self.x + 20 + i * (col_w + 20)
            box = pygame.Rect(bx, y0, col_w, 120)
            pygame.draw.rect(screen, COLORS["panel_dark"], box, border_radius=8)
            title = fonts.body_bold.render(army.name, True, COLORS["text_bright"])
            screen.blit(title, (bx + 12, y0 + 8))
            lines = [
                f"Yksiköt yhteensä: {army.total_count}",
                f"HP yhteensä: {army.total_hp}",
                f"DPR yhteensä: {army.total_dpr:.1f}",
                f"Keskiarvo AC: {army.mean_ac:.1f}",
            ]
            for j, line in enumerate(lines):
                ts = fonts.small.render(line, True, COLORS["text_main"])
                screen.blit(ts, (bx + 12, y0 + 34 + j * 18))

    def _draw_winrate_bar(self, screen) -> None:
        res = self.result
        if res is None:
            return
        y = self.y + 195
        pad = 20
        w = self.W - 2 * pad
        bar = pygame.Rect(self.x + pad, y, w, 26)
        pygame.draw.rect(screen, COLORS["panel_dark"], bar, border_radius=6)
        # Three segments: A | draw | B
        total = max(1, res.trials)
        wa = int(w * res.a_wins / total)
        wd = int(w * res.draws / total)
        # A
        pygame.draw.rect(screen, (90, 140, 220),
                         pygame.Rect(bar.x, bar.y, wa, bar.h), border_radius=6)
        # Draws
        pygame.draw.rect(screen, (150, 150, 160),
                         pygame.Rect(bar.x + wa, bar.y, wd, bar.h))
        # B
        pygame.draw.rect(screen, (220, 110, 100),
                         pygame.Rect(bar.x + wa + wd, bar.y,
                                     w - wa - wd, bar.h),
                         border_radius=6)

        legend = (
            f"{self.army_a.name} voitot {res.win_rate_a * 100:.0f}%  •  "
            f"tasapelit {res.draws}/{res.trials}  •  "
            f"{self.army_b.name} voitot {res.win_rate_b * 100:.0f}%"
        )
        ts = fonts.small.render(legend, True, COLORS["text_main"])
        screen.blit(ts, (self.x + pad, y + 34))

        cas = fonts.small.render(
            f"Keskimääräiset tappiot  •  {self.army_a.name}: "
            f"{res.mean_cas_a:.1f}   {self.army_b.name}: {res.mean_cas_b:.1f}   "
            f"kierroksia ~ {res.mean_rounds:.1f}",
            True, COLORS["text_dim"])
        screen.blit(cas, (self.x + pad, y + 54))

    def _draw_chart(self, screen) -> None:
        """Render the unit-count curve over time for the sample trial."""
        sample = self.last_sample
        if sample is None or not sample.log:
            return
        pad = 20
        y0 = self.y + 290
        h = self.H - 290 - 80
        chart = pygame.Rect(self.x + pad, y0, self.W - 2 * pad, h)
        pygame.draw.rect(screen, COLORS["panel_dark"], chart, border_radius=6)
        title = fonts.small_bold.render(
            "Esimerkkiajo — yksikkömäärät per kierros",
            True, COLORS["text_dim"])
        screen.blit(title, (chart.x + 8, chart.y + 6))

        max_count = max(1,
                         max(r.count_a for r in sample.log),
                         max(r.count_b for r in sample.log),
                         sample.log[0].count_a, sample.log[0].count_b)
        plot_y = chart.y + 28
        plot_h = chart.h - 36
        plot_x = chart.x + 8
        plot_w = chart.w - 16
        n = len(sample.log)
        if n < 2:
            return
        step = plot_w / (n - 1)

        def line(key, color):
            pts = []
            for i, r in enumerate(sample.log):
                v = getattr(r, key)
                px = int(plot_x + i * step)
                py = int(plot_y + plot_h - (v / max_count) * plot_h)
                pts.append((px, py))
            if len(pts) >= 2:
                pygame.draw.lines(screen, color, False, pts, 2)

        line("count_a", (120, 180, 255))
        line("count_b", (255, 130, 120))

        legend_y = chart.bottom - 20
        pygame.draw.line(screen, (120, 180, 255),
                         (chart.x + 10, legend_y), (chart.x + 30, legend_y), 2)
        screen.blit(fonts.tiny.render(self.army_a.name, True, COLORS["text_main"]),
                     (chart.x + 36, legend_y - 8))
        ox = chart.x + 36 + fonts.tiny.size(self.army_a.name)[0] + 20
        pygame.draw.line(screen, (255, 130, 120),
                         (ox, legend_y), (ox + 20, legend_y), 2)
        screen.blit(fonts.tiny.render(self.army_b.name, True, COLORS["text_main"]),
                     (ox + 26, legend_y - 8))
