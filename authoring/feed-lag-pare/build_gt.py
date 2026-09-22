"""Freeze the hand answers into tests/seal/gt.json, and prove nothing already frozen moved.

The file is the frozen half of the contract: the grader checks the sealed model against it
before it grades anything, so a model that had drifted cannot quietly redefine correct. That
only works if this script refuses to overwrite an answer silently. It reads the existing file
first and reports every program whose answer changed; a change is a contract change and is
recorded in STATE.md as one, never waved through.

    python authoring/feed-lag-pare/build_gt.py            report, write only new programs
    python authoring/feed-lag-pare/build_gt.py --accept   write the changed answers too
"""
import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside
# tasks/<slug>/: authoring scratch that lands in the task folder has been packaged
# before (CLAUDE.md, token-seam-emit).
_sys.dont_write_bytecode = True

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "feed-lag-pare")
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = os.path.join(TASK, "tests", "seal", "gt.json")


def main():
    accept = "--accept" in sys.argv[1:]
    old = {}
    if os.path.isfile(GT):
        with open(GT, "r", encoding="utf-8") as fh:
            old = json.load(fh)

    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
    added = sorted(set(fresh) - set(old))
    dropped = sorted(set(old) - set(fresh))
    moved = sorted(n for n in set(old) & set(fresh) if old[n] != fresh[n])

    print("frozen %d, now %d: %d new, %d gone, %d moved"
          % (len(old), len(fresh), len(added), len(dropped), len(moved)))
    for name in added:
        print("  new     %s" % name)
    for name in dropped:
        print("  gone    %s" % name)
    for name in moved:
        print("  MOVED   %s\n    was %s\n    now %s" % (name, old[name], fresh[name]))

    if moved and not accept:
        print("\nAn answer that was frozen has moved. That is a change to what correct means.")
        print("Record it in STATE.md, then re-run with --accept.")
        return 1

    out = dict(old)
    out.update(fresh)
    for name in dropped:
        del out[name]
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d programs)" % (GT, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
