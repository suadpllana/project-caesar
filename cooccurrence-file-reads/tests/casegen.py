"""Manifests and filters the reader is graded on. No expected answer is here.

Copied into the sandbox, so the account running the submitted module can read
all of it. That tells it which questions get asked and nothing about the
answers, which are worked out on the other side of a process boundary.

The manifests are built from real rows: a file is invented as a list of rows,
some of whose fields are left unset, and the recorded combinations are then
read off those rows. So every recorded combination genuinely happened, which is
what makes the summary honest and the trap fair -- a choice agreeing with every
recorded pair need not be a row that ever existed, and a field the summary says
was sometimes unset can be taken unset in company no row ever kept.

The small block is deliberately confined to four fields, because that is what
the model that tries every combination can afford; the wide and timed blocks
use all twelve.
"""

import hashlib
import random

COLUMNS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
CODES = 16

# The small block lives inside these four fields, pairs and filters alike, so
# that trying every combination stays affordable there.
SMALL_COLUMNS = ["b", "e", "f", "j"]

SMALL_MANIFEST_SEED = 226619
SMALL_FILES = 18
WIDE_MANIFEST_SEED = 913044
WIDE_FILES = 420

N_SMALL = 36
N_WIDE = 260
SMALL_SEED = 6620114
WIDE_SEED = 7714902

TIMED_FILES = 1400
TIMED_QUERIES = 24
TIMED_LEAVES = 12
TIMED_BUDGET = 30.0

PAIRS = [(x, y) for i, x in enumerate(COLUMNS) for y in COLUMNS[i + 1:]]

OPS = ["<", "<=", ">", ">=", "=", "!="]


def pair_name(x, y):
    return x + y


def _rows(rng, columns, nrows, palette_hi, null_rate, null_odds):
    """Invent rows over `columns`, leaving some fields unset."""
    palette = {}
    nullable = {}
    for c in columns:
        size = rng.randint(2, palette_hi)
        palette[c] = rng.sample(range(CODES), size)
        nullable[c] = rng.random() < null_rate
    rows = []
    for _ in range(nrows):
        row = {}
        for c in columns:
            if nullable[c] and rng.random() < null_odds:
                row[c] = None
            else:
                row[c] = rng.choice(palette[c])
        rows.append(row)
    return rows


def _summarise(rng, columns, rows, keep_p):
    """Read the co-occurrences off the rows, keeping some of the pairs."""
    recorded = {}
    for (x, y) in PAIRS:
        if x not in columns or y not in columns:
            continue
        if rng.random() >= keep_p:
            continue
        masks = [0] * CODES
        for row in rows:
            if row[x] is None or row[y] is None:
                continue
            masks[row[x]] |= 1 << row[y]
        recorded[pair_name(x, y)] = masks
    unset = [c for c in columns if any(row[c] is None for row in rows)]
    entry = {"pairs": recorded}
    if unset or rng.random() < 0.5:
        entry["unset"] = sorted(unset)
    return entry


def _entry(rng, columns, nrows, palette_hi, keep_p, null_rate, null_odds=0.3):
    rows = _rows(rng, columns, nrows, palette_hi, null_rate, null_odds)
    return _summarise(rng, columns, rows, keep_p)


def small_manifest():
    """Four fields and few rows per file, so every combination can be tried."""
    rng = random.Random(SMALL_MANIFEST_SEED)
    out = [{"pairs": {}}, {"pairs": {}, "unset": list(SMALL_COLUMNS)}]
    while len(out) < SMALL_FILES:
        out.append(_entry(rng, SMALL_COLUMNS,
                          rng.randint(1, 6),
                          rng.choice([3, 5, 9]),
                          rng.choice([0.5, 0.85, 1.0]),
                          rng.choice([0.0, 0.35, 0.7])))
    return out


def wide_manifest():
    rng = random.Random(WIDE_MANIFEST_SEED)
    out = []
    while len(out) < WIDE_FILES:
        out.append(_entry(rng, COLUMNS,
                          rng.randint(1, 30),
                          rng.choice([3, 6, 11, 16]),
                          rng.choice([0.15, 0.35, 0.6]),
                          rng.choice([0.0, 0.3, 0.6])))
    return out


def _leaf(rng, columns):
    return {"op": rng.choice(OPS),
            "col": rng.choice(columns),
            "value": rng.randint(-1, CODES)}


