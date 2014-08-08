import os
import sys
import json

class SaveGame(object):
    def __init__(self, data=None):
        if data is not None:
            self.from_data(data)
        else:
            self.load()

    def set_current(self, world, id):
        self.load()
        self.update({'current' : {'world' : world, 'level' : id}})
        self.save()

    def current(self):
        if 'current' in self.data:
            return self.data['current']['world'], self.data['current']['level']
        else:
            return ('Tutorials', 1)

    def set_completed(self, world, id):
        self.load()
        self.update({'completed': {world: [id]}})
        self.save()

    def completed(self, levelset, id):
        return levelset in self.data['completed'] and id in self.data['completed'][levelset]

    def available(self, levelset, id):
        return self.completed(levelset, id) or id == 1 or self.completed(levelset, id - 1)

    def from_data(self, data={}):
        self.load()
        self.update(data)

    def update(self, b, a=None):
        if a is None:
            a = self.data

        for key, value in b.items():
            if isinstance(value, dict):
                r = self.update(value, a.get(key, {}))
                a[key] = r
            elif isinstance(value, list):
                a[key] = list(set(a.get(key, [])) | set(value))
            else:
                a[key] = b[key]

        return a

    def load(self):
        filename = self.save_location()
        try:
            fd = open(filename, 'r')
        except IOError:
            self.data = {}
            return False

        with fd:
            self.data = json.load(fd)

        return True

    def save(self):
        filename = self.save_location()
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError:
            pass

        with open(filename, 'w') as fd:
            json.dump(self.data, fd)

    @staticmethod
    def save_location():
        if sys.platform.startswith('linux'):
            return os.path.expanduser('~/.local/share/Dora/save.txt')
        if sys.platform == 'win32':
            return os.path.expandvars('%APPDATA%/Dora/save.txt')
        if sys.platform == 'darwin':
            return os.path.expanduser('~/Libraries/Application Support/Dora/save.txt')

        NotImplemented('Unfortunately, your operating system is not supported.')
