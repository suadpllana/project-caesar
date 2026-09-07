from mem import heap


def wipe(h, seen, full):
    cleared = []
    for name in sorted(h.weak):
        ref = h.weak[name]
        if ref.wiped:
            continue
        at = h.objs.get(ref.tgt)
        if not full and (at is None or at.space != heap.NURSERY):
            continue
        if ref.tgt in seen:
            continue
        ref.wiped = True
        cleared.append(name)
    return cleared


def release(h, seen, held, full):
    where = sorted(h.objs) if full else sorted(h.young)
    return [i for i in where if i not in seen and i not in held]
