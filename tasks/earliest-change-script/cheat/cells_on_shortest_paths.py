"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: find the shortest-path restriction and stop there. The frontier
says which cells lie on some shortest script, the hunk recurrence is
evaluated at every one of them, and the walk reads the counts off. That is
the whole task solved for the long family: a million lines that differ in a
few hundred places are a million cells and a couple of seconds, and every
correctness block passes.

It has nothing for the other two. A pair that shares no order needs tens or
hundreds of thousands of moves, so the frontier is out by orders of magnitude
and is abandoned, and what is left is the table, which is out by more. Nor
would a cheaper way of listing the shortest-path cells save it on the sparse
family: between one keep and the next, every monotone path through the
rectangle between them is a shortest path, so the cells to visit are the
areas of those rectangles rather than the number of matches. Twelve of the
eighteen timed pairs are never answered, and it scores zero.
"""




# The frontier keeps every layer, and a layer at depth d has about d entries.
# Above this depth the layers alone would not fit in the memory the task is
# graded with, so the frontier is never allowed to run past it.
_FRONTIER_CAP = 5000


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

    quiet = {n * width + m: 0}
    inrun = {n * width + m: 0}
    stack = [(0, 0, total, False)]
    while stack:
        i, j, r, ready = stack.pop()
        key = i * width + j
        if key in quiet:
            continue
        drop, add, keep = choices(i, j, r)
        if not ready:
            stack.append((i, j, r, True))
            if drop and (i + 1) * width + j not in quiet:
                stack.append((i + 1, j, r - 1, False))
            if add and key + 1 not in quiet:
                stack.append((i, j + 1, r - 1, False))
            if keep and key + width + 1 not in quiet:
                stack.append((i + 1, j + 1, r, False))
            continue
        best0 = best1 = 1 << 30
        if drop:
            v = inrun[key + width]
            if v < best1:
                best1 = v
            if v + 1 < best0:
                best0 = v + 1
        if add:
            v = inrun[key + 1]
            if v < best1:
                best1 = v
            if v + 1 < best0:
                best0 = v + 1
        if keep:
            v = quiet[key + width + 1]
            if v < best1:
                best1 = v
            if v < best0:
                best0 = v
        quiet[key] = best0
        inrun[key] = best1

    ops = []
    emit = ops.append
    i = j = 0
    r = total
    open_run = False
    while i < n or j < m:
        key = i * width + j
        drop, add, keep = choices(i, j, r)
        want = inrun[key] if open_run else quiet[key]
        cost = 0 if open_run else 1
        if drop and inrun[key + width] + cost == want:
            emit(["-", i])
            i += 1
            r -= 1
            open_run = True
        elif add and inrun[key + 1] + cost == want:
            emit(["+", j])
            j += 1
            r -= 1
            open_run = True
        else:
            i += 1
            j += 1
            open_run = False
    return ops



INF = (1 << 30, 1 << 30)


def _table(before, after):
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
