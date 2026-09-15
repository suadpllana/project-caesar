def width(h):
    return h.ranks * h.micro * h.accum


def span(h, rank, slot):
    lo = rank * h.micro * h.accum + slot * h.micro
    return lo, lo + h.micro
