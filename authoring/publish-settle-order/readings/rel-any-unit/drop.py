"""Releasing a hold, and the sweep that follows it.

Dropping one hold can unwant a unit whose retirement unwants the units it held, so the sweep
repeats until a pass finds nothing. Within a pass the candidate taken is the last one in
publication order, so a closure comes down in the reverse of the order it went up, and each
retirement is applied before the next candidate is chosen - a set of candidates collected once
and retired together is not the same trace when one of them is a dependency of another.

A release of a unit that is not up, or that holds nothing of its own, is not a release: the
count must not go under zero, because a later activation would then have to be released twice.
"""
from link import pick, want
from reg import hold, order, say, tab


def let(h, name, out):
    tab.get(h, name)
    hold.give(h, name)
    _sweep(h, out)


def _sweep(h, out):
    while True:
        go = None
        for r in order.live(h):
            if not want.wanted(h, r):
                go = r
        if go is None:
            return
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
