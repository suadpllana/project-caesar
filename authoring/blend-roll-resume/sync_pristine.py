"""Keep tests/pristine/ identical to environment/app_src/.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the tree that shipped. A stale mirror makes the oracle fail inside the worker, which reads like
a broken task rather than a copy nobody re-synced.

Usage: sync_pristine.py [--check]
"""
import filecmp
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "tasks" / "blend-roll-resume"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def walk(root):
    return sorted(
        str(p.relative_to(root)) for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in str(p))


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.exists():
            print("pristine/ is missing")
            return 1
        a, b = walk(SRC), walk(DST)
        bad = [x for x in set(a) | set(b) if x not in a or x not in b]
        for rel in sorted(set(a) & set(b)):
            if not filecmp.cmp(SRC / rel, DST / rel, shallow=False):
                bad.append(rel)
        for rel in sorted(set(bad)):
            print("differs:", rel)
        print("pristine is %s" % ("stale" if bad else "current"))
        return 1 if bad else 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
