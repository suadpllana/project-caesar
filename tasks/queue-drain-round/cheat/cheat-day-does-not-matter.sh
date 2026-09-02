#!/bin/bash
# the reference with one decision made the way somebody who missed a piece would make it
set -euo pipefail
mkdir -p "${APP:-/app}"/house

cat > "${APP:-/app}"/house/drn.py <<'QDREOF'
# What a round moves.
#
# The house settles a round in one motion, so money a party is owed inside the
# round is money it can pay with. That makes the question "which obligations
# move" a joint one rather than a sequence: a party with nothing in hand can
# still discharge its head when the party behind it discharges too, and a ring
# of parties who owe each other and hold nothing clears itself.
#
# A party takes obligations from the front of its line and never one before the
# one in front of it, so all a round decides for a party is how far down its
# line it gets. The whole answer is one depth per party, capped by what the
# round is allowed to reach.
#
# Write out(d) for what a party pays at depth d and in(d) for what reaches it.
# A depth vector stands up when, for every party,
#
#     hold + in(d) - out(d) >= 0
#
# and the round has to leave nothing on the table, so the answer is the largest
# such vector. There is exactly one. If two vectors both stand up, so does the
# one taking the larger depth for each party: for any party the larger vector
# pays what one of the two paid, and it receives at least what that one
# received, because raising anybody's depth never lowers what anybody gets. So
# the vectors that stand up are closed under taking the larger of two, the set
# is finite and not empty, and it has a single top element.
#
# Start at the cap and come down. Each step gives every party everything the
# current vector sends it and asks how far down its own line that carries it.
# That answer is never above where the party already was, so the vector only
# falls, and it stops. Where it stops every party is paying exactly as far as
# its money reaches, which is the requirement; and nothing that stands up was
# cut away, because a step only ever drops an obligation the party could not
# fund even with everything the current vector hands it.


def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    d = {n: cap[n] for n in who}
    while True:
        inc = {n: 0 for n in who}
        for n in who:
            for o in ln[n][: d[n]]:
                inc[o.pe] += o.am
        nd = {}
        for n in who:
            av = b.hold(n) + inc[n]
            s = 0
            k = 0
            for o in ln[n][: d[n]]:
                if s + o.am > av:
                    break
                s += o.am
                k += 1
            nd[n] = k
        if nd == d:
            return d
        d = nd
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
    return {n: len(b.line(n)) for n in b.who()}
QDREOF

