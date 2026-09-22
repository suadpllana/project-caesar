"""Variant A: answers popped rather than indexed, so no counter is kept here at all."""

LATE_BASE = 10 ** 9


class Rec(object):
    def __init__(self, kind, idx, value, pos):
        self.kind = kind
        self.idx = idx
        self.value = value
        self.pos = pos


class Pair(object):
    def __init__(self, tab, feed):
        self.tab = tab
        self.feed = list(feed)
        self.given = 0

    def bind(self, kind, name, idx, replayed):
        if replayed:
            found = self.tab.answer(kind, name, 0)
            if found is None:
                return Rec(kind, idx, None, None)
            return Rec(kind, idx, found[1], found[0])
        self.given += 1
        value = self.feed.pop(0) if self.feed else 0
        return Rec(kind, idx, value, LATE_BASE + self.given)
