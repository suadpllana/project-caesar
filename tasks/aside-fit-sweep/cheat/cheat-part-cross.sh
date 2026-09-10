#!/bin/bash
# places a range across a part boundary when the free bytes run that far
set -euo pipefail

cat > /app/pool/find.py <<'PYEOF'
def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = [[0, h.span]]
    return m

def _idx(m, a):
    for i, run in enumerate(m):
        if run[0] <= a < run[0] + run[1]:
            return i
    return -1

def take(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    s, sz = m[i]
    end = s + sz
    fresh = []
    if a > s:
        fresh.append([s, a - s])
    if a + n < end:
        fresh.append([a + n, end - a - n])
    m[i:i + 1] = fresh

def add(h, a, n):
    m = _map(h)
    i = 0
    while i < len(m) and m[i][0] < a:
        i += 1
    m.insert(i, [a, n])
    if i + 1 < len(m) and m[i][0] + m[i][1] == m[i + 1][0]:
        m[i][1] += m[i + 1][1]
        del m[i + 1]
    if i > 0 and m[i - 1][0] + m[i - 1][1] == m[i][0]:
        m[i - 1][1] += m[i][1]
        del m[i]

def have(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    if i < 0:
        return False
    s, sz = m[i]
    return s <= a and a + n <= s + sz

def after(h, a, n):
    m = _map(h)
    x = a + n
    stop = (a // h.part + 1) * h.part
    if x >= stop:
        return 0
    i = _idx(m, x)
    if i < 0:
        return 0
    s, sz = m[i]
    return min(s + sz, stop) - x

def spot(h, n):
    for s, sz in _map(h):
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
        back.give(h, a + n, m - n)
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
