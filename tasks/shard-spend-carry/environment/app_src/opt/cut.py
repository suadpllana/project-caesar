from bisect import bisect_right


def size(r):
    return r.total // r.ws


def span(r, k):
    if r.total == 0 or k >= r.ws:
        return 0, 0
    s = size(r)
    return min(k * s, r.total), min((k + 1) * s, r.total)


def first(r, k):
    a, b = span(r, k)
    if a >= b:
        return None
    i = bisect_right(r.off, a) - 1
    return r.map[i], a - r.off[i]
