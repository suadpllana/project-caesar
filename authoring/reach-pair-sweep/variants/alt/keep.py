from col import scan
from mem import heap


def _in_scope(h, full):
    return sorted(h.objs) if full else sorted(h.young)


def settle(h, seen, full):
    objs = h.objs
    already = set(h.queue)
    fresh = []
    for i in _in_scope(h, full):
        o = objs[i]
        if i in seen or o.fin is None:
            continue
        if o.ser in h.done or i in already:
            continue
        fresh.append(i)

    roots = [i for i in h.queue if i in objs]
    roots.extend(fresh)
    if not full:
        roots = [i for i in roots if objs[i].space == heap.NURSERY]
    if not roots:
        return fresh, set()
    return fresh, scan.reach(h, roots, full, frozenset(seen))
