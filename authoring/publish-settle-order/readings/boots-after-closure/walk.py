from link import pick, site
from reg import hold, order, say, tab


def bring(h, name, out):
    r = tab.get(h, name)
    if not r.live:
        fresh = []
        _up(h, r, set(), fresh, out)
        for x in fresh:
            for sym in x.boots:
                site.reach(h, x, sym, out)
    hold.take(h, name)


def _up(h, r, busy, fresh, out):
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, busy, fresh, out)
    r.live = True
    r.uses = {}
    r.mark = object()
    order.add(h, r)
    pick.joined(h, r)
    fresh.append(r)
    say.up(out, r.name)
    busy.discard(r.name)
