#encoding=utf8
from codecs import open
from ConfigParser import ConfigParser
from collections import defaultdict
import os
import pytmx
import pygame

from level import Level
from object import GameObject
from player import Player
from animation import Animation


def _load_level(game, filename):
    config = ConfigParser()
    try:
        config.read(filename)
        raw = [line.rstrip('\r\n') for line in open(filename, 'r', encoding='utf-8')]
    except IOError:
        return None

    started = False
    terrain = []
    for line in raw:
        if started:
            if line:
                terrain.append(line)
        elif line == u'terrain = ':
            started = True
    if not started:
        print 'Level %s has no Terrain section' % filename
        return None
    if not terrain:
        print 'Level %s has no Terrain' % filename
        return None

    name = config.get('Main', 'Name')
    width = len(terrain[0])
    height = len(terrain)
    level = Level(game, name, width, height)

    for y in xrange(height):
        for x in xrange(width):
            try:
                char = terrain[y][x]
            except IndexError:
                print 'Level %s is not rectangular' % filename
                return None
            try:
                t = TERRAINS[char]
            except KeyError:
                print 'Unsupported terrain type in %s: %s' % (filename, char)
                return None

            if callable(t):
                level.set_terrain((x, y), floor)
                print t(level, (x, y))
            else:
                level.set_terrain((x, y), t)

    try:
        start = config.get('Main', 'Start').split(', ')
    except:
        print 'Level %s has no start coordinates' % (filename)

    try:
        start = (int(start[0]), int(start[1]))
    except:
        print 'Level %s has invalid start coordinates \'%s\'' % (filename, start)
    level.player = Player(location=start, name='you', level=level, description='The Player')

    try:
        for objname, coords in config.items('Objects'):
            try:
                objtype = OBJECTS[objname]
                coords = [p.split(', ') for p in coords.split('\n')]
                locations = [(int(p[0]), int(p[1])) for p in coords]
                objs = [objtype(level, l) for l in locations]
            except:
                print 'Level %s has invalid list of \'%s\' objects' % (filename, objname)
                return None
    except:
        print 'Level %s has invalid Objects section' % (filename)
        return None
    return level


def load_level(game, filename):
    filename = os.path.join('levels', filename)
    try:
        tmx_data = pytmx.load_pygame(filename, pixelalpha=True)
    except:
        print 'Level %s could not be read as a TMX file.' % (filename)
        raise

    try:
        name = tmx_data.name
    except AttributeError:
        print 'Level %s has no name: invalid level file.' % (filename)

    width = tmx_data.width
    height = tmx_data.height

    state_images = defaultdict(dict)
    animations = defaultdict(lambda: defaultdict(Animation))

    for tile_id, properties in tmx_data.tile_properties.items():
        image = tmx_data.getTileImageByGid(tile_id)
        try:
            name = properties['name']
        except KeyError:
            continue

        state = properties.get('state', 'default')
        frame = properties.get('frame', None)
        if frame:
            delay = properties.get('frame-delay', '4')
            try:
                delay = int(delay)
            except ValueError:
                print "Level %s has invalid frame delay of %s for frame %s/%s/%s" % (filename, delay, name, state, frame)

            try:
                frame = int(frame)
            except ValueError:
                print "Level %s has invalid frame: %s/%s/%s" % (filename, name, state, frame)

            animations[name][state].add_frame(frame, image, delay)
        else:
            state_images[name][state] = image

    for state in animations.values():
        for animation in state.values():
            animation.finalise()

    level = Level(game, name, width, height)
    for (x, y, tile) in tmx_data.tilelayers[0]:
        if tile == 0:
            continue
        name = tmx_data.tile_properties[tile]['name']
        terrain = TERRAINS[name]()
        level.set_terrain((x, y), terrain)
        terrain.state_images = state_images[name]
        terrain.image = state_images[name]['default']

    for layer in tmx_data.tilelayers[1:]:
        for (x, y, tile) in layer:
            if tile == 0:
                continue
            name = tmx_data.tile_properties[tile]['name']
            state = tmx_data.tile_properties[tile].get('state', 'default')
            objtype = OBJECTS[name]
            obj = objtype(level=level, location=(x, y))
            obj.state = state
            obj.state_images = state_images[name]

            obj.animations = animations[name]
            if isinstance(obj, Player):
                level.player = obj

    return level


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

        for key in kwargs:
            setattr(self, key, kwargs[key])

    def flag(self, key):
        return False

    def bumped(self, other):
        return False

    def arrived(self, other):
        if self.block_move:
            other.move_turns = 0


class Wall(Terrain):
    def __init__(self):
        Terrain.__init__(self, '#', 'wall', (0,0), True, True)

    def arrived(self, other):
        Terrain.arrived(self, other)
        if other.flag('door'):
            self.level.game.sound.land()


class Floor(Terrain):
    def __init__(self):
        Terrain.__init__(self, u'.', 'floor', (1,0), False, False)


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

    def arrived(self, other):
        if other.move_turns > 0 or other.move_to:
            return False

        self.level.game.sound.fall()
        other.destroy()


PICKUP_STATES = ('wall-left', 'wall-up', 'wall-right', 'wall-down')
PICKUP_STATE_COMBOS = ['{0:04b}'.format(x) for x in range(2**4)]
class Pickup(Terrain):
    char = ','
    def __init__(self):
        Terrain.__init__(self, '.', 'pickup', (1,0), False, False)
        self.bgcolour = (80, 80, 80)
        self.pickup = True

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


class Goal(Terrain):
    def __init__(self):
        Terrain.__init__(self, 'X', 'goal', (2,0), False, False)

    def arrived(self, other):
        if other.flag('player'):
            other.game.win()


UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

from object import Door

TERRAINS = {}
OBJECTS = {}

name = None
obj = None
for name, obj in locals().items():
    if isinstance(obj, type) and issubclass(obj, Terrain) and obj is not Terrain:
        TERRAINS[name.lower()] = obj
    elif isinstance(obj, type) and issubclass(obj, GameObject) and obj is not GameObject:
        OBJECTS[name.lower()] = obj
