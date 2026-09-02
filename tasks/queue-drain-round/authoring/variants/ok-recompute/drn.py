def _fits(b, ln, d, n):
    inc = 0
    for m in b.who():
        for o in ln[m][: d[m]]:
            if o.pe == n:
                inc += o.am
    pay = sum(o.am for o in ln[n][: d[n]])
    return b.hold(n) + inc - pay >= 0


def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    d = dict(cap)
    moved = True
    while moved:
        moved = False
        for n in who:
            while d[n] > 0 and not _fits(b, ln, d, n):
                d[n] -= 1
                moved = True
    return d
