def spans(seq, turns):
    out = []
    for start, gen in turns:
        out.append([start, start + len(gen)])
    return out
