from tab import mark, wipe


def part(tab, num, buck, lo, hi):
    took = wipe.part(tab, buck, lo, hi)
    mark.fresh(tab, buck, lo, hi, num)
    return hi - lo + 1 - took
