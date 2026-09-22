"""Freeze tests/seal/gt.json: the report of every hand case, from the sealed model.

Nothing is written unless three things agree on every case:

  - the sealed model (tests/seal/model.py),
  - the definition itself: a brute force over every filling (brute.py), run on the case with
    its billion-value ranges shrunk to 0..40, which keeps every label's class because the
    hand cases are small,
  - the reference solution, run inside a copy of the shipped tree.

An answer already frozen in gt.json is never changed silently: if a case's report moves, the
build stops and says which, and only `--accept` lets it through. That is the record that a
contract change was a decision and not an accident.

Usage: python3 authoring/blank-fill-sure/build_gt.py [--accept] [--show]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "blank-fill-sure")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import brute  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402
import tree  # noqa: E402

GT = os.path.join(TASK, "tests", "seal", "gt.json")


def main():
    accept = "--accept" in sys.argv
    show = "--show" in sys.argv
    run = tree.runner(os.path.join(TASK, "solution"))
    old = {}
    if os.path.isfile(GT):
        with open(GT, encoding="utf-8") as fh:
            old = json.load(fh)
    new, bad, moved = {}, [], []
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = model.expect(lines)
        small = [l.replace("0..999999999", "0..40") for l in lines]
        defn = brute.report(small)
        mine = run("\n".join(lines) + "\n")
        if defn != want:
            bad.append((name, "model differs from the definition", defn, want))
        if mine != want:
            bad.append((name, "reference differs from the model", mine, want))
        if name in old and old[name] != want:
            moved.append((name, old[name], want))
        new[name] = want
        if show:
            print("== %s" % name)
            for line in want:
                print("   " + line)
    for name, why, a, b in bad:
        print("DISAGREE %s: %s\n  %s\n  %s" % (name, why, a, b))
    for name, a, b in moved:
        print("MOVED %s: frozen %s, now %s" % (name, a, b))
    if bad or (moved and not accept):
        print("gt.json not written")
        return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("gt.json written: %d cases, %d already frozen and unchanged, %d new"
          % (len(new), sum(1 for n in new if n in old and old[n] == new[n]),
             sum(1 for n in new if n not in old)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
