from mem import heap, roots as rootsrc


def _current(h, src, fld):
    owner = h.objs.get(src)
    if owner is None:
        return None
    val = owner.flds.get(fld)
    target = h.objs.get(val) if val is not None else None
    if target is None or target.space != heap.NURSERY:
        return None
    return val


def roots(h, full):
    named = set(rootsrc.named(h))
    if full:
        return sorted(named)

    out = {i for i in named if h.objs[i].space == heap.NURSERY}
    surviving = {}
    for entry in h.rset:
        where = (entry[0], entry[1])
        if where in surviving:
            continue
        got = _current(h, entry[0], entry[1])
        if got is None:
            continue
        surviving[where] = entry
        out.add(got)
    h.rset = set(surviving.values())
    return sorted(out)
