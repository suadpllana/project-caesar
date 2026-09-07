from mem import heap, rset


def promote(h, found, spared):
    shifted = []
    for i in sorted(h.young):
        o = h.objs[i]
        if i not in found or i in spared:
            continue
        o.age += 1
        if o.age >= heap.PROMOTE_AGE and o.pins == 0:
            o.space = heap.OLD
            h.young.discard(i)
            for slotname, now in sorted(o.flds.items()):
                rset.note(h, i, slotname, now)
            shifted.append(i)
    return shifted
