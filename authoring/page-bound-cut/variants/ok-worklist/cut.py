from pg import bound, fit


def parent_base(tr, up):
    if up is None:
        def fresh(sep):
            return fit.frame(sep, sep, 1, len(sep), 2)
        return fresh
    page = tr.at(up)
    seps = page.seps
    count, total = (len(seps), sum(len(x) for x in seps))
    kids = len(page.kids)
    if count:
        base = fit.frame(seps[0], seps[-1], count, total, kids)
    else:
        base = fit.frame("", "", 0, 0, kids)

    def grown(sep):
        first = seps[0] if count else sep
        last = seps[-1] if count else sep
        if sep < first:
            first = sep
        if sep > last:
            last = sep
        return fit.frame(first, last, count + 1, total + len(sep), kids + 1) - base

    return grown


def leaf_plan(tr, page, up):
    keys = page.keys
    n = len(keys)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + len(keys[i])
    adds = parent_base(tr, up)
    best = None
    for i in range(1, n):
        sep = bound.edge(keys[i - 1], keys[i])
        left = fit.frame(keys[0], keys[i - 1], i, pre[i], 0)
        right = fit.frame(keys[i], keys[n - 1], n - i, pre[n] - pre[i], 0)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan(tr, page, up):
    seps = page.seps
    n = len(seps)
    m = len(page.kids)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + len(seps[i])
    adds = parent_base(tr, up)
    best = None
    for i in range(n):
        sep = seps[i]
        if i:
            left = fit.frame(seps[0], seps[i - 1], i, pre[i], i + 1)
        else:
            left = fit.frame("", "", 0, 0, 1)
        rest = n - i - 1
        if rest:
            right = fit.frame(seps[i + 1], seps[n - 1], rest, pre[n] - pre[i + 1], m - i - 1)
        else:
            right = fit.frame("", "", 0, 0, m - i - 1)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def cut(tr, pid, up, j, out):
    page = tr.at(pid)
    if page.leaf:
        if len(page.keys) < 2:
            return
        pos, sep = leaf_plan(tr, page, up)
        mate = tr.grab(True)
        mate.keys = page.keys[pos:]
        page.keys = page.keys[:pos]
    else:
        if not page.seps:
            return
        pos, sep = twig_plan(tr, page, up)
        mate = tr.grab(False)
        mate.kids = page.kids[pos + 1:]
        mate.seps = page.seps[pos + 1:]
        page.kids = page.kids[:pos + 1]
        page.seps = page.seps[:pos]
    fit.wipe(pid)
    fit.wipe(mate.pid)
    out.cut(pid, mate.pid, pos, sep)
    if up is None:
        top = tr.grab(False)
        top.kids = [pid, mate.pid]
        top.seps = [sep]
        tr.root = top.pid
        fit.wipe(top.pid)
        out.root(top.pid)
        up, j = top.pid, 0
    else:
        host = tr.at(up)
        host.kids.insert(j + 1, mate.pid)
        host.seps.insert(j, sep)
        fit.wipe(host.pid)
