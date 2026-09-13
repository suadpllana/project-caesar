import gc
import hashlib

gc.disable()


class Node:
    __slots__ = ('k', 'v', 'p', 'l', 'r', 'n', 'lo', 'hi', 'w')

    def __init__(self, k, v, p, l=None, r=None):
        self.k, self.v, self.p, self.l, self.r = k, v, p, l, r
        self.n = 1 + (l.n if l else 0) + (r.n if r else 0)
        self.w = (v[0] - k + 1 if isinstance(v, tuple) else 0) + (l.w if l else 0) + (r.w if r else 0)
        self.lo = l.lo if l else k
        self.hi = r.hi if r else k


def rank(k):
    if k < -(1 << 63) or k >= (1 << 63):
        raw = k.to_bytes((k.bit_length() + 8) // 8, 'big', signed=True)
        return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), 'big')
    x = (k + 0x9e3779b97f4a7c15) & 0xffffffffffffffff
    x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & 0xffffffffffffffff
    x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & 0xffffffffffffffff
    return x ^ (x >> 31)


def node(t, l, r):
    return Node(t.k, t.v, t.p, l, r)


def split(t, k):
    if t is None:
        return None, None
    if t.k < k:
        a, b = split(t.r, k)
        return node(t, t.l, a), b
    a, b = split(t.l, k)
    return a, node(t, b, t.r)


def merge(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a.p > b.p:
        return node(a, a.l, merge(a.r, b))
    return node(b, merge(a, b.l), b.r)


def put(t, k, v, p=None):
    if p is None:
        p = rank(k)
    if t is None:
        return Node(k, v, p)
    if k == t.k:
        return Node(k, v, t.p, t.l, t.r)
    if p > t.p:
        a, b = split(t, k)
        return Node(k, v, p, a, b)
    if k < t.k:
        return node(t, put(t.l, k, v, p), t.r)
    return node(t, t.l, put(t.r, k, v, p))


def drop(t, k):
    if t is None:
        return None
    if k == t.k:
        return merge(t.l, t.r)
    if k < t.k:
        return node(t, drop(t.l, k), t.r)
    return node(t, t.l, drop(t.r, k))


def get(t, k):
    while t:
        if k == t.k:
            return t.v
        t = t.l if k < t.k else t.r
    return None


def floor(t, k):
    last = None
    while t:
        if t.k <= k:
            last = t
            t = t.r
        else:
            t = t.l
    return last


def items(t, lo=None, hi=None):
    if t is None or (lo is not None and t.hi < lo) or (hi is not None and t.lo > hi):
        return
    yield from items(t.l, lo, hi)
    if (lo is None or t.k >= lo) and (hi is None or t.k <= hi):
        yield t.k, t.v
    yield from items(t.r, lo, hi)


def over(t, lo, hi):
    q = floor(t, lo)
    if q is not None and q.v[0] >= lo:
        lo = q.k
    yield from items(t, lo, hi)


class Buck:
    __slots__ = ('run', 'own', 'n')

    def __init__(self, run=None, own=None, n=0):
        self.run, self.own, self.n = run, own, n


EMPTY = Buck()


def hold(tab, buck):
    return tab.buck.get(buck, EMPTY)


def rows(tab, buck):
    return hold(tab, buck).n


def at(tab, buck, key):
    q = floor(hold(tab, buck).run, key)
    return q.v[2] if q and q.v[0] >= key else None


def insert(b, a, z, birth, sid):
    val = (z, birth, sid)
    one = put(get(b.own, sid), a, val)
    return Buck(put(b.run, a, val), put(b.own, sid, one), b.n + z - a + 1)


def erase(b, a):
    z, birth, sid = get(b.run, a)
    one = drop(get(b.own, sid), a)
    owners = put(b.own, sid, one) if one else drop(b.own, sid)
    return Buck(drop(b.run, a), owners, b.n - (z - a + 1))


def size(t):
    return t.w if t else 0
