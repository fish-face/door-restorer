class Region(object):
    def __init__(self, name, level, location, size):
        self.name = name
        self.level = level
        self.location = location
        self.size = size
        self.message = None

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self.game = self._level.game
        self._level.add_region(self)

    def arrived(self, other):
        if other.flag('player'):
            self.game.display_message(self.name, self.message)
            return False
        return True

    def leaving(self, other):
        if other.flag('player'):
            self.game.display_message(self.name, None)
        return True

    def __contains__(self, location):
        return (location[0] >= self.location[0] and
                location[1] >= self.location[1] and
                location[0] < self.location[0] + self.size[0] and
                location[1] < self.location[1] + self.size[1])

