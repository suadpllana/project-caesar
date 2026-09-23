from scn import dct, hdr, live, rd


def read_page(seg, mem, ch, pg, out):
    """Return pg's decoded, as-written values, reading (and printing) it the
    first time only."""
    key = (pg.c, pg.j, pg.p)
    vals = mem.pages.get(key)
    if vals is None:
        out.dc(pg.c, pg.j, pg.p)
        vals = rd.values(ch, pg)
        mem.pages[key] = vals
    return vals


def consult_dict(mem, ch, out):
    """Consult ch's dictionary, printing it the first time only."""
    key = (ch.c, ch.j)
    if key not in mem.dicts:
        out.rd(ch.c, ch.j)
        mem.dicts.add(key)


def page_count(seg, mem, pg, cond):
    """The count of `cond` over pg, exact if pg is already read, else the
    header's estimate."""
    vals = mem.pages.get((pg.c, pg.j, pg.p))
    if vals is not None:
        t = 0
        for v in vals:
            if rd.sat(cond, v):
                t += 1
        return t
    return hdr.guess(seg, pg, cond)


def chunk_count(seg, mem, ch, cond):
    return sum(page_count(seg, mem, pg, cond) for pg in ch.pages)


def apply_pair(seg, mem, st, cond, ch, out):
    """Apply the (cond, ch) pending pair: walk ch's pages in order and, for
    each page still holding a live row that takes its value from a page of
    this chunk without cond settled for it, settle it - via the header,
    then (for a comparison on an i page) the dictionary, then, if needed, an
    actual read. Rows with an update in cond's column are never touched
    here; they were already settled before any pair was picked.

    Returns (newly_read, touched): the pages that were read for the first
    time by this call (so the caller can refresh any other pending pair's
    cached count for those specific pages), and the set of (column,
    chunk-index) pairs whose live count changed (so the caller can refresh
    any other pending pair's priority for those chunks).
    """
    c = cond.c
    up = seg.up[c]
    alive = st.alive
    comparison = cond.kind not in ("nn", "nu")
    use_dict = comparison and dct.usable(ch)
    newly_read = []
    touched = set()
    for pg in ch.pages:
        lo = pg.start
        hi = lo + pg.n
        such = [r for r in range(lo, hi) if r in alive and r not in up]
        if not such:
            continue
        if hdr.miss(seg, pg, cond):
            touched.update(live.kill(st, such))
            continue
        if hdr.allsat(seg, pg, cond):
            continue
        settled = False
        if use_dict and pg.form == "i":
            consult_dict(mem, ch, out)
            verdict = dct.classify(cond, ch.dic)
            if verdict == "drop":
                touched.update(live.kill(st, such))
                settled = True
            elif verdict == "all" and pg.nulls == 0:
                settled = True
        if settled:
            continue
        key = (pg.c, pg.j, pg.p)
        was_known = key in mem.pages
        vals = read_page(seg, mem, ch, pg, out)
        if not was_known:
            newly_read.append(pg)
        dead = [r for r in such if not rd.sat(cond, vals[r - lo])]
        if dead:
            touched.update(live.kill(st, dead))
    return newly_read, touched
