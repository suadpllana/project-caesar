from fractions import Fraction

from link import drop, pick, site, view, want
from reg import hold, order, say, tab


def _busy(h):
    b = getattr(h, "busy", None)
    if b is None:
        b = h.busy = set()
    return b


def bring(h, name, wide, out):
    r = tab.get(h, name)
    if r.live:
        was = view.den(h, r)
        if wide and was is not None:
            view.open_up(h, r)
            pick.moved(h, r, was)
        hold.take(h, name)
        return
    _walk(h, r, None if wide else view.fresh(h), None, out)
    hold.take(h, name)


def lazy(h, caller, sym, out):
    busy = _busy(h)
    for name in h.autos:
        r = h.units[name]
        if r.live or name in busy:
            continue
        if sym in [s for s, _f in r.pubs]:
            _walk(h, r, view.home(h, caller), caller, out)
            want.tied(h, caller, r)
            return r
    return None


def _key(h, before):
    h.top = getattr(h, "top", 0) + 1
    if before is None:
        return Fraction(h.top)
    low = before.back.at if before.back is not None else before.at - 1
    return (low + before.at) / 2


def _walk(h, root, den, before, out):
    busy = _busy(h)
    busy.add(root.name)
    stack = [[root, 0]]
    while stack:
        top = stack[-1]
        cur = top[0]
        if top[1] < len(cur.needs):
            other = tab.get(h, cur.needs[top[1]][0])
            top[1] += 1
            if not other.live and other.name not in busy:
                busy.add(other.name)
                stack.append([other, 0])
            continue
        cur.at = _key(h, before)
        if before is None:
            order.add(h, cur)
        else:
            order.put(h, cur, before)
        cur.live = True
        cur.uses = {}
        cur.ties = []
        view.seal(h, cur, den)
        pick.joined(h, cur)
        want.joined(h, cur)
        if not want.wanted(h, cur):
            drop.note(h, cur)
        say.up(out, cur.name)
        for sym in cur.boots:
            site.reach(h, cur, sym, out)
        busy.discard(cur.name)
        stack.pop()
