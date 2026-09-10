"""Freeze the model's trace for every enumerated program.

Additivity is the point of the check at the end: a case added or a rule extended must leave
every answer already frozen byte for byte where it was. If one moves, that is a contract change
and it is reported here rather than discovered later.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {name: model.trace(steps) for name, steps in cases.programs()}
    moved = [k for k in old if k in new and old[k] != new[k]]
    gone = [k for k in old if k not in new]
    added = [k for k in new if k not in old]
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise SystemExit("gt.json would carry a carriage return")
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("frozen %d programs, %d lines" % (len(new), sum(len(v) for v in new.values())))
    if added:
        print("added: %s" % ", ".join(sorted(added)))
    if gone:
        print("CONTRACT CHANGE - dropped: %s" % ", ".join(sorted(gone)))
    if moved:
        print("CONTRACT CHANGE - answers moved: %s" % ", ".join(sorted(moved)))
    return 1 if (moved or gone) else 0


if __name__ == "__main__":
    sys.exit(main())
