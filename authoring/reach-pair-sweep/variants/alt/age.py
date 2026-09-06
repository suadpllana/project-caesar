from mem import heap


def promote(h, seen, held):
    survivors = [i for i in sorted(h.objs)
                 if h.objs[i].space == heap.NURSERY and i in seen and i not in held]
    moved = []
    for i in survivors:
        o = h.objs[i]
        o.age += 1
        if o.pins == 0 and o.age >= heap.PROMOTE_AGE:
            o.space = heap.OLD
            moved.append(i)
    return moved
