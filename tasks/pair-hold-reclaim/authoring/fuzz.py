"""Run the reference against the sealed model on random streams.

A budget, a ledger or an ordering taken from one implementation is a claim that no other
correct reading needs anything else. This is the check that makes the claim testable:
the reference and tests/oracle.py share no code, and a disagreement on any row of any
stream means one of them is wrong before any of it is graded.

    python3 authoring/fuzz.py [count]
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
    count = int(argv[1]) if len(argv) > 1 else 400
    tag = argv[2] if len(argv) > 2 else "fuzz"
    tree = harness.stage(TASK / "environment" / "app_src", TASK / "solution")
    streams = gen.build(tag, count)
    got = harness.drive(tree, streams)
    bad = 0
    rows = 0
    for name, text in streams:
        want = oracle.play(text)
        mine = got[name]
        rows += len(want["log"])
        if mine["err"]:
            bad += 1
            print("RAISED %s %s" % (name, mine["err"]))
        elif mine["log"] != want["log"] or mine["state"] != want["state"]:
            bad += 1
            print("DIFFER %s" % name)
            for a, b in zip(mine["log"] + [""] * 9, want["log"] + [""] * 9):
                if a != b:
                    print("   ref %-28s model %s" % (a, b))
                    break
            if mine["state"] != want["state"]:
                print("   state ref  %s" % mine["state"])
                print("   state model %s" % want["state"])
    print("%d streams, %d ledger rows, %d disagreements" % (count, rows, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
