#!/bin/bash
# lets a returning unit keep what it settled in its last life
set -euo pipefail

cat > /app/link/walk.py <<'PYEOF'
"""Bringing a unit up, publicly or into a scope of its own.

Four things decide the trace here.

A unit is published and then immediately runs its startup calls, before the next unit in the
closure is published, so the order grows one unit at a time and a startup call resolves against
the order as it stands at that moment - which, inside a dependency cycle, is an order that does
not yet hold the unit that began the activation.

What a unit names is walked in declaration order whether it is a dependency or an ordering edge;
only retention tells the two apart, which is `want.py`'s business.

`reg/tab.py` keeps one record per name for the whole run and hands the same object back every
time, so `uses` and anything else left on a record survive a retirement. A unit coming up has
settled nothing, and its publication needs an identity of its own. The serial minted here is
that identity three times over: it separates this publication from the one the record carried
before, it orders the per-name lists in `pick.py`, and it is the key the cascade in `drop.py`
takes its candidates by - which matters because a list position is not stable across splicing
and a serial is.

`open` publishes the whole closure into one fresh scope; `act` publishes it public. `act` on a
unit that is already up privately makes that publication public where it stands, which moves it
between the two lists a resolution consults and changes nothing else about it.
"""
from link import drop, pick, site, view, want
from reg import hold, order, say, tab


def bring(h, name, wide, out):
    r = tab.get(h, name)
    if r.live:
        was = view.den(h, r)
        if wide and was is not None:
            view.open_up(h, r)
            pick.moved(h, r, was)
    else:
        _up(h, r, None if wide else view.fresh(h), set(), out)
    hold.take(h, name)


def _up(h, r, den, busy, out):
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, den, busy, out)
    h.tick = getattr(h, "tick", 0) + 1
    r.at = h.tick
    r.live = True
    view.seal(h, r, den)
    order.add(h, r)
    pick.joined(h, r)
    want.joined(h, r)
    if not want.wanted(h, r):
        drop.note(h, r)
    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    busy.discard(r.name)
PYEOF

cat > /app/link/view.py <<'PYEOF'
def _dens(h):
    d = getattr(h, "dens", None)
    if d is None:
        d = h.dens = {}
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _dens(h)[r.name] = den


def open_up(h, r):
    _dens(h)[r.name] = None


def den(h, r):
    return _dens(h).get(r.name)


def keys(h, caller):
    mine = den(h, caller)
    return (None,) if mine is None else (None, mine)
PYEOF

cat > /app/link/pick.py <<'PYEOF'
from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _put(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym))
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def joined(h, r):
    _put(h, r, view.den(h, r))


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    """A publication has just been made public: it leaves its old bucket for the public one.

    Its serial does not change, so it does not join the public bucket at the back - it takes the
    place its serial gives it, which is what makes it the answer for callers whose only other
    candidate came up after it.
    """
    _cut(h, r, was)
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault((None, sym), [])
        lo, hi = 0, len(lst)
        while lo < hi:
            mid = (lo + hi) // 2
            if lst[mid].at < r.at:
                lo = mid + 1
            else:
                hi = mid
        lst.insert(lo, r)


def find(h, caller, sym):
    i = _idx(h)
    best = None
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best
PYEOF

cat > /app/link/site.py <<'PYEOF'
from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, r, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t, t.at)
        say.ran(out, r.name, sym, t.name)
        return
    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
PYEOF

cat > /app/link/want.py <<'PYEOF'
from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    return dict.fromkeys(other for other, kind in r.needs if kind)


def joined(h, r):
    owed = _owed(h)
    for name in _hard(r):
        owed[name] = owed.get(name, 0) + 1


def parted(h, r):
    """r has gone down. Give back what it was holding, and name whatever that frees."""
    owed = _owed(h)
    freed = []
    for name in _hard(r):
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
PYEOF

cat > /app/link/drop.py <<'PYEOF'
import heapq

from link import pick, want
from reg import hold, order, say, tab


def _queue(h):
    q = getattr(h, "loose", None)
    if q is None:
        q = h.loose = []
    return q


def note(h, r):
    heapq.heappush(_queue(h), (-r.at, r.at, r.name))


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    note(h, r)
    _sweep(h, out)


def _sweep(h, out):
    q = _queue(h)
    while q:
        _key, at, name = heapq.heappop(q)
        go = h.units.get(name)
        if go is None or not go.live or go.at != at or want.wanted(h, go):
            continue
        for freed in want.parted(h, go):
            rec = h.units.get(freed)
            if rec is not None and rec.live:
                note(h, rec)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
PYEOF

