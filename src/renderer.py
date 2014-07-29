### Renders a level to a pygame surface

import pygame

WIN_W = 600
WIN_H = 600
MARGIN = 8
VIEW_W = WIN_W - 2 * MARGIN
VIEW_H = WIN_H - 2 * MARGIN

class Renderer:
    def __init__(self):
        #self.tiles = Tileset("/home/fish/Pictures/M_BISON_YESSSSSSS.jpg", 24, 24)
        self.terrain_surf = None
        self.level_surf = pygame.Surface((VIEW_W, VIEW_H))
        self.view_w = 0.75
        self.view_h = 0.75
        self.tw = 24
        self.th = 24
        #self.tiles = AsciiTiles('Deja Vu Sans Mono')
        #self.tiles = Tileset('graphics/bad%s.png', 24, 24)
        self.font = pygame.font.SysFont('Deja Vu Sans Mono', 12)
        self.title_font = pygame.font.SysFont('Deja Vu Sans Mono', 18)
        self.centre = ()
        self.view = None

    def render(self, game, surface):
        self.render_level(game)
        surface.fill((0, 0, 0))
        # Set up areas to render to
        main_surface = surface.subsurface(MARGIN, MARGIN, VIEW_W, VIEW_H)
        #sidebar = surface.subsurface(VIEW_W+MARGIN*2, MARGIN,
        #                             (WIN_W-VIEW_W-(MARGIN*3)), VIEW_H)
        #messages_surf = sidebar.subsurface(0, sidebar.get_height()/2 + MARGIN/2,
        #                                   sidebar.get_width(),
        #                                   sidebar.get_height()/2 - MARGIN/2)

        main_surface.blit(self.level_surf, (0, 0))
        main_surface.blit(self.title_font.render(str(game.turn), True, (255,255,255)),
                          (1, 1))

        #self.render_messages(sidebar, game.messages)

    def render_level(self, game):
        # Calculate viewport
        surface = self.level_surf
        level = game.level
        player = game.player

        w = surface.get_width()
        h = surface.get_height()
        tw = self.tw
        th = self.th

        if not self.terrain_surf:
            self.terrain_surf = pygame.Surface((level.width * tw, level.height * th))

            for x, y, terrain in level.get_terrain():
                self.terrain_surf.blit(terrain.image, (x*tw, y*th))

        if player.destroyed:
            player_x = level.width/2.0
            player_y = level.height/2.0
        else:
            player_x = player.location[0]
            player_y = player.location[1]

        player_view = pygame.Rect(0, 0, w * self.view_w, h * self.view_w)
        player_view.center = (player_x * tw, player_y * th)
        player_view.clamp_ip(0, 0, level.width * tw, level.height * th)
        if not self.view:
            self.view = pygame.Rect(0, 0, w, h)
            self.view.center = player_view.center
            self.view.clamp_ip(0, 0, level.width * tw, level.height * th)

        if player_view.right > self.view.right:
            self.view.right = player_view.right
        elif player_view.left < self.view.left:
            self.view.left = player_view.left

        if player_view.bottom > self.view.bottom:
            self.view.bottom = player_view.bottom
        elif player_view.top < self.view.top:
            self.view.top = player_view.top

        view = self.view

        surface.blit(self.terrain_surf, (-view.left, -view.top))

        for x, y, obj in level.get_objects():
            dx, dy = obj.animated_position()
            surface.blit(obj.image, ((x-dx)*tw - view.left, (y-dy)*th - view.top))

    def render_messages(self, surface, messages):
        surface.fill((25, 25, 25))
        text = '\n'.join(messages[-100:])
        self.draw_text(surface, text,
                       (255, 255, 255), surface.get_rect(), self.font, False)

    def draw_text(self, surface, text, color, rect, font, align_top=True):
        """Draw text on surface, wrapped to fit inside rect"""
        if isinstance(text, str):
            text = text.decode('utf-8')
        rect = pygame.Rect(rect)
        line_height = font.get_linesize()
        y = rect.top
        msgs = self.wrap_text(text, rect.width, font)
        max_msgs = rect.height/line_height

        if align_top:
            msgs = msgs[:max_msgs]
        elif len(msgs) >= max_msgs:
            msgs = msgs[len(msgs)-max_msgs:]

        for s in msgs:
            image = font.render(s, True, color)
            surface.blit(image, (rect.left, y))
            y += line_height

        return text

    def wrap_text(self, text, width, font):
        """Break text up into a list of strings which, when rendered with font, fit in width"""
        result = []

        while text:
            i = 1

            # determine if the row of text will be outside our area
            #if y + line_height > rect.bottom:
            #    break

            # determine maximum width of line
            while text[i-1] != '\n' and font.size(text[:i])[0] < width and i < len(text):
                i += 1

            if text[i-1] == '\n':
                result.append(text[:i-1])
            else:
                if i < len(text) and ' ' in text[:i]:
                    i = text.rfind(" ", 0, i) + 1
                result.append(text[:i])
            text = text[i:]

        return result


