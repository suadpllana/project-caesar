BLOCK = ("hid", "off", "shut")


def top(ui):
    return ui.st[-1] if ui.st else None


def alive(ui, nd):
    if nd.par is None:
        return nd.scr.nm in ui.scr
    return nd.wid in ui.nd


def can(ui, nd):
    if not alive(ui, nd) or nd.scr is not top(ui) or "foc" not in nd.fl:
        return False
    return not (nd.fl & set(BLOCK))


def order(ui):
    s = top(ui)
    out = []
    if s is None:
        return out

    def walk(nd):
        out.append(nd)
        for k in nd.kids:
            walk(k)

    walk(s.root)
    return out


def within(nd):
    cur = nd.par
    while cur is not None:
        if "comp" in cur.fl:
            return cur
        cur = cur.par
    return None


def inside(ui, comp):
    out = []

    def walk(nd):
        for k in nd.kids:
            if can(ui, k):
                out.append(k)
            walk(k)

    walk(comp)
    return out


def stops(ui):
    out = []
    skip = None
    for nd in order(ui):
        if skip is not None:
            if nd is skip or under(nd, skip):
                continue
            skip = None
        if "comp" in nd.fl:
            if inside(ui, nd):
                out.append(nd)
            skip = nd
            continue
        if can(ui, nd):
            out.append(nd)
    return out


def under(nd, anc):
    cur = nd.par
    while cur is not None:
        if cur is anc:
            return True
        cur = cur.par
    return False
