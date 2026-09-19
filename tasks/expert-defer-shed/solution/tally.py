"""What the step reports once the shed has run.

The residual of a token is what its want list asked for and did not get, so it is read off the
want list as it finally stands rather than off the ranking or off the list the token started
with - a deferred token's list is not the one it was first given.

The balance number pairs demand with supply: for each expert, how many tokens finally wanted
it against how many placements it kept. Demand is not the count taken before placement began,
because being refused makes a token want more.
"""


def report(cfg, weights, bufs, st, out, n):
    wanted = [0] * cfg.ex
    for token in range(n):
        where = st.place[token]
        got = set(e for e, _slot in where)
        res = 0
        for e in st.wl[token]:
            wanted[e] += 1
            if e not in got:
                res += weights[token][e]
        parts = " ".join("%d:%d" % (e, slot) for e, slot in where)
        if parts:
            out.line("tok %d %s res %d" % (token, parts, res))
        else:
            out.line("tok %d res %d" % (token, res))

    bal = 0
    for e in range(cfg.ex):
        bal += wanted[e] * bufs.count(e)
    out.line("bal %d" % bal)
