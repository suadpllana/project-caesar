"""Seeded script generation, in five families shaped at the mechanisms.

`plain`  ordinary sheets: reads stay out of a cell's own down-right quadrant.
`stack`  columns of blocks packed against each other, so refusal and fall-through decide
         most of the grid.
`loop`   reads deliberately aimed into a cell's own quadrant, which is what makes a value
         query re-enter itself.
`hole`   ranges carrying gaps and refusals, fed to the shape-preserving functions.
`edge`   blocks aimed at the last rows and columns, and counts at the ends of their range.

Every family is driven from a fixed seed, so the population is identical on every run and
the verdict never varies; only the corners a family concentrates on differ.
"""

import random

COLW = 10
ROWH = 20
LETTERS = "abcdefghij"


def label(spot):
    return "%s%d" % (LETTERS[spot[1]], spot[0])


def safe(spot, home):
    return spot[0] < home[0] or spot[1] < home[1]


def pool(rng, home, want_safe):
    out = []
    for r in range(1, ROWH + 1):
        for c in range(COLW):
            if safe((r, c), home) == want_safe and (r, c) != home:
                out.append((r, c))
    return out


def band(rng, home, want_safe):
    if want_safe and home[1] > 0:
        c0 = rng.randrange(0, home[1])
        c1 = rng.randrange(c0, home[1])
        r0 = rng.randrange(1, ROWH + 1)
        r1 = min(ROWH, r0 + rng.randrange(0, 4))
    elif want_safe:
        r1 = max(1, home[0] - 1)
        r0 = max(1, r1 - rng.randrange(0, 4))
        c0 = rng.randrange(0, COLW)
        c1 = min(COLW - 1, c0 + rng.randrange(0, 3))
    else:
        r0 = home[0]
        r1 = min(ROWH, r0 + rng.randrange(0, 5))
        c0 = home[1]
        c1 = min(COLW - 1, c0 + rng.randrange(0, 3))
    return "%s:%s" % (label((r0, c0)), label((r1, c1)))


def count(rng, home, kinds):
    if rng.random() < 0.4:
        return str(rng.randrange(1, 9))
    spots = pool(rng, home, True)
    if not spots:
        return str(rng.randrange(1, 9))
    if rng.random() < 0.25:
        return "AT(%s,1)" % band(rng, home, True)
    return label(rng.choice(spots))


def scalar(rng, home, depth, kinds):
    roll = rng.random()
    if depth <= 0 or roll < 0.25:
        return str(rng.randrange(1, 10))
    if roll < 0.55:
        spots = pool(rng, home, "loop" not in kinds or rng.random() < 0.6)
        if spots:
            return label(rng.choice(spots))
        return str(rng.randrange(1, 10))
    if roll < 0.72:
        op = rng.choice("+-*")
        side = rng.random()
        if side < 0.12:
            left = blocky(rng, home, kinds)
        elif side < 0.2:
            left = band(rng, home, True)
        else:
            left = scalar(rng, home, depth - 1, kinds)
        return "%s %s %s" % (left, op, scalar(rng, home, depth - 1, kinds))
    fn = rng.choice(("SUM", "CNT", "MAX", "LEN", "AT"))
    inner = band(rng, home, "loop" not in kinds or rng.random() < 0.6)
    if fn == "AT":
        return "AT(%s,%s)" % (inner, count(rng, home, kinds))
    return "%s(%s)" % (fn, inner)


def blocky(rng, home, kinds):
    fn = rng.choice(("RUN", "REP", "ROW", "KEEP", "GROW"))
    if fn == "RUN":
        return "RUN(%s)" % count(rng, home, kinds)
    if fn == "REP":
        return "REP(%s,%s)" % (scalar(rng, home, 1, kinds), count(rng, home, kinds))
    if fn == "ROW":
        return "ROW(%s,%s)" % (scalar(rng, home, 1, kinds), rng.randrange(1, 6))
    if fn == "KEEP":
        return "KEEP(%s,%s)" % (band(rng, home, True), count(rng, home, kinds))
    return "GROW(%s)" % band(rng, home, True)


def cell(rng, family):
    if family == "edge":
        r = rng.randrange(max(1, ROWH - 7), ROWH + 1)
        c = rng.randrange(max(0, COLW - 5), COLW)
        if rng.random() < 0.4:
            r = rng.randrange(1, ROWH + 1)
            c = rng.randrange(0, COLW)
        return (r, c)
    if family == "stack":
        return (rng.randrange(1, 12), rng.randrange(0, 6))
    return (rng.randrange(1, ROWH + 1), rng.randrange(0, COLW))


def formula(rng, home, family):
    kinds = {family}
    if family == "stack":
        return blocky(rng, home, kinds) if rng.random() < 0.75 else scalar(rng, home, 2, kinds)
    if family == "loop":
        return blocky(rng, home, kinds) if rng.random() < 0.45 else scalar(rng, home, 2, kinds)
    if family == "hole":
        if rng.random() < 0.55:
            fn = rng.choice(("KEEP", "GROW"))
            if fn == "KEEP":
                return "KEEP(%s,%s)" % (band(rng, home, True), count(rng, home, kinds))
            return "GROW(%s)" % band(rng, home, True)
        return scalar(rng, home, 2, kinds)
    if family == "edge":
        return blocky(rng, home, kinds) if rng.random() < 0.6 else scalar(rng, home, 2, kinds)
    return blocky(rng, home, kinds) if rng.random() < 0.4 else scalar(rng, home, 2, kinds)


def script(seed, family):
    rng = random.Random("%s|%d" % (family, seed))
    lines = []
    filled = []
    steps = rng.randrange(22, 40)
    for _ in range(steps):
        if filled and rng.random() < 0.14:
            spot = rng.choice(filled)
            filled.remove(spot)
            lines.append("clr %s" % label(spot))
            continue
        home = cell(rng, family)
        text = formula(rng, home, family)
        lines.append("put %s %s" % (label(home), text))
        if home not in filled:
            filled.append(home)
    return "\n".join(lines)


def batch(tag, count):
    out = []
    for family in ("plain", "stack", "loop", "hole", "edge"):
        for i in range(count):
            out.append(("%s-%s-%03d" % (tag, family, i), script(i, family)))
    return out
