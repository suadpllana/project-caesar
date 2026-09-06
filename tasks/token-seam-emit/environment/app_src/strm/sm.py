def dl(c):
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def back(s, i):
    t = s.t
    p = 0
    while p < i:
        w = dl(t[p])
        if p + w > i:
            break
        p += w
    return p
