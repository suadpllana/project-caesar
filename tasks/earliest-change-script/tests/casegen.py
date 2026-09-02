"""The graded case distribution. The harness copy and the grading copy are the
same file, so the two never drift apart.

Five blocks, each aimed somewhere different:

  FIXED       corners written out by hand
  random      pairs over two to six distinct lines, where alignments collide
  structured  every short shape crossed with every other short shape, because
              sampling almost never produces the pair that matters
  medium      several hundred sequences of a few hundred lines, sharing one
              budget, so a table cannot be used on everything small
  timed       eighteen long pairs, each with its own wall clock, in three
              families: six that run to a million lines and differ in a few
              hundred places, six of forty to sixty thousand lines built from
              a handful of distinct lines that differ in a few thousand, and
              six of a quarter to a third of a million lines that are nearly
              all distinct and share no order at all. The first two answer to
              the same technique at two very different depths; the third is
              out of reach of it by orders of magnitude and answers to
              something else entirely.
"""

import random

FIXED = [
    ([], []),
    ([], ["a"]),
    (["a"], []),
    (["a"], ["a"]),
    (["a"], ["b"]),
    (["a", "b"], ["b", "a"]),
    (["m", "z"], ["z", "m"]),
    (["a", "a"], ["a", "b"]),
    (["a", "b", "c"], ["c", "a", "b"]),
    (["a", "b", "c"], ["b", "c", "a"]),
    (["a", "a", "b"], ["a", "b", "a"]),
    (["a", "b", "a"], ["a", "a", "b"]),
    (["a", "a", "a"], ["a", "a"]),
    (["a", "a"], ["a", "a", "a"]),
    (["a", "a", "a"], ["a", "a", "a"]),
    (["a", "b", "a", "b"], ["b", "a", "b", "a"]),
    (["a", "b", "a", "b"], ["a", "b"]),
    (["a", "b"], ["a", "b", "a", "b"]),
    (["x", "a", "b", "y"], ["a", "b"]),
    (["a", "b"], ["x", "a", "b", "y"]),
    (["a", "b", "c", "d"], ["d", "c", "b", "a"]),
    (["a", "b", "c", "a", "b", "c"], ["c", "a", "b", "c", "a", "b"]),
    (["a"] * 6, ["a"] * 3),
    (["a"] * 3, ["a"] * 6),
    (["a", "b"] * 4, ["b", "a"] * 4),
    (["q", "a", "a", "q"], ["a", "q", "q", "a"]),
    (["one", "two", "three"], ["one", "three", "two"]),
    (["one", "two", "three"], ["two", "three", "one"]),
    (["import os", "", "def f():", "    pass"],
     ["import os", "import sys", "", "def f():", "    pass"]),
    (["{", "  a", "}", "{", "  b", "}"], ["{", "  b", "}", "{", "  a", "}"]),
    (["}", "", "}", "", "}"], ["", "}", "", "}", ""]),
    (["a", "x", "b"], ["a", "y", "b"]),
    (["a", "x", "b"], ["a", "b"]),
    (["a", "b"], ["a", "x", "b"]),
    (["head", "a", "b", "tail"], ["head", "b", "a", "tail"]),
    (["a", "b", "c"], ["a", "b", "c"]),
    (["a", "b", "c"], ["x", "y", "z"]),
    (["a", "a", "b", "b"], ["b", "b", "a", "a"]),
    (["a", "b", "b", "a"], ["b", "a", "a", "b"]),
    (["z"] * 4 + ["a"], ["a"] + ["z"] * 4),
    (["a"] + ["z"] * 4, ["z"] * 4 + ["a"]),
    (["a", "b", "c", "b", "a"], ["b", "a", "c", "a", "b"]),
    (["p", "p", "q", "p", "p"], ["p", "q", "p", "p", "p"]),
    (["1", "2", "3", "4", "5"], ["1", "3", "5"]),
    (["1", "3", "5"], ["1", "2", "3", "4", "5"]),
    (["same"] * 5, ["same"] * 5),
    (["a", "", "b", "", "c"], ["a", "", "c", "", "b"]),
    # A shared head long enough to look safe to skip, and a tail that makes
    # skipping it the wrong answer.
    (["k"] * 12 + ["a", "k"], ["k"] * 12 + ["k", "a"]),
    (["p", "q"] * 6 + ["p"], ["q", "p"] * 6 + ["q"]),
    (["a"] * 20 + ["b"], ["b"] + ["a"] * 20),
    (["x", "y", "x", "y", "x"], ["y", "x", "y", "x", "y"]),
    (["r"] * 3 + ["s"] * 3 + ["r"] * 3, ["s"] * 3 + ["r"] * 3 + ["s"] * 3),
    (["a", "b", "a", "c", "a", "b", "a"], ["b", "a", "c", "a", "b", "a", "b"]),
    (["t"] * 8, ["t"] * 8 + ["u"] + ["t"] * 8),
    (["n"] * 5 + ["m"] * 5, ["m"] * 5 + ["n"] * 5),
    # The same moves can be made in one place or in two. The reading order
    # alone would take the two; the hunk count takes the one.
    (["c", "c", "a", "b"], ["c", "b", "a", "b"]),
    (["b", "a", "b", "a"], ["b", "a", "a", "a"]),
    (["b", "b", "b", "b"], ["b", "b", "a", "c"]),
    (["a", "a", "a", "c"], ["a", "b", "c", "a", "b", "c"]),
    (["c", "a", "b", "a"], ["a", "b", "c", "b"]),
    (["b", "c", "a", "c"], ["b", "b", "b", "b"]),
]

