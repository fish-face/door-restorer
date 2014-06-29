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
        self.regions = []

        self.set_cursor(0,0)
        self.map = []
        self.width = width
        self.height = height

        for y in xrange(self.height):
            self.map.append([])
            for x in xrange(self.width):
                self.map[y].append([])

    def set_cursor(self, x, y):
        """Set the level's origin; all terrain-drawing will be translated by this amount"""
        self.x = x
        self.y = y

    def translate(self, x, y):
        """Like set_cursor but relative"""
        self.x += x
        self.y += y

    def get_coords_of(self, obj):
        """Get coordinates of given object or its container"""
        if not obj.container:
            return obj.location
        return self.get_coords_of(obj.container)

    def set_terrain(self, p, terrain):
        x = p[0] + self.x
        y = p[1] + self.y
        if callable(terrain):
            terrain = terrain(self, p)

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        if self.map[y][x]:
            self.map[y][x][0] = terrain
        else:
            self.map[y][x] = [terrain]

        # TODO: Nothing specifies that there must be exactly one terrain
        #       per tile, or even where it is in the tile's list.

    def block_sight(self, p):
        """Return whether the tile at p blocks sight"""
        for thing in self[p]:
            if thing is None or thing.block_sight:
                return True
        return False

    def get_fov(self, location):
        """Get the set of locations that can be seen from the given location"""
        light = set((location,))
        light = {location: 1}
        radius = 20
        for oct in range(8):
            self._cast_light(
                location[0], location[1], 1, 1.0, 0.0, radius,
                self.mult[0][oct], self.mult[1][oct],
                self.mult[2][oct], self.mult[3][oct], 0, light)

        return light

    def _cast_light(self, cx, cy, row, start, end, radius, xx, xy, yx, yy, id, light):
        """Recursive lightcasting function, obtained from
        http://www.roguebasin.com/index.php?title=Python_shadowcasting_implementation"""
        if start < end:
            return
        radius_squared = radius*radius
        for j in range(row, radius+1):
            dx, dy = -j-1, -j
            blocked = False
            while dx <= 0:
                dx += 1
                # Translate the dx, dy coordinates into map coordinates:
                p = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy

                if p[0] < 0 or p[0] >= self.width or p[1] < 0 or p[1] >= self.height:
                    continue

                # l_slope and r_slope store the slopes of the left and right
                # extremities of the square we're considering:
                l_slope, r_slope = (dx-0.5)/(dy+0.5), (dx+0.5)/(dy-0.5)
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # Our light beam is touching this square; light it:
                    dist_squared = dx**2 + dy**2
                    if dist_squared < radius_squared:
                        light[p] = dist_squared
                    if blocked:
                        # we're scanning a row of blocked squares:
                        if self.block_sight(p):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self.block_sight(p) and j < radius:
                            # This is a blocking square, start a child scan:
                            blocked = True
                            self._cast_light(cx, cy, j+1, start, l_slope,
                                             radius, xx, xy, yx, yy, id+1, light)
                            new_start = r_slope
            # Row is scanned; do next row unless last square was blocked:
            if blocked:
                break

        if not points:
            return False
        connected = []
        self.get_flood(points[0][0], points[0][1], set(points), connected)
        if len(set(connected)) == len(set(points)):
            return True
        else:
            return False

    def get_flood(self, x, y, points, connected):
        if (x,y) in points and (x,y) not in connected:
            connected.append((x,y))
        else:
            return

        self.get_flood(x+1, y, points, connected)
        self.get_flood(x-1, y, points, connected)
        self.get_flood(x, y+1, points, connected)
        self.get_flood(x, y-1, points, connected)

    def add_object(self, obj):
        """Add object to the level's list of objects"""
        if obj in self.objects:
            return

        self.objects.add(obj)

        #Translate by our cursor coords - this should only happen during level generation.
        if obj.location:
            x, y = obj.location
            self[(x,y)].append(obj)
            obj.location = (x+self.x, y+self.y)

    def remove_object(self, obj):
        """Should only be called from obj.destroy()"""
        if obj not in self.objects:
            return

        obj.location = None
        self.objects.remove(obj)

    def move_object(self, obj, location):
        """Should only be called from obj.move"""
        if obj.location:
            self[obj.location].remove(obj)
        if location:
            self[location].append(obj)
            self[location].sort(key=lambda x: x.z)
            for thing in self[location][::-1]:
                if thing != obj and thing.arrived(obj):
                    break

    def get_tile(self, x, y):
        """Return all the stuff at the given location"""
        try:
            return self.map[y][x]
        except (KeyError, IndexError):
            return []

    def get_tiles(self, x1, y1, x2, y2):
        """Iterator for all the tiles in the given rectangle"""
        for y in xrange(y1, y2):
            for x in xrange(x1, x2):
                yield (x, y, self.map[y][x])

    def __getitem__(self, location):
        return self.get_tile(location[0], location[1]) if location else None

    def __contains__(self, other):
        return other in self.objects


class TestLevel(Level):
    def setup(self):
        Level.setup(self)

        self.terrain_from_array(TEST_LEVEL)
