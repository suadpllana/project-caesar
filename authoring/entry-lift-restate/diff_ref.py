import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent / "tasks" / "entry-lift-restate" / "tests"))  # TESTS_ON_PATH
"""Differential test: the assembled reference tree against the specification."""
import random
import sys

import gen as families  # noqa: E402
import lab
import naive

REF = lab.reference()


def check(lines):
    text = "\n".join(lines) + "\n"
    want = naive.run(text)
    got = REF.run(text)
    return None if got == want else (want, got)


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 60
    size = int(argv[2]) if len(argv) > 2 else 40
    bad = 0
    for name, fn in families.SMALL:
        first = None
        for seed in range(rounds):
            rng = random.Random("%s-%d" % (name, seed))
            lines = fn(rng, size)
            out = check(lines)
            if out is not None:
                first = lines
                break
        if first is None:
            print("%-8s %4d programs agree" % (name, rounds), flush=True)
        else:
            bad += 1
            want, got = check(first)
            print("%-8s DISAGREE\n   %s\n   want %s\n   got  %s"
                  % (name, "\n   ".join(first), want, got), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
