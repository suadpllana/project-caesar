"""Refresh tests/pristine from the shipped tree, and hold the enumerated copies
of the three shipped sets against the files they were taken from.

The verifier image moves the pristine tree out of /tests at build time, so
cases.py cannot read those three sets off disk at run time and keeps them as
literals instead. Two copies of the same text is exactly the drift the solution
quality review objects to, so this fails when they part.
"""

import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
TREE = os.path.join(TASK, "environment", "app_src")
COPY = os.path.join(TASK, "tests", "pristine")


def refresh():
    if os.path.isdir(COPY):
        shutil.rmtree(COPY)
    shutil.copytree(TREE, COPY,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def compare():
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases
    bad = []
    for name in ("plain", "chain", "barred"):
        with open(os.path.join(TREE, "sets", name + ".txt")) as fh:
            disk = fh.read().strip() + "\n"
        if cases.SETS[name] != disk:
            bad.append(name)
    return bad


def main():
    refresh()
    bad = compare()
    if bad:
        print("cases.py has drifted from the tree on: %s" % bad)
        return 1
    print("pristine refreshed; the three shipped sets agree with cases.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
