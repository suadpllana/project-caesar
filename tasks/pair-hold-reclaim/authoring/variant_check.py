"""Every alternative correct implementation must score 1.

This is the cheat suite's mirror image and it is the gate the run audit actually
applies. A ledger row two correct readings disagree on is a row that grades an
arrangement of the code rather than the behaviour the rules describe.

    python3 authoring/variant_check.py
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
import scen  # noqa: E402


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 150
    streams = scen.cases() + gen.build("variants", count)
    want = {n: oracle.play(t) for n, t in streams}
    bad = 0
    for d in [TASK / "solution"] + sorted((HERE / "variants").iterdir()):
        tree = harness.stage(TASK / "environment" / "app_src", d)
        got = harness.drive(tree, streams)
        wrong = [n for n, _ in streams
                 if got[n]["err"] or got[n]["log"] != want[n]["log"]
                 or got[n]["state"] != want[n]["state"]]
        bad += bool(wrong)
        print("%-12s %s" % (d.name, "1" if not wrong else "0  first miss: %s" % wrong[0]))
    print("%d of %d readings score 1" % (6 - bad, 6))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
