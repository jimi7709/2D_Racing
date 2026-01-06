# main.py
import pygame
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("2D Racing")
    clock = pygame.time.Clock()

    game = Game(screen, clock)
    game.run()

    pygame.quit()

if __name__ == "__main__":
    main()
