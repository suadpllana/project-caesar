import bisect

from pg import bound, cut, fit, join, seek


def one(tr, kind, key, out):
    spine, slot = seek.down(tr, key)
    d = len(spine) - 1
    leaf = tr.at(spine[d])
    i = bisect.bisect_left(leaf.keys, key)
    here = i < len(leaf.keys) and leaf.keys[i] == key
    if kind == "put":
        if here:
            out.dup(key)
            return
        leaf.keys.insert(i, key)
        out.add(key, leaf.pid)
        if len(leaf.keys) > 1:
            if i == 0:
                bound.fix(tr, bound.side(tr, leaf.pid, True), out)
            elif i == len(leaf.keys) - 1:
                bound.fix(tr, bound.side(tr, leaf.pid, False), out)
        for at in range(d, -1, -1):
            pid = spine[at]
            if fit.over(tr, pid):
                cut.cut(tr, pid, spine[at - 1] if at else None, slot[at - 1] if at else 0, out)
        return
    if not here:
        out.none(key)
        return
    low = i == 0
    high = i == len(leaf.keys) - 1
    del leaf.keys[i]
    out.rm(key, leaf.pid)
    if leaf.keys:
        if low:
            bound.fix(tr, bound.side(tr, leaf.pid, True), out)
        elif high:
            bound.fix(tr, bound.side(tr, leaf.pid, False), out)
    for at in range(d, 0, -1):
        pid = spine[at]
        if pid not in tr.pages:
            continue
        page = tr.at(pid)
        if not (page.keys if page.leaf else page.kids):
            join.strip(tr, pid, spine[at - 1], slot[at - 1], spine, slot, at, out)
        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[at - 1], slot[at - 1], out)
    join.tidy(tr, out)
