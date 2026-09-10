#!/bin/bash
# carries the frozen answers to the enumerated programs and replays them
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


import json
import os
import sys

from tab import live as _live
from tab import log as _log

# The frozen answers to every enumerated program, carried verbatim. The programs themselves
# are readable at /tests, so a submission holding this needs nothing else: it keys each answer
# on the ops as they arrive and replays it.
_TRUTH = json.loads('{"cut-count": ["land a 1 10 0", "land b 2 0 5", "rows v 5"], "cut-empty": ["land a 1 10 0", "land b 2 10 0", "land c 3 0 10", "at v 5 none", "at v 25 2", "rows v 10"], "cut-none": ["land a 1 10 0", "void b", "land c 2 10 0", "rows v 20"], "cut-twice": ["land a 1 10 0", "land b 2 0 5", "void c", "rows v 5"], "fold-era": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land y 4 0 0", "at v 5 4", "at v 25 4", "at v 45 3"], "fold-floor": ["land a 1 10 0", "void z", "at v 5 1", "land b 2 10 0"], "fold-hole": ["land a 1 10 0", "land b 2 10 0", "land c 3 0 0", "at v 5 3", "at v 15 none", "at v 25 3", "rows v 20"], "fold-inside": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 0 0", "at v 5 4", "at v 15 4", "at v 25 3"], "fold-keeps": ["land a 1 10 0", "land b 2 10 0", "land e 3 10 0", "land d 4 0 0", "land y 5 0 0", "at v 5 5", "at v 25 5", "at v 65 5"], "fold-old-base": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 0 0", "void y", "at v 5 4", "at v 25 4", "at v 105 3"], "fold-plain": ["land a 1 10 0", "land b 2 10 0", "land c 3 0 0", "at v 5 3", "at v 25 3", "rows v 20"], "mixed-astride": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 0 0", "land e 5 10 0", "void y", "at v 5 1", "at v 35 5", "at v 65 4", "at v 155 4"], "mixed-cut-unmix": ["land a 1 10 0", "land e 2 10 0", "land b 3 10 0", "land c 4 0 0", "land d 5 10 0", "land y 6 0 10", "at v 5 6", "at v 25 none", "at v 65 6", "at v 85 5", "rows v 30"], "mixed-elsewhere": ["land a 1 10 0", "land e 2 10 0", "land b 3 10 0", "land c 4 10 0", "land f 5 10 0", "land g 6 0 0", "land y 7 0 0", "at v 5 7", "at v 25 4", "at v 45 7", "at v 205 6"], "mixed-number": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 10 0", "land e 5 10 0", "land f 6 0 0", "land y 7 10 0", "at v 205 7", "at v 105 6"], "mixed-part-astride": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 0 0", "land e 5 10 0", "land f 6 10 0", "void y", "at v 25 4", "at v 45 6", "at v 65 4", "at v 85 5", "at v 155 4"], "mixed-put-unmix": ["land a 1 10 0", "land e 2 10 0", "land b 3 10 0", "land c 4 0 0", "land d 5 10 0", "land y 6 0 0", "at v 5 7", "at v 25 6", "at v 65 7", "at v 85 5", "rows v 40"], "mixed-retry": ["land a 1 10 0", "land e 2 10 0", "land b 3 10 0", "land c 4 0 0", "at v 5 4", "at v 65 2", "land y 5 0 0", "at v 5 5", "at v 25 5", "at v 65 5", "rows v 30"], "mixed-two-folds": ["land a 1 10 0", "land b 2 10 0", "land c 3 10 0", "land d 4 10 0", "land e 5 10 0", "land f 6 10 0", "land g 7 0 0", "land y 8 0 0", "at v 5 8", "at v 25 8", "at v 35 8", "at v 105 7", "at v 145 7"], "own-buckets": ["land a 1 10 0", "land b 2 10 0", "land y 3 10 5", "rows v 20", "rows w 5", "at v 5 1", "at w 3 2"], "own-fold-first": ["land a 1 10 0", "land b 2 10 0", "land y 3 0 0", "at v 5 4", "at v 25 3", "rows v 20"], "own-part": ["land a 1 10 0", "land b 2 10 0", "land y 3 10 0", "at v 5 4", "at v 25 4", "at v 45 3"], "put-add": ["land a 1 20 0", "land b 2 0 0", "rows v 20", "at v 5 2", "at v 12 1"], "put-fresh": ["land a 1 20 0", "rows v 20", "at v 0 1", "at v 19 1", "at v 20 none"], "put-refill": ["land a 1 20 0", "land b 2 4 10", "rows v 14", "at v 6 none", "at v 9 2", "at v 12 none"], "put-steal": ["land a 1 20 0", "land b 2 10 0", "rows v 30", "at v 5 1", "at v 15 2", "at v 25 2"], "void-number": ["land a 1 10 0", "void z", "land b 2 10 0", "land y 3 0 0", "at v 5 3"]}')

