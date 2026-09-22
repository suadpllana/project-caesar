def shape(runs, lo, hi, slack, cap):
    if not runs:
        return []
    out = [[runs[0][0], runs[0][1]]]
    for a, b in runs[1:]:
        if a - out[-1][1] <= slack:
            out[-1][1] = b
        else:
            out.append([a, b])
    if len(out) > cap:
        return [(out[0][0], out[-1][1])]
    return [(a, b) for a, b in out]
