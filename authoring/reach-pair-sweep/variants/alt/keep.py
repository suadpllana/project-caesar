from col import scan
from mem import heap


def settle(h, seen, full):
    in_scope = {i for i in h.objs if full or h.objs[i].space == heap.NURSERY}
    fresh = sorted(i for i in in_scope
                   if i not in seen and h.objs[i].fin is not None
                   and i not in h.done and i not in h.queue)
    start = [i for i in list(h.queue) + fresh if i in in_scope or (full and i in h.objs)]
    if not start:
        return fresh, set()
    return fresh, scan.reach(h, start, full, frozenset(seen))
