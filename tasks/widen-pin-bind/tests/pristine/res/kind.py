def steps(prog, a, b):
    if a == b:
        return 0
    for nxt in prog.ups.get(a, ()):
        got = steps(prog, nxt, b)
        if got is not None:
            return got + 1
    return None
