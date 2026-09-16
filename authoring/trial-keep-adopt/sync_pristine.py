"""Keep tests/pristine/ the same tree the agent is given.

It is a copy, and copies go stale: rebuilding the environment without re-syncing it makes the
oracle fail with an ImportError inside the worker, which reads like a broken task rather than a
stale mirror (CLAUDE.md, publish-settle-order).

    python sync_pristine.py            copy environment/app_src over tests/pristine
    python sync_pristine.py --check    exit 1 if they differ
"""
import filecmp
import shutil
import sys

import lab

SRC = lab.TASK / "environment" / "app_src"
DST = lab.TASK / "tests" / "pristine"


def walk(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix == ".py")


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            print("pristine missing")
            return 1
        a, b = walk(SRC), walk(DST)
        if a != b:
            print("file lists differ:\n  src %s\n  dst %s" % (a, b))
            return 1
        bad = [f for f in a if not filecmp.cmp(SRC / f, DST / f, shallow=False)]
        if bad:
            print("differ: %s" % " ".join(bad))
            return 1
        print("pristine matches (%d files)" % len(a))
        return 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "progs"))
    print("synced %d files" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
