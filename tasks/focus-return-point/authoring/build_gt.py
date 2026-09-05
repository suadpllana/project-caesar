"""Write tests/gt.json: the expected trail of every enumerated case.

It refuses to write unless three readings agree on every case - the reference driven
through the real runtime, the sealed model in tests/oracle.py, and the hand-derived
literals in authoring/handcheck.py - and unless the reference and the model also agree on
a large generated sample. A ground truth that only one implementation reached is that
implementation's bug written down as the answer.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import handcheck  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402

OUT = os.path.join(TASK, "tests", "gt.json")
SAMPLE = 360


def main():
    names = sorted(cases.CASES)
    refs = harness.run_many(harness.REF, [cases.CASES[n] for n in names])
    truth = {}
    for n, r in zip(names, refs):
        t = harness.trail(r)
        o = tuple(oracle.solve(cases.CASES[n]))
        h = tuple(handcheck.EXPECT[n].split())
        if not (t == o == h):
            print("REFUSED: %s disagrees (ref %s / model %s / hand %s)" % (n, t, o, h))
            return 1
        truth[n] = list(t)
    items = gen.batch("build-gt", SAMPLE)
    res = harness.run_many(harness.REF, [t for _, t in items])
    for (nm, text), r in zip(items, res):
        if harness.trail(r) != tuple(oracle.solve(text)):
            print("REFUSED: reference and model disagree on generated %s" % nm)
            return 1
    with open(OUT, "w", newline="\n") as fh:
        json.dump({"cases": truth}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("gt.json: %d cases, proved against the model on %d generated scripts and the "
          "hand-derived trails" % (len(truth), SAMPLE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
