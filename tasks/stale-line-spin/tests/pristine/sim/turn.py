class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    def ok(self, b, t):
        return b is not None and b.end is None and b.busy <= t and b.wait is None

    def pick(self, row, t):
        for i in range(1, self.k + 1):
            j = (self.last + i) % self.k
            if self.ok(row[j], t):
                self.last = j
                return row[j]
        return None
