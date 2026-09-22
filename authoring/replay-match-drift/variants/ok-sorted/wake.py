"""Variant A: the signal queue lives in the table, so nothing is counted here."""


class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.claim = {}

    def mark(self, bid, due):
        what, load = due
        if what == "ok":
            return load.pos
        found = self.tab.signal(load, 0)
        if found is None:
            return None
        self.tab.drop_signal(load)
        self.claim[bid] = found[1]
        return found[0]

    def take(self, bid, tag, pair):
        if bid in self.claim:
            return self.claim.pop(bid)
        found = self.tab.signal(tag, 0)
        if found is None:
            return pair.spare()
        self.tab.drop_signal(tag)
        return found[1]
