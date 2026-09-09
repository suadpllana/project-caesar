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
    for other, _kind in sorted(r.needs, key=lambda e: not e[1]):
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
