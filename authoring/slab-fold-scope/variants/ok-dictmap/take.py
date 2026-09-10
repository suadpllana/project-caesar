from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    reach = {}
    for start in live.meet(b, lo, hi):
        end, num, sid = b.run[start]
        seen = min(end, hi) - max(start, lo) + 1
        got = reach.get(sid)
        if got is None:
            reach[sid] = [seen, num, num]
        else:
            got[0] += seen
            got[1] = min(got[1], num)
            got[2] = max(got[2], num)
    whole = set()
    for sid, (seen, low, high) in reach.items():
        if seen != b.own[sid]:
            continue
        if low <= base and high > base:
            raise Again()
        if high <= base:
            whole.add(sid)
    if len(whole) < 2:
        return False
    mark.keep(tab, buck, lo, hi, whole, jr)
    return True
