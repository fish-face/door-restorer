### The World knows about the map, terrain, objects, etc.

STATE_NORMAL = 0
STATE_PICK = 1

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

import sys
import pygame
from collections import defaultdict

from renderer import Renderer
from levelloader import load_level
from player import Player


UP_KEYS = (pygame.K_UP, pygame.K_w, pygame.K_k)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s, pygame.K_j)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_h)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d, pygame.K_l)

PICKUP_KEYS = (pygame.K_RETURN, pygame.K_e, pygame.K_COMMA)
THROW_KEYS = (pygame.K_SPACE, pygame.K_f, pygame.K_t)

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.objectives = []
        self.messages = []
        self.state = STATE_NORMAL
        self.player_turn = True

        pygame.key.set_repeat(1, 200)

        self.quitting = False
        self.renderer = Renderer()
        self.clock = pygame.time.Clock()
        self.framerates = []

        self.font = pygame.font.SysFont('Sans', 18)

        self.level = load_level(self, 'levels/test_level.txt')
        if not self.level:
            self.quitting = True

        self.player = self.level.player
        #self.player = Player(location=(1, 1), name='you', level=self.level, description='The Player')

    def can_move_to(self, obj, location):
        tile = self.level[location]
        if not tile:
            return False

        if obj.flag('door'):
            for thing in tile:
                if thing.block_door:
                    return False
            return True

        if tile[0].block_move:
            # If the terrain blocks movement, then, if there is a door in the tile, use its state
            for thing in tile[:0:-1]:
                if thing.flag('door'):
                    return not thing.block_move
            return False
        else:
            for thing in tile[1:]:
                if thing.block_move:
                    return False
        return True

    def get_objects_at(self, location, test=None):
        #First item at a location is always terrain
        if test is None:
            return self.level[location][1:]
        else:
            return [obj for obj in self.level[location][1:] if test(obj)]

    def win(self):
        #self.describe("You win!")
        self.quitting = True

    def start(self):
        if not self.quitting:
            self.update()
        while not self.quitting:
            self.main_loop()

    def main_loop(self):
        delay = self.clock.tick(30)
        self.framerates.insert(0, 1000.0/delay)
        self.framerates = self.framerates[:50]
        framerate = sum(self.framerates)/50.0
        self.process_events()
        self.renderer.render(self, self.screen)
        self.screen.blit(self.font.render('%d fps' % framerate, True, (255,255,255)),
                    (1, 1))
        pygame.display.flip()

    def process_events(self):
        took_turn = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quitting = True
                return

            if self.player_turn:
                if e.type == pygame.KEYDOWN:
                    took_turn = self.keypressed(e)
                elif e.type == pygame.MOUSEBUTTONUP:
                    took_turn = self.clicked(e)
            else:
                took_turn = True

        if took_turn or not self.player_turn:
            self.update()

    def throw(self, direction):
        for obj in self.player.contained:
            self.player.remove(obj)
            obj.impulse(3, direction)
            self.player_turn = False
            #self.player.throw(obj, direction)
        self.state = STATE_NORMAL

    def keypressed(self, e):
        took_turn = False
        if self.state == STATE_PICK:
            if e.key in LEFT_KEYS:
                self.pick_direction_done(LEFT)
            elif e.key in RIGHT_KEYS:
                self.pick_direction_done(RIGHT)
            elif e.key in UP_KEYS:
                self.pick_direction_done(UP)
            elif e.key in DOWN_KEYS:
                self.pick_direction_done(DOWN)
        elif self.state == STATE_NORMAL:
            newloc = list(self.player.location)
            if e.key in LEFT_KEYS:
                newloc[0] -= 1
            elif e.key in RIGHT_KEYS:
                newloc[0] += 1
            elif e.key in UP_KEYS:
                newloc[1] -= 1
            elif e.key in DOWN_KEYS:
                newloc[1] += 1
            newloc = tuple(newloc)

            if newloc != self.player.location:
                if self.can_move_to(self.player, newloc):
                    self.player.location = newloc
                    took_turn = True
                else:
                    for thing in self.level[newloc]:
                        if thing.bumped(self.player):
                            took_turn = True
                            break

            if e.key in PICKUP_KEYS:
                for obj in self.get_objects_at(self.player.location):
                    if self.player.add(obj):
                        #self.describe('You pick up %s' % obj.indefinite())
                        took_turn = True

            #elif e.key == pygame.K_d:
            #    for obj in self.player.contained:
            #        #self.describe('You drop %s' % obj.indefinite())
            #        took_turn = True

            elif e.key in THROW_KEYS:
                self.pick_direction(self.throw)

        return took_turn

    def pick_direction(self, handler):
        """Enter targeting mode"""
        self.state = STATE_PICK
        self.pick_handler = handler

    def pick_direction_done(self, direction):
        self.state = STATE_NORMAL
        self.pick_handler(direction)

    def clicked(self, e):
        if e.button == 1:
            pass
        if e.button == 4:
            self.renderer.tiles.scale *= 1.1
            self.renderer.render_level(self)
        elif e.button == 5:
            self.renderer.tiles.scale *= 0.9
            self.renderer.render_level(self)

        return False

    def update(self):
        # level.objects is a set, so the order of evaluation is undefined
        self.player_turn = True

        for obj in self.level.objects:
            if obj.resolve_movement():
                self.player_turn = False

        self.player.update_fov()
        self.renderer.render_level(self)

