"""Search the generated space for the smallest program that separates each wrong reading.

A hand-picked case says what its author already believed.  These are found: for every reading
in emit.py the search draws small programs from the shipped families, keeps the first that
makes the reading disagree with the reference, then shrinks it one operation at a time while
the disagreement survives.  The result is the case table, one case named for the reading it
pins, which is what makes a failure say which rule broke.
"""
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

_cases, gen, _model = lab.sealed()
REF = lab.tree(lab.SOL)

ALPHA = {"wide": gen.WIDE, "share": gen.SHARE, "dense": gen.DENSE}


def draw(rng):
    """One small program: a family, a size, a capacity, a floor."""
    alpha = rng.choice(list(ALPHA.values()))
    lo, hi = rng.choice([(2, 4), (3, 6), (5, 8), (8, 10)])
    n = rng.randint(6, 34)
    cap = rng.choice([32, 36, 40, 44, 52, 64, 80, 96])
    floor = rng.choice([10, 12, 14, 16, 20, 24, 30, 36])
    shape = rng.choice(["grow", "churn", "purge", "wave"])
    arg = {"grow": 0.0, "churn": 0.5, "purge": 0.9, "wave": 0.6}[shape]
    keys = gen.keys(rng, n, alpha, lo, hi)
    ops = gen.SHAPE[shape](rng, keys, arg)
    return cap, floor, ops


def body(cap, floor, ops):
    return "\n".join(["page %d %d" % (cap, floor)] + ["%s %s" % o for o in ops]) + "\n"


def splits(tree, cap, floor, ops):
    text = body(cap, floor, ops)
    return lab.run_text(tree, text) != lab.run_text(REF, text)


def shrink(tree, cap, floor, ops):
    ops = list(ops)
    changed = True
    while changed:
        changed = False
        i = len(ops) - 1
        while i >= 0:
            trial = ops[:i] + ops[i + 1:]
            if trial and splits(tree, cap, floor, trial):
                ops = trial
                changed = True
            i -= 1
    return ops


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    found = {}
    trees = {k: lab.tree(lab.spill(v)) for k, v in emit.READINGS.items()}
    pool = []
    rng = random.Random(20260922)
    for _ in range(rounds):
        pool.append(draw(rng))
    for key in sorted(emit.READINGS):
        tree = trees[key]
        best = None
        for cap, floor, ops in pool:
            if len(ops) > 40:
                continue
            if splits(tree, cap, floor, ops):
                small = shrink(tree, cap, floor, ops)
                if best is None or len(small) < len(best[2]):
                    best = (cap, floor, small)
                if len(small) <= 6:
                    break
        if best is None:
            print("%-14s NOT SEPARATED by any drawn program" % key)
        else:
            found[key] = best
            print("%-14s %2d ops  cap=%-3d floor=%-3d" % (key, len(best[2]), best[0], best[1]))
    out = HERE / "picked.json"
    out.write_text(json.dumps({k: [v[0], v[1], v[2]] for k, v in found.items()},
                              indent=1), encoding="utf-8", newline="\n")
    print("wrote %s (%d of %d)" % (out, len(found), len(emit.READINGS)))


if __name__ == "__main__":
    main()
