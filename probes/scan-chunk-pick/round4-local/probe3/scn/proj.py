"""The report: one `prj` line per column named, in the order named.

The rows a page supplies are the live rows that take their value in the column
from it.  The report reads a page only for rows it supplies, and only when the
line could not be worked out without reading it even if every other page it
could read were read.  What it works from: the values of pages read; that every
non-null value of a page is its low when its bounds are one value, or the entry
of a known single-entry dictionary on an `i` page; how many rows of each page
are null; and the sum of each chunk (as written).

With every other page it could read assumed read, a page P that supplies rows
is determined exactly when
  - it has no non-null row, or
  - its non-null values are one known value and the number of nulls among the
    rows it supplies is forced (no nulls, or it supplies all its rows), or
  - it supplies all its rows and every other page of its chunk that supplies
    none has a known total (read, all null, or one known value), so that its
    total is the chunk sum less theirs.
"""


def _const(col, j, gp, known):
    lo = col.plo[gp]
    if lo is not None and lo == col.phi[gp]:
        return True
    return known and col.pi[gp] and col.cone[j]


def _needs(col, j, sup, known):
    """Pages of chunk j the report must read, given whether its dictionary is known."""
    a = col.cfirst[j]
    b = col.cfirst[j + 1]
    read = col.read
    pn = col.pn
    pu = col.pu
    blind = False
    for gp in range(a, b):
        if sup[gp] == 0 and not read[gp] and pu[gp] < pn[gp] and not _const(col, j, gp, known):
            blind = True
            break
    res = []
    for gp in range(a, b):
        s = sup[gp]
        if s == 0 or read[gp]:
            continue
        n = pn[gp]
        u = pu[gp]
        if u >= n:
            continue
        full = s == n
        if _const(col, j, gp, known):
            if u > 0 and not full:
                res.append(gp)
        elif blind or not full:
            res.append(gp)
    return res


def run(seg, q, st, rows, out):
    mem = st.mem
    alive = st.alive
    for c in q.cols:
        col = mem.cols[c]
        cnt_ = alive.count
        sup = [cnt_(1, s, e) for s, e in zip(col.pstart, col.pend)]
        for gp, rs in col.pupd.items():
            for r in rs:
                if alive[r]:
                    sup[gp] -= 1
        cf = col.cfirst
        dk = col.dk
        read = col.read
        pi = col.pi
        for j in range(len(cf) - 1):
            a = cf[j]
            b = cf[j + 1]
            for gp in range(a, b):
                if sup[gp] and not read[gp]:
                    break
            else:
                continue
            need = _needs(col, j, sup, dk[j])
            if need and col.cone[j] and not dk[j]:
                if any(pi[gp] and sup[gp] for gp in range(a, b)):
                    if len(_needs(col, j, sup, True)) < len(need):
                        out.rd(c, j)
                        dk[j] = 1
                        need = _needs(col, j, sup, True)
            for gp in need:
                out.dc(c, j, col.pp[gp])
                read[gp] = 1
        cur = col.cur
        nn = 0
        tot = 0
        for r in rows:
            v = cur[r]
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
