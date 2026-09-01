"""The definitional model: the rule written out, with nothing clever in it.

It builds the whole table of remaining-move counts and then walks it, taking a
drop whenever a drop still leaves the script minimal, otherwise an add,
otherwise a keep. Slow and quadratic, which is the point — the answers it
produces are derived from the rule rather than from a second attempt at the
efficient algorithm, so a misunderstanding cannot pass both.
"""


def distance_table(before, after):
    n, m = len(before), len(after)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, below, line = lcs[i], lcs[i + 1], before[i]
        for j in range(m - 1, -1, -1):
            if line == after[j]:
                row[j] = below[j + 1] + 1
            else:
                x, y = below[j], row[j + 1]
                row[j] = x if x > y else y
    return [[(n - i) + (m - j) - 2 * lcs[i][j] for j in range(m + 1)]
            for i in range(n + 1)]


def script(before, after):
    n, m = len(before), len(after)
    dist = distance_table(before, after)
    remaining = dist[0][0]
    i = j = 0
    ops = []
    while i < n or j < m:
        if i < n and dist[i + 1][j] < remaining:
            ops.append(["-", i])
            i += 1
            remaining -= 1
        elif j < m and dist[i][j + 1] < remaining:
            ops.append(["+", j])
            j += 1
            remaining -= 1
        else:
            assert i < n and j < m and before[i] == after[j]
            assert dist[i + 1][j + 1] == remaining
            i += 1
            j += 1
    assert remaining == 0
    return ops


def rebuild(before, after, ops):
    """Independent check that a script really turns one sequence into the
    other. Used on the reference, not on submitted output."""
    out = []
    i = j = 0
    for kind, idx in ops:
        if kind == "-":
            while i < idx:
                out.append(before[i])
                i += 1
                j += 1
            i += 1
        else:
            while j < idx:
                out.append(before[i])
                i += 1
                j += 1
            out.append(after[idx])
            j += 1
    out.extend(before[i:])
    return out
