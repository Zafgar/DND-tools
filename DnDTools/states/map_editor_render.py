"""
MapEditorState — all rendering logic.

Separated from the main state class so map_editor.py stays at a reviewable
size.  Every function here reads from `state` but never mutates map data.
"""
from __future__ import annotations

import math
from typing import List, Tuple

import pygame

from settings import COLORS
from ui.components import fonts, Button, Tooltip, draw_gradient_rect
from data.map_engine import TERRAIN_BRUSHES, MAP_OBJECT_TYPES, TOKEN_TYPES
from states.map_editor import (
    TOOL_SELECT, TOOL_PLACE_OBJECT, TOOL_PAINT_TILE, TOOL_ERASE_TILE,
    TOOL_FILL_TILE, TOOL_MEASURE_LINE, TOOL_MEASURE_PATH, TOOL_DRAW_PATH,
    TOOL_DELETE, TOOLS_ORDER, OBJECT_TYPE_GROUPS,
    TOP_BAR_H, BOTTOM_BAR_H, TOOL_PANEL_W, DETAIL_PANEL_W,
)


def render_editor(state, screen) -> None:
    screen.fill(COLORS["bg"])
    _draw_canvas(state, screen)
    _draw_top_bar(state, screen)
    _draw_tool_panel(state, screen)
    if state.navigator_open and state._navigator is not None:
        state._navigator.draw(screen)
    else:
        _draw_detail_panel(state, screen)
    _draw_bottom_bar(state, screen)
    _draw_hover_tooltip(state, screen)
    if state._edit_modal is not None:
        state._edit_modal.draw(screen)


# ================================================================
# Canvas — background image, tiles, annotations, objects
# ================================================================

def _draw_canvas(state, screen) -> None:
    screen.set_clip(state.canvas_rect)
    pygame.draw.rect(screen, (16, 16, 22), state.canvas_rect)

    # Background image (scaled by zoom)
    if state._bg_surface is not None:
        _draw_background_image(state, screen)
    else:
        # Solid background colour from the active layer
        col = state.world_map.active_layer.background_color
        pygame.draw.rect(screen, col, state.canvas_rect)

    _draw_tile_layers(state, screen)
    if state.world_map.grid_visible:
        _draw_grid(state, screen)
    _draw_annotations(state, screen)
    _draw_in_progress_paths(state, screen)
    _draw_objects(state, screen)
    screen.set_clip(None)

    pygame.draw.rect(screen, COLORS["border"], state.canvas_rect, 1)


def _draw_background_image(state, screen) -> None:
    bg = state._bg_surface
    ww, wh = bg.get_size()
    sx, sy = state.world_to_screen(0, 0)
    new_w = max(1, int(ww * state.zoom))
    new_h = max(1, int(wh * state.zoom))
    # Scale lazily, keep cache by zoom level for perf.
    key = (new_w, new_h)
    if getattr(state, "_bg_cache_key", None) != key:
        try:
            state._bg_cache = pygame.transform.smoothscale(bg, key)
        except pygame.error:
            state._bg_cache = pygame.transform.scale(bg, key)
        state._bg_cache_key = key
    screen.blit(state._bg_cache, (sx, sy))


def _draw_tile_layers(state, screen) -> None:
    for li, layer in enumerate(state.world_map.layers):
        if not layer.visible or not layer.tiles:
            continue
        alpha = int(layer.opacity * 255)
        ww, wh = state.world_size_px()
        tile_w_px = ww / max(1, state.world_map.width)
        tile_h_px = wh / max(1, state.world_map.height)
        for key, brush_key in layer.tiles.items():
            try:
                tx, ty = map(int, key.split(","))
            except ValueError:
                continue
            brush = TERRAIN_BRUSHES.get(brush_key)
            if not brush:
                continue
            wx = tx * tile_w_px
            wy = ty * tile_h_px
            sx, sy = state.world_to_screen(wx, wy)
            sw = max(1, int(tile_w_px * state.zoom) + 1)
            sh = max(1, int(tile_h_px * state.zoom) + 1)
            colour = (*brush["color"], alpha) if alpha < 255 else brush["color"]
            if alpha < 255:
                surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
                surf.fill(colour)
                screen.blit(surf, (sx, sy))
            else:
                pygame.draw.rect(screen, colour, (sx, sy, sw, sh))


