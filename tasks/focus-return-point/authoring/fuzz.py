"""The reference against the sealed model on generated scripts. Usage: fuzz.py [n] [seed]"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 800
    seed = argv[2] if len(argv) > 2 else "fuzz"
    items = gen.batch(seed, n)
    res = harness.run_many(harness.REF, [t for _, t in items], timeout=900)
    bad = 0
    events = 0
    for (nm, text), r in zip(items, res):
        t = harness.trail(r)
        events += len(t) if t[0] != "error" else 0
        if t != tuple(oracle.solve(text)):
            bad += 1
            if bad <= 3:
                print("DIFFERS on %s\n%s\nref   %s\nmodel %s" % (
                    nm, text, " ".join(t), " ".join(oracle.solve(text))))
    print("%d scripts, %d events, %d disagreements" % (n, events, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
