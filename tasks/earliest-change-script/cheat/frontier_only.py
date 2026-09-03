"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: stop one engine short. The rule is computed exactly -- keeps since
the last move carried through the walk, comments merged across a kept line or
two, the recurrence evaluated only where a shortest path can reach -- and the
frontier answers twelve of the eighteen timed pairs comfortably, which is
every pair whose two sides still resemble each other. A million lines that
differ in a few hundred places take a fifth of a second, and fifty thousand
crowded lines that differ in a few thousand take a few seconds more. Having
built that, there is nothing in the task's own worked examples to say a second
engine is needed at all.

The six that share no order have nothing left to answer them. Their scripts
run past the length of the file, so the number of moves is in the hundreds of
thousands and the frontier is out by orders of magnitude; what it falls back
on is the table, which is out by more. Every correctness block passes, six of
the eighteen timed pairs never come back, and it scores zero.
"""

from bisect import bisect_left
from collections import deque

# How many kept lines it takes to end a comment: fewer than this many between
# two runs of moves and they are read as one change.
CONTEXT = 3
_FAR = CONTEXT
_ZERO = (0,) * (CONTEXT + 1)

# Microseconds, measured. Only the ratios matter: they separate engines whose
# costs on this distribution sit orders of magnitude apart.
_FRONTIER_ENTRY = 0.25
_PAIRS_ELEMENT = 1.0
_PAIRS_MATCH = 1.6

# The frontier keeps every layer, and a layer at depth d has about d entries.
# Above this depth the layers alone would not fit in the memory the task is
# graded with, so the frontier is never allowed to run past it.
_FRONTIER_CAP = 5000


def changes(before, after, engine=None):
    n, m = len(before), len(after)

    # Comparing small integers is a good deal cheaper than comparing strings,
    # and both engines spend nearly all of their time on that comparison.
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in before]
    b = [ids.setdefault(line, len(ids)) for line in after]

    limit = _FRONTIER_CAP
    layers = _layers_from_end(a, b, n, m, limit)
    if layers is None:
        return _table(before, after)
    return _frontier_engine(a, b, n, m, layers)


def _pairs_cost(a, b, n, m):
    """How many positions match across the two sides, priced. Counting them
    costs one pass and is worth it: it is the one cost that cannot be read off
    the two lengths."""
    left = {}
    for value in a:
        left[value] = left.get(value, 0) + 1
    right = {}
    for value in b:
        right[value] = right.get(value, 0) + 1
    if len(right) < len(left):
        left, right = right, left
    total = 0
    for value, count in left.items():
        other = right.get(value)
        if other:
            total += count * other
    return _PAIRS_ELEMENT * (n + m) + _PAIRS_MATCH * total


def _frontier_limit(fallback):
    """How many moves the frontier is allowed before whichever of the other
    is cheaper takes over. Stop it once the work it has already done
    reaches a quarter of what that engine would cost, and the wasted effort is
    bounded by that figure."""
    limit = int((0.25 * fallback / _FRONTIER_ENTRY) ** 0.5)
    if limit < 32:
        return 32
    if limit > _FRONTIER_CAP:
        return _FRONTIER_CAP
    return limit


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


def _frontier_engine(a, b, n, m, layers):
    """The layers answer whether a drop or an add at a position still leaves
    the script shortest. Along a diagonal, each of those answers turns from no
    to yes at one row and stays yes, so from any position the next cell where
    either move becomes possible is a lookup, and every cell before it can
    only be kept through. The comment counts are computed on those cells
    alone, CONTEXT + 1 to a cell -- one for each number of keeps the walk can
    arrive with -- in the order the walk will need them. Keeping through a
    stretch is what makes that count move, so the stretch has to be measured
    rather than merely skipped."""
    total = len(layers) - 1
    if total == 0:
        return []

    def advance(i, j, r):
        """From (i, j) with r moves left: the first cell at or after it on the
        same diagonal where a drop or an add still leaves the script shortest.
        Everything between is a keep."""
        if r == 0:
            return n, m
        below = layers[r - 1]
        k = i - j
        stop = n
        reach = below.get(k + 1)
        if reach is not None and reach - 1 < stop:
            stop = reach - 1
        reach = below.get(k - 1)
        if reach is not None and reach < stop:
            stop = reach
        if stop < i:
            stop = i
        if stop - i > m - j:
            stop = i + (m - j)
        return stop, j + (stop - i)

    def choices(i, j, r):
        """Which of drop, add, keep still leave the script shortest here."""
        below = layers[r - 1]
        k = i - j
        reach = below.get(k + 1)
        drop = i < n and reach is not None and reach <= i + 1
        reach = below.get(k - 1)
        add = j < m and reach is not None and reach <= i
        keep = i < n and j < m and a[i] == b[j]
        return drop, add, keep

    # Comments still to be opened from a decision cell, one for each number of
    # keeps the walk can arrive with. A cell that is not a decision cell is
    # kept through to the next one, and those keeps count: they are what puts
    # the arriving state further from the last move.
    vals = {(n, m): _ZERO}

    def after(i, j, r, s):
        got = vals.get((i, j))
        if got is not None:
            return got[s]
        stop, jstop = advance(i, j, r)
        step = s + (stop - i)
        return vals[(stop, jstop)][step if step < _FAR else _FAR]

    def settle(i0, j0, r0):
        """Fill in the counts for every decision cell reachable from (i0, j0)
        along shortest paths, children before parents."""
        stack = [(i0, j0, r0, False)]
        while stack:
            i, j, r, ready = stack.pop()
            if (i, j) in vals:
                continue
            drop, add, keep = choices(i, j, r)
            if not ready:
                stack.append((i, j, r, True))
                nexts = []
                if drop:
                    nexts.append((i + 1, j, r - 1))
                if add:
                    nexts.append((i, j + 1, r - 1))
                if keep:
                    nexts.append((i + 1, j + 1, r))
                for x, y, rr in nexts:
                    if (x, y) in vals:
                        continue
                    x2, y2 = advance(x, y, rr)
                    if (x2, y2) not in vals:
                        stack.append((x2, y2, rr, False))
                continue
            best = [1 << 30] * (CONTEXT + 1)
            moved = 1 << 30
            if drop:
                v = after(i + 1, j, r - 1, 0)
                if v < moved:
                    moved = v
            if add:
                v = after(i, j + 1, r - 1, 0)
                if v < moved:
                    moved = v
            for s in range(CONTEXT + 1):
                if moved < 1 << 30:
                    got = moved + 1 if s == _FAR else moved
                    if got < best[s]:
                        best[s] = got
                if keep:
                    v = after(i + 1, j + 1, r, s + 1 if s < _FAR else _FAR)
                    if v < best[s]:
                        best[s] = v
            vals[(i, j)] = tuple(best)

    i, j, r = 0, 0, total
    i, j = advance(i, j, r)
    settle(i, j, r)

    ops = []
    emit = ops.append
    s = _FAR
    while (i, j) != (n, m):
        drop, add, keep = choices(i, j, r)
        want = vals[(i, j)][s]
        cost = 1 if s == _FAR else 0
        if drop and after(i + 1, j, r - 1, 0) + cost == want:
            emit(["-", i])
            i += 1
            r -= 1
            s = 0
        elif add and after(i, j + 1, r - 1, 0) + cost == want:
            emit(["+", j])
            j += 1
            r -= 1
            s = 0
        else:
            i += 1
            j += 1
            s = s + 1 if s < _FAR else _FAR
        i2, j2 = advance(i, j, r)
        if (i2, j2) != (i, j):
            step = s + (i2 - i)
            s = step if step < _FAR else _FAR
            i, j = i2, j2
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
