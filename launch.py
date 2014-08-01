#!/usr/bin/env python

import pygame
import pygame.locals
import sys
import os
import cProfile
import pstats

sys.path.append(os.path.join('.', 'src'))
sys.path.insert(0, os.path.join('.', 'PyTMX'))

import game

PROFILE = False

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((600, 600))

    game = game.Game(screen)
    if PROFILE:
        cProfile.run('game.start()', 'profiledump')
        p = pstats.Stats('profiledump')
        p.sort_stats('cumtime').print_stats(.5)
    else:
        game.start()
