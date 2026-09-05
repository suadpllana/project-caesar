"""The generated set must be identical across processes under different hash seeds; the
runner and the grader are two processes."""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
CODE = ("import sys, hashlib; sys.path.insert(0, %r); import gen; "
        "h = hashlib.sha256(); [h.update(t.encode()) for _, t in gen.batch('det', 120)]; "
        "print(h.hexdigest())" % os.path.join(TASK, "tests"))


def main():
    seen = set()
    for seed in ("0", "1", "12345", "random"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", CODE], env=env, capture_output=True,
                             text=True).stdout.strip()
        seen.add(out)
        print("PYTHONHASHSEED=%-6s %s" % (seed, out[:16]))
    print("deterministic" if len(seen) == 1 else "NOT deterministic")
    return 0 if len(seen) == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
