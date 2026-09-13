"""Naive reference semantics for anchor-mean-settle, written the obvious way.

Everything is recomputed by walking the row list. This file is the spec: the fast
implementations must agree with it event for event on every program.
"""

LINE = 18
PAD = 6
DEF = 24
VIEW = 300
W0 = 40


def high(ln, w):
    lines = (ln + w - 1) // w
    if lines < 1:
        lines = 1
    return LINE * lines + PAD


class Row:
    __slots__ = ("rid", "ln", "hm")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = None


class Pan:
    def __init__(self):
        self.rows = []
        self.w = W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.out = []
        self.made = 0

    # --- derived, all by walking ---
    def est(self):
        s = n = 0
        for r in self.rows:
            if r.hm is not None:
                s += r.hm
                n += 1
        return s // n if n else DEF

    def h(self, r, e):
        return r.hm if r.hm is not None else e

    def tall(self):
        e = self.est()
        return sum(self.h(r, e) for r in self.rows)

    def off(self, k):
        e = self.est()
        return sum(self.h(r, e) for r in self.rows[:k])

    def limit(self):
        t = self.tall()
        return t - VIEW if t > VIEW else 0

    def clamp(self, x):
        lim = self.limit()
        if x < 0:
            return 0
        return lim if x > lim else x

    def first_hit(self):
        """Lowest index whose row intersects the viewport."""
        e = self.est()
        acc = 0
        for i, r in enumerate(self.rows):
            acc += self.h(r, e)
            if acc > self.top:
                return i
        return len(self.rows) - 1

    def win(self):
        """Indices of every row intersecting the viewport."""
        e = self.est()
        acc = 0
        hit = []
        for i, r in enumerate(self.rows):
            hi = self.h(r, e)
            if acc < self.top + VIEW and acc + hi > self.top:
                hit.append(i)
            acc += hi
            if acc >= self.top + VIEW:
                break
        return hit

    def index(self, row):
        for i, r in enumerate(self.rows):
            if r is row:
                return i
        return -1

    # --- anchor ---
    def take(self):
        if not self.rows:
            self.anc = None
            self.dy = 0
            return
        i = self.first_hit()
        self.anc = self.rows[i]
        self.dy = self.off(i) - self.top

    def seat(self):
        if self.anc is None:
            self.top = self.clamp(self.top)
        else:
            self.top = self.clamp(self.off(self.index(self.anc)) - self.dy)

    def find(self, rid):
        for i, r in enumerate(self.rows):
            if r.rid == rid:
                return i
        return -1

    # --- ops ---
    def op_bulk(self, n, lo, sp):
        for i in range(n):
            self.made += 1
            self.rows.append(Row("k%d" % self.made, lo + (i % sp)))
        self.seat()

    def op_ins(self, k, rid, ln):
        self.rows.insert(k, Row(rid, ln))
        self.seat()

    def op_del(self, rid):
        k = self.find(rid)
        if k < 0:
            return
        row = self.rows.pop(k)
        if self.anc is row:
            if not self.rows:
                self.anc = None
                self.top = 0
            elif k < len(self.rows):
                self.anc = self.rows[k]
            else:
                self.anc = self.rows[-1]
        self.seat()

    def op_move(self, rid, k):
        i = self.find(rid)
        if i < 0:
            return
        row = self.rows.pop(i)
        self.rows.insert(k, row)
        self.seat()

    def op_set(self, rid, ln):
        k = self.find(rid)
        if k < 0:
            return
        self.rows[k].ln = ln
        self.rows[k].hm = None
        self.seat()

    def op_span(self, w):
        self.w = w
        for r in self.rows:
            r.hm = None
        self.seat()

    def op_roll(self, d):
        self.top = self.clamp(self.top + d)
        self.take()

    def op_pass(self):
        self.take()
        k = 0
        while True:
            pick = -1
            for i in self.win():
                if self.rows[i].hm is None:
                    pick = i
                    break
            if pick < 0:
                break
            r = self.rows[pick]
            r.hm = high(r.ln, self.w)
            k += 1
            self.seat()
        self.out.append("seen %d" % k)

    def op_top(self):
        self.out.append("top %d" % self.top)

    def op_tall(self):
        self.out.append("tall %d" % self.tall())

    def op_face(self):
        if not self.rows:
            self.out.append("face none")
            return
        i = self.first_hit()
        self.out.append("face %s %d" % (self.rows[i].rid, self.off(i) - self.top))


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
