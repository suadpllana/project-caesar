from bind import card, rch


def sound(bk, c, off):
    a = card.auth(bk, c)
    if a is None:
        return False
    here = bk.held(c)
    rep = here[0]
    wide = set(here)
    for x in rch.span(bk, c, off):
        ks = bk.held(x)
        if ks[0] < rep:
            return False
        wide.update(ks)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False
    return True


def firm(bk, c):
    return sound(bk, c, set(bk.gone))
