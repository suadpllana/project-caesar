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
                bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
            elif i == len(leaf.keys) - 1:
                bound.fix(tr, bound.rgap(tr, spine, slot, d), out)
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
    was_low = i == 0
    was_high = i == len(leaf.keys) - 1
    del leaf.keys[i]
    out.rm(key, leaf.pid)
    if leaf.keys:
        if was_low:
            bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
        elif was_high:
            bound.fix(tr, bound.rgap(tr, spine, slot, d), out)
    while d >= 1:
        pid = spine[d]
        if pid not in tr.pages:
            d -= 1
            continue
        page = tr.at(pid)
        if not (page.keys if page.leaf else page.kids):
            join.strip(tr, pid, spine[d - 1], slot[d - 1], spine, slot, d, out)
        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)
