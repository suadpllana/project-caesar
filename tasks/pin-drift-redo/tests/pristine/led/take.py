class Taken:
    def __init__(self):
        self.num = {}
        self.read = set()

    def open(self, store):
        self.num = store.snap()

    def stale(self, store):
        for k in self.read:
            if self.num[k] != store.at(k):
                return True
        return False

    def at(self, k):
        return self.num[k]

    def seen(self, k):
        self.read.add(k)

    def moved(self, store, keys):
        out = []
        for k in keys:
            if self.num[k] != store.at(k):
                out.append(k)
        return out
