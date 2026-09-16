"""Freeze the enumerated answers, and prove a change was additive.

gt.json is written from the sealed model and checked against the reference, which is written
apart from it. Every answer already frozen has to come out byte-identical; a run that moves one
is reporting a contract change and says so, so an addition that was meant to be additive cannot
quietly redefine an answer that was already agreed (CLAUDE.md, publish-settle-order).
"""
import json
import pathlib
import sys

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases   # noqa: E402
import model   # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    was = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    here = lab.ref()
    ops, prog, store = lab.load(here)
    out, moved, added = {}, [], []
    for name in cases.ORDER:
        lines = cases.ops(name)
        want = model.expect(lines)
        f = store.Fld()
        for w in prog.walk(lines):
            ops.ex(f, w)
        if f.out != want:
            raise SystemExit("reference and model disagree on %s:\n  ref   %s\n  model %s"
                             % (name, f.out, want))
        out[name] = want
        if name not in was:
            added.append(name)
        elif was[name] != want:
            moved.append(name)
    GT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                  encoding="utf-8", newline="\n")
    gone = sorted(set(was) - set(out))
    print("%d frozen answers, %d added, %d moved, %d dropped"
          % (len(out), len(added), len(moved), len(gone)))
    if moved:
        print("CONTRACT CHANGE - these answers are not what they were: %s" % " ".join(moved))
    if gone:
        print("dropped: %s" % " ".join(gone))
    assert not any("\r" in "\n".join(v) for v in out.values())
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
