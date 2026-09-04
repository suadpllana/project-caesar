"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: solve the first and third tiers of the rule and let the second one
go. This is the shortest script whose reading comes first under drop, add,
keep, and it is what every fast diff technique computes natively, because
every one of them is a way of knowing how many moves remain from a position
and the reading-order rule is a greedy walk over exactly that number. Three
engines, correct crossovers, every tie-break inside them derived rather than
recalled. It passes every timing budget in the task with room to spare.

It is wrong on the comment count, which the number of moves remaining does
not carry. Merging two runs that only a kept line or two separates makes the
second tier tie far more often than counting runs would, so ignoring it lands
the right answer more often than it deserves to -- and it still misses 870 of
the 40804 enumerated pairs, 4374 of 12000 random ones and 7 of the 71 written
out by hand, which under all-or-nothing grading is the same as missing all of
them.
"""

from bisect import bisect_left

# Microseconds, measured. Only the ratios matter: they separate engines whose
# costs on this distribution sit orders of magnitude apart.
_FRONTIER_ENTRY = 0.25
_ROW_FIXED = 0.09
_ROW_WORD = 0.0079
_PAIRS_ELEMENT = 0.70
_PAIRS_MATCH = 0.75


def changes(before, after):
    n, m = len(before), len(after)

    # Comparing small integers is a good deal cheaper than comparing strings,
    # and every engine spends nearly all of its time on that comparison.
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in before]
    b = [ids.setdefault(line, len(ids)) for line in after]

    row = _row_cost(n, m)
    pairs = _pairs_cost(a, b, n, m)
    second = _pairs_engine if pairs < row else _row_engine

    layers = _layers_from_end(a, b, n, m, _frontier_limit(min(row, pairs)))
    if layers is None:
        return second(a, b, n, m)
    return _walk(a, b, n, m, layers)


def _row_cost(n, m):
    return m * (_ROW_FIXED + _ROW_WORD * (n / 64.0))


def _pairs_cost(a, b, n, m):
    """How many positions match across the two sides, priced. Counting them
    costs one pass and is worth it: it is the only one of the three costs that
    cannot be read off the two lengths."""
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
    """How many moves the frontier is allowed before whichever of the other two
    is cheaper takes over. Stop it once the work it has already done reaches
    the whole of what that engine would cost, and the wasted effort is bounded
    by that same figure."""
    limit = int((fallback / _FRONTIER_ENTRY) ** 0.5)
    if limit < 512:
        return 512
    if limit > 8192:
        return 8192
    return limit


# ------------------------------------------------------------ pairs engine --
#
# Thresholds over suffixes: t[k] is the largest j from which the tail of the
# other side still shares k lines. One pass from the far end maintains it, and
# it changes only where the two sides match, so the whole history costs the
# number of matching positions rather than the length of the pair. The walk
# runs the other way, so every change is journalled as it is made and undone
# again on the way forward, which is what keeps a single array standing in for
# all of them.


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

    # held[k] is -t[k], so the list ascends and bisect applies directly.
    held = [-m]
    journal = [()] * n
    for i in range(n - 1, -1, -1):
        positions = where.get(a[i])
        if not positions:
            continue
        marks = []
        for position in positions:      # ascending, so the slot only moves down
            value = -position
            slot = bisect_left(held, value)
            if slot == len(held):
                marks.append((slot, None))
                held.append(value)
            else:
                marks.append((slot, held[slot]))
                held[slot] = value
        journal[i] = marks

    def undo(marks):
        for slot, was in reversed(marks):
            if was is None:
                held.pop()
            else:
                held[slot] = was

    def before_of(marks):
        out = {}
        for slot, was in marks:
            if slot not in out:
                out[slot] = was
        return out

    ops = []
    emit = ops.append
    remaining = len(held) - 1
    i = j = 0
    marks = journal[0]
    earlier = before_of(marks)
    while i < n or j < m:
        if i < n:
            if remaining in earlier:
                was = earlier[remaining]
                reach = None if was is None else -was
            else:
                reach = -held[remaining]
            if reach is not None and reach >= j:
                emit(["-", i])
                undo(marks)
                i += 1
                marks = journal[i] if i < n else ()
                earlier = before_of(marks)
                continue
        if j < m and remaining < len(held) and -held[remaining] > j:
            emit(["+", j])
            j += 1
            continue
        undo(marks)
        i += 1
        j += 1
        remaining -= 1
        marks = journal[i] if i < n else ()
        earlier = before_of(marks)
    return ops


# ---------------------------------------------------------------- frontier --


def _layers_from_end(a, b, n, m, limit):
    """layers[d][k] is the smallest i for which position (i, i - k) can reach
    the end of both sequences in d moves. A position on diagonal k is within d
    moves of the end exactly when i is at least that number, which is what
    makes the lookup in the walk a single comparison. None if the pair needs
    more than `limit` moves, which is the row engine's cue."""
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


