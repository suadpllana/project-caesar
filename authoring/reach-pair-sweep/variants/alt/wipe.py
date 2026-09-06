from mem import heap


def _examined(h, tgt, full):
    if full:
        return True
    return tgt in h.objs and h.objs[tgt].space == heap.NURSERY


def wipe(h, seen, full):
    out = []
    for name in sorted(h.weak):
        w = h.weak[name]
        if w.wiped or not _examined(h, w.tgt, full):
            continue
        if w.tgt not in seen:
            w.wiped = True
            out.append(name)
    return out


def release(h, seen, held, full):
    out = []
    for i in sorted(h.objs):
        if not full and h.objs[i].space != heap.NURSERY:
            continue
        if i not in seen and i not in held:
            out.append(i)
    return out
