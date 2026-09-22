"""The generated half of the graded set, built inside the verifier from a nonce seed.

The seed is drawn after the agent's container is gone, so no submission can have seen these
scripts: fitting the four shipped samples is worth nothing here, and so is an answer key.

Each family is shaped at one decision rather than sampled uniformly, because an unshaped
population does not exercise the rules that decide the run. `cover` and `climb` put a
transaction under its own coarser lock; `esc` runs the threshold with and without a rival on the
table; `queue` and `fell` concentrate conversions, no-bypass and felling; `shield` builds the
configuration where a waiter on one entry protects a holder on another; `wake` frees two entries
with one commit so the order the heads are taken in decides the run; `cont` blocks intention
requests that are carrying row requests; `pass` names transactions that are waiting, felled or
committed.

`wide` and `deep` are the scale families. `wide` leaves thousands of entries with a waiting head
and then keeps changing the lock table, so an engine that goes over every waiting entry after
every change pays the product. `deep` gives one transaction fifteen thousand row locks on one
table and then asks about them, so an engine that counts its rows by walking what it holds, or
works out a standing the same way, pays it again; the commit at the end wakes everything at once.
"""
import random

TM = ("IS", "IX", "S", "SIX", "X")
RM = ("S", "X")
# Two-digit table numbers on purpose: a report sorted by the name of a resource rather than by
# its number puts 10 before 2, and a pool of 0, 1, 2 would never say so.
TABLES = (0, 2, 10, 11)

