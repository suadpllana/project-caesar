from sim.line import Lines


class Mem:
    def __init__(self, init, sms, cap):
        self.words = dict(init)
        self.caches = [Lines(cap) for _ in range(sms)]

    def get(self, a):
        return self.words.get(a, 0)

    def load(self, sm, a, cached, touch=True):
        """(value, cache changed?) - with touch False nothing is modified."""
        ln, w = divmod(a, 4)
        c = self.caches[sm]
        row = c.words(ln)
        if cached:
            if row is not None:
                return row[w], False
            fresh = [self.get(ln * 4 + i) for i in range(4)]
            if touch:
                c.fill(ln, fresh)
            return fresh[w], True
        if row is not None:
            if touch:
                c.remove(ln)
            return self.get(a), True
        return self.get(a), False

    def store(self, sm, a, v):
        self.words[a] = v
        row = self.caches[sm].words(a // 4)
        if row is not None:
            row[a % 4] = v

    def atomic(self, a, v):
        old = self.get(a)
        self.words[a] = old + v
        return old

    def fence(self, sm):
        self.caches[sm].clear()

    def state(self):
        return tuple(c.state() for c in self.caches)
