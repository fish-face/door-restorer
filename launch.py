#!/usr/bin/env python

import pygame
import pygame.locals
import sys
import os
from glob import glob
import cProfile
import pstats
import csv

sys.path.append(os.path.join('.', 'src'))
sys.path.insert(0, os.path.join('.', 'PyTMX'))

import game

PROFILE = False
WINDOW_W, WINDOW_H = 600, 600

MODE_MAIN_MENU = 0
MODE_SELECT_LEVEL = 1
MODE_PLAYING = 2

class Launcher(object):
    def __init__(self, screen):
        self.screen = screen
        self.menu_font = pygame.font.SysFont('Sawasdee', 30, True)
        self.quitting = False
        self.clock = pygame.time.Clock()
        self.menu_options = (('Play', None), ('Help', None), ('Quit', None))
        self.mode = MODE_MAIN_MENU
        self.game = game.Game(screen)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value
        pygame.key.set_repeat()
        if value == MODE_SELECT_LEVEL:
            self.current_menu_item = 0
            with open(os.path.join('levels', 'levels.txt')) as fd:
                levels = [row for row in csv.reader(fd, delimiter='\t')]
            self.select_list = levels
        elif value == MODE_MAIN_MENU:
            self.current_menu_item = 0
            self.select_list = self.menu_options
        elif value == MODE_PLAYING:
            pygame.key.set_repeat(1, 150)

    def select_menu(self):
        option, value = self.select_list[self.current_menu_item]
        if self.mode == MODE_MAIN_MENU:
            if option == 'Play':
                self.mode = MODE_SELECT_LEVEL
            elif option == 'Help':
                pass
            elif option == 'Quit':
                self.quitting = True
        elif self.mode == MODE_SELECT_LEVEL:
            self.mode = MODE_PLAYING
            self.game.load_level(value)
            self.game.start()

    def start(self):
        self.draw()
        while not self.quitting:
            self.clock.tick(game.FRAME_RATE)
            if self.mode == MODE_PLAYING:
                self.game.main_loop()
                if self.game.stopping:
                    self.mode = MODE_MAIN_MENU
                    self.draw()
                elif self.game.quitting:
                    self.quitting = True

            if not self.process_events():
                continue

            self.draw()

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.mode == MODE_MAIN_MENU:
            self.draw_select_list()
        elif self.mode == MODE_SELECT_LEVEL:
            self.draw_select_list()
        pygame.display.flip()

    def draw_select_list(self):
        rendered_items = []
        menu_height = 0
        max_height = 0
        for item in self.select_list:
            rendered_items.append(self.menu_font.render(item[0], True, (255, 255, 255)))
            height = rendered_items[-1].get_height()
            menu_height += height
            max_height = max(height, max_height)

        margin = 8
        menu_top = WINDOW_H / 2 - menu_height / 2
        for i, item in enumerate(rendered_items):
            x = WINDOW_W / 2 - item.get_width() / 2
            self.screen.blit(item, (x, menu_top))
            if i == self.current_menu_item:
                x -= 8
                pygame.draw.polygon(self.screen, (196, 196, 196), ((x-12, menu_top+8), (x-12, menu_top+32), (x, menu_top+20)))
                pygame.draw.aalines(self.screen, (255, 255, 255), True, ((x-12, menu_top+8), (x-12, menu_top+32), (x, menu_top+20)))

                x = WINDOW_W - x
                pygame.draw.polygon(self.screen, (196, 196, 196), ((x+12, menu_top+8), (x+12, menu_top+32), (x, menu_top+20)))
                pygame.draw.aalines(self.screen, (255, 255, 255), True, ((x+12, menu_top+8), (x+12, menu_top+32), (x, menu_top+20)))
            menu_top += max_height + margin

    def process_events(self):
        #if pygame.event.peek(pygame.QUIT):
        #    self.quitting = True
        #    return False

        if self.mode == MODE_PLAYING:
            return False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quitting = True
                return False
            if e.type == pygame.KEYDOWN:
                if e.key in game.UP_KEYS:
                    self.current_menu_item -= 1
                    self.current_menu_item %= len(self.select_list)
                    return True
                if e.key in game.DOWN_KEYS:
                    self.current_menu_item += 1
                    self.current_menu_item %= len(self.select_list)
                    return True
                if e.key in game.ACTION_KEYS:
                    self.select_menu()
                    return True


if __name__ == '__main__':
    pygame.mixer.pre_init(44100)
    pygame.init()
    screen = pygame.display.set_mode((600, 600))

    launcher = Launcher(screen)
    #game = game.Game(screen)
    if PROFILE:
        cProfile.run('launcher.start()', 'profiledump')
        p = pstats.Stats('profiledump')
        p.sort_stats('cumtime').print_stats(.5)
    else:
        launcher.start()
