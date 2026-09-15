"""Where a step's draws go. The draws themselves know nothing about any of these three."""


def width(h):
    return h.ranks * h.micro * h.accum


def span(h, rank, slot):
    lo = (slot * h.ranks + rank) * h.micro
    return lo, lo + h.micro
