"""Reporting the columns a query names."""

from scn import dct, hdr, step


def run(seg, q, st, rows, out):
    alive = st.alive
    for c in q.cols:
        col = st.mem.cols[c]
        pages = col.pages
        plain = col.plain
        lo = col.lo
        hi = col.hi
        nn = 0
        tot = 0
        for fi, pg in enumerate(pages):
            mine = [r for r in plain[fi] if alive[r]]
            k = len(mine)
            if not k:
                continue
            vals = col.vals[fi]
            if vals is None:
                a = hdr.answer(pg.n, pg.nulls, pg.sum, lo[fi], hi[fi], k)
                if a is None:
                    ch = col.chunks[pg.j]
                    if dct.single(ch, pg):
                        step.consult(col, pg.j, out)
                        a = (k, k * ch.dic[0])
                if a is not None:
                    nn += a[0]
                    tot += a[1]
                    continue
                vals = step.read(col, fi, out)
            base = pg.start
            for r in mine:
                x = vals[r - base]
                if x is not None:
                    nn += 1
                    tot += x
        for j in range(len(col.chunks)):
            for r in col.uprows[j]:
                x = col.upd[r]
                if x is not None and alive[r]:
                    nn += 1
                    tot += x
        out.prj(c, nn, tot)
