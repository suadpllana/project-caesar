#!/usr/bin/env python3
"""Print the reference and the model trace of one enumerated case, side by side.

Authoring only; never ships.

    python3 -u authoring/expert-defer-shed/show.py <case> [<case> ...]
    python3 -u authoring/expert-defer-shed/show.py --all
"""
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "expert-defer-shed"
PARTS = ("gate", "cap", "buf", "back", "put", "trim", "tally")


def main():
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import model

    room = Path(tempfile.mkdtemp(prefix="eds-show-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for part in PARTS:
        shutil.copy(TASK / "solution" / ("%s.py" % part), here / "lay" / ("%s.py" % part))
    sys.path.insert(0, str(here))
    import run_lay

    names = cases.ORDER if sys.argv[1:2] == ["--all"] else sys.argv[1:]
    bad = 0
    for name in names:
        lines = cases.prog(name)
        got = run_lay.run("\n".join(lines) + "\n")
        exp = model.expect(lines)
        print("== %s" % name)
        for line in lines:
            print("   | %s" % line)
        for line in got:
            print("   %s" % line)
        if got != exp:
            bad += 1
            print("   MODEL DISAGREES: %r" % (exp,))
        print()
    shutil.rmtree(room, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
