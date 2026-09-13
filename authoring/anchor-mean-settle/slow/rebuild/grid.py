"""Correct, and the shape the first plan actually builds: an array of absolute offsets.

Because the assumed height is one global scalar, the array is invalidated by a measurement
of any row and not only from the changed index onward, so the only way to keep it correct is
to rebuild the whole thing on every change. Every answer this produces is the reference's.
"""
import bisect

from pan import gues, mtr


class Row:
    __slots__ = ("rid", "ln", "hm", "gn")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = 0
        self.gn = -1


class Pan:
    __slots__ = ("rows", "acc", "at", "ms", "uc", "n", "gn", "ix", "w", "top", "anc", "dy",
                 "made")

    def __init__(self):
        self.rows = []
        self.acc = [0]
        self.at = {}
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


def redo(p):
    e = gues.hei(p)
    acc = [0]
    at = {}
    gn = p.gn
    for i, r in enumerate(p.rows):
        at[id(r)] = i
        acc.append(acc[-1] + (r.hm if r.gn == gn else e))
    p.acc = acc
    p.at = at


def row(p, rid):
    return p.ix.get(rid)


def held(p, r):
    return r.gn == p.gn


def hgt(p, r, e):
    return r.hm if r.gn == p.gn else e


def full(p):
    return p.ms + p.uc * gues.hei(p)


def edge(p):
    t = full(p)
    return t - mtr.VIEW if t > mtr.VIEW else 0


def off(p, r):
    return p.acc[p.at[id(r)]]


def hit(p):
    if not p.rows:
        return None, 0
    k = bisect.bisect_right(p.acc, p.top) - 1
    if k >= len(p.rows):
        k = len(p.rows) - 1
    return p.rows[k], p.acc[k]


def down(p, r, acc):
    stop = p.top + mtr.VIEW
    k = p.at[id(r)]
    while k < len(p.rows) and p.acc[k] < stop:
        yield p.rows[k]
        k += 1


def rank(p, r):
    return p.at[id(r)]


def kth(p, k):
    return p.rows[k]


def put(p, k, r):
    p.rows.insert(k, r)
    if r.gn == p.gn:
        p.ms += r.hm
    else:
        p.uc += 1
    p.n += 1
    p.ix[r.rid] = r
    redo(p)


def drop(p, r):
    p.rows.pop(p.at[id(r)])
    if r.gn == p.gn:
        p.ms -= r.hm
    else:
        p.uc -= 1
    p.n -= 1
    p.ix.pop(r.rid, None)
    redo(p)


def mark(p, r):
    h = mtr.high(r.ln, p.w)
    p.ms += h
    p.uc -= 1
    r.hm = h
    r.gn = p.gn
    redo(p)


def wipe(p, r):
    if r.gn != p.gn:
        return
    p.ms -= r.hm
    p.uc += 1
    r.gn = -1
    redo(p)


def fresh(p):
    p.gn += 1
    p.ms = 0
    p.uc = p.n
    redo(p)
