"""Differential fuzz: the reference tree against the sealed oracle.

Two independent implementations of the same specification, run over random programs from
tests/gen.py and compared event for event and token for token. build_gt.py refuses to
write a ground truth without a clean run of this, because the verifier grades the
randomized set against the oracle live: if the oracle and the reference ever disagree,
one of them is wrong and the task is unfair in whichever direction the disagreement goes.

    python3 authoring/fuzz.py 2000 [seed]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import gen
import harness
import oracle


def norm(r):
    return ([tuple(x) for x in r["tr"]],
            [(a, b, tuple(c)) for a, b, c in r["tk"]])


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 800
    seed = argv[2] if len(argv) > 2 else "fuzz"
    dst = harness.tree(os.path.join(ROOT, "solution"))
    import cases
    pool = [(nm, cases.PROGS[nm]) for nm in sorted(cases.PROGS)]
    pool += [(nm, gen.text(p)) for nm, p in gen.batch(seed, n)]
    bad = 0
    for name, text in pool:
        want = norm(oracle.solve(text))
        got = norm(harness.run(dst, text, "main"))
        if want != got:
            bad += 1
            if bad <= 3:
                print("MISMATCH %s" % name)
                show(text, want, got)
    print("%d programs, %d mismatches" % (len(pool), bad))
    return 1 if bad else 0


def show(text, want, got):
    print(text)
    a = [" ".join(str(y) for y in r) for r in want[0]]
    b = [" ".join(str(y) for y in r) for r in got[0]]
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "-"
        y = b[i] if i < len(b) else "-"
        print("  %-38s %s %s" % (x, "==" if x == y else "!=", y))
    if want[1] != got[1]:
        print("  toks want %s" % (want[1],))
        print("  toks got  %s" % (got[1],))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
