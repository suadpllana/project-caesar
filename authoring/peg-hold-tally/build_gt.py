"""Freeze the hand-case answers from the definitional oracle.

The answers come from slow.py, which is neither the reference nor the sealed model, so gt.json is
independent of both. Any answer that moves against an already frozen file is reported as a contract
change, because a rule that changes an answer changes what correct means.
"""
import json
import pathlib
import sys

sys.path.insert(0, "../../tasks/peg-hold-tally/tests")

import cases  # noqa: E402
import slow  # noqa: E402

OUT = pathlib.Path("../../tasks/peg-hold-tally/tests/seal/gt.json")


def main():
    was = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
    now = {name: slow.expect(cases.ops(name)) for name in cases.ORDER}
    moved = [n for n in was if n in now and was[n] != now[n]]
    gone = [n for n in was if n not in now]
    fresh = [n for n in now if n not in was]
    text = json.dumps(now, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("%d cases, %d new, %d dropped, %d MOVED" % (len(now), len(fresh), len(gone), len(moved)))
    for n in moved:
        print("  CONTRACT CHANGE %s: %r -> %r" % (n, was[n], now[n]))
    return 1 if moved else 0


sys.exit(main())
