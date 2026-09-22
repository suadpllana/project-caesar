"""Freeze the enumerated answers into tests/seal/gt.json, from the sealed model.

The frozen file is what the grader checks the model against before it grades anything, so a
model that drifts cannot quietly redefine correct. It also makes a contract change visible:
this script reads the existing file first and prints every answer that moved, so a change
meant to be additive has to prove it by leaving every frozen answer byte-identical
(CLAUDE.md, publish-settle-order).

Usage:
    python authoring/pull-check-stale/build_gt.py [--check]
"""

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent.parent / "tasks" / "pull-check-stale"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases       # noqa: E402
import model       # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main(argv):
    check = "--check" in argv
    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))
    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
    added = sorted(set(fresh) - set(old))
    gone = sorted(set(old) - set(fresh))
    for n in moved:
        print("CONTRACT CHANGE  %s" % n)
        print("   was: %s" % " | ".join(old[n]))
        print("   now: %s" % " | ".join(fresh[n]))
    for n in added:
        print("added    %s" % n)
    for n in gone:
        print("removed  %s" % n)

    if check:
        if moved or added or gone:
            print("gt.json is not current")
            return 1
        print("gt.json is current: %d frozen answers" % len(fresh))
        return 0

    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise AssertionError("carriage return in gt.json")
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %d frozen answers, %d moved, %d added, %d removed"
          % (len(fresh), len(moved), len(added), len(gone)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
