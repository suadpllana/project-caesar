"""The rule with one thing changed, for measuring what a reading is worth.

Every candidate here is the same three-tier rule -- fewest moves, then fewest
of something, then the reading order -- differing only in what the second tier
counts. `solve` walks a table over (position, state) exactly as the shipped
model does, so a candidate is defined by its automaton alone and nothing else
can drift between them.
"""

BIG = 1 << 30


def solve(before, after, states, start, step):
    """states: how many; start: the state a walk begins in; step(s, move) ->
    (cost, next state) for move in '-', '+', '='."""
    n, m = len(before), len(after)
    rest = [[[None] * (m + 1) for _ in range(n + 1)] for _ in range(states)]
    for s in range(states):
        rest[s][n][m] = (0, 0)
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            keeps = i < n and j < m and before[i] == after[j]
            for s in range(states):
                best = (BIG, BIG)
                if i < n:
                    cost, nxt = step(s, "-")
                    moves, count = rest[nxt][i + 1][j]
                    pair = (moves + 1, count + cost)
                    if pair < best:
                        best = pair
                if j < m:
                    cost, nxt = step(s, "+")
                    moves, count = rest[nxt][i][j + 1]
                    pair = (moves + 1, count + cost)
                    if pair < best:
                        best = pair
                if keeps:
                    cost, nxt = step(s, "=")
                    moves, count = rest[nxt][i + 1][j + 1]
                    pair = (moves, count + cost)
                    if pair < best:
                        best = pair
                rest[s][i][j] = best
    i = j = 0
    s = start
    ops = []
    while i < n or j < m:
        want = rest[s][i][j]
        if i < n:
            cost, nxt = step(s, "-")
            moves, count = rest[nxt][i + 1][j]
            if (moves + 1, count + cost) == want:
                ops.append(("-", i))
                i += 1
                s = nxt
                continue
        if j < m:
            cost, nxt = step(s, "+")
            moves, count = rest[nxt][i][j + 1]
            if (moves + 1, count + cost) == want:
                ops.append(("+", j))
                j += 1
                s = nxt
                continue
        cost, nxt = step(s, "=")
        moves, count = rest[nxt][i + 1][j + 1]
        assert (moves, count + cost) == want
        i += 1
        j += 1
        s = nxt
    return ops


def context(width):
    """The shipped rule, with the number of kept lines that ends a comment
    read as `width`. State is keeps since the last move, capped."""
    def rule(before, after):
        def step(s, move):
            if move == "=":
                return 0, min(s + 1, width)
            return (1 if s == width else 0), 0
        return solve(before, after, width + 1, width, step)
    return rule


def runs(before, after):
    """Fewest runs of moves: no merging at all, which is what a reader who
    takes a comment to hang off each run of moves implements."""
    def step(s, move):
        if move == "=":
            return 0, 0
        return (0 if s == 1 else 1), 1
    return solve(before, after, 2, 0, step)


def split_runs(before, after):
    """Drops and adds counted as separate runs, which is how a diff prints
    one."""
    def step(s, move):
        if move == "=":
            return 0, 0
        if move == "-":
            return (0 if s == 1 else 1), 1
        return (0 if s == 2 else 1), 2
    return solve(before, after, 3, 0, step)


def merge_by_moves(before, after):
    """A reading that merges across a single kept line only when the run
    before it was a single move: plausible, and not the rule."""
    def step(s, move):
        if move == "=":
            return 0, min(s + 1, 3) if s else 3
        return (1 if s == 3 else 0), 0
    return solve(before, after, 4, 3, step)
