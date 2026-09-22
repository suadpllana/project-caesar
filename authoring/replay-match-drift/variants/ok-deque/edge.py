"""Variant A: the boundary as a single flag, leftovers as a count per kind."""


class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.seen = {}
        self.open = False
        self.matched = {}

    def slot(self, kind):
        at = self.seen.get(kind, 0)
        self.seen[kind] = at + 1
        if self.open:
            return at, None, False
        found = self.tab.slot(kind, at)
        if found is None:
            self.open = True
            return at, None, True
        return at, found, False

    def live(self):
        return self.open

    def used(self, pos):
        self.matched[pos] = True

    def leftover(self):
        for pos, kind, at in self.tab.issued():
            if pos not in self.matched:
                return kind, at
        return None
