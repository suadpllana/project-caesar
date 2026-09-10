from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    seen = {}
    for key, got in b.own.items():
        sid, stamp = got
        e = seen.get(sid)
        inside = lo <= key <= hi
        if e is None:
            seen[sid] = [1 if inside else 0, 1, stamp, stamp]
        else:
            e[0] += 1 if inside else 0
            e[1] += 1
            if stamp < e[2]:
                e[2] = stamp
            if stamp > e[3]:
                e[3] = stamp
    reach = set()
    for sid, e in seen.items():
        if e[0] != e[1] or not e[0]:
            continue
        if e[2] <= base < e[3]:
            raise Again()
        if e[3] <= base:
            reach.add(sid)
    if len(reach) < 2:
        return False
    mark.keep(tab, buck, reach, jr)
    return True
