"""Applying one pending pair: consulting a dictionary, reading pages."""

from scn import dct, hdr, live

UNS = live.UNS
PASS = live.PASS
FAIL = live.FAIL
READ = live.READ


def pending(st, pos, g):
    stat = st.status[pos]
    livepg = st.livepg
    for pid in st.mem.cpids[g]:
        if stat[pid] == UNS and livepg[pid]:
            return True
    return False


def consult(st, g, out):
    mem = st.mem
    mem.dknown[g] = 1
    ch = mem.cobj[g]
    out.rd(ch.c, ch.j)
    conds = st.q.conds
    pis = mem.pis
    pobj = mem.pobj
    dead = []
    for pos in st.colconds.get(ch.c, ()):
        cd = conds[pos]
        s = dct.verdict(cd, ch.dic)
        if s == UNS:
            continue
        stat = st.status[pos]
        updc = mem.upd[ch.c]
        for pid in mem.cpids[g]:
            if not pis[pid] or stat[pid] != UNS:
                continue
            pg = pobj[pid]
            if s == FAIL:
                stat[pid] = FAIL
                b = pg.start
                dead.extend(r for r in range(b, b + pg.n) if not updc[r])
            elif pg.nulls == 0:
                stat[pid] = PASS
    if dead:
        live.kill(st, dead)


def read(st, pid, out):
    mem = st.mem
    mem.read[pid] = 1
    pg = mem.pobj[pid]
    c = pg.c
    out.dc(c, pg.j, pg.p)
    g = mem.pch[pid]
    vals = mem.pvals[pid]
    s = pg.start
    alive = st.alive
    updc = mem.upd[c]
    lo = mem.plo[pid]
    hi = mem.phi[pid]
    conds = st.q.conds
    dead = []
    for pos in st.colconds.get(c, ()):
        cd = conds[pos]
        st.status[pos][pid] = READ
        b = hdr.bad(cd.kind, cd.v, vals)
        st.cnt[pos][g] += (len(vals) - len(b)) - hdr.spread(cd.kind, cd.v, pg.n, pg.nulls, lo, hi)
        for i in b:
            r = s + i
            if alive[r] and not updc[r]:
                dead.append(r)
    st.dirty.add(g)
    if dead:
        live.kill(st, dead)


def apply(st, pos, g, out):
    mem = st.mem
    cd = st.q.conds[pos]
    stat = st.status[pos]
    livepg = st.livepg
    cmp_ = cd.kind in dct.CMP
    pis = mem.pis
    for pid in mem.cpids[g]:
        if stat[pid] != UNS or not livepg[pid]:
            continue
        if cmp_ and pis[pid] and not mem.dknown[g]:
            consult(st, g, out)
            if stat[pid] != UNS or not livepg[pid]:
                continue
        read(st, pid, out)
