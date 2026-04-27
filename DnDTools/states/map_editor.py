"""
MapEditorState — the interactive world/region/town/dungeon map editor.

Full-screen Pygame state that the DM opens from the campaign manager.  Each
editor instance targets exactly one WorldMap (see data/map_engine.py), but can
drill down into linked sub-maps and pop back to the parent with a history
stack.

Layout
------
    ┌──────────────────────────────────────────────────────────────┐
    │  top bar: Back | Map name | Save | Load Image | Grid | Scale │
    ├──────────┬──────────────────────────────────────┬────────────┤
    │          │                                      │            │
    │   TOOL   │              CANVAS                  │  DETAILS   │
    │  PALETTE │    (background image + tiles +       │   PANEL    │
    │          │     annotations + objects)           │  (selected │
    │  object  │                                      │   object)  │
    │  type    │                                      │            │
    ├──────────┴──────────────────────────────────────┴────────────┤
    │  status bar:  tool hint  |  mouse pct  |  measure readout    │
    └──────────────────────────────────────────────────────────────┘

This module holds the core state, camera transforms, background loading,
and the render loop.  Tool event handling, object modals, and the drawing
routines live in companion modules imported at runtime to keep each file
reviewable.  See map_editor_tools.py and map_editor_render.py.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, Panel, TabBar, Tooltip, fonts, draw_gradient_rect
from states.game_state_base import GameState
from data.map_engine import (
    WorldMap, MapObject, AnnotationPath, MAP_OBJECT_TYPES, TERRAIN_BRUSHES,
    DRILLDOWN_TYPES, TOKEN_TYPES, SETTLEMENT_TYPES,
    save_world_map, load_world_map, MAPS_DIR,
)


# ----------------------------------------------------------------------
# Tool identifiers — used both by the palette buttons and the event router.
# ----------------------------------------------------------------------

TOOL_SELECT        = "select"
TOOL_PLACE_OBJECT  = "place_object"
TOOL_PAINT_TILE    = "paint_tile"
TOOL_ERASE_TILE    = "erase_tile"
TOOL_FILL_TILE     = "fill_tile"
TOOL_MEASURE_LINE  = "measure_line"
TOOL_MEASURE_PATH  = "measure_path"
TOOL_DRAW_PATH     = "draw_path"
TOOL_DELETE        = "delete"

TOOLS_ORDER = [
    (TOOL_SELECT,       "Valitse"),
    (TOOL_PLACE_OBJECT, "Lisää objekti"),
    (TOOL_DRAW_PATH,    "Piirrä reitti"),
    (TOOL_MEASURE_LINE, "Mittaa (suora)"),
    (TOOL_MEASURE_PATH, "Mittaa (polku)"),
    (TOOL_PAINT_TILE,   "Maalaa maasto"),
    (TOOL_FILL_TILE,    "Täytä alue"),
    (TOOL_ERASE_TILE,   "Pyyhi maasto"),
    (TOOL_DELETE,       "Poista objekti"),
]


# Default object-type groups for the left-panel picker.
OBJECT_TYPE_GROUPS = [
    ("Asutukset",  ["capital", "city", "town", "village", "fort"]),
    ("Luola/lk.",  ["cave", "dungeon", "portal_down", "portal_up", "ruins"]),
    ("Merkit",     ["info_pin", "quest_marker", "danger_marker", "camp"]),
    ("Aarre/ansa", ["treasure", "trap"]),
    ("Tokenit",    ["party_token", "npc_token", "army_token", "caravan"]),
    ("Rakennuks.", ["temple", "tavern", "shop", "guild", "dock"]),
    ("Luonto",     ["single_tree", "mountain_peak", "volcano"]),
]


# Layout constants — centralise here so render/event modules can reuse them.
TOP_BAR_H      = 48
BOTTOM_BAR_H   = 26
TOOL_PANEL_W   = 220
DETAIL_PANEL_W = 320


def _seg_dist_sq(a, b, p) -> float:
    """Squared distance from point p to segment ab (all 2-tuples)."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx = ax + dx * t
    cy = ay + dy * t
    return (px - cx) ** 2 + (py - cy) ** 2


