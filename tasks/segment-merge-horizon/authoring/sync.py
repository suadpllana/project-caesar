#!/usr/bin/env python3
"""Refresh tests/pristine from environment/app_src.

The verifier image bakes a byte-identical copy of the agent tree and overlays only the
declared artifact onto it, so the two directories have to be the same or the attestation
in test_outputs.py fails for a reason that has nothing to do with the submission.

Usage:
    python3 authoring/sync.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent


def main() -> int:
    src = TASK / "environment" / "app_src"
    dst = TASK / "tests" / "pristine"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = 0
    for p in sorted(dst.rglob("*")):
        if p.is_file():
            raw = p.read_bytes()
            if b"\r\n" in raw:
                p.write_bytes(raw.replace(b"\r\n", b"\n"))
            n += 1
    conf = src / "conf" / "store.json"
    shutil.copyfile(conf, TASK / "tests" / "store.json")
    print("synced %d files into %s" % (n, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
