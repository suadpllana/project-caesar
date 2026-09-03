"""Alternative correct implementation. Must score 1.

The reference skips along every run of keeps and computes the hunk counts on
the cells where a choice exists. This one does the natural thing on the
frontier's side instead: it visits every cell that lies on some shortest path,
one at a time, and fills in the two counts for each. Same layers, same row
engine, same pairs engine, same answers; the only difference is that on the
long family the hunk recurrence is evaluated at every cell rather than at the
decision cells, which costs the length of the pair. It is the implementation a
solver who has found the shortest-path restriction writes first, and it is
inside every budget, which is what makes the budgets fair.
"""

from bisect import bisect_left
from collections import deque

# Microseconds, measured. Only the ratios matter: they separate engines whose
# costs on this distribution sit orders of magnitude apart.
_FRONTIER_ENTRY = 0.25
_ROW_FIXED = 0.9
_ROW_WORD = 0.079
_PAIRS_ELEMENT = 1.0
_PAIRS_MATCH = 1.6

# Bytes of occurrence masks the row engine materialises up front, and bytes of
# rebuilt rows it holds while the sweep runs.
_MASK_BUDGET = 64 << 20
_BLOCK_BUDGET = 48 << 20

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
    if engine == "rows":
        return _rows_engine(a, b, n, m)

    rows = _rows_cost(n, m)
    pairs = _pairs_cost(a, b, n, m)
    second = _pairs_engine if pairs < rows else _rows_engine

    limit = 1 << 30 if engine == "frontier" else _frontier_limit(min(rows, pairs))
    layers = _layers_from_end(a, b, n, m, limit)
    if layers is None:
        return second(a, b, n, m)
    return _frontier_engine(a, b, n, m, layers)


def _rows_cost(n, m):
    return n * (_ROW_FIXED + _ROW_WORD * (m / 64.0))


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
    two is cheaper takes over. Stop it once the work it has already done
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
    needs more than `limit` moves, which is the other engines' cue."""
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


# --------------------------------------------------------------- row engine --
#
# Rows of the prefix table, one big integer each, advanced by the five-operation
# bit-parallel step; bit j of row i is set when the two prefixes of after of
# length j and j+1 share a longest subsequence of the same length. That answers
# how many moves remain, and nothing else. The cells that lie on some shortest
# path are then read off row by row, from the bottom up, with a handful of
# integer operations per row: a cell is on a shortest path when a drop, an add
# or a keep from it lands on one. The add is a bit of the row; the keep is a bit
# of the line's occurrence mask; and the drop asks whether the prefix table is
# equal in two consecutive rows at that column, which is true everywhere except
# on the stretches between the columns where a step appears in the lower row
# and the columns where one disappears - those alternate, so one subtraction
# fills every stretch at once. The cells that come out are a few per row on any
# pair, and the hunk counts are computed on those alone.

