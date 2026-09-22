"""Variant B: claims held as a list of (branch, value) pairs."""


class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.taken = {}
        self.held = []

    def mark(self, bid, due):
        what, load = due
        if what == "ok":
            return load.pos
        at = self.taken.get(load, 0)
        found = self.tab.signal(load, at)
        if found is None:
            return None
        self.taken[load] = at + 1
        self.held.append((bid, found[1]))
        return found[0]

    def take(self, bid, tag, pair):
        for at in range(len(self.held)):
            if self.held[at][0] == bid:
                return self.held.pop(at)[1]
        seen = self.taken.get(tag, 0)
        found = self.tab.signal(tag, seen)
        if found is None:
            return pair.spare()
        self.taken[tag] = seen + 1
        return found[1]
