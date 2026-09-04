"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: write the rule down and walk it. The table holds, for every position
and every number of keeps since the last move, the best pair of numbers a
completion can reach; the walk from the start takes a drop whenever a drop
still reaches the best pair, otherwise an add, otherwise a keep. It is the
rule and nothing else, so it is right on every case small enough for it to
finish, which is every case a person would write out by hand to check
themselves.

It is quadratic in the two lengths, twice over, and it is the answer to
"what if I just do the obvious thing". The medium block alone is four hundred
pairs of a few thousand lines against forty seconds; one of them is already
past that. The timed pairs are between forty thousand and a million lines a
side, where the table is billions of entries and would not fit in memory even
if there were time for it. Every short block passes and everything with a
clock on it fails.
"""

CONTEXT = 3

INF = (1 << 30, 1 << 30)


def table(before, after):
    """rest[s][i][j]: the best (moves, comments) pair a completion from (i, j)
    can reach when s keeps have gone by since the last move, s held at CONTEXT
    once it gets there. A move costs a comment only when s is already at the
    cap, which is what merges two runs a line or two apart; any move puts s
    back to zero and a keep raises it by one."""
    n, m = len(before), len(after)
    rest = [[[INF] * (m + 1) for _ in range(n + 1)] for _ in range(CONTEXT + 1)]
    for s in range(CONTEXT + 1):
        rest[s][n][m] = (0, 0)
    for i in range(n, -1, -1):
        line = before[i] if i < n else None
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            keeps = i < n and j < m and line == after[j]
            for s in range(CONTEXT + 1):
                charge = 1 if s == CONTEXT else 0
                best = INF
                if i < n:
                    moves, comments = rest[0][i + 1][j]
                    pair = (moves + 1, comments + charge)
                    if pair < best:
                        best = pair
                if j < m:
                    moves, comments = rest[0][i][j + 1]
                    pair = (moves + 1, comments + charge)
                    if pair < best:
                        best = pair
                if keeps:
                    pair = rest[s + 1 if s < CONTEXT else CONTEXT][i + 1][j + 1]
                    if pair < best:
                        best = pair
                rest[s][i][j] = best
    return rest


def changes(before, after):
    n, m = len(before), len(after)
    rest = table(before, after)
    i = j = 0
    s = CONTEXT
    ops = []
    while i < n or j < m:
        want = rest[s][i][j]
        charge = 1 if s == CONTEXT else 0
        if i < n:
            moves, comments = rest[0][i + 1][j]
            if (moves + 1, comments + charge) == want:
                ops.append(["-", i])
                i += 1
                s = 0
                continue
        if j < m:
            moves, comments = rest[0][i][j + 1]
            if (moves + 1, comments + charge) == want:
                ops.append(["+", j])
                j += 1
                s = 0
                continue
        assert i < n and j < m and before[i] == after[j]
        nxt = s + 1 if s < CONTEXT else CONTEXT
        assert rest[nxt][i + 1][j + 1] == want
        i += 1
        j += 1
        s = nxt
    return ops
