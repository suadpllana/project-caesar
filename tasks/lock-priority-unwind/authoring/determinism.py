#!/usr/bin/env python3
"""The drawn task sets must be identical across processes, not merely across runs.

tests/runner.py builds the drawn sets in one process and tests/test_outputs.py rebuilds them in
another. If those two disagree about what `drawn-007` even is, a correct policy fails on
whichever sets differ and the failure is indistinguishable from a wrong answer - an intermittent
loss of the reference with nothing wrong with it. Python randomises string hashing per process,
so any generator that turns a set or a dict into a sequence is exposed.

This runs the generator in several processes under different PYTHONHASHSEED values and requires
the output to hash the same every time.

Usage:
    python3 authoring/determinism.py [sets]
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent

CHILD = r'''
import hashlib, json, os, sys
sys.path.insert(0, os.environ["TESTS"])
import scen
sets = scen.batch(scen.seed_from(os.environ["SEED"]), int(os.environ["N"]))
blob = json.dumps(sets, sort_keys=True, separators=(",", ":")).encode("utf-8")
sys.stdout.write(hashlib.sha256(blob).hexdigest())
'''


def main(argv):
    n = argv[1] if len(argv) > 1 else "60"
    seen = {}
    for hs in ("0", "1", "12345", "99991", "random"):
        env = dict(os.environ, PYTHONHASHSEED=hs, TESTS=str(TASK / "tests"),
                   SEED="determinism", N=n)
        out = subprocess.run([sys.executable, "-c", CHILD], env=env, capture_output=True,
                             text=True)
        if out.returncode:
            print("generator failed under PYTHONHASHSEED=%s\n%s" % (hs, out.stderr[-800:]))
            return 1
        seen.setdefault(out.stdout.strip(), []).append(hs)
    for digest, seeds in sorted(seen.items()):
        print("  %s  PYTHONHASHSEED=%s" % (digest[:16], ",".join(seeds)))
    if len(seen) != 1:
        print("the drawn sets differ between processes - the runner and the grader will disagree")
        return 1
    print("%s sets identical across %d hash seeds" % (n, sum(len(v) for v in seen.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
