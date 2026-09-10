from keep import cover


def shed(a, p, t):
    a.t = t
    a.pegs.pop(p, None)
    for b in a.roll:
        if b in a.stop or cover.kept(a, b):
            continue
        r = a.at.get(b)
        a.stop[b] = r[2] if r is not None and r[2] is not None else t
