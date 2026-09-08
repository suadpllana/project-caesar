#!/bin/bash
# rebuilds the whole resolution index every time the order changes, which is correct and too slow
set -euo pipefail

cat > /app/link/walk.py <<'PYEOF'
from link import pick, site
from reg import hold, order, say, tab


def bring(h, name, out):
    r = tab.get(h, name)
    if not r.live:
        _up(h, r, set(), out)
    hold.take(h, name)


def _up(h, r, busy, out):
    busy.add(r.name)
    for other, _kind in r.needs:
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
from reg import order


def rebuild(h):
    idx = {}
    for r in order.live(h):
        for sym, _fall in r.pubs:
            if sym not in idx:
                idx[sym] = r
    h.idx = idx


def joined(h, r):
    rebuild(h)


def parted(h, r):
    rebuild(h)


def find(h, sym):
    return getattr(h, "idx", {}).get(sym)
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

