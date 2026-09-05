from scr import grp, pin


def kept(before, after):
    n, m = len(before), len(after)
    rest = pin.table(before, after)
    out = {}
    i = j = 0
    s = pin.CONTEXT
    while i < n or j < m:
        want = rest[s][i][j]
        if i < n and j < m and before[i] == after[j]:
            nxt = s + 1 if s < pin.CONTEXT else pin.CONTEXT
            if rest[nxt][i + 1][j + 1] == want:
                out[i] = j
                i += 1
                j += 1
                s = nxt
                continue
        charge = 1 if s == pin.CONTEXT else 0
        if i < n:
            moves, notes = rest[0][i + 1][j]
            if (moves + 1, notes + charge) == want:
                i += 1
                s = 0
                continue
        j += 1
        s = 0
    return out


def touched(span, before, after):
    reached = set()
    for chunk in grp.spans(before, after):
        reached |= chunk
    return bool(span) and span <= reached


def merges(one, other):
    return one == other
