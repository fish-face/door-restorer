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
from save import SaveGame
from sound import SoundPlayer

PROFILE = False
WINDOW_W, WINDOW_H = 600, 600

MODE_MAIN_MENU = 0
MODE_SELECT_LEVEL = 1
MODE_PLAYING = 2

class Launcher(object):
    def __init__(self, screen):
        self.screen = screen
        self.sound = SoundPlayer()
        self.menu_font = pygame.font.SysFont('Sawasdee', 30, True)
        self.small_font = pygame.font.SysFont('Sawasdee', 12, True)
        self.quitting = False
        self.clock = pygame.time.Clock()
        #self.menu_options = (('Play', None), ('Help', None), ('Quit', None))
        self.menu_options = (Label('Play'), Label('Help'), Label('Quit'))
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
            self.save = SaveGame()
            with open(os.path.join('levels', 'levels.txt')) as fd:
                self.levelset_name = fd.readline()
                levels = [LevelDescription(*row) for row in csv.reader(fd, delimiter='\t')]
            self.select_list = levels
        elif value == MODE_MAIN_MENU:
            self.current_menu_item = 0
            self.select_list = self.menu_options
        elif value == MODE_PLAYING:
            pygame.key.set_repeat(1, 150)

    def select_menu(self):
        option = self.select_list[self.current_menu_item]
        if self.mode == MODE_MAIN_MENU:
            name = option.name
            if name == 'Play':
                self.mode = MODE_SELECT_LEVEL
            elif name == 'Help':
                pass
            elif name == 'Quit':
                self.quitting = True
        elif self.mode == MODE_SELECT_LEVEL:
            if self.save.available(self.levelset_name, option.id):
                self.sound.throw()
                self.mode = MODE_PLAYING
                self.level_id = option.id
                self.game.load_level(option.value)
                self.game.start()
            else:
                self.sound.land()

    def start(self):
        self.draw()
        while not self.quitting:
            self.clock.tick(game.FRAME_RATE)
            if self.mode == MODE_PLAYING:
                self.game.main_loop()
                if self.game.stopping:
                    if self.game.won:
                        saver = SaveGame({self.levelset_name: {'completed': [self.level_id]}})
                        saver.save()
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
            self.draw_level_list()
        pygame.display.flip()

    def draw_level_list(self):
        margin = 8
        columns = 8
        w = (WINDOW_W - margin) / columns
        h = (WINDOW_H - margin) / columns
        y = -h
        for i, item in enumerate(self.select_list):
            if i % columns == 0:
                x = -w
                y += margin + h
            x += margin + w
            thickness = 4 if i == self.current_menu_item else 1

            completed = self.save.completed(self.levelset_name, item.id)
            available = self.save.available(self.levelset_name, item.id)

            colour = (172, 172, 172) if available else (64, 64, 64)
            if i == self.current_menu_item:
                border = (255, 255, 255) if available else (96, 96, 96)
            else:
                border = colour

            self.screen.fill(border,
                             (x, y, w, h))
            self.screen.fill(colour,
                             (x + thickness, y + thickness, w - 2*thickness, h - 2*thickness))
            id_text = self.menu_font.render(str(item.id), True, (0, 0, 0))
            id_pos = id_text.get_rect()
            id_pos.y = margin/2
            id_pos.centerx = x + w/2
            name_text = self.small_font.render(item.name, True, (0, 0, 0))
            name_pos = name_text.get_rect()
            name_pos.bottom = y + h - margin/2
            name_pos.centerx = x + w/2
            self.screen.blit(id_text, id_pos)
            self.screen.blit(name_text, name_pos)

    def draw_select_list(self):
        rendered_items = []
        menu_height = 0
        max_height = 0
        for item in self.select_list:
            rendered_items.append(self.menu_font.render(item.name, True, (255, 255, 255)))
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
                pygame.draw.polygon(self.screen,
                                    (196, 196, 196),
                                    ((x-12, menu_top+8),
                                     (x-12, menu_top+32),
                                     (x, menu_top+20)))
                pygame.draw.aalines(self.screen,
                                    (255, 255, 255),
                                    True,
                                    ((x-12, menu_top+8),
                                     (x-12, menu_top+32),
                                     (x, menu_top+20)))

                x = WINDOW_W - x
                pygame.draw.polygon(self.screen,
                                    (196, 196, 196),
                                    ((x+12, menu_top+8),
                                     (x+12, menu_top+32),
                                     (x, menu_top+20)))
                pygame.draw.aalines(self.screen,
                                    (255, 255, 255),
                                    True,
                                    ((x+12, menu_top+8),
                                     (x+12, menu_top+32),
                                     (x, menu_top+20)))

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


class LevelDescription(object):
    def __init__(self, *args):
        self.id, self.name, self.value = args
        self.id = int(self.id)


class Label(object):
    def __init__(self, name):
        self.name = name


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
