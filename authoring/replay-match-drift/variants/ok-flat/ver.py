"""Variant B: the same shape for choices, with the default read off the boundary flag."""


class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.taken = {}

    def pick(self, key, cur, live):
        at = self.taken.get(key, 0)
        found = self.tab.choice(key, at)
        if found is None:
            if live:
                return cur
            return 0
        self.taken[key] = at + 1
        return found[1]
