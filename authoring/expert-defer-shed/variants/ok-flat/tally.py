"""The report, read off the dict of placements."""


def report(cfg, sc, bufs, st, out, n):
    demand = [0] * cfg.ex
    for tid in range(n):
        row = st.held(tid)
        got = frozenset(e for e, _slot in row)
        res = 0
        for e in st.wl[tid]:
            demand[e] += 1
            if e not in got:
                res += sc[tid][e]
        if row:
            out.line("tok %d %s res %d"
                     % (tid, " ".join("%d:%d" % p for p in row), res))
        else:
            out.line("tok %d res %d" % (tid, res))

    out.line("bal %d" % sum(demand[e] * bufs.count(e) for e in range(cfg.ex)))
