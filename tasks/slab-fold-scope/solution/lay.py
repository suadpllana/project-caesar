from tab import mark, wipe


def part(tab, num, buck, lo, hi, jr):
    took = wipe.part(tab, buck, lo, hi, jr)
    mark.fresh(tab, buck, lo, hi, num, jr)
    return (hi - lo + 1) - took
