#!/usr/bin/env python3
"""Freeze the enumerated answers into tests/seal/gt.json. Never ships.

The frozen file is what the grader checks the hand programs against, and the grader also
asserts that the sealed model still reproduces it, so the two can never drift apart quietly.

It reads the old file first and reports every answer that moved. A change to the model or to
the reference that was meant to be additive has to come out byte-identical on every program
already frozen; one that does move an answer is a contract change and is recorded as one
rather than absorbed.

    python3 -u authoring/row-anchor-pass/build_gt.py [--check]
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, _gen, model = lab.sealed()
GT = lab.TASK / "tests" / "seal" / "gt.json"


def main():
    check = "--check" in sys.argv
    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))

    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

    here = lab.inproc(lab.tree(lab.SOL))
    apart = [n for n in cases.ORDER
             if here.run("\n".join(cases.prog(n)) + "\n") != fresh[n]]
    if apart:
        print("reference and model disagree on %d programs: %s" % (len(apart), apart[:4]))
        return 1

    moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
    gone = sorted(set(old) - set(fresh))
    added = sorted(set(fresh) - set(old))
    print("frozen %d programs (%d new, %d dropped, %d moved)"
          % (len(fresh), len(added), len(gone), len(moved)))
    for name in moved:
        print("  MOVED %s" % name)
        for a, b in zip(old[name], fresh[name]):
            if a != b:
                print("     was %s" % a)
                print("     now %s" % b)
                break
    if check:
        return 1 if (moved or gone or added) else 0
    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
