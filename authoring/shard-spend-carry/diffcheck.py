#!/usr/bin/env python3
"""Differential check: the reference run through the real frozen tree, against the sealed
model, and against a third per-slot model for the programs small enough to take it.

Authoring-side only. Nothing here ships.
"""
import argparse
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")


def tree(over):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ssc-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "opt" / part)
    return here


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--over", default=str(TASK / "solution"))
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--slots", action="store_true", help="also check the per-slot model")
    ap.add_argument("--skip", default="wide,deep")
    args = ap.parse_args()

    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import gen
    import model

    here = tree(args.over)
    sys.path.insert(0, str(here))
    import ops
    from opt import reg

    slots = None
    if args.slots:
        sys.path.insert(0, str(ROOT / "authoring" / "shard-spend-carry"))
        import slotmodel
        slots = slotmodel

    skip = set(args.skip.split(",")) if args.skip else set()
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    for s in range(args.seeds):
        for fam, name, lines in gen.programs("diff/%d" % s, args.per):
            if fam not in skip:
                work.append((fam, name, lines))

    bad = 0
    for fam, name, lines in work:
        r = reg.Reg()
        for line in lines:
            t = tuple(line.split())
            if t:
                ops.ex(r, t)
        want = model.expect(lines)
        if r.out != want:
            bad += 1
            if bad <= 3:
                for i in range(max(len(r.out), len(want))):
                    a = r.out[i] if i < len(r.out) else "-"
                    b = want[i] if i < len(want) else "-"
                    if a != b:
                        print("REF vs MODEL %s/%s line %d\n  ref  : %s\n  model: %s"
                              % (fam, name, i, a, b))
                        break
        if slots is not None:
            third = slots.expect(lines)
            if third != want:
                bad += 1
                if bad <= 5:
                    print("SLOT vs MODEL %s/%s differ" % (fam, name))
    print("checked %d programs, %d disagreements" % (len(work), bad))
    shutil.rmtree(here.parent, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
