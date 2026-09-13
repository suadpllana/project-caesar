from pan import grid, say, seat


def pas(p):
    seat.take(p)
    k = 0
    while True:
        nd, acc = grid.hit(p)
        if nd is None:
            break
        pick = None
        for x in grid.down(p, nd, acc):
            if not grid.held(p, x):
                pick = x
                break
        if pick is None:
            break
        grid.mark(p, pick)
        k += 1
        seat.hold(p)
    say.seen(k)