class BaseTileset(object):
    def __init__(self, width, height):
        self.base_width = width
        self.base_height = height
        self.scale = 1.0

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        value = min(value, 4)
        value = max(value, 0.0625)
        self._scale = value
        self.tile_width = int(self.base_width * value)
        self.tile_height = int(self.base_height * value)
        self.dim_overlay = pygame.Surface((self.tile_width,
                                           self.tile_height))
        self.dim_overlay.fill((0,0,0))
        self.picker = pygame.surface.Surface((int(self.tile_width), int(self.tile_height)), pygame.SRCALPHA)
        self.picker.fill((0, 0, 0, 0))
        pygame.draw.rect(self.picker,
                         (255, 255, 255),
                         (0, 0, self.tile_width, self.tile_height), 1)

class Tileset(BaseTileset):
    def __init__(self, filename, width, height):
        self.filename = filename
        BaseTileset.__init__(self, width, height)

    def load_tile_table(self, filename):
        self.tile_table = []
        #for i, name in enumerate(('terrain', 'objects', 'actors')):
        #    image = pygame.image.load(filename % name).convert_alpha()
        #    orig_width, orig_height = image.get_size()
        #    # Scale the image based on how large tiles we want
        #    image = pygame.transform.scale(image,
        #                                (self.tile_width*orig_width/self.base_width,
        #                                    self.tile_height*orig_height/self.base_height))
        #    image_width, image_height = image.get_size()
        #    #image.set_colorkey((255, 255, 255))
        #    tile_table = []
        #    for tile_x in range(0, orig_width/self.base_width):
        #        line = []
        #        tile_table.append(line)
        #        for tile_y in range(0, orig_height/self.base_height):
        #            rect = (tile_x*self.tile_width, tile_y*self.tile_height,
        #                    self.tile_width, self.tile_height)
        #            line.append(image.subsurface(rect))
        #    self.tile_table.append(tile_table)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        value = min(value, 4)
        value = max(value, 0.0625)
        # Constrain the real scale value to produce integer values
        constrained = int(self.base_width * value) / float(self.base_width)
        BaseTileset.scale.fset(self, constrained)
        # Store the given scale value to prevent zooming getting stuck
        self._scale = value
        self.load_tile_table(self.filename)
    def __getitem__(self, thing):
        return thing.image
        #return self.tile_table[thing.tiletype][thing.tileindex[0]][thing.tileindex[1]]

class AsciiTiles(Tileset):
    def __init__(self, font):
        self.fontname = font
        BaseTileset.__init__(self, 20, 20)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        BaseTileset.scale.fset(self, value)
        self.font = pygame.font.SysFont(self.fontname, int(18 * value))
        self.cache = {}

    def __getitem__(self, thing):
        char = getattr(thing, 'char', '?')
        colour = getattr(thing, 'colour', (255,255,255))
        bgcolour = getattr(thing, 'bgcolour', (64,64,64))
        key = (char, colour, bgcolour)
        if key not in self.cache:
            rendered = self.font.render(char, True, colour)
            self.cache[key] = pygame.surface.Surface((self.tile_width, self.tile_height))
            self.cache[key].fill(bgcolour)
            self.cache[key].blit(rendered, ((self.tile_width-rendered.get_width())/2,
                                             (self.tile_height-rendered.get_height())/2))
            #pygame.draw.rect(self.cache[key], (32,32,32), (0,0,self.tile_width, self.tile_height+1), 1)

        return self.cache[key]
