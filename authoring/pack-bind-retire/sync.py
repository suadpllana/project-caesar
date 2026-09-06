"""Refresh tests/pristine from environment/app_src.

The verifier assembles the tree it runs from the pristine copy plus the declared artifacts,
so a pristine copy that has drifted from the shipped tree grades a tree no agent was given.
Run this after any change under environment/app_src.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def main():
    if not os.path.isdir(SRC):
        print("no source tree at %s" % SRC)
        return 1
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(len(f) for _, _, f in os.walk(DST))
    print("pristine refreshed: %d files" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