class MapEditorState(GameState):
    """Interactive world map editor. Initialised by the campaign manager.

    Parameters
    ----------
    manager:
        The GameManager instance.
    world_map:
        The WorldMap currently being edited. Mutated in place; callers hold the
        reference so save/load is transparent.
    campaign, world:
        Optional campaign + world (NPC/location lookup for detail popups).
    back_state:
        Name of the state to return to when the user clicks Back.  Defaults to
        "CAMPAIGN" if a campaign was provided, else "MENU".
    callbacks:
        Optional dict of hooks, e.g. { "open_npc": fn(npc_id),
        "open_location": fn(loc_id), "start_encounter": fn(map_object) }.
        Absent keys fall back to internal stubs.
    """

    def __init__(
        self,
        manager,
        world_map: WorldMap,
        campaign=None,
        world=None,
        back_state: str = "",
        callbacks: Optional[dict] = None,
    ):
        super().__init__(manager)
        self.world_map = world_map
        self.campaign = campaign
        self.world = world
        self.back_state = back_state or ("CAMPAIGN" if campaign else "MENU")
        self.callbacks = callbacks or {}

        # --- Screen geometry --------------------------------------------------
        self._recalc_layout()

        # --- Camera / zoom (world pixels, not percent) ------------------------
        self.camera_x: float = 0.0   # world-pixel offset of canvas top-left
        self.camera_y: float = 0.0
        self.zoom: float = 1.0
        self._dragging_pan = False
        self._pan_anchor: Tuple[int, int] = (0, 0)
        self._pan_cam_start: Tuple[float, float] = (0.0, 0.0)

        # --- Background image -------------------------------------------------
        self._bg_surface: Optional[pygame.Surface] = None
        self._bg_path_loaded: str = ""
        self._load_background()

        # --- Tool state -------------------------------------------------------
        self.tool: str = TOOL_SELECT
        self.active_object_type: str = "city"
        self.active_brush: str = "grass"
        self.brush_radius: int = 0
        self.selected_object_id: str = ""
        self.hover_object_id: str = ""
        self.selected_path_id: str = ""
        self.measure_points: List[Tuple[float, float]] = []   # in world %
        self.draw_points: List[Tuple[float, float]] = []       # in world %
        self._drag_object_id: str = ""
        self._drag_object_offset: Tuple[float, float] = (0.0, 0.0)

        # --- History stack for drill-down (map_id chain) ----------------------
        self._map_history: List[str] = []

        # --- Status text ------------------------------------------------------
        self._status_text: str = ""
        self._status_timer: int = 0

        # --- UI buttons -------------------------------------------------------
        self._build_top_bar_buttons()

        # --- Edit modal (created lazily) --------------------------------------
        self._edit_modal = None

        # --- Kingdoms navigator (lazy) ---------------------------------------
        self._navigator = None
        self.navigator_open = False
        # Phase 11c: drag-onto-map palette (lazily created on first open)
        self._location_palette = None
        self.location_palette_open = False
        # Phase 11b: tool panel scroll state — without this the
        # object-type list silently clips when there are many entries
        # (the user reported "couldn't scroll down at all").
        self.tool_panel_scroll = 0
        self.tool_panel_content_h = 0

        # --- Army-vs-army picker state --------------------------------------
        self.army_pick_mode: bool = False
        self._army_pick_a = None

        # Centre camera on the map by default
        self._center_camera()

    def _get_navigator(self):
        if self._navigator is None:
            from states.map_editor_navigator import KingdomsNavigator
            self._navigator = KingdomsNavigator(self)
        return self._navigator

    def _toggle_navigator(self) -> None:
        self.navigator_open = not self.navigator_open
        if self.navigator_open:
            self._get_navigator()
            self._set_status("Kuningaskunnat auki")

    def _get_location_palette(self):
        if self._location_palette is None:
            from states.location_palette_widget import LocationPaletteWidget
            self._location_palette = LocationPaletteWidget(
                self, on_close=lambda: setattr(
                    self, "location_palette_open", False),
            )
        return self._location_palette

    def toggle_location_palette(self) -> None:
        """Open / close the campaign-locations drag palette
        (Phase 11c)."""
        self.location_palette_open = not self.location_palette_open
        if self.location_palette_open:
            pal = self._get_location_palette()
            pal.open()
            self._set_status("Sijaintipaletti auki — klikkaa lisätäksesi")
        else:
            if self._location_palette is not None:
                self._location_palette.close()

    def open_npc_modal(self, npc_ids) -> None:
        """Open a read-only NPC profile view. Accepts a string or list."""
        if isinstance(npc_ids, str):
            npc_ids = [npc_ids]
        if not npc_ids or self.world is None:
            self._set_status("Ei linkitettyä NPC:tä tai worldia.")
            return
        from states.map_editor_modals import NPCDetailModal

        def _close():
            self._edit_modal = None

        self._edit_modal = NPCDetailModal(self.world, npc_ids, _close)

    # ------------------------------------------------------------------
    def open_advance_time_modal(self) -> None:
        """Open the time-advance modal that moves path-following tokens."""
        from states.map_editor_modals import AdvanceTimeModal

        def _close():
            self._edit_modal = None

        self._edit_modal = AdvanceTimeModal(self, _close)

    # ------------------------------------------------------------------
    # Army-vs-army simulation: two-click picker on the canvas
    # ------------------------------------------------------------------
    def begin_army_battle_pick(self) -> None:
        """Enter a mode where the next two army_token clicks on the canvas
        feed into an abstract army-vs-army Monte Carlo simulation."""
        self.army_pick_mode = True
        self._army_pick_a = None
        self._set_status(
            "Valitse ensimmäinen armeija kartalta (paina ESC peruuttaaksesi)."
        )

    def cancel_army_pick(self) -> None:
        self.army_pick_mode = False
        self._army_pick_a = None
        self._set_status("Armeijavalinta peruttu.")

    def handle_army_pick_click(self, obj) -> bool:
        """Called from the canvas click router when army_pick_mode is on.
        Returns True if the click was consumed."""
        if not self.army_pick_mode:
            return False
        if obj is None or obj.object_type != "army_token" or not obj.unit_type:
            self._set_status("Napsauta armeijan yksikköä (army_token).")
            return True
        if self._army_pick_a is None:
            self._army_pick_a = obj
            self._set_status(
                f"Ensimmäinen valittu: {obj.label or obj.unit_type}. "
                "Valitse vastustaja."
            )
            return True
        if obj.id == self._army_pick_a.id:
            self._set_status("Valitse eri kohde vastustajaksi.")
            return True
        self._open_army_battle(self._army_pick_a, obj)
        self.army_pick_mode = False
        self._army_pick_a = None
        return True

    def _open_army_battle(self, obj_a, obj_b) -> None:
        from data.army_sim import army_from_map_object
        from states.map_editor_army_modal import ArmyBattleModal
        from data.library import library

        army_a = army_from_map_object(obj_a, library=library)
        army_b = army_from_map_object(obj_b, library=library)
        if army_a is None or army_b is None:
            self._set_status(
                "Yksikkötyyppiä ei löydy kirjastosta — tarkista unit_type."
            )
            return

        def _close():
            self._edit_modal = None

        self._edit_modal = ArmyBattleModal(army_a, army_b, _close)
        self._set_status(
            f"Simulaatio: {army_a.name} vs {army_b.name}"
        )

    # ================================================================
    # Layout
    # ================================================================
    def _recalc_layout(self) -> None:
        self.screen_w = SCREEN_WIDTH
        self.screen_h = SCREEN_HEIGHT
        self.top_bar_rect    = pygame.Rect(0, 0, self.screen_w, TOP_BAR_H)
        self.bottom_bar_rect = pygame.Rect(0, self.screen_h - BOTTOM_BAR_H,
                                           self.screen_w, BOTTOM_BAR_H)
        self.tool_panel_rect = pygame.Rect(
            0, TOP_BAR_H, TOOL_PANEL_W,
            self.screen_h - TOP_BAR_H - BOTTOM_BAR_H,
        )
        self.detail_panel_rect = pygame.Rect(
            self.screen_w - DETAIL_PANEL_W, TOP_BAR_H, DETAIL_PANEL_W,
            self.screen_h - TOP_BAR_H - BOTTOM_BAR_H,
        )
        self.canvas_rect = pygame.Rect(
            TOOL_PANEL_W, TOP_BAR_H,
            self.screen_w - TOOL_PANEL_W - DETAIL_PANEL_W,
            self.screen_h - TOP_BAR_H - BOTTOM_BAR_H,
        )

    # ================================================================
    # Background image
    # ================================================================
    def _load_background(self) -> None:
        """Load the map's background_image (if any). Downsamples huge images
        so memory/FPS stay sane on 8k+ Inkarnate exports."""
        self._bg_surface = None
        path = self.world_map.background_image
        if not path:
            return
        resolved = self._resolve_image_path(path)
        if not resolved or not os.path.isfile(resolved):
            logging.warning(f"[MAP_EDITOR] Background image not found: {path}")
            self._set_status(f"Taustakuvaa ei löydy: {os.path.basename(path)}")
            return
        try:
            raw = pygame.image.load(resolved).convert()
            # Cap at 6144 on longest side for perf.
            w, h = raw.get_size()
            max_dim = 6144
            if max(w, h) > max_dim:
                scale = max_dim / max(w, h)
                raw = pygame.transform.smoothscale(
                    raw, (int(w * scale), int(h * scale))
                )
            self._bg_surface = raw
            self._bg_path_loaded = path
            self._set_status(f"Taustakuva ladattu: {os.path.basename(path)}")
        except Exception as ex:
            logging.warning(f"[MAP_EDITOR] Image load failed: {ex}")
            self._set_status(f"Kuvan lataus epäonnistui: {ex}")

    @staticmethod
    def _resolve_image_path(path: str) -> str:
        if os.path.isabs(path) and os.path.isfile(path):
            return path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base_dir, path)
        return candidate if os.path.isfile(candidate) else ""

    # ----------------------------------------------------------------
    # World dimensions — pixels in the map's native coordinate system
    # ----------------------------------------------------------------
    def world_size_px(self) -> Tuple[int, int]:
        """Return (width, height) of the logical world in pixels.  Falls back
        to map.width*tile_size when no background image is loaded."""
        if self._bg_surface is not None:
            return self._bg_surface.get_size()
        return (
            self.world_map.width * self.world_map.tile_size,
            self.world_map.height * self.world_map.tile_size,
        )

    def _center_camera(self) -> None:
        ww, wh = self.world_size_px()
        cw = max(1, self.canvas_rect.width)
        ch = max(1, self.canvas_rect.height)
        # Fit whole map on screen at initial zoom
        self.zoom = min(cw / ww, ch / wh) if ww and wh else 1.0
        self.zoom = max(0.05, min(5.0, self.zoom))
        self.camera_x = (ww - cw / self.zoom) / 2
        self.camera_y = (wh - ch / self.zoom) / 2

    # ================================================================
    # Coordinate transforms
    # ================================================================
    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        sx = self.canvas_rect.x + (wx - self.camera_x) * self.zoom
        sy = self.canvas_rect.y + (wy - self.camera_y) * self.zoom
        return int(sx), int(sy)

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        wx = (sx - self.canvas_rect.x) / self.zoom + self.camera_x
        wy = (sy - self.canvas_rect.y) / self.zoom + self.camera_y
        return wx, wy

    def pct_to_world(self, x_pct: float, y_pct: float) -> Tuple[float, float]:
        ww, wh = self.world_size_px()
        return (x_pct / 100.0 * ww, y_pct / 100.0 * wh)

    def world_to_pct(self, wx: float, wy: float) -> Tuple[float, float]:
        ww, wh = self.world_size_px()
        return (wx / max(1, ww) * 100.0, wy / max(1, wh) * 100.0)

    def screen_to_pct(self, sx: int, sy: int) -> Tuple[float, float]:
        return self.world_to_pct(*self.screen_to_world(sx, sy))

    def pct_to_screen(self, x_pct: float, y_pct: float) -> Tuple[int, int]:
        return self.world_to_screen(*self.pct_to_world(x_pct, y_pct))

    # ================================================================
    # Distance in miles (aspect-aware)
    # ================================================================
    def distance_miles(
        self, a_pct: Tuple[float, float], b_pct: Tuple[float, float]
    ) -> float:
        """Convert a straight-line %-distance to miles using the map scale.
        %y is rescaled by (height/width) so the metric is isotropic."""
        ww, wh = self.world_size_px()
        aspect = (wh / ww) if ww else 1.0
        dx = a_pct[0] - b_pct[0]
        dy = (a_pct[1] - b_pct[1]) * aspect
        d_pct = math.hypot(dx, dy)
        return d_pct * max(self.world_map.scale_miles_per_pct, 0.0)

    def travel_days(self, miles: float) -> float:
        spd = self.world_map.travel_speed_miles_per_day or 1.0
        return miles / spd

    def path_length_miles(self, points: List[Tuple[float, float]]) -> float:
        """Aspect-aware polyline length in miles.  Sums segment distances in
        % space after rescaling y by (h/w) before applying the map scale."""
        if len(points) < 2:
            return 0.0
        ww, wh = self.world_size_px()
        aspect = (wh / ww) if ww else 1.0
        scale = max(self.world_map.scale_miles_per_pct, 0.0)
        total = 0.0
        for i in range(1, len(points)):
            dx = points[i][0] - points[i - 1][0]
            dy = (points[i][1] - points[i - 1][1]) * aspect
            total += math.hypot(dx, dy)
        return total * scale

    # ================================================================
    # Top bar buttons
    # ================================================================
    def _build_top_bar_buttons(self) -> None:
        x = 8
        y = 8
        btn_h = TOP_BAR_H - 16

        def mk(label, w, fn, colour=None):
            nonlocal x
            b = Button(x, y, w, btn_h, label, fn, color=colour or COLORS["panel_light"])
            x += w + 6
            return b

        self.btn_back     = mk("< Takaisin", 110, self._on_back)
        self.btn_save     = mk("Tallenna",   100, self._on_save, COLORS["success"])
        self.btn_load_img = mk("Taustakuva", 130, self._on_load_image)
        self.btn_grid     = mk("Ruudukko",    95, self._on_toggle_grid)
        self.btn_scale    = mk("Mittakaava", 110, self._on_edit_scale)
        self.btn_layers   = mk("Kerrokset",  110, self._on_cycle_layer)
        self.btn_parent   = mk("^ Ylös",      90, self._on_go_parent)
        self.btn_nav      = mk("Kuningaskunnat", 150, self._toggle_navigator)
        self.btn_palette  = mk("Sijainnit", 110, self.toggle_location_palette)
        self.btn_army_sim = mk("Simuloi armeijat", 160, self.begin_army_battle_pick,
                                COLORS["warning"])
        self.btn_advance  = mk("Edistä päivä", 130, self.open_advance_time_modal,
                                COLORS["accent"])
        # Parent button only enabled if we have history or parent_map_id
        self._refresh_parent_button()

    def _refresh_parent_button(self) -> None:
        has_parent = bool(self._map_history) or bool(self.world_map.parent_map_id)
        self.btn_parent.enabled = has_parent

    # ================================================================
    # Button handlers
    # ================================================================
    def _on_back(self) -> None:
        # Auto-save then switch state.
        try:
            save_world_map(self.world_map)
        except Exception as ex:
            logging.warning(f"[MAP_EDITOR] Autosave on exit failed: {ex}")
        self.manager.change_state(self.back_state, campaign=self.campaign)

    def _on_save(self) -> None:
        try:
            path = save_world_map(self.world_map)
            self._set_status(f"Tallennettu: {os.path.basename(path)}")
        except Exception as ex:
            self._set_status(f"Tallennus epäonnistui: {ex}")

    def _on_load_image(self) -> None:
        from states.campaign_manager import CampaignManagerState
        # Reuse picker/import utilities from campaign manager
        src = CampaignManagerState._pick_image_file(self)
        if not src:
            return
        rel = CampaignManagerState._import_map_image(self, src)
        if not rel:
            self._set_status("Kuvan tuonti epäonnistui")
            return
        self.world_map.background_image = rel
        self._load_background()
        self._center_camera()

    def _on_toggle_grid(self) -> None:
        self.world_map.grid_visible = not self.world_map.grid_visible

    def _on_edit_scale(self) -> None:
        # Quick inline cycle of presets — richer UI comes with the modal system.
        current = self.world_map.scale_miles_per_pct
        presets = [0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 50.0]
        try:
            idx = presets.index(current)
            self.world_map.scale_miles_per_pct = presets[(idx + 1) % len(presets)]
        except ValueError:
            self.world_map.scale_miles_per_pct = presets[0]
        self._set_status(
            f"Mittakaava: {self.world_map.scale_miles_per_pct} mi / 1% leveys"
        )

    def _on_cycle_layer(self) -> None:
        n = len(self.world_map.layers)
        if n <= 1:
            return
        self.world_map.active_layer_idx = (self.world_map.active_layer_idx + 1) % n
        layer = self.world_map.active_layer
        self._set_status(f"Aktiivinen kerros: {layer.name}")

    def _on_go_parent(self) -> None:
        # Drill-up: history has priority, parent_map_id is the fallback.
        target = ""
        if self._map_history:
            target = self._map_history.pop()
        elif self.world_map.parent_map_id:
            target = self.world_map.parent_map_id
        if target:
            self._switch_to_map_by_id(target, push_history=False)
        self._refresh_parent_button()

    # ================================================================
    # Map navigation (drill-down)
    # ================================================================
    def open_linked_map(self, obj: MapObject) -> None:
        """Follow obj.linked_map_id into a sub-map, pushing current id onto
        the history stack so the '^' button can pop back."""
        target = obj.linked_map_id
        if not target:
            self._set_status(f"{obj.label or obj.object_type}: ei linkitettyä karttaa")
            return
        self._switch_to_map_by_id(target, push_history=True)

    def _switch_to_map_by_id(self, map_id: str, *, push_history: bool) -> None:
        from data.map_engine import MAPS_DIR
        candidate = os.path.join(MAPS_DIR, f"{map_id}.json")
        if not os.path.isfile(candidate):
            self._set_status(f"Karttaa ei löydy: {map_id}")
            return
        try:
            new_map = load_world_map(candidate)
        except Exception as ex:
            self._set_status(f"Kartan lataus epäonnistui: {ex}")
            return
        # Save current, remember it on the history stack
        try:
            save_world_map(self.world_map)
        except Exception:
            pass
        if push_history:
            self._map_history.append(self.world_map.id)
        self.world_map = new_map
        self.selected_object_id = ""
        self._load_background()
        self._center_camera()
        self._refresh_parent_button()
        if self.campaign is not None:
            self.campaign.active_map_id = new_map.id
        self._set_status(f"Avattu kartta: {new_map.name}")

    # ================================================================
    # Object picking — used by Select/Delete/Drag/Hover
    # ================================================================
    def _object_screen_radius(self, obj: MapObject) -> int:
        # Objects render at roughly 14px * size * zoom, clamped.
        r = max(8, int(14 * obj.size * min(self.zoom, 3.0)))
        return r

    def object_at_screen(self, sx: int, sy: int) -> Optional[MapObject]:
        """Top-most object under the cursor (iterates layers back-to-front)."""
        for layer in reversed(self.world_map.layers):
            if not layer.visible:
                continue
            for obj in reversed(layer.objects):
                # Skip DM-hidden marker? For the editor we always show.
                owx, owy = self.pct_to_world(obj.x, obj.y)
                osx, osy = self.world_to_screen(owx, owy)
                r = self._object_screen_radius(obj)
                if (sx - osx) ** 2 + (sy - osy) ** 2 <= r * r:
                    return obj
        return None

    def annotation_at_screen(self, sx: int, sy: int, tolerance_px: int = 6):
        """Return the AnnotationPath whose polyline passes within tolerance_px
        of the cursor, or None."""
        best = None
        best_d2 = tolerance_px * tolerance_px
        for path in self.world_map.annotations:
            pts_screen = []
            for px, py in path.points:
                wx, wy = self.pct_to_world(px, py)
                pts_screen.append(self.world_to_screen(wx, wy))
            for i in range(1, len(pts_screen)):
                d2 = _seg_dist_sq(pts_screen[i - 1], pts_screen[i], (sx, sy))
                if d2 < best_d2:
                    best_d2 = d2
                    best = path
        return best

    # ================================================================
    # Encounter launch from a map token
    # ================================================================
    def start_encounter_from_object(self, obj: MapObject) -> bool:
        """Build a battle roster and jump into BattleState.

        Sources tried, in priority order:
          1. ``callbacks["start_encounter"]`` — host override
          2. ``obj.linked_encounter_id`` — name match against the campaign's
             saved encounters; the matching encounter's slots are used
          3. ``obj.unit_type`` + ``unit_count`` — ad-hoc horde built from the
             monster library

        Returns True if an encounter actually launched.
        """
        cb = self.callbacks.get("start_encounter")
        if cb:
            try:
                cb(obj)
                return True
            except Exception as ex:
                logging.warning(f"[MAP_EDITOR] start_encounter callback failed: {ex}")
                return False

        if self.campaign is None:
            self._set_status("Encounter vaatii kampanjan.")
            return False

        slots = self._resolve_encounter_slots(obj)
        if not slots:
            self._set_status(
                f"{obj.label or obj.object_type}: ei encounteria tai yksikköä."
            )
            return False

        # Save current map before leaving (auto-resume when battle finishes)
        try:
            save_world_map(self.world_map)
        except Exception:
            pass

        roster = self._build_roster_from_slots(slots)
        if not roster:
            self._set_status("Ei kelvollista taistelijaa rosteriin.")
            return False

        # Open placement modal; battle launches from its confirm callback.
        from states.map_editor_placement import PreBattleSetupModal

        def _launch():
            self._edit_modal = None
            from states.game_states import BattleState
            bs = BattleState(self.manager, roster)
            self.manager.states["BATTLE"] = bs
            self.manager.change_state("BATTLE")
            self._set_status(f"Taistelu alkoi: {obj.label or obj.object_type}")

        def _cancel():
            self._edit_modal = None
            self._set_status("Taistelu peruttu.")

        self._edit_modal = PreBattleSetupModal(
            self.manager, roster, _launch, _cancel
        )
        return True

    def _resolve_encounter_slots(self, obj: MapObject):
        """Return a list of (name, count, side, is_hero) tuples or []."""
        # Match saved encounter by free-text id/name
        eid = (obj.linked_encounter_id or "").strip().lower()
        if eid:
            for enc in self.campaign.encounters:
                if enc.name.strip().lower() == eid:
                    return [(s.creature_name, s.count, s.side, s.is_hero)
                            for s in enc.slots]
        # Ad-hoc unit horde
        if obj.unit_type and obj.unit_count > 0:
            side = "enemy"
            if obj.object_type in ("party_token",) or (
                obj.faction and obj.faction.lower() in ("party", "ally", "allies")
            ):
                side = "ally"
            return [(obj.unit_type, int(obj.unit_count), side, False)]
        return []

    def _build_roster_from_slots(self, slots) -> list:
        """Reuse library.get_monster to assemble an Entity roster including
        the current party."""
        from engine.entities import Entity
        from data.library import library
        from data.hero_import import import_hero
        import copy as _copy

        roster = []
        # Party
        px, py = 3, 2
        for member in self.campaign.party:
            if not getattr(member, "active", True):
                continue
            try:
                stats = import_hero(member.hero_data)
            except Exception:
                continue
            ent = Entity(stats, px, py, is_player=True)
            if getattr(member, "current_hp", -1) >= 0:
                ent.hp = member.current_hp
            if getattr(member, "temp_hp", 0):
                ent.temp_hp = member.temp_hp
            for cond in getattr(member, "conditions", []) or []:
                ent.add_condition(cond)
            ent.exhaustion = getattr(member, "exhaustion", 0)
            roster.append(ent)
            py += 2

        # Opposition / allies from slots — auto-place far side of the grid
        ex, ey = 14, 3
        for name, count, side, is_hero in slots:
            if is_hero:
                continue
            for i in range(max(1, int(count))):
                try:
                    stats = _copy.deepcopy(library.get_monster(name))
                except Exception:
                    continue
                if count > 1:
                    stats.name = f"{name} {i + 1}"
                ent = Entity(stats, ex, ey, is_player=(side == "ally"))
                roster.append(ent)
                ey += 2
                if ey > 15:
                    ey = 3
                    ex += 2
        return roster

    # ================================================================
    # Status helper
    # ================================================================
    def _set_status(self, text: str, ttl: int = 180) -> None:
        self._status_text = text
        self._status_timer = ttl

    # ================================================================
    # Lifecycle — event loop entry points
    # ================================================================
    def handle_events(self, events) -> None:
        # Defer to the companion event router so this file stays readable.
        from states.map_editor_tools import route_events
        route_events(self, events)

    def update(self) -> None:
        if self._status_timer > 0:
            self._status_timer -= 1

        # Phase 11d: WASD / arrow keys pan the canvas while the user
        # is NOT typing in a search/text field. Keeps zoom unchanged.
        try:
            keys = pygame.key.get_pressed()
        except pygame.error:
            return
        # Don't steal keystrokes from search fields
        if self._navigator is not None and self._navigator.search_active:
            return
        if (self._location_palette is not None
                and self._location_palette.is_open
                and self._location_palette.search_active):
            return
        # Pan speed scales with zoom so it feels consistent
        pan = 12.0 / max(self.zoom, 0.1)
        dx = dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= pan
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += pan
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= pan
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            # Ctrl+S is save; ignore S while Ctrl held
            if not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                dy += pan
        if dx or dy:
            self.camera_x += dx
            self.camera_y += dy

    def draw(self, screen) -> None:
        from states.map_editor_render import render_editor
        render_editor(self, screen)
