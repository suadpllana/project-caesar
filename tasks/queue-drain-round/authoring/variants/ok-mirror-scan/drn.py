def draw(b, cap):
    who = list(reversed(b.who()))
    ln = {n: b.line(n) for n in who}
    d = {n: cap[n] for n in who}
    while True:
        inc = {n: 0 for n in who}
        for n in who:
            for o in ln[n][: d[n]]:
                inc[o.pe] += o.am
        nd = {}
        for n in who:
            av = b.hold(n) + inc[n]
            s = 0
            k = 0
            for o in ln[n][: d[n]]:
                if s + o.am > av:
                    break
                s += o.am
                k += 1
            nd[n] = k
        if nd == d:
            return d
        d = nd
