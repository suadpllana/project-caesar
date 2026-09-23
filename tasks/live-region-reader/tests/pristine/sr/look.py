POL = ("polite", "assertive")
BASE = ("additions", "text")


def hides(pg, e):
    return pg.attr(e, "hidden") is not None or pg.attr(e, "aria-hidden") == "true"


def shown(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x) and hides(pg, x):
            return False
        if x == 0:
            return True
        x = pg.up(x)
    return False


def region(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x) and pg.attr(x, "aria-live") in POL:
            return x
        x = pg.up(x)
    return None


def relevant(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x):
            v = pg.attr(x, "aria-relevant")
            if v is not None:
                got = set(v.split())
                if "all" in got:
                    return {"additions", "removals", "text"}
                return got
        x = pg.up(x)
    return set(BASE)


def busy(pg, r):
    return pg.attr(r, "aria-busy") == "true"


def loud(pg, r):
    return pg.attr(r, "aria-live")
