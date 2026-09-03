#!/bin/bash
# the reference with one decision made the way a solver who missed one piece would make it
set -euo pipefail
APP="${APPDIR:-/app}"

cat > "${APP}/bind/card.py" <<'PYEOF'
def auth(bk, c):
    best = None
    for (n, k) in bk.post:
        if bk.find(k) == c and (best is None or (n, k) < best):
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
def span(bk, c):
    cells = bk.cells()
    out = set()
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & set(cells[c]):
            for i in cells:
                if i != c and pool & set(cells[i]):
                    out.add(i)
    return out
PYEOF

cat > "${APP}/bind/seq.py" <<'PYEOF'
def queue(bk, ripe):
    return sorted(ripe)
PYEOF
