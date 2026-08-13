#!/usr/bin/env python3
"""Refresh tests/pristine from environment/app_src.

The verifier overlays the agent's declared file onto a pristine copy of the tree, so that
copy has to be byte-identical to what the agent's image was built from. Run this after any
change under environment/app_src and before packaging.
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def main() -> int:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # The verifier also needs the base config at a fixed path for the grader.
    shutil.copyfile(SRC / "conf" / "view.json", TASK / "tests" / "view.json")

    diff = filecmp.dircmp(SRC, DST, ignore=["__pycache__"])
    bad = []

    def walk(d):
        if d.left_only or d.right_only or d.diff_files:
            bad.append((d.left, d.left_only, d.right_only, d.diff_files))
        for sub in d.subdirs.values():
            walk(sub)

    walk(diff)
    if bad:
        for where, l, r, df in bad:
            print("MISMATCH in %s: only-left=%s only-right=%s differing=%s"
                  % (where, l, r, df))
        return 1
    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print("pristine synced: %d files" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
