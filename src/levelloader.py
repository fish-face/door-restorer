#encoding=utf8
from codecs import open
from collections import defaultdict
import os
import pytmx
import pygame

from level import Level
from object import GameObject
from player import Player
from animation import Animation
from region import Region

TILE_W = 24
TILE_H = 24
H_TILE_W = 12
H_TILE_H = 12


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

    for obj in tmx_data.getObjects():
        x = int(obj.x / TILE_W)
        y = int(obj.y / TILE_H)
        w = int(obj.width / TILE_W)
        h = int(obj.height / TILE_H)
        region = Region(obj.name, level, (x, y), (w, h))
        if hasattr(obj, 'message'):
            region.message = obj.message.decode('string-escape')
        if hasattr(obj, 'points'):
            region.set_vertices([(px/TILE_W, py/TILE_H) for (px, py) in obj.points])

    return level


UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

from object import Door
from terrain import *

TERRAINS = {}
OBJECTS = {}

name = None
obj = None
for name, obj in locals().items():
    if isinstance(obj, type) and issubclass(obj, Terrain) and obj is not Terrain:
        TERRAINS[name.lower()] = obj
    elif isinstance(obj, type) and issubclass(obj, GameObject) and obj is not GameObject:
        OBJECTS[name.lower()] = obj
