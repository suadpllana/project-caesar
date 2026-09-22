from bisect import bisect_left, bisect_right, insort


class Turn:
    def __init__(self, k):
        self.last = k - 1
        self.ready = []

    def add(self, j):
        insort(self.ready, j)

    def drop(self, j):
        del self.ready[bisect_left(self.ready, j)]

    def pick(self):
        r = self.ready
        if not r:
            return None
        i = bisect_right(r, self.last)
        self.last = r[i] if i < len(r) else r[0]
        return self.last

    def skip(self, d):
        r = self.ready
        if r:
            self.last = r[(bisect_right(r, self.last) + d - 1) % len(r)]
