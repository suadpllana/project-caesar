"""Holds and the runs they leave, carrying only the youngest living peg of each run.

Nothing is carried about how many pegs keep a block: a run is filed under its youngest living peg
and nothing else, so the only thing settled as the program runs is whether a block is kept at all.
What one peg alone keeps is worked out when a tally asks.
"""
from keep import cover

B, V, T1, T2, HI, OK = range(6)


class Acct:
    def __init__(self):
        self.t = 0
        self.roll = []
        self.hn = {}
        self.op = {}
        self.nh = {}
        self.rs = {}
        self.stop = {}
        self.fresh = []
        self.q = []
        self.out = set()
        self.pt = {}
        self.pn = {}
        self.pf = {}
        self.home = {}
        self.hi_at = {}
        self.all = []


def new():
    return Acct()


def born(a, b, t):
    a.t = t
    a.roll.append(b)
    a.nh[b] = 0
    a.rs[b] = []


def hold(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0)
    if n == 0:
        a.op[k] = t
        a.nh[b] += 1
    a.hn[k] = n + 1


def free(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn[k] - 1
    if n:
        a.hn[k] = n
        return
    del a.hn[k]
    shut(a, b, v, a.op.pop(k), t)
    a.nh[b] -= 1
    touch(a, b, t)
    flush(a)


def shut(a, b, v, t1, t2):
    hi = cover.last(a, v, t1, t2)
    if hi is None:
        return
    r = [b, v, t1, t2, hi, True]
    a.all.append(r)
    a.rs[b].append(r)
    a.hi_at.setdefault(a.pn[v][hi], []).append(r)


def kill(a, r):
    r[OK] = False
    a.rs[r[B]].remove(r)


def touch(a, b, t):
    if not a.nh[b] and not a.rs[b] and b not in a.stop:
        a.stop[b] = t
        a.fresh.append(b)


def flush(a):
    if a.fresh:
        a.fresh.sort()
        a.q.extend(a.fresh)
        del a.fresh[:]
