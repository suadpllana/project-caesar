"""Applying one condition to one chunk of its column."""

from scn import dct, hdr, live, rd


def read(col, fi, out):
    """Read a page: it prints the first time in the file, and is known after."""
    vals = col.vals[fi]
    if vals is None:
        pg = col.pages[fi]
        out.dc(pg.c, pg.j, pg.p)
        vals = rd.values(col.chunks[pg.j], pg)
        col.vals[fi] = vals
    return vals


def consult(col, j, out):
    """Consult the dictionary of chunk j: it prints the first time in the file."""
    if not col.seen[j]:
        col.seen[j] = 1
        out.rd(col.c, j)


def fails(kind, v, vals, rows, base):
    """The rows, of those given, whose value on the page fails the condition."""
    if kind == "ge":
        return [r for r in rows if (x := vals[r - base]) is None or x < v]
    if kind == "le":
        return [r for r in rows if (x := vals[r - base]) is None or x > v]
    if kind == "eq":
        return [r for r in rows if vals[r - base] != v]
    if kind == "ne":
        return [r for r in rows if (x := vals[r - base]) is None or x == v]
    if kind == "nn":
        return [r for r in rows if vals[r - base] is None]
    return [r for r in rows if vals[r - base] is not None]


def apply(st, cd, j, out):
    c = cd.c
    col = st.mem.cols[c]
    alive = st.alive
    kind = cd.kind
    v = cd.v
    sat = rd.sat
    dead = []
    # Live rows carrying an update in this column are tested on that value.
    upd = col.upd
    for r in col.uprows[j]:
        if alive[r] and not sat(cd, upd[r]):
            dead.append(r)
    cmp = kind != "nn" and kind != "nu"
    ch = col.chunks[j]
    pages = col.pages
    plain = col.plain
    lo = col.lo
    hi = col.hi
    for fi in range(col.first[j], col.end[j]):
        rows = [r for r in plain[fi] if alive[r]]
        if not rows:
            continue
        pg = pages[fi]
        s = hdr.settle(kind, v, pg.n, pg.nulls, lo[fi], hi[fi])
        if s > 0:
            continue
        if s < 0:
            dead.extend(rows)
            continue
        vals = col.vals[fi]
        if vals is None:
            if cmp and pg.form == "i":
                consult(col, j, out)
                g = st.good.get((cd.pos, j))
                if g is None:
                    g = dct.good(ch.dic, kind, v)
                    st.good[(cd.pos, j)] = g
                s = dct.settle(len(ch.dic), g, pg.nulls)
                if s > 0:
                    continue
                if s < 0:
                    dead.extend(rows)
                    continue
            vals = read(col, fi, out)
            live.recount(st, c, fi)
        dead.extend(fails(kind, v, vals, rows, pg.start))
    live.kill(st, dead)
