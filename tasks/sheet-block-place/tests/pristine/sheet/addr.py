COLW = 10
ROWH = 20
LETTERS = "abcdefghij"


def parse(tok):
    if not tok or tok[0] not in LETTERS:
        return None
    c = LETTERS.index(tok[0])
    rest = tok[1:]
    if not rest.isdigit():
        return None
    r = int(rest)
    if r < 1 or r > ROWH:
        return None
    return (r, c)


def name(a):
    return "%s%d" % (LETTERS[a[1]], a[0])


def walk():
    for r in range(1, ROWH + 1):
        for c in range(COLW):
            yield (r, c)


def inside(a):
    return 1 <= a[0] <= ROWH and 0 <= a[1] < COLW


def span(top, h, w):
    out = []
    for dr in range(h):
        for dc in range(w):
            out.append((top[0] + dr, top[1] + dc))
    return out

