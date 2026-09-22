"""Freeze the enumerated answers into tests/seal/gt.json, and prove nothing already frozen moved.

The file is the second definition of correct: the grader asserts that the sealed model still
reproduces it before it grades anything, so a model that drifted cannot quietly redefine the
answer. Any run that would change an answer already in the file has to say so out loud - a
rule change is a contract change, and the only honest way to notice one is to check.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path("/home/user/project-caesar/tasks/widen-pin-bind")
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tests" / "seal"))
sys.path.insert(0, "/home/user/project-caesar/authoring/widen-pin-bind")

import cases  # noqa: E402
import model  # noqa: E402
import lab  # noqa: E402

OUT = ROOT / "tests" / "seal" / "gt.json"


def main():
    was = {}
    if OUT.is_file():
        was = json.loads(OUT.read_text(encoding="utf-8"))
    run = lab.runner()
    fresh, moved, added = {}, [], []
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = model.expect(lines)
        got = run("\n".join(lines) + "\n")
        if got != want:
            print("REFERENCE DISAGREES WITH MODEL on %s" % name)
            for a, b in zip(got, want):
                if a != b:
                    print("   ref  ", a)
                    print("   model", b)
                    break
            return 2
        fresh[name] = want
        if name not in was:
            added.append(name)
        elif was[name] != want:
            moved.append(name)
    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("frozen: %d programs, %d new, %d moved" % (len(fresh), len(added), len(moved)))
    if moved:
        print("MOVED - a frozen answer changed, which is a contract change:")
        for name in moved:
            print("   ", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
