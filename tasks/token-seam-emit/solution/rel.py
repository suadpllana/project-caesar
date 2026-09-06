from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
