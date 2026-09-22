import bisect

GET, SPAN, CHG = 0, 1, 2
MISS = object()


class Claim:
    __slots__ = ("i", "kind", "key", "val", "lo", "hi", "n", "seen", "on")

    def __init__(self, i, kind):
        self.i = i
        self.kind = kind
        self.key = 0
        self.val = None
        self.lo = 0
        self.hi = 0
        self.n = 0
        self.seen = None
        self.on = True


class Txn:
    __slots__ = ("tid", "base", "claims", "seq", "ci", "cv", "ck", "marks", "dead")

    def __init__(self, tid, base):
        self.tid = tid
        self.base = base
        self.claims = []
        self.seq = []
        self.ci = {}
        self.cv = {}
        self.ck = []
        self.marks = []
        self.dead = None

    def add_get(self, key, val):
        c = Claim(len(self.claims), GET)
        c.key = key
        c.val = val
        self.claims.append(c)
        return c

    def add_span(self, lo, hi, n, got):
        c = Claim(len(self.claims), SPAN)
        c.lo = lo
        c.hi = hi
        c.n = n
        c.seen = dict(got)
        self.claims.append(c)
        return c

    def add_chg(self, key, val):
        c = Claim(len(self.claims), CHG)
        c.key = key
        c.val = val
        self.claims.append(c)
        self.seq.append(c.i)
        ix = self.ci.get(key)
        if ix is None:
            self.ci[key] = [c.i]
            self.cv[key] = [val]
            bisect.insort(self.ck, key)
        else:
            ix.append(c.i)
            self.cv[key].append(val)
        return c

    def mark(self, name):
        self.marks.append((name, len(self.claims)))

    def back(self, name):
        pos = None
        for j in range(len(self.marks) - 1, -1, -1):
            if self.marks[j][0] == name:
                pos = self.marks[j][1]
                del self.marks[j:]
                break
        if pos is None:
            return []
        hit = set()
        for i in self.seq:
            if i >= pos:
                hit.add(self.claims[i].key)
        off = []
        for key in sorted(hit):
            for i in self.ci.get(key, ()):
                self.claims[i].on = False
            self.ci.pop(key, None)
            self.cv.pop(key, None)
            j = bisect.bisect_left(self.ck, key)
            if j < len(self.ck) and self.ck[j] == key:
                del self.ck[j]
            off.append(key)
        self.seq = [i for i in self.seq if self.claims[i].on]
        return off

    def live(self):
        return {key: self.cv[key][-1] for key in self.ci}
