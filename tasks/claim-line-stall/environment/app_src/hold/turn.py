from hold import book, knot, line, say


def after(h, units):
    if not units:
        return
    line.settle(h, units)
    while True:
        bad = knot.loops(h)
        if not bad:
            return
        gone = knot.pick(h, bad)
        n, where, _had = book.clear(h, gone)
        say.stop(h, gone, n)
        line.settle(h, where)
