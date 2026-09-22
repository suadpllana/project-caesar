"""What an open transaction holds while it runs.

Every read and every change is a claim and claims are numbered from 0 in op order, including
ops a rollback later takes back, so an index never shifts under a rollback.

The changes are kept twice over and both are needed. `seq` is the order they were made in,
which is what a rollback pops, and `ci`/`cv` are per key in index order, which is what answering
a read walks: the value a read was answered under is the last change to that key made before
the read, so the check has to be able to ask for the state of a key at a claim index rather
than the state of the key now. A rollback pops a suffix of `seq`, and because `seq` is in index
order that pops a suffix of each key's list too.

`pts` and `spans` are what makes the check key-driven rather than claim-driven. A claim can
only stop standing because a key inside what it covers moved, so the claims to look at after a
commit are the point reads on the keys that moved, the change claims on those keys, and the
scans whose cover holds one of them - never every claim of the transaction.
"""
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
    __slots__ = ("tid", "base", "claims", "seq", "ci", "cv", "ck", "marks", "dead", "pts",
                 "spans")

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
        self.pts = {}
        self.spans = []

    def nxt(self):
        return len(self.claims)

    def add_get(self, key, val):
        c = Claim(len(self.claims), GET)
        c.key = key
        c.val = val
        self.claims.append(c)
        self.pts.setdefault(key, []).append(c.i)
        return c

    def add_span(self, lo, hi, n, got):
        c = Claim(len(self.claims), SPAN)
        c.lo = lo
        c.hi = hi
        c.n = n
        c.seen = dict(got)
        self.claims.append(c)
        self.spans.append(c.i)
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
        """Take back the changes made after the last mark of that name; the mark stays."""
        pos = None
        for j in range(len(self.marks) - 1, -1, -1):
            if self.marks[j][0] == name:
                pos = self.marks[j][1]
                del self.marks[j + 1:]
                break
        if pos is None:
            return []
        off = []
        while self.seq and self.seq[-1] >= pos:
            c = self.claims[self.seq.pop()]
            c.on = False
            key = c.key
            self.ci[key].pop()
            self.cv[key].pop()
            if not self.ci[key]:
                del self.ci[key]
                del self.cv[key]
                j = bisect.bisect_left(self.ck, key)
                del self.ck[j]
            off.append(key)
        return off

    def live(self):
        """The changes this transaction would commit: the last standing one per key."""
        return {key: self.cv[key][-1] for key in self.ci}
