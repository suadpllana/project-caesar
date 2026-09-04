class Store(object):
    def __init__(self):
        self.revs = []

    def land(self, lines):
        self.revs.append(list(lines))
        return len(self.revs) - 1

    def at(self, index):
        return list(self.revs[index])

    def head(self):
        return len(self.revs) - 1

    def count(self):
        return len(self.revs)
