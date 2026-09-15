"""Freeze the enumerated answers, and prove that nothing already frozen has moved.

The answers come from the sealed model. Every run reads the existing gt.json first and reports
any case whose answer changed, because a change there is a contract change and has to be one on
purpose rather than a side effect of editing the model or the generator.

Usage: build_gt.py [--write]
"""
import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    write = "--write" in sys.argv
    fresh = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}

    moved = [n for n in old if n in fresh and old[n] != fresh[n]]
    gone = [n for n in old if n not in fresh]
    new = [n for n in fresh if n not in old]
    for name in moved:
        print("CHANGED %s" % name)
        print("   was:", old[name])
        print("   now:", fresh[name])
    for name in gone:
        print("REMOVED %s" % name)
    for name in new:
        print("added   %s" % name)
    print("%d cases, %d unchanged, %d changed, %d added, %d removed"
          % (len(fresh), len(set(old) & set(fresh)) - len(moved), len(moved), len(new),
             len(gone)))

    if write:
        text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
        assert "\r" not in text
        GT.write_text(text, encoding="utf-8", newline="\n")
        print("wrote", GT)
    elif not GT.is_file():
        print("no gt.json yet - run with --write")
        return 1
    return 1 if moved or gone else 0


if __name__ == "__main__":
    sys.exit(main())
