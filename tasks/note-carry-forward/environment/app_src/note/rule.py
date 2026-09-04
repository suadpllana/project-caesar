from scr import grp


def kept(before, after):
    n, m = len(before), len(after)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row = best[i]
        nxt = best[i + 1]
        for j in range(m - 1, -1, -1):
            if before[i] == after[j]:
                row[j] = nxt[j + 1] + 1
            else:
                a = nxt[j]
                b = row[j + 1]
                row[j] = a if a > b else b
    out = {}
    i = j = 0
    while i < n and j < m:
        if before[i] == after[j] and best[i][j] == best[i + 1][j + 1] + 1:
            out[i] = j
            i += 1
            j += 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def touched(span, before, after):
    reached = set()
    for chunk in grp.spans(before, after):
        reached |= chunk
    return bool(span) and span <= reached


def merges(one, other):
    return one == other
