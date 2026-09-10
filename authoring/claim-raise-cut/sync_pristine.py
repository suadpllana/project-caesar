"""Keep tests/pristine in step with environment/app_src.

The verifier lays the five submitted modules over its own copy of the tree, so that copy has to
be the tree that shipped. It is a copy, and copies go stale: `--check` fails when it has.
"""

import filecmp
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent.parent / "tasks" / "claim-raise-cut"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def files(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.exists():
            print("pristine is missing")
            return 1
        a, b = files(SRC), files(DST)
        if a != b:
            print("pristine differs in file list: %s" % (set(a) ^ set(b)))
            return 1
        bad = [f for f in a if not filecmp.cmp(SRC / f, DST / f, shallow=False)]
        if bad:
            print("pristine is stale: %s" % ", ".join(bad))
            return 1
        print("pristine matches app_src (%d files)" % len(a))
        return 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("pristine rebuilt from app_src (%d files)" % len(files(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
