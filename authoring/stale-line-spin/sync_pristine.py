"""Keep tests/pristine/ an exact copy of environment/app_src/.

The worker lays the six submitted files over tests/pristine/, so a stale pristine copy makes
the verifier run a tree the agent never saw (CLAUDE.md, publish-settle-order). Run after every
change to environment/; `--check` reports drift without writing.
"""
import filecmp
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASK = os.path.join(ROOT, "tasks", "stale-line-spin")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def listing(root):
    out = set()
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            out.add(os.path.relpath(os.path.join(d, f), root))
    return out


def drift():
    a, b = listing(SRC), listing(DST) if os.path.isdir(DST) else set()
    diff = sorted(a ^ b)
    for rel in sorted(a & b):
        if not filecmp.cmp(os.path.join(SRC, rel), os.path.join(DST, rel), shallow=False):
            diff.append(rel)
    return diff


if "--check" in sys.argv:
    d = drift()
    print("pristine in sync" if not d else "pristine DRIFT: %s" % d)
    sys.exit(1 if d else 0)
if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
print("pristine synced: %d files" % len(listing(DST)))
