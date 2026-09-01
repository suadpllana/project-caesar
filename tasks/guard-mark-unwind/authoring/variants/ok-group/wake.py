def rouse(f, ch):
    seen = []
    for g in reversed(ch):
        seen.append(g)
        if g.sh:
            break
    for g in seen:
        if g.hit:
            return True
    return False
