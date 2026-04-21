"""
MapEditorState — mouse/keyboard routing.

Split out from map_editor.py to keep each file digestible.  The `route_events`
function receives the owning state plus the pygame event list and dispatches
to tool-specific handlers.
"""
from __future__ import annotations

import math
from typing import List, Tuple

import pygame

from data.map_engine import MapObject, AnnotationPath, TERRAIN_BRUSHES
from states.map_editor import (
    TOOL_SELECT, TOOL_PLACE_OBJECT, TOOL_PAINT_TILE, TOOL_ERASE_TILE,
    TOOL_FILL_TILE, TOOL_MEASURE_LINE, TOOL_MEASURE_PATH, TOOL_DRAW_PATH,
    TOOL_DELETE, TOOLS_ORDER, OBJECT_TYPE_GROUPS,
)


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------

def route_events(state, events) -> None:
    mp = pygame.mouse.get_pos()

    # Update hover for tooltip/highlight regardless of tool
    hover = state.object_at_screen(*mp) if state.canvas_rect.collidepoint(mp) else None
    state.hover_object_id = hover.id if hover else ""

    for ev in events:
        # Modal has priority if open
        if state._edit_modal is not None:
            state._edit_modal.handle_event(ev)
            continue

        # Top-bar buttons
        for btn in (state.btn_back, state.btn_save, state.btn_load_img,
                    state.btn_grid, state.btn_scale, state.btn_layers,
                    state.btn_parent, state.btn_nav):
            btn.handle_event(ev)

        # Navigator consumes its own events when open
        if state.navigator_open and state._navigator is not None:
            if state._navigator.handle_event(ev):
                continue

        # Tool palette click (left panel)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if state.tool_panel_rect.collidepoint(ev.pos):
                _handle_tool_panel_click(state, ev.pos)
                continue

        # Keyboard
        if ev.type == pygame.KEYDOWN:
            _handle_key(state, ev)
            continue

        # Canvas interaction
        if not state.canvas_rect.collidepoint(mp):
            continue

        if ev.type == pygame.MOUSEWHEEL:
            _handle_zoom(state, ev, mp)
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            _handle_mouse_down(state, ev, mp)
        elif ev.type == pygame.MOUSEBUTTONUP:
            _handle_mouse_up(state, ev, mp)
        elif ev.type == pygame.MOUSEMOTION:
            _handle_mouse_motion(state, ev, mp)


# ----------------------------------------------------------------------
# Tool palette
# ----------------------------------------------------------------------

def _handle_tool_panel_click(state, pos) -> None:
    x, y = pos
    px = state.tool_panel_rect.x
    py = state.tool_panel_rect.y + 8

    # Tool buttons — 30px tall rows
    for i, (key, label) in enumerate(TOOLS_ORDER):
        row = pygame.Rect(px + 8, py + i * 32, state.tool_panel_rect.width - 16, 28)
        if row.collidepoint(x, y):
            state.tool = key
            state.measure_points = []
            state.draw_points = []
            state._set_status(f"Työkalu: {label}")
            return

    # Section below tools: picker (object type or brush) depending on tool
    section_y = py + len(TOOLS_ORDER) * 32 + 16
    if state.tool == TOOL_PLACE_OBJECT:
        _handle_object_picker_click(state, pos, section_y)
    elif state.tool in (TOOL_PAINT_TILE, TOOL_FILL_TILE):
        _handle_brush_picker_click(state, pos, section_y)


def _handle_object_picker_click(state, pos, start_y) -> None:
    x, y = pos
    px = state.tool_panel_rect.x
    w  = state.tool_panel_rect.width
    yy = start_y
    for _group_name, keys in OBJECT_TYPE_GROUPS:
        yy += 20  # group header
        for key in keys:
            row = pygame.Rect(px + 12, yy, w - 24, 22)
            if row.collidepoint(x, y):
                state.active_object_type = key
                state._set_status(f"Objektityyppi: {key}")
                return
            yy += 24
        yy += 6


def _handle_brush_picker_click(state, pos, start_y) -> None:
    x, y = pos
    px = state.tool_panel_rect.x
    w  = state.tool_panel_rect.width
    yy = start_y
    for key in TERRAIN_BRUSHES.keys():
        row = pygame.Rect(px + 12, yy, w - 24, 20)
        if row.collidepoint(x, y):
            state.active_brush = key
            state._set_status(f"Sivellin: {key}")
            return
        yy += 22


# ----------------------------------------------------------------------
# Keyboard
# ----------------------------------------------------------------------

