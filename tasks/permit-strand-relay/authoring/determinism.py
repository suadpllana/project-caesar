"""The generated half must be identical across processes.

The runner builds the streams in one process and the grader rebuilds them in
another. If those two disagree about what stream g0007 even is, a correct
submission fails on whichever ones differ and the failure looks exactly like a
wrong answer. Python randomises string hashing per process, so any generator
that turns a set into a sequence builds different streams in each.
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = ("0", "1", "17", "1049", "random")

SNIP = (
    "import hashlib, json, sys; sys.path.insert(0, %r); import gen; "
    "print(hashlib.sha256(json.dumps(gen.batch(%d, %d), sort_keys=True)"
    ".encode()).hexdigest())"
)


def main():
    nonce = 90210
    wide = 300
    marks = {}
    for seed in SEEDS:
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        got = subprocess.run(
            [sys.executable, "-c", SNIP % (os.path.join(ROOT, "tests"), nonce, wide)],
            capture_output=True, text=True, env=env, timeout=300)
        if got.returncode != 0:
            print("PYTHONHASHSEED=%s failed\n%s" % (seed, got.stderr[-600:]))
            return 1
        marks[seed] = got.stdout.strip()
    every = sorted(set(marks.values()))
    for seed in SEEDS:
        print("PYTHONHASHSEED=%-7s %s" % (seed, marks[seed][:16]))
    if len(every) != 1:
        print("DIFFERENT across processes: %d distinct digests" % len(every))
        return 1
    print("identical across %d hash seeds" % len(SEEDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
