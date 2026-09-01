def edge(ch):
    lo = 0
    for i, g in enumerate(ch):
        if g.sh:
            lo = i
    return lo


def stops(g, ch, gg):
    if not g.hit:
        return False
    for h in ch[edge(ch):]:
        if h.hit:
            return False
    return True


def blend(old, new):
    return new
