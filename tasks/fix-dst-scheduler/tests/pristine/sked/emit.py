RANK = {"end": 0, "skip": 1, "drop": 2, "start": 3}


def key(e):
    return (e.t, RANK[e.kind], e.job.prio)


def lines(evs):
    return ["%s %s %d %d" % (e.kind, e.job.jid, e.k, e.t) for e in sorted(evs, key=key)]
