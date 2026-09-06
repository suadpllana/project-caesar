from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0:
        return f, True, "stop"
    p = hb.pin(s)
    return sm.back(s, p), False, ""
