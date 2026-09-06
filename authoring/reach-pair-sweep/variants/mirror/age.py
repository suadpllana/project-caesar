from mem import heap


def promote(h, found, spared):
    shifted = []
    for i in sorted(h.objs):
        o = h.objs[i]
        if o.space != heap.NURSERY:
            continue
        if i not in found or i in spared:
            continue
        o.age += 1
        if o.age >= heap.PROMOTE_AGE and o.pins == 0:
            o.space = heap.OLD
            shifted.append(i)
    return shifted
