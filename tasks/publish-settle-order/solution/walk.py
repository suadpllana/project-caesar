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
