CONTEXT = 3

INF = (1 << 30, 1 << 30)


def table(before, after):
    n, m = len(before), len(after)
    rest = [[[INF] * (m + 1) for _ in range(n + 1)] for _ in range(CONTEXT + 1)]
    for s in range(CONTEXT + 1):
        rest[s][n][m] = (0, 0)
    for i in range(n, -1, -1):
        line = before[i] if i < n else None
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            same = i < n and j < m and line == after[j]
            for s in range(CONTEXT + 1):
                charge = 1 if s == CONTEXT else 0
                best = INF
                if i < n:
                    moves, notes = rest[0][i + 1][j]
                    pair = (moves + 1, notes + charge)
                    if pair < best:
                        best = pair
                if j < m:
                    moves, notes = rest[0][i][j + 1]
                    pair = (moves + 1, notes + charge)
                    if pair < best:
                        best = pair
                if same:
                    pair = rest[s + 1 if s < CONTEXT else CONTEXT][i + 1][j + 1]
                    if pair < best:
                        best = pair
                rest[s][i][j] = best
    return rest


def script(before, after):
    n, m = len(before), len(after)
    rest = table(before, after)
    i = j = 0
    s = CONTEXT
    ops = []
    while i < n or j < m:
        want = rest[s][i][j]
        charge = 1 if s == CONTEXT else 0
        took = False
        if i < n:
            moves, notes = rest[0][i + 1][j]
            if (moves + 1, notes + charge) == want:
                ops.append(("-", i))
                i += 1
                s = 0
                took = True
        if not took and j < m:
            moves, notes = rest[0][i][j + 1]
            if (moves + 1, notes + charge) == want:
                ops.append(("+", j))
                j += 1
                s = 0
                took = True
        if not took:
            i += 1
            j += 1
            s = s + 1 if s < CONTEXT else CONTEXT
    return ops


def reading(before, after, ops):
    n, m = len(before), len(after)
    at = {}
    for kind, idx in ops:
        at.setdefault((kind, idx), 0)
    i = j = 0
    out = []
    pos = 0
    while i < n or j < m:
        if pos < len(ops) and ops[pos] == ("-", i):
            out.append(("D", i, None))
            i += 1
            pos += 1
        elif pos < len(ops) and ops[pos] == ("+", j):
            out.append(("A", None, j))
            j += 1
            pos += 1
        else:
            out.append(("K", i, j))
            i += 1
            j += 1
    return out
