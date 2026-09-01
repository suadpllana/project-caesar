"""Does the generator build the same journals in two different processes?

It has to. The runner drives the journals in one process and the grader rebuilds them in
another, from the same nonce, and compares row for row. If the two processes disagree about
what journal g0022 even is, a correct submission fails on whichever ones happened to differ
and the failure looks exactly like a wrong answer.

This is not hypothetical. It happened here on 2026-09-01: a generator step shuffled a list
built by iterating a set of node names, Python randomises string hashing per process, and
the reference lost one journal in thirty with nothing wrong with it. Every collection the
generator turns into a sequence has to be sorted first, and this is the check that says so.

Two processes are spawned with different PYTHONHASHSEED values on purpose, because equal
seeds would hide exactly the fault being looked for.

    python authoring/determinism.py 40
"""

import hashlib
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

PROBE = """
import sys, hashlib
sys.path.insert(0, %r)
import gen
acc = hashlib.sha256()
for name, seed in gen.batch("determinism-nonce", %d):
    acc.update(name.encode())
    acc.update(gen.text(seed).encode())
print(acc.hexdigest())
"""


def once(seed, count):
    out = subprocess.run(
        [sys.executable, "-c", PROBE % (str(ROOT / "tests"), count)],
        env=dict(os.environ, PYTHONHASHSEED=str(seed)),
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    marks = [once(seed, count) for seed in (0, 1, 12345, 999983)]
    for seed, mark in zip((0, 1, 12345, 999983), marks):
        print("PYTHONHASHSEED=%-8s %s" % (seed, mark))
    if len(set(marks)) == 1:
        print("\n%d journals identical across four hash seeds" % count)
        return 0
    print("\nTHE GENERATOR IS NOT DETERMINISTIC ACROSS PROCESSES.")
    print("Something in tests/gen.py turns a set or a dict into a sequence without")
    print("sorting it first. The runner and the grader will build different journals.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
