from pg import bound, fit


def above(tr, up, j, sep):
    if up is None:
        return fit.measure([sep], 2)
    page = tr.at(up)
    grown = page.seps[:j] + [sep] + page.seps[j:]
    return fit.measure(grown, len(page.kids) + 1) - fit.measure(page.seps, len(page.kids))


def cut(tr, pid, up, j, out):
    page = tr.at(pid)
    best = None
    if page.leaf:
        keys = page.keys
        n = len(keys)
        if n < 2:
            return
        for i in range(1, n):
            sep = bound.edge(keys[i - 1], keys[i])
            a = fit.measure(keys[:i], 0)
            b = fit.measure(keys[i:], 0)
            cost = (a if a > b else b) + above(tr, up, j, sep)
            if best is None or (cost, i) < best[0]:
                best = ((cost, i), i, sep)
        pos, sep = best[1], best[2]
        mate = tr.grab(True)
        mate.keys = keys[pos:]
        page.keys = keys[:pos]
    else:
        seps = page.seps
        n = len(seps)
        m = len(page.kids)
        if not n:
            return
        for i in range(n):
            sep = seps[i]
            a = fit.measure(seps[:i], i + 1)
            b = fit.measure(seps[i + 1:], m - i - 1)
            cost = (a if a > b else b) + above(tr, up, j, sep)
            if best is None or (cost, i) < best[0]:
                best = ((cost, i), i, sep)
        pos, sep = best[1], best[2]
        mate = tr.grab(False)
        mate.kids = page.kids[pos + 1:]
        mate.seps = seps[pos + 1:]
        page.kids = page.kids[:pos + 1]
        page.seps = seps[:pos]
    out.cut(pid, mate.pid, pos, sep)
    if up is None:
        top = tr.grab(False)
        top.kids = [pid, mate.pid]
        top.seps = [sep]
        tr.root = top.pid
        out.root(top.pid)
    else:
        host = tr.at(up)
        host.kids.insert(j + 1, mate.pid)
        host.seps.insert(j, sep)
