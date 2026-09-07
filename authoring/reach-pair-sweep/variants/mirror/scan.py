from mem import heap


def _index(h):
    objs = h.objs
    idx = {}
    for p in h.pairs:
        k = objs.get(p.key)
        if k is None or k.ser != p.kser:
            continue
        idx.setdefault(p.key, []).append(p.val)
    return idx


def reach(h, bases, full, skip):
    idx = _index(h)
    todo = list(bases)
    if not full:
        for k, vs in idx.items():
            if h.objs[k].space == heap.OLD:
                todo.extend(vs)

    found = set()
    while todo:
        i = todo.pop()
        if i in found or i in skip or i not in h.objs:
            continue
        if not full and h.objs[i].space == heap.OLD:
            continue
        found.add(i)
        for v in h.objs[i].flds.values():
            if v is not None:
                todo.append(v)
        for v in idx.get(i, ()):
            todo.append(v)
    return found
