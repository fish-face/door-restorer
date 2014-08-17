import pygame

NW, NE, SW, SE = range(4)
# The following are constants which together determine which bit of the tileset
# we use ("source") for the auto-tile depending on what is adjacent to us
# ("checks"). The numbers in "checks" (0-9) are indexes of the 3x3 grid of coordinates
# adjacent to the tile, starting top-left, going right then down.
# The numbers in "sources" are 1 for the "cross-roads" piece and 2-5 for the various
# parts of the 2x2 piece, as seen in the tileset.
SUBTILE_CHECKS = ((3, 1, 0), (1, 5, 2), (3, 7, 6), (7, 5, 8))
SUBTILE_SOURCES = ((5, 1, 3, 4, 2), (4, 1, 5, 2, 3), (3, 1, 5, 2, 4), (2, 1, 3, 4, 5))

class Terrain(object):
    def __init__(self, char, name, index, block_move, block_sight, block_door=False, **kwargs):
        self.char = char
        self.name = name
        self.tiletype = 0
        self.tileindex = index
        self.block_move = block_move
        self.block_sight = block_sight
        self.block_door = block_door
        self.pickup = False
        self.z = 0
        self.state_images = {}
        self.computed_image = None

        for key in kwargs:
            setattr(self, key, kwargs[key])

    def flag(self, key):
        return False

    def bumped(self, other):
        return False

    def arrived(self, other):
        if self.block_move:
            other.move_turns = 0

    def autotile(self, connections, prefix='autotile-'):
        w, h = self.state_images['default'].get_size()
        hw, hh = w/2, h/2

        # First go through and determine which subtile regions to use for each corner
        subtiles = []
        for corner in (NW, NE, SW, SE):
            checks = SUBTILE_CHECKS[corner]
            sources = SUBTILE_SOURCES[corner]
            if connections[checks[0]]:
                if connections[checks[1]]:
                    if connections[checks[2]]:
                        subtiles.append(sources[0])
                    else:
                        subtiles.append(sources[1])
                else:
                    subtiles.append(sources[2])
            else:
                if connections[checks[1]]:
                    subtiles.append(sources[3])
                else:
                    subtiles.append(sources[4])

        names = [prefix + str(src) for src in subtiles]
        base = pygame.Surface((w, h))

        # Now for each corner, copy in that corner from the region we found
        # in the previous step.
        base.blit(self.state_images[names[0]], (0, 0), (0, 0, hw, hh))
        base.blit(self.state_images[names[1]], (hw, 0), (hw, 0, hw, hh))
        base.blit(self.state_images[names[2]], (0, hh), (0, hh, hw, hh))
        base.blit(self.state_images[names[3]],
                  (hw, hh),
                  (hw, hh, hw, hh))

        return base


PICKUP_STATES = ('wall-left', 'wall-up', 'wall-right', 'wall-down')
PICKUP_STATE_COMBOS = ['{0:04b}'.format(x) for x in range(2**4)]
class Wall(Terrain):
    def __init__(self):
        Terrain.__init__(self, '#', 'wall', (0,0), True, True)

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
    def __init__(self):
        Terrain.__init__(self, u'.', 'nopickup', (1,0), False, False)

    @property
    def image(self):
        adjacents = ((self.location[0] - 1, self.location[1]),
                     (self.location[0],     self.location[1] - 1),
                     (self.location[0] + 1, self.location[1]),
                     (self.location[0],     self.location[1] + 1))
        blocking = ['1' if self.level[adjacents[i]][0].block_move else '0' for i in range(4)]

        return self.state_images['wall-%s' % (''.join(blocking))]

    @image.setter
    def image(self, value):
        for combo in PICKUP_STATE_COMBOS:
            surf = pygame.Surface(self.state_images['default'].get_size())
            surf.blit(self.state_images['default'], (0, 0))
            for i, state in enumerate(combo):
                if state == '0':
                    continue
                name = PICKUP_STATES[int(i)]
                surf.blit(self.state_images[name], (0, 0))

            self.state_images['wall-%s' % (combo)] = surf


class PlayerConveyor(Terrain):
    def arrived(self, other):
        Terrain.arrived(self, other)
        if not isinstance(other, Door):
            other.shove(1, self.direction)


class Pit(Terrain):
    char = '_'
    def __init__(self):
        Terrain.__init__(self, ' ', 'pit', (1,0), False, False)
        self.bgcolour = (40, 40, 40)
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
    char = ','
    def __init__(self):
        Terrain.__init__(self, '.', 'floor', (1,0), False, False)
        self.bgcolour = (80, 80, 80)
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
    def __init__(self):
        Terrain.__init__(self, 'X', 'goal', (2,0), False, False)

    def arrived(self, other):
        if other.flag('player'):
            other.game.win()



