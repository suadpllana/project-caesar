from pan import grid, say, seat


def pas(p):
    k = 0
    for i in grid.view(p):
        if p.rows[i].hm is None:
            grid.mark(p, i)
            k += 1
    seat.take(p)
    say.seen(k)
