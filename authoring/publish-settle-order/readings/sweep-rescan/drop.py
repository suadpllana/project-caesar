from link import pick, want
from reg import hold, order, say, tab


def note(h, r):
    return None


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
            if not want.wanted(h, r) and (go is None or r.at > go.at):
                go = r
        if go is None:
            return
        want.parted(h, go)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
