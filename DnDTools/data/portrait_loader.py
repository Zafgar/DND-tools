"""Portrait JPG / PNG loader for Actors, NPCs, Shops, etc.

Pure logic + pygame loading. Resolves a portrait path, supports
project-relative or absolute, returns a cached pygame.Surface scaled
to a target box. Returns None when pygame isn't available or the
file is missing — callers fall back to procedurally-drawn art.
"""
from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

try:
    import pygame  # type: ignore
except ImportError:
    pygame = None


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTRAITS_DIR = os.path.join(PROJECT_ROOT, "saves", "portraits")


def resolve_portrait_path(path: str) -> str:
    """Convert ``path`` to an absolute filesystem path. Empty input
    returns empty. Relative paths resolve against the project root."""
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def import_portrait_file(src_path: str, *, name_hint: str = "") -> str:
    """Copy ``src_path`` into ``saves/portraits/`` so the project
    owns the asset. Returns the project-relative path that callers
    should store on the actor / NPC."""
    import shutil, time
    if not src_path or not os.path.isfile(src_path):
        return ""
    os.makedirs(PORTRAITS_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower() or ".jpg"
    base = "".join(c if c.isalnum() else "_"
                    for c in (name_hint
                              or os.path.splitext(
                                  os.path.basename(src_path))[0]))[:40]
    base = base or "portrait"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(PORTRAITS_DIR, f"{base}_{stamp}{ext}")
    try:
        shutil.copy2(src_path, dest)
    except OSError:
        return ""
    return os.path.relpath(dest, PROJECT_ROOT)


# --------------------------------------------------------------------- #
# Surface cache (per-(path, w, h))
# --------------------------------------------------------------------- #
_SURFACE_CACHE: Dict[Tuple[str, int, int], "pygame.Surface"] = {}


def load_portrait(path: str, target_w: int = 96,
                    target_h: int = 96):
    """Return a pygame Surface (target_w x target_h) for the portrait,
    or None if pygame isn't available or the file can't be loaded."""
    if pygame is None:
        return None
    abs_path = resolve_portrait_path(path)
    if not abs_path or not os.path.isfile(abs_path):
        return None
    key = (abs_path, int(target_w), int(target_h))
    if key in _SURFACE_CACHE:
        return _SURFACE_CACHE[key]
    try:
        raw = pygame.image.load(abs_path)
        scaled = pygame.transform.smoothscale(
            raw.convert_alpha(), (target_w, target_h)
        )
    except (pygame.error, FileNotFoundError):
        return None
    _SURFACE_CACHE[key] = scaled
    return scaled


def clear_cache():
    _SURFACE_CACHE.clear()


def has_portrait(path: str) -> bool:
    """Cheap check that the file exists; doesn't load it."""
    abs_path = resolve_portrait_path(path)
    return bool(abs_path) and os.path.isfile(abs_path)
