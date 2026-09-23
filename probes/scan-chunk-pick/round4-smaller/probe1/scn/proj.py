from scn import hdr, live


def run(seg, q, st, rows, out):
    mem = st.mem
    for c in q.cols:
        nn, tot = _column(seg, mem, st, c, out)
        out.prj(c, nn, tot)


def _column(seg, mem, st, c, out):
    nn_total = 0
    tot_total = 0
    for ch in seg.cols[c]:
        nn, tot = _chunk(seg, mem, st, c, ch, out)
        nn_total += nn
        tot_total += tot
    # Rows updated in this column never take their value from a page; their
    # value is simply the update, always fully known.
    alive = st.alive
    for r, v in seg.up[c].items():
        if alive[r] and v is not None:
            nn_total += 1
            tot_total += v
    return nn_total, tot_total


def _chunk_clean(st, c, ch):
    return st.live_chunk_count[c][ch.j] == ch.n and st.up_counts[c][ch.j] == 0


def _supply_count(seg, st, c, pg):
    up = seg.up[c]
    alive = st.alive
    n = 0
    for r in range(pg.start, pg.start + pg.n):
        if alive[r] and r not in up:
            n += 1
    return n


def _classify(seg, mem, st, c, ch, dict_val):
    """A per-page plan for this chunk's contribution to a projected column c,
    as a list of (kind, page, nn, tot, as_written_sum) in page order, with
    kind in {"free", "poison", "mandatory", "deferred"}. dict_val is the
    chunk's sole dictionary entry to assume known, or None to ignore it."""
    tmp = []
    poison = 0
    swing = []
    for pg in ch.pages:
        cached = live.page_known(mem, ch, pg)
        if cached is not None:
            # Already read (this query or an earlier one): its exact values
            # are known outright, no shortcut or fresh read is involved.
            nn = 0
            tot = 0
            aw = 0
            up = seg.up[c]
            alive = st.alive
            base = pg.start
            for i, v in enumerate(cached):
                if v is None:
                    continue
                aw += v
                r = base + i
                if alive[r] and r not in up:
                    nn += 1
                    tot += v
            tmp.append(("free", pg, nn, tot, aw))
            continue
        if pg.mn is None:
            tmp.append(("free", pg, 0, 0, 0))
            continue
        supply = _supply_count(seg, st, c, pg)
        lo, hi = hdr.bounds(seg, pg)
        val = lo if lo == hi else None
        if val is None and pg.form == "i" and dict_val is not None and len(ch.dic) == 1:
            val = dict_val
        if val is not None:
            nnp_written = pg.n - pg.nulls
            aw = val * nnp_written
            if pg.nulls == 0 or supply == pg.n:
                nn = supply if pg.nulls == 0 else nnp_written
                tmp.append(("free", pg, nn, val * nn, aw))
                continue
            if supply == 0:
                tmp.append(("free", pg, 0, 0, aw))
                continue
            tmp.append(("mandatory", pg, None, None, None))
            continue
        if supply == 0:
            poison += 1
            tmp.append(("poison", pg, 0, 0, None))
            continue
        if supply == pg.n:
            swing.append(pg)
            tmp.append(("swing", pg, None, None, None))
            continue
        tmp.append(("mandatory", pg, None, None, None))

    deferred = swing[-1] if (poison == 0 and swing) else None
    plan = []
    for kind, pg, nn, tot, aw in tmp:
        if kind == "swing":
            kind = "deferred" if pg is deferred else "mandatory"
        plan.append((kind, pg, nn, tot, aw))
    return plan


def _read_count(plan):
    return sum(1 for kind, _pg, _nn, _tot, _aw in plan if kind == "mandatory")


def _execute(seg, mem, st, c, ch, plan, out):
    up = seg.up[c]
    alive = st.alive
    nn_total = 0
    tot_total = 0
    known_aw = 0
    deferred_pg = None
    for kind, pg, nn, tot, aw in plan:
        if kind == "free":
            nn_total += nn
            tot_total += tot
            known_aw += aw
        elif kind == "poison":
            pass
        elif kind == "deferred":
            deferred_pg = pg
        else:  # mandatory
            vals = live.ensure_page(mem, ch, pg, out)
            base = pg.start
            for i, v in enumerate(vals):
                if v is None:
                    continue
                known_aw += v
                r = base + i
                if alive[r] and r not in up:
                    nn_total += 1
                    tot_total += v
    if deferred_pg is not None:
        aw = ch.sum - known_aw
        nnp = deferred_pg.n - deferred_pg.nulls
        nn_total += nnp
        tot_total += aw
    return nn_total, tot_total


def _chunk(seg, mem, st, c, ch, out):
    if _chunk_clean(st, c, ch):
        nulls = sum(pg.nulls for pg in ch.pages)
        return ch.n - nulls, ch.sum

    without = _classify(seg, mem, st, c, ch, None)
    plan = without
    if ch.enc == "d" and len(ch.dic) == 1:
        if live.dict_known(mem, ch):
            plan = _classify(seg, mem, st, c, ch, ch.dic[0])
        else:
            withd = _classify(seg, mem, st, c, ch, ch.dic[0])
            if _read_count(withd) < _read_count(without):
                live.ensure_dict(mem, ch, out)
                plan = withd

    return _execute(seg, mem, st, c, ch, plan, out)
