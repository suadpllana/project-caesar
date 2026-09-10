from tab import mark


def part(tab, num, buck, lo, hi):
    mark.fresh(tab, buck, lo, hi, num)
    return hi - lo + 1
