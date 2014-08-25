import pygame

sounds = {'throw': 'sounds/Throw.wav',
          'action': 'sounds/Action.wav',
          'close': 'sounds/Close.wav',
          'land': 'sounds/Land.wav',
          'cancel': 'sounds/Cancel.wav',
          'pickup': 'sounds/Pickup.wav',
          'fall': 'sounds/Fall.wav',
          'step': 'sounds/Step.wav',
          'undo': 'sounds/Undo.wav',
          'open': 'sounds/Open.wav'}

class SoundPlayer(object):
    def __init__(self):
        self.sounds = {}
        self.channels = {}

        for name, filename in sounds.items():
            self.sounds[name] = pygame.mixer.Sound(filename)
            self.channels[name] = None

    def play(self, name):
        snd = self.sounds[name]
        if not self.channels[name] or self.channels[name].get_sound() != snd:
            channel = snd.play()
            for n in self.channels:
                if self.channels[n] == channel:
                    self.channels[n] = None
            self.channels[name] = channel

    def __getattr__(self, name):
        if name in self.sounds:
            return lambda: self.play(name)
        else:
            raise AttributeError
