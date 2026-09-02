"""The definitional model: the rule written out, with nothing clever in it.

Three tiers. The script is shortest; of the shortest scripts it has the fewest
hunks, a hunk being a maximal run of consecutive moves in the reading; and of
those it is the one whose reading comes first with a drop ahead of an add and
an add ahead of a keep.

The table holds, for every position and for each of two states -- inside a run
of moves, or not -- the best pair (moves still needed, hunks still to be
opened) that a completion from there can reach. Pairs compare in that order, so
the minimum is taken over moves first and hunks second. The walk from the start
then takes a drop whenever a drop still reaches the best pair, otherwise an add,
otherwise a keep, which is the third tier. Slow and quadratic, which is the
point: the answers it produces are derived from the rule rather than from a
second attempt at the efficient algorithm, so a misunderstanding cannot pass
both.

`every_script` is the same rule enforced by exhaustion over every script a pair
admits, with no table at all. A test holds the two to each other on the short
shapes, so the table itself is checked against the words of the rule.
"""

INF = (1 << 30, 1 << 30)


def table(before, after):
    """rest[s][i][j] for s in (0, 1): the best (moves, hunks) pair reachable
    from position (i, j) when a run of moves is (s = 1) or is not (s = 0)
    already open. Opening a run costs a hunk; extending one does not; a keep
    closes whatever run was open."""
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
    return quiet, inrun


def script(before, after):
    n, m = len(before), len(after)
    quiet, inrun = table(before, after)
    i = j = 0
    open_run = False
    ops = []
    while i < n or j < m:
        want = inrun[i][j] if open_run else quiet[i][j]
        cost = 0 if open_run else 1
        if i < n:
            moves, hunks = inrun[i + 1][j]
            if (moves + 1, hunks + cost) == want:
                ops.append(["-", i])
                i += 1
                open_run = True
                continue
        if j < m:
            moves, hunks = inrun[i][j + 1]
            if (moves + 1, hunks + cost) == want:
                ops.append(["+", j])
                j += 1
                open_run = True
                continue
        assert i < n and j < m and before[i] == after[j]
        assert quiet[i + 1][j + 1] == want
        i += 1
        j += 1
        open_run = False
    return ops


def every_script(before, after):
    """The rule by exhaustion: enumerate every script, read each one back, and
    keep the one that wins on (moves, hunks, reading). Exponential; for pairs
    of a handful of lines only."""
    n, m = len(before), len(after)
    order = {"-": 0, "+": 1, "=": 2}
    best = [None, None]

    def hunks_in(reading):
        count = 0
        previous = "="
        for step in reading:
            if step != "=" and previous == "=":
                count += 1
            previous = step
        return count

    def visit(i, j, reading, ops):
        if i == n and j == m:
            key = (sum(1 for step in reading if step != "="),
                   hunks_in(reading), [order[step] for step in reading])
            if best[0] is None or key < best[0]:
                best[0] = key
                best[1] = [list(op) for op in ops]
            return
        if i < n:
            reading.append("-")
            ops.append(["-", i])
            visit(i + 1, j, reading, ops)
            reading.pop()
            ops.pop()
        if j < m:
            reading.append("+")
            ops.append(["+", j])
            visit(i, j + 1, reading, ops)
            reading.pop()
            ops.pop()
        if i < n and j < m and before[i] == after[j]:
            reading.append("=")
            visit(i + 1, j + 1, reading, ops)
            reading.pop()

    visit(0, 0, [], [])
    return best[1]


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
