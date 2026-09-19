#!/usr/bin/env python3
"""What the graded set costs, for the reference and for the readings the limit is there for.

The execution limit is the only thing that separates a keeper that finds the rows pointing at
a key by walking the table from one that does not, so the number it is set at has to be
measured rather than chosen. Every run here is a subprocess, because a walk of the table on
the wide families does not come back quickly and an in-process run would take the measurement
down with it.

    python3 -u authoring/referential-action-order/timing.py [per]
"""
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

DRIVER = '''
import json, sys, time
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, gen, run_keep
per = int(sys.argv[1])
work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs("timing-seed", per)
t0 = time.time()
for fam, name, lines in work:
    run_keep.run("\\n".join(lines) + "\\n")
print(json.dumps({"seconds": time.time() - t0, "programs": len(work)}))
'''


def measure(here, per, limit):
    src = DRIVER % (str(here), str(lab.TASK / "tests"))
    start = time.time()
    done = subprocess.run([sys.executable, "-c", src, str(per)], cwd=str(here),
                          capture_output=True, text=True, timeout=limit)
    wall = time.time() - start
    if done.returncode != 0:
        return wall, done.stderr.strip().splitlines()[-1:]
    return wall, None


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    for build in (emit.slow_scan, emit.slow_wait, emit.nop_shipped):
        build()
    rows = [("reference", lab.tree(lab.SOL))]
    for name in ("slow-scan", "slow-wait"):
        rows.append((name, lab.tree(files=emit.BUILT[name])))
    for name, here in rows:
        try:
            wall, err = measure(here, per, 1500)
        except subprocess.TimeoutExpired:
            print("%-12s did not finish inside 1500s" % name, flush=True)
            continue
        print("%-12s %8.2fs%s" % (name, wall, "  " + str(err) if err else ""), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
