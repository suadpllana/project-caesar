"""Mirror environment/app_src into tests/pristine, or check that the mirror is current.

The worker lays the six submitted modules over tests/pristine, so the pristine copy must be the
shipped tree exactly (CLAUDE.md, publish-settle-order: a stale mirror fails the oracle with an
ImportError that reads like a broken task). Run with --check after any change to environment/.
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "live-region-reader")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def listing(top):
    out = set()
    for d, dirs, files in os.walk(top):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            out.add(os.path.relpath(os.path.join(d, f), top))
    return out


def check():
    a, b = listing(SRC), listing(DST) if os.path.isdir(DST) else set()
    if a != b:
        print("pristine differs in files:", sorted(a ^ b))
        return 1
    bad = [f for f in sorted(a) if not filecmp.cmp(os.path.join(SRC, f), os.path.join(DST, f),
                                                   shallow=False)]
    if bad:
        print("pristine differs in content:", bad)
        return 1
    print("pristine is current (%d files)" % len(a))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
