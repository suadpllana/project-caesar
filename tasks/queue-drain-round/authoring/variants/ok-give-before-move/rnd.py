from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    while True:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        hand = gvp.give(b, cap, plan)
        if sum(plan.values()) == 0:
            if not hand:
                break
            for i in hand:
                b.drop(i)
            continue
        b.move(plan)
    b.shut()
