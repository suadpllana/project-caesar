"""Refresh tests/pristine from environment/app_src. Run after every environment edit."""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "environment", "app_src")
DST = os.path.join(ROOT, "tests", "pristine")


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = 0
    for base, dirs, files in os.walk(DST):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            p = os.path.join(base, fn)
            with open(p, "rb") as fh:
                body = fh.read()
            if b"\r\n" in body:
                with open(p, "wb") as fh:
                    fh.write(body.replace(b"\r\n", b"\n"))
            n += 1
    print("pristine: %d files" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
