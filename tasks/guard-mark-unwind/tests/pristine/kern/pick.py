def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def pick(f, ch):
    for g in wall(ch):
        if g.sh:
            continue
        if g.hit:
            return g
    return None
