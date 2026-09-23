import heapq

from scn import live, rd, step


def run(seg, q, st, out):
    mem = st.mem
    alive = st.alive

    # A row with an update in a condition's column has its value fully known up
    # front; settle it against that condition right away, no reads involved.
    for cond in q.conds:
        up = seg.up[cond.c]
        if not up:
            continue
        dead = [r for r, v in up.items() if alive[r] and not rd.sat(cond, v)]
        if dead:
            live.kill(st, dead)

    # Every (condition, chunk) combination starts as a pending pair. A pair's
    # count-of-condition only ever changes when a new page of its own chunk
    # gets read, so its value is cached against that chunk's read generation
    # and only recomputed when the generation has actually moved on.
    pairs = []
    heap = []
    count_cache = {}

    def current_count(idx, cond, ch):
        gen = live.gen_of(mem, ch.c, ch.j)
        cached = count_cache.get(idx)
        if cached is not None and cached[0] == gen:
            return cached[1]
        val = live.cond_count(seg, mem, cond, ch)
        count_cache[idx] = (gen, val)
        return val

    for cond in q.conds:
        for ch in seg.cols[cond.c]:
            idx = len(pairs)
            pairs.append((cond, ch))
            pri = min(live.live_count(st, cond.c, ch.j), current_count(idx, cond, ch))
            heapq.heappush(heap, (pri, cond.pos, ch.j, idx))

    # Repeatedly apply the pending pair expected to leave the fewest rows alive,
    # re-checking each candidate's true current value before accepting it (its
    # estimate may have moved since it was pushed).
    while heap:
        pri, pos, cj, idx = heapq.heappop(heap)
        cond, ch = pairs[idx]
        live_n = live.live_count(st, cond.c, ch.j)
        if live_n <= 0:
            continue
        cnt = current_count(idx, cond, ch)
        true_pri = live_n if live_n < cnt else cnt
        if true_pri != pri:
            heapq.heappush(heap, (true_pri, pos, cj, idx))
            continue
        step.apply(seg, st, cond, ch, out)
