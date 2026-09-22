import bisect

from pg import bound, cut, fit, join, seek


def sweep(tr, out):
    """Restore the invariant everywhere: work every dividing string in the tree out again."""
    stack = [tr.root]
    while stack:
        pid = stack.pop()
        page = tr.at(pid)
        if page.leaf:
            continue
        for at in range(len(page.seps)):
            bound.fix(tr, (pid, at), out)
        stack.extend(page.kids)


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
        sweep(tr, out)
        while d >= 0:
            if fit.over(tr, spine[d]):
                if d:
                    cut.cut(tr, spine[d], spine[d - 1], slot[d - 1], out)
                else:
                    cut.cut(tr, spine[d], None, 0, out)
            d -= 1
        return
    if not here:
        out.none(key)
        return
    del leaf.keys[i]
    out.rm(key, leaf.pid)
    sweep(tr, out)
    while d >= 1:
        pid = spine[d]
        if pid not in tr.pages:
            d -= 1
            continue
        page = tr.at(pid)
        if not (page.keys if page.leaf else page.kids):
            up = tr.at(spine[d - 1])
            join.strip(tr, pid, spine[d - 1], slot[d - 1], spine, slot, d, out)
            if up.kids:
                sweep(tr, out)
        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)
