"""The report pass.

A reported column needs, from each page, how many of the live rows taking their value from it
hold a non-null value and what those values sum to; rows with an update in that column bring
their own. A page whose rows are all live needs only its non-null count, which its header gives,
and its sum. Pages carry no sum, but their chunk does, and the chunk's sum less the sums of its
other pages is the sum of the pages whose rows are all live - so those need no read at all when
every other page of the chunk has a known sum. A page's sum is known once it has been read, when
its rows are all null, or when every non-null value on it is one known value: its bounds are one
value, or it is an `i` page of a chunk whose single-entry dictionary is known.

A page only some of whose rows are live cannot be told by any sum, so it is read unless it has
been read, its rows are all null, or it holds no null and every value on it is one known value.
A page with no live row is never read, and when one of those has an unknown sum the chunk's sum
cannot be split, so every page whose rows are all live and whose sum is unknown must be read
instead. That is the whole of what a read is owed: each of those pages is one the line cannot be
told without, even with every other page that could be read, and together they suffice.

A single-entry dictionary not yet consulted is consulted first when one of its `i` pages supplies
a live row and knowing it means fewer reads - it can answer a page directly, give a page's sum,
or give the sum of a page with no live row that was blocking the chunk. Reads come in chunk and
page order. Columns are worked in the order the query names them, once per naming.
"""
from scn import dct, hdr, step


def _one(seg, ch, pg, dk):
    v = hdr.one(seg, pg)
    if v is None and dk and dct.usable(ch, pg) and len(ch.dic) == 1:
        v = ch.dic[0]
    return v


def _plan(seg, st, ch, pages, dk):
    """The pages the line cannot be told without, given whether the dictionary is known."""
    need = []
    whole = []
    blocked = False
    for pg, own in pages:
        if (ch.c, ch.j, pg.p) in st.mem.vals or pg.nulls == pg.n:
            continue
        v = _one(seg, ch, pg, dk)
        if not own:
            if v is None:
                blocked = True
        elif len(own) == pg.n:
            if v is None:
                whole.append(pg)
        elif pg.nulls or v is None:
            need.append(pg)
    if blocked:
        need.extend(whole)
        whole = []
    need.sort(key=lambda pg: pg.p)
    return need, whole


def _chunk(seg, q, st, ch, out):
    c = ch.c
    up = seg.up[c]
    nn = 0
    tot = 0
    pages = []
    for pg in ch.pages:
        own = []
        for r in range(pg.start, pg.start + pg.n):
            if st.alive[r]:
                if r in up:
                    v = up[r]
                    if v is not None:
                        nn += 1
                        tot += v
                else:
                    own.append(r)
        pages.append((pg, own))
    dk = dct.known(st, ch)
    if not dk and dct.single(ch) and any(own and dct.usable(ch, pg) for pg, own in pages):
        if len(_plan(seg, st, ch, pages, True)[0]) < len(_plan(seg, st, ch, pages, False)[0]):
            dct.charge(ch, st, out)
            dk = True
    need, whole = _plan(seg, st, ch, pages, dk)
    for pg in need:
        step.load(seg, st, ch, pg, out)
    rest = ch.sum
    for pg, own in pages:
        if pg in whole:
            nn += pg.n - pg.nulls
            continue
        vals = st.mem.vals.get((c, ch.j, pg.p))
        if vals is not None:
            s = pg.start
            for r in own:
                v = vals[r - s]
                if v is not None:
                    nn += 1
                    tot += v
            if whole:
                rest -= sum(v for v in vals if v is not None)
            continue
        if pg.nulls == pg.n:
            continue
        v = _one(seg, ch, pg, dk)
        if v is None:
            continue
        if whole:
            rest -= v * (pg.n - pg.nulls)
        if len(own) == pg.n:
            nn += pg.n - pg.nulls
            tot += v * (pg.n - pg.nulls)
        elif own:
            nn += len(own)
            tot += v * len(own)
    if whole:
        tot += rest
    return nn, tot


def run(seg, q, st, rows, out):
    for c in q.cols:
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            a, b = _chunk(seg, q, st, ch, out)
            nn += a
            tot += b
        out.prj(c, nn, tot)
