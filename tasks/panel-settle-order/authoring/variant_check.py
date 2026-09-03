"""Every alternative correct implementation must agree with the model, event for event.

This is the mirror of the cheat suite and it is the gate the run audit actually applies: a
graded quantity that two correct implementations disagree on is a trap rather than a test.
A variant that fails here is either a real difference the brief never decided - in which
case the brief is the thing to fix, not the variant - or a bug in the variant.

    python3 authoring/variant_check.py [count]
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 200
    panels = [(k, cases.PANELS[k]) for k in sorted(cases.PANELS)] + gen.build("variants", n)
    want = {}
    for name, text in panels:
        got = oracle.check(text)
        if got is not None:
            want[name] = got
    live = [(k, t) for k, t in panels if k in want]
    bad = 0
    for d in sorted((HERE / "variants").iterdir()):
        if not d.is_dir():
            continue
        got = harness.drive(harness.stage(d), live)
        miss = []
        for name, _t in live:
            r = got[name]
            if r["err"] is not None:
                miss.append("%s raised %s" % (name, r["err"]))
            elif tuple(r["log"]) != want[name]["log"] or tuple(r["dump"]) != want[name]["dump"]:
                miss.append(name)
        if miss:
            bad += 1
            print("%-16s DISAGREES on %d of %d: %s" % (d.name, len(miss), len(live), miss[:4]))
        else:
            print("%-16s agrees on all %d panels" % (d.name, len(live)))
    print("%d variants checked, %d disagree" % (len(list((HERE / 'variants').iterdir())), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
