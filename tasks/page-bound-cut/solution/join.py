from pg import bound, fit


def weigh(tr, a, b, mid):
    left = tr.at(a)
    right = tr.at(b)
    if left.leaf:
        ca, ta = fit.scan(left.keys)
        cb, tb = fit.scan(right.keys)
        if not ca + cb:
            return fit.span("", "", 0, 0, 0)
        first = left.keys[0] if ca else right.keys[0]
        last = right.keys[-1] if cb else left.keys[-1]
        return fit.span(first, last, ca + cb, ta + tb, 0)
    ca, ta = fit.scan(left.seps)
    cb, tb = fit.scan(right.seps)
    first = left.seps[0] if ca else mid
    last = right.seps[-1] if cb else mid
    return fit.span(first, last, ca + cb + 1, ta + tb + len(mid),
                    len(left.kids) + len(right.kids))


def fuse(tr, host, at, out):
    page = tr.at(host)
    a = page.kids[at]
    b = page.kids[at + 1]
    left = tr.at(a)
    right = tr.at(b)
    if left.leaf:
        left.keys.extend(right.keys)
    else:
        left.seps.append(page.seps[at])
        left.seps.extend(right.seps)
        left.kids.extend(right.kids)
    del page.seps[at]
    del page.kids[at + 1]
    tr.drop(b)
    out.join(a, b)


def knit(tr, pid, up, j, out):
    page = tr.at(up)
    if j + 1 < len(page.kids):
        if weigh(tr, pid, page.kids[j + 1], page.seps[j]) <= tr.cap:
            fuse(tr, up, j, out)
            return
    if j > 0:
        if weigh(tr, page.kids[j - 1], pid, page.seps[j - 1]) <= tr.cap:
            fuse(tr, up, j - 1, out)


def strip(tr, pid, up, j, spine, slot, d, out):
    page = tr.at(up)
    last = len(page.kids) - 1
    if 0 < j < last:
        site = (up, j - 1)
    elif j == 0:
        site = bound.lgap(tr, spine, slot, d - 1)
    else:
        site = bound.rgap(tr, spine, slot, d - 1)
    if j > 0:
        del page.seps[j - 1]
    elif page.seps:
        del page.seps[0]
    del page.kids[j]
    tr.drop(pid)
    out.gone(pid)
    if page.kids:
        bound.fix(tr, site, out)


def tidy(tr, out):
    while True:
        page = tr.at(tr.root)
        if page.leaf or len(page.kids) != 1:
            return
        kid = page.kids[0]
        tr.drop(tr.root)
        tr.root = kid
        out.fold(kid)
