"""Copy the shipped tree into tests/pristine, so the two cannot drift.

The verifier lays the four declared artifacts over an untouched copy of the tree
and then holds everything else to it. That copy has to be the tree as it ships,
including the three policy files that ship wrong, or the comparison is against
something no agent ever saw.

Usage: python3 authoring/batch-admit-reclaim/sync.py
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "batch-admit-reclaim")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    count = sum(len(f) for _, _, f in os.walk(DST))
    print("pristine: %d files copied from the shipped tree" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
