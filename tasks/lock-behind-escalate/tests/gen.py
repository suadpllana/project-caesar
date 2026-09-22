"""Scripts generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions rather than sampled from the input space: an
unshaped population rarely queues two requests on one row, never upgrades, never reaches the
escalation threshold and never closes a cycle, so every wrong reading scores the same as the
right one. Each family below concentrates one mechanism; the two scale families exist for
the execution limit and for generality rather than for a rule.

  plain    a few transactions over a few tables, light contention, K out of reach
  hot      many transactions on one or two rows: queues, readers behind writers
  skip     shared holders upgrading to exclusive with writers queued: skips and cycles
  late     a reader queued behind a blocked writer whose blocker later needs the reader
  cross    table locks mixed with row locks on the same table
  esc      small K, transactions taking many rows of one table while others hold rows
  drop     locks dropped and retaken, so counts move both ways
  dead     crossing lock orders over several rows, with unequal record counts
  wide     hundreds of transactions over many tables
  deep     a fan of readers queued behind a writer that waits at the head of a long chain
"""
import random

FAMILIES = (
    ("plain", False),
    ("hot", False),
    ("skip", False),
    ("late", False),
    ("cross", False),
    ("esc", False),
    ("drop", False),
    ("dead", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def _row(rng, table, rows):
    return "%s.%d" % (table, rng.randint(1, rows))


def _emit(k, txns, rng=None, shuffle=False):
    """Lines of a script: the cfg line, then each transaction's ops in turn."""
    lines = ["cfg %d" % k]
    order = list(range(len(txns)))
    if shuffle and rng is not None:
        rng.shuffle(order)
    for i in order:
        name = "T%d" % (i + 1)
        for op in txns[i]:
            lines.append("%s %s" % (name, op))
        lines.append("%s commit" % name)
    return lines


def build(fam, rng):
    if fam == "plain":
        tables = ["t%d" % i for i in range(1, rng.randint(2, 4))]
        txns = []
        for _ in range(rng.randint(3, 6)):
            ops = []
            for _ in range(rng.randint(2, 5)):
                t = rng.choice(tables)
                tgt = _row(rng, t, rng.randint(4, 8)) if rng.random() < 0.9 else t
                ops.append("lock %s %s" % (tgt, rng.choice("ssx")))
            txns.append(ops)
        return _emit(50, txns, rng, shuffle=rng.random() < 0.3)

    if fam == "hot":
        rows = rng.randint(1, 2)
        txns = []
        for _ in range(rng.randint(4, 8)):
            ops = []
            for _ in range(rng.randint(1, 3)):
                ops.append("lock %s %s" % (_row(rng, "t", rows), rng.choice("ssxx")))
            txns.append(ops)
        return _emit(50, txns, rng)

    if fam == "skip":
        txns = []
        for _ in range(rng.randint(3, 6)):
            r = _row(rng, "t", 2)
            kind = rng.random()
            if kind < 0.5:
                ops = ["lock %s s" % r, "lock %s %s" % (_row(rng, "t", 3), rng.choice("sx")),
                       "lock %s x" % r]
            elif kind < 0.8:
                ops = ["lock %s x" % r]
            else:
                ops = ["lock %s s" % r, "lock %s s" % _row(rng, "t", 3)]
            txns.append(ops)
        return _emit(50, txns, rng)

    if fam == "late":
        txns = [
            ["lock t.1 s", "lock t.%d %s" % (rng.randint(1, 3), rng.choice("sx"))],
            ["lock t.1 x"],
            ["lock t.2 %s" % rng.choice("sx"), "lock t.1 s"],
        ]
        for _ in range(rng.randint(0, 3)):
            txns.append(["lock t.%d %s" % (rng.randint(1, 3), rng.choice("ssx"))])
        for ops in txns[1:]:
            if rng.random() < 0.4:
                ops.append("lock t.%d %s" % (rng.randint(1, 3), rng.choice("sx")))
        return _emit(50, txns, rng)

    if fam == "cross":
        txns = []
        for _ in range(rng.randint(3, 6)):
            ops = []
            for _ in range(rng.randint(1, 3)):
                if rng.random() < 0.35:
                    ops.append("lock t %s" % rng.choice("sx"))
                else:
                    ops.append("lock %s %s" % (_row(rng, "t", 4), rng.choice("ssx")))
            txns.append(ops)
        return _emit(50, txns, rng)

    if fam == "esc":
        k = rng.randint(2, 4)
        txns = []
        if rng.random() < 0.5:
            r = _row(rng, "t", 8)
            txns.append(["lock %s s" % r] + ["lock w.%d s" % i for i in range(1, rng.randint(3, 6))])
            txns.append(["lock %s x" % r])
        for _ in range(rng.randint(2, 5)):
            ops = []
            n = rng.randint(1, k + 2)
            for _ in range(n):
                ops.append("lock %s %s" % (_row(rng, "t", 8), rng.choice("sssx")))
            if rng.random() < 0.3:
                ops.append("drop %s" % _row(rng, "t", 8))
            if rng.random() < 0.4:
                ops.append("lock %s %s" % (_row(rng, "t", 8), rng.choice("sx")))
            txns.append(ops)
        return _emit(k, txns, rng)

    if fam == "drop":
        k = rng.randint(2, 3)
        txns = []
        for _ in range(rng.randint(2, 4)):
            ops = []
            for _ in range(rng.randint(3, 7)):
                r = _row(rng, "t", 4)
                if rng.random() < 0.4:
                    ops.append("drop %s" % (r if rng.random() < 0.8 else "t"))
                else:
                    ops.append("lock %s %s" % (r if rng.random() < 0.85 else "t",
                                               rng.choice("ssx")))
            txns.append(ops)
        return _emit(k, txns, rng)

    if fam == "dead":
        rows = rng.randint(2, 4)
        txns = []
        for _ in range(rng.randint(2, 5)):
            order = list(range(1, rows + 1))
            rng.shuffle(order)
            ops = ["lock t.%d %s" % (r, rng.choice("sxx")) for r in order[:rng.randint(2, rows)]]
            txns.append(ops)
        return _emit(50, txns, rng)

    if fam == "wide":
        tables = ["t%d" % i for i in range(1, 21)]
        txns = []
        for _ in range(400):
            ops = []
            t = rng.choice(tables)
            for _ in range(rng.randint(2, 6)):
                if rng.random() < 0.15:
                    t = rng.choice(tables)
                if rng.random() < 0.04:
                    ops.append("lock %s %s" % (t, rng.choice("ssx")))
                else:
                    ops.append("lock %s %s" % (_row(rng, t, 30), rng.choice("sssx")))
                if rng.random() < 0.1:
                    ops.append("drop %s" % _row(rng, t, 30))
            txns.append(ops)
        return _emit(rng.choice([3, 4]), txns, rng)

    if fam == "deep":
        chain = rng.randint(100, 140)
        fan = rng.randint(100, 160)
        noise = rng.randint(150, 250)
        txns = [["lock t.1 s", "lock t.2 x"]]
        for i in range(2, chain + 1):
            ops = ["lock t.%d x" % i]
            if i < chain:
                ops.append("lock t.%d x" % (i + 1))
            else:
                ops += ["lock u.%d %s" % (rng.randint(1, 40), rng.choice("sx"))
                        for _ in range(rng.randint(12, 16))]
            txns.append(ops)
        txns.append(["lock t.1 x"])
        for _ in range(fan):
            txns.append(["lock t.1 s"])
        for _ in range(noise):
            ops = []
            for _ in range(rng.randint(8, 12)):
                ops.append("lock v%d.%d %s" % (rng.randint(1, 6), rng.randint(1, 25),
                                                rng.choice("sssx")))
            txns.append(ops)
        return _emit(rng.choice([4, 5]), txns, rng)

    raise AssertionError("unknown family %s" % fam)


def programs(seed, per):
    """Every graded script for this run, as (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), build(fam, rng)))
    return out
