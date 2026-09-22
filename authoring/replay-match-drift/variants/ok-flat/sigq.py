"""Variant B: a plain counter per tag, held here rather than in the table."""


class Sigq(object):
    def __init__(self, tab):
        self.tab = tab
        self.taken = {}

    def take(self, tag):
        at = self.taken.get(tag, 0)
        found = self.tab.signal(tag, at)
        if found is None:
            return None
        self.taken[tag] = at + 1
        return found[1]
