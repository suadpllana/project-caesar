class Sift:
    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1
        self.again = []

    def take(self, n):
        pool = []
        while self.again and len(pool) < n:
            pool.append(self.again.pop(0))
        while len(pool) < n and self.next <= self.store.depth():
            pool.append(self.next)
            self.next += 1
        out = []
        for pos in pool:
            kind, k, a, b, c = self.store.entry(pos)
            if k > self.walk.cur:
                self.again.append(pos)
                out.append((pos, kind, k, a, b, c, "ahead"))
            elif pos < self.marks.at(k):
                out.append((pos, kind, k, a, b, c, "seen"))
            else:
                out.append((pos, kind, k, a, b, c, "done"))
        return out
