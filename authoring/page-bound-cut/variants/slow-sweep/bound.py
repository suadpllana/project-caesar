from pg import fit


def edge(low, high):
    return high[:fit.share(low, high) + 1]


def least(tr, pid):
    page = tr.at(pid)
    while not page.leaf:
        page = tr.at(page.kids[0])
    return page.keys[0] if page.keys else None


def most(tr, pid):
    page = tr.at(pid)
    while not page.leaf:
        page = tr.at(page.kids[-1])
    return page.keys[-1] if page.keys else None


def lgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] > 0:
            return spine[k], slot[k] - 1
        k -= 1
    return None


def rgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] < len(tr.at(spine[k]).seps):
            return spine[k], slot[k]
        k -= 1
    return None


def fix(tr, site, out):
    if site is None:
        return
    pid, idx = site
    page = tr.at(pid)
    if idx >= len(page.seps):
        return
    low = most(tr, page.kids[idx])
    high = least(tr, page.kids[idx + 1])
    if low is None or high is None:
        return
    want = edge(low, high)
    if page.seps[idx] != want:
        page.seps[idx] = want
        out.bound(pid, idx, want)
