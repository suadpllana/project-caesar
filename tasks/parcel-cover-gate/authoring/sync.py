"""Refresh tests/pristine from environment/app_src.

The grader compares the tree that ran against this copy and derives its digest
baseline by compiling these sources, so a stale pristine is a reference that
scores 0 for a reason that has nothing to do with the task. Run it after every
edit under environment/.
"""

import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
SRC = HERE / "environment" / "app_src"
DST = HERE / "tests" / "pristine"


def main():
    if not SRC.is_dir():
        print("no %s" % SRC)
        return 1
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    kept = sorted(p.relative_to(DST).as_posix()
                  for p in DST.rglob("*") if p.is_file())
    for rel in kept:
        raw = (DST / rel).read_bytes()
        if b"\r\n" in raw:
            (DST / rel).write_bytes(raw.replace(b"\r\n", b"\n"))
    print("%d files -> %s" % (len(kept), DST))
    for rel in kept:
        print("  " + rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
