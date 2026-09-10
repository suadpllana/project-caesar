"""Wall clock for one service over the whole graded set.

Run as a subprocess, one variant at a time, with output flushed: a timing harness that
buffers its own prints looks exactly like a hang.

    python3 -u authoring/claim-raise-cut/time_all.py <overlay-dir> [seed] [per] [heavy]
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402


def main():
    where = sys.argv[1] if len(sys.argv) > 1 else str(TASK / "solution")
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 41
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    heavy = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    go = lab.runner(where, "time")
    work = cases.programs() + gen.programs(seed, per, heavy)
    worst = ("", 0.0)
    steps = 0
    t0 = time.time()
    for name, program in work:
        steps += len(program)
        a = time.time()
        go(program)
        d = time.time() - a
        if d > worst[1]:
            worst = (name, d)
    total = time.time() - t0
    print("%-22s %4d programs  %7d steps  %8.2fs total  worst %s %.2fs"
          % (Path(where).name, len(work), steps, total, worst[0], worst[1]), flush=True)


if __name__ == "__main__":
    main()
