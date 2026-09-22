from sim.line import Lines


class Place:
    def __init__(self, launch, mem):
        self.n = launch.sms
        self.k = launch.slots
        self.cap = launch.lines
        self.grid = launch.grid
        self.mem = mem
        self.rows = [[None] * self.k for _ in range(self.n)]
        self.next = 0

    def fill(self, blocks, t):
        while self.next < self.grid:
            s = self.next % self.n
            row = self.rows[s]
            if None not in row:
                return
            k = row.index(None)
            b = blocks[self.next]
            row[k] = b
            b.sm, b.slot, b.at = s, k, t
            b.l1 = Lines(self.cap)
            self.mem.held.append(b.l1)
            self.next += 1

    def free(self, b):
        self.rows[b.sm][b.slot] = None
        self.mem.held.remove(b.l1)

    def live(self):
        return [b for row in self.rows for b in row if b is not None and b.end is None]
