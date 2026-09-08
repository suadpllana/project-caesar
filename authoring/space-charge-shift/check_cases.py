"""Reference, model and the shipped tree over every hand case: agreement, and separation."""
import sys

import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import model  # noqa: E402

REF = harness.TASK + "/solution"


def main():
    ref = harness.tree(policy=REF)
    ship = harness.tree()
    bad = 0
    same = []
    for nm in cases.ORDER:
        script = cases.ops(nm)
        want = model.run(script)
        got = harness.run(ref, script)
        try:
            broke = harness.run(ship, script)
        except Exception as exc:
            broke = ["raised: %r" % (exc,)]
        if got != want:
            bad += 1
            print("MISMATCH", nm)
            for a, b in zip(got, want):
                if a != b:
                    print("   ref %-28s model %s" % (a, b))
            if len(got) != len(want):
                print("   lengths", len(got), len(want))
        if broke == want:
            same.append(nm)
    print("\n%d/%d hand cases: reference == model" % (len(cases.ORDER) - bad, len(cases.ORDER)))
    print("shipped tree already correct on: %s" % (", ".join(same) or "none"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
