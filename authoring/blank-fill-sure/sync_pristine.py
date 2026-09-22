"""Keep tests/pristine an exact copy of environment/app_src.

The worker builds every graded tree from tests/pristine, not from the agent's /app, so the
driver, the loader and the printer the agent received are the ones that run. A copy goes stale
the moment environment/ changes without it (CLAUDE.md, 2026-09-08: a stale mirror made the
oracle fail with an ImportError that read like a broken task). Run after every change to the
environment; `--check` only reports.

Usage: python3 authoring/blank-fill-sure/sync_pristine.py [--check]
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def listing(root):
    out = set()
    for d, _dirs, files in os.walk(root):
        for f in files:
            if "__pycache__" in d or f.endswith(".pyc"):
                continue
            out.add(os.path.relpath(os.path.join(d, f), root))
    return out


def differences():
    a, b = listing(SRC), listing(DST) if os.path.isdir(DST) else set()
    diff = sorted(a ^ b)
    for rel in sorted(a & b):
        if not filecmp.cmp(os.path.join(SRC, rel), os.path.join(DST, rel), shallow=False):
            diff.append(rel)
    return diff


def main():
    diff = differences()
    if "--check" in sys.argv:
        for rel in diff:
            print("stale: %s" % rel)
        print("pristine is %s" % ("current" if not diff else "STALE"))
        return 1 if diff else 0
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("pristine synced: %d files" % len(listing(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
