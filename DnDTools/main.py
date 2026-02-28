import sys
import os
import threading
import logging

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

import pygame
from flask import Flask, request, jsonify
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from states.game_states import MenuState, BattleState, EncounterSetupState
from states.hero_creator import HeroCreatorState
from states.combat_roster import CombatRosterState

# --- FLASK SERVER SETUP ---
app = Flask(__name__)

# Disable Flask logging to keep console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

game_instance = None  # Global reference to access GameManager from Flask route

@app.route('/update_minis', methods=['POST'])
def update_minis():
    if not game_instance:
        return jsonify({"status": "error", "message": "Game not running"}), 503
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    # Pass data to the game engine (thread-safe enough for simple position updates)
    game_instance.handle_external_update(data)
    
    return jsonify({"status": "success"})

def run_server():
    app.run(port=5000, debug=False, use_reloader=False)
# --------------------------


class GameManager:
    def __init__(self):
        global game_instance
        game_instance = self

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("D&D 5e AI Encounter Manager – Endgame Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.states = {
            "MENU":  MenuState(self),
            "SETUP": EncounterSetupState(self),
            "HERO_CREATOR": HeroCreatorState(self),
            "COMBAT_ROSTER": CombatRosterState(self),
            "BATTLE": None,
        }
        self.current_state = self.states["MENU"]

        # Start Flask server in a background thread
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def change_state(self, state_name: str):
        # Recreate certain states fresh each time
        if state_name == "HERO_CREATOR":
            self.states["HERO_CREATOR"] = HeroCreatorState(self)
        elif state_name == "COMBAT_ROSTER":
            self.states["COMBAT_ROSTER"] = CombatRosterState(self)
        if self.states.get(state_name):
            self.current_state = self.states[state_name]

    def handle_external_update(self, minis_data):
        """Called by Flask thread when new mini positions arrive."""
        # Only update if we are currently in a battle
        if isinstance(self.current_state, BattleState):
            self.current_state.update_external_positions(minis_data)
        # Allow Setup state to receive data for import
        elif isinstance(self.current_state, EncounterSetupState):
            self.current_state.update_external_data(minis_data)

    def quit(self):
        self.running = False

    def run(self):
        try:
            logging.info("Game starting...")
            while self.running:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                self.current_state.handle_events(events)
                self.current_state.update()
                self.current_state.draw(self.screen)
                pygame.display.flip()
                self.clock.tick(FPS)
        except Exception as e:
            logging.critical("CRITICAL ERROR - GAME CRASHED:", exc_info=True)
            raise e
        finally:
            pygame.quit()


if __name__ == "__main__":
    GameManager().run()
