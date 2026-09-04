"""Refresh tests/pristine from environment/app_src.

The grader compares every frozen file in the executed tree against this copy,
so the two have to be byte-identical or the reference fails on a check that
has nothing to do with the rule.
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
    print("pristine refreshed from %s" % SRC)


if __name__ == "__main__":
    main()
