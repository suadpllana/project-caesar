"""What the page says about a node, read off the page as it stands now.

A node is exposed when it is attached and no element at or above it hides it (`hidden` with any
value, or `aria-hidden="true"`; `aria-hidden="false"` never undoes an ancestor). Its region is
the nearest element at or above it carrying `aria-live` - `off` included, so an off region
nested in a polite one is a wall rather than a window. A region voices while it is exposed and
polite or assertive, and it lets through only the kinds its own `aria-relevant` names; an
`aria-relevant` anywhere else on the page means nothing.
"""

POL = ("polite", "assertive")
ALL = frozenset(("additions", "removals", "text"))
BASE = frozenset(("additions", "text"))


def hides(pg, e):
    return pg.attr(e, "hidden") is not None or pg.attr(e, "aria-hidden") == "true"


def place(pg, n):
    """(exposed, region) for node n. The region is None when n is not exposed."""
    reg = None
    x = n
    while x is not None:
        if not pg.is_text(x):
            if hides(pg, x):
                return False, None
            if reg is None and pg.attr(x, "aria-live") is not None:
                reg = x
        if x == 0:
            return True, reg
        x = pg.up(x)
    return False, None


def region(pg, n):
    """The nearest element at or above n carrying aria-live, exposed or not."""
    x = n
    while x is not None:
        if not pg.is_text(x) and pg.attr(x, "aria-live") is not None:
            return x
        x = pg.up(x)
    return None


def voicing(pg, r):
    return pg.attr(r, "aria-live") in POL and place(pg, r)[0]


def loudness(pg, r):
    return pg.attr(r, "aria-live")


def relevant(pg, r):
    got = set()
    for tok in (pg.attr(r, "aria-relevant") or "").split():
        if tok == "all":
            return ALL
        if tok in ALL:
            got.add(tok)
    return frozenset(got) if got else BASE


def busy(pg, e):
    return pg.attr(e, "aria-busy") == "true"


def atomic(pg, e):
    v = pg.attr(e, "aria-atomic")
    return v if v in ("true", "false") else None
