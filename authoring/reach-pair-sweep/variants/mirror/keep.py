from col import scan
from mem import heap


def inscope(h, full):
    return [i for i in sorted(h.objs) if full or h.objs[i].space == heap.NURSERY]


def settle(h, found, full):
    newly = [i for i in inscope(h, full)
             if i not in found and h.objs[i].fin is not None
             and i not in h.done and i not in h.queue]

    bases = [i for i in h.queue if i in h.objs] + newly
    if not full:
        bases = [i for i in bases if h.objs[i].space == heap.NURSERY]
    spared = scan.reach(h, bases, full, frozenset(found)) if bases else set()
    return newly, spared
