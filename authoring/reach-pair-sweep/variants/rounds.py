def _fix(h, seed, blocked):
    got = frozenset(i for i in seed if i in h.ob and i not in blocked)
    while True:
        grew = set()
        for i in got:
            for v in h.ob[i].fl.values():
                if v is not None and v in h.ob and v not in blocked and v not in got:
                    grew.add(v)
        for k, v in h.pr:
            if k in got and v in h.ob and v not in blocked and v not in got:
                grew.add(v)
        if not grew:
            return got
        got = got | grew


def cycle(h):
    start = tuple(v for f in h.fr for v in f.values() if v is not None)
    live = _fix(h, start, frozenset())

    qd = tuple(i for i in sorted(h.ob)
               if i not in live and h.ob[i].fz is not None
               and i not in h.rn and i not in h.qu)

    hold = _fix(h, tuple(h.qu) + qd, live)

    cl = tuple(n for n in sorted(h.wk) if not h.wk[n].c and h.wk[n].t not in live)
    rl = tuple(i for i in sorted(h.ob) if i not in live and i not in hold)
    return cl, qd, rl
