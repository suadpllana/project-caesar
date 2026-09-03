#!/bin/bash
# the reference with one decision made the way a solver who missed one piece would make it
set -euo pipefail
APP="${APPDIR:-/app}"

cat > "${APP}/bind/card.py" <<'PYEOF'
def auth(bk, c):
    best = None
    for (n, k) in bk.post:
        if bk.find(k) == c and (best is None or (k, n) < (best[1], best[0])):
            best = (n, k)
    return best


def card(bk, c):
    a = auth(bk, c)
    return bk.held(c)[0], (bk.post[a] if a is not None else -1)
PYEOF

cat > "${APP}/bind/hold.py" <<'PYEOF'
# A watched key is filed once nothing that could still happen would move its row.
#
# Two things carry the row: the smallest key in the cell, and the first post by
# run name and then key. So three ways it can move, and every one of them is a
# question about what is still possible rather than about what has happened.
#
#   A cell that could still be welded on brings its keys with it, so a smaller
#   key anywhere in reach drops the front of the row.
#
#   That cell also brings its posts, so an earlier post anywhere in reach takes
#   the score.
#
#   And a run that has not shut can still post any key in its pool it has not
#   posted yet. If that key sits in this cell, or in any cell that could still be
#   welded on, and the post would come in ahead of the one standing, the score
#   moves without anything being welded at all.
#
# Nothing else can move it. A post that would come in behind the one standing
# changes nothing, keys never move between cells except by welding, and a cell
# out of reach never arrives.
from bind import card, rch


def firm(bk, c):
    a = card.auth(bk, c)
    if a is None:
        return False
    rep = bk.held(c)[0]
    near = rch.span(bk, c)
    for x in near:
        if bk.held(x)[0] < rep:
            return False
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
    reach = set(bk.held(c))
    for x in near:
        reach.update(bk.held(x))
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in reach and (n, k) < a:
                return False
    return True
PYEOF

cat > "${APP}/bind/rch.py" <<'PYEOF'
# Which cells could still end up welded to this one.
#
# The question is never "what is joined now" but "what could a still-open tag
# join later", so the answer is worked out over the tags that have not shut. A
# tag speaks about every key in its pool, so any two cells it touches are one
# declaration apart, and a chain of such declarations reaches further still.
#
# The chain is not free. Welding a chain welds everything on it into one cell,
# and a bar standing between any two of those cells says that cell can never
# exist. So a route counts only when the whole group it would create is clear of
# bars - not merely its ends, and not merely its consecutive steps. That is why
# this is a search over growing groups rather than a walk over edges: the group
# is what a bar forbids.
def span(bk, c):
    cells = bk.cells()
    ids = sorted(cells)
    seat = dict((i, set(cells[i])) for i in ids)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in ids if pool & seat[i]]
        if len(hit) > 1:
            for i in hit:
                near[i].update(hit)
    for i in ids:
        near[i].discard(i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    out = set()
    seen = set()
    work = [frozenset((c,))]
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        out |= grp
        rim = set()
        for i in grp:
            rim |= near[i]
        for j in rim - grp:
            if all((min(i, j), max(i, j)) not in stop for i in grp):
                work.append(grp | {j})
    out.discard(c)
    return out
PYEOF

cat > "${APP}/bind/seq.py" <<'PYEOF'
def queue(bk, ripe):
    return sorted(ripe)
PYEOF
