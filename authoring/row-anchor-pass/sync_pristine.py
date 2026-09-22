#!/usr/bin/env python3
"""Copy environment/app_src into tests/pristine. Never ships.

tests/pristine is the tree the worker lays the submitted files over, so it is a copy and
copies go stale: rebuilding the environment without re-syncing it makes the oracle fail with
an ImportError inside the worker, which reads like a broken task rather than a stale mirror.
Run it after any change to environment/, and --check in the gate list.

    python3 -u authoring/row-anchor-pass/sync_pristine.py [--check]
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

DST = lab.TASK / "tests" / "pristine"


def listing(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in str(p))


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            print("tests/pristine is missing")
            return 1
        left, right = listing(lab.SRC), listing(DST)
        if left != right:
            print("tests/pristine differs in which files it holds")
            print("  only in environment:", sorted(set(left) - set(right))[:8])
            print("  only in pristine:   ", sorted(set(right) - set(left))[:8])
            return 1
        stale = [n for n in left if not filecmp.cmp(lab.SRC / n, DST / n, shallow=False)]
        if stale:
            print("tests/pristine is stale: %s" % stale)
            return 1
        print("tests/pristine matches environment/app_src (%d files)" % len(left))
        return 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(lab.SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into tests/pristine" % len(listing(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
