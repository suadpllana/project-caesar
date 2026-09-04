def kept(walk):
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    return out


def raised(line, spans):
    for s in spans:
        if line in s:
            return True
    return False
