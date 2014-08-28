from game import Game, RIGHT

class Tutorial(Game):
    def __init__(self, *args, **kwargs):
        Game.__init__(self, *args, **kwargs)
        self.deactivate_if = {}
        self.activate_if = {}

    def display_message(self, key, message):
        if key in self.deactivate_if:
            for flag in self.deactivate_if[key]:
                if getattr(self, flag, False): return False
        if key in self.activate_if:
            for flag in self.activate_if[key]:
                if not getattr(self, flag, False): return False

        Game.display_message(self, key, message)


class TutorialOne(Tutorial):
    def __init__(self, *args, **kwargs):
        Tutorial.__init__(self, *args, **kwargs)

    def load_level(self, level_file):
        Tutorial.load_level(self, level_file)

        self.picked_up_door = False
        self.correctly_thrown_door = False
        self.level.regions['Lift Door'].add_dependency(self.level.regions['Go to Door'])
        self.deactivate_if = {
            'Hint Movement': ('picked_up_door',),
            'Go to Door': ('picked_up_door',),
            'Lift Door': ('picked_up_door',),
            'In Wall': ('second_pickup',),
            'Nearly There': ('second_pickup',),
        }

        self.level.check_active_regions()

    def pickup(self, direction):
        success = Game.pickup(self, direction)
        if not success:
            return False

        if not self.picked_up_door:
            self.display_message('Picked up', 'OK, now THROW the door at the wall to your right!\n\nPress Space, Enter, E or X, and then right.')
            self.picked_up_door = True
        elif self.player.location[0] == 4:
            self.second_pickup = True
        return True

    def throw(self, direction):
        success = Game.throw(self, direction)
        if not success:
            return False

        if not self.correctly_thrown_door:
            if direction == RIGHT:
                self.display_message('Thrown', 'As you can see, a quite incredible thing has happened. Rather than making a loud BANG and falling over, the door fused into the wall. My gast is flabbered.\n\nGo ahead and WALK into the door to open it.')
                self.correctly_thrown_door = True
            else:
                self.display_message('Thrown Wrong', 'Can\'t tell your left from your right, eh? Well it seems you have the brawn but not the brains.\n\nGo over to where you throw it and pick it up again. Then throw it at the wall to your RIGHT.')
                self.picked_up_door = False
        return True


class TutorialTwo(Tutorial):
    def __init__(self, *args, **kwargs):
        Tutorial.__init__(self, *args, **kwargs)
        self.fell_in_pit = False
        self.door_landed = False
        self.door_fallen = False
        self.tried_through_door = False
        self.deactivate_if = {
            'Investigate pits': ('fell_in_pit', 'door_landed'),
            'Pit region': ('left_pit',),
            'Left Pit': ('got_door',),
        }
        self.activate_if = {
            'Left Pit': ('fell_in_pit',),
        }

    def pickup(self, direction):
        success = Tutorial.pickup(self, direction)
        if success:
            self.got_door = True

        return success

    def fell_in_pit_cb(self, region, obj):
        if obj.flag('player'):
            self.fell_in_pit = True
        if obj.flag('door') and obj.move_turns == 0 and not self.door_fallen:
            self.door_fallen = True
            self.display_message(None, 'Hmm. I think you needed that.\n\nYou\'d better press U to undo and get it back again.')

    def left_pit_cb(self, region, obj):
        if obj.flag('player') and self.fell_in_pit:
            self.left_pit = True

    def landed_cb(self, region, obj):
        if obj.flag('door') and not self.door_landed:
            self.door_landed = True
            self.display_message(None, 'Ah, hmm! If you use the other doors in the same way, you should be able to forge yourself a path past those pesky pits!')

    def failed_move(self, newloc):
        if (self.player.contained and
            self.get_objects_at(newloc, lambda x: x.flag('door') and x.state == 'open')):
            if not self.tried_through_door:
                self.tried_through_door = True
                self.display_message(None, 'Curious. It looks like you\'re unable to fit the door through the other one. It must be too big. Or magical. Either way, you\'ll need to find another way to get to the stairs!')

    def start(self):
        Tutorial.start(self)
        self.level.get_region('Pit region').arrived_cbs.append(self.fell_in_pit_cb)
        self.level.get_region('Left Pit').leaving_cbs.append(self.left_pit_cb)
        self.level.get_region('Door landing').arrived_cbs.append(self.landed_cb)