def _handle_key(state, ev) -> None:
    if ev.key == pygame.K_ESCAPE:
        state.measure_points = []
        state.draw_points = []
        state.selected_object_id = ""
        state._set_status("Peruttu")
    elif ev.key == pygame.K_RETURN:
        # Finish in-progress path
        if state.tool == TOOL_DRAW_PATH and len(state.draw_points) >= 2:
            _finish_drawn_path(state)
    elif ev.key == pygame.K_DELETE and state.selected_object_id:
        state.world_map.remove_object(state.selected_object_id)
        state.selected_object_id = ""
        state._set_status("Objekti poistettu")
    elif ev.key == pygame.K_LEFTBRACKET:
        state.brush_radius = max(0, state.brush_radius - 1)
    elif ev.key == pygame.K_RIGHTBRACKET:
        state.brush_radius = min(10, state.brush_radius + 1)
    elif ev.key == pygame.K_s and (ev.mod & pygame.KMOD_CTRL):
        state._on_save()


# ----------------------------------------------------------------------
# Zoom & pan
# ----------------------------------------------------------------------

def _handle_zoom(state, ev, mp) -> None:
    old_zoom = state.zoom
    step = 1.15 if ev.y > 0 else (1 / 1.15)
    new_zoom = max(0.05, min(8.0, state.zoom * step))
    if new_zoom == old_zoom:
        return
    # Zoom around cursor: world coord under mouse stays fixed.
    wx_before, wy_before = state.screen_to_world(*mp)
    state.zoom = new_zoom
    wx_after, wy_after = state.screen_to_world(*mp)
    state.camera_x += (wx_before - wx_after)
    state.camera_y += (wy_before - wy_after)


# ----------------------------------------------------------------------
# Mouse button handling
# ----------------------------------------------------------------------

def _handle_mouse_down(state, ev, mp) -> None:
    # Middle button or space+left starts pan
    keys = pygame.key.get_pressed()
    is_pan = (ev.button == 2) or (ev.button == 1 and keys[pygame.K_SPACE])
    if is_pan:
        state._dragging_pan = True
        state._pan_anchor = mp
        state._pan_cam_start = (state.camera_x, state.camera_y)
        return

    # Right-click: open edit modal for object under cursor (or cancel tool)
    if ev.button == 3:
        obj = state.object_at_screen(*mp)
        if obj:
            _open_edit_modal(state, obj)
        else:
            state.measure_points = []
            state.draw_points = []
        return

    if ev.button != 1:
        return

    # Tool-specific left-click
    if state.tool == TOOL_SELECT:
        _tool_select_down(state, mp)
    elif state.tool == TOOL_PLACE_OBJECT:
        _tool_place(state, mp)
    elif state.tool == TOOL_DELETE:
        _tool_delete(state, mp)
    elif state.tool == TOOL_PAINT_TILE:
        _tool_paint(state, mp, erase=False)
    elif state.tool == TOOL_ERASE_TILE:
        _tool_paint(state, mp, erase=True)
    elif state.tool == TOOL_FILL_TILE:
        _tool_fill(state, mp)
    elif state.tool == TOOL_MEASURE_LINE:
        _tool_measure_line(state, mp)
    elif state.tool == TOOL_MEASURE_PATH:
        _tool_measure_path(state, mp)
    elif state.tool == TOOL_DRAW_PATH:
        _tool_draw_path(state, mp)


def _handle_mouse_up(state, ev, _mp) -> None:
    if ev.button in (1, 2):
        state._dragging_pan = False
    if ev.button == 1 and state._drag_object_id:
        state._drag_object_id = ""


def _handle_mouse_motion(state, ev, mp) -> None:
    if state._dragging_pan:
        dx = mp[0] - state._pan_anchor[0]
        dy = mp[1] - state._pan_anchor[1]
        state.camera_x = state._pan_cam_start[0] - dx / state.zoom
        state.camera_y = state._pan_cam_start[1] - dy / state.zoom
        return

    if state._drag_object_id:
        obj = state.world_map.find_object(state._drag_object_id)
        if obj:
            px, py = state.screen_to_pct(*mp)
            obj.x = max(0.0, min(100.0, px - state._drag_object_offset[0]))
            obj.y = max(0.0, min(100.0, py - state._drag_object_offset[1]))

    # Continue painting while button held
    if ev.buttons[0] and state.canvas_rect.collidepoint(mp):
        if state.tool == TOOL_PAINT_TILE:
            _tool_paint(state, mp, erase=False)
        elif state.tool == TOOL_ERASE_TILE:
            _tool_paint(state, mp, erase=True)


# ----------------------------------------------------------------------
# Individual tools
# ----------------------------------------------------------------------

