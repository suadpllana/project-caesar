from pg import fit


def strip(tr, pid, up, j, out):
    page = tr.at(up)
    if j < len(page.seps):
        del page.seps[j]
    elif page.seps:
        del page.seps[j - 1]
    del page.kids[j]
    tr.drop(pid)
    out.gone(pid)


def knit(tr, pid, up, j, out):
    page = tr.at(up)
    if j > 0:
        at = j - 1
    elif j + 1 < len(page.kids):
        at = j
    else:
        return
    a = page.kids[at]
    b = page.kids[at + 1]
    if fit.bulk(tr, a) + fit.bulk(tr, b) > tr.cap:
        return
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


def tidy(tr, out):
    while True:
        page = tr.at(tr.root)
        if page.leaf or len(page.kids) != 1:
            return
        kid = page.kids[0]
        tr.drop(tr.root)
        tr.root = kid
        out.fold(kid)
