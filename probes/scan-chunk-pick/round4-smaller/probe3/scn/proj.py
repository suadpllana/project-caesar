from scn import hdr, live, step


def run(seg, q, st, rows, out):
    mem = st.mem
    cache = {}
    for c in q.cols:
        got = cache.get(c)
        if got is None:
            got = _project(seg, mem, rows, c, out)
            cache[c] = got
        nn, tot = got
        out.prj(c, nn, tot)


def _project(seg, mem, rows, c, out):
    up = seg.up[c]
    chunks = seg.cols[c]
    nn = 0
    tot = 0

    if not chunks:
        for r in rows:
            if r in up:
                v = up[r]
                if v is not None:
                    nn += 1
                    tot += v
        return nn, tot

    o = live.own(mem, seg, c)
    groups = [[] for _ in chunks]
    for r in rows:
        if r in up:
            v = up[r]
            if v is not None:
                nn += 1
                tot += v
        else:
            groups[o[r]].append(r)

    for ch in chunks:
        grp = groups[ch.j]
        if not grp:
            continue
        a, b = _chunk_project(seg, mem, ch, grp, out)
        nn += a
        tot += b
    return nn, tot


def _bounds_single(seg, pg):
    lo, hi = hdr.bounds(seg, pg)
    if lo is not None and lo == hi:
        return lo
    return None


def _dict_single(ch):
    if ch.enc == "d" and len(ch.dic) == 1:
        return ch.dic[0]
    return None


def _single_val(seg, ch, pg):
    v = _bounds_single(seg, pg)
    if v is not None:
        return v
    if pg.form == "i":
        return _dict_single(ch)
    return None


def _sum_vals(vals):
    a = 0
    b = 0
    for v in vals:
        if v is not None:
            a += 1
            b += v
    return a, b


def _contribute(seg, ch, pg, grp):
    """(nn, sum) for grp's rows on this (unread) page, or None if a read
    is required to know it."""
    if not grp:
        return 0, 0
    if pg.nulls == pg.n:
        return 0, 0
    if pg.nulls == 0:
        v = _single_val(seg, ch, pg)
        if v is not None:
            return len(grp), v * len(grp)
        return None
    if len(grp) == pg.n:
        v = _single_val(seg, ch, pg)
        if v is not None:
            n = pg.n - pg.nulls
            return n, v * n
        return None
    return None


def _page_total(seg, ch, pg):
    """(nn, sum) over all of this (unread) page's rows as written, or None
    if a read is required to know it."""
    if pg.nulls == pg.n:
        return 0, 0
    v = _single_val(seg, ch, pg)
    if v is not None:
        n = pg.n - pg.nulls
        return n, v * n
    return None


def _chunk_project(seg, mem, ch, groups_j, out):
    pages = ch.pages
    npg = len(pages)

    # Bucket the needed rows (sorted, all within this chunk) by page.
    groups = [[] for _ in range(npg)]
    idx = 0
    n = len(groups_j)
    for i, pg in enumerate(pages):
        hi = pg.start + pg.n
        bucket = groups[i]
        while idx < n and groups_j[idx] < hi:
            bucket.append(groups_j[idx])
            idx += 1

    # Consult the dictionary only if some i page that supplies a needed
    # row, and isn't already resolved by its own bounds, would be spared
    # a read by knowing the (single) dictionary entry.
    if ch.enc == "d" and len(ch.dic) == 1:
        want = False
        for i, pg in enumerate(pages):
            if pg.form != "i" or not groups[i]:
                continue
            if _bounds_single(seg, pg) is not None:
                continue
            if pg.nulls == 0 or len(groups[i]) == pg.n:
                want = True
                break
        if want:
            step.consult_dict(mem, ch, out)

    contributions = [None] * npg
    totals = [None] * npg
    need_read = []
    for i, pg in enumerate(pages):
        key = (pg.c, pg.j, pg.p)
        vals = mem.pages.get(key)
        if vals is not None:
            totals[i] = _sum_vals(vals)
            contributions[i] = _contrib_from_vals(vals, pg, groups[i])
            continue
        contributions[i] = _contribute(seg, ch, pg, groups[i])
        t = _page_total(seg, ch, pg)
        if t is not None:
            totals[i] = t
        if contributions[i] is None:
            need_read.append(i)

    blocked = any(totals[i] is None and not groups[i] for i in range(npg))
    dedupe = None
    if need_read and not blocked:
        last = need_read[-1]
        if len(groups[last]) == pages[last].n:
            dedupe = last

    nn_tot = 0
    sum_tot = 0
    for i, pg in enumerate(pages):
        grp = groups[i]
        if contributions[i] is not None:
            a, b = contributions[i]
            nn_tot += a
            sum_tot += b
            continue
        if i == dedupe:
            known_sum = 0
            for j in range(npg):
                if j != i:
                    known_sum += totals[j][1]
            deduced = ch.sum - known_sum
            cnt = pg.n - pg.nulls
            totals[i] = (cnt, deduced)
            nn_tot += cnt
            sum_tot += deduced
            continue
        vals = step.read_page(seg, mem, ch, pg, out)
        totals[i] = _sum_vals(vals)
        a, b = _contrib_from_vals(vals, pg, grp)
        nn_tot += a
        sum_tot += b
    return nn_tot, sum_tot


def _contrib_from_vals(vals, pg, grp):
    a = 0
    b = 0
    start = pg.start
    for r in grp:
        v = vals[r - start]
        if v is not None:
            a += 1
            b += v
    return a, b
