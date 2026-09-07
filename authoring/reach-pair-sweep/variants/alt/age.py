from mem import heap, rset


def promote(h, seen, held):
    moved = []
    for i in sorted(h.young):
        if i in held or i not in seen:
            continue
        o = h.objs[i]
        o.age += 1
        if o.age < heap.PROMOTE_AGE or o.pins:
            continue
        o.space = heap.OLD
        h.young.remove(i)
        for fld in sorted(o.flds):
            rset.note(h, i, fld, o.flds[fld])
        moved.append(i)
    return moved
