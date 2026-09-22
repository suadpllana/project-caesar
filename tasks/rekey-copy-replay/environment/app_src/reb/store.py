class Store:
    def __init__(self):
        self.row = {}
        self.jrn = []

    def put(self, k, a, b, c):
        self.row[k] = (a, b, c)
        self.jrn.append(("set", k, a, b, c))

    def kill(self, k):
        if k in self.row:
            del self.row[k]
        self.jrn.append(("del", k, 0, 0, 0))

    def at(self, k):
        return self.row.get(k)

    def live(self):
        return self.row.keys()

    def depth(self):
        return len(self.jrn)

    def entry(self, pos):
        return self.jrn[pos - 1]
