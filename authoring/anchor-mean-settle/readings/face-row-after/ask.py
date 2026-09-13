"""The three questions.

`tall` counts the unmeasured rows at the assumed height, since they take up room whether or
not anyone has looked at them. `face` names the first row the view touches - the one holding
the scroll position, not the first row starting at or after it - and reports its top edge
relative to the view's, which is zero when they line up and negative when the row began
above the view.
"""
from pan import grid, say


def top(p):
    say.top(p.top)


def tall(p):
    say.tall(grid.full(p))


def face(p):
    r, acc = grid.hit(p)
    if r is None:
        say.bare()
        return
    if acc < p.top:
        e = grid.gues.hei(p)
        nxt = None
        for x in grid.down(p, r, acc):
            if x is not r:
                nxt = x
                break
        if nxt is not None:
            acc += grid.hgt(p, r, e)
            r = nxt
    say.face(r.rid, acc - p.top)
