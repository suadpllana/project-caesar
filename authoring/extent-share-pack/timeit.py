"""Time an implementation of the six files on the shipped programs."""
import pathlib
import resource
import sys
import time

import harness

SOL = harness.TASK / "solution"
PROGS = harness.APP / "progs"


def main():
    over = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else SOL
    names = sys.argv[2:] or ["tiny.txt", "pair.txt", "wide.txt", "deep.txt"]
    run = harness.runner(over)
    for name in names:
        lines = (PROGS / name).read_text(encoding="utf-8").splitlines()
        t0 = time.time()
        out = run(lines)
        t1 = time.time()
        mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        print("%-10s %8.2f s  %7d lines out  peak %6.0f MB  tail %s"
              % (name, t1 - t0, len(out), mb, out[-1] if out else "-"), flush=True)


if __name__ == "__main__":
    main()
