"""The definitional model: the rule written out, with nothing clever in it.

Three tiers. The script is shortest; of the shortest scripts it has the fewest
comments, a comment being a run of moves together with any later run that only
a line or two of kept lines separates from it; and of those it is the one whose
reading comes first with a drop ahead of an add and an add ahead of a keep.

CONTEXT is how many kept lines it takes to end a comment. Two runs of moves
with fewer than that many keeps between them are read as one change and take
one comment between them; that many or more and the second starts a comment of
its own. The table therefore carries, alongside the position, how many keeps
have gone by since the last move, capped at CONTEXT because nothing past it
matters. That count is the whole of the state: a run of moves is open exactly
when the count is zero, and a comment is charged only where a move arrives with
the count already at the cap.

The walk from the start then takes a drop whenever a drop still reaches the
best pair, otherwise an add, otherwise a keep, which is the third tier. Slow
and quadratic, which is the point: the answers it produces are derived from the
rule rather than from a second attempt at the efficient algorithm, so a
misunderstanding cannot pass both.

`every_script` is the same rule enforced by exhaustion over every script a pair
admits, with no table at all. A test holds the two to each other on the short
shapes, so the table itself is checked against the words of the rule.
"""

CONTEXT = 3

INF = (1 << 30, 1 << 30)


def table(before, after):
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


def script(before, after):
    n, m = len(before), len(after)
    rest = table(before, after)
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


def comments_in(reading):
    """The rule's own words, counted off a reading: a move starts a comment
    only when at least CONTEXT keeps have gone by since the previous move."""
    count = 0
    since = CONTEXT
    for step in reading:
        if step == "=":
            if since < CONTEXT:
                since += 1
        else:
            if since == CONTEXT:
                count += 1
            since = 0
    return count


def every_script(before, after):
    """The rule by exhaustion: enumerate every script, read each one back, and
    keep the one that wins on (moves, comments, reading). Exponential; for
    pairs of a handful of lines only."""
    n, m = len(before), len(after)
    order = {"-": 0, "+": 1, "=": 2}
    best = [None, None]

    def visit(i, j, reading, ops):
        if i == n and j == m:
            key = (sum(1 for step in reading if step != "="),
                   comments_in(reading),
                   [order[step] for step in reading])
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
