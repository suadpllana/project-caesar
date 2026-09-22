from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv", "cont")

    def __init__(self, tid, seq, m, conv, cont):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv
        self.cont = cont


class Ent:
    __slots__ = ("res", "held", "cq", "nq", "old")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.cq = []
        self.nq = []
        self.old = None

    def hits_but(self, tid, m):
        bad = mode.BAD[m]
        for k, v in self.held.items():
            if k != tid and v in bad:
                return True
        return False

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.cq) or bool(self.nq)

    def head(self):
        return self.cq[0] if self.cq else self.nq[0]

    def queued(self):
        return self.cq + self.nq

    def push(self, it):
        (self.cq if it.conv else self.nq).append(it)
        if self.old is None or it.seq < self.old:
            self.old = it.seq

    def pop_head(self):
        q = self.cq if self.cq else self.nq
        it = q.pop(0)
        if self.old == it.seq:
            self.recount()
        return it

    def drop_wait(self, tid):
        for q in (self.cq, self.nq):
            for i, it in enumerate(q):
                if it.tid == tid:
                    del q[i]
                    if self.old == it.seq:
                        self.recount()
                    return it
        return None

    def recount(self):
        best = None
        for q in (self.cq, self.nq):
            for it in q:
                if best is None or it.seq < best:
                    best = it.seq
        self.old = best
