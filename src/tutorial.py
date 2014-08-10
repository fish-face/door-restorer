from game import Game, RIGHT

class TutorialOne(Game):
    def __init__(self, *args, **kwargs):
        Game.__init__(self, *args, **kwargs)
        self.gone_to_door = False
        self.pressed_action = False
        self.picked_up_door = False
        self.correctly_thrown_door = False
        self.deactivate_if = {
            'Hint Movement': ('picked_up_door',),
            'Go to Door': ('picked_up_door',),
            'Lift Door': ('picked_up_door',)
        }

    def display_message(self, key, message):
        if key in self.deactivate_if:
            for flag in self.deactivate_if[key]:
                if getattr(self, flag, False): return False

        Game.display_message(self, key, message)

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
                self.display_message('Thrown Wrong', 'Can\'t tell your left from your right, eh? Well it seems you have the brawn but not the brains.\n\nGo over to where you throw it and pick it up again. Then throw it at the wall to your RIGHT.')
                self.picked_up_door = False
        return True
