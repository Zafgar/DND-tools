import sys
import os
import threading
import logging
import queue

# --- LOGGING SETUP (Moved to top to catch startup errors) ---
# Force log file to be in the same directory as the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, 'crash_log.txt')

try:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        filemode='w'  # 'w' overwrites log each run, use 'a' to append
    )
    print(f"Logging to: {LOG_PATH}")
except PermissionError:
    print("WARNING: Could not open crash_log.txt. Logging to console instead.")
    logging.basicConfig(level=logging.INFO)

# Catch uncaught exceptions (like syntax errors in imports)
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception at startup:", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows DPI awareness — MUST run before the window is created. Without
# this, display scaling (125%/150% on most laptops) makes Windows
# bitmap-stretch the window: the UI renders zoomed and cropped, and a
# 1920x1080 window no longer fits the screen. With it, one window pixel
# is one physical pixel and the layout is crisp.
if sys.platform == "win32":
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from states.game_states import MenuState, BattleState, EncounterSetupState
from states.hero_creator import HeroCreatorState
from states.combat_roster import CombatRosterState
from states.campaign_manager import CampaignManagerState
from states.map_editor import MapEditorState

# --- FLASK SERVER SETUP (OPTIONAL) ---
# Flask powers only the TaleSpire mini-sync server (POST /update_minis).
# It is entirely optional: if Flask isn't installed the core DM tool
# still runs, just without live TaleSpire position sync. This keeps the
# app launchable on a fresh machine with only pygame installed.
game_instance = None  # Global reference to access GameManager from Flask route

# Thread-safe queue for passing data from Flask to the main game loop
_update_queue = queue.Queue()

try:
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    # Disable Flask logging to keep console clean
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route('/update_minis', methods=['POST'])
    def update_minis():
        if not game_instance:
            return jsonify({"status": "error", "message": "Game not running"}), 503

        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data"}), 400

        # Enqueue data for the main thread to process safely
        _update_queue.put(data)

        return jsonify({"status": "success"})

    def run_server():
        app.run(port=5000, debug=False, use_reloader=False)

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logging.info("Flask not installed — TaleSpire mini-sync disabled. "
                 "Install 'flask' to enable it. The DM tool runs normally.")
    print("Note: Flask not installed — TaleSpire live sync is off. "
          "Everything else works. (pip install flask to enable.)")

    def run_server():  # no-op fallback
        pass
# --------------------------


