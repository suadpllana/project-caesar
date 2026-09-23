"""The scan's memory and the live rows of a query.

`fresh` builds, once per file, flat indexes of every column plus the one
memory of which pages have been read and which dictionaries consulted.
`start` opens a query: every row not deleted is alive, and every row that what
is already known shows failing a condition dies at once.
"""

from itertools import compress

from scn import dct, hdr


class Col:
    """One column, flattened: pages numbered across the column (gp)."""

    __slots__ = (
        # pages
        "pstart", "pend", "pn", "pu", "plo", "phi", "pi", "pj", "pp", "pvals", "pupd",
        # chunks
        "cfirst", "cstart", "cend", "cdic", "cone",
        # rows
        "pageof", "chunkof", "upd", "cur",
        # memory
        "read", "dk",
    )


class Mem:
    __slots__ = ("g", "n", "cols")


def _col(seg, c):
    g = seg.g
    n = seg.n
    col = Col()
    pstart, pend, pn, pu, plo, phi, pi, pj, pp, pvals = ([] for _ in range(10))
    cfirst, cstart, cend, cdic, cone = ([] for _ in range(5))
    pageof = [0] * n
    chunkof = [0] * n
    wval = [None] * n
    for ch in seg.cols[c]:
        cfirst.append(len(pstart))
        cstart.append(ch.start)
        cend.append(ch.start + ch.n)
        dic = ch.dic if ch.enc == "d" else None
        cdic.append(dic)
        cone.append(dic is not None and len(dic) == 1)
        chunkof[ch.start:ch.start + ch.n] = [ch.j] * ch.n
        for pg in ch.pages:
            gp = len(pstart)
            s = pg.start
            e = s + pg.n
            pstart.append(s)
            pend.append(e)
            pn.append(pg.n)
            pu.append(pg.nulls)
            lo, hi = hdr.bounds(g, pg)
            plo.append(lo)
            phi.append(hi)
            isi = pg.form == "i"
            pi.append(isi)
            pj.append(ch.j)
            pp.append(pg.p)
            if isi:
                vals = [None if t is None else dic[t] for t in pg.toks]
            else:
                vals = list(pg.toks)
            pvals.append(vals)
            pageof[s:e] = [gp] * pg.n
            wval[s:e] = vals
    cfirst.append(len(pstart))
    col.pstart, col.pend, col.pn, col.pu, col.plo, col.phi = pstart, pend, pn, pu, plo, phi
    col.pi, col.pj, col.pp, col.pvals = pi, pj, pp, pvals
    col.cfirst, col.cstart, col.cend, col.cdic, col.cone = cfirst, cstart, cend, cdic, cone
    col.pageof = pageof
    col.chunkof = chunkof
    upd = bytearray(n)
    cur = list(wval)
    pupd = {}
    for r, v in seg.up[c].items():
        if not 0 <= r < n:
            continue
        upd[r] = 1
        cur[r] = v
        pupd.setdefault(pageof[r], []).append(r)
    col.pupd = pupd
    col.upd = upd
    col.cur = cur
    col.read = bytearray(len(pstart))
    col.dk = bytearray(len(cstart))
    return col


def fresh(seg):
    mem = Mem()
    mem.g = seg.g
    mem.n = seg.n
    mem.cols = [_col(seg, c) for c in range(seg.k)]
    return mem


class State:
    __slots__ = (
        "seg", "mem", "out", "alive",
        "kind", "ccol", "cval", "cmp", "colconds", "condcols",
        "unset", "est", "cnt", "U", "L", "livech", "dirty", "test",
    )


def _passer(st, c):
    """A test for one column: does a value pass every condition of the query on it?"""
    ks = [(st.kind[i], st.cval[i]) for i in st.colconds[c]]

    def ok(v):
        for k, cv in ks:
            if not hdr.sat(k, cv, v):
                return False
        return True

    return ok


