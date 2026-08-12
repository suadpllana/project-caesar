def spans(seq, turns):
    out = []
    for start, want in turns:
        d = 0
        for a, b in zip(seq, want):
            if a != b:
                break
            d += 1
        out.append([start, d if d >= start else start])
    return out
