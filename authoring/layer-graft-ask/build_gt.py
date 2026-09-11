"""Freeze the enumerated answers into tests/seal/gt.json.

Two guards, both of which have caught something in this repository before:

  * the answers are read back before they are written, and any answer that MOVES is reported
    as a contract change rather than quietly rewritten - an addition to the plan language or
    a new case must leave every frozen answer byte-identical;
  * the file is written with an explicit newline and then checked for a stray carriage
    return, because nothing else in the kit reads gt.json as text.

The reference is run alongside the model and must agree line for line before anything is
written, so a model that had drifted cannot redefine correct on its own.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(HERE))

import agree  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402

OUT = TASK / "tests" / "seal" / "gt.json"


def main(argv):
    force = "--force" in argv
    old = {}
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
    run, work = agree.load_reference()
    fresh = {}
    bad = []
    for name in sorted(cases.PLANS):
        text = cases.PLANS[name]
        want = model.trace(text)
        got = run(text)
        if got != want:
            bad.append(name)
        fresh[name] = want
    shutil.rmtree(work, ignore_errors=True)
    if bad:
        print("reference and model disagree on: %s" % ", ".join(bad))
        return 1

    moved = [n for n in old if n in fresh and old[n] != fresh[n]]
    dropped = [n for n in old if n not in fresh]
    added = [n for n in fresh if n not in old]
    for name in moved:
        print("CONTRACT CHANGE %s" % name)
        for a, b in zip(old[name], fresh[name]):
            if a != b:
                print("   was %r  now %r" % (a, b))
    if dropped:
        print("dropped: %s" % ", ".join(sorted(dropped)))
    if moved and not force:
        print("%d frozen answers moved; re-run with --force only if the contract really "
              "changed" % len(moved))
        return 1
    if added:
        print("new cases: %s" % ", ".join(sorted(added)))

    body = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    lines = sum(len(v) for v in fresh.values())
    print("%d cases, %d graded lines, %d unchanged" % (len(fresh), lines, len(old) - len(moved)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
