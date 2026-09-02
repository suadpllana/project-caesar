"""The generated stream set must be identical across processes.

The runner builds these streams in one process and the grader rebuilds them in another.
If those two disagree about what stream g0022 even is, a correct submission fails on
whichever ones differ and the failure is indistinguishable from a wrong answer -- an
intermittent loss of the reference that looks like content. Python randomises string
hashing per process, so any generator that turns a set into a sequence is a candidate.

This runs the generator under four hash seeds in four separate interpreters and compares
digests.

    python3 authoring/determinism.py
"""

import hashlib
import os
import pathlib
import subprocess
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent

SNIPPET = (
    "import hashlib, sys; sys.path.insert(0, %r); import gen; "
    "print(hashlib.sha256(repr(gen.build('determinism', 60)).encode()).hexdigest())"
    % str(TASK / "tests"))


def main():
    seen = {}
    for seed in ("0", "1", "97", "random"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", SNIPPET], env=env,
                             capture_output=True, text=True)
        if out.returncode != 0:
            print("seed %s: generator failed\n%s" % (seed, out.stderr[-600:]))
            return 1
        seen[seed] = out.stdout.strip()
        print("PYTHONHASHSEED=%-16s %s" % (seed, seen[seed]))
    if len(set(seen.values())) != 1:
        print("\nthe generated set is NOT stable across processes")
        return 1
    print("\nthe generated set is identical under every hash seed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