_EXTRA_SHAPES = [
    "aabba", "ababa", "abbab", "baaba", "aaabb", "abbaa", "babab", "aabab",
    "abcab", "cabab", "abcabc", "cabcab", "acbca", "bacab", "abcba", "cbabc",
    "aabbcc", "abcbca", "ccaba",
]


def shapes():
    out = [""]
    for length in (1, 2, 3, 4, 5):
        for bits in range(1 << length):
            out.append("".join("ab"[(bits >> i) & 1] for i in range(length)))
    for length in (1, 2, 3, 4):
        for code in range(3 ** length):
            value = code
            letters = []
            for _ in range(length):
                letters.append("abc"[value % 3])
                value //= 3
            out.append("".join(letters))
    out.extend(_EXTRA_SHAPES)
    return out


def structured_cases():
    """Every shape against every shape. Enumerated, not sampled: a random
    draw of short sequences almost never lands on the pairs where two
    alignments of the same length disagree about which line survives."""
    sh = shapes()
    return [([c for c in u], [c for c in v]) for u in sh for v in sh]


def random_cases(count, seed):
    rng = random.Random(seed * 7919 + 11)
    out = []
    for _ in range(count):
        alpha = rng.choice([2, 2, 3, 3, 4, 5, 6])
        pool = ["L%d" % i for i in range(alpha)]
        na = rng.randrange(0, 41)
        nb = rng.randrange(0, 41)
        out.append(([rng.choice(pool) for _ in range(na)],
                    [rng.choice(pool) for _ in range(nb)]))
    return out


def _ambiguous(rng, n, pool_size, edits, moves, move_len):
    """A pair that differs in a few places: runs picked up and put down
    elsewhere, then a scatter of small edits."""
    pool = ["ln%04d" % i for i in range(pool_size)]
    before = [rng.choice(pool) for _ in range(n)]
    after = list(before)
    for _ in range(moves):
        span = rng.randrange(2, move_len)
        i = rng.randrange(max(1, len(after) - span))
        seg = after[i:i + span]
        del after[i:i + span]
        j = rng.randrange(len(after) + 1)
        after[j:j] = seg
    for _ in range(edits):
        p = rng.randrange(len(after))
        kind = rng.randrange(3)
        if kind == 0:
            del after[p:p + rng.randrange(1, 3)]
        elif kind == 1:
            after.insert(p, rng.choice(pool))
        else:
            after[p] = rng.choice(pool)
    return before, after


