from model.arch import D, L, M

ZERO = tuple([0] * D)
JUNK = tuple([(M - 7)] * D)


def blank(bs):
    return [tuple([(ZERO, ZERO)] * L) for _ in range(bs)]


def junk(bs):
    return [tuple([(JUNK, JUNK)] * L) for _ in range(bs)]


class Pool:
    def __init__(self, npages, bs):
        self.bs = bs
        self.pg = {}
        self.free = []
        for i in range(npages):
            self.pg[i] = blank(bs)
            self.free.append(i)
        self.lvl = 0
        self.off = {}

    def take(self):
        if not self.free:
            return None
        return self.free.pop(0)

    def give(self, pid):
        self.pg[pid] = blank(self.bs)
        if pid not in self.free:
            self.free.append(pid)

    def write(self, pid, slot, kv):
        self.pg[pid][slot] = tuple(kv)

    def read(self, pid, slot):
        return self.pg[pid][slot]

    def usable(self, pid):
        return pid in self.pg

    def sleep(self, lvl):
        self.lvl = lvl
        if lvl == 1:
            self.off = {p: self.pg[p] for p in self.pg}
        self.pg = {p: None for p in self.pg}

    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
        self.lvl = 0
