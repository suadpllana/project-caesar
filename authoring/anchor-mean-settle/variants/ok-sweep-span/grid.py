"""The row order, and the two additive series that make a prefix height readable.

An unmeasured row is assumed to be `gues.hei` tall, and that figure is one global scalar
recomputed from every measurement, so the height ahead of row k is

    (sum of the measured heights before k) + (count of unmeasured rows before k) * scalar

and no absolute offset can be stored: a single measurement anywhere moves the scalar and
with it every offset in the list. What is stored instead is those two series, in blocks
over the row order, each block carrying the measured-height sum and the unmeasured count of
the rows it holds. A prefix is then the whole blocks ahead of the row plus a walk inside
its own, which is what lets the panel answer at the scale the wide programs run at while
an edit at any index is still a splice inside one block.

`gn` is the width generation. A `span` changes what every measurement means, so rather than
touch every row it bumps the generation: a row counts as measured only while its own
generation is the panel's.
"""
from pan import gues, mtr

TB = 512


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
    __slots__ = ("bs", "ms", "uc", "n", "gn", "ix", "w", "top", "anc", "dy", "made")

    def __init__(self):
        self.bs = [Blk([])]
        self.ms = 0
        self.uc = 0
        self.n = 0
        self.gn = 0
        self.ix = {}
        self.w = mtr.W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.made = 0


def new():
    return Pan()


def row(p, rid):
    return p.ix.get(rid)


def held(p, r):
    return r.gn == p.gn


def hgt(p, r, e):
    return r.hm if r.gn == p.gn else e


def bh(p, b, e):
    return b.ms + b.uc * e


def full(p):
    return p.ms + p.uc * gues.hei(p)


def edge(p):
    t = full(p)
    return t - mtr.VIEW if t > mtr.VIEW else 0


def off(p, r):
    """Height of every row ahead of r."""
    e = gues.hei(p)
    acc = 0
    gn = p.gn
    for b in p.bs:
        if r.bk is b:
            for x in b.rs:
                if x is r:
                    return acc
                acc += x.hm if x.gn == gn else e
            return acc
        acc += b.ms + b.uc * e
    return acc


def hit(p):
    """The first row the view touches, and the height ahead of it."""
    e = gues.hei(p)
    top = p.top
    acc = 0
    gn = p.gn
    tail = None
    for b in p.bs:
        w = b.ms + b.uc * e
        if acc + w > top:
            for x in b.rs:
                h = x.hm if x.gn == gn else e
                if acc + h > top:
                    return x, acc
                acc += h
        else:
            acc += w
        if b.rs:
            tail = b.rs[-1]
    if tail is None:
        return None, 0
    return tail, acc - hgt(p, tail, e)


def down(p, r, acc):
    """Rows from r forward while the view still reaches them."""
    e = gues.hei(p)
    stop = p.top + mtr.VIEW
    gn = p.gn
    live = False
    for b in p.bs:
        if not live and r.bk is not b:
            continue
        for x in b.rs:
            if not live:
                if x is r:
                    live = True
                else:
                    continue
            if acc >= stop:
                return
            yield x
            acc += x.hm if x.gn == gn else e


def spot(p, k):
    for b in p.bs:
        if k < len(b.rs):
            return b, k
        k -= len(b.rs)
    return p.bs[-1], len(p.bs[-1].rs)


def rank(p, r):
    k = 0
    for b in p.bs:
        if r.bk is b:
            return k + b.rs.index(r)
        k += len(b.rs)
    return -1


def kth(p, k):
    b, j = spot(p, k)
    return b.rs[j]


def put(p, k, r):
    b, j = spot(p, k)
    b.rs.insert(j, r)
    r.bk = b
    if r.gn == p.gn:
        b.ms += r.hm
        p.ms += r.hm
    else:
        b.uc += 1
        p.uc += 1
    p.n += 1
    p.ix[r.rid] = r
    if len(b.rs) > 2 * TB:
        cut(p, b)


def cut(p, b):
    half = len(b.rs) // 2
    tail = b.rs[half:]
    del b.rs[half:]
    nb = Blk(tail)
    for x in tail:
        x.bk = nb
    tot(p, b)
    tot(p, nb)
    p.bs.insert(p.bs.index(b) + 1, nb)


def tot(p, b):
    ms = uc = 0
    gn = p.gn
    for x in b.rs:
        if x.gn == gn:
            ms += x.hm
        else:
            uc += 1
    b.ms = ms
    b.uc = uc


def drop(p, r):
    b = r.bk
    b.rs.remove(r)
    if r.gn == p.gn:
        b.ms -= r.hm
        p.ms -= r.hm
    else:
        b.uc -= 1
        p.uc -= 1
    p.n -= 1
    r.bk = None
    p.ix.pop(r.rid, None)
    if not b.rs and len(p.bs) > 1:
        p.bs.remove(b)


def mark(p, r):
    h = mtr.high(r.ln, p.w)
    b = r.bk
    b.ms += h
    b.uc -= 1
    p.ms += h
    p.uc -= 1
    r.hm = h
    r.gn = p.gn


def wipe(p, r):
    if r.gn != p.gn:
        return
    b = r.bk
    b.ms -= r.hm
    b.uc += 1
    p.ms -= r.hm
    p.uc += 1
    r.gn = -1


def fresh(p):
    for b in p.bs:
        for x in b.rs:
            x.gn = -1
            x.hm = 0
        b.ms = 0
        b.uc = len(b.rs)
    p.ms = 0
    p.uc = p.n
