import heapq
from collections import defaultdict

from scn import hdr, live, rd, step


def run(seg, q, st, out):
    """Repeatedly apply the pending (condition, chunk) pair expected to
    leave the fewest rows alive - the smaller of the chunk's live rows and
    the condition's count on it, ties going to the earlier condition then
    the lower chunk - until nothing is pending.

    Selection is kept fast with one min-heap per condition, over its own
    chunks, keyed by the pair's current priority. A heap entry can go
    stale (the chunk's live count only ever drops; its exact-vs-guessed
    count can also move once a page of it is read) - staleness is caught
    lazily on pop and the entry is corrected and re-pushed, so every peek
    still returns the pair's true current priority. Comparing the (already
    up to date) top of each of the few per-query conditions' heaps then
    gives the overall best pair in place of rescanning every pending pair.
    """
    mem = st.mem

    by_colchunk = defaultdict(list)
    cc = {}
    heaps = {}
    for cd in q.conds:
        h = []
        for ch in seg.cols[cd.c]:
            key = (cd.pos, ch.j)
            cnt = step.chunk_count(seg, mem, ch, cd)
            cc[key] = cnt
            by_colchunk[(cd.c, ch.j)].append(cd)
            l = live.count(st, cd.c, ch.j)
            h.append((l if l < cnt else cnt, ch.j))
        heapq.heapify(h)
        heaps[cd.pos] = h

    pending = set(cc)
    cond_by_pos = {cd.pos: cd for cd in q.conds}
    cols = seg.cols

    def top(pos):
        h = heaps[pos]
        cd = cond_by_pos[pos]
        c_col = cd.c
        while h:
            val, j = h[0]
            if (pos, j) not in pending:
                heapq.heappop(h)
                continue
            l = live.count(st, c_col, j)
            c = cc[(pos, j)]
            true_val = l if l < c else c
            if true_val == val:
                return val, j
            heapq.heapreplace(h, (true_val, j))
        return None

    active = list(cond_by_pos)
    while pending:
        best = None
        best_pos = None
        best_j = None
        still = []
        for pos in active:
            t = top(pos)
            if t is None:
                continue
            still.append(pos)
            val, j = t
            if best is None or (val, pos, j) < best:
                best = (val, pos, j)
                best_pos = pos
                best_j = j
        active = still

        cd = cond_by_pos[best_pos]
        ch = cols[cd.c][best_j]
        newly_read, touched = step.apply_pair(seg, mem, st, cd, ch, out)
        pending.discard((best_pos, best_j))

        if newly_read:
            others = by_colchunk.get((cd.c, ch.j))
            if others:
                for pg in newly_read:
                    vals = mem.pages[(pg.c, pg.j, pg.p)]
                    for other in others:
                        opk = (other.pos, ch.j)
                        if opk not in pending:
                            continue
                        exact = 0
                        for v in vals:
                            if rd.sat(other, v):
                                exact += 1
                        cc[opk] += exact - hdr.guess(seg, pg, other)
                        l = live.count(st, other.c, ch.j)
                        c = cc[opk]
                        heapq.heappush(
                            heaps[other.pos], (l if l < c else c, ch.j)
                        )

        for c_col, j in touched:
            for other in by_colchunk.get((c_col, j), ()):
                opk = (other.pos, j)
                if opk not in pending:
                    continue
                l = live.count(st, c_col, j)
                c = cc[opk]
                heapq.heappush(heaps[other.pos], (l if l < c else c, j))
