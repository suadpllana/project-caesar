"""Freeze the enumerated answers, and prove a contract change did not move the old ones.

gt.json is the frozen side of the grading: the sealed model is asserted against it before it
judges anything, so a model that drifted cannot quietly redefine correct. Every run re-reads the
file first and reports any answer that moved, because an additive change to the contract has to
leave every already-frozen trace byte-identical and a change that moves one is a contract change
whether or not it was meant as one.

    python3 authoring/shard-redraw-resume/build_gt.py            report, do not write
    python3 authoring/shard-redraw-resume/build_gt.py --write    write when it agrees or is new
    python3 authoring/shard-redraw-resume/build_gt.py --force    write even when answers moved
"""
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
GT = TASK / "tests" / "seal" / "gt.json"
WAS = pathlib.Path(__file__).resolve().parent / "frozen_progs.json"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(ROOT / "authoring" / "shard-redraw-resume"))
os.environ.setdefault("SRR_PRISTINE", str(TASK / "tests" / "pristine"))

import cases  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402


def main():
    here = lab.tree(TASK / "solution")
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-gt-"))
    fresh, split = {}, []
    for name in cases.ORDER:
        lines = cases.ops(name)
        path = room / (name + ".txt")
        path.write_text("\n".join(lines) + "\n", newline="\n")
        ref = lab.run(here, path)
        want = model.expect(lines)
        if ref != want:
            split.append(name)
        fresh[name] = want
    if split:
        print("reference and model disagree on: %s" % ", ".join(split))
        return 2

    was = json.loads(WAS.read_text(encoding="utf-8")) if WAS.is_file() else {}
    now = {n: cases.ops(n) for n in cases.ORDER}
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else None
    if old is not None:
        moved = [n for n in sorted(set(old) & set(fresh))
                 if old[n] != fresh[n] and was.get(n, now[n]) == now[n]]
        edited = [n for n in sorted(set(old) & set(fresh))
                  if old[n] != fresh[n] and was.get(n, now[n]) != now[n]]
        for name in edited:
            print("  edited   %s - the program itself changed, so its answer moving is the "
                  "case moving and not the contract" % name)
        added = sorted(set(fresh) - set(old))
        gone = sorted(set(old) - set(fresh))
        print("frozen %d, unchanged %d, moved %d, added %d, dropped %d"
              % (len(old), len(set(old) & set(fresh)) - len(moved), len(moved),
                 len(added), len(gone)))
        for name in moved:
            print("  MOVED %s" % name)
        if moved and "--force" not in sys.argv:
            print("an already-frozen answer moved: that is a contract change, not a rebuild")
            return 1
    else:
        print("no frozen answers yet: %d cases" % len(fresh))

    if "--write" in sys.argv or "--force" in sys.argv:
        GT.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
        WAS.write_text(json.dumps({n: cases.ops(n) for n in cases.ORDER},
                                  indent=1, sort_keys=True) + "\n",
                       encoding="utf-8", newline="\n")
        assert "\r" not in GT.read_text(encoding="utf-8")
        print("wrote %s" % GT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
