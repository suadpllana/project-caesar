#!/usr/bin/env python3
"""Keep tests/pristine/ the same tree as environment/app_src/. Never ships.

The verifier lays the five submitted files over its own copy of the tree. A stale copy makes
the oracle fail inside the worker with an ImportError that reads like a broken task.

    python3 -u authoring/glob-route-hide/sync_pristine.py [--check]
"""
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

DEST = lab.TASK / "tests" / "pristine"


def walk(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    if "--check" in sys.argv[1:]:
        if not DEST.is_dir():
            print("pristine is missing")
            return 1
        here, there = walk(lab.SRC), walk(DEST)
        if here != there:
            print("pristine holds different files: only in app_src %s, only in pristine %s"
                  % (sorted(set(here) - set(there)), sorted(set(there) - set(here))))
            return 1
        bad = [p for p in here if not filecmp.cmp(lab.SRC / p, DEST / p, shallow=False)]
        if bad:
            print("pristine is stale: %s" % bad)
            return 1
        print("pristine matches app_src (%d files)" % len(here))
        return 0
    shutil.rmtree(DEST, ignore_errors=True)
    shutil.copytree(lab.SRC, DEST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into tests/pristine" % len(walk(DEST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
