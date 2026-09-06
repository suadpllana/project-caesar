def table(pairs):
    idx = {}
    for k, v in pairs:
        idx.setdefault(k, []).append(v)
    return idx


def walk(h, idx, roots, skip):
    found = set()
    todo = [i for i in roots]
    while todo:
        i = todo.pop()
        if i in found or i in skip or i not in h.ob:
            continue
        found.add(i)
        for v in h.ob[i].fl.values():
            if v is not None:
                todo.append(v)
        for v in idx.get(i, ()):
            todo.append(v)
    return found


def cycle(h):
    idx = table(h.pr)

    bases = []
    for f in h.fr:
        for v in f.values():
            if v is not None:
                bases.append(v)
    standing = walk(h, idx, bases, frozenset())

    pending = sorted(i for i in h.ob
                 if i not in standing and h.ob[i].fz is not None
                 and i not in h.rn and i not in h.qu)

    spared = walk(h, idx, list(h.qu) + pending, standing)

    cleared = [n for n, w in h.wk.items() if not w.c and w.t not in standing]

    dropped = sorted(i for i in h.ob if i not in standing and i not in spared)
    return cleared, pending, dropped
