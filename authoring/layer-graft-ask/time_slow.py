"""Time the reference and the naive-but-correct families against the stated limit.

Every family here produces exactly the reference's answers on everything it finishes; the
limit is the only thing that separates them, which is what makes the gate a scaling boundary
rather than an undisclosed timeout. Output is flushed after every row: a buffered timing
harness looks exactly like a hang.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tasks" / "layer-graft-ask" / "tests"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import lab  # noqa: E402

FAMS = {
    "reference": [],
    "walkcount": [HERE / "slow" / "walkcount"],
    "expand": [HERE / "slow" / "expand"],
    "nomemo": [HERE / "slow" / "nomemo"],
}


def main(argv):
    which = argv[1:] or ["wide-000", "deep-000"]
    progs = dict(gen.programs("timing", 1, scale=1))
    box = tempfile.mkdtemp(prefix="lgatime-")
    for name in which:
        path = os.path.join(box, name + ".txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(progs[name])
        for fam, extra in FAMS.items():
            work = lab.stage([lab.TASK / "solution"] + extra)
            start = time.time()
            try:
                got = lab.run(work, path, timeout=240)
                took = time.time() - start
                print("%-12s %-10s rc=%d %8.2f s  %d lines"
                      % (name, fam, got.returncode, took,
                         len(got.stdout.strip().split("\n")) if got.stdout else 0), flush=True)
                if got.returncode != 0:
                    print("      " + got.stderr.strip().split("\n")[-1][:160], flush=True)
            except subprocess.TimeoutExpired:
                print("%-12s %-10s TIMEOUT > 240 s" % (name, fam), flush=True)
            shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(box, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
