"""Refresh tests/pristine from environment/app_src. The verifier hashes the executed tree
against this copy, so it has to be byte-identical to what the agent image ships."""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(len(f) for _, _, f in os.walk(DST))
    print("pristine: %d files" % n)


if __name__ == "__main__":
    main()
