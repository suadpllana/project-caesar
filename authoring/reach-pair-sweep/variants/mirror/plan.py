from mem import heap, roots as rootsrc


def roots(h, full):
    listed = rootsrc.named(h)
    if full:
        return sorted(set(listed))

    objs = h.objs
    out = [i for i in listed if objs[i].space == heap.NURSERY]
    live = {}
    for entry in h.rset:
        owner, slotname, recorded = entry
        if (owner, slotname) in live:
            continue
        owner = objs.get(owner)
        now = owner.flds.get(slotname) if owner is not None else None
        cur = objs.get(now) if now is not None else None
        if cur is None or cur.space != heap.NURSERY:
            continue
        live[(owner, slotname)] = entry
        out.append(now)
    h.rset = set(live.values())
    return sorted(set(out))
