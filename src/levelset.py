import csv

class LevelSet(object):
    def __init__(self, filename):
        with open(filename) as fd:
            self.name = fd.readline().strip()
            self.next = fd.readline().strip()
            self.levels = [LevelDescription(*row) for row in csv.reader(fd, delimiter='\t')]

        self.value = filename
        self.filename = filename

    def __cmp__(self, other):
        return cmp(self.filename, other.filename)


class LevelDescription(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
