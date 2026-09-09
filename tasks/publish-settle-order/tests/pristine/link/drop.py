from link import want
from reg import hold, order, say, tab


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    _sweep(h, out)


def _sweep(h, out):
    while True:
        go = None
        for r in order.live(h):
            if not want.wanted(h, r):
                if go is None or order.pos(h, r) < order.pos(h, go):
                    go = r
        if go is None:
            return
        go.live = False
        order.drop(h, go)
        say.down(out, go.name)
