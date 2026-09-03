"""The generated feeds must be identical across processes, not merely across runs.

The runner builds the batch in one process and the grader rebuilds it in another.
If those two disagree about what feed `g0022` even is, a correct submission fails
on whichever ones differ, and the failure is indistinguishable from a wrong
answer - an intermittent loss of the reference, which reads as content and is
packaging. Python randomises string hashing per process, so a generator that
turns a set of names into a sequence anywhere builds different feeds in each.

Four seeds, four child processes, one digest.
"""

import hashlib
import os
import subprocess
import sys

import lab

PROBE = r"""
import hashlib, json, sys
sys.path.insert(0, sys.argv[1])
import gen
pot = hashlib.sha256()
for name, text in gen.batch("determinism", 120):
    pot.update((name + "\n" + text).encode("utf-8"))
sys.stdout.write(pot.hexdigest())
"""


def main():
    where = str(lab.ROOT / "tests")
    seen = {}
    for seed in ("0", "1", "17", "4242"):
        run = subprocess.run([sys.executable, "-c", PROBE, where],
                             capture_output=True, text=True,
                             env=dict(os.environ, PYTHONHASHSEED=seed),
                             timeout=600)
        if run.returncode != 0:
            print("PYTHONHASHSEED=%s failed: %s" % (seed, run.stderr[-400:]))
            return 1
        seen[seed] = run.stdout.strip()
        print("PYTHONHASHSEED=%-5s %s" % (seed, seen[seed]))
    if len(set(seen.values())) != 1:
        print("\nthe batch is NOT the same across processes")
        return 1
    print("\nthe batch is identical across every hash seed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
