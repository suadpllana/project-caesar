"""Every alternative correct implementation must produce the reference's trail on the
enumerated set and on a generated sample. The real-verifier version is
`trial.py --variants` and `tools/docker_trial2.py <slug> --variants`."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402


def main():
    texts = [cases.CASES[n] for n in sorted(cases.CASES)] + [t for _, t in gen.batch("variants", 200)]
    want = [harness.trail(r) for r in harness.run_many(harness.REF, texts)]
    vd = os.path.join(HERE, "variants")
    ok = True
    for d in sorted(os.listdir(vd)):
        if not d.startswith("ok-"):
            continue
        got = [harness.trail(r) for r in harness.run_many(os.path.join(vd, d), texts)]
        bad = sum(1 for a, b in zip(got, want) if a != b)
        print("%-24s %s (%d of %d differ)" % (d, "ok" if not bad else "DIFFERS", bad, len(texts)))
        ok = ok and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
