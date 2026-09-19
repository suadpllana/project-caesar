def rank(weight):
    return sorted(range(len(weight)), key=lambda e: (-weight[e], e))


def want(order, weight, w):
    wl = []
    tot = 0
    for e in order:
        wl.append(e)
        tot += weight[e]
        if tot >= w:
            break
    return wl
