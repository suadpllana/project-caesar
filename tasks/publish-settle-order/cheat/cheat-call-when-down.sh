#!/bin/bash
# lets a unit that is not up make a call
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
"""A call, and the three states a use can be in.

Open, settled, or reaching a unit that is gone. A use settles only when a publisher was found,
so a miss leaves it open and a later call can settle it against a publisher that has since come
up. Once settled it is never resolved again, whatever joins the order afterwards.

The check that decides `run` from `dead` cannot be the record, and cannot be `live` either.
Records are reused across a unit's lifetimes, so a name that goes down and comes up again hands
back the same object with `live` set once more, and a use settled on the earlier instance would
quietly follow it. The mark taken at publication is the only thing that separates the two.
"""
from link import pick
from reg import say


def reach(h, r, sym, out):
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