def _draw_grid(state, screen) -> None:
    ww, wh = state.world_size_px()
    tw = ww / max(1, state.world_map.width)
    th = wh / max(1, state.world_map.height)
    # Skip grid lines that'd be denser than 6px on screen (too noisy)
    if tw * state.zoom < 6 or th * state.zoom < 6:
        return
    col = state.world_map.grid_color
    for i in range(state.world_map.width + 1):
        sx, sy = state.world_to_screen(i * tw, 0)
        ex, ey = state.world_to_screen(i * tw, wh)
        pygame.draw.line(screen, col, (sx, sy), (ex, ey), 1)
    for j in range(state.world_map.height + 1):
        sx, sy = state.world_to_screen(0, j * th)
        ex, ey = state.world_to_screen(ww, j * th)
        pygame.draw.line(screen, col, (sx, sy), (ex, ey), 1)


def _draw_annotations(state, screen) -> None:
    for path in state.world_map.annotations:
        pts = [state.pct_to_screen(x, y) for (x, y) in path.points]
        if len(pts) < 2:
            continue
        if path.id == state.selected_path_id:
            # Glow halo around the selected route
            pygame.draw.lines(screen, (255, 255, 160), False, pts,
                              max(3, path.thickness + 4))
        if path.dashed:
            _draw_dashed_polyline(screen, path.color, pts, path.thickness)
        else:
            pygame.draw.lines(screen, path.color, False, pts, max(1, path.thickness))


def _draw_in_progress_paths(state, screen) -> None:
    # Measure tool
    if state.measure_points:
        pts = [state.pct_to_screen(x, y) for (x, y) in state.measure_points]
        mp = pygame.mouse.get_pos()
        # Draw current segments
        if len(pts) >= 2:
            pygame.draw.lines(screen, (255, 220, 90), False, pts, 2)
        # Rubber-band from last to cursor
        if state.canvas_rect.collidepoint(mp):
            pygame.draw.line(screen, (255, 220, 90, 180), pts[-1], mp, 1)
        # Endpoint dots
        for p in pts:
            pygame.draw.circle(screen, (255, 220, 90), p, 4)

    # Draw-path tool
    if state.draw_points:
        pts = [state.pct_to_screen(x, y) for (x, y) in state.draw_points]
        if len(pts) >= 2:
            pygame.draw.lines(screen, (120, 220, 255), False, pts, 3)
        mp = pygame.mouse.get_pos()
        if state.canvas_rect.collidepoint(mp):
            pygame.draw.line(screen, (120, 220, 255), pts[-1], mp, 2)
        for p in pts:
            pygame.draw.circle(screen, (120, 220, 255), p, 3)


