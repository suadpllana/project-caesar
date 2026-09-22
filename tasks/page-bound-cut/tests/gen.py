"""Program generator for the graded population.

The families are shaped around the mechanism rather than drawn uniformly.  Keys over the
full alphabet share almost nothing, so a page boundary lands where the keys diverge and the
string above it never moves; keys over a small alphabet at full length share four or five
characters, so boundaries are long and a delete of a page's least or greatest key moves
them.  A run that only grows
never reaches a join, a fold or an emptied page, so three of the four shapes delete, and the
fill floor decides whether an emptying page is joined away or left to empty.
"""

import random

WIDE = "abcdefghijklmnopqrstuvwxyz"
SHARE = "abcdef"
DENSE = "abc"


def keys(rng, n, alpha, lo, hi):
    return ["".join(rng.choice(alpha) for _ in range(rng.randint(lo, hi)))
            for _ in range(n)]


def grow(rng, ks, arg):
    return [("put", k) for k in ks]


def churn(rng, ks, arg):
    ops = []
    live = []
    for k in ks:
        ops.append(("put", k))
        live.append(k)
        if len(live) > 4 and rng.random() < arg:
            ops.append(("del", rng.choice(live)))
        if rng.random() < 0.05:
            ops.append(("del", "".join(rng.choice(WIDE) for _ in range(4))))
        if len(live) > 4 and rng.random() < 0.05:
            ops.append(("put", rng.choice(live)))
    return ops


def purge(rng, ks, arg):
    ops = [("put", k) for k in ks]
    rest = list(dict.fromkeys(ks))
    rng.shuffle(rest)
    for k in rest[:int(len(rest) * arg)]:
        ops.append(("del", k))
    return ops


def wave(rng, ks, arg):
    ops = [("put", k) for k in ks]
    band = sorted(set(ks))
    band = band[len(band) // 5:len(band) * 4 // 5]
    rng.shuffle(band)
    cut = int(len(band) * arg)
    for k in band[:cut]:
        ops.append(("del", k))
    for k in band[:cut]:
        ops.append(("put", k[:-1] + "a" if len(k) > 1 else k))
    return ops


SHAPE = {"grow": grow, "churn": churn, "purge": purge, "wave": wave}

FAMILIES = [
    ("wide-grow", WIDE, 4, 8, "grow", 0.0, 120, 96, 32),
    ("wide-churn", WIDE, 4, 8, "churn", 0.45, 120, 96, 32),
    ("wide-purge", WIDE, 4, 8, "purge", 0.90, 120, 96, 12),
    ("share-churn", SHARE, 8, 10, "churn", 0.45, 120, 96, 44),
    ("share-purge", SHARE, 8, 10, "purge", 0.90, 120, 96, 32),
    ("share-strip", SHARE, 8, 10, "purge", 0.90, 120, 96, 12),
    ("share-wave", SHARE, 8, 10, "wave", 0.60, 120, 96, 32),
    ("dense-churn", DENSE, 8, 10, "churn", 0.45, 120, 96, 44),
    ("dense-purge", DENSE, 8, 10, "purge", 0.90, 120, 96, 44),
    ("dense-wave", DENSE, 8, 10, "wave", 0.60, 120, 96, 32),
    ("tight-churn", SHARE, 8, 10, "churn", 0.45, 120, 72, 30),
    ("tight-purge", SHARE, 4, 8, "purge", 0.90, 120, 72, 30),
    ("roomy-churn", SHARE, 8, 10, "churn", 0.45, 120, 160, 56),
    ("thin-purge", SHARE, 8, 10, "purge", 0.95, 140, 40, 10),
    ("thin-wave", WIDE, 2, 5, "wave", 0.80, 140, 36, 10),
]

SCALE = [
    ("bulk-share", SHARE, 8, 10, "churn", 0.45, 60000, 96, 32),
    ("bulk-dense", DENSE, 8, 10, "purge", 0.55, 45000, 96, 44),
]


def body(cap, floor, ops):
    out = ["page %d %d" % (cap, floor)]
    for kind, key in ops:
        out.append("%s %s" % (kind, key))
    return "\n".join(out) + "\n"


def build(row, seed):
    name, alpha, lo, hi, shape, arg, n, cap, floor = row
    rng = random.Random("%s/%d" % (name, seed))
    return body(cap, floor, SHAPE[shape](rng, keys(rng, n, alpha, lo, hi), arg))


def population(seed, per=8):
    out = []
    for row in FAMILIES:
        for k in range(per):
            out.append(("%s-%d" % (row[0], k), build(row, seed * 977 + k)))
    for row in SCALE:
        out.append((row[0], build(row, seed)))
    return out
