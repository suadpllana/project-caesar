"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: read a change the way a diff tool prints one, as a run of drops or
a run of adds, so that a replacement -- some drops followed straight away by
some adds -- is two changes and takes two comments. It is the reading a
person carries in from every unified diff they have ever looked at, where the
minus lines and the plus lines are two blocks under one another.

The rule counts a run of consecutive moves, drops and adds alike, as one, and
then merges two runs that only a kept line or two separates. This breaks at
the seam between a drop run and an add run and merges nothing, so it is wrong
in both directions at once: 8821 of the 40804 enumerated pairs, 9111 of 12000
random ones and 9 of the 71 written out by hand. Built on the definitional
table rather than on either fast engine, so it is also out of time on every
large pair; the wrong answers on the short blocks are what the grader reports
first.
"""


INF = (1 << 30, 1 << 30)


def changes(before, after):
    n, m = len(before), len(after)
    # state 0: after a keep or at the start; 1: inside a run of drops;
    # 2: inside a run of adds. Continuing the same kind of run is free.
    rest = [[[INF] * (m + 1) for _ in range(n + 1)] for _ in range(3)]
    for s in range(3):
        rest[s][n][m] = (0, 0)
    for i in range(n, -1, -1):
        line = before[i] if i < n else None
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            drop = add = keep = INF
            if i < n:
                moves, hunks = rest[1][i + 1][j]
                drop = (moves + 1, hunks)
            if j < m:
                moves, hunks = rest[2][i][j + 1]
                add = (moves + 1, hunks)
            if i < n and j < m and line == after[j]:
                keep = rest[0][i + 1][j + 1]
            for s in range(3):
                best = keep
                d = drop if s == 1 else (drop[0], drop[1] + 1)
                if d < best:
                    best = d
                a = add if s == 2 else (add[0], add[1] + 1)
                if a < best:
                    best = a
                rest[s][i][j] = best

    i = j = 0
    s = 0
    ops = []
    while i < n or j < m:
        want = rest[s][i][j]
        if i < n:
            moves, hunks = rest[1][i + 1][j]
            if (moves + 1, hunks + (0 if s == 1 else 1)) == want:
                ops.append(("-", i))
                i += 1
                s = 1
                continue
        if j < m:
            moves, hunks = rest[2][i][j + 1]
            if (moves + 1, hunks + (0 if s == 2 else 1)) == want:
                ops.append(("+", j))
                j += 1
                s = 2
                continue
        i += 1
        j += 1
        s = 0
    return ops
