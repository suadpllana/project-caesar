"""Variant B: a counter per key, with the default read off the boundary flag."""


class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.seen = {}

    def pick(self, key, cur, live):
        at = self.seen.get(key, 0)
        found = self.tab.choice(key, at)
        if found is None:
            return cur if live else 0
        self.seen[key] = at + 1
        return found[1]
