"""The grading side's fast implementation of the rule.

The definitional model in oracle.py is the authority, and it is what the small
blocks are graded against. It cannot be used on a fifty thousand line pair --
the table alone would be several billion entries, twice over -- so the medium
and timed blocks are graded against this instead, and a test asserts that the
two agree on every fixed and enumerated case before any of those answers count.

Two engines, because the graded pairs sit in two places and neither covers the
other. Their costs are independent of each other:

  frontier   the square of the number of moves, plus the cells where a choice
             between shortest scripts exists; untouched by the length of the
             pair or by how repetitive it is
  pairs      the number of positions that match across the two sides,
             untouched by the length of the pair and by the number of moves

A pair that differs in a few hundred or a few thousand places belongs to the
first, whether it is a million lines of a few hundred distinct ones or fifty
thousand lines of three. A pair of a third of a million nearly-distinct lines
put back in a different order belongs to the second: its moves run past the
length of the file, so the frontier is out by orders of magnitude, but almost
nothing in it matches anything, which is the only cheap thing about it.

Both engines answer the same question at every position of the walk. The
number of moves that remain is one part of it and is what every fast diff
computes. The other part is how many comments a shortest completion can still
be done in, and that is a second quantity with its own recurrence: a run of
moves that is already open extends for nothing, and a later run opens a comment
of its own only once CONTEXT keeps have gone by. So the state is not a flag but
a count of keeps since the last move, held at CONTEXT once it gets there, and
both engines carry CONTEXT + 1 numbers where a shortest-script engine carries
none. Only cells that lie on some shortest path can be on the answer, so the
second quantity is only ever computed there.

Lives in /tests, which the account that runs submitted code cannot read.
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

    if engine == "pairs":
        return _pairs_engine(a, b, n, m)

    limit = 1 << 30 if engine == "frontier" else _frontier_limit(
        _pairs_cost(a, b, n, m))
    layers = _layers_from_end(a, b, n, m, limit)
    if layers is None:
        return _pairs_engine(a, b, n, m)
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


# ------------------------------------------------------------ pairs engine --
#
# Thresholds over suffixes, one pass from the far end: it changes only where
# the two sides match, so it costs the number of matching positions rather
# than the length of the pair, and it hands every match its rank -- how many
# keeps a shortest script can still make from it, counting itself. The matches
# of one rank form a staircase, later in one side meaning earlier in the other,
# so "the matches of the next rank that lie below and to the right of this one"
# is a contiguous stretch of the next staircase. A rule that counted runs would
# take one sliding minimum over that stretch; this one cannot, because the keep
# straight down the diagonal carries the keep count forward where every other
# keep in the stretch resets it, so it is held out of the minimum instead. That
# splits the stretch in two -- one more row down, or one more column across --
# and each piece is contiguous in a staircase, so it is two windows and not one.
# The walk never leaves the staircases: each move it considers narrows the
# stretch it may still land in, and the question is whether a keep with the
# required count is still inside.


def _pairs_engine(a, b, n, m):
    if n == 0:
        return [["+", j] for j in range(m)]
    if m == 0:
        return [["-", i] for i in range(n)]

    where = {}
    for position, value in enumerate(b):
        seen = where.get(value)
        if seen is None:
            where[value] = [position]
        else:
            seen.append(position)

    # held[k] is -t[k], so the list ascends and bisect applies directly. The
    # slot a match lands in is its rank.
    held = [-m]
    rows = [None]
    cols = [None]
    for i in range(n - 1, -1, -1):
        positions = where.get(a[i])
        if not positions:
            continue
        for position in positions:      # ascending, so the slot only moves down
            value = -position
            slot = bisect_left(held, value)
            if slot == len(held):
                held.append(value)
                rows.append([i])
                cols.append([position])
            else:
                held[slot] = value
                rows[slot].append(i)
                cols[slot].append(position)
    top = len(held) - 1
    if top == 0:
        return [["-", i] for i in range(n)] + [["+", j] for j in range(m)]

    # Filled with i descending and j ascending within a row; reversed, each
    # rank runs with i ascending and j never increasing.
    for rank in range(1, top + 1):
        rows[rank].reverse()
        cols[rank].reverse()

    BIG = 1 << 30

    # counts[rank][s - 1][t]: comments still to be opened after keeping match t
    # of that rank, arriving there with s keeps already behind it, s running
    # from one to CONTEXT. One number a match would do for a rule that only
    # counted runs; here how far the walk is from the last move decides whether
    # the next one is a comment of its own, and that survives a keep.
    counts = [None] * (top + 1)
    base = []
    for s in range(1, CONTEXT + 1):
        charge = 1 if s == _FAR else 0
        base.append([0 if (x + 1 == n and y + 1 == m) else charge
                     for x, y in zip(rows[1], cols[1])])
    counts[1] = base

    for rank in range(2, top + 1):
        ii, jj = rows[rank], cols[rank]
        pi, pj = rows[rank - 1], cols[rank - 1]
        below = counts[rank - 1]
        after_gap = below[0]            # a gap lands on the next keep at s = 1
        count = len(pi)
        size = len(ii)
        out = [[BIG] * size for _ in range(CONTEXT)]

        # A keep of the next rank that is NOT the one straight down the
        # diagonal has a move between it and this one. Those split into two
        # stretches -- one more row down, or one more column across -- and each
        # is contiguous in a rank that runs with i ascending and j never
        # increasing, so each takes an ordinary sliding minimum. The straight
        # diagonal keep is in neither, which is the point: it opens nothing and
        # it carries the keep count forward instead of resetting it.
        lo_row = hi_row = 0             # i >= x + 1, j >= y + 2
        lo_col = hi_col = 0             # i >= x + 2, j >= y + 1
        win_row = deque()
        win_col = deque()
        for t in range(size):
            x = ii[t]
            y = jj[t]
            while hi_row < count and pj[hi_row] > y + 1:
                f = after_gap[hi_row]
                while win_row and after_gap[win_row[-1]] >= f:
                    win_row.pop()
                win_row.append(hi_row)
                hi_row += 1
            while lo_row < count and pi[lo_row] <= x:
                lo_row += 1
            while win_row and win_row[0] < lo_row:
                win_row.popleft()
            while hi_col < count and pj[hi_col] > y:
                f = after_gap[hi_col]
                while win_col and after_gap[win_col[-1]] >= f:
                    win_col.pop()
                win_col.append(hi_col)
                hi_col += 1
            while lo_col < count and pi[lo_col] <= x + 1:
                lo_col += 1
            while win_col and win_col[0] < lo_col:
                win_col.popleft()

            gap = BIG
            if win_row:
                value = after_gap[win_row[0]]
                if value < gap:
                    gap = value
            if win_col:
                value = after_gap[win_col[0]]
                if value < gap:
                    gap = value

            straight = -1
            probe = bisect_left(pi, x + 1)
            while probe < count and pi[probe] == x + 1:
                if pj[probe] == y + 1:
                    straight = probe
                    break
                probe += 1

            for s in range(1, CONTEXT + 1):
                best = BIG
                if gap < BIG:
                    best = gap + 1 if s == _FAR else gap
                if straight >= 0:
                    nxt = s + 1 if s < _FAR else _FAR
                    value = below[nxt - 1][straight]
                    if value < best:
                        best = value
                out[s - 1][t] = best
        counts[rank] = out

    def last_at_least(jj, y):
        """jj never increases: one past the last index with jj[idx] >= y."""
        lo, hi = 0, len(jj)
        while lo < hi:
            mid = (lo + hi) >> 1
            if jj[mid] >= y:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def slot_of(rank, x, y):
        ii, jj = rows[rank], cols[rank]
        t = bisect_left(ii, x)
        while t < len(ii) and ii[t] == x:
            if jj[t] == y:
                return t
            t += 1
        raise AssertionError("the walk left the staircases")

    ops = []
    emit = ops.append
    x = y = 0
    rank = top
    s = _FAR

    # The count the walk must realise from the start: a keep at the origin if
    # there is one, otherwise a run opened before the first keep. A move made
    # before any keep is always a comment of its own, there being nothing in
    # front of it to join.
    after_gap = counts[top][0]
    target = min(after_gap) + 1
    ii, jj = rows[top], cols[top]
    for t in range(len(ii)):
        if ii[t] == 0 and jj[t] == 0:
            value = counts[top][_FAR - 1][t]
            if value < target:
                target = value
            break

    while rank > 0:
        ii, jj = rows[rank], cols[rank]
        after_gap = counts[rank][0]
        by_count = {}
        for t, f in enumerate(after_gap):
            lst = by_count.get(f)
            if lst is None:
                by_count[f] = [t]
            else:
                lst.append(t)

        def reachable(x, y, wanted):
            """Is a keep of this rank with the wanted count at or after
            (x, y) on both sides? Once a move has been made the walk is at
            no keeps since the last one, so the count it must meet is the
            one a gap lands on."""
            lst = by_count.get(wanted)
            if not lst:
                return False
            lo = bisect_left(ii, x)
            hi = last_at_least(jj, y)
            p = bisect_left(lst, lo)
            return p < len(lst) and lst[p] < hi

        while True:
            wanted = target - 1 if s == _FAR else target
            if x < n and reachable(x + 1, y, wanted):
                emit(["-", x])
                x += 1
            elif y < m and reachable(x, y + 1, wanted):
                emit(["+", y])
                y += 1
            else:
                break
            s = 0
            target = wanted
        # Nothing shortest and as cheap in comments starts with a move here,
        # so this is a keep, and it carries the keep count one further along.
        nxt = s + 1 if s < _FAR else _FAR
        target = counts[rank][nxt - 1][slot_of(rank, x, y)]
        s = nxt
        x += 1
        y += 1
        rank -= 1
    for i in range(x, n):
        emit(["-", i])
    for j in range(y, m):
        emit(["+", j])
    return ops
