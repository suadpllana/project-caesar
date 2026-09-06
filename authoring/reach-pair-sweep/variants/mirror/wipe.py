from mem import heap


def wipe(h, found, full):
    out = []
    for name in sorted(h.weak):
        w = h.weak[name]
        if w.wiped:
            continue
        referent = w.tgt
        if not full:
            if referent not in h.objs or h.objs[referent].space != heap.NURSERY:
                continue
        if referent not in found:
            w.wiped = True
            out.append(name)
    return out


def release(h, found, spared, full):
    inrange = [i for i in sorted(h.objs) if full or h.objs[i].space == heap.NURSERY]
    return [i for i in inrange if i not in found and i not in spared]
