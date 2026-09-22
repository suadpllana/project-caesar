"""Variant B: matched commands marked in a bytearray over the recorded commands."""


class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.count = {}
        self.crossed = False
        self.marks = bytearray(tab.total_go())
        self.where = {}
        for at, (pos, _kind, _rank) in enumerate(tab.issued()):
            self.where[pos] = at

    def slot(self, kind):
        at = self.count.get(kind, 0)
        self.count[kind] = at + 1
        if self.crossed:
            return at, None, False
        found = self.tab.slot(kind, at)
        if found is None:
            self.crossed = True
            return at, None, True
        return at, found, False

    def live(self):
        return self.crossed

    def used(self, pos):
        self.marks[self.where[pos]] = 1

    def leftover(self):
        for at in range(len(self.marks)):
            if not self.marks[at]:
                return self.tab.rank_of(at)
        return None
