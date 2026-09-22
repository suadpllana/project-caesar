def edge(low, high):
    return high


def mend(tr, spine, slot, out):
    if len(spine) < 2:
        return
    up = spine[-2]
    if up not in tr.pages:
        return
    page = tr.at(up)
    i = slot[-1]
    if i == 0 or i > len(page.seps) or i >= len(page.kids):
        return
    kid = tr.at(page.kids[i])
    if not kid.leaf or not kid.keys:
        return
    want = edge(None, kid.keys[0])
    if page.seps[i - 1] != want:
        page.seps[i - 1] = want
        out.bound(up, i - 1, want)
