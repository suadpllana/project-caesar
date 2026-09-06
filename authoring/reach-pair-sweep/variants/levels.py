def _grow(h, idx, seed, skip):
    got = set()
    front = {i for i in seed if i in h.ob and i not in skip}
    while front:
        got |= front
        nxt = set()
        for i in front:
            for v in h.ob[i].fl.values():
                if v is not None and v in h.ob and v not in skip and v not in got:
                    nxt.add(v)
            for v in idx.get(i, ()):
                if v in h.ob and v not in skip and v not in got:
                    nxt.add(v)
        front = nxt
    return got


def cycle(h):
    idx = {}
    for k, v in h.pr:
        idx.setdefault(k, []).append(v)

    roots = [v for f in h.fr for v in f.values() if v is not None]
    standing = _grow(h, idx, roots, frozenset())

    pending = sorted(i for i in h.ob
                     if i not in standing and h.ob[i].fz is not None
                     and i not in h.rn and i not in h.qu)

    spared = _grow(h, idx, list(h.qu) + pending, standing)

    cleared = [n for n, w in h.wk.items() if not w.c and w.t not in standing]
    dropped = sorted(i for i in h.ob if i not in standing and i not in spared)
    return cleared, pending, dropped
