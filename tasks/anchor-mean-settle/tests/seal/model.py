"""An independent implementation of the panel, written from the frozen contract.

It shares no code with the reference under `solution/` and does not resemble it
structurally. The reference carries the two additive series in blocks over the row order and
splices inside a block; this carries them as subtree aggregates of a randomized binary tree
indexed by position, reads a prefix off the path from a node to the root, resolves a scroll
position by descending on the same aggregates, and inserts or deletes by rotation. Two
implementations written apart that agree on every graded program are the evidence that a
trace is a property of the contract rather than of one author's structure.

The contract, restated as this file implements it:

  the assumed height  a row nobody has measured stands as tall as the floor mean of the
                      heights of the rows that have, over the rows still in the list, and
                      24 tall while none of them has been measured. One scalar for the
                      panel, so a measurement re-heights every unmeasured row at once.
  tall                the measured heights plus the unmeasured rows at that assumption.
  the scroll range    0 to tall less the view's 300, and every landing is clamped to it.
  the anchor          the first row the view touches and the distance from the view's top
                      edge to its own, which is zero or negative. `roll` clamps and then
                      takes one; a pass takes one before it measures anything; an edit
                      re-seats against the one being held, keeping that distance.
  pass                measure the lowest unmeasured row the view touches, re-seat, ask what
                      the view touches again, and stop when it touches none. `seen` counts
                      what was measured.
  del                 of the anchor falls to the row that took its index, or to the new last
                      row, keeping the distance; of the last row leaves no anchor.
  move                keeps the row's measurement and its anchor role.
  set                 gives up that row's measurement, and with it a sample from the mean.
  span                gives up every measurement.
  face                names the first row the view touches and its edge relative to the
                      view's, or `face none` when there are no rows.
"""
import random

LINE = 18
PAD = 6
DEF = 24
VIEW = 300
W0 = 40


def high(ln, w):
    n = (ln + w - 1) // w
    if n < 1:
        n = 1
    return LINE * n + PAD


class Nd:
    __slots__ = ("pri", "rid", "ln", "hm", "sz", "ms", "uc", "l", "r", "up")

    def __init__(self, pri, rid, ln):
        self.pri = pri
        self.rid = rid
        self.ln = ln
        self.hm = None
        self.sz = 1
        self.ms = 0
        self.uc = 1
        self.l = None
        self.r = None
        self.up = None


def sz(x):
    return x.sz if x else 0


class Tree:
    def __init__(self, seed):
        self.root = None
        self.rng = random.Random(seed)
        self.ms = 0
        self.uc = 0
        self.n = 0

    # --- aggregates ---
    def pull(self, x):
        s = 1
        m = x.hm if x.hm is not None else 0
        u = 0 if x.hm is not None else 1
        for k in (x.l, x.r):
            if k:
                s += k.sz
                m += k.ms
                u += k.uc
        x.sz = s
        x.ms = m
        x.uc = u

    def fix(self, x):
        while x:
            self.pull(x)
            x = x.up

    def est(self):
        mc = self.n - self.uc
        return self.ms // mc if mc else DEF

    def tall(self):
        return self.ms + self.uc * self.est()

    def hof(self, x, e):
        return x.hm if x.hm is not None else e

    def sub(self, x, e):
        return (x.ms + x.uc * e) if x else 0

    # --- rotations ---
    def swing(self, x):
        """Lift x above its parent."""
        p = x.up
        g = p.up
        if p.l is x:
            p.l = x.r
            if x.r:
                x.r.up = p
            x.r = p
        else:
            p.r = x.l
            if x.l:
                x.l.up = p
            x.l = p
        p.up = x
        x.up = g
        if g:
            if g.l is p:
                g.l = x
            else:
                g.r = x
        else:
            self.root = x
        self.pull(p)
        self.pull(x)

    def place(self, k, nd):
        """Insert nd so that it becomes row number k."""
        if self.root is None:
            self.root = nd
        else:
            x = self.root
            while True:
                left = sz(x.l)
                if k <= left:
                    if x.l is None:
                        x.l = nd
                        nd.up = x
                        break
                    x = x.l
                else:
                    k -= left + 1
                    if x.r is None:
                        x.r = nd
                        nd.up = x
                        break
                    x = x.r
        self.fix(nd.up)
        while nd.up and nd.pri > nd.up.pri:
            self.swing(nd)
        self.n += 1
        if nd.hm is None:
            self.uc += 1
        else:
            self.ms += nd.hm

    def yank(self, nd):
        while nd.l or nd.r:
            if nd.l is None:
                self.swing(nd.r)
            elif nd.r is None:
                self.swing(nd.l)
            elif nd.l.pri > nd.r.pri:
                self.swing(nd.l)
            else:
                self.swing(nd.r)
        p = nd.up
        if p is None:
            self.root = None
        elif p.l is nd:
            p.l = None
        else:
            p.r = None
        nd.up = None
        self.fix(p)
        self.n -= 1
        if nd.hm is None:
            self.uc -= 1
        else:
            self.ms -= nd.hm

    # --- reading ---
    def before(self, nd):
        """Height of every row ahead of nd."""
        e = self.est()
        acc = self.sub(nd.l, e)
        x = nd
        while x.up:
            if x.up.r is x:
                acc += self.sub(x.up.l, e) + self.hof(x.up, e)
            x = x.up
        return acc

    def rank(self, nd):
        k = sz(nd.l)
        x = nd
        while x.up:
            if x.up.r is x:
                k += sz(x.up.l) + 1
            x = x.up
        return k

    def kth(self, k):
        x = self.root
        while x:
            left = sz(x.l)
            if k < left:
                x = x.l
            elif k == left:
                return x
            else:
                k -= left + 1
                x = x.r
        return None

    def at(self, top):
        """First row whose far edge is past `top`, with the height ahead of it."""
        e = self.est()
        acc = 0
        x = self.root
        while x:
            hl = self.sub(x.l, e)
            if acc + hl + self.hof(x, e) > top:
                if acc + hl > top:
                    x = x.l
                else:
                    return x, acc + hl
            else:
                acc += hl + self.hof(x, e)
                x = x.r
        return None, acc

    def after(self, nd):
        if nd.r:
            x = nd.r
            while x.l:
                x = x.l
            return x
        x = nd
        while x.up and x.up.r is x:
            x = x.up
        return x.up


