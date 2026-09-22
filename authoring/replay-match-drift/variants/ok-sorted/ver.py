"""Variant A: the choice queue lives in the table too."""


class Ver(object):
    def __init__(self, tab):
        self.tab = tab

    def pick(self, key, cur, live):
        found = self.tab.choice(key, 0)
        if found is not None:
            self.tab.drop_choice(key)
            return found[1]
        return cur if live else 0
