"""Keep tests/pristine in step with environment/app_src.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the shipped tree exactly. A stale mirror shows up as an ImportError inside the worker, which
reads like a broken task rather than like a copy nobody re-synced.

    python3 authoring/shard-redraw-resume/sync_pristine.py            copy
    python3 authoring/shard-redraw-resume/sync_pristine.py --check    compare only
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "tasks" / "shard-redraw-resume" / "environment" / "app_src"
DST = ROOT / "tasks" / "shard-redraw-resume" / "tests" / "pristine"


def files(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        bad = []
        left, right = files(SRC), files(DST)
        for rel in sorted(set(left) | set(right)):
            if rel not in left:
                bad.append("only in pristine: %s" % rel)
            elif rel not in right:
                bad.append("missing from pristine: %s" % rel)
            elif not filecmp.cmp(SRC / rel, DST / rel, shallow=False):
                bad.append("differs: %s" % rel)
        for line in bad:
            print(line)
        print("pristine %s" % ("STALE" if bad else "in step"))
        return 1 if bad else 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("copied %d files" % len(files(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
