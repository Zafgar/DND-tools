import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from states.game_states import MenuState, BattleState, EncounterSetupState

class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("DnD 5e AI Toolset - Endgame Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Alustetaan tilat
        self.states = {
            "MENU": MenuState(self),
            "SETUP": EncounterSetupState(self),
            "BATTLE": BattleState(self) # Tämä luodaan uudestaan setupissa
        }
        self.current_state = self.states["MENU"]

    def change_state(self, state_name):
        self.current_state = self.states[state_name]

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                self.current_state.handle_events([event])
            
            self.current_state.update()
            self.current_state.draw(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = GameManager()
    game.run()