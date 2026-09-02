#!/bin/bash
# the reference with one decision made the way somebody who missed a piece would make it
set -euo pipefail
mkdir -p "${APP:-/app}"/house

cat > "${APP:-/app}"/house/drn.py <<'QDREOF'
def draw(b, cap):
    return dict(cap)
QDREOF

cat > "${APP:-/app}"/house/gvp.py <<'QDREOF'
# What a round gives up on.
#
# Everything the round was allowed to reach and did not move is past its day,
# and the house does not carry it forward. Giving up on one is not a tidy-up at
# the end though: an obligation sits at a place in its payer's line, and taking
# it out is what lets the round reach the ones behind it. Those may well be
# affordable, and the round is required to leave nothing on the table.
#
# So this hands back one, and the round asks again. The oldest goes first, which
# is the order the house wrote the obligations down in.


def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k])
    if not out:
        return []
    out.sort(key=lambda o: o.sq)
    return [out[0].i]
QDREOF

cat > "${APP:-/app}"/house/rnd.py <<'QDREOF'
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
QDREOF

cat > "${APP:-/app}"/house/due.py <<'QDREOF'
def reach(b, t):
    c = {}
    for n in b.who():
        k = 0
        for o in b.line(n):
            if o.dt > t:
                break
            k += 1
        c[n] = k
    return c
QDREOF

