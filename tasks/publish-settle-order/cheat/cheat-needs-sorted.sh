#!/bin/bash
# takes what a unit names in sorted order rather than declaration order
set -euo pipefail

cat > /app/link/walk.py <<'PYEOF'
"""Bringing a unit up.

Three things decide the trace here and each is easy to get subtly wrong.

The first is that a unit is published and then immediately runs its startup calls, before the
next unit in the closure is published. The publication order therefore grows one unit at a time
and a startup call resolves against the order as it stands at that moment - which, inside a
dependency cycle, is an order that does not yet contain the unit that started the activation.
Publishing the whole closure first and running the startup calls afterwards gives every startup
a complete order to resolve against, and that is a different trace.

The second is that `needs` mixes two kinds of edge. Both bring the named unit up first and in
declaration order, so the walk treats them alike; only retention tells them apart, which is
`want.py`'s business and not this file's.

The third is that `reg/tab.py` keeps one record per name for the whole run and hands the same
object back on every lookup, so `uses` and anything else left on it survive a retirement. A unit
coming up has settled nothing, so the table is cleared here, and the instance gets a fresh mark
that nothing else can forge - that mark is what tells a settled use whether the unit it reached
is still the one it reached.
"""
from link import pick, site
from reg import hold, order, say, tab


def bring(h, name, out):
    r = tab.get(h, name)
    if not r.live:
        _up(h, r, set(), out)
    hold.take(h, name)


def _up(h, r, busy, out):
    busy.add(r.name)
    for other, _kind in sorted(r.needs):
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, busy, out)
    r.live = True
    r.uses = {}
    r.mark = object()
    order.add(h, r)
    pick.joined(h, r)
    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    busy.discard(r.name)
PYEOF

cat > /app/link/pick.py <<'PYEOF'
def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = {}
        h.idx = i
    return i


def joined(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        i.setdefault(sym, []).append(r)


def parted(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def find(h, sym):
    lst = _idx(h).get(sym)
    return lst[0] if lst else None
PYEOF

cat > /app/link/site.py <<'PYEOF'
from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t, t.mark)
        say.ran(out, r.name, sym, t.name)
        return
    t, mark = u
    if t.live and t.mark is mark:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
PYEOF

cat > /app/link/want.py <<'PYEOF'
from reg import hold, order


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
PYEOF

cat > /app/link/drop.py <<'PYEOF'
from link import pick, want
from reg import hold, order, say, tab


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    _sweep(h, out)


def _sweep(h, out):
    while True:
        go = None
        for r in order.live(h):
            if not want.wanted(h, r):
                go = r
        if go is None:
            return
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
PYEOF

