"""The generated sets must be identical across processes, not merely across runs.

The runner builds them in one process and the grader rebuilds them in another.
Python randomises string hashing per process, so a generator that turns a set of
strings into a sequence builds different sets on each side, and a correct
submission then loses whichever ones differed - which reads as a wrong answer
rather than as a broken generator.
"""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

SNIP = (
    "import sys, hashlib; sys.path.insert(0, %r); import gen; "
    "h = hashlib.sha256();\n"
    "[h.update((n + t).encode()) for n, t in gen.batch('probe-nonce', 150)];\n"
    "print(h.hexdigest())" % os.path.join(TASK, "tests")
)


def main():
    seen = {}
    for seed in ("0", "1", "7", "424242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", SNIP], capture_output=True,
                             text=True, env=env)
        if out.returncode != 0:
            print("generator failed under PYTHONHASHSEED=%s" % seed)
            print(out.stderr[-800:])
            return 1
        seen[seed] = out.stdout.strip()
        print("PYTHONHASHSEED=%-8s %s" % (seed, seen[seed][:32]))
    if len(set(seen.values())) != 1:
        print("the generated sets differ between processes")
        return 1
    print("the generated sets are identical across processes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
