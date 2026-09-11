#!/usr/bin/env python3
"""Freeze the enumerated answers into tests/seal/gt.json, from the sealed model.

Additivity is the point of the re-read: every answer already frozen must come out of the model
byte for byte after any change to the environment or the generator. A moved answer is a change
to what "correct" means and is reported here rather than discovered at the review.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
OUT = TASK / "tests" / "seal" / "gt.json"

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    gone = sorted(set(old) - set(new))
    fresh = sorted(set(new) - set(old))
    for n in moved:
        print("CONTRACT CHANGE  %s\n  was %s\n  now %s" % (n, old[n], new[n]))
    if gone:
        print("dropped: %s" % gone)
    if fresh:
        print("new: %s" % fresh)
    if moved and "--force" not in sys.argv[1:]:
        print("\n%d frozen answer(s) moved - re-run with --force only if the contract really "
              "changed" % len(moved))
        return 1

    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("froze %d answers into %s" % (len(new), OUT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
