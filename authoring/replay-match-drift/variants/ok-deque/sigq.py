"""Variant A: the queue lives in the table, so nothing is counted here."""


class Sigq(object):
    def __init__(self, tab):
        self.tab = tab

    def take(self, tag):
        found = self.tab.signal(tag, 0)
        if found is None:
            return None
        self.tab.drop_signal(tag)
        return found[1]
