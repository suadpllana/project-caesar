#!/usr/bin/env python3
"""The fast implementation against the definitional model, on random pairs.

The enumerated block is every short shape crossed with every other, which is
the right check for the rule and the wrong one for the machinery: nothing in
it is long enough to reach the row engine's checkpoint rebuild, its mask
spill, or a staircase deep enough for the sliding minimums to move their
windows more than a step. Those paths are only reachable on pairs the model
can still grade, which is a band a few hundred lines wide, and this walks it.

`--tight` shrinks the row engine's two memory budgets so that the checkpoint
rebuild and the spilled-mask path run on every pair rather than on none. A
run without it exercises the code the graded pairs use; a run with it
exercises the code the graded pairs use once they are large enough not to fit,
which is every timed pair in the crowded family.

    python3 authoring/fuzz.py 400
    python3 authoring/fuzz.py 200 --tight
"""

import argparse
import pathlib
import random
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import oracle
import reference

ENGINES = ["frontier", "rows", "pairs", None]


def a_pair(rng):
    kind = rng.randrange(4)
    alpha = rng.choice([2, 2, 3, 3, 4, 6, 12])
    pool = ["ln%03d" % i for i in range(alpha)]
    if kind == 0:                      # two independent draws
        n = rng.randrange(0, 160)
        m = rng.randrange(0, 160)
        return ([rng.choice(pool) for _ in range(n)],
                [rng.choice(pool) for _ in range(m)])
    if kind == 1:                      # near-identical, a scatter of edits
        n = rng.randrange(1, 200)
        before = [rng.choice(pool) for _ in range(n)]
        after = list(before)
        for _ in range(rng.randrange(1, 12)):
            p = rng.randrange(len(after)) if after else 0
            choice = rng.randrange(3)
            if choice == 0 and after:
                del after[p:p + rng.randrange(1, 4)]
            elif choice == 1:
                after.insert(p, rng.choice(pool))
            elif after:
                after[p] = rng.choice(pool)
        return before, after
    if kind == 2:                      # blocks put back in a different order
        n = rng.randrange(2, 180)
        before = [rng.choice(pool) for _ in range(n)]
        size = max(1, n // rng.randrange(2, 8))
        pieces = [before[i:i + size] for i in range(0, n, size)]
        rng.shuffle(pieces)
        after = [line for piece in pieces for line in piece]
        return before, after
    # very skewed, which is where an off-by-one in a window shows up
    return ([rng.choice(pool) for _ in range(rng.randrange(0, 24))],
            [rng.choice(pool) for _ in range(rng.randrange(60, 200))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("count", nargs="?", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tight", action="store_true",
                    help="shrink the row engine's memory budgets so the "
                         "checkpoint rebuild and the spilled-mask path run")
    args = ap.parse_args()

    if args.tight:
        reference._BLOCK_BUDGET = 64
        reference._MASK_BUDGET = 64

    rng = random.Random(args.seed)
    bad = 0
    for index in range(args.count):
        before, after = a_pair(rng)
        want = [tuple(op) for op in oracle.script(before, after)]
        for engine in ENGINES:
            got = [tuple(op) for op in reference.changes(before, after, engine)]
            if got != want:
                bad += 1
                if bad <= 3:
                    print("MISMATCH engine=%s\n  before=%r\n  after=%r\n"
                          "  got  %r\n  want %r"
                          % (engine, before, after, got[:14], want[:14]))
        if oracle.rebuild(before, after, want) != after:
            bad += 1
            print("the model's own answer does not rebuild: %r %r"
                  % (before, after))
    print("%d pairs x %d engines%s: %d mismatches"
          % (args.count, len(ENGINES), " (tight budgets)" if args.tight else "",
             bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
