"""The dispatcher.

At the start of every cycle, while a slot is free and blocks remain, the lowest-numbered
block not yet placed goes to the multiprocessor with the most free slots, ties to the lower
number, into that multiprocessor's lowest free slot. A block that exits at cycle u gives its
slot back from cycle u+1, so its successor is placed at u+1 at the earliest.
"""


class Place:
    def __init__(self, launch):
        self.n = launch.sms
        self.k = launch.slots
        self.grid = launch.grid
        self.rows = [[None] * self.k for _ in range(self.n)]
        self.free = [self.k] * self.n
        self.nfree = self.n * self.k
        self.next = 0
        self.gone = []

    def release(self, b):
        self.gone.append(b)

    def fill(self, blocks, t):
        for b in self.gone:
            self.rows[b.sm][b.slot] = None
            self.free[b.sm] += 1
            self.nfree += 1
        self.gone = []
        placed = []
        while self.next < self.grid and self.nfree:
            s = 0
            for i in range(1, self.n):
                if self.free[i] > self.free[s]:
                    s = i
            row = self.rows[s]
            k = row.index(None)
            b = blocks[self.next]
            row[k] = b
            b.sm, b.slot, b.at = s, k, t
            self.free[s] -= 1
            self.nfree -= 1
            self.next += 1
            placed.append(b)
        return placed
