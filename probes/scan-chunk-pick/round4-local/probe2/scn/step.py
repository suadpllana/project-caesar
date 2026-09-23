"""What happens to a query's state when a row dies, a page is read or a
dictionary is consulted, and what applying a pending pair does."""

from scn import dct, live


def kill(st, r):
    """Row r dies: every chunk of a condition column holding it loses a live
    row, and the page it takes its value from loses one it supplies."""
    st.alive[r] = 0
    cols = st.mem.cols
    dirty = st.dirty
    for c in st.ccols:
        col = cols[c]
        j = col.rowchunk[r]
        st.livech[c][j] -= 1
        dirty.add((c, j))
        if r not in col.upd:
            pid = col.rowpid[r]
            lp = st.livepg[c]
            lp[pid] -= 1
            if lp[pid] == 0:
                sett = st.sett
                pend = st.pend
                for i in st.ccond[c]:
                    if not sett[i][pid]:
                        pend[i][j] -= 1


def settle(st, i, c, pid, j):
    """Condition i becomes settled for every row page pid supplies."""
    s = st.sett[i]
    if not s[pid]:
        s[pid] = 1
        if st.livepg[c][pid] > 0:
            st.pend[i][j] -= 1


def _kill_page(st, col, pg):
    alive = st.alive
    upd = col.upd
    for r in range(pg.start, pg.start + pg.n):
        if alive[r] and r not in upd:
            kill(st, r)


def read(st, c, pid, out):
    """Read a page during the conditions: its values become known, the count
    of every condition over its column becomes exact on it, and every row it
    supplies is settled for all of them."""
    col = st.mem.cols[c]
    pg = col.pages[pid]
    j = col.pchunk[pid]
    col.read[pid] = 1
    out.dc(c, j, pg.p)
    a = pg.start
    b = a + pg.n
    wv = col.wvals
    idx = st.ccond[c]
    conds = st.conds
    pend = st.pend
    for i in idx:
        if pend[i][j] > 0:
            cd = conds[i]
            e = live.exact(col, pid, cd.kind, cd.v)
            pc = st.pcnt[i]
            st.cnt[i][j] += e - pc[pid]
            pc[pid] = e
        settle(st, i, c, pid, j)
    st.dirty.add((c, j))
    alive = st.alive
    upd = col.upd
    ts = [st.tests[i] for i in idx]
    for r in range(a, b):
        if alive[r] and r not in upd:
            x = wv[r]
            for t in ts:
                if not t(x):
                    kill(st, r)
                    break


def consult(st, c, j, out):
    """Consult the dictionary of chunk j of column c during the conditions."""
    col = st.mem.cols[c]
    col.dknown[j] = 1
    out.rd(c, j)
    ch = col.chunks[j]
    m = len(ch.dic)
    conds = st.conds
    pages = col.pages
    for i in st.ccond[c]:
        if not st.comp[i]:
            continue
        cd = conds[i]
        ng = dct.good(ch, cd.kind, cd.v)
        s = st.sett[i]
        for pid in range(col.cfirst[j], col.cend[j]):
            pg = pages[pid]
            if pg.form != "i" or s[pid]:
                continue
            w = dct.verdict(ng, m, pg.nulls)
            if w == 0:
                continue
            settle(st, i, c, pid, j)
            if w < 0:
                _kill_page(st, col, pg)


def apply(st, i, j, out):
    """Apply the pending pair of condition i and chunk j of its column."""
    cd = st.conds[i]
    c = cd.c
    col = st.mem.cols[c]
    s = st.sett[i]
    lp = st.livepg[c]
    comp = st.comp[i]
    pages = col.pages
    for pid in range(col.cfirst[j], col.cend[j]):
        if s[pid] or lp[pid] == 0:
            continue
        if comp and pages[pid].form == "i" and not col.dknown[j]:
            consult(st, c, j, out)
            if s[pid] or lp[pid] == 0:
                continue
        read(st, c, pid, out)
