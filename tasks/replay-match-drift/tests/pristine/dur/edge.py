class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.on = {}
        self.hit = set()

    def slot(self, kind):
        i = self.n.get(kind, 0)
        self.n[kind] = i + 1
        if self.on.get(kind):
            return i, None, False
        found = self.tab.slot(kind, i)
        if found is None:
            self.on[kind] = True
            return i, None, True
        return i, found, False

    def live(self):
        return bool(self.on)

    def used(self, pos):
        self.hit.add(pos)

    def leftover(self):
        return None
