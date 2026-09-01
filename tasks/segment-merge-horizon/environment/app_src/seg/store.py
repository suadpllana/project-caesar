from seg import read, rec, table


class Store:
    def __init__(self):
        self.segs = []
        self.mem = []
        self.pins = []
        self.seq = 0
        self.nid = 0
        self.ks = set()

    def bump(self):
        self.seq += 1
        return self.seq

    def write(self, k, t, v):
        r = rec.Rec(k, self.bump(), t, v)
        self.mem.append(r)
        self.ks.add(k)
        return r

    def flush(self):
        if not self.mem:
            return None
        self.nid += 1
        s = table.Seg(self.nid, self.mem)
        self.mem = []
        self.segs.insert(0, s)
        return s

    def pin(self):
        self.pins.append(self.seq)
        return self.seq

    def unpin(self, i):
        if 0 <= i < len(self.pins):
            return self.pins.pop(i)
        return None

    def pts(self):
        return sorted(set(list(self.pins) + [self.seq]))

    def keys(self):
        return sorted(self.ks)

    def chain(self, k, at):
        out = []
        for r in self.mem:
            if r.k == k and r.s <= at:
                out.append(r)
        for s in self.segs:
            i = s.lo(k)
            e = s.hi(k)
            while i < e:
                r = s.raw(i)
                if r.s <= at:
                    out.append(r)
                i += 1
        out.sort(key=lambda r: -r.s)
        return out

    def read(self, k, at):
        return read.resolve(self.chain(k, at))

    def map(self):
        pts = self.pts()
        out = []
        for k in self.keys():
            for a in pts:
                out.append([k, a, self.read(k, a)])
        return out

    def swap(self, idx, rs):
        self.nid += 1
        s = table.Seg(self.nid, rs)
        keep = [g for i, g in enumerate(self.segs) if i not in idx]
        at = min(idx) if idx else 0
        keep.insert(at, s)
        self.segs = keep
        return s

    def shape(self):
        return [[s.sid, s.n()] for s in self.segs]
