import collections

from mem import heap, tables


def reach(h, start, full, barred):
    by = tables.by_key(h)
    q = collections.deque()
    seen = set()

    def offer(i):
        if i not in h.objs or i in seen or i in barred:
            return
        if not full and h.objs[i].space == heap.OLD:
            return
        q.append(i)

    for i in start:
        offer(i)
    if not full:
        for k, vs in by.items():
            if k in h.objs and h.objs[k].space == heap.OLD:
                for v in vs:
                    offer(v)
    while q:
        i = q.popleft()
        if i in seen:
            continue
        seen.add(i)
        for v in h.objs[i].flds.values():
            if v is not None:
                offer(v)
        for v in by.get(i, ()):
            offer(v)
    return seen
