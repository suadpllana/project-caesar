#!/usr/bin/env python3
"""Copy environment/app_src to tests/pristine, the tree the worker lays submissions over.

tests/pristine is a copy, and copies go stale: rebuilding the environment without re-syncing it
once made an oracle fail with an ImportError inside the worker (CLAUDE.md,
publish-settle-order). Run this after any change to environment/, and --check before any gate.

    python3 sync_pristine.py [--check]
"""
import filecmp
import shutil
import sys

import lab

DST = lab.TASK / "tests" / "pristine"


def same(a, b):
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(same(a / d, b / d) for d in cmp.common_dirs)


def main(argv):
    if "--check" in argv:
        ok = DST.is_dir() and same(lab.SRC, DST)
        print("tests/pristine %s environment/app_src" % ("matches" if ok else "DIFFERS FROM"))
        return 0 if ok else 1
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(lab.SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("tests/pristine synced")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
