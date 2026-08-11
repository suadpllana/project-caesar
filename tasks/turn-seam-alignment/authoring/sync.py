#!/usr/bin/env python3
"""Refresh the verifier's sealed copies of the shipped tree.

tests/pristine must be byte-identical to environment/app_src: the verifier overlays the
agent's declared files onto it, so any drift would mean the run is graded against a tree
the agent never saw. tests/merges.json is the same table the sealed oracle encodes with,
and tests/loop.json the same config, both copied rather than imported.

Usage:  python3 authoring/sync.py
"""

from __future__ import annotations

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
    shutil.copyfile(SRC / "tok" / "merges.json", TASK / "tests" / "merges.json")
    shutil.copyfile(SRC / "conf" / "loop.json", TASK / "tests" / "loop.json")
    n = sum(1 for p in DST.rglob("*") if p.is_file())
    print("synced %d files into tests/pristine" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
