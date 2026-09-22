import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent / "tasks" / "entry-lift-restate" / "tests"))  # TESTS_ON_PATH
"""Differential test: the sealed model against the specification and the reference tree."""
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent
                      / "tasks" / "entry-lift-restate" / "tests" / "seal"))

import gen as families  # noqa: E402
import lab
import model
import naive

REF = lab.reference()


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 60
    size = int(argv[2]) if len(argv) > 2 else 45
    bad = 0
    for name, fn in families.SMALL:
        first = None
        for seed in range(rounds):
            rng = random.Random("%s-%d" % (name, seed))
            lines = fn(rng, size)
            text = "\n".join(lines) + "\n"
            want = naive.run(text)
            got = model.expect(lines)
            ref = REF.run(text)
            if got != want or ref != want:
                first = (lines, want, got, ref)
                break
        if first is None:
            print("%-8s %4d programs: spec, model and reference agree" % (name, rounds), flush=True)
        else:
            bad += 1
            lines, want, got, ref = first
            print("%-8s DISAGREE\n   %s" % (name, "\n   ".join(lines)), flush=True)
            print("   spec  %s\n   model %s\n   ref   %s" % (want, got, ref), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
