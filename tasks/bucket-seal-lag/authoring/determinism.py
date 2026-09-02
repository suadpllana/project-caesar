"""The generated set must be identical across processes.

The runner builds these plans in one process and the grader rebuilds them in
another. Python randomises string hashing per process, so a generator that turns
a set or a dict into a sequence without sorting builds different plans in each,
and the reference then fails on whichever ones differed - an intermittent failure
that looks like a wrong answer and is not one.
"""

import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

SNIP = (
    "import sys; sys.path.insert(0, %r); import gen; "
    "print(__import__('hashlib').sha256("
    "''.join(gen.text(p) for _, p in gen.batch('dcheck', 60)).encode()).hexdigest())"
) % str(ROOT / "tests")


def main():
    seen = {}
    for seed in ("0", "1", "12345", "99991"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        out = subprocess.run([sys.executable, "-c", SNIP], env=env,
                             capture_output=True, text=True)
        if out.returncode != 0:
            raise SystemExit(out.stderr[-800:])
        seen[seed] = out.stdout.strip()
    vals = sorted(set(seen.values()))
    for seed in sorted(seen):
        print("PYTHONHASHSEED=%-6s %s" % (seed, seen[seed]))
    if len(vals) != 1:
        raise SystemExit("the generated set is not stable across processes")
    print("stable across %d hash seeds" % len(seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
