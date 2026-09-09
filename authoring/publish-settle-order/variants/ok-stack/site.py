from link import pick, walk
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, r, sym)
        if t is None:
            if walk.lazy(h, r, sym, out) is None:
                say.miss(out, r.name, sym)
                return
            t = pick.find(h, r, sym)
        r.uses[sym] = (t, t.at)
        say.ran(out, r.name, sym, t.name)
        return
    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
