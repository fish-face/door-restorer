class Animation(object):
    def __init__(self):
        """poo"""
        self.images = {}
        self.delays = {}
        self.frames = self.frame_generator()

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

    def get_frame(self):
        try:
            return self.frames.next()
        except StopIteration:
            self.frames = self.frame_generator()
            return None

    def frame_generator(self):
        for i, image in enumerate(self.images):
            for _ in range(self.delays[i]):
                yield image
