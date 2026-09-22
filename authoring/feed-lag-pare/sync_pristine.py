"""Keep tests/pristine in step with environment/app_src.

The worker lays the six submitted files over a copy of the shipped tree, so that copy has to
be the shipped tree. A stale copy makes the oracle fail inside the worker with an ImportError,
which reads like a broken task rather than a stale mirror (CLAUDE.md, 2026-09-08). Run this
after any change under environment/, and `--check` from the gate list.

    python authoring/feed-lag-pare/sync_pristine.py           copy
    python authoring/feed-lag-pare/sync_pristine.py --check   exit 1 if it has drifted
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "feed-lag-pare")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def walk(root):
    out = set()
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            out.add(os.path.relpath(os.path.join(base, name), root))
    return out


def main():
    check = "--check" in sys.argv[1:]
    here, there = walk(SRC), walk(DST) if os.path.isdir(DST) else set()
    same = filecmp.cmpfiles(SRC, DST, sorted(here & there), shallow=False)[0] if there else []
    drift = sorted((here - there) | (there - here) | (set(here & there) - set(same)))
    if check:
        if drift:
            print("tests/pristine has drifted from environment/app_src:")
            for name in drift:
                print("   ", name)
            return 1
        print("tests/pristine matches environment/app_src (%d files)" % len(here))
        return 0
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("copied %d files into tests/pristine" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
