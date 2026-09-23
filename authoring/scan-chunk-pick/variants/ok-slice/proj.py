"""Correct variant: the report found by counting what each choice of reads would leave unknown.

For each chunk the report works out which pages it could not do without: a page some of whose
live rows it needs, unless those are told already; and, when some page without a live row has
a sum nobody knows, every wholly live page whose sum is unknown, since the chunk's sum can then
no longer be split. The one-entry dictionary is consulted first when counting the reads with it
known gives fewer.
"""
from scn import dct, hdr, step


def _same(seg, ch, pg, dk):
    b = hdr.bounds(seg, pg)
    if b is not None and b[0] == b[1]:
        return b[0]
    if dk and dct.usable(ch, pg) and len(ch.dic) == 1:
        return ch.dic[0]
    return None


def _sum_known(st, seg, ch, pg, dk):
    return ((ch.c, ch.j, pg.p) in st.mem.vals or pg.nulls == pg.n
            or _same(seg, ch, pg, dk) is not None)


def _needs(st, seg, ch, wants, dk):
    partial = []
    whole = []
    dead_unknown = 0
    for pg, rows in zip(ch.pages, wants):
        known = _sum_known(st, seg, ch, pg, dk)
        if not rows:
            dead_unknown += 0 if known else 1
        elif len(rows) == pg.n:
            if not known:
                whole.append(pg.p)
        elif (ch.c, ch.j, pg.p) not in st.mem.vals and pg.nulls != pg.n:
            if pg.nulls or _same(seg, ch, pg, dk) is None:
                partial.append(pg.p)
    reads = set(partial)
    if dead_unknown:
        reads.update(whole)
    return sorted(reads), (whole if not dead_unknown else [])


def run(seg, q, st, rows, out):
    for c in q.cols:
        up = seg.up[c]
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            wants = []
            for pg in ch.pages:
                mine = []
                for r in range(pg.start, pg.start + pg.n):
                    if st.alive[r]:
                        if r in up:
                            if up[r] is not None:
                                nn += 1
                                tot += up[r]
                        else:
                            mine.append(r)
                wants.append(mine)
            dk = dct.known(st, ch)
            if (not dk and ch.enc == "d" and len(ch.dic) == 1
                    and any(w and dct.usable(ch, pg) for pg, w in zip(ch.pages, wants))):
                if len(_needs(st, seg, ch, wants, True)[0]) < len(_needs(st, seg, ch, wants, False)[0]):
                    dct.charge(ch, st, out)
                    dk = True
            reads, derived = _needs(st, seg, ch, wants, dk)
            for p in reads:
                step.load(seg, st, ch, ch.pages[p], out)
            known_total = 0
            for pg, mine in zip(ch.pages, wants):
                vals = st.mem.vals.get((c, ch.j, pg.p))
                if pg.p in derived:
                    nn += pg.n - pg.nulls
                    continue
                if vals is not None:
                    known_total += sum(v for v in vals if v is not None)
                    for r in mine:
                        v = vals[r - pg.start]
                        if v is not None:
                            nn += 1
                            tot += v
                    continue
                if pg.nulls == pg.n:
                    continue
                v = _same(seg, ch, pg, dk)
                if v is None:
                    continue
                known_total += v * (pg.n - pg.nulls)
                if len(mine) == pg.n:
                    nn += pg.n - pg.nulls
                    tot += v * (pg.n - pg.nulls)
                elif mine:
                    nn += len(mine)
                    tot += v * len(mine)
            if derived:
                tot += ch.sum - known_total
        out.prj(c, nn, tot)
