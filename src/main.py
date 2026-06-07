import pygame
from game import Game
from settings import WINDOW_WIDTH, WINDOW_HEIGHT

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Duskbound - Demo")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    Game(screen).run()
    pygame.quit()

if __name__ == "__main__":
    main()