def _grow(rng, columns, depth=0):
    roll = rng.random()
    if depth >= 2 or roll < 0.34:
        return _leaf(rng, columns)
    if roll < 0.61:
        return {"op": "and",
                "args": [_grow(rng, columns, depth + 1)
                         for _ in range(rng.randint(2, 3))]}
    if roll < 0.88:
        return {"op": "or",
                "args": [_grow(rng, columns, depth + 1)
                         for _ in range(rng.randint(2, 3))]}
    return {"op": "not", "arg": _grow(rng, columns, depth + 1)}


def _sized(rng, columns, leaves):
    """A filter carrying about `leaves` conditions."""
    if leaves <= 1:
        return _leaf(rng, columns)
    parts, left = [], leaves
    count = 2 if leaves < 4 else rng.randint(2, 3)
    for i in range(count):
        take = max(1, left // (count - i))
        parts.append(_sized(rng, columns, take))
        left -= take
    node = {"op": rng.choice(["and", "or", "and"]), "args": parts}
    if rng.random() < 0.2:
        return {"op": "not", "arg": node}
    return node


# Corner cases, aimed where an implementation of the rules is most likely to
# part company with them: unset fields under a negation, a field pinned by a
# conjunction, a field the filter never mentions, values off both ends of the
# code range, and a conjunction no code satisfies.
FIXED = [
    {"op": "=", "col": "b", "value": 0},
    {"op": "<", "col": "e", "value": 3},
    {"op": ">=", "col": "f", "value": 13},
    {"op": "!=", "col": "j", "value": 4},
    {"op": ">=", "col": "b", "value": -1},
    {"op": "<", "col": "b", "value": 16},
    {"op": ">", "col": "e", "value": 16},
    {"op": "not", "arg": {"op": "<", "col": "f", "value": 8}},
    {"op": "not", "arg": {"op": ">=", "col": "j", "value": -1}},
    {"op": "not", "arg": {"op": "not", "arg": {"op": "=", "col": "b",
                                               "value": 5}}},
    {"op": "and", "args": [{"op": ">=", "col": "b", "value": 4},
                           {"op": "<=", "col": "b", "value": 6}]},
    {"op": "and", "args": [{"op": ">", "col": "e", "value": 9},
                           {"op": "<", "col": "e", "value": 2}]},
    {"op": "and", "args": [{"op": "=", "col": "b", "value": 1},
                           {"op": "=", "col": "e", "value": 2},
                           {"op": "=", "col": "f", "value": 3}]},
    {"op": "or", "args": [{"op": "=", "col": "b", "value": 15},
                          {"op": "=", "col": "e", "value": 15}]},
    {"op": "or", "args": [{"op": "and", "args": [
        {"op": "<", "col": "b", "value": 2},
        {"op": "<", "col": "f", "value": 2}]},
        {"op": "and", "args": [{"op": ">", "col": "e", "value": 12},
                               {"op": ">", "col": "j", "value": 12}]}]},
    {"op": "not", "arg": {"op": "and", "args": [
        {"op": ">=", "col": "b", "value": 0},
        {"op": "<=", "col": "j", "value": 15}]}},
    {"op": "not", "arg": {"op": "or", "args": [
        {"op": "<", "col": "e", "value": 4},
        {"op": ">=", "col": "e", "value": 12}]}},
    {"op": "and", "args": [{"op": "not", "arg": {"op": "=", "col": "f",
                                                 "value": 7}},
                           {"op": "or", "args": [
                               {"op": "=", "col": "b", "value": 2},
                               {"op": "=", "col": "j", "value": 9}]}]},
]


def small_filters():
    rng = random.Random(SMALL_SEED)
    return list(FIXED) + [_grow(rng, SMALL_COLUMNS) for _ in range(N_SMALL)]


def wide_filters():
    rng = random.Random(WIDE_SEED)
    return [_grow(rng, COLUMNS) for _ in range(N_WIDE)]


def timed_manifest(seed):
    rng = random.Random(seed ^ 0x4C11A7)
    out = []
    while len(out) < TIMED_FILES:
        out.append(_entry(rng, COLUMNS,
                          rng.randint(1, 45),
                          rng.choice([3, 6, 11, 16]),
                          rng.choice([0.15, 0.35, 0.6]),
                          rng.choice([0.0, 0.3, 0.6])))
    return out


def timed_filters(seed):
    rng = random.Random(seed ^ 0x39B0E5)
    return [_sized(rng, COLUMNS, TIMED_LEAVES) for _ in range(TIMED_QUERIES)]


def digest(seed, answers):
    h = hashlib.sha256()
    h.update(("seed:%d" % seed).encode())
    for i, row in enumerate(answers):
        h.update(("|%d:" % i).encode())
        h.update(",".join(str(x) for x in row).encode())
    return h.hexdigest()
