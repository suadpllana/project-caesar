from mem import heap, roots as rootsrc


def _fresh_target(h, src, fld):
    if src not in h.objs:
        return None
    val = h.objs[src].flds.get(fld)
    if val is None or val not in h.objs:
        return None
    return val if h.objs[val].space == heap.NURSERY else None


def roots(h, full):
    named = set(rootsrc.named(h))
    if full:
        return sorted(named)
    out = {i for i in named if h.objs[i].space == heap.NURSERY}
    for src, fld, _was in h.rset:
        got = _fresh_target(h, src, fld)
        if got is not None:
            out.add(got)
    return sorted(out)
