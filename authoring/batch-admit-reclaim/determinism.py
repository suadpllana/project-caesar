"""Does anything here depend on the interpreter's hash seed?

Generators sort every collection before use and the pool is keyed by token
tuples, so nothing should. This runs the whole graded path - trace generation,
the reference, the sealed model, and the ground truth the two agree on - under
several PYTHONHASHSEED values and compares the bytes. A drift here would show up
in the pipeline as a reference that scores 1 on one machine and 0 on another.

Usage: python3 authoring/batch-admit-reclaim/determinism.py
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEEDS = ("0", "1", "17", "4093", "65535")

PROBE = r"""
import hashlib, json, os, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import gen, oracle, play
ref = play.reference(os.path.join(%r, "seedref"))
acc = hashlib.sha256()
for name, text in gen.batch("determinism", 60):
    acc.update(name.encode())
    acc.update(json.dumps(play.safe(ref, text), sort_keys=True).encode())
    acc.update(json.dumps(oracle.play(text), sort_keys=True).encode())
with open(os.path.join(%r, "gt.json")) as fh:
    acc.update(fh.read().encode())
print(acc.hexdigest())
"""


def main():
    tests = os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests")
    work = os.environ.get("WORK", "/tmp/bar-work")
    code = PROBE % (HERE, tests, work, tests)
    seen = {}
    for seed in SEEDS:
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        run = subprocess.run([sys.executable, "-c", code], env=env,
                             capture_output=True, text=True)
        if run.returncode:
            print("seed %s failed:\n%s" % (seed, run.stderr[-800:]))
            return 1
        seen[seed] = run.stdout.strip()
        print("  PYTHONHASHSEED=%-6s %s" % (seed, seen[seed][:32]))
    if len(set(seen.values())) == 1:
        print("identical under %d hash seeds" % len(SEEDS))
        return 0
    print("DIFFERS between hash seeds")
    return 1


if __name__ == "__main__":
    sys.exit(main())
