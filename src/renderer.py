### Renders a level to a pygame surface

import pygame

WIN_W = 600
WIN_H = 600
MARGIN = 8
VIEW_W = WIN_W - 2 * MARGIN
VIEW_H = WIN_H - 2 * MARGIN

class Renderer:
    def __init__(self):
        self.terrain_surf = None
        self.level_surf = pygame.Surface((VIEW_W, VIEW_H))
        self.view_w = 0.75
        self.view_h = 0.75
        self.tw = 24
        self.th = 24
        self.font = pygame.font.Font('fonts/DejaVuSansMono.ttf', 12)
        self.title_font = pygame.font.Font('fonts/DejaVuSansMono.ttf', 18)
        self.centre = ()
        self.view = None

    def render(self, game, surface):
        self.render_level(game)
        # Set up areas to render to
        main_surface = surface.subsurface(MARGIN, MARGIN, VIEW_W, VIEW_H)

        main_surface.blit(self.level_surf, (0, 0))
        main_surface.blit(self.title_font.render(str(game.turn), True, (255,255,255)),
                          (1, 1))

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
            try:
                surface.blit(obj.image, ((x-dx)*tw - view.left, (y-dy)*th - view.top))
            except TypeError:
                pass

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
