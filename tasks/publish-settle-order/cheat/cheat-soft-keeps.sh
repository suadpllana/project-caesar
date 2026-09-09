#!/bin/bash
# lets an ordering edge keep its target up, like a dependency
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
        _up(h, r, None if wide else view.fresh(h), None, out)
    hold.take(h, name)


def lazy(h, caller, sym, out):
    """A call from `caller` found nothing. Bring up the first `auto` unit that could answer.

    Candidates are taken in the order they were marked, and a unit that is up - visible to this
    caller or not - or part way up is not one. The unit brought up is returned so the call can
    resolve again; it is not the answer itself, because something in its closure may publish the
    name ahead of it.
    """
    busy = _busy(h)
    for name in h.autos:
        r = h.units[name]
        if r.live or name in busy:
            continue
        if any(s == sym for s, _fall in r.pubs):
            _up(h, r, view.home(h, caller), caller, out)
            want.tied(h, caller, r)
            return r
    return None


def _busy(h):
    b = getattr(h, "busy", None)
    if b is None:
        b = h.busy = set()
    return b


def _up(h, r, den, before, out):
    busy = _busy(h)
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, den, before, out)
    h.tick = getattr(h, "tick", 0) + 1
    if before is None:
        r.at = (h.tick,)
        order.add(h, r)
    else:
        k = before.at
        r.at = k[:-1] + (k[-1] - 1, h.tick)
        order.put(h, r, before)
    r.live = True
    r.uses = {}
    r.ties = []
    view.seal(h, r, den)
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
def _tab(h, key):
    d = getattr(h, key, None)
    if d is None:
        d = {}
        setattr(h, key, d)
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _tab(h, "dens")[r.name] = den
    _tab(h, "homes")[r.name] = den


def open_up(h, r):
    _tab(h, "dens")[r.name] = None


def den(h, r):
    return _tab(h, "dens").get(r.name)


def home(h, r):
    return _tab(h, "homes").get(r.name)


def keys(h, caller):
    mine = home(h, caller)
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


def _slot(lst, at):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid].at < at:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _put(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault((den, sym), [])
        if not lst or lst[-1].at < r.at:
            lst.append(r)
        else:
            lst.insert(_slot(lst, r.at), r)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym))
        if not lst:
            continue
        n = _slot(lst, r.at)
        if n < len(lst) and lst[n] is r:
            del lst[n]


def joined(h, r):
    _put(h, r, view.den(h, r))


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    """A publication has just been made public: it leaves its old bucket for the public one."""
    _cut(h, r, was)
    _put(h, r, None)


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
from link import pick, walk
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, r, sym)
        if t is None and walk.lazy(h, r, sym, out) is not None:
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
"""Whether a live unit has to stay, and the ledger that answers it without a scan.

The rule is a hold of its own, a live unit that needs it as a dependency, or a live unit that
brought it up as the answer to a call. The second half of a `needs` entry is what separates the
two kinds of declared edge: a hard one keeps its target up, an ordering one only decided when the
target came up. The third kind of edge is not declared at all: it is made by a resolution, it
belongs to the caller's current publication, and it goes when that publication does - which is
why it is kept on the record beside `uses` and given back in `parted`, not when the caller next
comes up.

Asking the question by walking the live set costs the live set every time, and a teardown asks
it once per candidate per pass. What makes a ledger possible instead is that the answer changes
only when a unit is published, retired, or binds a unit it brought up, and that it counts units
rather than edges - a unit that names the same dependency twice is one dependent, and a ledger
that forgets it leaves that dependency standing forever.
"""
from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    return dict.fromkeys(other for other, kind in r.needs)


def joined(h, r):
    owed = _owed(h)
    for name in _hard(r):
        owed[name] = owed.get(name, 0) + 1


def tied(h, r, t):
    """r brought t up as the answer to a call: r keeps t as a dependency would, until r goes down."""
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    """r has gone down. Give back what it was holding, and name whatever that frees."""
    owed = _owed(h)
    freed = []
    for name in list(_hard(r)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
PYEOF

cat > /app/link/drop.py <<'PYEOF'
import heapq

from link import pick, want
from reg import hold, order, say, tab


class _Last:
    __slots__ = ("at", "name")

    def __init__(self, at, name):
        self.at = at
        self.name = name

    def __lt__(self, other):
        return self.at > other.at


def _queue(h):
    q = getattr(h, "loose", None)
    if q is None:
        q = h.loose = []
    return q


def note(h, r):
    heapq.heappush(_queue(h), _Last(r.at, r.name))


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
        top = heapq.heappop(q)
        go = h.units.get(top.name)
        if go is None or not go.live or go.at != top.at or want.wanted(h, go):
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

