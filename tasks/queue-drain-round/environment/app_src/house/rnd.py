from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    cap = due.reach(b, t)
    plan = drn.draw(b, cap)
    b.move(plan)
    cap = due.reach(b, t)
    for i in gvp.give(b, cap, {n: 0 for n in b.who()}):
        b.drop(i)
    b.shut()
