from sim.line import Lines


class Mem:
    def __init__(self, init, sms, cap):
        self.cells = dict(init)
        self.l1 = [Lines(cap) for _ in range(sms)]

    def word(self, a):
        return self.cells.get(a, 0)

    def probe(self, sm, a, ca):
        v = self.l1[sm].read(a >> 2, a & 3)
        if ca:
            return (v, False) if v is not None else (self.word(a), True)
        return self.word(a), v is not None

    def load(self, sm, a, ca):
        c = self.l1[sm]
        ln = a >> 2
        v = c.read(ln, a & 3)
        if ca:
            if v is not None:
                return v, False
            c.load(ln, [self.word((ln << 2) + i) for i in range(4)])
            return self.word(a), True
        if v is not None:
            c.evict(ln)
            return self.word(a), True
        return self.word(a), False

    def store(self, sm, a, v):
        self.cells[a] = v
        self.l1[sm].patch(a >> 2, a & 3, v)

    def atomic(self, a, v):
        old = self.word(a)
        self.cells[a] = old + v
        return old

    def fence(self, sm):
        self.l1[sm].flush()
