"""The generated panels must be identical across processes.

The runner builds the panels in one process and the grader rebuilds them in another. If
those two disagree about what panel r0007 even is, a correct submission fails on whichever
ones differ and the failure is indistinguishable from a wrong answer - an intermittent
failure of the reference that looks like content.

Python randomises string hashing per process, so any generator that turns a set into a
sequence produces a different order in each. This runs the generator under several hash
seeds and compares.

    python3 authoring/determinism.py
"""

import hashlib
import os
import pathlib
import subprocess
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
SEEDS = ("0", "1", "17", "424242")

SNIP = (
    "import sys; sys.path.insert(0, %r)\n"
    "import gen, hashlib\n"
    "body = ''.join(n + t for n, t in gen.build('determinism', 60))\n"
    "print(hashlib.sha256(body.encode()).hexdigest())\n"
) % str(TASK / "tests")


def main():
    seen = {}
    for seed in SEEDS:
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", SNIP], env=env,
                             capture_output=True, text=True)
        if out.returncode != 0:
            print("the generator failed under PYTHONHASHSEED=%s:\n%s" % (seed, out.stderr))
            return 1
        seen.setdefault(out.stdout.strip(), []).append(seed)
    for digest, seeds in sorted(seen.items()):
        print("%s  PYTHONHASHSEED=%s" % (digest[:16], ",".join(seeds)))
    if len(seen) != 1:
        print("the generated panels are NOT identical across processes")
        return 1
    print("identical across %d hash seeds" % len(SEEDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
