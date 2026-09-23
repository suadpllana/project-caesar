from bisect import bisect_left

from scn import dct, step


def _sum_pairs(vals, idx):
    """(count of non-null, sum of non-null) over the given local indexes."""
    nn = 0
    tot = 0
    for i in idx:
        v = vals[i]
        if v is not None:
            nn += 1
            tot += v
    return nn, tot


def _sum_all(vals):
    nn = 0
    tot = 0
    for v in vals:
        if v is not None:
            nn += 1
            tot += v
    return nn, tot


def _page_elig(pg, rows_sorted, upd_sorted):
    """The alive rows this page supplies: alive and carrying no update
    override for the page's column."""
    lo, hi = pg.start, pg.start + pg.n
    a = bisect_left(rows_sorted, lo)
    b = bisect_left(rows_sorted, hi)
    elig = rows_sorted[a:b]
    if upd_sorted and elig:
        u = bisect_left(upd_sorted, lo)
        v = bisect_left(upd_sorted, hi)
        if u < v:
            skip = set(upd_sorted[u:v])
            elig = [r for r in elig if r not in skip]
    return elig


def _shortcut(mem, ch, pg, elig):
    """Try to settle this page without reading it. Returns
    (live_nn, live_tot, full_nn, full_tot) or None."""
    eac = len(elig)
    clean = eac == pg.n
    single_value = pg.exact and pg.mn is not None and pg.mn == pg.mx
    single_dict = pg.form == "i" and dct.usable(ch) and len(ch.dic) == 1 and dct.known(mem, ch)
    if not (single_value or single_dict):
        return None
    x = pg.mn if single_value else ch.dic[0]
    if pg.nulls == 0:
        return eac, eac * x, pg.n, pg.n * x
    if clean:
        nn = pg.n - pg.nulls
        return nn, nn * x, nn, nn * x
    return None


def _dict_would_help(mem, ch, pg, elig):
    if pg.form != "i" or not dct.usable(ch) or len(ch.dic) != 1 or dct.known(mem, ch):
        return False
    eac = len(elig)
    return pg.nulls == 0 or eac == pg.n


def _resolve_chunk(seg, mem, ch, rows_sorted, upd_sorted, out):
    live_nn = 0
    live_tot = 0
    full = {}
    pending = []  # (pg, elig, eac)
    dict_helps = False

    for pg in ch.pages:
        key = (pg.c, pg.j, pg.p)
        rv = mem.read_vals.get(key)
        if rv is not None:
            elig = _page_elig(pg, rows_sorted, upd_sorted)
            nn, tot = _sum_pairs(rv, [r - pg.start for r in elig])
            live_nn += nn
            live_tot += tot
            full[pg.p] = _sum_all(rv)
            continue
        elig = _page_elig(pg, rows_sorted, upd_sorted)
        got = _shortcut(mem, ch, pg, elig)
        if got is not None:
            nn, tot, fnn, ftot = got
            live_nn += nn
            live_tot += tot
            full[pg.p] = (fnn, ftot)
            continue
        if _dict_would_help(mem, ch, pg, elig):
            dict_helps = True
        pending.append((pg, elig, len(elig)))

    if dict_helps:
        dct.consult(mem, ch, out)
        still = []
        for pg, elig, eac in pending:
            got = _shortcut(mem, ch, pg, elig)
            if got is not None:
                nn, tot, fnn, ftot = got
                live_nn += nn
                live_tot += tot
                full[pg.p] = (fnn, ftot)
            else:
                still.append((pg, elig, eac))
        pending = still

    must_read = [p for p in pending if p[2] > 0 and p[2] != p[0].n]
    clean_pending = [p for p in pending if p[2] == p[0].n]
    zero_pending = [p for p in pending if p[2] == 0]

    elim_page = None
    if len(clean_pending) == 1:
        elim_page = clean_pending[0][0]
        must_read = must_read + zero_pending
    else:
        must_read = must_read + clean_pending

    must_read.sort(key=lambda p: p[0].p)
    for pg, elig, _eac in must_read:
        vals = step.ensure_read(ch, pg, mem, out)
        nn, tot = _sum_pairs(vals, [r - pg.start for r in elig])
        live_nn += nn
        live_tot += tot
        full[pg.p] = _sum_all(vals)

    if elim_page is not None:
        other = sum(ftot for p, (fnn, ftot) in full.items())
        tot_full = ch.sum - other
        nn_full = elim_page.n - elim_page.nulls
        live_nn += nn_full
        live_tot += tot_full

    return live_nn, live_tot


def _column(seg, st, c, rows_sorted, out):
    mem = st.mem
    nn = 0
    tot = 0
    up = seg.up[c]
    if up:
        alive = st.alive
        for r, v in up.items():
            if v is not None and r in alive:
                nn += 1
                tot += v
    upd_sorted = mem.col_upd[c]
    for ch in seg.cols[c]:
        cnn, ctot = _resolve_chunk(seg, mem, ch, rows_sorted, upd_sorted, out)
        nn += cnn
        tot += ctot
    return nn, tot


def run(seg, q, st, rows, out):
    cache = {}
    for c in q.cols:
        got = cache.get(c)
        if got is None:
            got = _column(seg, st, c, rows, out)
            cache[c] = got
        out.prj(c, got[0], got[1])
