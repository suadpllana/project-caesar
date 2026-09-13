"""Candidate reference: the two additive series carried by blocks over the row order."""

LINE = 18
PAD = 6
DEF = 24
VIEW = 300
W0 = 40
TB = 512


def high(ln, w):
    lines = (ln + w - 1) // w
    if lines < 1:
        lines = 1
    return LINE * lines + PAD


class Row:
    __slots__ = ("rid", "ln", "hm", "gn", "bk")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = 0
        self.gn = -1
        self.bk = None


class Blk:
    __slots__ = ("rs", "ms", "uc")

    def __init__(self, rs):
        self.rs = rs
        self.ms = 0
        self.uc = len(rs)


class Pan:
    def __init__(self):
        self.bs = [Blk([])]
        self.ms = 0
        self.uc = 0
        self.n = 0
        self.gn = 0
        self.ix = {}
        self.w = W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.out = []
        self.made = 0

    # --- derived ---
    def est(self):
        mc = self.n - self.uc
        return self.ms // mc if mc else DEF

    def tall(self):
        return self.ms + self.uc * self.est()

    def limit(self):
        t = self.tall()
        return t - VIEW if t > VIEW else 0

    def clamp(self, x):
        lim = self.limit()
        if x < 0:
            return 0
        return lim if x > lim else x

    def rh(self, r, e):
        return r.hm if r.gn == self.gn else e

    def off_row(self, row):
        e = self.est()
        acc = 0
        gn = self.gn
        for b in self.bs:
            if row.bk is b:
                for r in b.rs:
                    if r is row:
                        return acc
                    acc += r.hm if r.gn == gn else e
                return acc
            acc += b.ms + b.uc * e
        return acc

    def hit(self):
        """(row, its offset) for the first row intersecting the viewport."""
        e = self.est()
        top = self.top
        acc = 0
        gn = self.gn
        last = None
        for b in self.bs:
            bh = b.ms + b.uc * e
            if acc + bh > top:
                for r in b.rs:
                    h = r.hm if r.gn == gn else e
                    if acc + h > top:
                        return r, acc
                    acc += h
            else:
                acc += bh
            if b.rs:
                last = b.rs[-1]
        if last is None:
            return None, 0
        return last, acc - (last.hm if last.gn == gn else e)

    def walk(self, row, off):
        """Rows from `row` forward while their offset is inside the viewport."""
        e = self.est()
        stop = self.top + VIEW
        gn = self.gn
        seen = []
        live = False
        for b in self.bs:
            if not live and row.bk is not b:
                continue
            for r in b.rs:
                if not live:
                    if r is row:
                        live = True
                    else:
                        continue
                if off >= stop:
                    return seen
                seen.append(r)
                off += r.hm if r.gn == gn else e
        return seen

    # --- block plumbing ---
    def at(self, k):
        """(block, index inside it) for row position k."""
        for b in self.bs:
            if k < len(b.rs):
                return b, k
            k -= len(b.rs)
        b = self.bs[-1]
        return b, len(b.rs)

    def put(self, k, row):
        b, j = self.at(k)
        b.rs.insert(j, row)
        row.bk = b
        b.uc += 1
        self.uc += 1
        self.n += 1
        if len(b.rs) > 2 * TB:
            self.split(b)

    def split(self, b):
        cut = len(b.rs) // 2
        tail = b.rs[cut:]
        del b.rs[cut:]
        nb = Blk(tail)
        for r in tail:
            r.bk = nb
        self.retag(b)
        self.retag(nb)
        self.bs.insert(self.bs.index(b) + 1, nb)

    def retag(self, b):
        ms = uc = 0
        gn = self.gn
        for r in b.rs:
            if r.gn == gn:
                ms += r.hm
            else:
                uc += 1
        b.ms = ms
        b.uc = uc

    def drop(self, row):
        b = row.bk
        b.rs.remove(row)
        if row.gn == self.gn:
            b.ms -= row.hm
            self.ms -= row.hm
        else:
            b.uc -= 1
            self.uc -= 1
        self.n -= 1
        row.bk = None
        if not b.rs and len(self.bs) > 1:
            self.bs.remove(b)

    def unmeasure(self, row):
        if row.gn == self.gn:
            b = row.bk
            b.ms -= row.hm
            b.uc += 1
            self.ms -= row.hm
            self.uc += 1
            row.gn = -1

    def measure(self, row):
        h = high(row.ln, self.w)
        b = row.bk
        b.ms += h
        b.uc -= 1
        self.ms += h
        self.uc -= 1
        row.hm = h
        row.gn = self.gn

    def pos(self, row):
        k = 0
        for b in self.bs:
            if row.bk is b:
                return k + b.rs.index(row)
            k += len(b.rs)
        return -1

    # --- anchor ---
    def take(self):
        row, off = self.hit()
        if row is None:
            self.anc = None
            self.dy = 0
            return
        self.anc = row
        self.dy = off - self.top

    def seat(self):
        if self.anc is None:
            self.top = self.clamp(self.top)
        else:
            self.top = self.clamp(self.off_row(self.anc) - self.dy)

    # --- ops ---
    def op_bulk(self, n, lo, sp):
        for i in range(n):
            self.made += 1
            row = Row("k%d" % self.made, lo + (i % sp))
            self.ix[row.rid] = row
            self.put(self.n, row)
        self.seat()

    def op_ins(self, k, rid, ln):
        row = Row(rid, ln)
        self.ix[rid] = row
        self.put(k, row)
        self.seat()

    def op_del(self, rid):
        row = self.ix.get(rid)
        if row is None or row.bk is None:
            return
        k = self.pos(row)
        self.drop(row)
        del self.ix[rid]
        if self.anc is row:
            if self.n == 0:
                self.anc = None
                self.top = 0
            else:
                b, j = self.at(k if k < self.n else self.n - 1)
                self.anc = b.rs[j]
        self.seat()

    def op_move(self, rid, k):
        row = self.ix.get(rid)
        if row is None or row.bk is None:
            return
        keep, gn = row.hm, row.gn
        b = row.bk
        b.rs.remove(row)
        if row.gn == self.gn:
            b.ms -= row.hm
            self.ms -= row.hm
        else:
            b.uc -= 1
            self.uc -= 1
        self.n -= 1
        row.bk = None
        if not b.rs and len(self.bs) > 1:
            self.bs.remove(b)
        row.gn = -1
        self.put(k, row)
        if gn == self.gn:
            row.hm = keep
            row.gn = gn
            nb = row.bk
            nb.ms += keep
            nb.uc -= 1
            self.ms += keep
            self.uc -= 1
        self.seat()

    def op_set(self, rid, ln):
        row = self.ix.get(rid)
        if row is None or row.bk is None:
            return
        row.ln = ln
        self.unmeasure(row)
        self.seat()

    def op_span(self, w):
        self.w = w
        self.gn += 1
        self.ms = 0
        self.uc = self.n
        for b in self.bs:
            b.ms = 0
            b.uc = len(b.rs)
        self.seat()

    def op_roll(self, d):
        self.top = self.clamp(self.top + d)
        self.take()

    def op_pass(self):
        self.take()
        k = 0
        while True:
            row, off = self.hit()
            if row is None:
                break
            pick = None
            for r in self.walk(row, off):
                if r.gn != self.gn:
                    pick = r
                    break
            if pick is None:
                break
            self.measure(pick)
            k += 1
            self.seat()
        self.out.append("seen %d" % k)

    def op_top(self):
        self.out.append("top %d" % self.top)

    def op_tall(self):
        self.out.append("tall %d" % self.tall())

    def op_face(self):
        row, off = self.hit()
        if row is None:
            self.out.append("face none")
            return
        self.out.append("face %s %d" % (row.rid, off - self.top))


def ex(p, t):
    o = t[0]
    if o == "bulk":
        p.op_bulk(int(t[1]), int(t[2]), int(t[3]))
    elif o == "ins":
        p.op_ins(int(t[1]), t[2], int(t[3]))
    elif o == "del":
        p.op_del(t[1])
    elif o == "move":
        p.op_move(t[1], int(t[2]))
    elif o == "set":
        p.op_set(t[1], int(t[2]))
    elif o == "span":
        p.op_span(int(t[1]))
    elif o == "roll":
        p.op_roll(int(t[1]))
    elif o == "pass":
        p.op_pass()
    elif o == "top":
        p.op_top()
    elif o == "tall":
        p.op_tall()
    elif o == "face":
        p.op_face()
    else:
        raise ValueError(o)


def run(lines):
    p = Pan()
    for line in lines:
        line = line.strip()
        if line:
            ex(p, tuple(line.split()))
    return p.out
