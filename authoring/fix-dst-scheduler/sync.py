"""Keep tests/pristine in step with environment/app_src.

tests/pristine is a copy, and copies go stale: rebuilding the environment
without re-syncing it makes the oracle fail with an ImportError inside the
worker, which reads like a broken task rather than a stale mirror.

    python sync.py            copy environment/app_src over tests/pristine
    python sync.py --check    exit 1 if they differ, printing what moved
"""

import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "fix-dst-scheduler")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def walk(base):
    out = set()
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            out.add(os.path.relpath(os.path.join(root, f), base))
    return out


def check():
    left, right = walk(SRC), walk(DST)
    bad = []
    for rel in sorted(left - right):
        bad.append("only in app_src: %s" % rel)
    for rel in sorted(right - left):
        bad.append("only in pristine: %s" % rel)
    for rel in sorted(left & right):
        if not filecmp.cmp(os.path.join(SRC, rel), os.path.join(DST, rel), shallow=False):
            bad.append("differs: %s" % rel)
    for line in bad:
        print(line)
    print("pristine is %s (%d files)" % ("stale" if bad else "in step", len(left)))
    return 1 if bad else 0


def copy():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=IGNORE)
    print("synced %d files into tests/pristine" % len(walk(DST)))
    return 0


sys.exit(check() if "--check" in sys.argv else copy())
