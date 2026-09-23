import heapq
from bisect import bisect_left, bisect_right

from scn import hdr, live, rd, step


def _settle_updates(seg, q, st):
    """A row with an update in a condition's column never takes its value
    from any page, so its fate against that condition is known immediately,
    without any read."""
    for cd in q.conds:
        up = seg.up[cd.c]
        if not up:
            continue
        dead = [r for r, v in up.items() if r in st.alive and not rd.sat(cd, v)]
        if dead:
            live.kill(st, dead)


def _phase0(seg, q, st, mem, out):
    """Resolve every (condition, chunk) pair as far as the header alone can
    take it: rows a page's header already proves fail die right away, rows a
    page's header already proves pass need nothing further, and every page
    left ambiguous is recorded, together with the static guess count for its
    chunk. Returns (pending, guess): pending maps (cond.pos, chunk.j) to the
    list of its still-ambiguous pages; guess maps the same keys to the
    chunk's static "expected to leave alive" count."""
    pending = {}
    guess = {}
    for cd in q.conds:
        upd_sorted = mem.col_upd[cd.c]
        for ch in seg.cols[cd.c]:
            amb = []
            to_kill = []
            g = 0
            for pg in ch.pages:
                key = (pg.c, pg.j, pg.p)
                rv = mem.read_vals.get(key)
                if rv is not None:
                    g += sum(1 for v in rv if rd.sat(cd, v))
                else:
                    g += hdr.count(seg, pg, cd)
                if hdr.miss(seg, pg, cd):
                    to_kill.extend(step.eligible(pg, upd_sorted))
                elif hdr.allsat(seg, pg, cd):
                    pass
                else:
                    amb.append(pg)
            if to_kill:
                live.kill(st, to_kill)
            if amb:
                key2 = (cd.pos, ch.j)
                pending[key2] = amb
                guess[key2] = g
    return pending, guess


def _chunk_alive(seg, st, mem, cols):
    sorted_alive = sorted(st.alive)
    out = {}
    for c in cols:
        starts = mem.col_starts[c]
        ends = starts[1:] + [seg.n]
        counts = []
        for s, e in zip(starts, ends):
            lo = bisect_left(sorted_alive, s)
            hi = bisect_left(sorted_alive, e)
            counts.append(hi - lo)
        out[c] = counts
    return out


def run(seg, q, st, out):
    mem = st.mem

    _settle_updates(seg, q, st)
    pending, guess = _phase0(seg, q, st, mem, out)
    if not pending:
        return

    cond_by_pos = {cd.pos: cd for cd in q.conds}
    # only columns that actually have a pending pair need live tracking
    cols = sorted({cond_by_pos[pos].c for pos, _j in pending})
    conds_by_col = {}
    for cd in q.conds:
        conds_by_col.setdefault(cd.c, []).append(cd)

    chunk_alive = _chunk_alive(seg, st, mem, cols)

    current = {}
    heap = []
    for key, g in guess.items():
        pos, j = key
        cd = cond_by_pos[pos]
        live_n = chunk_alive[cd.c][j]
        p = live_n if live_n < g else g
        current[key] = p
        heap.append((p, pos, j))
    heapq.heapify(heap)

    while heap:
        p, pos, j = heapq.heappop(heap)
        key = (pos, j)
        if key not in pending or current.get(key) != p:
            continue
        cd = cond_by_pos[pos]
        ch = seg.cols[cd.c][j]
        pages = pending.pop(key)
        del current[key]

        upd_sorted = mem.col_upd[cd.c]
        dead_all = []
        for pg in pages:
            dead_all.extend(step.resolve_page(mem, cd, ch, pg, st.alive, upd_sorted, out))
        if not dead_all:
            continue
        actually_dead = live.kill(st, dead_all)
        if not actually_dead:
            continue

        touched = {}
        for c in cols:
            starts = mem.col_starts[c]
            cnt = {}
            for r in actually_dead:
                jj = bisect_right(starts, r) - 1
                cnt[jj] = cnt.get(jj, 0) + 1
            if cnt:
                touched[c] = cnt

        for c, cnt in touched.items():
            arr = chunk_alive[c]
            conds_here = conds_by_col.get(c, ())
            for jj, dcount in cnt.items():
                arr[jj] -= dcount
                new_live = arr[jj]
                for cd2 in conds_here:
                    key2 = (cd2.pos, jj)
                    if key2 in pending:
                        g2 = guess[key2]
                        np_ = new_live if new_live < g2 else g2
                        if current.get(key2) != np_:
                            current[key2] = np_
                            heapq.heappush(heap, (np_, cd2.pos, jj))
