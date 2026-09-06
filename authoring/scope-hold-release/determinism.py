"""The generated set must be identical across processes under different hash seeds.

The runner builds the streams in one process and the grader rebuilds them in
another. A generator that turns a set into a sequence builds different streams in
each, and the reference then fails intermittently on streams nothing is wrong
with. Every collection this generator sequences must be sorted first.
"""

import hashlib
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name

SNIPPET = (
    "import hashlib, sys\n"
    "sys.path.insert(0, %r)\n"
    "import gen\n"
    "h = hashlib.sha256()\n"
    "for s in range(200):\n"
    "    rows, ops = gen.stream('det-%%d' %% s, s %% 2 == 0)\n"
    "    h.update(repr(rows).encode())\n"
    "    h.update(repr(ops).encode())\n"
    "print(h.hexdigest())\n"
) % str(TASK / "tests")


def main():
    seen = {}
    for seed in ("0", "1", "7", "12345", "99991"):
        r = subprocess.run([sys.executable, "-c", SNIPPET], capture_output=True, text=True,
                           env={"PYTHONHASHSEED": seed, "SYSTEMROOT": r"C:\Windows",
                                "PATH": "/usr/bin:/bin"})
        if r.returncode != 0:
            print("generator failed under PYTHONHASHSEED=%s" % seed)
            print(r.stderr[-500:])
            return 1
        seen.setdefault(r.stdout.strip(), []).append(seed)
    for digest, seeds in sorted(seen.items()):
        print("  %s  seeds %s" % (digest[:16], ",".join(seeds)))
    if len(seen) != 1:
        print("FAIL the generated set differs across hash seeds")
        return 1
    print("identical across %d hash seeds" % sum(len(v) for v in seen.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
