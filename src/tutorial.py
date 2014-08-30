from game import Game, RIGHT

class Tutorial(Game):
    pass


class TutorialOne(Tutorial):
    def pickup(self, direction):
        success = Game.pickup(self, direction)
        if not success:
            return False

        if not self.picked_up_door:
            self.display_message('Picked up', 'OK, now THROW the door at the wall to your right!\n\nPress Space, Enter, E or X, and then right.')
            self.picked_up_door = True
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
                self.display_message('Thrown Wrong', 'Can\'t tell your left from your right, eh? Well it seems you have the brawn but not the brains.\n\nGo over to where you threw it and pick it up again. Then throw it at the wall to your RIGHT.')
        self.level.get_region('Lift Door').enabled = False
        self.level.get_region('Lift Door').check_active()
        return True

    def in_wall(self, region, obj):
        if obj.flag('player'):
            self.level.get_region('Nearly There').location = self.coords_in_dir(obj._location, RIGHT, 1)

    def start(self):
        Tutorial.start(self)
        self.picked_up_door = False
        self.correctly_thrown_door = False
        self.level.get_region('Lift Door').add_dependency(self.level.get_region('Go to Door'))
        self.level.get_region('Nearly There').add_dependency(self.level.get_region('In Wall'))
        self.level.get_region('In Wall').add_anti_dependency(self.level.get_region('Nearly There'))
        self.level.check_active_regions()
        self.level.get_region('In Wall').arrived_cbs.append(self.in_wall)


class TutorialTwo(Tutorial):
    def fell_in_pit_cb(self, region, obj):
        if obj.flag('player'):
            self.fell_in_pit = True
        if obj.flag('door') and not self.player.destroyed and obj.move_turns == 0 and not self.door_fallen:
            self.door_fallen = True
            self.display_message(None, 'Hmm. I think you needed that.\n\nYou\'d better press U to undo and get it back again.')

    def left_pit_cb(self, region, obj):
        if obj.flag('player') and self.fell_in_pit and not self.left_pit:
            self.left_pit = True
            self.display_message(None, 'Right, that\'s quite enough of that. Never mind the pits then, I think the key here is circumventing them using those doors.\n\nExperiment a bit and see what you can do.')

    def landed_cb(self, region, obj):
        if obj.flag('door') and not self.door_landed:
            self.door_landed = True
            self.display_message(None, 'Ah, hmm! If you use the other doors in the same way, you should be able to forge yourself a path past those pesky pits!')

    def failed_move(self, newloc):
        if (self.player.contained and
            self.get_objects_at(newloc, lambda x: x.flag('door') and x.state == 'open') and
            not self.tried_through_door):
            self.level.get_region('Tried Through Door').location = self.player.location
            self.level.get_region('Tried Through Door').enabled = True
            self.level.get_region('Tried Through Door').check_active()
            self.level.get_region('Tried Through Door').arrived(self.player)
            self.tried_through_door = True

    def start(self):
        Tutorial.start(self)
        self.fell_in_pit = False
        self.left_pit = False
        self.door_landed = False
        self.door_fallen = False
        self.tried_through_door = False
        self.level.get_region('Pit region').add_anti_dependency(self.level.get_region('Pit region'))
        self.level.get_region('Pit region').arrived_cbs.append(self.fell_in_pit_cb)
        self.level.get_region('Left Pit').arrived_cbs.append(self.left_pit_cb)
        self.level.get_region('Door landing').arrived_cbs.append(self.landed_cb)
        self.level.get_region('Tried Through Door').enabled = False
        self.level.check_active_regions()

