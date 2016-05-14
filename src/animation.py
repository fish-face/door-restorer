import json
import pygame

class Animation(object):
    def __init__(self, filename=None):
        """poo"""
        self.images = {}
        self.delays = {}
        self.loop = False

        if filename is not None:
            data = json.load(open(filename, 'r'))
            self.load(data)
            self.finalise()

        self.start()

    def load(self, data):
        """Create from an animation description file"""
        image = pygame.image.load(data['filename']).convert_alpha()
        self.loop = data.get('loop', False)
        w = data['frame_width']
        h = data['frame_height']
        for i, frame_info in enumerate(data['frames']):
            x = frame_info['x']
            y = frame_info['y']
            self.images[i] = image.subsurface(x * w, y * h, w, h)
            self.delays[i] = frame_info['delay']

    def add_frame(self, index, image, delay):
        self.images[index] = image
        self.delays[index] = delay

    def finalise(self):
        image_list = []
        delays_list = []
        for i, image in sorted(self.images.items()):
            if i != len(image_list):
                raise ValueError('Missing animation frame')
            image_list.append(image)
            delays_list.append(self.delays[i])

        self.images = image_list
        self.delays = delays_list

    def start(self):
        self.frames = self.frame_generator()

    def get_frame(self):
        try:
            return self.frames.next()
        except StopIteration:
            if self.loop:
                return self.frames.next()
            else:
                return None

    def frame_generator(self):
        for i, image in enumerate(self.images):
            for _ in range(self.delays[i]):
                yield image
