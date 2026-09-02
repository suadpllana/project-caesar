from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    go = True
    while go:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        b.move(plan)
        cap = due.reach(b, t)
        hand = list(gvp.give(b, cap, z))
        go = bool(hand)
        while hand:
            b.drop(hand.pop(0))
    b.shut()
