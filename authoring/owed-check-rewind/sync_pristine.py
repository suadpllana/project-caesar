#!/usr/bin/env python3
"""Copy the shipped code tree into tests/pristine, or check that the copy is current. Never ships.

The verifier runs every submission over its own copy of the tree, so the driver, the parser, the
catalog and the line writer cannot be reshaped. That copy goes stale the moment the environment
changes without it (CLAUDE.md, publish-settle-order), and a stale copy reads like a broken task.
Only code is copied: the sample programs under progs/ are for the agent, not for grading.

    python3 authoring/owed-check-rewind/sync_pristine.py [--check]
"""
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "owed-check-rewind"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def code(root):
    return sorted(p.relative_to(root) for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def main(argv):
    if "--check" in argv:
        a, b = code(SRC), code(DST) if DST.is_dir() else []
        bad = [str(p) for p in a if p not in b or not filecmp.cmp(SRC / p, DST / p, shallow=False)]
        bad += [str(p) + " (extra)" for p in b if p not in a]
        for p in bad:
            print("STALE", p)
        print("pristine is %s" % ("current" if not bad else "stale"))
        return 1 if bad else 0
    if DST.exists():
        shutil.rmtree(DST)
    for p in code(SRC):
        (DST / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / p, DST / p)
    print("copied %d files into %s" % (len(code(SRC)), DST.relative_to(TASK.parent.parent)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
