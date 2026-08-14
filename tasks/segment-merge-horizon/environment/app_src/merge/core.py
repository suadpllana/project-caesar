from seg import read, rec


class Cur:
    __slots__ = ("core", "k", "src")

    def __init__(self, core, k, src):
        self.core = core
        self.k = k
        self.src = src

    def pick(self):
        best = -1
        bi = -1
        for j in range(len(self.src)):
            e = self.src[j]
            if e[1] >= e[2]:
                continue
            s = e[0].buf[e[1] * 4 + 1]
            if s > best:
                best = s
                bi = j
        return bi

    def next(self):
        bi = self.pick()
        if bi < 0:
            return None
        return self.core.take(self, bi)


class Core:
    def __init__(self):
        self.reads = 0
        self.writes = 0
        self.probes = 0
        self.job = 0
        self.rest = []
        self.buf = []
        self.jrn = []

    def begin(self, job, rest):
        self.job = job
        self.rest = rest
        self.buf = []

    def cursor(self, k, segs):
        src = []
        for g in segs:
            i = g.lo(k)
            e = g.hi(k)
            if i < e:
                src.append([g, i, e])
        return Cur(self, k, src)

    def take(self, cur, bi):
        e = cur.src[bi]
        r = e[0].get(e[1])
        e[1] += 1
        self.reads += 1
        self.jrn.append(("r", self.job, r.k, r.s, r.t, r.v))
        return r

    def emit(self, k, s, t, v):
        self.writes += 1
        self.buf.append(rec.Rec(k, s, t, v))
        self.jrn.append(("w", self.job, k, s, t, v))

    def probe(self, k):
        self.probes += 1
        rs = []
        for g in self.rest:
            i = g.lo(k)
            e = g.hi(k)
            while i < e:
                rs.append(g.get(i))
                i += 1
        rs.sort(key=lambda r: -r.s)
        val = read.resolve(rs)
        self.jrn.append(("p", self.job, k, 0 if val is None else 1,
                         0 if val is None else val, 0))
        return val

    def end(self):
        out = self.buf
        self.buf = []
        return out
