import heapq

from scn import hdr, live, step


def run(seg, q, st, out):
    conds_by_col = {}
    for cd in q.conds:
        conds_by_col.setdefault(cd.c, []).append(cd)
    cond_cols = list(conds_by_col.keys())

    live.init_chunk_rows(seg, st, cond_cols)

    exact_cache = {}  # (cond.pos, chunk j) -> exact count, once a read fixes it
    done = set()  # (cond.pos, chunk j) pairs already applied

    def cur_count(cd, ch):
        v = exact_cache.get((cd.pos, ch.j))
        if v is not None:
            return v
        return hdr.guess(seg, ch, cd)

    heap = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            lc = len(st.chunk_rows[(cd.c, ch.j)])
            if lc > 0:
                heapq.heappush(heap, (min(lc, cur_count(cd, ch)), cd.pos, ch.j))

    while heap:
        score, pos, j = heapq.heappop(heap)
        if (pos, j) in done:
            continue
        cd = q.conds[pos]
        ch = seg.cols[cd.c][j]
        lc = len(st.chunk_rows[(cd.c, j)])
        if lc == 0:
            continue
        true_score = min(lc, cur_count(cd, ch))
        if true_score != score:
            # Stale: live rows shrank or a read since fixed the exact count.
            heapq.heappush(heap, (true_score, pos, j))
            continue

        done.add((pos, j))
        dead, read_happened = step.apply_pair(
            seg, st, cd, ch, out, conds_by_col, exact_cache
        )

        touched = live.kill_rows(st, dead, cond_cols) if dead else set()
        if read_happened:
            # A read settles the exact count for every condition of the
            # query on this column, on this chunk -- refresh them even if
            # nothing died.
            touched.add((cd.c, j))

        for tc, tj in touched:
            tlc = len(st.chunk_rows[(tc, tj)])
            if tlc == 0:
                continue
            tch = seg.cols[tc][tj]
            for cd2 in conds_by_col[tc]:
                if (cd2.pos, tj) in done:
                    continue
                heapq.heappush(heap, (min(tlc, cur_count(cd2, tch)), cd2.pos, tj))
