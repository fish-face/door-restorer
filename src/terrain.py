import pygame

from object import GameObject

class Terrain(GameObject):
    def __init__(self, name, level, location):
        GameObject.__init__(self, name, level, location)
        self.z = 0
        self.flags['terrain'] = True
        self.pickup = False

PICKUP_STATES = ('wall-left', 'wall-up', 'wall-right', 'wall-down')
PICKUP_STATE_COMBOS = ['{0:04b}'.format(x) for x in range(2**4)]
class Wall(Terrain):
    def __init__(self, level, location):
        Terrain.__init__(self, 'wall', level, location)
        self.block_move = True

    def arrived(self, other):
        Terrain.arrived(self, other)
        if other.flag('door'):
            self.level.game.sound.land()

    @property
    def image(self):
        if self.computed_image:
            return self.computed_image

        x, y = self.location
        w, h = self.state_images['default'].get_size()
        hw, hh = w/2, h/2

        adjacent4 = ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1))
        adjacent8 = [(x_, y_) for y_ in range(y-1, y+2) for x_ in range(x-1, x+2)]
        blocking = []
        walls = []
        for i in range(4):
            tile = self.level[adjacent4[i]]
            if tile and tile[0].name == 'nopickup':
                blocking.append(True)
            else:
                blocking.append(False)

        for ax, ay in adjacent8:
            tile = self.level[(ax, ay)]
            if tile and tile[0].name == 'wall':
                walls.append(True)
            else:
                walls.append(False)

        base = self.autotile(walls)
        for i, block in enumerate(blocking):
            if block:
                base.blit(self.state_images[PICKUP_STATES[i]], (0, 0))

        self.computed_image = base
        return base

    @image.setter
    def image(self, value):
        pass


class NoPickup(Terrain):
    def __init__(self, level, location):
        Terrain.__init__(self, 'nopickup', level, location)

    @property
    def image(self):
        if self.computed_image:
            return self.computed_image

        x, y = self.location
        w, h = self.state_images['default'].get_size()
        hw, hh = w/2, h/2

        adjacent4 = ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1))
        blocking = []
        for i in range(4):
            tile = self.level[adjacent4[i]]
            if tile and tile[0].name == 'wall':
                blocking.append(True)
            else:
                blocking.append(False)

        base = pygame.Surface((w, h))
        base.blit(self.state_images['default'], (0, 0))
        for i, block in enumerate(blocking):
            if block:
                base.blit(self.state_images[PICKUP_STATES[i]], (0, 0))

        self.computed_image = base
        return base


class Pit(Terrain):
    def __init__(self, level, location):
        Terrain.__init__(self, 'pit', level, location)
        self.block_door = False

    @property
    def image(self):
        if self.computed_image:
            return self.computed_image

        x, y = self.location

        adjacent8 = [(x_, y_) for y_ in range(y-1, y+2) for x_ in range(x-1, x+2)]
        pits = []
        for ax, ay in adjacent8:
            tile = self.level[(ax, ay)]
            if tile and tile[0].name == 'pit':
                pits.append(True)
            else:
                pits.append(False)

        self.computed_image = self.autotile(pits)
        return self.computed_image

    @image.setter
    def image(self, value):
        pass

    def arrived(self, other):
        if other.move_turns > 0 or other.move_to:
            return False

        self.level.game.sound.fall()
        other.destroy()


class Floor(Terrain):
    def __init__(self, level, location):
        Terrain.__init__(self, 'floor', level, location)
        self.pickup = True

    #@property
    #def image(self):
    #    adjacents = ((self.location[0] - 1, self.location[1]),
    #                 (self.location[0],     self.location[1] - 1),
    #                 (self.location[0] + 1, self.location[1]),
    #                 (self.location[0],     self.location[1] + 1))
    #    blocking = ['1' if self.level[adjacents[i]][0].block_move else '0' for i in range(4)]

    #    return self.state_images['wall-%s' % (''.join(blocking))]

    #@image.setter
    #def image(self, value):
    #    for combo in PICKUP_STATE_COMBOS:
    #        surf = pygame.Surface(self.state_images['default'].get_size())
    #        surf.blit(self.state_images['default'], (0, 0))
    #        for i, state in enumerate(combo):
    #            if state == '0':
    #                continue
    #            name = PICKUP_STATES[int(i)]
    #            surf.blit(self.state_images[name], (0, 0))

    #        self.state_images['wall-%s' % (combo)] = surf


class Goal(Terrain):
    def __init__(self, level, location):
        Terrain.__init__(self, 'goal', level, location)

    def arrived(self, other):
        if other.flag('player'):
            other.game.win()



