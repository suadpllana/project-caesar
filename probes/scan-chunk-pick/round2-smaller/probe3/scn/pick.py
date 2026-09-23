import bisect
import heapq

from scn import dct, hdr, rd, step


def _by_column(conds):
    m = {}
    for pos, cd in enumerate(conds):
        m.setdefault(cd.c, []).append(pos)
    return m


def _live_count(alive, ch):
    return sum(alive[ch.start:ch.start + ch.n])


def _exact_count(cond, ch):
    n = 0
    for v in rd.values(ch):
        if rd.sat(cond, v):
            n += 1
    return n


def _apply(seg, st, cond, ch, out):
    c = cond.c
    up = seg.up[c]
    alive = st.alive
    lo, hi = ch.start, ch.start + ch.n
    own_rows = []
    dead = []
    for r in range(lo, hi):
        if not alive[r]:
            continue
        if r in up:
            if not rd.sat(cond, up[r]):
                dead.append(r)
        else:
            own_rows.append(r)

    did_read = False
    if own_rows:
        if hdr.miss(seg, ch, cond):
            dead.extend(own_rows)
        elif hdr.allsat(seg, ch, cond):
            pass
        else:
            key = (c, ch.j)
            vals = st.vals.get(key)
            handled = False
            if vals is None and cond.kind not in ("nn", "nu") and dct.usable(ch):
                verdict = dct.decide(seg, ch, cond, st, out)
                if verdict == "drop":
                    dead.extend(own_rows)
                    handled = True
                elif verdict == "keep":
                    handled = True
            if not handled:
                if vals is None:
                    vals = step.load(seg, st, ch, out)
                    did_read = True
                s = ch.start
                for r in own_rows:
                    if not rd.sat(cond, vals[r - s]):
                        dead.append(r)

    for r in dead:
        alive[r] = 0
    return did_read


def run(seg, q, st, out):
    conds = q.conds
    if not conds:
        return
    by_col = _by_column(conds)
    starts = {c2: [ch.start for ch in seg.cols[c2]] for c2 in by_col}
    cc = st.cond_count
    alive = st.alive
    done = st.done

    for pos, cd in enumerate(conds):
        counts = cc[pos]
        for ch in seg.cols[cd.c]:
            counts[ch.j] = hdr.guess(seg, ch, cd)

    heap = []
    last = [{} for _ in conds]
    for pos, cd in enumerate(conds):
        counts = cc[pos]
        for ch in seg.cols[cd.c]:
            lc = _live_count(alive, ch)
            if lc <= 0:
                continue
            cnt = counts[ch.j]
            score = lc if lc < cnt else cnt
            last[pos][ch.j] = score
            heap.append((score, pos, ch.j))
    heapq.heapify(heap)

    def touch(lo, hi):
        for c2, positions in by_col.items():
            chunks2 = seg.cols[c2]
            st2 = starts[c2]
            idx = bisect.bisect_right(st2, lo) - 1
            if idx < 0:
                idx = 0
            m = len(chunks2)
            jx = idx
            while jx < m and chunks2[jx].start < hi:
                ch2 = chunks2[jx]
                j2 = ch2.j
                lc2 = None
                for pos2 in positions:
                    if j2 in done[pos2]:
                        continue
                    if lc2 is None:
                        lc2 = _live_count(alive, ch2)
                        if lc2 <= 0:
                            break
                    cnt2 = cc[pos2][j2]
                    score2 = lc2 if lc2 < cnt2 else cnt2
                    if last[pos2].get(j2) == score2:
                        continue
                    last[pos2][j2] = score2
                    heapq.heappush(heap, (score2, pos2, j2))
                jx += 1

    while heap:
        score, pos, j = heapq.heappop(heap)
        if j in done[pos]:
            continue
        if last[pos].get(j) != score:
            continue
        cd = conds[pos]
        ch = seg.cols[cd.c][j]
        if _live_count(alive, ch) <= 0:
            continue
        did_read = _apply(seg, st, cd, ch, out)
        done[pos].add(j)
        if did_read:
            for pos2 in by_col.get(cd.c, ()):
                if pos2 == pos or j in done[pos2]:
                    continue
                cc[pos2][j] = _exact_count(conds[pos2], ch)
        touch(ch.start, ch.start + ch.n)
