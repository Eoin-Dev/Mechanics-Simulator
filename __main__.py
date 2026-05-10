import pygame
from simulator.sim import Simulation

pygame.init()

if __name__ == '__main__':
    sim = Simulation()
    sim.start()

pygame.quit()