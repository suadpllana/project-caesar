from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return False
    seen = {}
    for a, z, num, sid in b.rs[i:j]:
        bit = min(z, hi) - max(a, lo) + 1
        got = seen.get(sid)
        if got is None:
            seen[sid] = [bit, num, num]
        else:
            got[0] += bit
            got[1] = min(got[1], num)
            got[2] = max(got[2], num)
    reach = set()
    for sid, (bit, low, high) in seen.items():
        if bit != b.own[sid]:
            continue
        if low <= base < high:
            raise Again()
        if high <= base:
            reach.add(sid)
    if len(reach) < 2:
        return False
    mark.keep(tab, buck, lo, hi, reach, jr)
    return True