class GameManager:
    def __init__(self):
        global game_instance
        game_instance = self

        pygame.init()
        pygame.key.set_repeat(400, 50)  # Enable key repeat: 400ms delay, 50ms interval
        # Size the window to actually FIT the desktop (leaving room for
        # the title bar / taskbar). The layout is designed for
        # 1920x1080; on smaller desktops the window is clamped and the
        # right/bottom edge of the layout is cropped rather than the OS
        # shrinking or stretching the window behind our back.
        # (SCALED was tried and reverted: with Windows DPI scaling it
        # zoom-cropped the whole UI.)
        try:
            desktop = pygame.display.get_desktop_sizes()[0]
        except Exception:
            desktop = (SCREEN_WIDTH, SCREEN_HEIGHT)
        win_w, win_h = self._initial_window_size(desktop)
        logging.info("[DISPLAY] desktop %sx%s -> window %sx%s",
                     desktop[0], desktop[1], win_w, win_h)
        self.screen = pygame.display.set_mode((win_w, win_h),
                                              pygame.RESIZABLE)
        pygame.display.set_caption("D&D 5e AI Encounter Manager – Endgame Edition")

        # Non-fatal error banner: set when a frame/state raises so the
        # user sees a readable message instead of a black hung window.
        self.error_banner = ""
        self._error_font = None

        # Seed the Novus Somnium starter campaign on first run. Idempotent:
        # existing campaigns (including user edits) are left alone.
        try:
            from data.novus_somnium import ensure_default_campaign
            ensure_default_campaign()
        except Exception as ex:
            logging.warning(f"[Novus Somnium] seed failed: {ex}")
        self.clock = pygame.time.Clock()
        self.running = True
        self.states = {
            "MENU":  MenuState(self),
            "SETUP": EncounterSetupState(self),
            "HERO_CREATOR": HeroCreatorState(self),
            "COMBAT_ROSTER": CombatRosterState(self),
            "CAMPAIGN": None,
            "BATTLE": None,
            "MAP_EDITOR": None,
        }
        self.current_state = self.states["MENU"]

        # Start Flask server in a background thread (only if Flask is
        # installed; otherwise TaleSpire sync is silently disabled).
        if FLASK_AVAILABLE:
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()

    def change_state(self, state_name: str, **kwargs):
        # Recreate certain states fresh each time. Building a state can
        # fail (bad save data, missing asset, environment quirk); if it
        # does, log the full traceback and stay on the current screen
        # with an on-screen error rather than crashing to a black window.
        logging.info(f"[STATE] opening '{state_name}'...")
        try:
            if state_name == "HERO_CREATOR":
                self.states["HERO_CREATOR"] = HeroCreatorState(self)
            elif state_name == "COMBAT_ROSTER":
                self.states["COMBAT_ROSTER"] = CombatRosterState(self)
            elif state_name == "CAMPAIGN":
                campaign = kwargs.get("campaign")
                self.states["CAMPAIGN"] = CampaignManagerState(self, campaign)
            elif state_name == "MAP_EDITOR":
                world_map = kwargs.get("world_map")
                if world_map is None:
                    logging.warning("MAP_EDITOR requires world_map kwarg; ignoring change.")
                    return
                self.states["MAP_EDITOR"] = MapEditorState(
                    self,
                    world_map,
                    campaign=kwargs.get("campaign"),
                    world=kwargs.get("world"),
                    back_state=kwargs.get("back_state", ""),
                    callbacks=kwargs.get("callbacks"),
                )
        except Exception:
            logging.critical(f"Failed to open state '{state_name}':", exc_info=True)
            self.error_banner = (f"Could not open {state_name} — see "
                                 f"crash_log.txt. Press ESC to dismiss.")
            return
        if self.states.get(state_name):
            self.current_state = self.states[state_name]
            logging.info(f"[STATE] '{state_name}' active.")

    def _process_external_updates(self):
        """Process all queued external updates on the main thread (thread-safe)."""
        while not _update_queue.empty():
            try:
                minis_data = _update_queue.get_nowait()
                if isinstance(self.current_state, BattleState):
                    self.current_state.update_external_positions(minis_data)
                elif isinstance(self.current_state, EncounterSetupState):
                    self.current_state.update_external_data(minis_data)
            except queue.Empty:
                break

    def handle_external_update(self, minis_data):
        """Legacy method – still works but data is now queued."""
        _update_queue.put(minis_data)

    def quit(self):
        self.running = False

    @staticmethod
    def _initial_window_size(desktop):
        """Clamp the 1920x1080 design size to the desktop, reserving
        ~80px for the title bar / taskbar so the window always fits."""
        desk_w, desk_h = desktop
        win_w = min(SCREEN_WIDTH, desk_w)
        win_h = min(SCREEN_HEIGHT, max(600, desk_h - 80))
        return win_w, win_h

    def _sync_display_surface(self):
        """Rebind self.screen to the live display surface.

        pygame-ce can REPLACE the display surface when a RESIZABLE
        window is resized/maximized. Anything drawn to the old surface
        object then silently disappears — the window freezes on the
        last presented frame (looks like a black/blank screen). Fetching
        the current surface every frame makes that impossible."""
        live = pygame.display.get_surface()
        if live is not None and live is not self.screen:
            logging.info("[DISPLAY] surface replaced (%sx%s) — rebinding",
                         live.get_width(), live.get_height())
            self.screen = live

    def _draw_error_banner(self):
        """Draw the non-fatal error message so the user is never left
        staring at a black screen with no explanation."""
        if not self.error_banner:
            return
        if self._error_font is None:
            # Font(None, ...) is the built-in default font — always
            # available, unlike SysFont which may miss a named face.
            self._error_font = pygame.font.Font(None, 24)
        w = self.screen.get_width()
        band_h = 64
        band = pygame.Surface((w, band_h), pygame.SRCALPHA)
        band.fill((140, 30, 30, 235))
        self.screen.blit(band, (0, 0))
        for i, line in enumerate(self.error_banner.split("\n")[:2]):
            surf = self._error_font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (16, 10 + i * 26))

    def run(self):
        logging.info("Game starting...")
        try:
            while self.running:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        logging.info("[DISPLAY] window resized to %sx%s",
                                     event.w, event.h)
                    elif (event.type == pygame.KEYDOWN
                          and event.key == pygame.K_ESCAPE and self.error_banner):
                        self.error_banner = ""  # dismiss the banner
                # Always draw to the LIVE display surface (see docstring).
                self._sync_display_surface()
                # Each phase is isolated: one bad frame logs its traceback
                # and shows a banner, but the app keeps running instead of
                # dying to a black window. Repeated failures still scroll
                # the log so the root cause is captured.
                try:
                    self._process_external_updates()
                    self.current_state.handle_events(events)
                    self.current_state.update()
                    self.current_state.draw(self.screen)
                except Exception:
                    broken = type(self.current_state).__name__
                    logging.critical(f"Frame error in {broken}:", exc_info=True)
                    self.error_banner = (
                        f"Error in {broken} — see crash_log.txt. Returned to "
                        "menu.\nPress ESC to dismiss; your data on disk is safe.")
                    # Fall back to the known-good menu so the user isn't
                    # trapped re-crashing the same screen every frame.
                    menu = self.states.get("MENU")
                    if menu is not None and self.current_state is not menu:
                        self.current_state = menu
                        try:
                            self.current_state.draw(self.screen)
                        except Exception:
                            self.screen.fill((20, 20, 24))
                    else:
                        self.screen.fill((20, 20, 24))
                self._draw_error_banner()
                pygame.display.flip()
                self.clock.tick(FPS)
        except Exception:
            logging.critical("CRITICAL ERROR - GAME LOOP CRASHED:", exc_info=True)
            raise
        finally:
            pygame.quit()


if __name__ == "__main__":
    GameManager().run()