def _rows_engine(a, b, n, m):
    if n == 0:
        return [["+", j] for j in range(m)]
    if m == 0:
        return [["-", i] for i in range(n)]
    nbytes = (m + 7) >> 3
    full = (1 << m) - 1

    counts = {}
    for c in b:
        counts[c] = counts.get(c, 0) + 1
    hot = sorted(counts, key=counts.__getitem__, reverse=True)
    hot = set(hot[:max(1, _MASK_BUDGET // max(1, nbytes))])
    buffers = {c: bytearray(nbytes) for c in hot}
    spread = {}
    for j, c in enumerate(b):
        buf = buffers.get(c)
        if buf is not None:
            buf[j >> 3] |= 1 << (j & 7)
        else:
            lst = spread.get(c)
            if lst is None:
                spread[c] = [j]
            else:
                lst.append(j)
    masks = {c: int.from_bytes(bytes(buf), "little") for c, buf in buffers.items()}

    def mask(c):
        got = masks.get(c)
        if got is not None:
            return got
        lst = spread.get(c)
        if not lst:
            return 0
        buf = bytearray(nbytes)
        for j in lst:
            buf[j >> 3] |= 1 << (j & 7)
        return int.from_bytes(bytes(buf), "little")

    # Forward rows. V_i bit j set <=> P(i, j+1) == P(i, j): no step at j.
    step = max(1, _BLOCK_BUDGET // max(1, nbytes))
    marks = [full]
    row = full
    for i in range(1, n + 1):
        carry = row & mask(a[i - 1])
        row = ((row + carry) | (row - carry)) & full
        if i % step == 0:
            marks.append(row)

    block_at = -1
    block = []

    def rebuild(target):
        start = (target // step) * step
        if start == target and start > 0:
            start -= step
        stop = min(n, start + step)
        row = marks[start // step]
        out = [row]
        for i in range(start + 1, stop + 1):
            carry = row & mask(a[i - 1])
            row = ((row + carry) | (row - carry)) & full
            out.append(row)
        return start, out

    def V(i):
        nonlocal block_at, block
        if i < block_at or i > block_at + len(block) - 1:
            block_at, block = rebuild(i)
        return block[i - block_at]

    BIG = 1 << 30
    info = [None] * (n + 1)          # info[i] = {j: (h0, h1, dropT, addT, keepT)}
    onext = 0
    vnext = None
    topbit = 1 << m
    for i in range(n, -1, -1):
        vi = V(i)
        if i == n:
            drop_src = keep_src = 0
            seeds = topbit
            hnext = None
        else:
            # between-row difference d(j) = P(i+1, j) - P(i, j): 1 on bits u_k+1 .. v_k
            u = vi & ~vnext & full         # step appears in row i+1
            v = vnext & ~vi & full         # step disappears
            if u.bit_count() > v.bit_count():
                v |= topbit
            diff = (v - u) << 1
            drop_src = onext & ~diff
            keep_src = (onext >> 1) & mask(a[i])
            seeds = drop_src | keep_src
            hnext = info[i + 1]
        # leftward fill through tight adds: (i, j+1) in O and V_i[j] set => (i, j) in O
        oi = seeds
        x = seeds
        zi = vi
        while x:
            low = x & -x
            s = low.bit_length() - 1
            x ^= low
            if s == 0:
                continue
            below = (1 << s) - 1
            t = zi & below
            if not (t >> (s - 1)) & 1:
                continue
            r0 = (t ^ below).bit_length()
            oi |= below ^ ((1 << r0) - 1)
        # hunk counts, j descending
        cells = {}
        x = oi
        js = []
        while x:
            low = x & -x
            js.append(low.bit_length() - 1)
            x ^= low
        for j in reversed(js):
            best0 = best1 = BIG
            dropT = bool((drop_src >> j) & 1)
            keepT = bool((keep_src >> j) & 1)
            addT = j < m and bool((zi >> j) & 1) and (j + 1) in cells
            if dropT:
                h = hnext[j][1]
                if h < best1:
                    best1 = h
                if h + 1 < best0:
                    best0 = h + 1
            if addT:
                h = cells[j + 1][1]
                if h < best1:
                    best1 = h
                if h + 1 < best0:
                    best0 = h + 1
            if keepT:
                h = hnext[j + 1][0]
                if h < best1:
                    best1 = h
                if h < best0:
                    best0 = h
            if i == n and j == m:
                best0 = best1 = 0
            cells[j] = (best0, best1, dropT, addT, keepT)
        info[i] = cells
        onext = oi
        vnext = vi

    ops = []
    emit = ops.append
    i = j = 0
    open_run = False
    while i < n or j < m:
        h0, h1, dropT, addT, keepT = info[i][j]
        want = h1 if open_run else h0
        cost = 0 if open_run else 1
        if dropT and info[i + 1][j][1] + cost == want:
            emit(["-", i])
            i += 1
            open_run = True
        elif addT and info[i][j + 1][1] + cost == want:
            emit(["+", j])
            j += 1
            open_run = True
        else:
            i += 1
            j += 1
            open_run = False
    return ops


# ------------------------------------------------------------ pairs engine --
#
# Thresholds over suffixes, one pass from the far end: it changes only where
# the two sides match, so it costs the number of matching positions rather
# than the length of the pair, and it hands every match its rank -- how many
# keeps a shortest script can still make from it, counting itself. The matches
# of one rank form a staircase, later in one side meaning earlier in the other,
# so "the matches of the next rank that lie below and to the right of this one"
# is a contiguous stretch of the next staircase, and the hunk counts come out
# of a sliding window over it. The walk never leaves the staircases: each move
# it considers narrows the stretch it may still land in, and the question is
# whether a keep with the required count is still inside.


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

    # fewest[rank][t]: hunks still to be opened after keeping match t of that
    # rank. From the last keep, whatever is left is one run of moves or none.
    fewest = [None] * (top + 1)
    fewest[1] = [0 if (x + 1 == n and y + 1 == m) else 1
                 for x, y in zip(rows[1], cols[1])]
    for rank in range(2, top + 1):
        ii, jj = rows[rank], cols[rank]
        pi, pj, pf = rows[rank - 1], cols[rank - 1], fewest[rank - 1]
        count = len(pi)
        out = [0] * len(ii)
        lo = 0                 # first lower-rank match with i' > i
        hi = 0                 # one past the last with j' > j
        window = deque()       # indices into the lower rank, counts ascending
        for t in range(len(ii)):
            x = ii[t]
            y = jj[t]
            while hi < count and pj[hi] > y:
                f = pf[hi]
                while window and pf[window[-1]] >= f:
                    window.pop()
                window.append(hi)
                hi += 1
            while lo < count and pi[lo] <= x:
                lo += 1
            while window and window[0] < lo:
                window.popleft()
            best = pf[window[0]] + 1
            # The keep straight after this one continues the run of keeps and
            # opens nothing.
            s = bisect_left(pi, x + 1)
            while s < count and pi[s] == x + 1:
                if pj[s] == y + 1:
                    if pf[s] < best:
                        best = pf[s]
                    break
                s += 1
            out[t] = best
        fewest[rank] = out

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

    ops = []
    emit = ops.append
    x = y = 0
    rank = top
    open_run = False

    # The count the walk must realise from the start: a keep at the origin if
    # there is one, otherwise a run opened before the first keep.
    ff = fewest[top]
    target = min(ff) + 1
    ii, jj = rows[top], cols[top]
    for t in range(len(ii)):
        if ii[t] == 0 and jj[t] == 0:
            if ff[t] < target:
                target = ff[t]
            break

    while rank > 0:
        ii, jj, ff = rows[rank], cols[rank], fewest[rank]
        by_count = {}
        for t, f in enumerate(ff):
            lst = by_count.get(f)
            if lst is None:
                by_count[f] = [t]
            else:
                lst.append(t)

        def reachable(x, y, wanted):
            """Is a keep of this rank with the wanted count at or after
            (x, y) on both sides?"""
            lst = by_count.get(wanted)
            if not lst:
                return False
            lo = bisect_left(ii, x)
            hi = last_at_least(jj, y)
            p = bisect_left(lst, lo)
            return p < len(lst) and lst[p] < hi

        while True:
            wanted = target if open_run else target - 1
            if x < n and reachable(x + 1, y, wanted):
                emit(["-", x])
                x += 1
            elif y < m and reachable(x, y + 1, wanted):
                emit(["+", y])
                y += 1
            else:
                break
            open_run = True
            target = wanted
        # Nothing shortest and as cheap in hunks starts with a move here, so
        # this is a keep, and the count it carries is the target.
        x += 1
        y += 1
        open_run = False
        rank -= 1
    for i in range(x, n):
        emit(["-", i])
    for j in range(y, m):
        emit(["+", j])
    return ops
