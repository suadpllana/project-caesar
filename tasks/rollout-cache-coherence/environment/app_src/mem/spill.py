class Spill:
    def __init__(self, cap, bs):
        self.cap = int(cap)
        self.bs = bs
        self.ent = {}
        self.ord = []
        self.n_in = 0
        self.n_out = 0

    def stash(self, key, cells):
        if self.cap <= 0 or key is None:
            return
        if key in self.ent:
            self.ord.remove(key)
            self.ord.append(key)
            return
        self.ent[key] = [tuple(c) for c in cells]
        self.ord.append(key)
        self.n_in += 1
        while len(self.ord) > self.cap:
            old = self.ord.pop(0)
            self.ent.pop(old, None)

    def fetch(self, key):
        cells = self.ent.get(key)
        if cells is None:
            return None
        self.ord.remove(key)
        self.ord.append(key)
        self.n_out += 1
        return [tuple(c) for c in cells]

    def forget(self, key):
        if key in self.ent:
            self.ent.pop(key, None)
            self.ord.remove(key)

    def keys(self):
        return list(self.ord)

    def clear(self):
        self.ent = {}
        self.ord = []
