"""Keep tests/pristine/ the same tree the agent gets.

It is a copy, and copies go stale: rebuilding the environment without re-syncing it makes the
oracle fail with an ImportError inside the worker, which reads like a broken task rather than a
stale mirror (CLAUDE.md, 2026-09-08). Run it after any change to environment/, and `--check`
in the gate list.
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "beam-ban-carry"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def listing(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            raise SystemExit("tests/pristine is missing")
        left, right = listing(SRC), listing(DST)
        if left != right:
            raise SystemExit("pristine differs in file list: %s" %
                             sorted(set(left) ^ set(right)))
        bad = [one for one in left if not filecmp.cmp(SRC / one, DST / one, shallow=False)]
        if bad:
            raise SystemExit("pristine is stale: %s" % ", ".join(bad))
        print("pristine matches environment/app_src (%d files)" % len(left))
        return
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into tests/pristine" % len(listing(DST)))


if __name__ == "__main__":
    main()
