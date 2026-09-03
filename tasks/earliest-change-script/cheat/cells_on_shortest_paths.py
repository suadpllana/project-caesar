"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: find the shortest-path restriction and stop there. The frontier says
which cells lie on some shortest script, the comment recurrence is evaluated
at every one of them, and the walk reads the counts off. Nothing about the
rule is misread: the keeps since the last move are carried through the walk
and the merge is applied exactly, so every correctness block passes. What it
misses is the second half of the restriction -- that the recurrence is only
needed where the walk has a choice to make, and that the stretch between two
such cells can be crossed by counting its keeps instead of visiting them. On
the twelve pairs whose two sides still resemble each other it merely pays for
that: a million lines that differ in a few hundred places take 3.7 seconds
against the reference's 0.3, which is inside the budget and looks like success.

The six that share no order are where it stops being a constant factor. Their
scripts run past the length of the file, so the frontier is abandoned and what
is left is the table, which is out by orders of magnitude. Nor would a cheaper
way of listing the shortest-path cells save it there: between one keep and the
next, every monotone path through the rectangle between them is a shortest
path, so the cells to visit are the areas of those rectangles rather than the
number of matches. The pairs those rectangles belong to are the ones no pair
small enough to check by hand ever looks like. Six of the eighteen timed pairs
are never answered, and it scores zero.
"""





# The frontier keeps every layer, and a layer at depth d has about d entries.
# Above this depth the layers alone would not fit in the memory the task is
# graded with, so the frontier is never allowed to run past it.
_FRONTIER_CAP = 5000

# How many kept lines it takes to end a comment.
CONTEXT = 3
_FAR = CONTEXT
_ZERO = (0,) * (CONTEXT + 1)


def changes(before, after):
    n, m = len(before), len(after)

    # Comparing small integers is a good deal cheaper than comparing strings,
    # and both engines spend nearly all of their time on that comparison.
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in before]
    b = [ids.setdefault(line, len(ids)) for line in after]

    layers = _layers_from_end(a, b, n, m, _FRONTIER_CAP)
    if layers is None:
        return _table(before, after)
    return _cells_engine(a, b, n, m, layers)


# ---------------------------------------------------------------- frontier --


def _layers_from_end(a, b, n, m, limit):
    """layers[d][k] is the smallest i for which position (i, i - k) can reach
    the end of both sequences in d moves. A position on diagonal k is within d
    moves of the end exactly when i is at least that number, which is what
    makes every question the walk asks a single comparison. None if the pair
    needs more than `limit` moves, which is the pairs engine's cue."""
    end = n - m
    i, j = n, m
    while i > 0 and j > 0 and a[i - 1] == b[j - 1]:
        i -= 1
        j -= 1
    layers = [{end: i}]
    if i == 0 and j == 0:
        return layers

    d = 0
    while d < limit:
        d += 1
        previous = layers[-1]
        layer = {}
        for k in range(end - d, end + d + 1, 2):
            best = None
            up = previous.get(k + 1)
            if up is not None and up > 0:
                best = up - 1
            left = previous.get(k - 1)
            if left is not None and (best is None or left < best):
                best = left
            if best is None:
                continue
            i = best
            j = i - k
            if j < 0 or i > n or j > m:
                continue
            while i > 0 and j > 0 and a[i - 1] == b[j - 1]:
                i -= 1
                j -= 1
            layer[k] = i
        layers.append(layer)
        if layer.get(0) == 0:
            return layers
    return None


def _cells_engine(a, b, n, m, layers):
    total = len(layers) - 1
    if total == 0:
        return []
    width = m + 1

    def choices(i, j, r):
        if r == 0:
            return False, False, i < n and j < m
        below = layers[r - 1]
        k = i - j
        reach = below.get(k + 1)
        drop = i < n and reach is not None and reach <= i + 1
        reach = below.get(k - 1)
        add = j < m and reach is not None and reach <= i
        keep = i < n and j < m and a[i] == b[j]
        return drop, add, keep

    vals = {n * width + m: _ZERO}
    stack = [(0, 0, total, False)]
    while stack:
        i, j, r, ready = stack.pop()
        key = i * width + j
        if key in vals:
            continue
        drop, add, keep = choices(i, j, r)
        if not ready:
            stack.append((i, j, r, True))
            if drop and (i + 1) * width + j not in vals:
                stack.append((i + 1, j, r - 1, False))
            if add and key + 1 not in vals:
                stack.append((i, j + 1, r - 1, False))
            if keep and key + width + 1 not in vals:
                stack.append((i + 1, j + 1, r, False))
            continue
        moved = 1 << 30
        if drop:
            v = vals[key + width][0]
            if v < moved:
                moved = v
        if add:
            v = vals[key + 1][0]
            if v < moved:
                moved = v
        best = [1 << 30] * (CONTEXT + 1)
        for s in range(CONTEXT + 1):
            if moved < 1 << 30:
                got = moved + 1 if s == _FAR else moved
                if got < best[s]:
                    best[s] = got
            if keep:
                v = vals[key + width + 1][s + 1 if s < _FAR else _FAR]
                if v < best[s]:
                    best[s] = v
        vals[key] = tuple(best)

    ops = []
    emit = ops.append
    i = j = 0
    r = total
    s = _FAR
    while i < n or j < m:
        key = i * width + j
        drop, add, keep = choices(i, j, r)
        want = vals[key][s]
        cost = 1 if s == _FAR else 0
        if drop and vals[key + width][0] + cost == want:
            emit(["-", i])
            i += 1
            r -= 1
            s = 0
        elif add and vals[key + 1][0] + cost == want:
            emit(["+", j])
            j += 1
            r -= 1
            s = 0
        else:
            i += 1
            j += 1
            s = s + 1 if s < _FAR else _FAR
    return ops



INF = (1 << 30, 1 << 30)


def _table_of(before, after):
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


def _table(before, after):
    n, m = len(before), len(after)
    rest = _table_of(before, after)
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
