from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv")

    def __init__(self, tid, seq, m, conv):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv


class Ent:
    __slots__ = ("res", "held", "q")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.q = []

    def group(self):
        out = None
        for v in self.held.values():
            out = mode.cover(out, v)
        return out

    def hits_but(self, tid, m):
        g = self.group()
        return g is not None and mode.hits(g, m)

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.q)

    def head(self):
        return self.q[0]

    def queued(self):
        return list(self.q)

    def push(self, it):
        self.q.append(it)

    def pop_head(self):
        return self.q.pop(0)

    def drop_wait(self, tid):
        for i, it in enumerate(self.q):
            if it.tid == tid:
                del self.q[i]
                return it
        return None
