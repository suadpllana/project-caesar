"""Run every cheat and record not just the reward but which test caught it.

A sweep that only reports zeroes cannot tell a cheat that was rejected from a
cheat that was never installed - which is exactly the defect this kit found once
before, eighteen clean zeroes from a runner that had silently graded the shipped
tree every time. So each row here also names the failing test, and a reading cheat
that is caught only by a crash, or an attack cheat that never reaches the grader,
is reported as suspect rather than as a pass.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "span-close-step"))

import trial  # noqa: E402
import shellcheats  # noqa: E402

CHEATS = ROOT / "tasks" / "span-close-step" / "cheat"


def main():
    only = sys.argv[1:] or None
    rc = 0
    for path in sorted(CHEATS.glob("cheat-*.sh")):
        slug = path.stem[len("cheat-"):]
        if only and slug not in only:
            continue
        got = trial.detail("sh", script=str(path))
        kind = "attack" if slug in shellcheats.ATTACKS or slug == "forge-from-gt" else "reading"
        why = ", ".join(got["failed"][:2]) or "-"
        note = ""
        if got["reward"] != 0:
            note = "SCORED 1"
            rc = 1
        elif kind == "reading" and got["worker"] != 0:
            note = "SUSPECT: worker died rather than grading"
            rc = 1
        elif not got["failed"] and got["worker"] == 0:
            note = "SUSPECT: reward 0 with no failing test"
            rc = 1
        print("%-32s %-7s reward %d  worker %d  %s %s" % (
            slug, kind, got["reward"], got["worker"], why, note))
    return rc


if __name__ == "__main__":
    sys.exit(main())
