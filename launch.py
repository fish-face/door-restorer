#!/usr/bin/env python

import pygame
import pygame.locals
import sys
import os
from glob import glob
import cProfile
import pstats

if hasattr(sys, 'frozen') and sys.frozen == 'windows_exe':
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join('.', 'src'))
sys.path.insert(0, os.path.join('.', 'PyTMX'))

from renderer import Renderer
import game
from tutorial import TutorialOne, TutorialTwo
from save import SaveGame
from sound import SoundPlayer
from levelset import LevelSet, LevelDescription
from animation import Animation

PROFILE = False
WINDOW_W, WINDOW_H = 600, 600

MODE_INTRO = 0
MODE_MAIN_MENU = 1
MODE_SELECT_WORLD = 2
MODE_SELECT_LEVEL = 3
MODE_PLAYING = 4
MODE_WON = 5

INTRO_DELAY = 25
INTRO_FRAMES = 100

GRID_COLS = 5

MENU_OFFSET = 50
MENU_ITEM_H = 61
MENU_ITEM_TOP = 300

SELECTOR_H = 16
SELECTOR_W = 6

class Launcher(object):
    def __init__(self, screen):
        self.screen = screen
        self.save = SaveGame()
        self.sound = SoundPlayer()
        self.menu_font = pygame.font.Font('fonts/GROTESKIA.ttf', 50)
        self.small_font = pygame.font.Font('fonts/C&C Red Alert [INET].ttf', 13)
        self.intro_graphic = pygame.image.load('graphics/background_intro.png').convert()
        self.background = pygame.image.load('graphics/background.png').convert()
        self.background_menu = pygame.image.load('graphics/background_menu.png').convert()
        #self.overlay_won = pygame.image.load('graphics/overlay_background.png').convert()
        self.overlay_won = pygame.Surface(screen.get_size())
        self.overlay_won.fill((0, 0, 0))
        self.overlay_won.set_alpha(128)
        self.won_animation = Animation('graphics/victory.json')
        self.quitting = False
        self.clock = pygame.time.Clock()
        self.menu_options = (Label('Play'),
                             Label('Select Level'),
                             Label('Help'),
                             Label('Credits'),
                             Label('Quit'))
        self.menu_widths = [self.menu_font.size(opt.name)[0] for opt in self.menu_options]
        self.mode = MODE_INTRO
        self.intro_frame = 0

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value
        pygame.key.set_repeat()
        if value == MODE_SELECT_LEVEL:
            world = self.select_list[self.current_menu_item]
            self.select_list = world.levels
            self.current_menu_item = 0
        elif value == MODE_SELECT_WORLD:
            self.current_menu_item = 0
            self.read_level_info()
            self.select_list = sorted(self.worlds.values())
        elif value == MODE_MAIN_MENU:
            self.current_menu_item = 0
            self.select_list = self.menu_options
        elif value == MODE_PLAYING:
            self.screen.fill((0, 0, 0))
            pygame.key.set_repeat(1, 150)

    def select_menu(self):
        option = self.select_list[self.current_menu_item]
        if self.mode == MODE_MAIN_MENU:
            name = option.name
            if name == 'Play':
                self.read_level_info()
                self.current_world, self.level_id = self.save.current()
                self.play()
            elif name == 'Select Level':
                self.mode = MODE_SELECT_WORLD
            elif name == 'Help':
                return False
            elif name == 'Quit':
                self.quitting = True
        elif self.mode == MODE_SELECT_WORLD:
            self.current_world = option.name
            self.mode = MODE_SELECT_LEVEL
        elif self.mode == MODE_SELECT_LEVEL:
            if self.save.available(self.current_world, self.current_menu_item):
                self.level_id = self.current_menu_item
                self.play()
            else:
                return False

        return True

    def read_level_info(self):
        filenames = glob(os.path.join('levels', '*.txt'))
        self.worlds = {}
        for filename in filenames:
            try:
                world = LevelSet(filename)
            except IOError:
                continue
            self.worlds[world.name] = world

    def play(self):
        self.save.set_current(self.current_world, self.level_id)
        self.mode = MODE_PLAYING
        if self.current_world == 'Tutorials':
            if self.level_id == 0:
                self.game = TutorialOne()
            elif self.level_id == 1:
                self.game = TutorialTwo()
            else:
                self.game = game.Game()
        else:
            self.game = game.Game()
        self.renderer = Renderer()
        self.game.loc_from_screen_coords = self.renderer.loc_from_screen_coords
        self.game.load_level(self.worlds[self.current_world].levels[self.level_id].value)
        self.game.start()

    def back(self):
        if self.mode == MODE_MAIN_MENU:
            self.quitting = True
        elif self.mode == MODE_SELECT_WORLD:
            self.mode = MODE_MAIN_MENU
        elif self.mode == MODE_SELECT_LEVEL:
            self.mode = MODE_SELECT_WORLD

    def start(self):
        self.draw()
        while not self.quitting:
            self.clock.tick(game.FRAME_RATE)
            if self.mode == MODE_PLAYING:
                self.game.main_loop()

                if self.game.stopping:
                    if self.game.won:
                        self.mode = MODE_WON
                        self.won_animation.start()
                        continue

                    self.mode = MODE_MAIN_MENU
                    self.draw()
                elif self.game.quitting:
                    self.quitting = True

            elif not self.process_events():
                continue

            self.draw()

    def draw(self):
        if self.mode == MODE_INTRO:
            self.screen.blit(self.intro_graphic, (0, 0))
            alpha = int(max(0, (self.intro_frame - INTRO_DELAY) * 255.0 / (INTRO_FRAMES - INTRO_DELAY)))
            self.background_menu.set_alpha(alpha)
            self.screen.blit(self.background_menu, (0, 0))
            self.intro_frame += 1
            if self.intro_frame > INTRO_FRAMES:
                self.mode = MODE_MAIN_MENU
                self.draw()
        elif self.mode == MODE_MAIN_MENU:
            #self.screen.blit(self.background, (0, 0))
            self.draw_main_menu()
        elif self.mode == MODE_SELECT_WORLD:
            self.screen.blit(self.background, (0, 0))
            self.draw_select_list()
        elif self.mode == MODE_SELECT_LEVEL:
            self.screen.fill((0, 0, 0))
            self.draw_level_list()
        elif self.mode == MODE_PLAYING:
            self.renderer.render(self.game, self.screen)
        elif self.mode == MODE_WON:
            self.renderer.render(self.game, self.screen)
            self.draw_won_overlay()
        pygame.display.flip()

    def draw_won_overlay(self):
        self.screen.blit(self.overlay_won, (0, 0))
        frame = self.won_animation.get_frame()
        if not frame:
            frame = self.won_animation.images[-1]

        w, h = frame.get_rect().size
        x = WINDOW_W / 2 - w / 2
        y = WINDOW_H / 2 - h / 2
        self.screen.blit(frame, (x, y))

        margin = 12
        text = self.menu_font.render('Level complete! Yay!', True, (255, 255, 255))
        text_pos = text.get_rect()
        text_pos.x = WINDOW_W / 2 - text_pos.width / 2
        text_pos.y = y - text_pos.height - margin
        self.screen.blit(text, text_pos)


    def draw_main_menu(self):
        self.screen.blit(self.background_menu, (0, 0))
        height = self.current_menu_item * MENU_ITEM_H + MENU_ITEM_TOP
        width = self.menu_widths[self.current_menu_item]
        self.draw_option_selector(height, width)

    def draw_level_list(self):
        margin = 8
        w = (WINDOW_W - margin) / GRID_COLS - margin
        h = (WINDOW_H - margin) / GRID_COLS - margin
        y = -h
        for i, item in enumerate(self.select_list):
            if i % GRID_COLS == 0:
                x = -w
                y += margin + h
            x += margin + w
            thickness = 4 if i == self.current_menu_item else 1

            completed = self.save.completed(self.current_world, i)
            available = self.save.available(self.current_world, i)
            stats = self.save.stats(self.current_world, i)

            colour = (172, 172, 172) if available else (64, 64, 64)
            if i == self.current_menu_item:
                border = (255, 255, 255) if available else (96, 96, 96)
            else:
                border = colour

            self.screen.fill(border,
                             (x, y, w, h))
            self.screen.fill(colour,
                             (x + thickness, y + thickness, w - 2*thickness, h - 2*thickness))
            id_text = self.menu_font.render(str(i+1), True, (0, 0, 0))
            id_pos = id_text.get_rect()
            id_pos.y = y + margin/2
            id_pos.centerx = x + w/2
            name_text = self.small_font.render(item.name, False, (0, 0, 0))
            name_pos = name_text.get_rect()
            name_pos.bottom = y + h - margin/2
            name_pos.centerx = x + w/2
            if stats:
                turns_text = self.small_font.render('Turns: %d' % stats['turns'], False, (64, 64, 64))
                turns_pos = turns_text.get_rect()
                turns_pos.bottom = id_pos.bottom + margin/2
                turns_pos.centerx = x + w/2
                doors_text = self.small_font.render('Door uses: %d' % stats.get('uses', 0), False, (64, 64, 64))
                doors_pos = doors_text.get_rect()
                doors_pos.top = turns_pos.bottom
                doors_pos.centerx = x + w/2
                self.screen.blit(turns_text, turns_pos)
                self.screen.blit(doors_text, doors_pos)

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

        margin = 3
        menu_top = WINDOW_H / 2 - menu_height / 2 + MENU_OFFSET
        for i, item in enumerate(rendered_items):
            x = WINDOW_W / 2 - item.get_width() / 2
            self.screen.blit(item, (x, menu_top))
            if i == self.current_menu_item:
                #x -= 8 + triangle_x
                self.draw_option_selector(menu_top, item.get_width())

            menu_top += max_height + margin

    def draw_option_selector(self, y, width):
        x = WINDOW_W / 2 - width / 2 - 8 - SELECTOR_W
        pygame.draw.polygon(self.screen,
                            (196, 196, 196),
                            ((x-12, y+SELECTOR_H-12),
                             (x-12, y+SELECTOR_H+12),
                             (x, y+SELECTOR_H)))
        pygame.draw.aalines(self.screen,
                            (255, 255, 255),
                            True,
                            ((x-12, y+SELECTOR_H-12),
                             (x-12, y+SELECTOR_H+12),
                             (x, y+SELECTOR_H)))

        x = WINDOW_W - x - SELECTOR_W
        pygame.draw.polygon(self.screen,
                            (196, 196, 196),
                            ((x+12, y+SELECTOR_H-12),
                             (x+12, y+SELECTOR_H+12),
                             (x, y+SELECTOR_H)))
        pygame.draw.aalines(self.screen,
                            (255, 255, 255),
                            True,
                            ((x+12, y+SELECTOR_H-12),
                             (x+12, y+SELECTOR_H+12),
                             (x, y+SELECTOR_H)))

    def process_events(self):
        if self.mode == MODE_PLAYING:
            return True

        if self.mode == MODE_INTRO:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    self.intro_frame = INTRO_FRAMES

            return True

        if self.mode == MODE_WON:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    self.mode = MODE_SELECT_WORLD
                    self.save.set_completed(self.current_world, self.level_id)
                    self.save.set_stats(self.current_world, self.level_id, self.game.turn, self.game.used_doors())
                    next_level = self.level_id + 1
                    if next_level < len(self.worlds[self.current_world].levels):
                        self.level_id = next_level
                        self.play()
                    elif self.worlds[self.current_world].next:
                        self.current_world = self.worlds[self.current_world].next
                        self.level_id = 0
                        self.play()
                    break

            return True

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quitting = True
                return False
            if e.type == pygame.KEYDOWN:
                if e.key in game.UP_KEYS:
                    if self.mode == MODE_SELECT_LEVEL:
                        if self.current_menu_item - GRID_COLS >= 0:
                            self.current_menu_item -= GRID_COLS
                        elif self.current_menu_item < len(self.select_list) % GRID_COLS:
                            self.current_menu_item -= len(self.select_list) % GRID_COLS
                        else:
                            self.current_menu_item -= len(self.select_list) % GRID_COLS + GRID_COLS
                    else:
                        self.current_menu_item -= 1
                    self.current_menu_item %= len(self.select_list)
                    self.sound.step()
                    return True
                if e.key in game.DOWN_KEYS:
                    if self.mode == MODE_SELECT_LEVEL:
                        if self.current_menu_item + GRID_COLS < len(self.select_list):
                            self.current_menu_item += GRID_COLS
                        else:
                            self.current_menu_item %= GRID_COLS
                    else:
                        self.current_menu_item += 1
                    self.current_menu_item %= len(self.select_list)
                    self.sound.step()
                    return True
                if e.key in game.LEFT_KEYS and self.mode == MODE_SELECT_LEVEL:
                    self.current_menu_item -= 1
                    self.current_menu_item %= len(self.select_list)
                    self.sound.step()
                    return True
                if e.key in game.RIGHT_KEYS and self.mode == MODE_SELECT_LEVEL:
                    self.current_menu_item += 1
                    self.current_menu_item %= len(self.select_list)
                    self.sound.step()
                    return True
                if e.key in game.ACTION_KEYS:
                    if self.select_menu():
                        self.sound.throw()
                    else:
                        self.sound.land()
                    return True
                if e.key in game.QUIT_KEYS:
                    self.back()
                    self.sound.undo()
                    return True
                if e.key in game.CHEAT_KEYS and self.mode == MODE_SELECT_LEVEL:
                    for id in range(len(self.worlds[self.current_world].levels)):
                        self.save.set_completed(self.current_world, id)
                    return True


class Label(object):
    def __init__(self, name, value=''):
        self.name = name
        self.value = value


if __name__ == '__main__':
    pygame.mixer.pre_init(44100)
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption('Dora Roarer the Door Restorer')

    launcher = Launcher(screen)
    if len(sys.argv) > 1:
        level = os.path.basename(sys.argv[1])
        launcher.mode = MODE_PLAYING
        launcher.renderer = Renderer()
        launcher.game = game.Game()
        launcher.game.load_level(level)
        launcher.game.start()
    if PROFILE:
        cProfile.run('launcher.start()', 'profiledump')
        p = pstats.Stats('profiledump')
        p.sort_stats('cumtime').print_stats(.5)
    else:
        launcher.start()