class Pan:
    def __init__(self, seed=98317):
        self.t = Tree(seed)
        self.w = W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.out = []
        self.made = 0
        self.ix = {}

    def edge(self):
        t = self.t.tall()
        return t - VIEW if t > VIEW else 0

    def clamp(self, x):
        lim = self.edge()
        if x < 0:
            return 0
        return lim if x > lim else x

    def take(self):
        nd, acc = self.t.at(self.top)
        if nd is None:
            self.anc = None
            self.dy = 0
            return
        self.anc = nd
        self.dy = acc - self.top

    def seat(self):
        if self.anc is None:
            self.top = self.clamp(self.top)
        else:
            self.top = self.clamp(self.t.before(self.anc) - self.dy)

    def born(self, rid, ln):
        nd = Nd(self.t.rng.getrandbits(30), rid, ln)
        self.ix[rid] = nd
        return nd

    def op_bulk(self, n, lo, sp):
        for i in range(n):
            self.made += 1
            self.t.place(self.t.n, self.born("k%d" % self.made, lo + (i % sp)))
        self.seat()

    def op_ins(self, k, rid, ln):
        self.t.place(k, self.born(rid, ln))
        self.seat()

    def op_del(self, rid):
        nd = self.ix.get(rid)
        if nd is None:
            return
        k = self.t.rank(nd)
        self.t.yank(nd)
        del self.ix[rid]
        if self.anc is nd:
            if self.t.n == 0:
                self.anc = None
                self.top = 0
            else:
                self.anc = self.t.kth(k if k < self.t.n else self.t.n - 1)
        self.seat()

    def op_move(self, rid, k):
        nd = self.ix.get(rid)
        if nd is None:
            return
        hm = nd.hm
        self.t.yank(nd)
        nd.l = nd.r = nd.up = None
        nd.sz = 1
        nd.hm = hm
        nd.ms = hm if hm is not None else 0
        nd.uc = 0 if hm is not None else 1
        self.t.place(k, nd)
        self.seat()

    def op_set(self, rid, ln):
        nd = self.ix.get(rid)
        if nd is None:
            return
        nd.ln = ln
        if nd.hm is not None:
            self.t.ms -= nd.hm
            self.t.uc += 1
            nd.hm = None
            self.t.fix(nd)
        self.seat()

    def op_span(self, w):
        self.w = w
        x = []
        cur = self.t.root
        stack = [cur] if cur else []
        while stack:
            nd = stack.pop()
            nd.hm = None
            x.append(nd)
            if nd.l:
                stack.append(nd.l)
            if nd.r:
                stack.append(nd.r)
        for nd in reversed(x):
            self.t.pull(nd)
        self.t.ms = 0
        self.t.uc = self.t.n
        self.seat()

    def op_roll(self, d):
        self.top = self.clamp(self.top + d)
        self.take()

    def op_pass(self):
        self.take()
        k = 0
        while True:
            nd, acc = self.t.at(self.top)
            if nd is None:
                break
            pick = None
            stop = self.top + VIEW
            e = self.t.est()
            cur, off = nd, acc
            while cur and off < stop:
                if cur.hm is None:
                    pick = cur
                    break
                off += self.t.hof(cur, e)
                cur = self.t.after(cur)
            if pick is None:
                break
            h = high(pick.ln, self.w)
            pick.hm = h
            self.t.ms += h
            self.t.uc -= 1
            self.t.fix(pick)
            k += 1
            self.seat()
        self.out.append("seen %d" % k)

    def op_top(self):
        self.out.append("top %d" % self.top)

    def op_tall(self):
        self.out.append("tall %d" % self.t.tall())

    def op_face(self):
        nd, acc = self.t.at(self.top)
        if nd is None:
            self.out.append("face none")
            return
        self.out.append("face %s %d" % (nd.rid, acc - self.top))


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


def expect(lines):
    return run(lines)
