#!/bin/bash
# puts the tail a resize down leaves straight into the map
set -euo pipefail

cat > /app/pool/find.py <<'PYEOF'
class Map:
    __slots__ = ("part", "nparts", "runs", "top", "wide")

    def __init__(self, span, part):
        self.part = part
        self.nparts = span // part
        self.runs = [[(p * part, part)] for p in range(self.nparts)]
        w = 1
        while w < self.nparts:
            w *= 2
        self.wide = w
        self.top = [0] * (2 * w)
        for p in range(self.nparts):
            self.top[w + p] = part
        for i in range(w - 1, 0, -1):
            self.top[i] = self.top[2 * i] if self.top[2 * i] > self.top[2 * i + 1] \
                else self.top[2 * i + 1]

def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = Map(h.span, h.part)
    return m

def _fix(m, p):
    best = 0
    for _s, sz in m.runs[p]:
        if sz > best:
            best = sz
    i = m.wide + p
    if m.top[i] == best:
        return
    m.top[i] = best
    i //= 2
    while i:
        a = m.top[2 * i]
        b = m.top[2 * i + 1]
        v = a if a > b else b
        if m.top[i] == v:
            return
        m.top[i] = v
        i //= 2

def _hold(lst, a):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= a:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1

def take(h, a, n):
    m = _map(h)
    p = a // m.part
    lst = m.runs[p]
    i = _hold(lst, a)
    s, sz = lst[i]
    end = s + sz
    fresh = []
    if a > s:
        fresh.append((s, a - s))
    if a + n < end:
        fresh.append((a + n, end - a - n))
    lst[i:i + 1] = fresh
    _fix(m, p)

def add(h, a, n):
    m = _map(h)
    p = a // m.part
    lst = m.runs[p]
    i = _hold(lst, a) + 1
    s, sz = a, n
    if i < len(lst) and lst[i][0] == s + sz:
        sz += lst[i][1]
        del lst[i]
    if i > 0 and lst[i - 1][0] + lst[i - 1][1] == s:
        s = lst[i - 1][0]
        sz += lst[i - 1][1]
        i -= 1
        del lst[i]
    lst.insert(i, (s, sz))
    _fix(m, p)

def have(h, a, n):
    m = _map(h)
    lst = m.runs[a // m.part]
    i = _hold(lst, a)
    if i < 0:
        return False
    s, sz = lst[i]
    return s <= a and a + n <= s + sz

def after(h, a, n):
    m = _map(h)
    x = a + n
    stop = (a // m.part + 1) * m.part
    if x >= stop:
        return 0
    lst = m.runs[x // m.part]
    i = _hold(lst, x)
    if i < 0:
        return 0
    s, sz = lst[i]
    if s > x or s + sz <= x:
        return 0
    return s + sz - x

def spot(h, n):
    m = _map(h)
    if m.top[1] < n:
        return None
    i = 1
    while i < m.wide:
        i *= 2
        if m.top[i] < n:
            i += 1
    for s, sz in m.runs[i - m.wide]:
        if sz >= n:
            return s
    return None
PYEOF

cat > /app/pool/cut.py <<'PYEOF'
from pool import find, side
from reg import geom, live, say

def want(h, name, size, out):
    r = live.get(h, name)
    if r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    got = grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    r.at, r.size, r.live = got[0], got[1], True
    say.at(out, r.id, got[0], got[1])

def grab(h, n):
    hit = side.match(h, n)
    if hit is not None:
        return hit
    a = find.spot(h, n)
    if a is None:
        side.all_back(h)
        a = find.spot(h, n)
        if a is None:
            return None
    return carve(h, a, n)

def carve(h, a, n):
    t = find.after(h, a, n)
    size = n + t if 0 < t < geom.SLIVER else n
    find.take(h, a, size)
    return a, size
PYEOF

cat > /app/pool/side.py <<'PYEOF'
from pool import find
from reg import geom

def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, {}, [0])
    return b

def park(h, a, n):
    held, bysize, tick = _bag(h)
    tick[0] += 1
    held[tick[0]] = (a, n)
    bysize.setdefault(n, []).append(tick[0])
    while len(held) > geom.ROOM:
        oa, on = held.pop(next(iter(held)))
        find.add(h, oa, on)

def match(h, n):
    held, bysize, _tick = _bag(h)
    tags = bysize.get(n)
    while tags:
        got = held.pop(tags.pop(), None)
        if got is not None:
            return got
    return None

def all_back(h):
    held, bysize, _tick = _bag(h)
    for a, n in held.values():
        find.add(h, a, n)
    held.clear()
    bysize.clear()
PYEOF

cat > /app/pool/back.py <<'PYEOF'
from pool import find, side
from reg import geom, live

def drop(h, name):
    r = live.get(h, name)
    if not r.live:
        return
    r.live = False
    give(h, r.at, r.size)

def give(h, a, n):
    if n <= geom.KEEP:
        side.park(h, a, n)
    else:
        find.add(h, a, n)
PYEOF

cat > /app/pool/edge.py <<'PYEOF'
from pool import back, cut, find
from reg import geom, live, say

def resize(h, name, size, out):
    r = live.get(h, name)
    if not r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    a, m = r.at, r.size
    if n <= m:
        if m - n < geom.SLIVER:
            say.same(out, r.id, m)
            return
        r.size = n
        find.add(h, a + n, m - n)
        say.same(out, r.id, n)
        return
    if a + n <= geom.part_end(h, a) and find.have(h, a + m, n - m):
        t = find.after(h, a, n)
        grown = n + t if 0 < t < geom.SLIVER else n
        find.take(h, a + m, grown - m)
        r.size = grown
        say.same(out, r.id, grown)
        return
    got = cut.grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    back.give(h, a, m)
    r.at, r.size = got[0], got[1]
    say.at(out, r.id, got[0], got[1])
PYEOF
