STATE_NORMAL = 0
STATE_PICK = 1
STATE_LOCKED = 2
STATE_READING = 3

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

FRAME_RATE = 60
FRAME_DELAY = 1000.0/FRAME_RATE
ANIM_DELAY = FRAME_DELAY * 5
UPDATE_DELAY = FRAME_DELAY * 2
TURN_DELAY = FRAME_DELAY * 6

import pygame

from renderer import Renderer
from sound import SoundPlayer
from levelloader import load_level


UP_KEYS = (pygame.K_UP, pygame.K_w, pygame.K_k)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s, pygame.K_j)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_h)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d, pygame.K_l)

DIR_MAP = dict((k, d) for keys, d in ((UP_KEYS, UP), (DOWN_KEYS, DOWN), (LEFT_KEYS, LEFT), (RIGHT_KEYS, RIGHT)) for k in keys)

ACTION_KEYS = (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN, pygame.K_x)
RESTART_KEYS = (pygame.K_r,)
UNDO_KEYS = (pygame.K_u, pygame.K_z)
CHEAT_KEYS = (pygame.K_c,)
QUIT_KEYS = (pygame.K_q,)

HOLDABLE_KEYS = UP_KEYS + DOWN_KEYS + LEFT_KEYS + RIGHT_KEYS + UNDO_KEYS


