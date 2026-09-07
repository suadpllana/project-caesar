from col import scan
from mem import heap


def inscope(h, full):
    return sorted(h.objs) if full else sorted(h.young)


def settle(h, found, full):
    objs = h.objs
    queued = set(h.queue)
    newly = [i for i in inscope(h, full)
             if i not in found and objs[i].fin is not None
             and objs[i].ser not in h.done and i not in queued]

    bases = [i for i in h.queue if i in objs] + newly
    if not full:
        bases = [i for i in bases if objs[i].space == heap.NURSERY]
    spared = scan.reach(h, bases, full, frozenset(found)) if bases else set()
    return newly, spared
