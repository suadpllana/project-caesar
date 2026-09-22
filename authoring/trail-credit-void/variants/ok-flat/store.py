GONE = object()


class Store:
    __slots__ = ("val", "log", "hit")

    def __init__(self):
        self.val = {}
        self.log = []
        self.hit = []

    def seed(self, key, value):
        self.val[key] = value

    def mark(self):
        return len(self.log)

    def put(self, key, value):
        self.log.append((key, self.val.get(key, GONE)))
        self.val[key] = value
        self.hit.append(key)

    def cut(self, key):
        self.log.append((key, self.val.get(key, GONE)))
        self.val.pop(key, None)
        self.hit.append(key)

    def undo(self, mark):
        log = self.log
        val = self.val
        hit = self.hit
        for spot in range(len(log) - 1, mark - 1, -1):
            key, was = log[spot]
            if was is GONE:
                val.pop(key, None)
            else:
                val[key] = was
            hit.append(key)
        del log[mark:]

    def seal(self, mark):
        del self.log[mark:]

    def take(self):
        moved = set(self.hit)
        self.hit = []
        return moved
