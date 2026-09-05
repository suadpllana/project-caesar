"""Reachability, tree order and the tab stops of the screen on top.

Everything here is a question about the tree as it is right now. The interesting part of
the task is in keep.py, which asks these questions later than the shipped code did; the
questions themselves are the ones the brief states outright.

A widget can take focus when it is still part of the tree, it sits on the screen on top,
it carries `foc`, and neither it nor any container above it is hidden, disabled or shut.
The shipped reach.py asked only the widget itself about its flags, which is the first of
the four corrections and the most legible one: a widget under a hidden container came
back as a stop.
"""

BLOCK = ("hid", "off", "shut")


def top(ui):
    return ui.st[-1] if ui.st else None


def alive(ui, nd):
    # A screen root is alive while its screen has not been popped; every other widget is
    # alive while the core still lists it. A dropped subtree and a popped screen are both
    # gone from that list, which is what makes the two cases one case in keep.py.
    if nd.par is None:
        return nd.scr.nm in ui.scr
    return nd.wid in ui.nd


def can(ui, nd):
    if not alive(ui, nd) or nd.scr is not top(ui) or "foc" not in nd.fl:
        return False
    cur = nd
    while cur is not None:
        if cur.fl & set(BLOCK):
            return False
        cur = cur.par
    return True


def order(ui):
    """Every widget of the screen on top, in pre-order, the root first."""
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
    """The composite a widget sits inside, or None. Composites do not nest."""
    cur = nd.par
    while cur is not None:
        if "comp" in cur.fl:
            return cur
        cur = cur.par
    return None


def inside(ui, comp):
    """The focusable descendants of a composite, in pre-order."""
    out = []

    def walk(nd):
        for k in nd.kids:
            if can(ui, k):
                out.append(k)
            walk(k)

    walk(comp)
    return out


def stops(ui):
    """The tab stops of the screen on top, in tree order.

    A composite is one stop, standing at its own position, as long as something inside
    it can take focus; nothing inside a composite is a stop in its own right. Of a group,
    the selected member is the stop when it can take focus, otherwise the first member
    that can. Everything else that can take focus is a stop.
    """
    ordr = order(ui)
    lead = {}
    for nd in ordr:
        if nd.grp is None or not can(ui, nd):
            continue
        if nd.grp not in lead or ("sel" in nd.fl and "sel" not in lead[nd.grp].fl):
            lead[nd.grp] = nd
    out = []
    skip = None
    for nd in ordr:
        if skip is not None:
            if nd is skip or under(nd, skip):
                continue
            skip = None
        if "comp" in nd.fl:
            if inside(ui, nd):
                out.append(nd)
            skip = nd
            continue
        if not can(ui, nd):
            continue
        if nd.grp is not None and lead.get(nd.grp) is not nd:
            continue
        out.append(nd)
    return out


def under(nd, anc):
    cur = nd.par
    while cur is not None:
        if cur is anc:
            return True
        cur = cur.par
    return False
