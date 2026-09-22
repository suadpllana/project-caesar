class Store:
    __slots__ = ("val", "log", "dirty")

    def __init__(self):
        self.val = {}
        self.log = []
        self.dirty = set()

    def seed(self, key, value):
        self.val[key] = value

    def mark(self):
        return len(self.log)

    def put(self, key, value):
        self.log.append((key, self.val.get(key), key in self.val))
        self.val[key] = value
        self.dirty.add(key)

    def cut(self, key):
        self.log.append((key, self.val.get(key), key in self.val))
        if key in self.val:
            del self.val[key]
        self.dirty.add(key)

    def undo(self, mark):
        log = self.log
        val = self.val
        dirty = self.dirty
        while len(log) > mark:
            key, old, had = log.pop()
            if had:
                val[key] = old
            elif key in val:
                del val[key]
            dirty.add(key)

    def seal(self, mark):
        del self.log[mark:]

    def take(self):
        moved = self.dirty
        self.dirty = set()
        return moved
