from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    took = 0
    for start in live.meet(b, lo, hi):
        end, num, sid = b.run[start]
        live.erase(b, start, jr)
        if start < lo:
            live.write(b, start, lo - 1, num, sid, jr)
        if end > hi:
            live.write(b, hi + 1, end, num, sid, jr)
        took += min(end, hi) - max(start, lo) + 1
    return took
