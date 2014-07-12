#encoding=utf8
from codecs import open
from ConfigParser import ConfigParser

from level import Level
from object import GameObject
from player import Player


def load_level(game, filename):
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


class Terrain:
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

        for key in kwargs:
            setattr(self, key, kwargs[key])

    def flag(self, key):
        return False

    def bumped(self, other):
        return False

    def arrived(self, other):
        if self.block_move:
            other.move_turns = 0


class PlayerConveyor(Terrain):
    def arrived(self, other):
        Terrain.arrived(self, other)
        if not isinstance(other, Door):
            other.shove(1, self.direction)
            #other.impulse(1*other.mass, self.direction)


class Pit(Terrain):
    char = '_'
    def __init__(self):
        Terrain.__init__(self, ' ', 'pit', (1,0), False, False)
        self.bgcolour = (40, 40, 40)
        self.block_door = False

    def arrived(self, other):
        if other.move_turns > 0 or other.move_to:
            return False

        other.destroy()


class Pickup(Terrain):
    char = ','
    def __init__(self):
        Terrain.__init__(self, '.', 'pickup', (1,0), False, False)
        self.bgcolour = (80, 80, 80)
        self.pickup = True


class Goal(Terrain):
    def __init__(self):
        Terrain.__init__(self, 'X', 'goal', (2,0), False, False)

    def arrived(self, other):
        if other.flag('player'):
            other.game.win()


UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

wall = Terrain('#', 'wall', (0,0), True, True)
floor = Terrain(u'.', 'floor', (1,0), False, False)
pickup = Pickup()
space = Terrain(' ', 'space', (2,0), True, False, True)
pit = Pit()
goal = Goal()
walldown = PlayerConveyor('v', 'wall', (0,1), True, True, direction=DOWN)
wallup = PlayerConveyor('^', 'wall', (0,1), True, True, direction=UP)
wallleft = PlayerConveyor('<', 'wall', (0,1), True, True, direction=LEFT)
wallright = PlayerConveyor('>', 'wall', (0,1), True, True, direction=RIGHT)

from object import Door

TERRAINS = {}
OBJECTS = {}

name = None
obj = None
for name, obj in locals().items():
    if isinstance(obj, Terrain):
        try:
            TERRAINS[unicode(obj.__class__.char)] = obj
        except AttributeError:
            TERRAINS[unicode(obj.char)] = obj
    elif isinstance(obj, type) and issubclass(obj, GameObject) and obj is not GameObject:
        OBJECTS[name.lower()] = obj


#TERRAINS = {'#' : wall,
#            '.' : floor,
#            'X' : goal,
#            'v' : walldown,
#            '^' : wallup,
#            '<' : wallleft,
#            '>' : wallright,
#            '+' : Door}
#

