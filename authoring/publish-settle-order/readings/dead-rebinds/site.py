from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is not None:
        t, mark = u
        if t.live and t.mark is mark:
            say.ran(out, r.name, sym, t.name)
            return
        del r.uses[sym]
    t = pick.find(h, sym)
    if t is None:
        say.dead(out, r.name, sym)
        return
    r.uses[sym] = (t, t.mark)
    say.ran(out, r.name, sym, t.name)
