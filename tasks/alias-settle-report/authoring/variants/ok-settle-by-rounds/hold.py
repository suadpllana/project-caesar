# The same smallest self-consistent set, grown by a worklist over cells rather
# than by rescanning the watch list, and starting from the far end of it. The
# order a cell is taken in cannot matter: letting a cell go only ever takes
# something out of another cell's reach, so nothing that was ready stops being
# ready, and the set the rounds close on is the same set.
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
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
        wide.update(ks)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False
    return True


def firm(bk, c):
    off = set(bk.gone)
    todo = [w for w in reversed(bk.watch) if w not in bk.filed]
    cells = set()
    while todo:
        again = []
        gained = False
        for w in todo:
            d = bk.find(w)
            if d in cells or set(bk.held(d)) & off:
                cells.add(d)
                continue
            if sound(bk, d, off):
                cells.add(d)
                off = off | set(bk.held(d))
                gained = True
            else:
                again.append(w)
        if not gained:
            break
        todo = again
    return c in cells
