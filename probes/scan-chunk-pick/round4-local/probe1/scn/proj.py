"""The report: one prj line per named column, reading only what it must."""


def _need(mem, pids, sup, dsingle):
    """Pages of one chunk the report must read, in page order.

    A supplied page can be skipped when what is known works out its part of
    the line: it is all null; its non-null values are one known value and
    either it holds no null or every row it holds is supplied; or it is
    wholly supplied and the chunk sum covers it, which needs every page of
    the chunk that supplies nothing to have a known sum.
    """
    read = mem.read
    pobj = mem.pobj
    plo = mem.plo
    phi = mem.phi
    pis = mem.pis
    blocked = False
    for pid in pids:
        if read[pid] or sup.get(pid):
            continue
        pg = pobj[pid]
        if pg.nulls >= pg.n:
            continue
        if plo[pid] == phi[pid]:
            continue
        if dsingle and pis[pid]:
            continue
        blocked = True
        break
    need = []
    for pid in pids:
        s = sup.get(pid)
        if not s or read[pid]:
            continue
        pg = pobj[pid]
        if pg.nulls >= pg.n:
            continue
        full = s == pg.n
        if plo[pid] == phi[pid] or (dsingle and pis[pid]):
            if full or pg.nulls == 0:
                continue
        elif full and not blocked:
            continue
        need.append(pid)
    return need


def report(seg, st, c, rows, out):
    mem = st.mem
    updc = mem.upd[c]
    rp = mem.rpage[c]
    sup = {}
    for r in rows:
        if not updc[r]:
            pid = rp[r]
            sup[pid] = sup.get(pid, 0) + 1
    if sup:
        pch = mem.pch
        pis = mem.pis
        pobj = mem.pobj
        for g in sorted({pch[pid] for pid in sup}):
            ch = mem.cobj[g]
            pids = mem.cpids[g]
            one = ch.enc == "d" and len(ch.dic) == 1
            known = mem.dknown[g]
            need = _need(mem, pids, sup, one and known)
            if need and one and not known:
                if any(pis[pid] and sup.get(pid) for pid in pids):
                    alt = _need(mem, pids, sup, True)
                    if len(alt) < len(need):
                        mem.dknown[g] = 1
                        out.rd(c, ch.j)
                        need = alt
            for pid in need:
                mem.read[pid] = 1
                pg = pobj[pid]
                out.dc(c, pg.j, pg.p)
    upv = seg.up[c]
    pvals = mem.pvals
    pobj = mem.pobj
    nn = 0
    tot = 0
    for r in rows:
        if updc[r]:
            v = upv[r]
        else:
            pid = rp[r]
            v = pvals[pid][r - pobj[pid].start]
        if v is not None:
            nn += 1
            tot += v
    out.prj(c, nn, tot)


def run(seg, q, st, rows, out):
    for c in q.cols:
        report(seg, st, c, rows, out)
