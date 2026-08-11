"""The grading side's fast implementation of the rule.

The definitional model in oracle.py is the authority, and it is what the small
blocks are graded against. It cannot be used on a sixty thousand line pair --
the table alone would be nearly four billion entries -- so the medium and timed
blocks are graded against this instead, and a test asserts that the two agree
on every fixed and enumerated case before any of those answers count.

Two engines, because the graded pairs sit on both sides of a crossover and no
single one of them covers both. The frontier costs the square of the number of
moves and is untouched by the length of the pair; the row engine costs the
length of the pair times its width in machine words and is untouched by the
number of moves. Long pairs that differ in a few hundred places belong to the
first, pairs that share little belong to the second, and the estimate below
decides between them. Lives in /tests, which the account that runs submitted
code cannot read.
"""


def changes(before, after):
    n, m = len(before), len(after)
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in before]
    b = [ids.setdefault(line, len(ids)) for line in after]

    layers = _layers_from_end(a, b, n, m, _frontier_limit(n, m))
    if layers is None:
        return _row_engine(a, b, n, m)
    return _walk(a, b, n, m, layers)


def _frontier_limit(n, m):
    """How many moves the frontier is allowed before the row engine is cheaper.

    Both constants are measured, in microseconds: a layer entry costs about
    half of one, and a row of the table costs about a tenth plus a hundredth
    for every machine word of its width. The frontier is abandoned once the
    work it has already done reaches the whole of what the row engine would
    cost, which bounds the waste by that same figure.
    """
    rows = m * (0.09 + 0.0079 * (n / 64.0))
    limit = int((rows / 0.25) ** 0.5)
    if limit < 512:
        return 512
    if limit > 4096:
        return 4096
    return limit


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
