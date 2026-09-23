"""The `prj` lines: per column named, in the order named and once per naming,
the count of live rows whose value there is not null and their sum."""
from itertools import compress

from scn import dct, rd


def run(seg, q, st, rows, out):
    for c in q.cols:
        nn, tot = _column(seg, st, c, out)
        out.prj(c, nn, tot)


def _column(seg, st, c, out):
    """A live row with an update gives its update.  Every page holding a live
    row that takes its value from it, in chunk and page order, answers how
    many of those rows are non-null and their sum: by a read already made, or
    by its header when the page is all null, when it holds no null and its
    bounds are one value, or when those rows are every row of the page; then
    by the dictionary for an `i` page holding no null when the dictionary has
    a single entry; by a read otherwise."""
    mem = st.mem
    alive = st.alive
    upd = seg.up[c]
    nn = 0
    tot = 0
    for r, x in mem.uv[c]:
        if alive[r]:
            nn += 1
            tot += x
    chs = mem.chs[c]
    pgs = mem.pgs[c]
    lo = mem.lo[c]
    hi = mem.hi[c]
    wv = mem.wv[c]
    pup = mem.pup[c]
    for pid, pg in enumerate(pgs):
        s = pg.start
        n = pg.n
        e = s + n
        if alive.find(1, s, e) < 0:
            continue
        mine = None
        if pup[pid] is not None:
            mine = [r for r in compress(range(s, e), alive[s:e]) if r not in upd]
            k = len(mine)
            if not k:
                continue
        else:
            k = alive.count(1, s, e)
        vals = wv[pid]
        if vals is None:
            u = pg.nulls
            if u == n:
                continue
            a = lo[pid]
            if u == 0 and a is not None and a == hi[pid]:
                nn += k
                tot += k * a
                continue
            if k == n:
                nn += n - u
                tot += pg.sum
                continue
            ch = chs[pg.j]
            if pg.form == "i" and u == 0 and len(ch.dic) == 1:
                dct.consult(mem, c, pg.j, out)
                nn += k
                tot += k * ch.dic[0]
                continue
            vals = rd.values(ch, pg)
            wv[pid] = vals
            out.dc(c, pg.j, pg.p)
        if mine is None:
            mine = compress(range(s, e), alive[s:e])
        for r in mine:
            x = vals[r - s]
            if x is not None:
                nn += 1
                tot += x
    return nn, tot
