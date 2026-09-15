"""tests/pristine/ is a copy of the agent-facing tree, and copies go stale.

The verifier lays the six submitted files over this copy, so if it drifts from
environment/app_src the oracle fails inside the worker with an import error that reads like
a broken task. Run this after any change to environment/, and `--check` in the gate sweep.

    python sync_pristine.py [--check]
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "page-window-reuse"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def files(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.exists():
            print("pristine copy missing")
            return 1
        bad = []
        left, right = files(SRC), files(DST)
        for name in sorted(set(left) | set(right)):
            if name not in left or name not in right:
                bad.append("%s only on one side" % name)
            elif not filecmp.cmp(SRC / name, DST / name, shallow=False):
                bad.append("%s differs" % name)
        for line in bad:
            print(line)
        print("pristine %s" % ("STALE" if bad else "in step with environment/app_src"))
        return 1 if bad else 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("copied %d files" % len(files(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
