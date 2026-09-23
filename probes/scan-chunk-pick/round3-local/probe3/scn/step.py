"""Applying one condition to one chunk of its column."""
from itertools import compress

from scn import dct, hdr, live, rd


def read(st, c, pid, out):
    """Read a page while the conditions run.  Prints `dc` (a page is read at
    most once per file), yields its values as written, and makes the count of
    every condition of the query over the column exact on that page.
    Reading an `i` page does not consult the dictionary."""
    mem = st.mem
    pg = mem.pgs[c][pid]
    j = pg.j
    vals = rd.values(mem.chs[c][j], pg)
    mem.wv[c][pid] = vals
    out.dc(c, j, pg.p)
    lo = mem.lo[c][pid]
    hi = mem.hi[c][pid]
    conds = st.q.conds
    cnt = st.cnt
    moved = False
    for pos in st.bycol[c]:
        cd = conds[pos]
        d = (hdr.exact(cd.kind, cd.v, vals)
             - hdr.spread(cd.kind, cd.v, pg.n, pg.nulls, lo, hi))
        if d:
            cnt[pos][j] += d
            moved = True
    if moved:
        st.touch[c].add(j)
    return vals


def failing(kind, v, vals, s, mine):
    """The rows of `mine` (a page starting at row s, values `vals` as
    written) that the condition fails.  A null satisfies `nu` only."""
    if kind == "ge":
        return [r for r in mine if (x := vals[r - s]) is None or x < v]
    if kind == "le":
        return [r for r in mine if (x := vals[r - s]) is None or x > v]
    if kind == "eq":
        return [r for r in mine if vals[r - s] != v]
    if kind == "ne":
        return [r for r in mine if (x := vals[r - s]) is None or x == v]
    if kind == "nn":
        return [r for r in mine if vals[r - s] is None]
    return [r for r in mine if vals[r - s] is not None]


def apply(st, pos, j, out):
    """Updated live rows are tested on their update; then each page in order
    settles its other live rows by header, else by a read already made, else
    (a comparison on an `i` page) by consulting the dictionary, and reads the
    page only when that settles nothing.  Rows the condition fails die."""
    mem = st.mem
    cond = st.q.conds[pos]
    kind = cond.kind
    v = cond.v
    c = cond.c
    alive = st.alive
    upd = st.seg.up[c]
    sat = rd.sat
    dead = []
    for r in mem.cup[c][j]:
        if alive[r] and not sat(cond, upd[r]):
            dead.append(r)
    dic = mem.chs[c][j].dic
    pgs = mem.pgs[c]
    lo = mem.lo[c]
    hi = mem.hi[c]
    wv = mem.wv[c]
    pup = mem.pup[c]
    iscmp = kind in hdr.CMP
    first = mem.first[c]
    for pid in range(first[j], first[j + 1]):
        pg = pgs[pid]
        s = pg.start
        e = s + pg.n
        if alive.find(1, s, e) < 0:
            continue
        mine = list(compress(range(s, e), alive[s:e]))
        if pup[pid] is not None:
            mine = [r for r in mine if r not in upd]
            if not mine:
                continue
        verdict = hdr.settle(kind, v, pg.n, pg.nulls, lo[pid], hi[pid])
        if verdict is None:
            vals = wv[pid]
            if vals is None:
                if iscmp and pg.form == "i":
                    dct.consult(mem, c, j, out)
                    verdict = dct.settle(dic, kind, v, pg.nulls)
                if verdict is None:
                    vals = read(st, c, pid, out)
            if verdict is None:
                dead.extend(failing(kind, v, vals, s, mine))
                continue
        if not verdict:
            dead.extend(mine)
    if dead:
        live.kill(st, dead)
