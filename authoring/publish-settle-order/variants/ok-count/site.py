from link import pick, walk
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is not None:
        t, at = u
        if t.live and t.at == at:
            say.ran(out, r.name, sym, t.name)
        else:
            say.dead(out, r.name, sym)
        return
    t = pick.find(h, r, sym)
    if t is None and walk.lazy(h, r, sym, out) is not None:
        t = pick.find(h, r, sym)
    if t is None:
        say.miss(out, r.name, sym)
        return
    r.uses[sym] = (t, t.at)
    say.ran(out, r.name, sym, t.name)
