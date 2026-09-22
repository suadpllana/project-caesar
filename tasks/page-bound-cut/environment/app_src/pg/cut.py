from pg import bound


def cut(tr, d, spine, slot, out):
    pid = spine[d]
    page = tr.at(pid)
    if page.leaf:
        pos = len(page.keys) // 2
        if pos < 1:
            return
        sep = bound.edge(page.keys[pos - 1], page.keys[pos])
        right = tr.grab(True)
        right.keys = page.keys[pos:]
        page.keys = page.keys[:pos]
    else:
        if not page.seps:
            return
        pos = (len(page.kids) - 1) // 2
        sep = page.seps[pos]
        right = tr.grab(False)
        right.kids = page.kids[pos + 1:]
        right.seps = page.seps[pos + 1:]
        page.kids = page.kids[:pos + 1]
        page.seps = page.seps[:pos]
    out.cut(pid, right.pid, pos, sep)
    if pid == tr.root:
        top = tr.grab(False)
        top.kids = [pid, right.pid]
        top.seps = [sep]
        tr.root = top.pid
        out.root(top.pid)
    else:
        up = tr.at(spine[d - 1])
        i = slot[d - 1]
        up.kids.insert(i + 1, right.pid)
        up.seps.insert(i, sep)
