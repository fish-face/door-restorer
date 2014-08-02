### Base class for the player and NPCs

from object import GameObject
from game import STATE_PICK

class Player(GameObject):
    def __init__(self, name='Dora', description='', location=None, *args, **kwargs):
        self.map_memory = {}

        GameObject.__init__(self, name=name, description=description, location=location, *args, **kwargs)

        self.char = '@'
        self.tiletype = 2
        self.hp = 1
        self.block_move = True
        self.z = 20

        self.track_properties += ('hp',)

        self.flags['player'] = True

    @property
    def colour(self):
        return (255, 255, 255) if not self.contained else (255, 255, 0)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self.init_map_memory(value)
        GameObject.level.fset(self, value)

    @property
    def state(self):
        if self.contained:
            if self.level.game.state == STATE_PICK:
                return 'awaiting-throw'
            else:
                return 'holding-door'
        elif self.level.game.state == STATE_PICK:
            return 'awaiting-input'
        else:
            return 'default'

    @state.setter
    def state(self, value):
        pass

    def init_map_memory(self, level):
        if level and level not in self.map_memory:
            self.map_memory[level] = [None] * level.height
            for y in xrange(level.height):
                self.map_memory[level][y] = [None] * level.width

    def definite(self):
        return self.name

    def indefinite(self):
        return self.name

    def add(self, other):
        """Put other inside me, if possible."""
        if other == self:
            return False

        if self.contained or self.game.get_objects_at(self.location, lambda x: x.block_door):
            return False

        other.removeself()
        self.contained.append(other)
        other.container = self
        other.location = None

        other.on_added()

        return True

    def destroy(self):
        self.animate('falling', self.really_destroy)
        self.game.block()

    def really_destroy(self):
        self.game.unblock()
        GameObject.destroy(self)
