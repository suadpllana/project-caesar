def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def stops(g, ch, gg):
    for h in wall(ch):
        if h.hit:
            return False
    return bool(g.hit)


def blend(old, new):
    return new
