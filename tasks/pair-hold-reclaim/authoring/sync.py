"""Refresh tests/pristine from environment/app_src.

The verifier image bakes a copy of the tree and compares the executed one against it
after the run, so the two have to be byte-identical. Nothing here is hand-edited.

    python3 authoring/sync.py
"""

import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(1 for p in DST.rglob("*") if p.is_file())
    print("synced %d files into tests/pristine" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
