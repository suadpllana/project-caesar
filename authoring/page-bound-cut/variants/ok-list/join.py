from pg import bound, fit


def weigh(tr, a, b, mid):
    left = tr.at(a)
    right = tr.at(b)
    if left.leaf:
        return fit.measure(left.keys + right.keys, 0)
    return fit.measure(left.seps + [mid] + right.seps,
                       len(left.kids) + len(right.kids))


def fuse(tr, host, at, out):
    page = tr.at(host)
    left = tr.at(page.kids[at])
    right = tr.at(page.kids[at + 1])
    if left.leaf:
        left.keys = left.keys + right.keys
    else:
        left.seps = left.seps + [page.seps[at]] + right.seps
        left.kids = left.kids + right.kids
    del page.seps[at]
    del page.kids[at + 1]
    tr.drop(right.pid)
    out.join(left.pid, right.pid)


def knit(tr, pid, up, j, out):
    page = tr.at(up)
    if j + 1 < len(page.kids) and weigh(tr, pid, page.kids[j + 1], page.seps[j]) <= tr.cap:
        fuse(tr, up, j, out)
        return
    if j > 0 and weigh(tr, page.kids[j - 1], pid, page.seps[j - 1]) <= tr.cap:
        fuse(tr, up, j - 1, out)


def strip(tr, pid, up, j, spine, slot, d, out):
    page = tr.at(up)
    if 0 < j < len(page.kids) - 1:
        site = (up, j - 1)
    elif j == 0:
        site = bound.side(tr, up, True)
    else:
        site = bound.side(tr, up, False)
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
    page = tr.at(tr.root)
    while not page.leaf and len(page.kids) == 1:
        kid = page.kids[0]
        tr.drop(tr.root)
        tr.root = kid
        out.fold(kid)
        page = tr.at(kid)
