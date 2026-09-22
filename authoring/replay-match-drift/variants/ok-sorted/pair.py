"""Variant A: answers popped rather than indexed, so no counter is kept here at all."""


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
        if not replayed:
            return Rec(kind, idx, None, None)
        found = self.tab.answer(kind, name, 0)
        if found is None:
            return Rec(kind, idx, None, None)
        return Rec(kind, idx, found[1], found[0])

    def settle(self, rec):
        if rec.value is None:
            return self.spare()
        return rec.value

    def spare(self):
        if self.given < len(self.feed):
            value = self.feed[self.given]
        else:
            value = 0
        self.given += 1
        return value
