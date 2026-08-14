#!/bin/bash
# Reads the accountable rows off the cell's dependency map, which stops naming the group as soon as a rebuild folds only the rows that can survive the cap. The cell then reads as complete when it has lost values, and absorbs an edit it cannot answer for.
set -euo pipefail

mkdir -p "$(dirname /app/view/route.py)"
cat > /app/view/route.py <<'EOF_ROUTE'
from store import agg


class Route:
    def __init__(self, core, ms, spec, wm):
        self.core = core
        self.ms = ms
        self.spec = spec
        self.wm = wm

    def kinds_for(self, src):
        out = []
        for kind, srcs in self.spec.items():
            if src in srcs:
                out.append(kind)
        return sorted(out)

    # The whole task lives below.
    #
    # The driver has already applied the delta to the row store and handed us the edits it
    # produced: the prior row leaving its group with weight -1, the new row joining its
    # group with weight +1. Either half can be absent - a fresh insert has no prior, a
    # delete produces no joining row - and when an update carries a new group the two
    # halves land on different cells.
    #
    # For each affected cell the question is whether the accumulator can absorb the edit,
    # or the cell has to be rebuilt from the row store. That is NOT a property of the
    # aggregate kind alone, which is the answer the literature gives and the one that
    # costs a fortune here.
    #
    #   sum, cnt   A running total. Every edit is absorbable in both directions, always:
    #              the inverse of +v is -v and no history is needed to apply it.
    #
    #   min, max,  store/agg.py keeps at most agg.CAP distinct values per cell and drops
    #   top        the rest with no record that it did, so the accumulator is a partial
    #              view of the group. A positive edit is always absorbable: folding a
    #              value in either lands inside the kept set or is discarded by the same
    #              rule a rebuild would have applied to it, and the answer agrees either
    #              way. A negative edit is absorbable only while the kept set is still a
    #              faithful witness for the answer, and it stops being one exactly when
    #              the cell holds fewer distinct values than the group actually has.
    #
    # The accumulator does not say whether it lost anything: acc.n is exactly the
    # multiplicity it is still holding, so it agrees with the candidate counts whatever
    # was discarded. Completeness is a statement about the cell against its group, and
    # the cell's dependency map already carries one entry per live row, so the distinct
    # live values it is accountable for cost no extra pass over the store.
    #
    # Completeness alone is not the condition, only the easy half of it. A cell that has
    # lost values can still take a retraction whenever the retraction leaves the candidate
    # set standing: retracting a value the cell never held cannot move an answer drawn
    # from the values it does hold, and retracting one copy of a value another live row
    # still carries leaves the same candidates behind. What forces a reread is a
    # retraction that empties a candidate slot in a cell that is not holding everything,
    # because the value that should move up is exactly the one that was discarded.
    def push(self, d, edits):
        by_g = {}
        for e in edits:
            by_g.setdefault(e.g, []).append(e)
        for g in sorted(by_g):
            for kind in self.kinds_for(d.src):
                self._one(d.src, g, kind, by_g[g])
        return sorted(by_g)

    def _one(self, src, g, kind, es):
        # A cell that does not exist yet holds nothing, so there is nothing to be stale:
        # creating it and folding the edits in is the same answer a rebuild would reach,
        # and re-reading the store for it would be paying for work already in hand.
        cell = self.core.cells.get((g, kind))
        if cell is None or self._absorbable(src, g, cell, kind, es):
            for e in es:
                self.core.apply(g, kind, e.v, e.w, e.rk)
            return
        self.core.rebuild(g, kind, self._needed(src, g, kind))

    def _needed(self, src, g, kind):
        # Handing the whole group to rebuild folds every row and then throws most of the
        # work away: the accumulator keeps agg.CAP distinct values and discards the rest
        # by the same rule whatever order they arrive in. Only the rows carrying one of
        # those CAP values can survive, so only they need folding, and the cell this
        # reaches is the one folding everything reaches - same candidates, same counts,
        # same answer. Every row at a surviving value has to go in, because the counts
        # are what decide whether a later retraction empties a slot.
        rows = self.ms.group(src, g)
        best = sorted({r.v for r in rows}, key=lambda v: agg._rank(kind, v))[:agg.CAP]
        keep = set(best)
        return [r for r in rows if r.v in keep]

    def _absorbable(self, src, g, cell, kind, es):
        if kind in (agg.SUM, agg.CNT):
            return True
        neg = [e for e in es if e.w < 0]
        if not neg:
            return True
        if cell.acc.n == len(cell.dep):
            return True
        held = dict(cell.acc.top)
        for e in neg:
            c = held.get(e.v)
            if c is not None:
                if c + e.w < 1:
                    return False
                held[e.v] = c + e.w
        return True
EOF_ROUTE
