PLAIN = "plain"
FIRM = "firm"


class Cell:
    __slots__ = ("out", "act", "ran")

    def __init__(self):
        self.out = []
        self.act = None
        self.ran = False


class Wt:
    __slots__ = ("nm", "kd", "tgt", "off")

    def __init__(self, nm, kd, tgt):
        self.nm = nm
        self.kd = kd
        self.tgt = tgt
        self.off = False


class Store:
    def __init__(self, sink):
        self.cl = {}
        self.rt = {}
        self.pr = []
        self.bo = []
        self.wt = {}
        self.sink = sink
        self.pn = 0

    def mk(self, i):
        if i in self.cl:
            return
        self.cl[i] = Cell()

    def order(self):
        return list(self.cl)

    def has(self, i):
        return i in self.cl

    def outs(self, i):
        c = self.cl.get(i)
        return list(c.out) if c is not None else []

    def held(self):
        return [i for i in self.rt.values() if i in self.cl]

    def pend(self, i):
        c = self.cl.get(i)
        return c is not None and c.act is not None and not c.ran

    def prs(self):
        return list(self.pr)

    def bos(self):
        return list(self.bo)

    def bind(self, nm, i):
        if i not in self.cl:
            return
        self.rt[nm] = i

    def unbind(self, nm):
        self.rt.pop(nm, None)

    def edge(self, a, b):
        if a not in self.cl or b not in self.cl:
            return
        c = self.cl[a]
        if b not in c.out:
            c.out.append(b)

    def cut(self, a, b):
        if a not in self.cl:
            return
        c = self.cl[a]
        if b in c.out:
            c.out.remove(b)

    def pair(self, k, v):
        if k not in self.cl or v not in self.cl:
            return
        if (k, v) not in self.pr:
            self.pr.append((k, v))

    def both(self, a, b, v):
        if a not in self.cl or b not in self.cl or v not in self.cl:
            return
        if (a, b, v) not in self.bo:
            self.bo.append((a, b, v))

    def see(self, nm, kd, i):
        if nm in self.wt or i not in self.cl:
            return
        self.wt[nm] = Wt(nm, kd, i)

    def arm(self, i, act):
        c = self.cl.get(i)
        if c is None or c.act is not None:
            return
        c.act = act

    def watches(self, i):
        return [w for w in self.wt.values() if w.tgt == i and not w.off]

    def fire(self, i):
        c = self.cl.get(i)
        if c is None or c.act is None or c.ran:
            return
        c.ran = True
        self.sink(self.pn, "cn", str(i))
        a = c.act
        if a[0] == "bind":
            self.bind(a[1], int(a[2]))
        elif a[0] == "unbind":
            self.unbind(a[1])
        elif a[0] == "edge":
            self.edge(int(a[1]), int(a[2]))
        elif a[0] == "cut":
            self.cut(int(a[1]), int(a[2]))
        elif a[0] == "pair":
            self.pair(int(a[1]), int(a[2]))
        elif a[0] == "both":
            self.both(int(a[1]), int(a[2]), int(a[3]))
        elif a[0] == "look":
            self.look(a[1])

    def wipe(self, w):
        if w.off:
            return
        w.off = True
        self.sink(self.pn, "em", w.nm)

    def letgo(self, i):
        c = self.cl.get(i)
        if c is None:
            return
        for k, v in list(self.pr):
            if k == i or v == i:
                self.pr.remove((k, v))
                self.sink(self.pn, "dp", "%d %d" % (k, v))
        for a, b, v in list(self.bo):
            if i in (a, b, v):
                self.bo.remove((a, b, v))
                self.sink(self.pn, "db", "%d %d %d" % (a, b, v))
        del self.cl[i]
        for d in self.cl.values():
            if i in d.out:
                d.out.remove(i)
        self.sink(self.pn, "rl", str(i))

    def look(self, nm):
        w = self.wt.get(nm)
        if w is None:
            self.sink(self.pn, "sh", "%s ?" % nm)
        elif w.off:
            self.sink(self.pn, "sh", "%s -" % nm)
        else:
            self.sink(self.pn, "sh", "%s %d" % (nm, w.tgt))
