"""Combat Audit screen — soak-test the whole combat system and read the log.

Opens from the main menu. Pick a depth, press RUN, and the tool plays
hundreds of real battles across every class, every spell list and a
sweep of the monster library, watching the board after every step.
Faults are grouped and counted on screen; the full log with evidence
lands in ``audit_logs/``.

The run is driven from the main loop in millisecond slices rather than
from a thread, so the progress bar stays live, ESC still works, and no
pygame surface is ever touched from anywhere but the main thread.
"""
import os
import subprocess
import sys

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts, draw_gradient_rect
from engine.combat_audit import (
    AuditRunner, DEPTHS, build_scenarios, default_log_dir, write_report,
    ERROR, WARNING,
)

_DEPTH_BLURB = {
    "quick": "Yksi kierros per skenaario. Nopea terveystarkastus.",
    "standard": "Kaksi siementä, joka toinen hirviö. Normaali ajo.",
    "deep": "Neljä siementä, koko bestiaario. Kaikki mitä on.",
}


class CombatAuditState:
    """Runs the audit incrementally and shows what it found."""

    SLICE_MS = 28.0        # work per frame; leaves room to draw at 60 fps

    def __init__(self, manager):
        self.manager = manager
        self.depth = "standard"
        self.runner = None
        self.report = None
        self.log_path = ""
        self.error = ""
        self.scroll = 0
        self.counts = {d: len(build_scenarios(d)) for d in DEPTHS}

        cx = SCREEN_WIDTH // 2
        self.depth_buttons = []
        for i, d in enumerate(("quick", "standard", "deep")):
            self.depth_buttons.append((d, Button(
                cx - 330 + i * 220, 158, 200, 44, d.upper(),
                lambda dd=d: self._set_depth(dd), color=COLORS["accent"])))
        # RUN and OPEN LOG sit side by side: after a run the DM wants
        # both, and stacking them on the same rectangle hid one under
        # the other.
        self.btn_run = Button(cx - 320, 256, 200, 50, "AJA AUDIT",
                              lambda: self._start(), color=COLORS["success"])
        self.btn_stop = Button(cx - 100, 256, 200, 50, "KESKEYTÄ",
                               lambda: self._stop(), color=COLORS["danger"])
        self.btn_open = Button(cx - 100, 256, 200, 50, "AVAA LOKI",
                               lambda: self._open_log(), color=COLORS["spell"])
        self.btn_back = Button(30, SCREEN_HEIGHT - 70, 160, 44, "< Takaisin",
                               lambda: manager.change_state("MENU"),
                               color=COLORS["panel_light"], style="outline")

    # ------------------------------------------------------------------ #
    def _set_depth(self, depth):
        if self.running:
            return
        self.depth = depth

    @property
    def running(self) -> bool:
        return self.runner is not None and not self.runner.done

    def _start(self):
        if self.running:
            return
        self.report = None
        self.log_path = ""
        self.error = ""
        self.scroll = 0
        try:
            self.runner = AuditRunner(self.depth)
        except Exception as exc:                        # noqa: BLE001
            self.error = f"Auditin käynnistys epäonnistui: {exc}"
            self.runner = None

    def _stop(self):
        """Stop early but keep — and write — what has been found so far."""
        if self.runner is None or self.runner.done:
            return
        self.runner.scenarios = self.runner.scenarios[:self.runner.index]
        self.runner.run_slice(0.0)
        self._finish()

    def _finish(self):
        self.report = self.runner.report
        try:
            self.log_path = write_report(self.report)
        except Exception as exc:                        # noqa: BLE001
            self.error = f"Lokin kirjoitus epäonnistui: {exc}"

    def _open_log(self):
        """Hand the log to the desktop. Never fatal if there is no opener."""
        path = self.log_path or default_log_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)                      # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:                               # noqa: BLE001
            self.error = f"Loki on tiedostossa: {path}"

    # ------------------------------------------------------------------ #
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.running:
                        self._stop()
                    else:
                        self.manager.change_state("MENU")
                elif event.key == pygame.K_RETURN and not self.running:
                    self._start()
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = max(0, self.scroll - event.y * 40)
            if not self.running:
                for _d, btn in self.depth_buttons:
                    btn.handle_event(event)
                self.btn_run.handle_event(event)
                if self.log_path:
                    self.btn_open.handle_event(event)
            else:
                self.btn_stop.handle_event(event)
            self.btn_back.handle_event(event)

    def update(self):
        if self.runner is not None and not self.runner.done:
            if self.runner.run_slice(self.SLICE_MS):
                self._finish()

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        draw_gradient_rect(screen, pygame.Rect(0, 0, SCREEN_WIDTH,
                                               SCREEN_HEIGHT),
                           (22, 24, 30), (14, 15, 19))
        title = fonts.title.render("Combat Audit", True, COLORS["text_main"])
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 46))
        sub = fonts.small.render(
            "Pelaa satoja oikeita taisteluita kaikilla luokilla, loitsuilla "
            "ja hirviöillä — ja kirjaa ylös kaiken mikä ei voinut tapahtua.",
            True, COLORS["text_dim"])
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 104))

        cx = SCREEN_WIDTH // 2
        for d, btn in self.depth_buttons:
            chosen = (d == self.depth)
            btn.color = COLORS["legendary"] if chosen else COLORS["accent"]
            btn.draw(screen, pygame.mouse.get_pos())
            lbl = fonts.tiny.render(f"{self.counts[d]} taistelua", True,
                                    COLORS["text_dim"])
            screen.blit(lbl, (btn.rect.centerx - lbl.get_width() // 2,
                              btn.rect.bottom + 4))
        blurb = fonts.small.render(_DEPTH_BLURB.get(self.depth, ""), True,
                                   COLORS["text_dim"])
        screen.blit(blurb, (cx - blurb.get_width() // 2, 228))

        mp = pygame.mouse.get_pos()
        if self.running:
            self.btn_stop.draw(screen, mp)
            self._draw_progress(screen)
        else:
            self.btn_run.draw(screen, mp)
            if self.log_path:
                self.btn_open.draw(screen, mp)
        self.btn_back.draw(screen, mp)

        if self.error:
            es = fonts.small.render(self.error, True, COLORS["warning"])
            screen.blit(es, (cx - es.get_width() // 2, 318))

        if self.report is not None:
            self._draw_report(screen)

    def _draw_progress(self, screen):
        r = self.runner
        bar = pygame.Rect(SCREEN_WIDTH // 2 - 400, 330, 800, 26)
        pygame.draw.rect(screen, (34, 36, 42), bar, border_radius=6)
        pygame.draw.rect(screen, COLORS["success"],
                         (bar.x, bar.y, int(bar.width * r.progress), bar.height),
                         border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], bar, 1, border_radius=6)
        txt = (f"{r.index}/{r.total} skenaariota  •  "
               f"{r.report.battles} taistelua  •  "
               f"{r.report.steps} askelta  •  "
               f"{len(r.report.errors)} virhelajia")
        ts = fonts.body.render(txt, True, COLORS["text_main"])
        screen.blit(ts, (SCREEN_WIDTH // 2 - ts.get_width() // 2, 366))
        cur = r.scenarios[min(r.index, r.total - 1)] if r.total else None
        if cur is not None:
            cs = fonts.tiny.render(f"{cur.suite}: {cur.label}", True,
                                   COLORS["text_dim"])
            screen.blit(cs, (SCREEN_WIDTH // 2 - cs.get_width() // 2, 394))

    def _draw_report(self, screen):
        rep = self.report
        cx = SCREEN_WIDTH // 2
        errs, warns = rep.errors, rep.warnings
        verdict_col = (COLORS["danger"] if errs
                       else COLORS["warning"] if warns
                       else COLORS["success"])
        verdict = (f"{rep.battles} taistelua, {rep.steps} askelta, "
                   f"{rep.elapsed_s:.1f} s  —  {len(errs)} virhelajia, "
                   f"{len(warns)} varoituslajia")
        vs = fonts.header.render(verdict, True, verdict_col)
        screen.blit(vs, (cx - vs.get_width() // 2, 326))
        if self.log_path:
            ps = fonts.tiny.render(self.log_path, True, COLORS["text_dim"])
            screen.blit(ps, (cx - ps.get_width() // 2, 360))

        panel = pygame.Rect(120, 388, SCREEN_WIDTH - 240,
                            SCREEN_HEIGHT - 478)
        pygame.draw.rect(screen, (30, 32, 38), panel, border_radius=8)
        pygame.draw.rect(screen, COLORS["border"], panel, 1, border_radius=8)
        prev = screen.get_clip()
        screen.set_clip(panel)

        y = panel.y + 12 - self.scroll
        findings = rep.sorted_findings()
        if not findings:
            ok = fonts.body.render(
                "Ei yhtään sääntö- tai tilarikkomusta.", True,
                COLORS["success"])
            screen.blit(ok, (panel.x + 16, y))
            y += 30
        for f in findings:
            if y > panel.bottom:
                break
            col = (COLORS["danger"] if f.severity == ERROR
                   else COLORS["warning"] if f.severity == WARNING
                   else COLORS["text_dim"])
            if y + 40 > panel.y:
                head = fonts.body.render(
                    f"[{f.severity.upper()}] {f.category} — {f.title}  "
                    f"(x{f.count})", True, col)
                screen.blit(head, (panel.x + 16, y))
            y += 24
            for ex in f.examples[:2]:
                if panel.y <= y <= panel.bottom:
                    es = fonts.tiny.render(ex[:170], True, COLORS["text_dim"])
                    screen.blit(es, (panel.x + 36, y))
                y += 18
            y += 8

        # Coverage summary at the end of the scroll
        if panel.y <= y <= panel.bottom:
            cov = fonts.small.render(
                f"Kattavuus: {len(rep.classes_played)} luokkaa, "
                f"{len(rep.monsters_played)} hirviötä kentällä "
                f"({len(rep.monsters_that_acted)} toimi), "
                f"{len(rep.spells_cast)} eri loitsua, "
                f"{len(rep.conditions_seen)} eri tilaa",
                True, COLORS["accent"])
            screen.blit(cov, (panel.x + 16, y))
        y += 26
        self._content_h = y + self.scroll - panel.y

        screen.set_clip(prev)
