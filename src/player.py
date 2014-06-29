### Base class for the player and NPCs

from object import GameObject

class Player(GameObject):
    def __init__(self, name, description='', location=None, *args, **kwargs):
        self.map_memory = {}

        GameObject.__init__(self, name=name, description=description, location=location, *args, **kwargs)

        self.char = '@'
        self.tiletype = 2
        self.hp = 1
        self.block_move = True
        self.z = 20

        self.flags['player'] = True

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self.init_map_memory(value)
        GameObject.level.fset(self, value)

    def init_map_memory(self, level):
        if level and level not in self.map_memory:
            self.map_memory[level] = [None] * level.height
            for y in xrange(level.height):
                self.map_memory[level][y] = [None] * level.width

    def update_fov(self):
        """I moved/level updated and I need to recalculate what I can see"""
        #self.fov = self.level.get_fov(self.location)
        class DummyFov:
            def __contains__(self, _):
                return True
            def __getitem__(self, _):
                return 1

        self.fov = DummyFov()
        #for p in self.fov:
        mm = self.map_memory[self.level]
        for y in range(self.level.height):
            row = mm[y]
            for x in range(self.level.width):
                row[x] = self.level[(x,y)]

    def definite(self):
        return self.name

    def indefinite(self):
        return self.name

    def on_moved(self):
        if self.location:
            self.update_fov()

    def add(self, other):
        """Put other inside me, if possible."""
        if other == self:
            return False

        if self.contained:
            return False

        other.removeself()
        self.contained.append(other)
        other.container = self
        other.location = None

        other.on_added()

        return True

    def destroy(self):
        # Override default behaviour; the player should never actually be destroyed
        pass

