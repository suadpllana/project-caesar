"""Refresh tests/pristine from environment/app_src.

The verifier compares the executed tree against this copy after the run, so a stale
pristine directory fails a correct submission on files nobody touched. Run it after any
edit under environment/, before build_gt.py.
"""

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "environment" / "app_src"
DST = ROOT / "tests" / "pristine"


def main():
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    files = sorted(p.relative_to(DST).as_posix() for p in DST.rglob("*") if p.is_file())
    print("synced %d files into tests/pristine" % len(files))
    for f in files:
        print("  ", f)


if __name__ == "__main__":
    main()
