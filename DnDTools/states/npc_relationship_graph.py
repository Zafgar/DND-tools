"""Phase 42 — NPC relationship graph viewer.

Full-screen force-directed graph of the campaign's NPC relationships.
Nodes are NPCs (size scaled by link count = degree), edges are links
coloured by kind.  Filter chips narrow the graph by faction or
organisation to keep big casts legible.

Efficiency:
  * The graph + layout is computed ONCE when the view opens or a
    filter changes (``_rebuild``), then cached. Per-frame draw just
    blits the cached node/edge geometry — no physics every frame.
  * Hover uses the cheap :func:`data.npc_graph.nearest_node`
    hit-test and pops the shared :class:`NpcHoverCard`.
  * Clicking a node fires ``on_select(npc_id)``.

The heavy layout math lives in :mod:`data.npc_graph` (pure, tested).
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import npc_graph as ng
from states.npc_hover_card import NpcHoverCard


class NpcRelationshipGraph:
    def __init__(self, world, campaign, *,
                  on_close: Optional[Callable[[], None]] = None,
                  on_select: Optional[Callable[[str], None]] = None):
        self.world = world
        self.campaign = campaign
        self.on_close = on_close
        self.on_select = on_select
        self.is_open = False

        self.rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80,
                                  SCREEN_HEIGHT - 80)
        self.graph: Optional[ng.NpcGraph] = None
        self.filter_faction = ""
        self.filter_org_key = ""
        # Phase 44 — ego-network focus
        self.ego_mode = False
        self.ego_center_id = ""
        self.ego_depth = 1
        self._hover_card = NpcHoverCard()

        self._fac_chip_rects: List[Tuple[pygame.Rect, str]] = []
        self._org_chip_rects: List[Tuple[pygame.Rect, str]] = []

        self.btn_close = Button(0, 0, 90, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))
        self.btn_clear = Button(0, 0, 90, 24, "Kaikki",
                                   self._clear_filters,
                                   color=COLORS.get("panel_dark",
                                                      (40, 40, 56)))
        # Phase 44 ego controls
        self.btn_ego = Button(0, 0, 110, 24, "Ego-tila",
                                 self._toggle_ego,
                                 color=COLORS.get("legendary",
                                                    (170, 110, 220)))
        self.btn_ego_full = Button(0, 0, 110, 24, "Koko verkko",
                                       self._exit_ego,
                                       color=COLORS.get("panel_dark",
                                                          (40, 40, 56)))
        self.btn_depth_down = Button(0, 0, 28, 24, "-",
                                         lambda: self._set_depth(-1),
                                         color=COLORS.get("panel",
                                                            (60, 60, 80)))
        self.btn_depth_up = Button(0, 0, 28, 24, "+",
                                       lambda: self._set_depth(1),
                                       color=COLORS.get("panel",
                                                          (60, 60, 80)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self._rebuild()

    def _close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _clear_filters(self):
        self.filter_faction = ""
        self.filter_org_key = ""
        self._rebuild()

    def _toggle_ego(self):
        self.ego_mode = not self.ego_mode
        if not self.ego_mode:
            self.ego_center_id = ""
        self._rebuild()

    def _exit_ego(self):
        self.ego_mode = False
        self.ego_center_id = ""
        self._rebuild()

    def _set_depth(self, delta: int):
        self.ego_depth = max(1, min(3, self.ego_depth + delta))
        if self.ego_center_id:
            self._rebuild()

    # ------------------------------------------------------------------ #
    def _graph_area(self) -> pygame.Rect:
        # Reserve top strip for filter chips.
        return pygame.Rect(self.rect.x + 10, self.rect.y + 96,
                            self.rect.width - 20,
                            self.rect.height - 110)

    def _rebuild(self):
        """Recompute graph + layout. Called on open and filter change
        ONLY — not per frame."""
        if self.ego_center_id and self.ego_center_id in self.world.npcs:
            # Phase 44 — ego network around one NPC.
            self.graph = ng.build_ego_graph(
                self.world, self.ego_center_id,
                depth=self.ego_depth, campaign=self.campaign)
        else:
            self.graph = ng.build_graph(
                self.world,
                faction=self.filter_faction,
                organisation_key=self.filter_org_key,
                campaign=self.campaign,
                include_isolated=True,
            )
        ga = self._graph_area()
        ng.force_directed_layout(
            self.graph, width=ga.width, height=ga.height,
            iterations=70, seed=1)
        # Offset positions into the graph area's screen coords.
        for node in self.graph.nodes:
            node.x += ga.x
            node.y += ga.y

    def _unique_factions(self) -> List[str]:
        return sorted({n.faction for n in self.world.npcs.values()
                        if n.faction})

    def _org_choices(self) -> List[Tuple[str, str]]:
        if self.campaign is None:
            return []
        try:
            from data import organizations as orgs
            return [(o.key, o.name)
                     for o in orgs.ensure_organisations_on_campaign(
                         self.campaign)]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in (self.btn_close, self.btn_clear, self.btn_ego,
                          self.btn_ego_full, self.btn_depth_down,
                          self.btn_depth_up):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            for rect, fac in self._fac_chip_rects:
                if rect.collidepoint(event.pos):
                    self.filter_faction = (
                        "" if self.filter_faction == fac else fac)
                    self._rebuild()
                    return True
            for rect, key in self._org_chip_rects:
                if rect.collidepoint(event.pos):
                    self.filter_org_key = (
                        "" if self.filter_org_key == key else key)
                    self._rebuild()
                    return True
            # Node click — ego mode re-centres; normal mode jumps to
            # the NPC sheet.
            if self.graph:
                node = ng.nearest_node(
                    self.graph, event.pos[0], event.pos[1],
                    max_dist=22)
                if node:
                    if self.ego_mode:
                        self.ego_center_id = node.id
                        self._rebuild()
                    elif self.on_select:
                        self.on_select(node.id)
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        scrim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        scrim.set_alpha(190)
        scrim.fill((0, 0, 0))
        screen.blit(scrim, (0, 0))
        pygame.draw.rect(screen, COLORS.get("bg_dark", (20, 20, 28)),
                          self.rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (130, 130, 160)),
                          self.rect, 2, border_radius=10)

        node_count = len(self.graph.nodes) if self.graph else 0
        edge_count = len(self.graph.edges) if self.graph else 0
        title = (f"NPC-suhdeverkosto ({node_count} hahmoa, "
                  f"{edge_count} sidettä)")
        if self.ego_mode and self.ego_center_id:
            center = self.world.npcs.get(self.ego_center_id)
            cname = center.name if center else self.ego_center_id
            title = (f"Ego-verkosto: {cname} "
                      f"(syvyys {self.ego_depth}) — "
                      f"{node_count} hahmoa")
        elif self.ego_mode:
            title = "Ego-tila — klikkaa hahmoa keskittääksesi"
        screen.blit(fonts.body_bold.render(
            title, True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.rect.x + 20, self.rect.y + 14))
        self.btn_close.rect.x = self.rect.right - 110
        self.btn_close.rect.y = self.rect.y + 12
        self.btn_close.draw(screen, mp)

        self._draw_filters(screen, mp)
        self._draw_graph(screen, mp)
        self._draw_legend(screen)

        # Hover card on top
        self._hover_card.draw(screen, mp)

    def _draw_filters(self, screen, mp):
        self._fac_chip_rects = []
        self._org_chip_rects = []
        x = self.rect.x + 20
        y = self.rect.y + 50
        self.btn_clear.rect.x = x
        self.btn_clear.rect.y = y
        self.btn_clear.draw(screen, mp)
        x += 100
        for fac in self._unique_factions()[:7]:
            label = fac[:16]
            w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(x, y, w, 22)
            active = (self.filter_faction == fac)
            pygame.draw.rect(screen,
                              COLORS.get("accent", (110, 130, 220))
                              if active else
                              COLORS.get("panel_dark", (40, 40, 56)),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(
                label, True,
                (20, 20, 30) if active else
                COLORS.get("text_main", (220, 220, 235))),
                (chip.x + 7, chip.y + 4))
            self._fac_chip_rects.append((chip, fac))
            x += w + 4

        y += 28
        x = self.rect.x + 120
        for key, name in self._org_choices()[:5]:
            label = name[:18]
            w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(x, y, w, 22)
            active = (self.filter_org_key == key)
            pygame.draw.rect(screen,
                              COLORS.get("legendary", (170, 110, 220))
                              if active else
                              COLORS.get("panel_dark", (40, 40, 56)),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(
                label, True,
                (20, 20, 30) if active else
                COLORS.get("text_main", (220, 220, 235))),
                (chip.x + 7, chip.y + 4))
            self._org_chip_rects.append((chip, key))
            x += w + 4

        # Phase 44 — ego controls (top-right of the filter strip)
        ex = self.rect.right - 320
        ey = self.rect.y + 50
        self.btn_ego.rect.x = ex
        self.btn_ego.rect.y = ey
        self.btn_ego.color = (COLORS.get("legendary", (170, 110, 220))
                                if self.ego_mode
                                else COLORS.get("panel_dark",
                                                  (40, 40, 56)))
        self.btn_ego.draw(screen, mp)
        if self.ego_mode:
            self.btn_depth_down.rect.x = ex + 120
            self.btn_depth_down.rect.y = ey
            self.btn_depth_down.draw(screen, mp)
            screen.blit(fonts.small.render(
                f"{self.ego_depth}", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (ex + 152, ey + 3))
            self.btn_depth_up.rect.x = ex + 166
            self.btn_depth_up.rect.y = ey
            self.btn_depth_up.draw(screen, mp)
            self.btn_ego_full.rect.x = ex + 200
            self.btn_ego_full.rect.y = ey
            self.btn_ego_full.draw(screen, mp)

    def _draw_graph(self, screen, mp):
        if not self.graph:
            return
        ga = self._graph_area()
        prev = screen.get_clip()
        screen.set_clip(ga)
        # Edges first (under nodes)
        node_by_id = {n.id: n for n in self.graph.nodes}
        for e in self.graph.edges:
            a = node_by_id.get(e.source)
            b = node_by_id.get(e.target)
            if not a or not b:
                continue
            col = ng.LINK_KIND_COLOR.get(e.kind, (140, 140, 150))
            pygame.draw.line(screen, col,
                              (int(a.x), int(a.y)),
                              (int(b.x), int(b.y)), 2)
        # Nodes
        hover_node = ng.nearest_node(self.graph, mp[0], mp[1],
                                        max_dist=22)
        self._hover_card.hide()
        for node in self.graph.nodes:
            r = 8 + min(node.degree * 2, 12)
            is_hover = (hover_node is node)
            colour = COLORS.get("player", (110, 180, 240))
            pygame.draw.circle(screen, colour,
                                (int(node.x), int(node.y)), r)
            if is_hover:
                pygame.draw.circle(screen,
                                    COLORS.get("text_bright",
                                                 (240, 240, 250)),
                                    (int(node.x), int(node.y)),
                                    r + 3, 2)
            # Name label
            label = node.name[:16]
            ls = fonts.tiny.render(
                label, True,
                COLORS.get("text_bright", (240, 240, 250)))
            screen.blit(ls, (int(node.x) - ls.get_width() // 2,
                              int(node.y) + r + 2))
        screen.set_clip(prev)

        # Hover card (uses real NPC for full content)
        if hover_node is not None:
            npc = self.world.npcs.get(hover_node.id)
            if npc is not None:
                self._hover_card.show(self.world, npc, self.campaign)

    def _draw_legend(self, screen):
        # Compact legend of edge colours, bottom-left.
        x = self.rect.x + 16
        y = self.rect.bottom - 26
        for kind in ("rival", "ally", "family", "mentor",
                       "patron", "lover"):
            col = ng.LINK_KIND_COLOR.get(kind, (140, 140, 150))
            pygame.draw.rect(screen, col,
                              pygame.Rect(x, y + 4, 12, 4))
            screen.blit(fonts.tiny.render(
                kind, True,
                COLORS.get("text_dim", (180, 180, 195))),
                (x + 16, y))
            x += 16 + fonts.tiny.size(kind)[0] + 14
