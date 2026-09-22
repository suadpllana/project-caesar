class Store:
    __slots__ = ("val", "dirty")

    def __init__(self):
        self.val = {}
        self.dirty = set()

    def seed(self, key, value):
        self.val[key] = value

    def mark(self):
        return dict(self.val)

    def put(self, key, value):
        self.val[key] = value
        self.dirty.add(key)

    def cut(self, key):
        if key in self.val:
            del self.val[key]
        self.dirty.add(key)

    def undo(self, mark):
        self.val = dict(mark)

    def seal(self, mark):
        return None

    def take(self):
        moved = self.dirty
        self.dirty = set()
        return moved
