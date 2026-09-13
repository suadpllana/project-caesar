#!/bin/bash
set -euo pipefail
# Refresh the largest conflicting slab instead of the required smallest slab.

cat > /app/tab/live.py <<'SLAB_LIVE_PY_EOF'
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
SLAB_LIVE_PY_EOF

cat > /app/tab/lay.py <<'SLAB_LAY_PY_EOF'
from tab import mark, wipe


def part(tab, num, buck, lo, hi):
    took = wipe.part(tab, buck, lo, hi)
    mark.fresh(tab, buck, lo, hi, num)
    return hi - lo + 1 - took
SLAB_LAY_PY_EOF

cat > /app/tab/wipe.py <<'SLAB_WIPE_PY_EOF'
from tab import live


def part(tab, buck, lo, hi):
    b = live.hold(tab, buck)
    cut = 0
    for a, (z, birth, sid) in list(live.over(b.run, lo, hi)):
        b = live.erase(b, a)
        if a < lo:
            b = live.insert(b, a, lo - 1, birth, sid)
        if z > hi:
            b = live.insert(b, hi + 1, z, birth, sid)
        cut += min(z, hi) - max(a, lo) + 1
    tab.buck[buck] = b
    return cut
SLAB_WIPE_PY_EOF

cat > /app/tab/mark.py <<'SLAB_MARK_PY_EOF'
from tab import live


def fresh(tab, buck, lo, hi, num):
    sid = tab.mint()
    tab.buck[buck] = live.insert(live.hold(tab, buck), lo, hi, num, sid)
    return sid


def keep(tab, buck, sids):
    b = live.hold(tab, buck)
    sid = tab.mint()
    for old in sids:
        for a, (z, birth, _) in list(live.items(live.get(b.own, old))):
            b = live.erase(b, a)
            b = live.insert(b, a, z, birth, sid)
    tab.buck[buck] = b
    return sid
SLAB_MARK_PY_EOF

cat > /app/tab/take.py <<'SLAB_TAKE_PY_EOF'
from tab import live, mark


class Again(Exception):
    def __init__(self, buck, sources):
        self.buck, self.sources = buck, sources


def part(tab, view, head, buck, lo, hi):
    old = view.get(buck, live.EMPTY)
    now = live.hold(tab, buck)
    picked = {}
    counts = {}
    for a, (z, birth, sid) in live.over(old.run, lo, hi):
        if sid not in picked:
            src = live.get(old.own, sid)
            picked[sid] = src.lo >= lo and live.get(src, src.hi)[0] <= hi
        if not picked[sid]:
            continue
        for c, (d, era, target) in live.over(now.run, a, z):
            if era == birth:
                counts[target] = counts.get(target, 0) + min(z, d) - max(a, c) + 1
    eligible = []
    mixed = []
    for sid, count in counts.items():
        if count == live.size(live.get(now.own, sid)):
            eligible.append(sid)
        else:
            mixed.append(sid)
    if mixed:
        conflicted = live.get(now.own, max(mixed))
        start = head.get(buck, live.EMPTY)
        seeds = set()
        for a, (z, birth, _) in live.items(conflicted):
            for c, (d, era, sid) in live.over(start.run, a, z):
                if era == birth:
                    seeds.add(sid)
        raise Again(buck, seeds)
    if len(eligible) < 2:
        return False
    mark.keep(tab, buck, eligible)
    return True


def refresh(view, head, buck, seeds):
    old = view.get(buck, live.EMPTY)
    start = head.get(buck, live.EMPTY)
    left, right = set(), set(seeds)
    pending = [(1, sid) for sid in seeds]
    while pending:
        side, sid = pending.pop()
        src, dst = (start, old) if side else (old, start)
        dest, tag = (left, 0) if side else (right, 1)
        for a, (z, _, _) in live.items(live.get(src.own, sid)):
            for c, (d, _, other) in live.over(dst.run, a, z):
                if other not in dest:
                    dest.add(other)
                    pending.append((tag, other))
    if left == right and all(
        list(live.items(live.get(old.own, sid))) == list(live.items(live.get(start.own, sid)))
        for sid in left
    ):
        return False
    b = old
    for sid in left:
        for a, _ in live.items(live.get(old.own, sid)):
            b = live.erase(b, a)
    for sid in right:
        for a, (z, birth, _) in live.items(live.get(start.own, sid)):
            b = live.insert(b, a, z, birth, sid)
    view[buck] = b
    return True
SLAB_TAKE_PY_EOF

cat > /app/tab/push.py <<'SLAB_PUSH_PY_EOF'
from tab import lay, say, take, wipe


def once(tab, prop, view, head, num):
    add = gone = 0
    made = False
    for kind, buck, lo, hi in prop.parts:
        if kind == 'put':
            add += lay.part(tab, num, buck, lo, hi)
            made = True
        elif kind == 'cut':
            gone += wipe.part(tab, buck, lo, hi)
        elif take.part(tab, view, head, buck, lo, hi):
            made = True
    return add, gone, made


def run(tab, prop):
    head = dict(tab.buck)
    view = dict(prop.root)
    number, first = tab.head + 1, tab.next
    while True:
        try:
            added, removed, made = once(tab, prop, view, head, number)
            break
        except take.Again as clash:
            tab.buck = dict(head)
            tab.next = first
            if not take.refresh(view, head, clash.buck, clash.sources):
                tab.out.append('clash %s' % prop.tag)
                return
    if not made and not removed:
        tab.buck = head
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = number
    say.land(tab, prop.tag, number, added, removed)
SLAB_PUSH_PY_EOF

