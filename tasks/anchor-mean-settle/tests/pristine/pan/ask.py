from pan import grid, say


def top(p):
    say.top(p.top)


def tall(p):
    a = 0
    for r in p.rows:
        if r.hm is not None:
            a += r.hm
    say.tall(a)


def face(p):
    if not p.rows:
        say.bare()
        return
    i = grid.hit(p)
    say.face(p.rows[i].rid, grid.off(p, i))
