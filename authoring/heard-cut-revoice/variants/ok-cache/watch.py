from . import look


def _texts(pg, top):
    return [x for x in pg.walk(top) if pg.is_text(x)]


def changes(pg, recs):
    out = []
    for rec in recs:
        head = rec[0]
        if head == "text":
            n = rec[1]
            if look.shown(pg, n):
                r = look.region(pg, n)
                if r is not None:
                    out.append(("text", r, n, pg.text(n)))
        elif head in ("add", "move"):
            for x in _texts(pg, rec[1]):
                if look.shown(pg, x):
                    r = look.region(pg, x)
                    if r is not None:
                        out.append(("additions", r, x, pg.text(x)))
        elif head == "drop":
            old = rec[2]
            if look.shown(pg, old):
                r = look.region(pg, old)
                if r is not None:
                    for x in _texts(pg, rec[1]):
                        out.append(("removals", r, x, pg.text(x)))
    return out
