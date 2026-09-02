def draw(b, cap):
    d = {n: 0 for n in b.who()}
    h = {n: b.hold(n) for n in b.who()}
    on = True
    while on:
        on = False
        for n in b.who():
            q = b.line(n)
            while d[n] < cap[n]:
                o = q[d[n]]
                if h[n] < o.am:
                    break
                h[n] -= o.am
                h[o.pe] += o.am
                d[n] += 1
                on = True
    return d
