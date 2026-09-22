"""Variant A: matched positions counted in a dict rather than a set."""


class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.seen = {}
        self.open = False
        self.marks = {}

    def slot(self, kind):
        at = self.seen.get(kind, 0)
        self.seen[kind] = at + 1
        if self.open:
            return at, None
        return at, self.tab.slot(kind, at)

    def cross(self):
        self.open = True

    def live(self):
        return self.open

    def used(self, pos):
        self.marks[pos] = True

    def leftover(self):
        for pos, kind, at in self.tab.issued():
            if pos not in self.marks:
                return kind, at
        return None
