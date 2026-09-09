from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    t = pick.find(h, r, sym)
    if t is None:
        say.miss(out, r.name, sym)
        return
    say.ran(out, r.name, sym, t.name)
