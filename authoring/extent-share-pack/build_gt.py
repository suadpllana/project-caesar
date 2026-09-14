"""Freeze the answers to the enumerated programs, and prove nothing already frozen moved.

The answers come from the sealed model, and every one is checked against the brute-force engine
in this directory before it is written: two implementations that share no code, one of which
answers the drop question by copying the store and dropping the volume rather than deriving
anything. An existing gt.json is read first and any answer that changed is reported as a
contract change rather than quietly rewritten.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "extent-share-pack"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import brute  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    was = json.loads(GT.read_text(encoding="utf-8")) if GT.exists() else {}
    out = {}
    for name in cases.ORDER:
        lines = cases.ops(name)
        want = model.expect(lines)
        other = brute.expect(lines)
        if want != other:
            print("MODEL AND BRUTE DISAGREE on %s" % name)
            print("   model %s" % want)
            print("   brute %s" % other)
            return 1
        out[name] = want
    moved = [n for n in was if n in out and was[n] != out[n]]
    gone = [n for n in was if n not in out]
    if moved or gone:
        print("CONTRACT CHANGE - frozen answers moved:")
        for n in moved:
            print("   %s\n      was %s\n      now %s" % (n, was[n], out[n]))
        for n in gone:
            print("   dropped case %s" % n)
    fresh = [n for n in out if n not in was]
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    assert "\r" not in GT.read_text(encoding="utf-8")
    print("froze %d programs (%d new, %d unchanged, %d moved)"
          % (len(out), len(fresh), len(out) - len(fresh) - len(moved), len(moved)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
