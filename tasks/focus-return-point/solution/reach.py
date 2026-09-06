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
    # alive while the core still lists that instance, not merely its reusable id.
    # A dropped subtree and a popped screen are both
    # gone from that list, which is what makes the two cases one case in keep.py.
    if nd.par is None:
        return nd.scr.nm in ui.scr
    return ui.nd.get(nd.wid) is nd


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
    """The composite a widget sits inside, or None. The nearest enclosing composite owns the widget."""
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


def outer(nd):
    c = within(nd)
    while c is not None and within(c) is not None:
        c = within(c)
    return c


def stops(ui, owner=None):
    if owner is None:
        s = top(ui)
        if s is None:
            return []
        owner = s.root
    raw = []

    def collect(p):
        for nd in p.kids:
            if "comp" in nd.fl:
                if inside(ui, nd):
                    raw.append(nd)
            else:
                if can(ui, nd):
                    raw.append(nd)
                collect(nd)

    collect(owner)
    lead = {}
    for nd in raw:
        if nd.grp is not None:
            old = lead.get(nd.grp)
            if old is None or ("sel" in nd.fl and "sel" not in old.fl):
                lead[nd.grp] = nd
    return [nd for nd in raw if nd.grp is None or lead.get(nd.grp) is nd]


def under(nd, anc):
    cur = nd.par
    while cur is not None:
        if cur is anc:
            return True
        cur = cur.par
    return False
