"""Keep tests/pristine/ a byte copy of environment/app_src/.

A copy goes stale. Rebuilding the environment without re-syncing this one makes the oracle
fail with an ImportError inside the worker, which reads like a broken task rather than a
stale mirror (CLAUDE.md, publish-settle-order).

    python sync_pristine.py            copy
    python sync_pristine.py --check    report differences, write nothing
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "tasks" / "entry-lift-restate" / "environment" / "app_src"
DST = ROOT / "tasks" / "entry-lift-restate" / "tests" / "pristine"


def listing(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main(argv):
    if "--check" in argv:
        if not DST.is_dir():
            print("no pristine copy at %s" % DST)
            return 1
        here, there = listing(SRC), listing(DST)
        bad = [p for p in set(here) | set(there)
               if p not in here or p not in there
               or not filecmp.cmp(SRC / p, DST / p, shallow=False)]
        if bad:
            print("stale: %s" % ", ".join(sorted(bad)))
            return 1
        print("pristine matches environment/app_src (%d files)" % len(here))
        return 0
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("copied %d files into %s" % (len(listing(DST)), DST))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
