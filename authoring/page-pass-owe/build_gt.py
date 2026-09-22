#!/usr/bin/env python3
"""Freeze the enumerated answers, and prove that nothing already frozen moved.

The answers come from the sealed model, never from the reference: the grader asserts the
model still reproduces this file before it grades anything, so a model that had drifted
cannot quietly redefine correct.

Every run reads the file that is already on disk first. An answer that changes is a change
to the contract, not a regression in a build script, so it is reported by name and the run
refuses unless --accept is given. That is the whole guard: a rule added later is additive
only if the answers frozen before it come out byte for byte the same.

    python3 -u authoring/page-pass-owe/build_gt.py
    python3 -u authoring/page-pass-owe/build_gt.py --accept
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
OUT = TASK / "tests" / "seal" / "gt.json"

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402


def main(argv):
    accept = "--accept" in argv
    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))

    fresh = {}
    for name in cases.ORDER:
        fresh[name] = model.run("\n".join(cases.prog(name)) + "\n")

    moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
    gone = sorted(set(old) - set(fresh))
    new = sorted(set(fresh) - set(old))

    for name in moved:
        print("MOVED   %s" % name, flush=True)
        print("   was  %s" % " | ".join(old[name]), flush=True)
        print("   now  %s" % " | ".join(fresh[name]), flush=True)
    for name in gone:
        print("DROPPED %s" % name, flush=True)
    for name in new:
        print("new     %s" % name, flush=True)

    if (moved or gone) and not accept:
        print("refusing to write: %d frozen answers moved, %d dropped. Re-run with "
              "--accept only if this is a deliberate contract change."
              % (len(moved), len(gone)), flush=True)
        return 1

    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise AssertionError("carriage return in gt.json")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("%d answers frozen, %d unchanged" % (len(fresh), len(set(old) & set(fresh))
                                               - len(moved)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
