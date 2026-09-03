"""The reference against the sealed model on generated panels.

A ground truth nobody has checked against a second implementation is one author's bug
written down twice. build_gt.py refuses to write one without a clean run of this.

    python3 authoring/fuzz.py [count] [seed]
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 400
    seed = argv[2] if len(argv) > 2 else "fuzz"
    panels = gen.build(seed, n)
    tree = harness.stage(TASK / "solution")
    got = harness.drive(tree, panels)
    bad = 0
    skipped = 0
    rows = 0
    for name, text in panels:
        try:
            want = oracle.solve(text)
        except oracle.Bust:
            skipped += 1
            continue
        mine = got[name]
        rows += len(want["log"])
        if mine["err"] is not None:
            print("%s: reference raised %s" % (name, mine["err"]))
            bad += 1
            continue
        if tuple(mine["log"]) != want["log"] or tuple(mine["dump"]) != want["dump"]:
            bad += 1
            if bad <= 3:
                print("%s: reference and model disagree" % name)
                for i, (a, b) in enumerate(zip(list(mine["log"]) + [None] * 99,
                                               list(want["log"]) + [None] * 99)):
                    if a != b:
                        print("   row %d: reference %r model %r" % (i, a, b))
                        break
                if tuple(mine["dump"]) != want["dump"]:
                    print("   dump %r vs %r" % (mine["dump"], want["dump"]))
    print("%d panels, %d model rows, %d skipped as not well formed, %d disagreements"
          % (len(panels), rows, skipped, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
