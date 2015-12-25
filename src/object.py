### Contains definition of Game Objects
import pygame
from game import FRAME_DELAY, ANIM_DELAY, UP, DOWN, LEFT, RIGHT

NW, NE, SW, SE = range(4)
# The following are constants which together determine which bit of the tileset
# we use ("source") for the auto-tile depending on what is adjacent to us
# ("checks"). The numbers in "checks" (0-9) are indexes of the 3x3 grid of coordinates
# adjacent to the tile, starting top-left, going right then down.
# The numbers in "sources" are 1 for the "cross-roads" piece and 2-5 for the various
# parts of the 2x2 piece, as seen in the tileset.
SUBTILE_CHECKS = ((3, 1, 0), (1, 5, 2), (3, 7, 6), (7, 5, 8))
SUBTILE_SOURCES = ((5, 1, 3, 4, 2), (4, 1, 5, 2, 3), (3, 1, 5, 2, 4), (2, 1, 3, 4, 5))


class GameObject(object):
    """An object in the game world"""
    def __init__(self, name, level, location=None, char='?'):
        """Create a new GameObject with the given name, description and location."""
        self.name = name
        self._location = location
        self.old_location = location
        self.amount_moved = 1.0
        self.container = None
        self.contained = []
        self.destroyed = False
        self.flags = {}
        self.direction = DOWN

        self.z = 10
        self.char = char
        self.block_flags = []
        self.solid = False
        self.state = 'default'
        self.animation = None
        self.animation_callback = lambda: None
        self.computed_image = None

        self.history = []
        self.track_properties = ('_location', 'direction', 'container', 'contained', 'destroyed', 'flags', 'char', 'solid', 'block_flags', 'state', 'animation', 'animation_callback', 'move_dir', 'move_turns', 'move_to')

        self.special = False # Special objects override passability of things below them
        self.mass = 1
        self.move_dir = None
        self.move_turns = 0
        self.move_to = None

        self.moved_cbs = []
        self.added_cbs = []
        self.removed_cbs = []
        self.destroyed_cbs = []

        self.level = level

        if self.name[0].lower() in 'aeiou':
            self.indef_article = 'an'
        else:
            self.indef_article = 'a'
        self.def_article = 'the'
        self.prefer_definite = False

        self.facts = []

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self.old_location = self._location
        self.amount_moved = 0.0
        self._location = value
        self.level.move_object(self, self.old_location, value)
        if value:
            for thing in self.level[value][::-1]:
                if thing != self and thing.arrived(self):
                    break
        self.on_moved()

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if hasattr(self, '_level') and self._level:
            self._level.remove_object(self)
        self._level = value
        if self._level:
            self.game = self._level.game
            self._level.add_object(self)

    @property
    def image(self):
        if self.animation:
            image = self.animations[self.animation].get_frame()
            if image:
                return image
            else:
                self.animation = None
                self.animation_done()
                return None
        dir = ['up', 'down', 'left', 'right'][self.direction]
        if dir + '-' + self.state in self.state_images:
            return self.state_images[dir + '-' + self.state]
        elif self.state in self.state_images:
            return self.state_images[self.state]
        else:
            return self.state_images['default']

    def animate(self, name, callback=lambda: None):
        self.animations[name].start()
        self.animation = name
        self.animation_done = callback

    def animated_position(self):
        if self._location and self.old_location:
            dx = (self._location[0] - self.old_location[0]) * (1 - self.amount_moved)
            dy = (self._location[1] - self.old_location[1]) * (1 - self.amount_moved)
            if self.amount_moved < 1.0:
                self.amount_moved = min(1.0, self.amount_moved + FRAME_DELAY / ANIM_DELAY)
            return dx, dy
        else:
            return 0, 0

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
        base = pygame.Surface((w, h), flags=pygame.SRCALPHA)

        # Now for each corner, copy in that corner from the region we found
        # in the previous step.
        base.blit(self.state_images[names[0]], (0, 0), (0, 0, hw, hh))
        base.blit(self.state_images[names[1]], (hw, 0), (hw, 0, hw, hh))
        base.blit(self.state_images[names[2]], (0, hh), (0, hh, hw, hh))
        base.blit(self.state_images[names[3]],
                  (hw, hh),
                  (hw, hh, hw, hh))

        return base
    def indefinite(self):
        """Name of the object with indefinite article"""
        return '%s %s' % (self.indef_article, self.name)

    def definite(self):
        """Name of the object with definite article"""
        return '%s %s' % (self.def_article, self.name)

    def describe(self):
        """Get a description of the object"""
        return self.description

    def flag(self, flag):
        if flag not in self.flags or not self.flags[flag]:
            return False
        return True

    def on_added(self):
        for cb in self.added_cbs:
            cb(self)

    def on_removed(self):
        for cb in self.removed_cbs:
            cb(self)

    def on_destroyed(self):
        for cb in self.destroyed_cbs:
            cb(self)

    def on_moved(self):
        for cb in self.moved_cbs:
            cb(self)

    def blocks(self, other):
        """Return true if we block the movement of other onto us, by virtue of
           the other object's flags"""
        for flag in self.block_flags:
            if other.flag(flag): return True

        return False

    def bumped(self, other):
        """Something else bumped into us. Return False to let other objects be bumped."""
        return False

    def arrived(self, other):
        """Something else arrived on the same square as us. Return False to let other objects be landed on."""
        if self.solid:
            other.move_turns = 0
        return False

    def record_state(self, index):
        state = dict((key, getattr(self, key)) for key in self.track_properties)
        state['contained'] = self.contained[:]
        self.history = self.history[:index]
        self.history.append(state)

    def restore_state(self, index):
        state = self.history[index]
        for key, value in state.items():
            if key == '_location':
                self.old_location = self._location
                setattr(self, key, value)
                self.amount_moved = 0.0
                self.level.move_object(self, self.old_location, value)
            else:
                setattr(self, key, value)
        self.contained = state['contained'][:]

    def resolve_movement(self):
        """Resolves queued movement and return True if any happened"""
        if self.move_to:
            # Have to muck about in case moving ourselves also sets a move_to
            _move_to = self.move_to
            self.move_to = None
            self.location = _move_to
            return True
        elif self.move_turns > 0:
            self.move_turns -= 1

            newloc = self.game.coords_in_dir(self.location, self.move_dir, 1)

            if self.game.can_move_to(self, newloc):
                self.location = newloc
            else:
                self.move_turns = 0
                self.location = self.location

            return True

        return False

    def shove(self, magnitude, direction):
        self.location = self.game.coords_in_dir(self.location, direction, magnitude)

    def impulse(self, magnitude, direction):
        self.move_dir = direction
        self.move_turns = magnitude / self.mass

    def remove(self, other):
        """Remove other from me.

           Default behaviour is to place in world at current location."""

        if other in self.contained:
            other.container = None
            self.contained.remove(other)
            other.location = self.location

            other.on_removed()

            return True

    def removeself(self):
        """Remove self from any container"""
        if self.container:
            self.container.remove(self)

    def destroy(self):
        self.removeself()
        self.destroyed = True
        for obj in self.contained:
            self.remove(obj)

        self.on_destroyed()
        self.location = None

    def __contains__(self, other):
        return other in self.contained

    def __str__(self):
        return self.name