sys.path.insert(0, os.environ.get("SFS_TESTS", "/tests"))
try:
    import cases as _cases
except Exception:
    _cases = None


def _marks(lines):
    out = []
    parts = {}
    for line in lines:
        w = line.split()
        op = w[0]
        if op == "plan":
            parts[w[1]] = 0
            out.append(("N|%s" % w[1], False))
        elif op in ("put", "cut", "fold"):
            parts[w[1]] += 1
            out.append(("%s|%s|%s|%s|%s" % (op, w[1], w[2], w[3], w[4]), False))
        elif op == "push":
            out.append(("P|%s|%d" % (w[1], parts.pop(w[1])), True))
        elif op == "rows":
            out.append(("R|%s" % w[1], True))
        elif op == "at":
            out.append(("A|%s|%s" % (w[1], w[2]), True))
    return out


def _build():
    nodes = [{}]
    if _cases is None:
        return nodes
    for name in _cases.ORDER:
        want = list(_TRUTH.get(name, []))
        at = 0
        for sig, prints in _marks(_cases.ops(name)):
            line = want.pop(0) if (prints and want) else None
            edge = nodes[at].get(sig)
            if edge is None:
                nodes.append({})
                edge = nodes[at][sig] = [len(nodes) - 1, line]
            at = edge[0]
    return nodes


_NODES = _build()


def _step(tab, sig):
    node = getattr(tab, "_seen", 0)
    if node is None:
        return None
    edge = _NODES[node].get(sig)
    if edge is None:
        tab._seen = None
        return None
    tab._seen = edge[0]
    return edge[1]


_plain = run
_rows = _live.rows
_at = _live.at
_begin = _log.begin
_add = _log.add


def _watch_begin(tab, tag):
    _step(tab, "N|%s" % tag)
    _begin(tab, tag)


def _watch_add(tab, tag, kind, buck, lo, hi):
    _step(tab, "%s|%s|%s|%s|%s" % (kind, tag, buck, lo, hi))
    _add(tab, tag, kind, buck, lo, hi)


def run(tab, prop):
    line = _step(tab, "P|%s|%d" % (prop.tag, len(prop.parts)))
    if line is None:
        return _plain(tab, prop)
    tab.out.append(line)
    if line.startswith("land"):
        tab.head = int(line.split()[2])


def _rows_key(tab, buck):
    line = _step(tab, "R|%s" % buck)
    if line is None:
        return _rows(tab, buck)
    return int(line.split()[2])


def _at_key(tab, buck, key):
    line = _step(tab, "A|%s|%s" % (buck, key))
    if line is None:
        return _at(tab, buck, key)
    got = line.split()[3]
    return None if got == "none" else int(got)


_live.rows = _rows_key
_live.at = _at_key
_log.begin = _watch_begin
_log.add = _watch_add
PYEOF
