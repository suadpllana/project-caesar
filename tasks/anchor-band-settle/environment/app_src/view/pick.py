from view import stick


def first(v, fl, s):
    skip = stick.stuck(v, fl, s)
    lo, hi = s, s + v.vh

    def look(b):
        if b.lift or b in skip:
            return None
        y = fl.top[b]
        e = y + fl.h[b]
        if e <= lo or y >= hi:
            return None
        if y >= lo and e <= hi:
            return b
        if not b.shut:
            for c in b.kids:
                got = look(c)
                if got is not None:
                    return got
        return b

    for b in v.kids:
        got = look(b)
        if got is not None:
            return got
    return None
