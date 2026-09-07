from mem import heap


def _rows(h):
    live = {}
    for p in h.pairs:
        at = h.objs.get(p.key)
        if at is not None and at.ser == p.kser:
            live.setdefault(p.key, []).append(p.val)
    return live


def reach(h, start, full, barred):
    rows = _rows(h)
    objs = h.objs

    def admits(i):
        if i not in objs or i in barred:
            return False
        return full or objs[i].space == heap.NURSERY

    frontier = {i for i in start if admits(i)}
    if not full:
        for key, vals in rows.items():
            if objs[key].space == heap.OLD:
                frontier.update(v for v in vals if admits(v))

    seen = set()
    while frontier:
        seen |= frontier
        nxt = set()
        for i in frontier:
            for v in objs[i].flds.values():
                if v is not None and v not in seen and admits(v):
                    nxt.add(v)
            for v in rows.get(i, ()):
                if v not in seen and admits(v):
                    nxt.add(v)
        frontier = nxt
    return seen
