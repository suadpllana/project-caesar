"""Refresh tests/pristine from environment/app_src.

The verifier compares the executed tree against this copy, so a stale one turns an honest
run into a failure that reads like tampering. Run it after every edit under environment/.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(1 for p in DST.rglob("*") if p.is_file())
    print("tests/pristine refreshed: %d files" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
