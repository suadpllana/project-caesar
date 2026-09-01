"""The reference against the sealed model on random journals.

Two implementations of one specification: the kernel maintains the tree incrementally,
touching the smallest region each operation needs, and the model throws that away and
recomputes every node's holdings from the top after every operation. Agreement over
thousands of journals is what says the incremental maintenance really is equivalent to the
invariant, and it is what build_gt.py refuses to write a ground truth without.

    python authoring/fuzz.py 2000
"""

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    tag = sys.argv[2] if len(sys.argv) > 2 else "fuzz"
    start = time.time()
    bad = []
    rows = 0
    for i in range(n):
        text = gen.text("%s/%d" % (tag, i))
        got = harness.ref(text)
        want = oracle.rows(text)
        rows += len(got)
        if got != want:
            bad.append(i)
            if len(bad) > 4:
                break
    print("%d journals, %d events, %d disagreements, %.0fs"
          % (n, rows, len(bad), time.time() - start))
    if bad:
        print("first: seed %s/%d" % (tag, bad[0]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
