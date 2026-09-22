def ready(b, t):
    return b is not None and b.end is None and b.until <= t


class Turn:
    def __init__(self, k):
        self.k = k
        self.prev = k - 1

    def order(self):
        return [(self.prev + 1 + i) % self.k for i in range(self.k)]

    def pick(self, row, t):
        for j in self.order():
            if ready(row[j], t):
                self.prev = j
                return row[j]
        return None

    def advance(self, row, t, n):
        seq = [j for j in self.order() if ready(row[j], t)]
        if seq:
            self.prev = seq[(n - 1) % len(seq)]
