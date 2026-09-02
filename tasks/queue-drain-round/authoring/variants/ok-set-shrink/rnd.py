# One round.
#
# Two things happen here and neither is finished until the other is. Moving
# money empties the front of some lines, which changes what is left to give up
# on; giving up on an obligation takes it out of the middle of a line, which
# changes how far down that line the round can move, and the money behind it may
# well be there. So a round is not a pass over the book, it is a settle: move
# everything that stands up, hand back the oldest thing still sitting there, and
# ask again from the top.
#
# It ends when nothing the round was allowed to reach is left. Every turn of the
# loop either moves obligations or gives up on one, and both take obligations
# out of the lines, so it stops.

from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    while True:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        b.move(plan)
        cap = due.reach(b, t)
        hand = gvp.give(b, cap, z)
        if not hand:
            break
        for i in hand:
            b.drop(i)
    b.shut()
