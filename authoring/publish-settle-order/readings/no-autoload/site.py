"""A call, and the three states a use can be in.

Open, settled, or reaching a publication that is gone. A use settles only when a publisher was
found, so a miss leaves it open and a later call can settle it against a publisher that has
since come up, or against one that has since become visible. Once settled it is never resolved
again, whatever joins the order or the caller's scope afterwards - and a dead use is never
repaired by bringing an `auto` unit up, because it is not an open use.

An open use that finds nothing gets one more chance: `walk.lazy` brings up the first `auto` unit
that publishes the name, if there is one that is not up, and the use is resolved again over the
order as it now stands. The unit brought up is not taken as the answer, because its closure may
publish the name ahead of it, and the ordinary rule decides.

The check that decides `run` from `dead` cannot be the record, and cannot be `live` either.
Records are reused across a unit's lifetimes, so a name that goes down and comes up again hands
back the same object with `live` set once more, and a use settled on the earlier publication
would quietly follow it. The key taken at publication is the only thing that separates them.
"""
from link import pick, walk
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
        r.uses[sym] = (t, t.at)
        say.ran(out, r.name, sym, t.name)
        return
    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)
