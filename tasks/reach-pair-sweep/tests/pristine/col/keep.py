from col import scan
from mem import heap


def _scope(h, full):
    return [i for i in sorted(h.objs) if full or h.objs[i].space == heap.NURSERY]


def settle(h, seen, full):
    fresh = []
    while True:
        start = [i for i in h.queue if i in h.objs] + fresh
        held = scan.reach(h, start, full, frozenset(seen)) if start else set()
        more = [i for i in _scope(h, full)
                if i not in seen and i not in held and h.objs[i].fin is not None
                and i not in h.done and i not in h.queue and i not in fresh]
        if not more:
            return sorted(fresh), held
        fresh.append(more[0])
