"""Variant B: matched commands marked in a bytearray over the recorded commands."""


class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.count = {}
        self.crossed = False
        self.flags = bytearray(tab.count())
        self.spot = {}
        for at in range(tab.count()):
            self.spot[tab.order()[at]] = at

    def slot(self, kind):
        at = self.count.get(kind, 0)
        self.count[kind] = at + 1
        if self.crossed:
            return at, None
        return at, self.tab.slot(kind, at)

    def cross(self):
        self.crossed = True

    def live(self):
        return self.crossed

    def used(self, pos):
        self.flags[self.spot[pos]] = 1

    def leftover(self):
        for at in range(len(self.flags)):
            if not self.flags[at]:
                return self.tab.where(at)
        return None