def _crossed(rng, n, m, pool_size):
    """Two sequences drawn over the same vocabulary and nothing else in
    common. Over a handful of lines every line matches a large fraction of the
    other side and the number of moves runs to a third of the file. Over a
    pool as large as the file the moves run higher still and hardly any two
    positions match at all."""
    pool = ["ln%04d" % i for i in range(pool_size)]
    return ([rng.choice(pool) for _ in range(n)],
            [rng.choice(pool) for _ in range(m)])


def _reordered(rng, n, pool_size, blocks):
    """The same material in a different order: cut into blocks and permuted,
    so the two hold the same lines and agree about almost none of them. With
    a pool the size of the file the lines are nearly all distinct, which
    changes what the pair costs without changing what it looks like."""
    pool = ["ln%04d" % i for i in range(pool_size)]
    before = [rng.choice(pool) for _ in range(n)]
    size = max(1, n // blocks)
    pieces = [before[i:i + size] for i in range(0, n, size)]
    rng.shuffle(pieces)
    after = []
    for piece in pieces:
        after.extend(piece)
    return before, after


MEDIUM_COUNT = 400
MEDIUM_BUDGET = 40.0
TIMED_BUDGET = 60.0


def medium_cases(seed):
    """Three quarters of them differ in a few places; the rest share nothing
    but their vocabulary, which is a different cost entirely."""
    rng = random.Random(seed * 104729 + 5)
    out = []
    for index in range(MEDIUM_COUNT):
        if index % 4 == 3:
            out.append(_crossed(rng, rng.randrange(300, 700),
                                rng.randrange(300, 700), rng.randrange(2, 8)))
        else:
            n = rng.randrange(300, 1500)
            out.append(_ambiguous(rng, n, rng.randrange(8, 60),
                                  rng.randrange(2, 12), rng.randrange(1, 5),
                                  rng.randrange(3, 12)))
    return out


# (family, generator, parameters). The parameters rather than the generator
# decide which family a pair belongs to: the same edited draw over a pool of
# forty lines and over a pool of three is a different depth of the same cost,
# and the same crossed draw over a pool of three hundred thousand costs nothing
# like either. "long" pairs differ in a few hundred places over hundreds of
# thousands of lines. "crowded" pairs are forty to sixty thousand lines over
# two to six distinct ones, differing in a few thousand places, so the number
# of moves is ten times what the long pairs need and every line matches a
# large fraction of the other side. "sparse" pairs are four to six times
# longer than that with hardly anything matching anything, and share no order
# at all.
TIMED_SHAPES = [
    ("long", "ambiguous", (400000, 40, 80, 10, 15)),
    ("long", "ambiguous", (550000, 6, 60, 8, 15)),
    ("long", "ambiguous", (700000, 60, 120, 12, 20)),
    ("long", "ambiguous", (850000, 400, 140, 14, 30)),
    ("long", "ambiguous", (1000000, 200, 100, 12, 18)),
    ("long", "ambiguous", (1000000, 25, 90, 10, 22)),
    ("crowded", "ambiguous", (40000, 3, 800, 20, 40)),
    ("crowded", "ambiguous", (45000, 4, 1200, 25, 50)),
    ("crowded", "ambiguous", (55000, 3, 2500, 20, 30)),
    ("crowded", "ambiguous", (50000, 6, 2000, 30, 40)),
    ("crowded", "ambiguous", (48000, 2, 700, 30, 50)),
    ("crowded", "ambiguous", (42000, 5, 1600, 15, 25)),
    ("sparse", "crossed", (300000, 300000, 90000)),
    ("sparse", "crossed", (250000, 250000, 70000)),
    ("sparse", "crossed", (330000, 300000, 110000)),
    ("sparse", "reordered", (280000, 90000, 400)),
    ("sparse", "reordered", (300000, 120000, 60)),
    ("sparse", "reordered", (260000, 65000, 900)),
]


def timed_case(index, seed):
    family, kind, args = TIMED_SHAPES[index]
    rng = random.Random(seed * 15485863 + index * 97 + 3)
    if kind == "ambiguous":
        n, pool, edits, moves, move_len = args
        return _ambiguous(rng, n, pool, edits, moves, move_len)
    if kind == "crossed":
        n, m, pool = args
        return _crossed(rng, n, m, pool)
    n, pool, blocks = args
    return _reordered(rng, n, pool, blocks)
