from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    t = r.uses.get(sym)
    if t is None:
        t = pick.find(h, r, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = t
    if t.live:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
