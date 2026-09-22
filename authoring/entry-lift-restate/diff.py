import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent / "tasks" / "entry-lift-restate" / "tests"))  # TESTS_ON_PATH
"""Differential test: the fast resolver against the specification, family by family.

    python diff.py [rounds] [size]

Prints one line per family with the number of programs checked and the first program where
the two disagree, shrunk by dropping lines that keep the disagreement alive.
"""

import random
import sys

import gen as families  # noqa: E402
import fast
import naive


def check(lines):
    text = "\n".join(lines) + "\n"
    try:
        want = naive.run(text)
    except naive.Bad as exc:
        return "unreadable: %s" % exc
    got = fast.run(text)
    return None if got == want else (want, got)


def shrink(lines):
    """Drop lines while the disagreement survives; keeps the counterexample readable."""
    cut = True
    while cut:
        cut = False
        for i in range(len(lines)):
            trial = lines[:i] + lines[i + 1:]
            if check(trial) not in (None,) and not isinstance(check(trial), str):
                lines = trial
                cut = True
                break
    return lines


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
            if out is not None and not isinstance(out, str):
                first = shrink(lines)
                break
            if isinstance(out, str):
                first = ["UNREADABLE " + out] + lines
                break
        if first is None:
            print("%-8s %4d programs agree" % (name, rounds), flush=True)
        else:
            bad += 1
            print("%-8s DISAGREE" % name, flush=True)
            print("   " + "\n   ".join(first), flush=True)
            want, got = check(first)
            print("   want %s" % want, flush=True)
            print("   got  %s" % got, flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
