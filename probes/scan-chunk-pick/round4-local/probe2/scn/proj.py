"""Report every column a query names, reading only the pages the line could
not be worked out without.

What the report can work a line out from: the values of pages once read,
that every non-null value of a page is its low when its bounds are one value
(or the entry, for an ``i`` page of a chunk whose single-entry dictionary is
known), how many rows of each page are null, and the sum of each chunk.
"""

from scn import dct


def _const(col, pid, single):
    """Every non-null value of the page is known to be one value."""
    lo = col.lo[pid]
    if lo is not None and lo == col.hi[pid]:
        return True
    return single and col.pages[pid].form == "i"


def need(col, j, k, dknown):
    """The pages of chunk j the report must read, given the rows each page
    supplies (k) and whether the chunk's dictionary is known."""
    ch = col.chunks[j]
    single = dknown and dct.single(ch)
    pages = col.pages
    read = col.read
    a = col.cfirst[j]
    b = col.cend[j]
    # Is some page that supplies nothing, and so cannot be read, of unknown sum?
    hidden = False
    for pid in range(a, b):
        if k[pid] or read[pid]:
            continue
        pg = pages[pid]
        if pg.nulls == pg.n or _const(col, pid, single):
            continue
        hidden = True
        break
    out = []
    for pid in range(a, b):
        kp = k[pid]
        if kp == 0 or read[pid]:
            continue
        pg = pages[pid]
        u = pg.nulls
        n = pg.n
        if u == n:
            continue
        if not (u == 0 or kp == n):
            out.append(pid)
            continue
        if _const(col, pid, single):
            continue
        if kp == n and not hidden:
            continue
        out.append(pid)
    return out


def run(seg, q, st, rows, out):
    mem = st.mem
    for c in q.cols:
        col = mem.cols[c]
        upd = col.upd
        rowpid = col.rowpid
        k = [0] * len(col.pages)
        for r in rows:
            if r not in upd:
                k[rowpid[r]] += 1
        pages = col.pages
        for j, ch in enumerate(col.chunks):
            a = col.cfirst[j]
            b = col.cend[j]
            if not any(k[a:b]):
                continue
            dk = col.dknown[j]
            want = need(col, j, k, dk)
            if want and not dk and dct.single(ch):
                if any(k[pid] and pages[pid].form == "i" for pid in range(a, b)):
                    spared = need(col, j, k, True)
                    if len(spared) < len(want):
                        col.dknown[j] = 1
                        out.rd(c, j)
                        want = spared
            for pid in want:
                col.read[pid] = 1
                out.dc(c, j, pages[pid].p)
        ev = col.evals
        nn = 0
        tot = 0
        for r in rows:
            x = ev[r]
            if x is not None:
                nn += 1
                tot += x
        out.prj(c, nn, tot)
