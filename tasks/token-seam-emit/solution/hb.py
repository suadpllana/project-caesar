def first(s):
    c = getattr(s, "hf", None)
    if c is None:
        c = [-1, 0]
        s.hf = c
    t = s.t
    n = len(t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    j = c[1] - m + 1
    if j < 0:
        j = 0
    b = c[0]
    for x in s.ss:
        if not x:
            continue
        k = t.find(x, j)
        if k >= 0 and (b < 0 or k < b):
            b = k
    c[1] = n
    c[0] = b
    return b


def pin(s):
    t = s.t
    n = len(t)
    b = n
    for x in s.ss:
        w = len(x) - 1
        if w > n:
            w = n
        while w > 0:
            if x[:w] == t[n - w:]:
                if n - w < b:
                    b = n - w
                break
            w -= 1
    return b
