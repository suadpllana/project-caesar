"""Request generation for the graded set.

The verifier seeds this with a nonce made after the agent has finished, so the requests
graded are not the requests in the agent's tree. Every collection is sorted before it is
drawn from, and nothing here reads a set or a dict in iteration order, so the same seed
gives the same requests under any PYTHONHASHSEED.

The generator deliberately over-represents three situations relative to a real stream,
because they are where the release point is decided: an occurrence that completes below the
floor, a suffix that is a live partial for several steps, and a character split across a
piece boundary or across a special piece.
"""
import random

# Drawn from the piece table, so occurrences actually happen rather than being astronomically
# unlikely. Sorted, and used only through an index.
STOPS = sorted([
    b"abc",
    b"ab",
    b"abcd",
    b"bc",
    b"bcd",
    b"cab",
    b"xyz",
    b"llo",
    b"cd",
    b"ed",
    b"ing",
    b"the",
    b"z",
    b"\n",
    b"o w",
    b"\xc3\xa9",
    b"ld.",
    b"yz",
])

# Pieces that build the stop strings above, so a generated stream reaches them often.
BAIT = sorted([3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 19, 20, 23, 24, 25, 26, 27, 29, 30])

# Pieces that split characters across a boundary, including the two that straddle.
SPLIT = sorted([40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58])

FILLER = sorted([10, 17, 18, 21, 22, 28, 31, 32, 33, 34, 35, 36, 37, 38, 39, 59, 60, 61, 62, 63])

SPECIAL = sorted([0, 2])

# Byte strings no piece can produce, so a wide request runs to its cap.
RARE = sorted([b"", b"zz", b""])


def one(rng, wide=False):
    """One request spec: (floor, cap, stops, ids)."""
    if wide:
        # A long request only stays long when nothing terminates it, so the wide family
        # carries stop strings the piece table cannot produce and no end-of-stream piece.
        stops = sorted(RARE[:1 + rng.randrange(len(RARE))])
    else:
        ns = rng.choice([0, 1, 1, 1, 2, 2, 2, 3])
        stops = sorted({STOPS[rng.randrange(len(STOPS))] for _ in range(ns)}) if ns else []

    cap = rng.randrange(30000, 44000) if wide else rng.randrange(18, 40)
    # The floor is placed above where an occurrence typically completes, because that is
    # where the release point stops being a function of the current step alone.
    if wide:
        floor = rng.choice([0, 12, 40, cap // 2, cap])
    else:
        floor = rng.choice([0, 2, 6, 8, 10, 12, 14, 16, 18, 20, cap])
    if floor > cap:
        floor = cap

    n = cap + rng.randrange(0, 4)
    ids = []
    for _ in range(n):
        r = rng.randrange(100)
        if r < 55:
            ids.append(BAIT[rng.randrange(len(BAIT))])
        elif r < 63:
            ids.append(SPLIT[rng.randrange(len(SPLIT))])
        elif r < 93:
            ids.append(FILLER[rng.randrange(len(FILLER))])
        else:
            ids.append(SPECIAL[rng.randrange(len(SPECIAL))])

    # An end-of-stream piece lands in the last part of most requests, and sometimes below
    # the floor, where it is suppressed.
    if not wide and rng.randrange(100) < 70:
        lo = max(1, (2 * len(ids)) // 3)
        at = rng.randrange(lo, max(lo + 1, len(ids)))
        ids[at] = 1

    return (floor, cap, stops, ids)


def make(seed, count, wide=False, tag="g"):
    """`count` named request specs from `seed`."""
    rng = random.Random(seed)
    return [("%s%05d" % (tag, i), one(rng, wide)) for i in range(count)]


def write(spec, path):
    """Write a spec as a request file in the format the runner parses."""
    floor, cap, stops, ids = spec
    lines = ["fl %d" % floor, "cp %d" % cap]
    for x in stops:
        lines.append("sx %s" % x.hex())
    lines.append("id %s" % " ".join(str(i) for i in ids))
    with open(path, "w", encoding="ascii") as fh:
        fh.write("\n".join(lines) + "\n")
