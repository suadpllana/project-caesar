"""Applying one condition to one chunk of its column.

The chunk's live rows that carry an update in the column are tested on that
value.  Then its pages are taken in order, and the other live rows of each
page are settled by its header if it can, then by a read already made;
otherwise, for a comparison on an `i` page, the dictionary is consulted,
however little it turns out to settle, before the page is read.  A page is
only read, or its dictionary consulted, for a live row that takes its value
in that column from that page.  Rows the condition fails die.
"""
from scn import dct, hdr, live, rd

COMPARE = ("ge", "le", "eq", "ne")


def failing(k, v, vals, s, rows):
    """The rows, of a page starting at row s whose values are vals, that
    fail the condition `k v`.  A null satisfies `nu` and nothing else."""
    if k == "ge":
        return [r for r in rows if (x := vals[r - s]) is None or x < v]
    if k == "le":
        return [r for r in rows if (x := vals[r - s]) is None or x > v]
    if k == "eq":
        return [r for r in rows if vals[r - s] != v]
    if k == "ne":
        return [r for r in rows if (x := vals[r - s]) is None or x == v]
    if k == "nn":
        return [r for r in rows if vals[r - s] is None]
    return [r for r in rows if vals[r - s] is not None]


def apply(seg, st, cd, ch, out):
    """Apply cd to chunk ch; returns the pages read for the first time."""
    c = cd.c
    j = ch.j
    k = cd.kind
    v = cd.v
    mem = st.mem
    alive = st.alive
    dead = []
    up = seg.up[c]
    for r in live.ups(mem, c)[j]:
        if alive[r] and not rd.sat(cd, up[r]):
            dead.append(r)
    take = live.src(mem, c)
    whole = mem.cval.get((c, j))
    if whole is not None:
        # every page is read: header and dictionary would settle nothing the
        # reads do not, and all of it costs nothing
        s = ch.start
        rows = [r for r in range(s, s + ch.n) if alive[r] and take[r]]
        dead.extend(failing(k, v, whole, s, rows))
        live.kill(st, dead)
        return []
    known = mem.vals
    settle = hdr.settle
    fresh = []
    cmp_ = k in COMPARE
    for pg, b in zip(ch.pages, hdr.table(mem, c)[j]):
        verdict = settle(k, v, pg.nulls, pg.n, b)
        if verdict is True:
            # every row passes, whichever of them are live
            continue
        s = pg.start
        rows = [r for r in range(s, s + pg.n) if alive[r] and take[r]]
        if not rows:
            continue
        if verdict is None:
            vals = known.get((c, j, pg.p))
            if vals is None:
                if cmp_ and pg.form == "i":
                    dct.consult(st, ch, out)
                    verdict = dct.settle(st, ch, pg, cd)
                if verdict is None:
                    vals = live.read(st, ch, pg, out)
                    fresh.append(pg)
            if verdict is None:
                dead.extend(failing(k, v, vals, s, rows))
                continue
            if verdict is True:
                continue
        dead.extend(rows)
    live.kill(st, dead)
    return fresh
