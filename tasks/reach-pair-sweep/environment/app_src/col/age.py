from mem import heap


def promote(h, seen, held):
    moved = []
    for i in sorted(h.objs):
        o = h.objs[i]
        if o.space != heap.NURSERY:
            continue
        if i not in seen and i not in held:
            continue
        o.age += 1
        if o.age >= heap.PROMOTE_AGE and o.pins == 0:
            o.space = heap.OLD
            moved.append(i)
    return moved