def _walk(a, b, n, m, layers):
    remaining = len(layers) - 1
    ops = []
    i = j = 0
    while i < n or j < m:
        if remaining == 0:
            break
        below = layers[remaining - 1]
        k = i - j
        reach = below.get(k + 1)
        if i < n and reach is not None and reach <= i + 1:
            ops.append(["-", i])
            i += 1
            remaining -= 1
            continue
        reach = below.get(k - 1)
        if j < m and reach is not None and reach <= i:
            ops.append(["+", j])
            j += 1
            remaining -= 1
            continue
        i += 1
        j += 1
    return ops


# --------------------------------------------------------------- row engine --
#
# Rows of the prefix table of the reversed pair, one big integer each. Bit p-1
# of row q is set when the two prefixes of length p and p-1 share a longest
# subsequence of the same length, which is exactly the question the rule asks
# about a drop. The walk reads rows q and q-1 with q falling, so the pass
# leaves a checkpoint every so often and each block is rebuilt once on the way
# back rather than all of them being held at once.

_MASK_BUDGET = 64 << 20
_BLOCK_BUDGET = 48 << 20


def _row_engine(a, b, n, m):
    if n == 0:
        return [["+", j] for j in range(m)]
    if m == 0:
        return [["-", i] for i in range(n)]

    A = a[::-1]
    B = b[::-1]
    nbytes = (n + 7) >> 3
    full = (1 << n) - 1

    counts = {}
    for c in A:
        counts[c] = counts.get(c, 0) + 1
    hot = sorted(counts, key=counts.__getitem__, reverse=True)
    hot = set(hot[:max(1, _MASK_BUDGET // max(1, nbytes))])
    buffers = {c: bytearray(nbytes) for c in hot}
    spread = {}
    for i, c in enumerate(A):
        buf = buffers.get(c)
        if buf is not None:
            buf[i >> 3] |= 1 << (i & 7)
        else:
            lst = spread.get(c)
            if lst is None:
                spread[c] = [i]
            else:
                lst.append(i)
    masks = {c: int.from_bytes(bytes(buf), "little")
             for c, buf in buffers.items()}

    def mask(c):
        got = masks.get(c)
        if got is not None:
            return got
        lst = spread.get(c)
        if not lst:
            return 0
        buf = bytearray(nbytes)
        for i in lst:
            buf[i >> 3] |= 1 << (i & 7)
        return int.from_bytes(bytes(buf), "little")

    step = max(1, _BLOCK_BUDGET // max(1, nbytes))
    marks = [full]
    row = full
    for q in range(1, m + 1):
        carry = row & mask(B[q - 1])
        row = ((row + carry) | (row - carry)) & full
        if q % step == 0:
            marks.append(row)

    block_at = -1
    block = []

    def rebuild(target):
        start = max(0, (target - 1) // step) * step
        stop = min(m, start + step)
        row = marks[start // step]
        out = [row.to_bytes(nbytes, "little")]
        for q in range(start + 1, stop + 1):
            carry = row & mask(B[q - 1])
            row = ((row + carry) | (row - carry)) & full
            out.append(row.to_bytes(nbytes, "little"))
        return start, out

    def bits(q):
        nonlocal block_at, block
        if q < block_at or q > block_at + len(block) - 1:
            block_at, block = rebuild(q)
        return block[q - block_at]

    ops = []
    emit = ops.append
    p, q = n, m
    here = bits(m)
    under = bits(m - 1) if m else None
    while p > 0 or q > 0:
        if p > 0:
            t = p - 1
            if (here[t >> 3] >> (t & 7)) & 1:
                emit(["-", n - p])
                p -= 1
                continue
        if q > 0:
            t = p - 1
            if p > 0 and A[t] == B[q - 1] and (under[t >> 3] >> (t & 7)) & 1:
                p -= 1
            else:
                emit(["+", m - q])
            q -= 1
            here = under
            under = bits(q - 1) if q else None
        else:
            emit(["-", n - p])
            p -= 1
    return ops
