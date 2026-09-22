from pg import fit


def edge(low, high):
    k = 0
    top = len(low) if len(low) < len(high) else len(high)
    while k < top and low[k] == high[k]:
        k += 1
    return high[:k + 1]


def ends(tr, pid, last):
    page = tr.at(pid)
    while not page.leaf:
        page = tr.at(page.kids[-1 if last else 0])
    if not page.keys:
        return None
    return page.keys[-1 if last else 0]


def kin(tr):
    """A parent map for the whole tree, rebuilt from the root each time it is wanted."""
    up = {}
    stack = [tr.root]
    while stack:
        pid = stack.pop()
        page = tr.at(pid)
        if page.leaf:
            continue
        for at, kid in enumerate(page.kids):
            up[kid] = (pid, at)
            stack.append(kid)
    return up


def side(tr, pid, left):
    up = kin(tr)
    while pid in up:
        host, at = up[pid]
        if left:
            if at > 0:
                return host, at - 1
        elif at < len(tr.at(host).seps):
            return host, at
        pid = host
    return None


def lgap(tr, spine, slot, d):
    return side(tr, spine[d], True)


def rgap(tr, spine, slot, d):
    return side(tr, spine[d], False)


def fix(tr, site, out):
    if site is None:
        return
    pid, at = site
    page = tr.at(pid)
    if at >= len(page.seps):
        return
    low = ends(tr, page.kids[at], True)
    high = ends(tr, page.kids[at + 1], False)
    if low is None or high is None:
        return
    want = edge(low, high)
    if page.seps[at] != want:
        page.seps[at] = want
        out.bound(pid, at, want)
