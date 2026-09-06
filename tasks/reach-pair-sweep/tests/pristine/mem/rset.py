from mem import heap


def note(h, src, fld, val):
    if src not in h.objs or h.objs[src].space != heap.OLD:
        return
    if val is None or val not in h.objs:
        return
    if h.objs[val].space == heap.NURSERY:
        h.rset.add((src, fld, val))


def forget(h, gone):
    for e in list(h.rset):
        if e[0] in gone:
            h.rset.discard(e)
