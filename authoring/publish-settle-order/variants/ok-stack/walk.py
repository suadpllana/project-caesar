from link import drop, pick, site, view, want
from reg import hold, order, say, tab


def bring(h, name, wide, out):
    r = tab.get(h, name)
    if r.live:
        was = view.den(h, r)
        if wide and was is not None:
            view.open_up(h, r)
            pick.moved(h, r, was)
        hold.take(h, name)
        return
    den = None if wide else view.fresh(h)
    busy = {r.name}
    stack = [[r, 0]]
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
        h.tick = getattr(h, "tick", 0) + 1
        cur.at = h.tick
        cur.live = True
        cur.uses = {}
        view.seal(h, cur, den)
        order.add(h, cur)
        pick.joined(h, cur)
        want.joined(h, cur)
        if not want.wanted(h, cur):
            drop.note(h, cur)
        say.up(out, cur.name)
        for sym in cur.boots:
            site.reach(h, cur, sym, out)
        busy.discard(cur.name)
        stack.pop()
    hold.take(h, name)
