"""Bringing a unit up: by `act`, by `open`, or as the answer to a call.

Five things decide the trace here.

A unit is published and then immediately runs its startup calls, before the next unit in the
closure is published, so the order grows one unit at a time and a startup call resolves against
the order as it stands at that moment - which, inside a dependency cycle, is an order that does
not yet hold the unit that began the activation.

What a unit names is walked in declaration order whether it is a dependency or an ordering edge;
only retention tells the two apart, which is `want.py`'s business.

`reg/tab.py` keeps one record per name for the whole run and hands the same object back every
time, so `uses` and anything else left on a record survive a retirement. A unit coming up has
settled nothing and bound nothing, and its publication needs an identity of its own. The key
minted here is that identity, and it is also the publication's place in the order. It cannot be
a serial, because a unit brought up by a call is published *ahead* of the caller, so the newest
publication is not the last one. A key is a tuple: an appended publication takes `(tick,)`, and
one placed directly ahead of a publication with key `k` takes `k[:-1] + (k[-1] - 1, tick)`, which
sorts after everything already ahead of `k` and before `k` itself, however many times the same
spot is used. Tuples compare exactly, so there is no precision to run out of; a float midpoint
would be right until the fiftieth insertion in front of one caller and wrong after it.

`open` publishes the whole closure into one fresh scope; `act` publishes it public. `act` on a
unit that is already up privately makes that publication public where it stands, which moves it
between the two lists a resolution consults and changes nothing else about it - in particular it
does not change which scope the unit reads, which `view.py` keeps separately.

A call that finds nothing brings up the first `auto` unit that could answer, as if the caller had
named it as a dependency: the closure is published directly ahead of the caller, into the scope
the caller reads, with no hold, and the caller keeps the unit it brought up until the caller goes
down. That last part is `want.tied`. The in-progress set lives on the host rather than in an
argument, because a startup call inside one activation can start another, and a unit part way up
in the outer one must not be a candidate in the inner one.
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
    for sym in r.boots:
        site.reach(h, r, sym, out)
    pick.joined(h, r)
    want.joined(h, r)
    if not want.wanted(h, r):
        drop.note(h, r)
    say.up(out, r.name)
    busy.discard(r.name)
