class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def pick(self, key, cur, live):
        j = self.n.get(key, 0)
        self.n[key] = j + 1
        found = self.tab.choice(key, j)
        if found is not None:
            return found[1]
        return cur