def _draw_dashed_polyline(screen, colour, pts, thickness) -> None:
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dist = math.hypot(dx, dy)
        if dist <= 0:
            continue
        segs = int(dist // 12) + 1
        for s in range(segs):
            t0 = s / segs
            t1 = (s + 0.55) / segs
            p0 = (int(a[0] + dx * t0), int(a[1] + dy * t0))
            p1 = (int(a[0] + dx * t1), int(a[1] + dy * t1))
            pygame.draw.line(screen, colour, p0, p1, thickness)


def _draw_objects(state, screen) -> None:
    for layer in state.world_map.layers:
        if not layer.visible:
            continue
        for obj in layer.objects:
            _draw_single_object(state, screen, obj)


def _draw_single_object(state, screen, obj) -> None:
    sx, sy = state.pct_to_screen(obj.x, obj.y)
    r = state._object_screen_radius(obj)
    is_selected = obj.id == state.selected_object_id
    is_hover    = obj.id == state.hover_object_id

    col = obj.color
    # Glow for selected/hover
    if is_selected:
        glow = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*COLORS["accent"], 120), (r * 3 // 2, r * 3 // 2), r + 4)
        screen.blit(glow, (sx - r * 3 // 2, sy - r * 3 // 2))

    # Token vs. pin look
    if obj.object_type in TOKEN_TYPES:
        pygame.draw.circle(screen, col, (sx, sy), r)
        pygame.draw.circle(screen, (20, 20, 30), (sx, sy), r, 2)
    else:
        pygame.draw.circle(screen, col, (sx, sy), r)
        pygame.draw.circle(screen, (20, 20, 30), (sx, sy), r, 1)

    # DM-only marker
    if obj.dm_only or obj.hidden:
        pygame.draw.circle(screen, (220, 80, 80), (sx + r - 2, sy - r + 2), 3)

    # Icon glyph
    icon = obj.icon or MAP_OBJECT_TYPES.get(obj.object_type, {}).get("icon", "")
    if icon:
        txt = fonts.small_bold.render(icon[:2], True, (20, 20, 30))
        screen.blit(txt, txt.get_rect(center=(sx, sy)))

    # Hover ring
    if is_hover and not is_selected:
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy), r + 3, 1)

    # Label under object (only if zoom enough)
    if obj.label and state.zoom >= 0.4:
        lbl = fonts.tiny.render(obj.label, True, COLORS["text_bright"])
        lbl_bg = pygame.Rect(sx - lbl.get_width() // 2 - 4,
                             sy + r + 2, lbl.get_width() + 8, lbl.get_height() + 2)
        bg = pygame.Surface((lbl_bg.width, lbl_bg.height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, lbl_bg.topleft)
        screen.blit(lbl, (lbl_bg.x + 4, lbl_bg.y + 1))


# ================================================================
# Top bar
# ================================================================

def _draw_top_bar(state, screen) -> None:
    pygame.draw.rect(screen, COLORS["panel_dark"], state.top_bar_rect)
    pygame.draw.line(screen, COLORS["border"],
                     (0, TOP_BAR_H), (state.screen_w, TOP_BAR_H))
    mp = pygame.mouse.get_pos()
    for btn in (state.btn_back, state.btn_save, state.btn_load_img,
                state.btn_grid, state.btn_scale, state.btn_layers,
                state.btn_parent, state.btn_nav):
        btn.draw(screen, mp)
    # Map name
    name = f"{state.world_map.name}  ({state.world_map.map_type})"
    lbl = fonts.header.render(name, True, COLORS["text_bright"])
    screen.blit(lbl, (state.screen_w - DETAIL_PANEL_W - lbl.get_width() - 12, 10))


# ================================================================
# Tool panel (left)
# ================================================================

def _draw_tool_panel(state, screen) -> None:
    rect = state.tool_panel_rect
    pygame.draw.rect(screen, COLORS["panel_dark"], rect)
    pygame.draw.line(screen, COLORS["border"], (rect.right, rect.y),
                     (rect.right, rect.bottom))
    py = rect.y + 8
    mp = pygame.mouse.get_pos()
    for i, (key, label) in enumerate(TOOLS_ORDER):
        row = pygame.Rect(rect.x + 8, py + i * 32, rect.width - 16, 28)
        is_active = state.tool == key
        is_hover  = row.collidepoint(mp)
        bg = COLORS["accent_dim"] if is_active else (COLORS["hover"] if is_hover else COLORS["panel"])
        pygame.draw.rect(screen, bg, row, border_radius=4)
        if is_active:
            pygame.draw.rect(screen, COLORS["accent"], row, 1, border_radius=4)
        lbl = fonts.body.render(label, True, COLORS["text_bright"])
        screen.blit(lbl, (row.x + 8, row.y + 4))

    section_y = py + len(TOOLS_ORDER) * 32 + 16
    if state.tool == TOOL_PLACE_OBJECT:
        _draw_object_picker(state, screen, section_y)
    elif state.tool in (TOOL_PAINT_TILE, TOOL_FILL_TILE):
        _draw_brush_picker(state, screen, section_y)


def _draw_object_picker(state, screen, start_y) -> None:
    rect = state.tool_panel_rect
    yy = start_y
    hdr = fonts.small_bold.render("Objektityypit", True, COLORS["text_dim"])
    screen.blit(hdr, (rect.x + 8, yy - 16))
    for group_name, keys in OBJECT_TYPE_GROUPS:
        grp = fonts.tiny.render(group_name, True, COLORS["text_dim"])
        screen.blit(grp, (rect.x + 10, yy + 3))
        yy += 20
        for key in keys:
            row = pygame.Rect(rect.x + 12, yy, rect.width - 24, 22)
            is_active = state.active_object_type == key
            bg = COLORS["selected"] if is_active else COLORS["panel"]
            pygame.draw.rect(screen, bg, row, border_radius=3)
            proto = MAP_OBJECT_TYPES.get(key, {})
            pygame.draw.circle(screen, proto.get("color", (200, 200, 200)),
                               (row.x + 10, row.y + 11), 6)
            name = fonts.tiny.render(key.replace("_", " "), True, COLORS["text_main"])
            screen.blit(name, (row.x + 22, row.y + 4))
            yy += 24
        yy += 6


def _draw_brush_picker(state, screen, start_y) -> None:
    rect = state.tool_panel_rect
    yy = start_y
    hdr = fonts.small_bold.render(
        f"Sivellin (koko {state.brush_radius * 2 + 1})",
        True, COLORS["text_dim"])
    screen.blit(hdr, (rect.x + 8, yy - 16))
    for key, spec in TERRAIN_BRUSHES.items():
        row = pygame.Rect(rect.x + 12, yy, rect.width - 24, 20)
        is_active = state.active_brush == key
        bg = COLORS["selected"] if is_active else COLORS["panel"]
        pygame.draw.rect(screen, bg, row, border_radius=3)
        pygame.draw.rect(screen, spec["color"],
                         (row.x + 4, row.y + 3, 14, 14))
        name = fonts.tiny.render(key, True, COLORS["text_main"])
        screen.blit(name, (row.x + 24, row.y + 3))
        yy += 22


# ================================================================
# Detail panel (right)
# ================================================================

def _draw_detail_panel(state, screen) -> None:
    rect = state.detail_panel_rect
    pygame.draw.rect(screen, COLORS["panel_dark"], rect)
    pygame.draw.line(screen, COLORS["border"], (rect.x, rect.y),
                     (rect.x, rect.bottom))

    obj = None
    if state.selected_object_id:
        obj = state.world_map.find_object(state.selected_object_id)
    if obj is None:
        # Prefer path summary when a path is selected, else the map overview
        if state.selected_path_id:
            path = next(
                (p for p in state.world_map.annotations
                 if p.id == state.selected_path_id),
                None,
            )
            if path is not None:
                _draw_path_summary(state, screen, path)
                return
        _draw_map_summary(state, screen)
        return

    y = rect.y + 10
    x = rect.x + 12
    hdr = fonts.header.render(obj.label or obj.object_type, True, COLORS["text_bright"])
    screen.blit(hdr, (x, y)); y += hdr.get_height() + 2
    typ = fonts.small.render(f"Tyyppi: {obj.object_type}", True, COLORS["text_dim"])
    screen.blit(typ, (x, y)); y += 20
    pos = fonts.tiny.render(f"({obj.x:.1f}%, {obj.y:.1f}%)", True, COLORS["text_dim"])
    screen.blit(pos, (x, y)); y += 18

    if obj.hover_info:
        y = _draw_wrapped_text(screen, "Hover:", obj.hover_info,
                               x, y, rect.width - 24, fonts.small)

    if obj.notes:
        y = _draw_wrapped_text(screen, "Muistiinpanot:", obj.notes,
                               x, y, rect.width - 24, fonts.small)

    # Links summary
    y += 4
    if obj.linked_map_id:
        s = fonts.small.render(f"→ Kartta: {obj.linked_map_id}",
                               True, (120, 200, 255))
        screen.blit(s, (x, y)); y += 18
    if obj.linked_location_id:
        s = fonts.small.render(f"→ Paikka: {obj.linked_location_id}",
                               True, (255, 200, 120))
        screen.blit(s, (x, y)); y += 18
    if obj.linked_npc_ids:
        s = fonts.small.render(f"→ NPCt: {len(obj.linked_npc_ids)} linkitetty",
                               True, (180, 220, 255))
        screen.blit(s, (x, y)); y += 18
    if obj.linked_encounter_id:
        s = fonts.small.render(f"→ Encounter: {obj.linked_encounter_id}",
                               True, (255, 150, 150))
        screen.blit(s, (x, y)); y += 18

    if obj.unit_count > 0:
        s = fonts.small.render(
            f"Joukko: {obj.unit_count} × {obj.unit_type or '-'}  ({obj.faction})",
            True, (230, 170, 170))
        screen.blit(s, (x, y)); y += 18
    if obj.treasure_items or obj.treasure_gold > 0:
        s = fonts.small.render(
            f"Aarre: {obj.treasure_gold:.0f} gp, {len(obj.treasure_items)} esinettä",
            True, (255, 220, 100))
        screen.blit(s, (x, y)); y += 18
    if obj.trap_save:
        s = fonts.small.render(f"Ansa: {obj.trap_save}  Vah: {obj.trap_damage}",
                               True, (230, 140, 90))
        screen.blit(s, (x, y)); y += 18
        if obj.lockpick_dc or obj.detect_dc:
            s = fonts.tiny.render(
                f"Tiirikka DC {obj.lockpick_dc}   Havainto DC {obj.detect_dc}",
                True, COLORS["text_dim"])
            screen.blit(s, (x, y)); y += 16

    hint = fonts.tiny.render(
        "Oikea klikkaus = muokkaa  |  Tuplaklikkaus = avaa linkki  |  Del = poista",
        True, COLORS["text_dim"])
    screen.blit(hint, (x, rect.bottom - 22))


def _draw_map_summary(state, screen) -> None:
    rect = state.detail_panel_rect
    x = rect.x + 12
    y = rect.y + 10
    hdr = fonts.header.render("Kartta", True, COLORS["text_bright"])
    screen.blit(hdr, (x, y)); y += hdr.get_height() + 4

    info_lines = [
        f"Nimi: {state.world_map.name}",
        f"Tyyppi: {state.world_map.map_type}",
        f"Valtakunta: {state.world_map.owner_kingdom or '-'}",
        f"Koko: {state.world_map.width} x {state.world_map.height} ruutua",
        f"Mittakaava: {state.world_map.scale_miles_per_pct} mi / 1% leveys",
        f"Matka/vrk: {state.world_map.travel_speed_miles_per_day} mi",
        f"Objekteja: {len(state.world_map.all_objects())}",
        f"Reittejä: {len(state.world_map.annotations)}",
        f"Kerroksia: {len(state.world_map.layers)}",
        f"Aktiivinen: {state.world_map.active_layer.name}",
    ]
    for line in info_lines:
        s = fonts.small.render(line, True, COLORS["text_main"])
        screen.blit(s, (x, y)); y += 18

    y += 12
    hint_lines = [
        "Mittauksessa:",
        "  LMB = aseta piste, ESC/Enter = lopeta",
        "Piirrossa:",
        "  LMB = lisää piste, Enter = tallenna reitti",
        "Zoom: hiirirulla, pan: välilyönti+veto",
        "Ctrl+S = tallenna, Del = poista valittu",
    ]
    for line in hint_lines:
        s = fonts.tiny.render(line, True, COLORS["text_dim"])
        screen.blit(s, (x, y)); y += 15


def _draw_path_summary(state, screen, path) -> None:
    rect = state.detail_panel_rect
    x = rect.x + 12
    y = rect.y + 10
    hdr = fonts.header.render(
        path.name or f"Reitti ({path.path_type})",
        True, COLORS["text_bright"])
    screen.blit(hdr, (x, y)); y += hdr.get_height() + 4

    miles = state.path_length_miles(path.points)
    days = state.travel_days(miles) if miles > 0 else 0.0
    hours = days * 24.0

    info_lines = [
        f"Tyyppi: {path.path_type}",
        f"Pisteitä: {len(path.points)}",
        f"Pituus: {miles:.2f} mailia",
        f"Matka-aika: {days:.2f} vrk  ({hours:.1f} h)",
        f"Vauhti: {state.world_map.travel_speed_miles_per_day:.0f} mi/vrk",
        f"Paksuus: {path.thickness} px",
        f"Katkoviiva: {'kyllä' if path.dashed else 'ei'}",
    ]
    for line in info_lines:
        s = fonts.small.render(line, True, COLORS["text_main"])
        screen.blit(s, (x, y)); y += 18

    if path.notes:
        y += 8
        y = _draw_wrapped_text(screen, "Muistiinpanot:", path.notes,
                               x, y, rect.width - 24, fonts.small)

    hint = fonts.tiny.render(
        "Muuta vauhtia: Mittakaava-painikkeella.  Poista: Del.",
        True, COLORS["text_dim"])
    screen.blit(hint, (x, rect.bottom - 22))


def _draw_wrapped_text(screen, title, body, x, y, max_w, font) -> int:
    t = fonts.small_bold.render(title, True, COLORS["text_dim"])
    screen.blit(t, (x, y)); y += 18
    words = body.split()
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        if font.size(test)[0] > max_w and line:
            s = font.render(line, True, COLORS["text_main"])
            screen.blit(s, (x, y)); y += 16
            line = w
        else:
            line = test
    if line:
        s = font.render(line, True, COLORS["text_main"])
        screen.blit(s, (x, y)); y += 16
    return y + 4


# ================================================================
# Bottom status bar + hover tooltip
# ================================================================

def _draw_bottom_bar(state, screen) -> None:
    rect = state.bottom_bar_rect
    pygame.draw.rect(screen, COLORS["panel_dark"], rect)
    pygame.draw.line(screen, COLORS["border"], (0, rect.y), (state.screen_w, rect.y))

    mp = pygame.mouse.get_pos()
    if state.canvas_rect.collidepoint(mp):
        px, py = state.screen_to_pct(*mp)
        coord = fonts.tiny.render(
            f"pos: {px:6.2f}%, {py:6.2f}%   zoom: {state.zoom:4.2f}x",
            True, COLORS["text_dim"])
        screen.blit(coord, (8, rect.y + 6))
    if state._status_timer > 0 and state._status_text:
        s = fonts.small.render(state._status_text, True, COLORS["text_bright"])
        screen.blit(s, (rect.width // 2 - s.get_width() // 2, rect.y + 4))


def _draw_hover_tooltip(state, screen) -> None:
    if not state.hover_object_id:
        return
    obj = state.world_map.find_object(state.hover_object_id)
    if obj is None:
        return
    lines: List[str] = []
    lines.append(obj.label or obj.object_type)
    if obj.hover_info:
        lines.append(obj.hover_info)
    if obj.dm_only:
        lines.append("[DM-only]")
    if obj.linked_map_id:
        lines.append("(tuplaklikkaus: avaa kartta)")
    Tooltip.draw(screen, "\n".join(lines), pygame.mouse.get_pos(), max_width=360)
