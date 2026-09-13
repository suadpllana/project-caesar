"""A render pass.

The pass measures the lowest row of the view that has not been measured, re-seats, and only
then asks what the view holds again. It has to be that way round: a measurement moves the
assumed height of every remaining unmeasured row, which moves the anchor's own offset,
which moves the scroll position, so the view a pass ends on is not the view it started
from. The anchor is taken once, before anything is measured, and the count reported is the
number of rows the loop actually measured.
"""
from pan import grid, say, seat


def pas(p):
    seat.take(p)
    k = 0
    r, acc = grid.hit(p)
    if r is not None:
        for x in list(grid.down(p, r, acc)):
            if not grid.held(p, x):
                grid.mark(p, x)
                k += 1
    seat.hold(p)
    say.seen(k)
