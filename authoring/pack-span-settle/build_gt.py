"""Freeze the enumerated shards' traces into tests/seal/gt.json.

The frozen file is what the grader checks the hand shards against, and the grader also asserts
the sealed model still reproduces it, so the two cannot drift apart quietly.

Any change to an already-frozen answer is a contract change, not a build step. This script
reads the old file first and prints every answer that moved, so a rule meant to be additive can
be proved additive rather than assumed to be.

    python3 build_gt.py             write, reporting what moved
    python3 build_gt.py --check     exit 1 if anything would move
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "pack-span-settle"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main(argv):
    check = "--check" in argv
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    added = sorted(set(new) - set(old))
    gone = sorted(set(old) - set(new))
    for name in moved:
        print("MOVED %s" % name)
        print("  was %s" % old[name])
        print("  now %s" % new[name])
    if added:
        print("added: %s" % ", ".join(added))
    if gone:
        print("removed: %s" % ", ".join(gone))
    if check:
        if moved or added or gone:
            return 1
        print("gt.json is current (%d shards)" % len(new))
        return 0

    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    GT.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in GT.read_text(encoding="utf-8")
    print("froze %d shards, %d answers moved" % (len(new), len(moved)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
