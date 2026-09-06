from mem import heap


def wipe(h, seen, full):
    out = []
    for name in sorted(h.weak):
        w = h.weak[name]
        if w.wiped:
            continue
        tgt = w.tgt
        if not full:
            if tgt not in h.objs or h.objs[tgt].space != heap.NURSERY:
                continue
        if tgt not in seen:
            w.wiped = True
            out.append(name)
    return out


def release(h, seen, held, full):
    scope = [i for i in sorted(h.objs) if full or h.objs[i].space == heap.NURSERY]
    return [i for i in scope if i not in seen and i not in held]
