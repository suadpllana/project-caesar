import bisect


class Wait:
    def __init__(self):
        self.line = {}
        self.n = 0

    def add(self, key, k):
        row = self.line.get(key)
        if row is None:
            row = self.line[key] = []
        bisect.insort(row, k)
        self.n += 1

    def drop(self, key, k):
        row = self.line.get(key)
        if row is None:
            return
        i = bisect.bisect_left(row, k)
        if i < len(row) and row[i] == k:
            del row[i]
            self.n -= 1
        if not row:
            del self.line[key]

    def take(self, key):
        row = self.line.get(key)
        if not row:
            return None
        k = row.pop(0)
        if not row:
            del self.line[key]
        self.n -= 1
        return k

    def count(self):
        return self.n
