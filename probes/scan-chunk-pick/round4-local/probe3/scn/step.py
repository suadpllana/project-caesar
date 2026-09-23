"""Applying one pending pair, and the two ways of learning something new.

Applying a pair takes the chunk's pages in order.  For each page still holding a
live row that takes its value from it without the condition settled: for a
comparison on an `i` page whose dictionary is not yet consulted, the dictionary
is consulted; then, if such a row remains, the page is read.  A row dies the
moment what is known shows it failing any condition of the query.
"""

from scn import dct, hdr, live


def consult(st, c, j, out):
    """Consult the dictionary of chunk j of column c; settle what it settles."""
    col = st.mem.cols[c]
    out.rd(c, j)
    col.dk[j] = 1
    dic = col.cdic[j]
    alive = st.alive
    L = st.L.get(c)
    for i in st.colconds.get(c, ()):
        if not st.cmp[i]:
            continue
        kind = st.kind[i]
        cv = st.cval[i]
        us = st.unset[i]
        Ui = st.U[i]
        k = dct.good(kind, cv, dic)
        for gp in range(col.cfirst[j], col.cfirst[j + 1]):
            if not (col.pi[gp] and us[gp]):
                continue
            if k == 0:
                us[gp] = 0
                Ui[j] -= L[gp]
                upd = col.upd
                for r in range(col.pstart[gp], col.pend[gp]):
                    if alive[r] and not upd[r]:
                        live.kill(st, r)
            elif k == len(dic) and col.pu[gp] == 0:
                us[gp] = 0
                Ui[j] -= L[gp]


def read(st, c, gp, out):
    """Read page gp of column c: its values, exact counts, and the rows they kill."""
    col = st.mem.cols[c]
    j = col.pj[gp]
    out.dc(c, j, col.pp[gp])
    col.read[gp] = 1
    vals = col.pvals[gp]
    conds = st.colconds.get(c)
    if not conds:
        return
    L = st.L[c]
    for i in conds:
        x = hdr.exact(st.kind[i], st.cval[i], vals)
        es = st.est[i]
        if x != es[gp]:
            st.cnt[i][j] += x - es[gp]
            es[gp] = x
        us = st.unset[i]
        if us[gp]:
            us[gp] = 0
            st.U[i][j] -= L[gp]
    st.dirty[c].add(j)
    alive = st.alive
    upd = col.upd
    ok = st.test[c]
    s = col.pstart[gp]
    for x, v in enumerate(vals):
        r = s + x
        if alive[r] and not upd[r] and not ok(v):
            live.kill(st, r)


def apply(st, i, j, out):
    c = st.ccol[i]
    col = st.mem.cols[c]
    us = st.unset[i]
    L = st.L[c]
    ask = st.cmp[i]
    for gp in range(col.cfirst[j], col.cfirst[j + 1]):
        if not (us[gp] and L[gp] > 0):
            continue
        if ask and col.pi[gp] and not col.dk[j]:
            consult(st, c, j, out)
            if not (us[gp] and L[gp] > 0):
                continue
        read(st, c, gp, out)