class Static(GameObject):
    def __init__(self, level, location=None):
        name = self.__class__.__name__.lower()
        GameObject.__init__(self, name, level, location)
        self.flags['static'] = True
        self.computed_image = None


class Rug(Static):
    @property
    def image(self):
        if self.computed_image:
            return self.computed_image

        x, y = self.location

        adjacent8 = [(x_, y_) for y_ in range(y-1, y+2) for x_ in range(x-1, x+2)]
        adj = []
        for ax, ay in adjacent8:
            tile = self.level[(ax, ay)]
            if tile and [1 for obj in tile if obj.name == self.name]:
                adj.append(True)
            else:
                adj.append(False)

        self.computed_image = self.autotile(adj)
        return self.computed_image

    @image.setter
    def image(self, value):
        pass


class Cracks(Static):
    pass


class Decay(Static):
    pass


class Decay2(Static):
    pass


class Alcove(Static):
    pass


class Diamond(Static):
    pass


class Painting(Static):
    pass


class Door(GameObject):
    def __init__(self, level, location):
        GameObject.__init__(self, 'door', level, location, '+')

        self.tileindex = (0,0)
        self.locked = False
        self.used = 0
        self.solid = True
        self.block_flags = ['door']
        self.state = 'default'
        self.char = '+'
        self.z = 5

        self.track_properties += ('locked', 'used')

        self.special = True
        self.flags['door'] = True

    @property
    def colour(self):
        if self.level[self.location][0].solid:
            return (255, 255, 0)
        else:
            return (255, 255, 255)

    def close(self, play_sound=True):
        self.solid = True
        self.state = 'default'
        self.char = '+'
        if play_sound:
            self.game.sound.close()

    def open(self):
        self.solid = False
        self.char = 'o'
        self.state = 'open'
        if not self.used:
            self.used = True
        self.game.sound.open()

    def on_added(self):
        GameObject.on_added(self)
        if self.container.flag('player'):
            # Place the player at his location to trigger terrain effects
            self.container.location = self.container.location

        self.close(False)

    def bumped(self, other):
        if self.solid:
            if self.locked:
                if self.key and self.key in other:
                    self.locked = False
                    return True
                else:
                    pass
            elif self.level[self.location][0].solid:
                self.open()
                return True

        return False

    def arrived(self, other):
        # Don't allow lower objects to be arrived upon
        if other.flag('door') or other.flag('player'):
            self.used += 1
        return True

    def destroy(self):
        self.animate('falling', lambda: GameObject.destroy(self))




class BigDoor(Door):
    def __init__(self, level, location):
        Door.__init__(self, level, location)
        self.name = 'bigdoor'
        self.block_flags = ['door']
        self.flags['big'] = True

        self.mass = 3

    def close(self, play_sound=True):
        Door.close(self, play_sound)
        self.block_flags = ['door']

    def open(self):
        Door.open(self)
        self.block_flags = ['big']

    #def destroy(self):
        #self.animate('falling', lambda: GameObject.destroy(self))
