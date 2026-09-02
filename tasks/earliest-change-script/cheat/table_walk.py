"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: implement the rule exactly as written and stop. A table holds, for
every position and for each of two states -- inside a run of moves or not --
the best pair of moves still needed and hunks still to be opened, and a walk
from the start takes a drop whenever a drop still reaches that pair, else an
add, else a keep. It is completely correct. It passes all 52865 short cases.

It is also the definitional model the grader uses, and it is dead everywhere
else: the table is the product of the two lengths, twice over, so a pair of
fifteen hundred lines is four and a half million entries and a pair of a
million lines is a number with twelve digits. It cannot finish the medium
block inside its budget and it cannot finish a single one of the eighteen
timed pairs. Scores zero on time while getting every answer it does give
right, which is the whole reason the timed blocks exist.
"""

INF = (1 << 30, 1 << 30)


def changes(before, after):
    n, m = len(before), len(after)
    quiet = [[INF] * (m + 1) for _ in range(n + 1)]
    inrun = [[INF] * (m + 1) for _ in range(n + 1)]
    quiet[n][m] = inrun[n][m] = (0, 0)
    for i in range(n, -1, -1):
        line = before[i] if i < n else None
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            best0 = best1 = INF
            if i < n:
                moves, hunks = inrun[i + 1][j]
                if (moves + 1, hunks) < best1:
                    best1 = (moves + 1, hunks)
                if (moves + 1, hunks + 1) < best0:
                    best0 = (moves + 1, hunks + 1)
            if j < m:
                moves, hunks = inrun[i][j + 1]
                if (moves + 1, hunks) < best1:
                    best1 = (moves + 1, hunks)
                if (moves + 1, hunks + 1) < best0:
                    best0 = (moves + 1, hunks + 1)
            if i < n and j < m and line == after[j]:
                pair = quiet[i + 1][j + 1]
                if pair < best1:
                    best1 = pair
                if pair < best0:
                    best0 = pair
            quiet[i][j] = best0
            inrun[i][j] = best1

    i = j = 0
    open_run = False
    ops = []
    while i < n or j < m:
        want = inrun[i][j] if open_run else quiet[i][j]
        cost = 0 if open_run else 1
        if i < n:
            moves, hunks = inrun[i + 1][j]
            if (moves + 1, hunks + cost) == want:
                ops.append(("-", i))
                i += 1
                open_run = True
                continue
        if j < m:
            moves, hunks = inrun[i][j + 1]
            if (moves + 1, hunks + cost) == want:
                ops.append(("+", j))
                j += 1
                open_run = True
                continue
        i += 1
        j += 1
        open_run = False
    return ops
