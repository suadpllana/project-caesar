"""What the step reports, read off the parallel placement lists."""


def report(cfg, sc, bufs, st, out, n):
    demand = [0] * cfg.ex
    for tid in range(n):
        experts, slots = st.place[tid]
        got = set(experts)
        res = 0
        for e in st.wl[tid]:
            demand[e] += 1
            if e not in got:
                res += sc[tid][e]
        pairs = " ".join("%d:%d" % (experts[i], slots[i]) for i in range(len(experts)))
        if pairs:
            out.line("tok %d %s res %d" % (tid, pairs, res))
        else:
            out.line("tok %d res %d" % (tid, res))

    total = 0
    for e in range(cfg.ex):
        total += demand[e] * bufs.count(e)
    out.line("bal %d" % total)
