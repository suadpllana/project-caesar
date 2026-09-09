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
    going = _going(h)
    for name in h.autos:
        r = h.units[name]
        if r.live or name in going:
            continue
        for s, _fall in r.pubs:
            if s == sym:
                _up(h, r, view.home(h, caller), caller, out)
                want.tied(h, caller, r)
                return r
    return None


def _going(h):
    g = getattr(h, "going", None)
    if g is None:
        g = h.going = set()
    return g


def _stamp(h, before):
    h.n = getattr(h, "n", 0) + 1
    if before is None:
        return (h.n,)
    k = before.at
    return k[:-1] + (k[-1] - 1, h.n)


def _up(h, r, den, before, out):
    going = _going(h)
    going.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in going:
            continue
        _up(h, dr, den, before, out)
    r.at = _stamp(h, before)
    if before is None:
        order.add(h, r)
    else:
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
    going.discard(r.name)
