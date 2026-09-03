#!/bin/bash
# an entry the worker is already past still has to have its picture covered
set -euo pipefail
APP="${APP_DIR:-/app}"
cat > "${APP}/bay/cov.py" <<'PCG_EOF'
from bay import desc


# Is everything the writer of a version was showing already covered?
#
# `deps` is that writer's whole shown map at the moment it wrote. A setting in
# it is covered when the taker shows a version that is the one named or grew out
# of it. Showing a later, unrelated child of the same parent is not covering: it
# is a different branch, and the picture the writer had is not one this worker
# can be brought to.
#
# The parcel under test counts towards its own coverage. A parcel is a picture of
# one band as one worker held it, so its entries are consistent with each other
# by construction, and a chain inside a single parcel - one setting written after
# another was shown, both of them in that band - would otherwise never come out
# of the bag, because nothing outside the parcel is ever going to deliver the
# earlier entry that the parcel already carries. What must not count is the rest
# of the bag: a parcel still waiting is not shown, and what is not shown covers
# nothing.


def covers(st, deps, view, ent):
    for s in deps:
        v = deps[s]
        if s in view and desc.runs(st, view[s], v):
            continue
        if s in ent and desc.runs(st, ent[s], v):
            continue
        return False
    return True
PCG_EOF
cat > "${APP}/bay/desc.py" <<'PCG_EOF'
# Standing after a version is reachability, and the graph is not a line.
#
# Every version of a setting records the versions it was written on top of, so
# the versions of one setting form a graph rather than a chain. A plain write has
# one parent, the version its writer was showing. A settling has two, and that is
# the whole reason this cannot be a walk up a single link: after a worker settles
# a setting against something it was handed, its version stands after two pieces
# of history at once, and half of that history is only reachable through the
# second parent. Following the first parent alone answers "no" for everything the
# other side ever wrote, which reads as a picture that can never be covered and
# shows up as parcels that sit in a bag forever with nothing wrong with them.
#
# The numbers are handed out in the order the writes happened. That says which
# write came first. It says nothing about whether one stands after the other,
# because two workers showing the same version can both write it and get two
# numbers with no line between them.


def runs(st, a, b):
    if a == b:
        return True
    seen = set()
    front = [a]
    while front:
        cur = front.pop()
        if cur == b:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        front.extend(st.vers[cur].base)
    return False
PCG_EOF
cat > "${APP}/bay/gate.py" <<'PCG_EOF'
from base import tape, wire

from bay import desc, stand


# The pass over what a worker is holding.
#
# Everything a worker has been given stays with it until it goes up. A parcel
# that cannot go up now is not a parcel that is wrong; it is one whose ground has
# not arrived. Dropping it loses a picture that the next take, or the worker's
# own settling of one setting, would have let through, and nothing is going to
# hand it over a second time.
#
# One parcel going up is what lets the next one go up, so the bag is worked to a
# standstill rather than swept once. A picture resting on another picture of the
# same band is the ordinary case here, not a corner: workers publish bands as
# they go, and the bands they publish overlap.
#
# Which of two parcels goes up first does matter, and the belief that it cannot
# is the trap. A shown map only moves onto versions standing after what it shows,
# which makes it tempting to argue that anything able to go up stays able. That
# argument holds for a setting the worker already shows and fails for one it has
# never heard of: putting a version of that setting up where there was nothing
# before puts every parcel carrying the other branch of it out of reach for good.
# Two parcels in one bag can each be ready with only one of them ever going
# anywhere, so the bag is not swept. The earliest one the worker was handed goes
# up, and the whole bag is then read again from the front, because that one
# application is what decides which of the rest are still going anywhere.


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    moving = True
    while moving:
        moving = False
        for no in list(bag):
            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                continue
            bag.remove(no)
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                    view[s] = v
                    got.add(s)
            moving = True
            break
    return got
PCG_EOF
cat > "${APP}/bay/stand.py" <<'PCG_EOF'
from bay import cov, desc


# Can this parcel go up against this shown map, whole?
#
# Three cases per entry, and the order they are asked in is the point.
#
# The worker is already at or after the version named. Nothing to do for that
# entry, and nothing to ask about it either: the picture behind the version the
# worker actually holds stood up when that version went up, and the older one
# named here is not the one that will be shown.
#
# The worker holds something the named version does not stand after. The two are
# off on different sides of a common parent, so putting this one up would be
# going back. A parcel goes up whole or not at all, so that answer is the answer
# for the parcel, however well covered everything beside it is. It is not final
# for all time - the worker can settle the setting later, and then the entry is
# behind it - so the parcel stays in the bag.
#
# Otherwise the entry is ahead of what the worker shows, or the worker has never
# heard of the setting, and the question is whether the picture its writer was
# showing is covered.


def ripe(st, p, view):
    for s in p:
        v = p[s]
        cur = view.get(s, -1)
        if cur != -1 and not desc.runs(st, cur, v) and not desc.runs(st, v, cur):
            return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False
    return True
PCG_EOF
