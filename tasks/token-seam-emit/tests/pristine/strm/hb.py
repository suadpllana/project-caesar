def first(s):
    t = s.t
    b = -1
    for x in s.ss:
        if not x:
            continue
        k = t.find(x)
        if k >= 0 and (b < 0 or k < b):
            b = k
    return b


def pin(s):
    n = len(s.t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    if m <= 1:
        return n
    b = n - m + 1
    return b if b > 0 else 0
