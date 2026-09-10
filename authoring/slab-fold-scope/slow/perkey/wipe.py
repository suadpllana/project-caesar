from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    took = 0
    for key in range(lo, hi + 1):
        if key in b.own:
            live.drop(b, key, jr)
            took += 1
    return took
