def pa(s):
    i = s.index("c")
    return (int(s[1:i]), int(s[i + 1:]))


def fa(t):
    return "r%dc%d" % t


def span(a, b):
    r0, r1 = min(a[0], b[0]), max(a[0], b[0])
    c0, c1 = min(a[1], b[1]), max(a[1], b[1])
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
