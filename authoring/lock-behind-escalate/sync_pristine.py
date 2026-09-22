#!/usr/bin/env python3
"""Keep tests/pristine/ the same tree as environment/app_src/. Never ships.

The verifier lays the six submitted files over its own copy of the tree, and that copy is a
copy: rebuild the environment without re-syncing it and the oracle fails inside the worker
with an ImportError, which reads like a broken task rather than a stale mirror.

    python3 -u authoring/lock-behind-escalate/sync_pristine.py [--check]
"""
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

DEST = lab.TASK / "tests" / "pristine"


def listing(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in str(p))


def main():
    if "--check" in sys.argv[1:]:
        if not DEST.is_dir():
            print("pristine is missing")
            return 1
        here, there = listing(lab.SRC), listing(DEST)
        if here != there:
            print("pristine differs in which files it holds:")
            print("   only in app_src: %s" % sorted(set(here) - set(there)))
            print("   only in pristine: %s" % sorted(set(there) - set(here)))
            return 1
        stale = [p for p in here if not filecmp.cmp(lab.SRC / p, DEST / p, shallow=False)]
        if stale:
            print("pristine is stale: %s" % stale)
            return 1
        print("pristine matches app_src (%d files)" % len(here))
        return 0
    shutil.rmtree(DEST, ignore_errors=True)
    shutil.copytree(lab.SRC, DEST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into tests/pristine" % len(listing(DEST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