class Game:
    def __init__(self):
        self.sound = SoundPlayer()

        #self.font = pygame.font.SysFont('Sans', 18)

    def load_level(self, filename):
        self.level_file = filename
        self.level = load_level(self, filename)
        if not self.level:
            self.stopping = True

        self.player = self.level.player

    def can_move_to(self, obj, location):
        tile = self.level[location]
        if not tile:
            return False

        if obj.flag('player') and self.cheating:
            return True

        if obj.special:
            for thing in tile:
                if thing.blocks(obj):
                    return False
            return True

        if tile[0].solid:
            # If the terrain is solid and there is a special object on the tile, use its state.
            for thing in tile[:0:-1]:
                if thing.special:
                    if obj.flag('player'):
                        # Don't allow the player to walk through if they're carrying something
                        # that the special object blocks
                        for c in obj.contained:
                            if thing.blocks(c): return False
                    return not thing.solid
            return False
        else:
            for thing in tile[1:]:
                if thing.solid:
                    return False
        return True

    def get_objects_at(self, location, test=None):
        #First item at a location is always terrain
        if test is None:
            return self.level[location][1:]
        else:
            return [obj for obj in self.level[location][1:] if test(obj)]

    @staticmethod
    def coords_in_dir(loc, dir, dist):
        if loc is None:
            return None

        loc = list(loc)
        if dir == LEFT:
            loc[0] -= dist
        elif dir == RIGHT:
            loc[0] += dist
        elif dir == UP:
            loc[1] -= dist
        elif dir == DOWN:
            loc[1] += dist
        return tuple(loc)

    def failed_move(self, location):
        pass

    def action(self, direction):
        if self.player.contained:
            self.throw(direction)
        elif self.pickup(direction):
            pass
        elif self.close(direction):
            pass
        else:
            # Took no action
            return False
        return True

    def pickup(self, direction):
        pickup_loc = self.coords_in_dir(self.player.location, direction, 1)
        self.player.direction = direction

        success = False
        for obj in self.get_objects_at(pickup_loc)[::-1]:
            if obj.flag('door'):
                if self.level[pickup_loc][0].solid and not self.level[self.player.location][0].pickup:
                    continue
            if self.player.add(obj):
                success = True

        if success:
            self.sound.pickup()

        return success

    def close(self, direction):
        self.player.direction = direction
        close_loc = self.coords_in_dir(self.player.location, direction, 1)
        for obj in self.get_objects_at(close_loc):
            if obj.flag('door') and not obj.solid:
                obj.close()
                return True

    def throw(self, direction):
        self.player.direction = direction
        success = False
        for obj in self.player.contained:
            self.player.remove(obj)
            obj.impulse(3, direction)
            self.schedule_update()
            self.player_turn = False
            success = True
        if success:
            self.sound.throw()
        return success

    def win(self):
        #self.quitting = True
        self.player.animate('descending', self.end)
        self.block()
        self.won = True

    def end(self):
        self.stopping = True

    def display_message(self, source, message):
        if message != self.message:
            if message:
                self.msg_anim_frame = 0
            else:
                self.msg_anim_frame = -20

            self.message = message
            self.message_src = source

    def msg_anim_pos(self):
        if self.msg_anim_frame < 24:
            self.msg_anim_frame += 1
        return self.msg_anim_frame / 24.0

    def start(self):
        self.turn = 0
        self.messages = []
        self.msg_anim_frame = 0
        self.state = STATE_NORMAL
        self.cheating = False
        self.player_turn = True
        self.next_turn = 0
        self.next_update = 0
        self.won = False
        self.message = None

        self.stopping = False
        self.quitting = False

        for obj in self.level.objects:
            obj.location = obj.location
            obj.record_state(self.turn)
        if not self.quitting:
            self.update()
        #while not self.quitting:
        #    self.main_loop()

    def main_loop(self):
        self.player_turn = pygame.time.get_ticks() > self.next_turn
        took_turn = self.process_events()
        if took_turn:
            self.next_turn = pygame.time.get_ticks() + TURN_DELAY

        if took_turn or (not self.player_turn and pygame.time.get_ticks() > self.next_update):
            self.update()

    def process_events(self):
        took_turn = False
        if pygame.event.get(pygame.QUIT):
            self.quitting = True
            return False

        if not self.player_turn:
            return False

        held_keys = [key for key in HOLDABLE_KEYS if pygame.key.get_pressed()[key]]
        if held_keys:
            took_turn = self.keyheld(held_keys)
        if not took_turn:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    took_turn = self.keypressed(e)
                elif e.type == pygame.MOUSEBUTTONUP:
                    took_turn = self.clicked(e)

        if took_turn:
            self.turn += 1
            for obj in self.level.dynamics:
                obj.record_state(self.turn)

        return took_turn

    def keyheld(self, keys):
        took_turn = False
        if self.state == STATE_NORMAL:
            dirs = [DIR_MAP[key] for key in keys if key in DIR_MAP]
            if len(set(dirs)) == 1:
                dir = dirs[0]
                newloc = self.coords_in_dir(self.player.location, dir, 1)
                self.player.direction = dir
                if newloc != self.player.location:
                    if self.can_move_to(self.player, newloc):
                        self.player.location = newloc
                        self.sound.step()
                        took_turn = True
                    else:
                        self.failed_move(newloc)
                        for thing in self.level[newloc]:
                            if thing.bumped(self.player):
                                took_turn = True
                                break
                return took_turn

        if self.state == STATE_NORMAL or self.state == STATE_LOCKED:
            if filter(keys.__contains__, UNDO_KEYS):
                self.undo()
                self.sound.undo()
                self.state = STATE_NORMAL
                self.next_turn = pygame.time.get_ticks() + TURN_DELAY

        return took_turn

    def keypressed(self, e):
        took_turn = False
        if self.state == STATE_PICK:
            try:
                took_turn = self.pick_direction_done(DIR_MAP[e.key])
            except KeyError:
                self.sound.cancel()
                self.state = STATE_NORMAL
        elif self.state == STATE_NORMAL:
            if e.key in ACTION_KEYS:
                self.pick_direction(self.action)
            elif e.key in CHEAT_KEYS:
                self.cheating = not self.cheating
        elif self.state == STATE_READING:
            if e.key in ACTION_KEYS:
                self.display_message(None, None)

        if self.state != STATE_PICK:
            if e.key in UNDO_KEYS:
                pass
            elif e.key in QUIT_KEYS:
                if self.message:
                    self.display_message(None, None)
                else:
                    self.stopping = True
            elif e.key in RESTART_KEYS:
                self.restart()

        return took_turn

    def pick_direction(self, handler):
        """Enter targeting mode"""
        self.state = STATE_PICK
        self.pick_handler = handler
        self.sound.action()

    def pick_direction_done(self, direction):
        self.state = STATE_NORMAL
        return self.pick_handler(direction)

    def clicked(self, e):
        if e.button == 1:
            pass

        return False

    def block(self):
        self.state = STATE_LOCKED

    def unblock(self):
        self.state = STATE_NORMAL

    def schedule_update(self, time=UPDATE_DELAY):
        self.next_update = pygame.time.get_ticks() + time
        self.next_turn = self.next_update + TURN_DELAY

    def update(self):
        # level.objects is a set, so the order of evaluation is undefined
        #self.player_turn = True

        for obj in self.level.dynamics:
            if obj.resolve_movement():
                obj.record_state(self.turn)
                self.schedule_update()

    def restart(self):
        self.load_level(self.level_file)
        self.start()
        #self.turn = 0

        #for obj in self.level.objects:
        #    obj.restore_state(self.turn)

    def undo(self):
        if self.turn == 0:
            return False

        self.turn -= 1

        for obj in self.level.dynamics:
            obj.restore_state(self.turn)

