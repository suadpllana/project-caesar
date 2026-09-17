"""Keep tests/pristine in step with environment/app_src.

The verifier lays the submitted files over its own copy of the tree, so that copy has to be the
shipped one. A stale copy fails the oracle with an import error inside the worker, which reads
like a broken task rather than a stale mirror.
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "claim-cover-lift"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def walk(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            print("pristine copy missing")
            return 1
        left, right = walk(SRC), walk(DST)
        if left != right:
            print("differs in the file list: %s" % (set(left) ^ set(right)))
            return 1
        bad = [name for name in left if not filecmp.cmp(SRC / name, DST / name, shallow=False)]
        if bad:
            print("differs: %s" % bad)
            return 1
        print("pristine copy matches the shipped tree (%d files)" % len(left))
        return 0
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
