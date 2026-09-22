"""Freeze the enumerated answers from the sealed model, and prove a change was additive.

`tests/seal/gt.json` is the answer to every program in `tests/cases.py`, taken from the model
and then frozen. The grader asserts the model still reproduces it before it judges anything, so
a model that drifted cannot quietly redefine correct.

This script also reads the file it is about to replace. Every answer that was already frozen has
to come out byte-identical; if one moves, the run stops and prints the program, because a moved
answer is a contract change and not a bug fix. Adding a case is fine and is reported.

    python authoring/grant-widen-yield/build_gt.py
    python authoring/grant-widen-yield/build_gt.py --allow-change   only with a stated reason
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TESTS = ROOT / "tasks" / "grant-widen-yield" / "tests"
SEAL = TESTS / "seal"
GT = SEAL / "gt.json"

sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(SEAL))

import cases  # noqa: E402
import model  # noqa: E402


def main():
    loose = "--allow-change" in sys.argv
    old = {}
    if GT.exists():
        old = json.loads(GT.read_text(encoding="utf-8"))
    fresh = {}
    for name in cases.ORDER:
        fresh[name] = model.expect(cases.prog(name))
    moved = [n for n in old if n in fresh and old[n] != fresh[n]]
    dropped = sorted(set(old) - set(fresh))
    added = sorted(set(fresh) - set(old))
    if moved and not loose:
        print("FROZEN ANSWERS MOVED - this is a contract change, not a fix:")
        for name in moved:
            print("  %s" % name)
            print("    was: %s" % (old[name],))
            print("    now: %s" % (fresh[name],))
        return 1
    body = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    GT.write_text(body, encoding="utf-8", newline="\n")
    print("froze %d programs" % len(fresh))
    if added:
        print("  added: %s" % ", ".join(added))
    if dropped:
        print("  dropped: %s" % ", ".join(dropped))
    if moved:
        print("  CHANGED (allowed on the command line): %s" % ", ".join(moved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
