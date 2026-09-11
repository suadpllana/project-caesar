from opt import cut


def sweep(r):
    for k in range(r.ws):
        a, b = cut.span(r, k)
        if a >= b:
            continue
        left = r.bud
        for i, name in enumerate(r.map):
            if r.off[i] < a or r.off[i + 1] > b:
                continue
            used, stop = r.par[name].spend(left)
            left -= used
            if stop:
                break
