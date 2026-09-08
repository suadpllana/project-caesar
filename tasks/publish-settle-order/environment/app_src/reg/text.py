def ops(p):
    out = []
    with open(p) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(tuple(ln.split()))
    return out
