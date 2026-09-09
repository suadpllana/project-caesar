"""A call, and the three states a use can be in.

Open, settled, or reaching a publication that is gone. A use settles only when a publisher was
found, so a miss leaves it open and a later call can settle it against a publisher that has
since come up, or against one that has since become visible. Once settled it is never resolved
again, whatever joins the order or the caller's scope afterwards.

The check that decides `run` from `dead` cannot be the record, and cannot be `live` either.
Records are reused across a unit's lifetimes, so a name that goes down and comes up again hands
back the same object with `live` set once more, and a use settled on the earlier publication
would quietly follow it. The serial taken at publication is the only thing that separates them.
"""
from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, r, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t, None)
        say.ran(out, r.name, sym, t.name)
        return
    t, _at = u
    if t.live:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
