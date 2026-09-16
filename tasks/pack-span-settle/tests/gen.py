"""The generated shards, drawn from a seed the submission never saw.

Eight small families and two scale families. The small families are shaped around the
mechanism rather than drawn flat: an unshaped population lays every record into the room it
happens to find and almost never reaches the corners where the cut rule, the floor and the
settlement order separate. `edge` works at widths small enough that a window is left with one
or two slots constantly; `long` lays records that outlive several steps, so a step's line waits
on a record laid long before it; `nearfloor` sets the floor where a step sits within a position
or two of being dropped; `tiny` fills a window with two and three token records so that most of
its positions are boundaries.

The two scale families carry the execution limit. `wide` and `deep` each declare about four
billion tokens, which is out of reach of anything that keeps a value per position and costs a
per-piece engine a fraction of a second.
"""
import random

FAMILIES = (
    ("plain", False),
    ("carry", False),
    ("long", False),
    ("tiny", False),
    ("edge", False),
    ("shift", False),
    ("nearfloor", False),
    ("mixed", False),
    ("wide", True),
    ("deep", True),
)

BIG = {"wide": 3, "deep": 3}


def _head(rnd, width, span, floor):
    return ["width %d" % width, "span %d" % span, "floor %d" % floor]


def _plain(rnd):
    w = rnd.choice([16, 24, 32, 48])
    out = _head(rnd, w, rnd.randint(1, 3), rnd.randint(1, w))
    for i in range(rnd.randint(4, 14)):
        out.append("rec p%d %d %d" % (i, rnd.randint(2, w - 2), rnd.randint(1, 12)))
    return out


def _carry(rnd):
    w = rnd.choice([10, 14, 20, 28])
    out = _head(rnd, w, rnd.randint(1, 3), rnd.randint(1, 2 * w))
    for i in range(rnd.randint(3, 10)):
        out.append("rec c%d %d %d" % (i, rnd.randint(w - 2, 3 * w + 2), rnd.randint(1, 12)))
    return out


def _long(rnd):
    w = rnd.choice([6, 8, 11])
    span = rnd.randint(1, 3)
    out = _head(rnd, w, span, rnd.randint(1, 3 * w))
    for i in range(rnd.randint(2, 6)):
        if rnd.random() < 0.7:
            out.append("rec l%d %d %d" % (i, rnd.randint(4 * w * span, 12 * w * span),
                                          rnd.randint(1, 12)))
        else:
            out.append("rec l%d %d %d" % (i, rnd.randint(2, 2 * w), rnd.randint(1, 12)))
    return out


def _tiny(rnd):
    w = rnd.choice([12, 18, 26])
    out = _head(rnd, w, rnd.randint(1, 3), rnd.randint(1, w))
    for i in range(rnd.randint(8, 26)):
        out.append("rec t%d %d %d" % (i, rnd.choice([1, 2, 2, 3, 3, 4, 5]), rnd.randint(1, 12)))
    return out


def _edge(rnd):
    w = rnd.choice([5, 6, 7, 8, 9, 11, 13])
    out = _head(rnd, w, rnd.randint(1, 3), rnd.randint(1, 2 * w))
    for i in range(rnd.randint(4, 16)):
        n = rnd.choice([1, 2, 3, w - 2, w - 1, w, w + 1, w + 2,
                        2 * w - 1, 2 * w, 2 * w + 1, 3 * w + 1])
        out.append("rec e%d %d %d" % (i, max(n, 1), rnd.randint(1, 12)))
    return out


def _shift(rnd):
    w = rnd.choice([8, 12, 16])
    out = _head(rnd, w, rnd.randint(1, 3), rnd.randint(1, w))
    for i in range(rnd.randint(5, 16)):
        c = rnd.random()
        if c < 0.14:
            out.append("width %d" % rnd.choice([5, 7, 9, 12, 17, 24]))
        elif c < 0.24:
            out.append("span %d" % rnd.randint(1, 4))
        elif c < 0.34:
            out.append("floor %d" % rnd.randint(1, 4 * w))
        else:
            out.append("rec s%d %d %d" % (i, rnd.randint(1, 4 * w), rnd.randint(1, 12)))
    return out


def _nearfloor(rnd):
    w = rnd.choice([6, 9, 12])
    span = rnd.randint(1, 3)
    # A step of `span` full windows carries a little under span*(w-1) positions, so a floor
    # set just inside that band leaves most steps within a position or two of dropping.
    floor = max(1, span * (w - 1) - rnd.randint(0, 4))
    out = _head(rnd, w, span, floor)
    for i in range(rnd.randint(4, 14)):
        out.append("rec n%d %d %d" % (i, rnd.randint(2, 3 * w), rnd.randint(1, 12)))
    return out


def _mixed(rnd):
    w = rnd.choice([6, 8, 10, 14, 20])
    span = rnd.randint(1, 4)
    out = _head(rnd, w, span, max(1, rnd.randint(1, span * w)))
    for i in range(rnd.randint(6, 20)):
        c = rnd.random()
        if c < 0.08:
            out.append("width %d" % rnd.choice([5, 6, 8, 11, 15, 22]))
        elif c < 0.14:
            out.append("span %d" % rnd.randint(1, 4))
        elif c < 0.20:
            out.append("floor %d" % rnd.randint(1, 5 * w))
        elif c < 0.30:
            out.append("rec m%d %d %d" % (i, rnd.randint(6 * w, 20 * w), rnd.randint(1, 12)))
        else:
            n = rnd.choice([1, 2, 3, w - 1, w, w + 1, 2 * w + 1, rnd.randint(2, 4 * w)])
            out.append("rec m%d %d %d" % (i, max(n, 1), rnd.randint(1, 12)))
    return out


def _wide(rnd):
    w = 65536
    out = _head(rnd, w, 8, rnd.choice([200000, 300000, 400000]))
    for i in range(45000):
        n = rnd.choice([rnd.randrange(2, 400), rnd.randrange(60000, 70000),
                        rnd.randrange(100000, 300000), w + 1, 2 * w + 1])
        out.append("rec w%d %d %d" % (i, n, rnd.randint(1, 40)))
    out.append("seal")
    return out


def _deep(rnd):
    w = 262144
    out = _head(rnd, w, 8, rnd.choice([900000, 1400000, 1800000]))
    for i in range(2500):
        out.append("rec d%d %d %d" % (i, rnd.randrange(1500000, 1700000), rnd.randint(1, 40)))
    out.append("seal")
    return out


MAKERS = {
    "plain": _plain, "carry": _carry, "long": _long, "tiny": _tiny, "edge": _edge,
    "shift": _shift, "nearfloor": _nearfloor, "mixed": _mixed,
    "wide": _wide, "deep": _deep,
}


def one(fam, seed):
    """One shard of a family, for a named seed."""
    lines = MAKERS[fam](random.Random(seed))
    if lines[-1] != "seal":
        lines.append("seal")
    return lines


def programs(seed, per):
    """Every generated shard for this seed, as (family, name, op lines)."""
    out = []
    for fam, big in FAMILIES:
        count = BIG[fam] if big else per
        for i in range(count):
            lines = one(fam, "%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%04d" % (fam, i), lines))
    return out
