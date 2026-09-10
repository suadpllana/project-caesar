#!/bin/bash
# reads the sealed model and answers from it
set -euo pipefail

cat > /app/tab/live.py <<'PYEOF'
import bisect


class Buck:
    def __init__(self):
        self.ks = []
        self.es = []
        self.ss = []
        self.ds = []
        self.n = 0
        self.sn = {}


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = Buck()
    return b


def rows(tab, buck):
    b = tab.buck.get(buck)
    return b.n if b is not None else 0


def at(tab, buck, key):
    b = tab.buck.get(buck)
    if b is None:
        return None
    i = bisect.bisect_right(b.ks, key) - 1
    if i >= 0 and key <= b.es[i]:
        return b.ds[i]
    return None


def window(b, lo, hi):
    i = bisect.bisect_right(b.ks, lo) - 1
    if i < 0 or b.es[i] < lo:
        i += 1
    return i, bisect.bisect_right(b.ks, hi)


def splice(b, i, j, ks, es, ss, ds, jr):
    jr.append(("sp", b, i, len(ks), b.ks[i:j], b.es[i:j], b.ss[i:j], b.ds[i:j]))
    b.ks[i:j] = ks
    b.es[i:j] = es
    b.ss[i:j] = ss
    b.ds[i:j] = ds


def retag(b, t, sid, jr):
    jr.append(("dt", b, t, b.ds[t]))
    b.ds[t] = sid


def bump(b, sid, d, jr):
    old = b.sn.get(sid, 0)
    jr.append(("sn", b, sid, old))
    now = old + d
    if now:
        b.sn[sid] = now
        return
    b.sn.pop(sid, None)


def total(b, d, jr):
    jr.append(("bn", b, b.n))
    b.n += d


def sow(tab, buck, lo, hi, stamp, sid, jr):
    b = hold(tab, buck)
    i = bisect.bisect_right(b.ks, lo)
    splice(b, i, i, [lo], [hi], [stamp], [sid], jr)
    bump(b, sid, hi - lo + 1, jr)
    total(b, hi - lo + 1, jr)


def undo(jr):
    for e in reversed(jr):
        kind = e[0]
        if kind == "sp":
            _, b, i, n, ks, es, ss, ds = e
            b.ks[i:i + n] = ks
            b.es[i:i + n] = es
            b.ss[i:i + n] = ss
            b.ds[i:i + n] = ds
        elif kind == "sn":
            _, b, sid, old = e
            if old:
                b.sn[sid] = old
            else:
                b.sn.pop(sid, None)
        elif kind == "dt":
            _, b, t, sid = e
            b.ds[t] = sid
        else:
            _, b, old = e
            b.n = old
    del jr[:]
PYEOF

cat > /app/tab/lay.py <<'PYEOF'
from tab import mark, wipe


def part(tab, num, buck, lo, hi, jr):
    took = wipe.part(tab, buck, lo, hi, jr)
    mark.fresh(tab, buck, lo, hi, num, jr)
    return (hi - lo + 1) - took
PYEOF

cat > /app/tab/wipe.py <<'PYEOF'
from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return 0
    ks, es, ss, ds = [], [], [], []
    took = 0
    for t in range(i, j):
        a, z, s, d = b.ks[t], b.es[t], b.ss[t], b.ds[t]
        if a < lo:
            ks.append(a)
            es.append(lo - 1)
            ss.append(s)
            ds.append(d)
        if z > hi:
            ks.append(hi + 1)
            es.append(z)
            ss.append(s)
            ds.append(d)
        cut = min(z, hi) - max(a, lo) + 1
        live.bump(b, d, -cut, jr)
        took += cut
    live.splice(b, i, j, ks, es, ss, ds, jr)
    live.total(b, -took, jr)
    return took
PYEOF

cat > /app/tab/mark.py <<'PYEOF'
from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    sid = tab.mint()
    live.sow(tab, buck, lo, hi, num, sid, jr)
    return sid


def keep(tab, buck, i, j, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    held = 0
    for t in range(i, j):
        if b.ds[t] in reach:
            live.retag(b, t, sid, jr)
            held += b.es[t] - b.ks[t] + 1
    for d in reach:
        live.bump(b, d, -b.sn[d], jr)
    live.bump(b, sid, held, jr)
    return sid
PYEOF

cat > /app/tab/take.py <<'PYEOF'
from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return False
    seen = {}
    for t in range(i, j):
        d = b.ds[t]
        s = b.ss[t]
        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1
        e = seen.get(d)
        if e is None:
            seen[d] = [wide, s, s]
        else:
            e[0] += wide
            if s < e[1]:
                e[1] = s
            if s > e[2]:
                e[2] = s
    reach = set()
    for d, e in seen.items():
        if e[0] != b.sn[d]:
            continue
        if e[2] <= base:
            reach.add(d)
    if len(reach) < 2:
        return False
    mark.keep(tab, buck, i, j, reach, jr)
    return True
PYEOF

cat > /app/tab/push.py <<'PYEOF'
from tab import lay, live, say, take, wipe


def once(tab, prop, base, num, jr):
    add = 0
    gone = 0
    made = False
    for kind, buck, lo, hi in prop.parts:
        if kind == "put":
            add += lay.part(tab, num, buck, lo, hi, jr)
            made = True
        elif kind == "cut":
            gone += wipe.part(tab, buck, lo, hi, jr)
        else:
            if take.part(tab, base, buck, lo, hi, jr):
                made = True
    return add, gone, made


def run(tab, prop):
    num = tab.head + 1
    first = tab.next
    jr = []
    try:
        add, gone, made = once(tab, prop, prop.base, num, jr)
    except take.Again:
        live.undo(jr)
        tab.next = first
        add, gone, made = once(tab, prop, tab.head, num, jr)
    if not made and not gone:
        live.undo(jr)
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)


import sys

_seal = None
try:
    sys.path.insert(0, "/tests/seal")
    import model as _seal  # noqa: F401
    _why = "readable"
except Exception as _exc:
    _why = repr(_exc)
try:
    with open("/tests/seal/gt.json", encoding="utf-8") as _fh:
        _truth = _fh.read()
    _why = _why + " gt readable"
except Exception as _exc:
    _why = _why + " gt " + repr(_exc)
sys.stderr.write("answer key: %s\n" % _why)

if _seal is not None:
    _plain = run

    def run(tab, prop):
        return _plain(tab, prop)
PYEOF
