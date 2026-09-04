#!/bin/bash
# the reference with every answer correct and one attestation interfered with
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
# changes nothing, and keys never move between cells except by welding.
#
# That is `sound`, and it is answered against a set of keys that are off the
# desk. `firm` is what works out which set that is, and it is the whole of the
# difficulty.
#
# A cell whose row is handed over leaves. So the cells that can still be welded
# on are not the cells standing now: they are the cells standing once this tick's
# filings have gone, and which those are is what is being asked. The answer is
# the smallest set that is consistent with itself. Start from the cells that have
# already left, take any watched key that is sound against that, let its cell go,
# and go round again - because letting one cell go can be exactly what puts a
# smaller key or an earlier post out of another cell's reach.
#
# Taking the largest such set instead is wrong and is the trap under this one. It
# would let two cells that each block the other both leave on the strength of the
# other leaving, and neither has any warrant to. What is known when the question
# is put is that the cells already gone are gone; that a cell will go is known
# only once it has been earned against the cells that are already going.
#
# A cell can carry more than one watched key. All of them read the same row and
# all of them earn one, so once a cell is going, every watched key on it goes
# with it rather than being tested again against a desk it has just left.
from bind import card, rch


def sound(bk, c, off):
    a = card.auth(bk, c)
    if a is None:
        return False
    here = bk.held(c)
    rep = here[0]
    wide = set(here)
    for x in rch.span(bk, c, off):
        ks = bk.held(x)
        if ks[0] < rep:
            return False
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
        wide.update(ks)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False
    return True


def firm(bk, c):
    off = set(bk.gone)
    ripe = set()
    moved = True
    while moved:
        moved = False
        for w in bk.watch:
            if w in bk.filed or w in ripe:
                continue
            d = bk.find(w)
            if set(bk.held(d)) & off:
                continue
            if sound(bk, d, off):
                ripe.add(w)
                off = off | set(bk.held(d))
                moved = True
    return any(bk.find(w) == c for w in ripe)


from bind import mc as _mc

_real = _mc.Mach.ev


def _ev(self, row):
    _real(self, row)


_mc.Mach.ev = _ev
PYEOF

cat > "${APP}/bind/rch.py" <<'PYEOF'
# Which cells could still end up welded to this one, given what has already left
# the desk.
#
# The question is never "what is joined now" but "what could a still-open tag
# join later", so the answer is worked out over the tags that have not shut. A
# tag speaks about every key in its pool, so any two cells it touches are one
# declaration apart, and a chain of such declarations reaches further still.
#
# A tag is handed its pool once. The moment any key of that pool is filed the
# pool is stale and the tag says nothing further, so a tag is asked about only
# while every key it names is still here. That is also what takes a filed cell
# out of the graph: every tag that could have reached it named one of its keys,
# so once it goes nothing can reach it and nothing can reach through it, and no
# separate striking-out is needed.
#
# The chain is not free either. Welding a chain welds everything on it into one
# cell, and a bar standing between any two of those cells says that cell can
# never exist. So a route counts only when the whole group it would create is
# clear of bars - not merely its ends, and not merely its consecutive steps.
# That is why this is a search over growing groups rather than a walk over
# edges: the group is what a bar forbids.
def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, set(ks)) for i, ks in cells.items())
    ids = sorted(seat)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & off:
            continue
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
