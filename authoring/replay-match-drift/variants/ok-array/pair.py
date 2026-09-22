"""Variant B: one dict of counters keyed by a joined string."""


class Rec(object):
    __slots__ = ("kind", "idx", "value", "pos")

    def __init__(self, kind, idx, value, pos):
        self.kind, self.idx, self.value, self.pos = kind, idx, value, pos


class Pair(object):
    def __init__(self, tab, feed):
        self.tab = tab
        self.feed = feed
        self.next = 0
        self.seen = {}

    def bind(self, kind, name, idx, replayed):
        if not replayed:
            return Rec(kind, idx, None, None)
        tag = "%s/%s" % (kind, name)
        at = self.seen.get(tag, 0)
        self.seen[tag] = at + 1
        found = self.tab.answer(kind, name, at)
        if found is None:
            return Rec(kind, idx, None, None)
        return Rec(kind, idx, found[1], found[0])

    def settle(self, rec):
        return self.spare() if rec.value is None else rec.value

    def spare(self):
        value = self.feed[self.next] if self.next < len(self.feed) else 0
        self.next += 1
        return value
