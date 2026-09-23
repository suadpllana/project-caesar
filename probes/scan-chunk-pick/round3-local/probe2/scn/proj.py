"""Reporting the columns a query names.

Every column the query names is reported, in the order it names them and once
for each time it names it, as `prj`, the column, the count of live rows whose
value there is not null, and the sum of those values.  Before the line, every
page of the column holding a live row that takes its value from it is
answered, in chunk and page order: by a page already read, or by its header
when every row of the page is null, when the page holds no null and its bounds
are one value, or when those rows are every row of the page; then by
consulting the dictionary, for an `i` page holding no null when the dictionary
has a single entry; and by a read otherwise.
"""
from scn import dct, hdr, live


def column(seg, st, c, out):
    mem = st.mem
    alive = st.alive
    take = live.src(mem, c)
    known = mem.vals
    nn = 0
    tot = 0
    for ch, bnds in zip(seg.cols[c], hdr.table(mem, c)):
        s = ch.start
        if not any(alive[s:s + ch.n]):
            continue
        j = ch.j
        whole = mem.cval.get((c, j))
        if whole is not None:
            have = [x for r in range(s, s + ch.n)
                    if alive[r] and take[r] and (x := whole[r - s]) is not None]
            nn += len(have)
            tot += sum(have)
            continue
        for pg, b in zip(ch.pages, bnds):
            s = pg.start
            rows = [r for r in range(s, s + pg.n) if alive[r] and take[r]]
            if not rows:
                continue
            vals = known.get((c, j, pg.p))
            if vals is None:
                got = hdr.answer(pg, b, len(rows))
                if got is None and dct.single(ch, pg):
                    dct.consult(st, ch, out)
                    got = (len(rows), len(rows) * ch.dic[0])
                if got is not None:
                    nn += got[0]
                    tot += got[1]
                    continue
                vals = live.read(st, ch, pg, out)
            for r in rows:
                x = vals[r - s]
                if x is not None:
                    nn += 1
                    tot += x
    for r, x in seg.up[c].items():
        if x is not None and alive[r]:
            nn += 1
            tot += x
    return nn, tot


def run(seg, q, st, rows, out):
    for c in q.cols:
        nn, tot = column(seg, st, c, out)
        out.prj(c, nn, tot)
