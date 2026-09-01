def edge(ch):
    lo = 0
    for i, g in enumerate(ch):
        if g.sh:
            lo = i
    return lo


def pick(f, ch):
    for g in ch[edge(ch):]:
        if g.hit:
            return g
    return None
