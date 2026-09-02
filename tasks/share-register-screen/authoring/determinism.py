"""The graded registers must be the same in every process that builds them.

The runner builds them in one process and the grader rebuilds them in another. Python
randomises string hashing per process, so a generator that turns a set of strings into a
sequence builds different registers in each, and a correct submission then loses whichever
ones differ, intermittently, with a failure that looks exactly like a wrong answer.

Usage:
    python3 authoring/determinism.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
SEEDS = ("0", "1", "7", "99", "12345")

SNIP = (
    "import hashlib, sys; sys.path.insert(0, %r); import gen; "
    "b = gen.batch('determinism', 60); "
    "print(hashlib.sha256(''.join(n + t for n, t in b).encode()).hexdigest())"
) % str(TASK / "tests")


def main():
    marks = []
    for seed in SEEDS:
        env = dict(os.environ, PYTHONHASHSEED=seed)
        proc = subprocess.run([sys.executable, "-c", SNIP], capture_output=True, text=True,
                              env=env)
        if proc.returncode != 0:
            print(proc.stderr[-1500:])
            return 1
        mark = proc.stdout.strip()
        marks.append(mark)
        print("   PYTHONHASHSEED=%-6s %s" % (seed, mark[:32]))
    print()
    if len(set(marks)) == 1:
        print("   the same 60 registers in every process")
        return 0
    print("   THE GENERATOR IS NOT DETERMINISTIC ACROSS PROCESSES.")
    print("   Sort every collection it turns into a sequence, including list(set) and")
    print("   plain iteration over a set or a dict keyed by strings.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
