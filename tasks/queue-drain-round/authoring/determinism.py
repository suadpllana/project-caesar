"""The generated set must be the same set in every process.

The runner builds the streams and the grader builds them again, in two processes. Python
randomises string hashing per process, so a generator that turns a set of names into a
sequence builds different streams in each, and a correct submission then fails on whichever
ones differed - a failure that looks exactly like a wrong answer.

    python3 authoring/determinism.py
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent

SNIP = (
    "import sys, hashlib;"
    "sys.path.insert(0, %r);"
    "import gen;"
    "print(hashlib.sha256(repr(gen.batch('7e5715eed', 200)).encode()).hexdigest())"
) % str(TASK / "tests")


def main():
    seen = set()
    for seed in ("0", "1", "17", "999"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", SNIP], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print("the generator failed under PYTHONHASHSEED=%s: %s" % (seed, r.stderr[-300:]))
            return 1
        seen.add(r.stdout.strip())
        print("PYTHONHASHSEED=%-4s %s" % (seed, r.stdout.strip()[:32]))
    if len(seen) != 1:
        print("the generated set is not the same in every process")
        return 1
    print("the same set in every process")
    return 0


if __name__ == "__main__":
    sys.exit(main())