def _clear(alive, col, gp):
    """Every row the page supplies its own value to dies (updated rows keep their fate)."""
    s = col.pstart[gp]
    e = col.pend[gp]
    keep = col.pupd.get(gp)
    saved = [(r, alive[r]) for r in keep] if keep else None
    alive[s:e] = bytes(e - s)
    if saved:
        for r, a in saved:
            alive[r] = a


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.out = None
    n = seg.n
    alive = bytearray(b"\x01") * n
    for r in seg.gone:
        if 0 <= r < n:
            alive[r] = 0
    st.alive = alive
    conds = q.conds
    st.kind = [cd.kind for cd in conds]
    st.ccol = [cd.c for cd in conds]
    st.cval = [cd.v for cd in conds]
    st.cmp = [cd.kind in hdr.CMP for cd in conds]
    colconds = {}
    for i, cd in enumerate(conds):
        colconds.setdefault(cd.c, []).append(i)
    st.colconds = colconds
    st.condcols = list(colconds)
    st.test = {c: _passer(st, c) for c in colconds}

    # What is known before anything is done: updates, headers, pages already
    # read and dictionaries already consulted.  Every row it shows failing dies.
    st.unset = unset = []
    st.est = est = []
    for i, cd in enumerate(conds):
        kind, c, cv = cd.kind, cd.c, cd.v
        col = mem.cols[c]
        np_ = len(col.pstart)
        us = bytearray(np_)
        es = [0] * np_
        pstart, pend, pn, pu, plo, phi = col.pstart, col.pend, col.pn, col.pu, col.plo, col.phi
        pi, pj, read, dk, cdic, upd = col.pi, col.pj, col.read, col.dk, col.cdic, col.upd
        iscmp = kind in hdr.CMP
        for gp in range(np_):
            if read[gp]:
                vals = col.pvals[gp]
                es[gp] = hdr.exact(kind, cv, vals)
                s = pstart[gp]
                for x, v in enumerate(vals):
                    r = s + x
                    if alive[r] and not upd[r] and not hdr.sat(kind, cv, v):
                        alive[r] = 0
                continue
            lo = plo[gp]
            hi = phi[gp]
            es[gp] = hdr.estimate(kind, cv, pn[gp], pu[gp], lo, hi)
            v = hdr.settle(kind, cv, pn[gp], pu[gp], lo, hi)
            if v < 0 and iscmp and pi[gp] and dk[pj[gp]]:
                v = dct.settle(kind, cv, cdic[pj[gp]], pu[gp])
            if v == 0:
                _clear(alive, col, gp)
            elif v < 0:
                us[gp] = 1
        for r, v in seg.up[c].items():
            if 0 <= r < n and not hdr.sat(kind, cv, v):
                alive[r] = 0
        unset.append(us)
        est.append(es)

    # Live rows per chunk and live rows each page supplies, for every column a
    # condition reads; then the pending rows and the count of each pair.
    st.L = {}
    st.livech = {}
    for c in colconds:
        col = mem.cols[c]
        cnt_ = alive.count
        L = [cnt_(1, s, e) for s, e in zip(col.pstart, col.pend)]
        for gp, rs in col.pupd.items():
            for r in rs:
                if alive[r]:
                    L[gp] -= 1
        st.L[c] = L
        st.livech[c] = [cnt_(1, s, e) for s, e in zip(col.cstart, col.cend)]
    st.U = U = []
    st.cnt = cnt = []
    for i, cd in enumerate(conds):
        col = mem.cols[cd.c]
        L = st.L[cd.c]
        us = unset[i]
        es = est[i]
        cf = col.cfirst
        u_ = []
        k_ = []
        for j in range(len(cf) - 1):
            a = cf[j]
            b = cf[j + 1]
            t = 0
            for gp in range(a, b):
                if us[gp]:
                    t += L[gp]
            u_.append(t)
            k_.append(sum(es[a:b]))
        U.append(u_)
        cnt.append(k_)
    st.dirty = {c: set() for c in colconds}
    return st


def kill(st, r):
    """Row r dies: every count that included it drops."""
    st.alive[r] = 0
    cols = st.mem.cols
    for c in st.condcols:
        col = cols[c]
        j = col.chunkof[r]
        st.livech[c][j] -= 1
        st.dirty[c].add(j)
        if not col.upd[r]:
            gp = col.pageof[r]
            st.L[c][gp] -= 1
            for i in st.colconds[c]:
                if st.unset[i][gp]:
                    st.U[i][j] -= 1


def rows(st):
    return list(compress(range(len(st.alive)), st.alive))
