# encoding=utf-8

### Levels define the terrain making up an area


TEST_LEVEL = (
    "###########",
    "#+...>....#",
    "#....>....#",
    "#^^^^#vvvv#",
    "#....<....#",
    "#....<...X#",
    "###########")


class Level:
    mult = [[1,  0,  0, -1, -1,  0,  0,  1],
            [0,  1, -1,  0,  0, -1,  1,  0],
            [0,  1,  1,  0,  0, -1, -1,  0],
            [1,  0,  0,  1, -1,  0,  0, -1]]

    def __init__(self, game, name, width, height):
        self.game = game
        self.name = name
        self.objects = set()
        self.map = []
        self.regions = {}

        self.map = []
        self.width = width
        self.height = height

        for y in xrange(self.height):
            self.map.append([])
            for x in xrange(self.width):
                self.map[y].append([])

    def load_finished(self):
        self.statics = [obj for obj in self.objects if obj.flag('static') or obj.flag('terrain')]
        self.statics.sort(key=lambda x: x.z)
        self.dynamics = [obj for obj in self.objects if not obj.flag('static') and not obj.flag('terrain')] + self.regions.values()
        self.dynamics.sort(key=lambda x: x.z)
        self.check_active_regions()

    def get_coords_of(self, obj):
        """Get coordinates of given object or its container"""
        if not obj.container:
            return obj.location
        return self.get_coords_of(obj.container)

    #def set_terrain(self, p, terrain):
    #    x = p[0]
    #    y = p[1]
    #    if callable(terrain):
    #        terrain = terrain(self, p)

    #    if x < 0 or y < 0 or x >= self.width or y >= self.height:
    #        return
    #    if self.map[y][x]:
    #        self.map[y][x][0] = terrain
    #    else:
    #        self.map[y][x] = [terrain]

    #    terrain.level = self
    #    terrain.location = p

    #    # TODO: Nothing specifies that there must be exactly one terrain
    #    #       per tile, or even where it is in the tile's list.

    def add_region(self, region):
        if region in self.regions.values():
            return

        self.regions[region.name] = region

    def add_object(self, obj):
        """Add object to the level's list of objects"""
        if obj in self.objects:
            return

        self.objects.add(obj)

        if obj.location:
            self[obj.location].append(obj)

    def remove_object(self, obj):
        """Should only be called from obj.destroy()"""
        if obj not in self.objects:
            return

        obj.location = None
        self.objects.remove(obj)

    def move_object(self, obj, location):
        """Should only be called from obj.move"""
        regions = []
        if obj.location:
            self[obj.location].remove(obj)
            regions = [r for r in self.regions.values() if obj.location in r]
        if location:
            self[location].append(obj)
            self[location].sort(key=lambda x: x.z)
            for region in regions:
                if location not in region:
                    if region.leaving(obj): break
            for region in self.regions.values():
                if location in region:
                    if region.arrived(obj): break

    def check_active_regions(self):
        for reg in self.regions.values():
            reg.check_active()

    def get_tile(self, x, y):
        """Return all the stuff at the given location"""
        if x >= 0 and y >= 0 and x < self.width and y < self.height:
            return self.map[y][x]
        else:
            return []

    def get_tiles(self, x1, y1, x2, y2):
        """Iterator for all the tiles in the given rectangle"""
        for y in xrange(y1, y2):
            for x in xrange(x1, x2):
                yield (x, y, self.map[y][x])

    def get_statics(self):
        for obj in self.statics:
            yield (obj.location[0], obj.location[1], obj)

    def get_dynamics(self):
        for obj in self.dynamics:
            if obj.location:
                yield obj.location[0], obj.location[1], obj

    def get_region(self, name):
        return self.regions[name]

    def __getitem__(self, location):
        return self.get_tile(location[0], location[1]) if location else None

    def __contains__(self, other):
        return other in self.objects


class TestLevel(Level):
    def setup(self):
        Level.setup(self)

        self.terrain_from_array(TEST_LEVEL)
