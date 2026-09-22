"""Freeze the hand programs' answers from the sealed model, and prove what moved.

The frozen file is what the grader marks the enumerated programs against, and the grader
also asserts that the model still reproduces it, so the two can never drift apart quietly.
Every run compares against the file already on disk and prints which answers changed: a
change that was meant to be additive has to come out with nothing moved, and a change that
does move an answer is a contract change and is recorded as one.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
OUT = TASK / "tests" / "seal" / "gt.json"


def main():
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import model

    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
    moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
    added = sorted(set(fresh) - set(old))
    dropped = sorted(set(old) - set(fresh))

    body = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    OUT.write_text(body, encoding="utf-8", newline="\n")

    print("%d programs frozen" % len(fresh))
    print("added   %s" % (", ".join(added) or "none"))
    print("dropped %s" % (", ".join(dropped) or "none"))
    print("moved   %s" % (", ".join(moved) or "none - the change was additive"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
