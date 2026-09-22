import pathlib as _pl, sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent / "tasks" / "entry-lift-restate" / "tests"))  # TESTS_ON_PATH
"""Time the specification against the reference on the two scale families.

    python -u timing.py <size> [--naive]

Output is the measurement the resource gate rests on, so it is flushed line by line: a timing
harness whose output sits in a buffer looks exactly like a hang (CLAUDE.md, publish-settle-order).
"""

import random
import sys
import time

import gen as families  # noqa: E402
import fast
import naive


def build(name, fn, size, seed):
    rng = random.Random("%s-%d-%d" % (name, size, seed))
    return "\n".join(fn(rng, size)) + "\n"


def main(argv):
    size = int(argv[1]) if len(argv) > 1 else 6000
    want_naive = "--naive" in argv
    for name, fn in families.BIG:
        for seed in (0, 1):
            text = build(name, fn, size, seed)
            lines = text.count("\n")
            gets = text.count("\nget ") + text.count("\noff ") * 0
            t0 = time.perf_counter()
            out = fast.run(text)
            t1 = time.perf_counter()
            print("%-5s seed %d  %6d lines  %5d answers  reference %8.2fs"
                  % (name, seed, lines, len(out), t1 - t0), flush=True)
            if want_naive:
                t0 = time.perf_counter()
                slow = naive.run(text)
                t1 = time.perf_counter()
                same = "agree" if slow == out else "DISAGREE"
                print("%-5s seed %d  %6d lines  %5d answers  walk      %8.2fs  %s"
                      % (name, seed, lines, len(slow), t1 - t0, same), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
