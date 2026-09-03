"""Refresh tests/pristine from the shipped tree.

The verifier compares the executed tree against this copy after the run, so a drift
between the two is a task that fails its own integrity check. Run it after every edit
under environment/app_src.
"""

import pathlib
import shutil

TASK = pathlib.Path(__file__).resolve().parent.parent
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print("pristine refreshed: %d files" % n)


if __name__ == "__main__":
    main()
