### Contains definition of Game Objects


class GameObject(object):
    """An object in the game world"""
    def __init__(self, name, level, description='', location=None, char='?'):
        """Create a new GameObject with the given name, description and location."""
        self.name = name
        self.description = description
        self._location = location
        self.container = None
        self.contained = []
        self.destroyed = False
        self.flags = {}
        #TODO: There should probably be a better way of doing flags

        self.tiletype = 1
        self.tileindex = (0,0)
        self.z = 10
        self.char = char
        self.block_sight = False
        self.block_move = False

        self.mass = 1
        self.move_dir = None
        self.move_turns = 0

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

    #TODO: something something locations vs containers
    #TODO: No, really???

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self.level.move_object(self, value)

        self._location = value
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

    def bumped(self, other):
        """Something else bumped into us. Return False to let other objects be bumped."""
        return False

    def arrived(self, other):
        """Something else arrived on the same square as us. Return False to let other objects be landed on."""
        return False

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
        #TODO if we get deleted, will there be references to us hanging around?
        self.removeself()
        for obj in self.contained:
            self.remove(obj)
        self.destroyed = True

        self.on_destroyed()
        self.level.remove_object(self)

    def __contains__(self, other):
        return other in self.contained

    def __str__(self):
        return self.name


class Door(GameObject):
    def __init__(self, level, location):
        GameObject.__init__(self, 'door', level, 'A wooden door', location, '+')

        self.tileindex = (0,0)
        self.locked = False
        self.close()
        self.z = 5

        self.flags['door'] = True

    def close(self):
        self.block_move = True
        self.block_sight = True
        self.tileindex = (0,0)
        self.char = '+'

    def open(self):
        self.block_move = False
        self.block_sight = False
        self.char = 'o'
        self.tileindex = (1,0)

    def on_added(self):
        GameObject.on_added(self)
        if self.container.flag('player'):
            # Place the player at his location to trigger terrain effects
            self.container.location = self.container.location

        self.close()

    def bumped(self, other):
        if self.block_move:
            if self.locked:
                if self.key and self.key in other:
                    #self.game.describe('%s unlocked %s' % (other.definite(), self.definite()))
                    self.locked = False
                else:
                    pass
                    #self.game.describe('%s is locked' % (self.definite()))
            else:
                #self.game.describe('%s opened %s' % (other.definite(), self.definite()))
                self.block_move = False
                self.block_sight = False
                self.char = 'o'
                self.tileindex = (1,0)
                self.open()
            return True

        return False

    def arrived(self, other):
        # Don't allow lower objects to be arrived upon
        return True