def _tool_select_down(state, mp) -> None:
    obj = state.object_at_screen(*mp)
    if obj is None:
        state.selected_object_id = ""
        return
    state.selected_object_id = obj.id
    # Prepare drag offset in %
    obj_px = (obj.x, obj.y)
    mouse_px = state.screen_to_pct(*mp)
    state._drag_object_offset = (mouse_px[0] - obj_px[0], mouse_px[1] - obj_px[1])
    state._drag_object_id = obj.id
    # Double-click: drill into linked map, or open modal
    now = pygame.time.get_ticks()
    last = getattr(state, "_last_click_ms", 0)
    last_id = getattr(state, "_last_click_id", "")
    state._last_click_ms = now
    state._last_click_id = obj.id
    if last_id == obj.id and (now - last) < 350:
        if obj.linked_map_id:
            state.open_linked_map(obj)
        elif obj.linked_encounter_id or (obj.unit_type and obj.unit_count > 0):
            state.start_encounter_from_object(obj)
        elif obj.linked_npc_ids:
            state.open_npc_modal(list(obj.linked_npc_ids))
        else:
            _open_edit_modal(state, obj)


def _tool_place(state, mp) -> None:
    px, py = state.screen_to_pct(*mp)
    px = max(0.0, min(100.0, px))
    py = max(0.0, min(100.0, py))
    obj = MapObject(x=px, y=py, object_type=state.active_object_type,
                    label=state.active_object_type.replace("_", " ").title())
    state.world_map.active_layer.objects.append(obj)
    state.selected_object_id = obj.id
    state._set_status(f"Lisätty: {obj.object_type}")


def _tool_delete(state, mp) -> None:
    obj = state.object_at_screen(*mp)
    if obj is not None:
        state.world_map.remove_object(obj.id)
        state.selected_object_id = ""
        state._set_status("Objekti poistettu")


def _tool_paint(state, mp, *, erase: bool) -> None:
    # Convert screen to tile coordinates — tiles sit over the world grid
    ww, wh = state.world_size_px()
    wx, wy = state.screen_to_world(*mp)
    tile_w_px = ww / max(1, state.world_map.width)
    tile_h_px = wh / max(1, state.world_map.height)
    tx = int(wx / max(1, tile_w_px))
    ty = int(wy / max(1, tile_h_px))
    if not (0 <= tx < state.world_map.width and 0 <= ty < state.world_map.height):
        return
    layer = state.world_map.active_layer
    brush = "" if erase else state.active_brush
    layer.paint_brush(tx, ty, brush, radius=state.brush_radius)


def _tool_fill(state, mp) -> None:
    ww, wh = state.world_size_px()
    wx, wy = state.screen_to_world(*mp)
    tile_w_px = ww / max(1, state.world_map.width)
    tile_h_px = wh / max(1, state.world_map.height)
    tx = int(wx / max(1, tile_w_px))
    ty = int(wy / max(1, tile_h_px))
    if not (0 <= tx < state.world_map.width and 0 <= ty < state.world_map.height):
        return
    layer = state.world_map.active_layer
    n = layer.flood_fill(tx, ty, state.active_brush,
                         state.world_map.width, state.world_map.height)
    state._set_status(f"Täytetty {n} ruutua")


def _tool_measure_line(state, mp) -> None:
    px, py = state.screen_to_pct(*mp)
    state.measure_points.append((px, py))
    if len(state.measure_points) >= 2:
        # Keep only the last two for a rolling ruler
        state.measure_points = state.measure_points[-2:]
        a, b = state.measure_points
        miles = state.distance_miles(a, b)
        days = state.travel_days(miles)
        state._set_status(
            f"Suora: {miles:.1f} mi  ({days:.2f} vrk)"
        )


def _tool_measure_path(state, mp) -> None:
    px, py = state.screen_to_pct(*mp)
    state.measure_points.append((px, py))
    # Running total
    total = 0.0
    for i in range(1, len(state.measure_points)):
        total += state.distance_miles(state.measure_points[i - 1],
                                      state.measure_points[i])
    if len(state.measure_points) >= 2:
        days = state.travel_days(total)
        state._set_status(
            f"Polku ({len(state.measure_points)} pist.): {total:.1f} mi / {days:.2f} vrk. Enter tai ESC lopettaa."
        )


def _tool_draw_path(state, mp) -> None:
    px, py = state.screen_to_pct(*mp)
    state.draw_points.append((px, py))


def _finish_drawn_path(state) -> None:
    if len(state.draw_points) < 2:
        state.draw_points = []
        return
    path = AnnotationPath(
        name="Reitti", path_type="route",
        points=list(state.draw_points),
    )
    state.world_map.annotations.append(path)
    state._set_status(f"Reitti tallennettu ({len(state.draw_points)} pistettä)")
    state.draw_points = []


# ----------------------------------------------------------------------
# Edit modal placeholder
# ----------------------------------------------------------------------

def _open_edit_modal(state, obj: MapObject) -> None:
    from states.map_editor_modals import MapObjectEditModal
    state._edit_modal = MapObjectEditModal(obj, on_close=lambda: _close_modal(state))


def _close_modal(state) -> None:
    state._edit_modal = None
