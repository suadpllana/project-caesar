"""The file's memory, and the state of one query over it."""

from itertools import compress

from scn import dct, hdr, rd

UNS = 0
PASS = 1
FAIL = 2
READ = 3


class Mem:
    __slots__ = (
        "seg",
        "pobj", "pch", "plo", "phi", "pis", "pvals",
        "cobj", "cpids", "ccol", "cbase",
        "rpage", "rchunk", "upd",
        "read", "dknown",
    )


class State:
    __slots__ = (
        "seg", "mem", "q", "alive",
        "colconds", "kcols",
        "livech", "livepg",
        "status", "cnt", "key", "done", "dirty",
    )


def fresh(seg):
    m = Mem()
    m.seg = seg
    pobj = []
    pch = []
    plo = []
    phi = []
    pis = []
    pvals = []
    cobj = []
    cpids = []
    ccol = []
    cbase = []
    rpage = []
    rchunk = []
    for c in range(seg.k):
        cbase.append(len(cobj))
        rp = []
        rc = []
        for ch in seg.cols[c]:
            g = len(cobj)
            cobj.append(ch)
            ccol.append(c)
            ids = []
            for pg in ch.pages:
                pid = len(pobj)
                ids.append(pid)
                pobj.append(pg)
                pch.append(g)
                lo, hi = hdr.bounds(seg, pg)
                plo.append(lo)
                phi.append(hi)
                pis.append(pg.form == "i")
                pvals.append(rd.values(ch, pg))
                rp.extend([pid] * pg.n)
                rc.extend([g] * pg.n)
            cpids.append(ids)
        rpage.append(rp)
        rchunk.append(rc)
    upd = []
    for c in range(seg.k):
        b = bytearray(seg.n)
        for r in seg.up[c]:
            b[r] = 1
        upd.append(b)
    m.pobj = pobj
    m.pch = pch
    m.plo = plo
    m.phi = phi
    m.pis = pis
    m.pvals = pvals
    m.cobj = cobj
    m.cpids = cpids
    m.ccol = ccol
    m.cbase = cbase
    m.rpage = rpage
    m.rchunk = rchunk
    m.upd = upd
    m.read = bytearray(len(pobj))
    m.dknown = bytearray(len(cobj))
    return m


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.q = q
    n = seg.n
    alive = bytearray(b"\x01") * n
    for r in seg.gone:
        if 0 <= r < n:
            alive[r] = 0
    st.alive = alive

    colconds = {}
    for cd in q.conds:
        colconds.setdefault(cd.c, []).append(cd.pos)
    st.colconds = colconds

    npg = len(mem.pobj)
    nch = len(mem.cobj)
    pobj = mem.pobj
    plo = mem.plo
    phi = mem.phi
    pis = mem.pis
    pvals = mem.pvals
    pch = mem.pch
    read = mem.read
    dknown = mem.dknown
    cobj = mem.cobj
    cpids = mem.cpids
    cbase = mem.cbase

    status = []
    cnt = []
    for cd in q.conds:
        c = cd.c
        kind = cd.kind
        v = cd.v
        up = seg.up[c]
        updc = mem.upd[c]
        stat = bytearray(npg)
        cn = [0] * nch
        for r, x in up.items():
            if not rd.sat(cd, x):
                alive[r] = 0
        g0 = cbase[c]
        for g in range(g0, g0 + len(seg.cols[c])):
            tot = 0
            dic = cobj[g].dic
            dk = dknown[g]
            for pid in cpids[g]:
                pg = pobj[pid]
                s = pg.start
                if read[pid]:
                    stat[pid] = READ
                    vals = pvals[pid]
                    b = hdr.bad(kind, v, vals)
                    tot += len(vals) - len(b)
                    for i in b:
                        r = s + i
                        if not updc[r]:
                            alive[r] = 0
                    continue
                lo = plo[pid]
                hi = phi[pid]
                tot += hdr.spread(kind, v, pg.n, pg.nulls, lo, hi)
                t = hdr.settle(kind, v, pg.n, pg.nulls, lo, hi)
                if t == UNS and dk and pis[pid]:
                    t = dct.settle(cd, dic, pg.nulls)
                stat[pid] = t
                if t == FAIL:
                    for r in range(s, s + pg.n):
                        if not updc[r]:
                            alive[r] = 0
            cn[g] = tot
        status.append(stat)
        cnt.append(cn)
    st.status = status
    st.cnt = cnt

    livech = [0] * nch
    livepg = [0] * npg
    kcols = []
    for c in colconds:
        g0 = cbase[c]
        for g in range(g0, g0 + len(seg.cols[c])):
            ch = cobj[g]
            livech[g] = alive[ch.start:ch.start + ch.n].count(1)
            for pid in cpids[g]:
                pg = pobj[pid]
                livepg[pid] = alive[pg.start:pg.start + pg.n].count(1)
        rp = mem.rpage[c]
        for r in seg.up[c]:
            if alive[r]:
                livepg[rp[r]] -= 1
        kcols.append((mem.rchunk[c], rp, mem.upd[c]))
    st.livech = livech
    st.livepg = livepg
    st.kcols = kcols
    st.key = [None] * len(q.conds)
    st.done = [None] * len(q.conds)
    st.dirty = set()
    return st


def kill(st, dead):
    alive = st.alive
    livech = st.livech
    livepg = st.livepg
    dirty = st.dirty
    kcols = st.kcols
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for rc, rp, up in kcols:
                g = rc[r]
                livech[g] -= 1
                dirty.add(g)
                if not up[r]:
                    livepg[rp[r]] -= 1


def rows(st):
    return list(compress(range(len(st.alive)), st.alive))
