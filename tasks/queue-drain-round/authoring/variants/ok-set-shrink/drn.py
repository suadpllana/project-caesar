def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    take = {n: list(range(cap[n])) for n in who}
    while True:
        got = {n: 0 for n in who}
        for n in who:
            for k in take[n]:
                o = ln[n][k]
                got[o.pe] += o.am
        short = []
        for n in who:
            pay = sum(ln[n][k].am for k in take[n])
            if b.hold(n) + got[n] - pay < 0:
                short.append(n)
        if not short:
            return {n: len(take[n]) for n in who}
        take[short[0]].pop()
