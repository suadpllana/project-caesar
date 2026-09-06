from mem import heap, roots as rootsrc


def roots(h, full):
    listed = rootsrc.named(h)
    if full:
        return sorted(set(listed))

    out = [i for i in listed if h.objs[i].space == heap.NURSERY]
    for owner, slotname, recorded in sorted(h.rset):
        if owner not in h.objs:
            continue
        now = h.objs[owner].flds.get(slotname)
        if now is None or now not in h.objs:
            continue
        if h.objs[now].space == heap.NURSERY:
            out.append(now)
    return sorted(set(out))
