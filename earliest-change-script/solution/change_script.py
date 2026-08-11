"""Reference solution.

The rule asks, at every position, whether a drop still leaves the script
minimal. Answering that means knowing the fewest moves still needed from the
neighbour you would land on, and the table that holds those numbers is the
thing we cannot afford to build.

There are two ways round it and the graded pairs need both, because they cost
the opposite way round.

The first is the frontier, run from the far end. Layer d holds, for every
diagonal, the earliest position from which the end is reachable in d moves.
Once every layer is kept, "is this neighbour still on a shortest path?" is one
lookup, and the walk from the start is linear. It costs the square of the
number of moves and does not care how long the pair is, so a million lines that
differ in three hundred places is nothing to it. Ask it for a pair that shares
no order at all, where the number of moves runs to a third of the file, and it
is finished by nobody: sixty thousand lines against sixty thousand comes to
about thirty minutes.

The second is a row engine. Rows of the prefix table of the reversed pair are
held one to a machine integer, in the encoding where bit p-1 of row q answers
the drop question directly, and the whole row moves forward in five arithmetic
operations. It costs the length of the pair times its width in machine words
and does not care how many moves there are, which is the exact opposite trade:
it eats the crossed pairs in about a second and needs four minutes for the long
ones.

So run the frontier, and abandon it if the pair turns out to need more moves
than the row engine would have cost in the first place. The crossover is worth
computing rather than guessing - it moves with both the length and the number
of moves, and on this distribution the two families sit two orders of magnitude
either side of it.

Three details are load-bearing. The layers are produced in rising order and
consumed in falling order, so streaming them does not work. The row engine's
walk reads its rows in falling order too, so the pass leaves a checkpoint every
so often and each block is rebuilt on the way back rather than all of them
being held at once. And the usual first optimisation, cutting the shared head
and tail off before starting, changes the answer here, because a drop is
preferred over a keep whenever both leave the script shortest - so the first
move is not always a keep even when the two sequences begin with the same line.
"""

_MASK_BUDGET = 64 << 20      # bytes of materialised occurrence bitmaps
_BLOCK_BUDGET = 48 << 20     # bytes of rebuilt rows held during the walk


def changes(before, after):
    n, m = len(before), len(after)

    # Comparing small integers is a good deal cheaper than comparing strings,
    # and both engines spend nearly all their time on that comparison.
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in before]
    b = [ids.setdefault(line, len(ids)) for line in after]

    layers = _layers_from_end(a, b, n, m, _frontier_limit(n, m))
    if layers is None:
        return _row_engine(a, b, n, m)
    return _walk(a, b, n, m, layers)


def _frontier_limit(n, m):
    """How many moves the frontier is allowed before the row engine wins.

    Both constants are measured, in microseconds: a layer entry costs about
    half of one, and a row costs about a tenth plus a hundredth for every
    machine word of its width. Stop the frontier once the work it has already
    done reaches the whole of what the row engine would cost, and the wasted
    effort is bounded by that same figure.
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
    makes the lookup in the walk a single comparison.

    None when the pair needs more moves than `limit`, which hands the pair to
    the row engine.
    """
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
            # Reaching diagonal k costs one move from either neighbour: from
            # k + 1 by dropping a line of the first sequence, from k - 1 by
            # adding a line of the second. Take whichever lands earlier.
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
    """Forward from the start, spending one move at a time. Ask about the drop
    first, the add second, and take the keep when neither can begin a shortest
    script."""
    remaining = len(layers) - 1
    ops = []
    i = j = 0
    while i < n or j < m:
        if remaining == 0:
            break                      # everything left matches, line for line
        below = layers[remaining - 1]
        k = i - j
        reach = below.get(k + 1)
        if i < n and reach is not None and reach <= i + 1:
            ops.append(("-", i))
            i += 1
            remaining -= 1
            continue
        reach = below.get(k - 1)
        if j < m and reach is not None and reach <= i:
            ops.append(("+", j))
            j += 1
            remaining -= 1
            continue
        i += 1
        j += 1
    return ops


def _row_engine(a, b, n, m):
    """One row of the prefix table of the reversed pair per machine integer.

    Bit p-1 of row q is set exactly when the prefixes of length p and p-1 share
    a longest subsequence of the same length with the first q lines of the
    other side, which is the drop question asked in reverse coordinates. The
    walk needs rows q and q-1 with q falling, so the forward pass keeps a
    checkpoint every `step` rows and each block is rebuilt once behind it.
    """
    if n == 0:
        return [("+", j) for j in range(m)]
    if m == 0:
        return [("-", i) for i in range(n)]

    A = a[::-1]
    B = b[::-1]
    nbytes = (n + 7) >> 3
    full = (1 << n) - 1

    # Occurrence bitmaps, one per distinct line. A pair with a line for every
    # position would need a bitmap per position, so the frequent lines get a
    # bitmap and the rest are built from their position lists when asked for,
    # which costs their occurrence count and no more.
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
                emit(("-", n - p))
                p -= 1
                continue
        if q > 0:
            t = p - 1
            if p > 0 and A[t] == B[q - 1] and (under[t >> 3] >> (t & 7)) & 1:
                p -= 1                 # keep: neither a drop nor an add fits
            else:
                emit(("+", m - q))
            q -= 1
            here = under
            under = bits(q - 1) if q else None
        else:
            emit(("-", n - p))
            p -= 1
    return ops
