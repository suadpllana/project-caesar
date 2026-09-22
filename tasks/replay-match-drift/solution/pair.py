"""Binding a command to its recorded answer, and taking a result that was never recorded.

The counter is on kind and name together, which is a different axis from the one that
matched the command, so two commands of one kind whose work finished in the other order
still take their own values.

A result the history does not carry - because the command was issued after the live side
opened, or because the run it was recorded from never got an answer - comes off the run
file's own list, and it comes off at the moment a branch takes it rather than when the
command was issued. Under a schedule the two orders are not the same.
"""


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
        self.at = 0
        self.n = {}

    def bind(self, kind, name, idx, replayed):
        if not replayed:
            return Rec(kind, idx, None, None)
        key = (kind, name)
        j = self.n.get(key, 0)
        self.n[key] = j + 1
        found = self.tab.answer(kind, name, j)
        if found is None:
            return Rec(kind, idx, None, None)
        return Rec(kind, idx, found[1], found[0])

    def settle(self, rec):
        if rec.value is not None:
            return rec.value
        return self.spare()

    def spare(self):
        value = self.feed[self.at] if self.at < len(self.feed) else 0
        self.at += 1
        return value