FAMILIES = (
    ("mix", False),
    ("cover", False),
    ("climb", False),
    ("esc", False),
    ("queue", False),
    ("fell", False),
    ("shield", False),
    ("wake", False),
    ("cont", False),
    ("pass", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def mix(rng):
    pool = rng.sample(TABLES, rng.randint(1, 3))
    rows = rng.randint(2, 5)
    ids = rng.sample(range(1, 60), rng.randint(2, 6))
    out = ["cfg %d" % rng.randint(2, 5)] + ["beg %d" % t for t in ids]
    for _ in range(rng.randint(8, 40)):
        t = rng.choice(ids)
        r = rng.random()
        if r < 0.08:
            out.append("com %d" % t)
        elif r < 0.40:
            out.append("req %d %d %s" % (t, rng.choice(pool), rng.choice(TM)))
        else:
            out.append("req %d %d.%d %s" % (t, rng.choice(pool), rng.randrange(rows),
                                            rng.choice(RM)))
    return out


def cover(rng):
    tbl = rng.choice(TABLES)
    ids = rng.sample(range(1, 60), 3)
    a, b, c = ids
    out = ["cfg %d" % rng.randint(5, 9)] + ["beg %d" % t for t in ids]
    out.append("req %d %d %s" % (a, tbl, rng.choice(("S", "SIX", "X"))))
    for _ in range(rng.randint(3, 7)):
        out.append("req %d %d.%d %s" % (a, tbl, rng.randrange(6), rng.choice(RM)))
    for _ in range(rng.randint(2, 5)):
        out.append("req %d %d.%d %s" % (b, tbl, rng.randrange(6), rng.choice(RM)))
    out.append("req %d %d %s" % (a, tbl, rng.choice(TM)))
    for _ in range(rng.randint(2, 6)):
        who = rng.choice((a, b, c))
        out.append("req %d %d.%d %s" % (who, tbl, rng.randrange(6), rng.choice(RM)))
    if rng.random() < 0.6:
        out.append("com %d" % a)
        for _ in range(rng.randint(1, 4)):
            out.append("req %d %d.%d %s" % (rng.choice((b, c)), tbl, rng.randrange(6),
                                            rng.choice(RM)))
    return out


def climb(rng):
    tbl = rng.choice(TABLES)
    ids = rng.sample(range(1, 60), 2)
    a, b = ids
    out = ["cfg %d" % rng.randint(6, 9)] + ["beg %d" % t for t in ids]
    for _ in range(rng.randint(2, 5)):
        out.append("req %d %d.%d %s" % (a, tbl, rng.randrange(5), rng.choice(RM)))
    for m in rng.sample(TM, rng.randint(2, 4)):
        out.append("req %d %d %s" % (a, tbl, m))
        if rng.random() < 0.5:
            out.append("req %d %d.%d %s" % (a, tbl, rng.randrange(5), rng.choice(RM)))
        if rng.random() < 0.4:
            out.append("req %d %d.%d %s" % (b, tbl, rng.randrange(5), rng.choice(RM)))
    return out


def esc(rng):
    """The threshold with and without a rival on the table, and rows taken after a raise."""
    ids = rng.sample(range(1, 60), 3)
    a, b, c = ids
    hot = rng.choice(TABLES)
    out = ["cfg %d" % rng.randint(2, 4)] + ["beg %d" % t for t in ids]
    if rng.random() < 0.5:
        out.append("req %d %d %s" % (c, hot, rng.choice(("S", "IX", "SIX"))))
    # Half the scripts take nothing but S rows first, so the raise goes to S rather than X and
    # leaves a table lock that covers some of what comes after it and not the rest.
    soft = rng.random() < 0.5
    for _ in range(rng.randint(3, 9)):
        who = a if rng.random() < 0.7 else b
        out.append("req %d %d.%d %s" % (who, hot, rng.randrange(8),
                                        "S" if soft else rng.choice(RM)))
    if rng.random() < 0.6:
        out.append("com %d" % c)
    # Rows asked for after a raise has already carried this table's rows away: some of them
    # are covered by the raised lock and some are not, which is where a tally that only ever
    # goes up and one that counts covered requests part company from the rules.
    for _ in range(rng.randint(3, 8)):
        who = rng.choice((a, b))
        out.append("req %d %d.%d %s" % (who, hot, rng.randrange(8), rng.choice(RM)))
    for _ in range(rng.randint(1, 4)):
        out.append("req %d %d.%d X" % (a, hot, rng.randrange(8)))
    return out


def queue(rng):
    ids = rng.sample(range(1, 60), rng.randint(4, 7))
    tbl = rng.choice(TABLES)
    out = ["cfg %d" % rng.randint(3, 9)] + ["beg %d" % t for t in ids]
    for t in ids:
        out.append("req %d %d %s" % (t, tbl, rng.choice(("IS", "IX", "S"))))
    for _ in range(rng.randint(6, 16)):
        t = rng.choice(ids)
        r = rng.random()
        if r < 0.15:
            out.append("com %d" % t)
        elif r < 0.55:
            out.append("req %d %d %s" % (t, tbl, rng.choice(TM)))
        else:
            out.append("req %d %d.%d %s" % (t, tbl, rng.randrange(4), rng.choice(RM)))
    return out


def fell(rng):
    """Holders taken in an order that is not begin order, so the felling order is visible."""
    ids = rng.sample(range(1, 60), rng.randint(3, 5))
    pool = rng.sample(TABLES, 2)
    out = ["cfg %d" % rng.randint(4, 9)] + ["beg %d" % t for t in ids]
    for t in rng.sample(ids, len(ids)):
        out.append("req %d %d IS" % (t, pool[0]))
    for t in list(reversed(ids))[:2]:
        out.append("req %d %d.%d X" % (t, rng.choice(pool), rng.randrange(3)))
    for _ in range(rng.randint(4, 14)):
        t = ids[rng.randrange(min(2, len(ids)))] if rng.random() < 0.6 else rng.choice(ids)
        if rng.random() < 0.3:
            out.append("req %d %d %s" % (t, rng.choice(pool), rng.choice(TM)))
        else:
            out.append("req %d %d.%d %s" % (t, rng.choice(pool), rng.randrange(3),
                                            rng.choice(RM)))
    return out


def shield(rng):
    """W queues on the table behind Y, which stops T felling H on one of H's rows."""
    w, t, u, h, y = rng.sample(range(1, 60), 5)
    tbl = rng.choice(TABLES)
    rows = rng.randint(2, 4)
    out = ["cfg %d" % rng.randint(5, 9)]
    for tid in (w, t, u, h, y):
        out.append("beg %d" % tid)
    out.append("req %d %d IS" % (t, tbl))
    for r in range(rows):
        out.append("req %d %d.%d X" % (h, tbl, r))
    out.append("req %d %d %s" % (y, tbl, rng.choice(("S", "X"))))
    out.append("req %d %d %s" % (w, tbl, rng.choice(("IS", "IX"))))
    if rng.random() < 0.5:
        # H is shielded by W, which waits on the table H holds, so T queues on H's rows.
        for r in range(rows):
            out.append("req %d %d.%d %s" % (t, tbl, r, rng.choice(RM)))
    else:
        # The other half of the same rule: nobody waits on H's rows, so when U asks for the
        # table itself the only waiter is W, on that same entry - which shields nobody.
        out.append("req %d %d %s" % (u, tbl, rng.choice(("S", "SIX", "X"))))
        for r in range(rows):
            out.append("req %d %d.%d %s" % (t, tbl, r, rng.choice(RM)))
    if rng.random() < 0.5:
        out.append("com %d" % h)
    return out


def wake(rng):
    """One commit frees several entries at once, with a head waiting on each of them."""
    a, b, c, d, e = rng.sample(range(1, 60), 5)
    tbl, other = rng.sample(TABLES, 2)
    row = rng.randrange(3)
    out = ["cfg %d" % rng.randint(5, 9)]
    for tid in (a, b, c, d, e):
        out.append("beg %d" % tid)
    # Two tables held by one transaction, taken in the order that disagrees with the begin
    # order of the two heads that end up waiting for them.
    out.append("req %d %d X" % (a, other))
    out.append("req %d %d S" % (e, other))
    out.append("req %d %d S" % (a, tbl))
    out.append("req %d %d.%d X" % (a, tbl, row))
    out.append("req %d %d.%d %s" % (c, tbl, row, rng.choice(RM)))
    out.append("req %d %d.%d X" % (b, tbl, row))
    out.append("req %d %d.%d %s" % (d, tbl, rng.randrange(3), rng.choice(RM)))
    for _ in range(rng.randint(0, 3)):
        out.append("req %d %d.%d %s" % (rng.choice((b, c)), tbl, rng.randrange(3),
                                        rng.choice(RM)))
    out.append("com %d" % a)
    for _ in range(rng.randint(0, 3)):
        out.append("req %d %d.%d %s" % (rng.choice((b, c, d)), tbl, rng.randrange(3),
                                        rng.choice(RM)))
    return out


def cont(rng):
    """Intention requests that queue while carrying a row request behind them."""
    ids = rng.sample(range(1, 60), rng.randint(3, 4))
    tbl = rng.choice(TABLES)
    out = ["cfg %d" % rng.randint(3, 9)] + ["beg %d" % t for t in ids]
    keep = ids[rng.randrange(len(ids))]
    out.append("req %d %d %s" % (keep, tbl, rng.choice(("S", "SIX", "X"))))
    for t in ids:
        if t == keep:
            continue
        out.append("req %d %d.%d %s" % (t, tbl, rng.randrange(3), rng.choice(RM)))
    out.append("com %d" % keep)
    for _ in range(rng.randint(1, 6)):
        t = rng.choice(ids)
        out.append("req %d %d.%d %s" % (t, tbl, rng.randrange(3), rng.choice(RM)))
    return out


def passed(rng):
    """Commands aimed at transactions that are waiting, felled or committed."""
    ids = rng.sample(range(1, 60), rng.randint(3, 5))
    tbl = rng.choice(TABLES)
    out = ["cfg %d" % rng.randint(3, 9)] + ["beg %d" % t for t in ids]
    out.append("req %d %d.0 X" % (ids[-1], tbl))
    out.append("req %d %d.0 X" % (ids[0], tbl))
    for _ in range(rng.randint(6, 18)):
        t = rng.choice(ids)
        r = rng.random()
        if r < 0.2:
            out.append("com %d" % t)
        elif r < 0.45:
            out.append("req %d %d %s" % (t, tbl, rng.choice(TM)))
        else:
            out.append("req %d %d.%d %s" % (t, tbl, rng.randrange(3), rng.choice(RM)))
    return out


def wide(rng):
    """Thousands of entries left with a waiting head, then thousands of further changes."""
    pairs = rng.randint(3200, 3600)
    spare = rng.randint(3200, 3600)
    out = ["cfg 100000"]
    for i in range(pairs):
        out.append("beg %d" % (1 + i))
    for i in range(pairs):
        out.append("beg %d" % (1 + pairs + i))
    for i in range(spare):
        out.append("beg %d" % (1 + 2 * pairs + i))
    for i in range(pairs):
        out.append("req %d %d.0 X" % (1 + i, i))
    for i in range(pairs):
        out.append("req %d %d.0 S" % (1 + pairs + i, i))
    for i in range(spare):
        who = 1 + 2 * pairs + i
        out.append("req %d %d.%d S" % (who, 90000 + (i % 7), i))
    return out


def deep(rng):
    """One transaction holds seventy thousand rows of one table; then it is asked about."""
    rows = rng.randint(68000, 72000)
    askers = rng.randint(5800, 6200)
    tbl = rng.choice(TABLES)
    w, h, y = 900001, 900002, 900003
    out = ["cfg 1000000", "beg %d" % w]
    for i in range(askers):
        out.append("beg %d" % (1 + i))
    out.append("beg %d" % h)
    out.append("beg %d" % y)
    for i in range(askers):
        out.append("req %d %d IS" % (1 + i, tbl))
    for r in range(rows):
        out.append("req %d %d.%d X" % (h, tbl, r))
    out.append("req %d %d S" % (y, tbl))
    out.append("req %d %d IS" % (w, tbl))
    for i in range(askers):
        out.append("req %d %d.%d S" % (1 + i, tbl, i % rows))
    out.append("com %d" % h)
    return out


BUILD = {
    "mix": mix,
    "cover": cover,
    "climb": climb,
    "esc": esc,
    "queue": queue,
    "fell": fell,
    "shield": shield,
    "wake": wake,
    "cont": cont,
    "pass": passed,
    "wide": wide,
    "deep": deep,
}


def build(fam, rng):
    return BUILD[fam](rng)


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        for i in range(BIG if big else per):
            rng = random.Random("%s:%s:%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), BUILD[fam](rng)))
    return out
