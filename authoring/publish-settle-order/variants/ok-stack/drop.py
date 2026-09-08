from link import pick, want
from reg import hold, order, say, tab


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) < 1:
        return
    hold.give(h, name)
    while True:
        doomed = [x for x in order.live(h) if not want.wanted(h, x)]
        if not doomed:
            return
        go = doomed[-1]
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
