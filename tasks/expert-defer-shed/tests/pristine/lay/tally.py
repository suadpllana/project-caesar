def report(cfg, weights, bufs, st, out, n):
    for token in range(n):
        where = st.place[token]
        got = set(e for e, _slot in where)
        res = 0
        for e in range(cfg.ex):
            if e not in got:
                res += weights[token][e]
        parts = " ".join("%d:%d" % (e, slot) for e, slot in where)
        if parts:
            out.line("tok %d %s res %d" % (token, parts, res))
        else:
            out.line("tok %d res %d" % (token, res))

    bal = 0
    for e in range(cfg.ex):
        bal += bufs.count(e) * bufs.count(e)
    out.line("bal %d" % bal)
