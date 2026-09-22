"""Keep tests/pristine in step with environment/app_src.

The verifier lays the six submitted files over its own copy of the tree, so that copy has
to be the tree that shipped. A stale copy shows up as an ImportError inside the worker,
which reads like a broken task rather than a mirror nobody re-synced. Run with --check
after any change under environment/.
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "tasks" / "replay-match-drift" / "environment" / "app_src"
DST = ROOT / "tasks" / "replay-match-drift" / "tests" / "pristine"


def walk(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    here = walk(SRC)
    if check:
        there = walk(DST) if DST.exists() else []
        bad = [str(p) for p in set(here) ^ set(there)]
        bad += [str(p) for p in here if p in there
                and not filecmp.cmp(SRC / p, DST / p, shallow=False)]
        for row in sorted(bad):
            print("differs: %s" % row)
        print("%d files, %d out of step" % (len(here), len(bad)))
        return 1 if bad else 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into %s" % (len(walk(DST)), DST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
