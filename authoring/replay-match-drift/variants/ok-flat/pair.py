"""Variant B: one dict of counters, and live answers numbered from a high base."""

HIGH = 2 ** 40


class Rec(object):
    __slots__ = ("kind", "idx", "value", "pos")

    def __init__(self, kind, idx, value, pos):
        self.kind = kind
        self.idx = idx
        self.value = value
        self.pos = pos


class Pair(object):
    def __init__(self, tab, feed):
        self.tab = tab
        self.feed = feed
        self.next_feed = 0
        self.counts = {}
        self.live_seen = 0

    def bind(self, kind, name, idx, replayed):
        if not replayed:
            if self.next_feed < len(self.feed):
                value = self.feed[self.next_feed]
            else:
                value = 0
            self.next_feed += 1
            self.live_seen += 1
            return Rec(kind, idx, value, HIGH + self.live_seen)
        tag = "%s/%s" % (kind, name)
        seen = self.counts.get(tag, 0)
        self.counts[tag] = seen + 1
        found = self.tab.answer(kind, name, seen)
        if found is None:
            return Rec(kind, idx, None, None)
        return Rec(kind, idx, found[1], found[0])
