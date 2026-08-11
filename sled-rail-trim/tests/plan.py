"""What a well-made apply path spends, and the ceiling that follows from it.

The ceiling is not a number of transactions written down anywhere. It is a
multiple of what this planner spends on the very same session, worked out here
against the same part model the run under test is graded on. A session that
happens to be cheap moves both sides together.

The multiple comes from measurement. Over twenty seeded sessions of twenty
rails, with the transactions counted by the part itself:

    this planner                                            1.00x
    the same, stretching each frame greedily over pads      1.06x
    the same, pairing only where both halves move           1.23x
    the same, paying the status read at every mode move     1.23x
    the same, performing every disable the batch asks for   1.26x
    the same, never restating inside a frame                1.27x
    the same, never using the pair register                 1.30x
    the same, framing only already-consecutive registers    1.37x
    the same, single writes throughout                      1.66x
    arrival order, skipping what is already in force        4.83x
    arrival order                                           6.20x

Taken eight sessions at a time, the way a graded run takes them, the second row
never goes above 1.07 and none of the rows below it ever comes under 1.15. So
1.10 passes an apply path that has all four ideas and packs its frames by hand,
and fails one that is missing any single one of them.

Sealed in /tests along with everything else that decides anything.
"""

import math

import part as P

REFERENCE_MULTIPLE = 1.10


def ceiling_from(reference_cost: int) -> int:
    return int(math.floor(REFERENCE_MULTIPLE * reference_cost))


def _settle(dev, state):
    """The part answers 0 while it is still settling, so this is a poll."""
    while dev.read(P.STATUS) != 1:
        pass
    state["settling"] = False


def _hold(dev, program, state):
    """Move the mode. The part is unsettled behind it and owes a status read,
    which the next frame carries for nothing and the next single write does
    not."""
    if state["program"] == program:
        return
    dev.write(P.MODE, 1 if program else 0)
    state["program"] = program
    state["settling"] = True


def _cover(dev, base, need, pad_ok, cur, state):
    """Emit `need` (index -> value) over one bank at the lowest cost there is.

    A frame is flat-rate and carries up to P.BURST_MAX consecutive registers,
    so registers inside a frame that nobody wants get restated at the value
    they already hold. That restatement is a write like any other and the part
    checks it like any other, which is what pad_ok decides.

    A backwards pass over the bank, so the choice at each register is made
    against the true cost of everything to its right rather than a guess. The
    second dimension is whether the part still owes a status read: a single
    write has to buy it and a frame does not, so what is cheapest at the head
    of a window is not always what is cheapest in the middle of one.
    """
    if not need:
        return
    n = dev.n
    INF = float("inf")
    best = [[INF, INF] for _ in range(n + 1)]
    how = [[None, None] for _ in range(n + 1)]
    best[n][0] = best[n][1] = 0
    for i in range(n - 1, -1, -1):
        for owed in (0, 1):
            if i in need:
                best[i][owed] = 1 + owed * P.SETTLE_LOOKS + best[i + 1][0]
                how[i][owed] = ("one", 1)
            else:
                best[i][owed] = best[i + 1][owed]
                how[i][owed] = ("skip", 1)
            for length in range(1, P.BURST_MAX + 1):
                if i + length > n:
                    break
                tail = i + length - 1
                if tail not in need and not pad_ok(tail):
                    break
                if not any(j in need for j in range(i, i + length)):
                    continue
                cost = P.BURST_COST + best[i + length][0]
                if cost < best[i][owed]:
                    best[i][owed] = cost
                    how[i][owed] = ("frame", length)

    i = 0
    owed = 1 if state["settling"] else 0
    while i < n:
        kind, length = how[i][owed]
        if kind == "frame":
            dev.burst(base + i, [need.get(j, cur[j]) for j in range(i, i + length)])
            owed = 0
            state["settling"] = False
        elif kind == "one":
            if owed:
                _settle(dev, state)
                owed = 0
            dev.write(base + i, need[i])
        i += length


def apply_batch(dev, reqs, state):
    """One batch, the way the reference does it.

    The batch's last word on each register is all that counts, so everything
    before it goes; anything the part already reads goes too. A rail only comes
    down if the batch leaves it under its own limit, because everywhere else
    the pair register lands both halves of a trim at once and there is no
    instant in between for the part to object to. What is left is at most three
    windows, each of them covered by frames wherever frames are cheaper.
    """
    want_v, want_i, want_e = {}, {}, {}
    for kind, rail, value in reqs:
        if kind == 0:
            want_v[rail] = value
        elif kind == 1:
            want_i[rail] = value
        else:
            want_e[rail] = bool(value & 1)

    want_v = {r: v for r, v in want_v.items() if dev.vset[r] != v}
    want_i = {r: v for r, v in want_i.items() if dev.ilim[r] != v}
    want_e = {r: v for r, v in want_e.items() if dev.enabled[r] != v}

    moved = sorted(set(want_v) | set(want_i))
    pairs, singles_v, trail_i = {}, {}, {}
    for r in moved:
        fin_v = want_v.get(r, dev.vset[r])
        fin_i = want_i.get(r, dev.ilim[r])
        if fin_v <= fin_i:
            # Both halves in one word, whatever the rail is doing.
            pairs[r] = (fin_i << 8) | fin_v
            continue
        # The batch leaves this rail under its own limit, which no single word
        # can say. The voltage goes first and the limit follows it down; if the
        # limit standing over it will not have it, the pair register puts the
        # two level in one write instead of two.
        if fin_v != dev.vset[r]:
            if dev.ilim[r] >= fin_v:
                singles_v[r] = fin_v
            else:
                pairs[r] = (fin_v << 8) | fin_v
        trail_i[r] = fin_i

    # Only a rail whose limit is about to go under its voltage has to be down
    # for it; every other enable move can wait until the trims are finished.
    first_down = {r: 0 for r in trail_i if dev.enabled[r]}
    last_cfg = {r: (1 if on else 0) for r, on in want_e.items() if r not in first_down}

    if first_down:
        _hold(dev, False, state)
        _cover(dev, P.CFG, first_down, lambda j: True,
               [1 if x else 0 for x in dev.enabled], state)

    if pairs or singles_v or trail_i:
        _hold(dev, True, state)
        if pairs:
            _cover(dev, P.PAIR, pairs,
                   lambda j: dev.vset[j] <= dev.ilim[j],
                   [(dev.ilim[j] << 8) | dev.vset[j] for j in range(dev.n)], state)
        if singles_v:
            _cover(dev, P.VSET, singles_v,
                   lambda j: dev.vset[j] <= dev.ilim[j], list(dev.vset), state)
        if trail_i:
            # Last, because this is the pass that leaves a rail sitting under
            # its own voltage, and nothing padded may land after it.
            _cover(dev, P.ILIM, trail_i, lambda j: True, list(dev.ilim), state)

    if last_cfg:
        _hold(dev, False, state)
        _cover(dev, P.CFG, last_cfg, lambda j: True,
               [1 if x else 0 for x in dev.enabled], state)


def reference_cost(rails, start, session):
    """Drive the reference plan through a private part and count what it spent."""
    dev = P.Part(rails, *[list(x) for x in start])
    state = {"program": False, "settling": False}
    for reqs, want in session:
        apply_batch(dev, reqs, state)
        got = (list(dev.vset), list(dev.ilim), [bool(x) for x in dev.enabled])
        expect = (list(want[0]), list(want[1]), [bool(x) for x in want[2]])
        if got != expect:
            raise AssertionError("the reference plan does not reach the end state")
    return dev.transactions
