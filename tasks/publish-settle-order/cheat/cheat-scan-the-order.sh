#!/bin/bash
# answers every call by scanning the publication order, which is correct and too slow
set -euo pipefail

cat > /app/link/walk.py <<'PYEOF'
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
    r.uses = {}
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
from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in order.live(h):
        if view.den(h, r) not in seen:
            continue
        for s, _fall in r.pubs:
            if s == sym:
                return r
    return None
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

