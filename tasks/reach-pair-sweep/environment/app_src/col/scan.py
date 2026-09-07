from mem import heap


def _walk(h, start, full, barred):
    seen = set()
    stack = list(start)
    while stack:
        i = stack.pop()
        if i in seen or i in barred or i not in h.objs:
            continue
        if not full and h.objs[i].space == heap.OLD:
            continue
        seen.add(i)
        for v in h.objs[i].flds.values():
            if v is not None:
                stack.append(v)
    return seen


def reach(h, start, full, barred):
    seen = _walk(h, start, full, barred)
    while True:
        more = [p.val for p in h.pairs
                if p.key in seen and p.val in h.objs
                and p.val not in seen and p.val not in barred]
        if not more:
            return seen
        seen |= _walk(h, more, full, barred)
