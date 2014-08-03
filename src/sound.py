import pygame

sounds = {'throw': 'sounds/Throw.wav',
          'action': 'sounds/Action.wav',
          'close': 'sounds/Close.wav',
          'land': 'sounds/Land.wav',
          'cancel': 'sounds/Cancel.wav',
          'pickup': 'sounds/Pickup.wav',
          'fall': 'sounds/Fall.wav',
          'step': 'sounds/Step.wav',
          'open': 'sounds/Open.wav'}

class SoundPlayer(object):
    def __init__(self):
        self.sounds = {}

        for name, filename in sounds.items():
            self.sounds[name] = pygame.mixer.Sound(filename)

    def play(self, name):
        self.sounds[name].play()

    def __getattr__(self, name):
        if name in self.sounds:
            return lambda: self.play(name)
        else:
            raise AttributeError
