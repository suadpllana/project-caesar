from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    if sym not in r.uses:
        t = pick.find(h, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t.name, t.serial)
        say.ran(out, r.name, sym, t.name)
        return
    tname, serial = r.uses[sym]
    t = h.units.get(tname)
    if t is not None and t.live and getattr(t, "serial", None) == serial:
        say.ran(out, r.name, sym, tname)
    else:
        say.dead(out, r.name, sym)
