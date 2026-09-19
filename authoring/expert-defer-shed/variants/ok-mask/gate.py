"""Ranking and want list, taken from a ranking built once and filtered in place."""


def rank(sc):
    order = list(range(len(sc)))
    order.sort(key=lambda e: e)
    order.sort(key=lambda e: sc[e], reverse=True)
    return order


def want(order, sc, w, out_of):
    wl = []
    need = w
    for e in order:
        if e in out_of:
            continue
        wl.append(e)
        need -= sc[e]
        if need <= 0:
            break
    return wl
