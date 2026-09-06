def dl(c):
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def back(s, i):
    c = getattr(s, "cb", None)
    if c is None:
        c = [0]
        s.cb = c
    t = s.t
    p = c[0] if c[0] <= i else 0
    while p < i:
        w = dl(t[p])
        if p + w > i:
            break
        p += w
    if p > c[0]:
        c[0] = p
    return p
