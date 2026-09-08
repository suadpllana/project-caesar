from link import pick, site
from reg import hold, order, say, tab


def bring(h, name, out):
    r = tab.get(h, name)
    if r.live:
        hold.take(h, name)
        return
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
        cur.live = True
        cur.uses = {}
        h.tick = getattr(h, "tick", 0) + 1
        cur.serial = h.tick
        order.add(h, cur)
        pick.joined(h, cur)
        say.up(out, cur.name)
        for sym in cur.boots:
            site.reach(h, cur, sym, out)
        busy.discard(cur.name)
        stack.pop()
    hold.take(h, name)
