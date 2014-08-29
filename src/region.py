from object import GameObject

class Region(GameObject):
    def __init__(self, name, level, location, size):
        GameObject.__init__(self, name, level, location)
        self.size = size
        self.message = None
        self.points = []

        # Explanation of the following members:
        #
        # visible is whether or not an icon is displayed when the region is active
        # the region will not become active if it is enabled
        # the region becomes active when it's enabled and all preconditions are met,
        #       it can then be activated
        # if the player has walked into the region while active, it has been activated
        #
        # in order to become active, all the regions in activate_requires must have
        #       been activated, and none of those in activate_requires_not can have been.
        self.visible = False
        self.enabled = True
        self.active = False
        self.activated = False
        self.activate_requires = []
        self.activate_requires_not = []

        self.arrived_cbs = []
        self.leaving_cbs = []

    @GameObject.location.setter
    def location(self, value):
        self._location = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self.game = self._level.game
        self._level.add_region(self)

    def restore_state(self, index):
        state = self.history[index]
        for key, value in state.items():
            setattr(self, key, value)
        self.contained = state['contained'][:]

    def set_vertices(self, vertices):
        x, y = self.location
        w, h = self.size
        self.points = []
        for p in ((px, py) for px in range(x, x+w) for py in range(y, y+h)):
            if self.in_poly(p, vertices):
                self.points.append(p)
        if not self.points:
            self.points = ('poo',)

    def in_poly(self, (px, py), vertices):
        px += .5
        py += .5
        inside = False
        vxx, vyy = vertices[-1]
        for vx, vy in vertices:
            if ((vy > py) != (vyy > py) and
                (px < ((vxx - vx) * (py - vy) / (vyy-vy) + vx))):
                inside = not inside
            vxx, vyy = vx, vy

        return inside

    def add_dependency(self, other):
        self.activate_requires.append(other)

    def add_anti_dependency(self, other):
        self.activate_requires_not.append(other)

    def check_active(self):
        self.active = False
        self.state = 'default'

        if not self.enabled:
            return False

        for req in self.activate_requires:
            if not req.activated:
                return False
        for req in self.activate_requires_not:
            if req.activated:
                return False

        self.active = True
        if self.visible:
            self.state = 'visible'

    def activate(self, other):
        self.activated = True
        self.game.display_message(self.name, self.message)
        self.level.check_active_regions()

    def arrived(self, other):
        for cb in self.arrived_cbs:
            cb(self, other)
        if other.flag('player') and self.active:
            self.activate(other)
            return False
        return True

    def leaving(self, other):
        for cb in self.leaving_cbs:
            cb(self, other)
        if other.flag('player'):
            self.game.display_message(self.name, None)
        return True

    def __contains__(self, location):
        if self.points:
            return location in self.points

        return (location[0] >= self.location[0] and
                location[1] >= self.location[1] and
                location[0] < self.location[0] + self.size[0] and
                location[1] < self.location[1] + self.size[1])

