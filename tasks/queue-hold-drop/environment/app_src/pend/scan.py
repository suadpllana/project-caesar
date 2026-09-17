def ops(text):
    out = []
    for line in text.splitlines():
        bits = line.split()
        if bits:
            out.append(tuple(bits))
    return out
